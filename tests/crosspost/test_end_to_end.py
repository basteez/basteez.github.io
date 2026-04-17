from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import responses

API = "https://dev.to/api"
LISTING_URL = f"{API}/articles/me/all"


def _hugo_config(tmp_path: Path) -> Path:
    p = tmp_path / "hugo.yaml"
    p.write_text("baseurl: https://bstz.it\npermalinks:\n  post: /p/:slug/\n")
    return p


def _make_post(tmp_path: Path, filename: str, body: str) -> Path:
    content_dir = tmp_path / "content" / "post"
    content_dir.mkdir(parents=True, exist_ok=True)
    target = content_dir / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    return target


def _register_default_listing(items: list[dict] | None = None) -> None:
    """Register a dev.to listing response. Callers who need richer listings (multi-page,
    failure) should register before invoking _run() so their responses are consumed first.
    """
    responses.add(
        responses.GET,
        LISTING_URL,
        json=items or [],
        status=200,
    )


def _run(tmp_path: Path, extra_env: dict | None = None, extra_args: list | None = None) -> tuple[int, str]:
    from scripts.crosspost.__main__ import run

    state_file = tmp_path / ".crosspost" / "state.json"
    content_dir = tmp_path / "content" / "post"
    hugo_cfg = tmp_path / "hugo.yaml"
    if not hugo_cfg.exists():
        _hugo_config(tmp_path)

    env = {"DEVTO_API_KEY": "test-key", "GITHUB_SHA": "abcdef1"}
    if extra_env is not None:
        env.update(extra_env)

    args = [
        "--content-dir",
        str(content_dir),
        "--state-file",
        str(state_file),
        "--hugo-config",
        str(hugo_cfg),
    ]
    if extra_args:
        args.extend(extra_args)

    # If no listing response was registered by the test, register a default empty one
    # so the pre-flight listing fetch succeeds. Registered tests should pre-register.
    have_listing = any(
        r.url == LISTING_URL and r.method == "GET" for r in responses.registered()
    )
    if not have_listing:
        _register_default_listing([])

    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = run(args, env)
    return code, buf.getvalue()


# ---------------------------------------------------------------------------
# Existing 001 scenarios (now with listing mock added)
# ---------------------------------------------------------------------------


@responses.activate
def test_new_post_creates_devto_draft(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello"
            date: 2026-04-17T10:00:00Z
            tags:
              - hugo
              - testing
            ---

            Body text.
            """
        ),
    )

    responses.add(
        responses.POST,
        f"{API}/articles",
        json={"id": 101, "url": "https://dev.to/u/hello-abc1", "published": False},
        status=201,
    )

    code, out = _run(tmp_path)
    assert code == 0, out

    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    body = json.loads(post_calls[0].request.body)
    assert body["article"]["published"] is False
    assert body["article"]["canonical_url"] == "https://bstz.it/p/hello/"
    assert body["article"]["tags"] == ["hugo", "testing"]

    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert state["hello"]["devto_article_id"] == 101
    assert state["hello"]["devto_url"] == "https://dev.to/u/hello-abc1"


@responses.activate
def test_unchanged_post_is_skipped(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello"
            date: 2026-04-17T10:00:00Z
            ---

            Body.
            """
        ),
    )

    from scripts.crosspost.posts import discover_posts

    posts = discover_posts(tmp_path / "content" / "post", "https://bstz.it", "/p/:slug/")
    prehash = posts[0].content_hash

    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 101,
            "devto_url": "https://dev.to/u/hello-abc1",
            "last_synced_commit": "earlier",
            "last_body_sha256": prehash,
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    state_path = tmp_path / ".crosspost" / "state.json"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    before = state_path.read_bytes()

    code, out = _run(tmp_path)
    assert code == 0, out
    # only the listing call is allowed; no POST/PUT
    assert all(c.request.method == "GET" for c in responses.calls)
    assert state_path.read_bytes() == before


@responses.activate
def test_edited_post_updates_in_place(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello v2"
            date: 2026-04-17T10:00:00Z
            ---

            New body.
            """
        ),
    )

    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 101,
            "devto_url": "https://dev.to/u/hello-abc1",
            "last_synced_commit": "old-sha",
            "last_body_sha256": "stale-hash",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    (tmp_path / ".crosspost" / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )

    # listing returns the same article id → update proceeds
    _register_default_listing(
        [
            {
                "id": 101,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/hello-abc1",
                "published": True,
            }
        ]
    )

    responses.add(
        responses.PUT,
        f"{API}/articles/101",
        json={"id": 101, "url": "https://dev.to/u/hello-abc1", "published": True},
        status=200,
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    put_calls = [c for c in responses.calls if c.request.method == "PUT"]
    assert len(put_calls) == 1
    body = json.loads(put_calls[0].request.body)
    assert "published" not in body["article"]
    updated = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert updated["hello"]["created_at"] == "2026-04-01T10:00:00Z"
    assert updated["hello"]["last_body_sha256"] != "stale-hash"


@responses.activate
def test_draft_frontmatter_skips_no_http(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-wip.md",
        dedent(
            """\
            ---
            title: "WIP"
            date: 2026-04-17T10:00:00Z
            draft: true
            ---

            Body.
            """
        ),
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    # no POST/PUT; only the listing GET
    assert all(c.request.method == "GET" for c in responses.calls)
    assert "SKIP" in out
    assert "draft" in out


@responses.activate
def test_future_dated_post_skipped_scheduled(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2099-01-01-future.md",
        dedent(
            """\
            ---
            title: "Future"
            date: 2099-01-01T10:00:00Z
            ---

            body
            """
        ),
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    assert all(c.request.method == "GET" for c in responses.calls)
    assert "scheduled" in out


@responses.activate
def test_opt_out_post_skipped(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-private.md",
        dedent(
            """\
            ---
            title: "Private"
            date: 2026-04-17T10:00:00Z
            crosspost: false
            ---

            body
            """
        ),
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    assert all(c.request.method == "GET" for c in responses.calls)
    assert "opt-out" in out
    assert not (tmp_path / ".crosspost" / "state.json").exists()


@responses.activate
def test_mixed_batch_opt_in_and_opt_out(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-public.md",
        dedent(
            """\
            ---
            title: "Public"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    _make_post(
        tmp_path,
        "2026-04-17-private.md",
        dedent(
            """\
            ---
            title: "Private"
            date: 2026-04-17T10:00:00Z
            crosspost: false
            ---

            body
            """
        ),
    )
    responses.add(
        responses.POST,
        f"{API}/articles",
        json={"id": 202, "url": "https://dev.to/u/public-xyz", "published": False},
        status=201,
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    assert len(post_calls) == 1
    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert "public" in state
    assert "private" not in state


@responses.activate
def test_missing_api_key_preflight_fails(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    code, out = _run(tmp_path, extra_env={"DEVTO_API_KEY": ""})
    assert code == 1
    assert len(responses.calls) == 0
    assert "DEVTO_API_KEY" in out or "credential" in out.lower()


@responses.activate
def test_update_404_reports_missing_and_exits_1(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello v2"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 9999,
            "devto_url": "https://dev.to/u/hello-old",
            "last_synced_commit": "old",
            "last_body_sha256": "stale",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    (tmp_path / ".crosspost" / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )
    # listing returns empty → no remote match → reconcile keeps UPDATE → PUT 404
    responses.add(
        responses.PUT, f"{API}/articles/9999", status=404, json={"error": "not found"}
    )

    code, out = _run(tmp_path)
    assert code == 1
    assert "FAIL" in out
    assert "9999" in out
    assert "not found" in out.lower()


@responses.activate
def test_mixed_run_ok_skip_fail(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-alpha.md",
        dedent(
            """\
            ---
            title: "Alpha"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    _make_post(
        tmp_path,
        "2026-04-17-beta.md",
        dedent(
            """\
            ---
            title: "Beta"
            date: 2026-04-17T10:00:00Z
            crosspost: false
            ---

            body
            """
        ),
    )
    _make_post(
        tmp_path,
        "2026-04-17-gamma.md",
        dedent(
            """\
            ---
            title: "Gamma v2"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    (tmp_path / ".crosspost").mkdir()
    state = {
        "gamma": {
            "devto_article_id": 9999,
            "devto_url": "https://dev.to/u/gamma-old",
            "last_synced_commit": "old",
            "last_body_sha256": "stale",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    (tmp_path / ".crosspost" / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )
    responses.add(
        responses.POST,
        f"{API}/articles",
        json={"id": 303, "url": "https://dev.to/u/alpha", "published": False},
        status=201,
    )
    responses.add(
        responses.PUT,
        f"{API}/articles/9999",
        status=404,
        json={"error": "not found"},
    )

    code, out = _run(tmp_path)
    assert code == 1
    lines = [ln for ln in out.splitlines() if ln.startswith(("OK", "SKIP", "FAIL"))]
    assert len(lines) == 3
    outcomes = [ln.split()[0] for ln in lines]
    slugs = [ln.split()[1] for ln in lines]
    assert slugs == sorted(slugs)
    assert set(outcomes) == {"OK", "SKIP", "FAIL"}
    assert (
        "summary: 1 created, 0 updated, 0 adopted, 1 skipped, 1 failed (of 3 candidates)"
        in out
    )


@responses.activate
def test_orphan_slug_logged(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    from scripts.crosspost.posts import discover_posts

    posts = discover_posts(tmp_path / "content" / "post", "https://bstz.it", "/p/:slug/")
    hello_hash = posts[0].content_hash

    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 1,
            "devto_url": "https://dev.to/u/hello",
            "last_synced_commit": "x",
            "last_body_sha256": hello_hash,
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        },
        "removed-post": {
            "devto_article_id": 999,
            "devto_url": "https://dev.to/u/removed",
            "last_synced_commit": "x",
            "last_body_sha256": "old",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        },
    }
    (tmp_path / ".crosspost" / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    assert "orphan" in out
    assert "removed-post" in out


@responses.activate
def test_dry_run_makes_no_http_or_state_writes(tmp_path: Path):
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            """\
            ---
            title: "Hello"
            date: 2026-04-17T10:00:00Z
            ---

            body
            """
        ),
    )
    code, out = _run(tmp_path, extra_args=["--dry-run"])
    assert code == 0, out
    # listing GET is allowed; no POST / PUT
    assert all(c.request.method == "GET" for c in responses.calls)
    assert not (tmp_path / ".crosspost" / "state.json").exists()


# ---------------------------------------------------------------------------
# US1: new integration tests for the adoption / reconciliation path
# ---------------------------------------------------------------------------


def _write_hello(tmp_path: Path, title: str = "Hello") -> None:
    _hugo_config(tmp_path)
    _make_post(
        tmp_path,
        "2026-04-17-hello.md",
        dedent(
            f"""\
            ---
            title: "{title}"
            date: 2026-04-17T10:00:00Z
            ---

            Body text.
            """
        ),
    )


@responses.activate
def test_us1_empty_state_match_in_listing_adopts(tmp_path: Path):
    _write_hello(tmp_path)
    _register_default_listing(
        [
            {
                "id": 777,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/hello-abc1",
                "published": False,
            }
        ]
    )

    code, out = _run(tmp_path)
    assert code == 0, out
    # zero POST, zero PUT
    assert [c.request.method for c in responses.calls] == ["GET"]
    assert "adopted https://dev.to/u/hello-abc1" in out

    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert state["hello"]["devto_article_id"] == 777
    assert state["hello"]["devto_url"] == "https://dev.to/u/hello-abc1"
    assert state["hello"]["last_synced_commit"] == "abcdef1"
    assert state["hello"]["created_at"] == state["hello"]["updated_at"]

    from scripts.crosspost.posts import discover_posts

    discovered = discover_posts(tmp_path / "content" / "post", "https://bstz.it", "/p/:slug/")
    assert state["hello"]["last_body_sha256"] == discovered[0].content_hash


@responses.activate
def test_us1_empty_state_no_match_creates(tmp_path: Path):
    _write_hello(tmp_path)
    # listing returns nothing → CREATE
    responses.add(
        responses.POST,
        f"{API}/articles",
        json={"id": 501, "url": "https://dev.to/u/hello-new", "published": False},
        status=201,
    )
    code, out = _run(tmp_path)
    assert code == 0, out
    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    assert len(post_calls) == 1
    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert state["hello"]["devto_article_id"] == 501


@responses.activate
def test_us1_state_and_listing_agree_updates(tmp_path: Path):
    _write_hello(tmp_path, title="Hello v2")
    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 111,
            "devto_url": "https://dev.to/u/hello-abc1",
            "last_synced_commit": "old",
            "last_body_sha256": "stale",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    (tmp_path / ".crosspost" / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )
    _register_default_listing(
        [
            {
                "id": 111,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/hello-abc1",
                "published": True,
            }
        ]
    )
    responses.add(
        responses.PUT,
        f"{API}/articles/111",
        json={"id": 111, "url": "https://dev.to/u/hello-abc1", "published": True},
        status=200,
    )
    code, out = _run(tmp_path)
    assert code == 0, out
    put_calls = [c for c in responses.calls if c.request.method == "PUT"]
    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    assert len(put_calls) == 1
    assert len(post_calls) == 0


@responses.activate
def test_us1_two_listing_matches_fail_multiple(tmp_path: Path):
    _write_hello(tmp_path)
    _register_default_listing(
        [
            {
                "id": 111,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/dup1",
                "published": True,
            },
            {
                "id": 222,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/dup2",
                "published": True,
            },
        ]
    )
    code, out = _run(tmp_path)
    assert code == 1
    post_calls = [c for c in responses.calls if c.request.method == "POST"]
    put_calls = [c for c in responses.calls if c.request.method == "PUT"]
    assert post_calls == [] and put_calls == []
    assert (
        "FAIL  hello  dev.to has multiple articles with canonical_url "
        "https://bstz.it/p/hello/ (ids: 111, 222) — delete duplicates on dev.to and re-run"
    ) in out
    assert not (tmp_path / ".crosspost" / "state.json").exists()


@responses.activate
def test_us1_state_id_mismatch_fails_id_mismatch(tmp_path: Path):
    _write_hello(tmp_path)
    (tmp_path / ".crosspost").mkdir()
    state = {
        "hello": {
            "devto_article_id": 111,
            "devto_url": "https://dev.to/u/hello-old",
            "last_synced_commit": "old",
            "last_body_sha256": "stale",
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-04-01T10:00:00Z",
        }
    }
    state_path = tmp_path / ".crosspost" / "state.json"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    _register_default_listing(
        [
            {
                "id": 222,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/hello-new",
                "published": True,
            }
        ]
    )
    code, out = _run(tmp_path)
    assert code == 1
    assert [c.request.method for c in responses.calls] == ["GET"]
    assert (
        "FAIL  hello  state says article 111 but canonical_url "
        "https://bstz.it/p/hello/ on dev.to resolves to article(s) 222 — reconcile manually"
    ) in out


@responses.activate
def test_us1_listing_fails_every_eligible_post_fails(tmp_path: Path):
    _hugo_config(tmp_path)
    for name, extra_line in [
        ("alpha", ""),
        ("beta", ""),
        ("gamma", ""),
        ("delta", "draft: true"),
    ]:
        fm_lines = [
            "---",
            f'title: "{name.title()}"',
            "date: 2026-04-17T10:00:00Z",
        ]
        if extra_line:
            fm_lines.append(extra_line)
        fm_lines.extend(["---", "", "body", ""])
        _make_post(tmp_path, f"2026-04-17-{name}.md", "\n".join(fm_lines))
    # listing fails with 500 twice
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})

    import scripts.crosspost.devto as devto_mod

    _orig = devto_mod.SERVER_RETRY_SLEEP_SECONDS
    devto_mod.SERVER_RETRY_SLEEP_SECONDS = 0
    try:
        code, out = _run(tmp_path)
    finally:
        devto_mod.SERVER_RETRY_SLEEP_SECONDS = _orig

    assert code == 1
    # zero POST / PUT
    assert all(c.request.method == "GET" for c in responses.calls)
    # delta (draft) still reported as SKIP
    assert "SKIP" in out and "delta" in out
    # 3 FAIL lines for alpha, beta, gamma — all with "dev.to listing unavailable:"
    fail_lines = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
    assert len(fail_lines) == 3
    for ln in fail_lines:
        assert "dev.to listing unavailable:" in ln
    assert not (tmp_path / ".crosspost" / "state.json").exists()


@responses.activate
def test_us1_two_posts_both_adopt_in_one_run(tmp_path: Path):
    _hugo_config(tmp_path)
    for slug in ("one", "two"):
        _make_post(
            tmp_path,
            f"2026-04-17-{slug}.md",
            dedent(
                f"""\
                ---
                title: "{slug}"
                date: 2026-04-17T10:00:00Z
                ---

                body
                """
            ),
        )
    _register_default_listing(
        [
            {
                "id": 1001,
                "canonical_url": "https://bstz.it/p/one/",
                "url": "https://dev.to/u/one-aaaa",
                "published": False,
            },
            {
                "id": 1002,
                "canonical_url": "https://bstz.it/p/two/",
                "url": "https://dev.to/u/two-bbbb",
                "published": False,
            },
        ]
    )
    code, out = _run(tmp_path)
    assert code == 0, out
    assert all(c.request.method == "GET" for c in responses.calls)
    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert state["one"]["devto_article_id"] == 1001
    assert state["two"]["devto_article_id"] == 1002


@responses.activate
def test_us1_pagination_match_on_page_2(tmp_path: Path):
    _write_hello(tmp_path)
    page1 = [
        {
            "id": i,
            "canonical_url": f"https://bstz.it/p/other-{i}/",
            "url": f"https://dev.to/u/other-{i}",
            "published": True,
        }
        for i in range(1, 101)
    ]
    page2 = [
        {
            "id": 777,
            "canonical_url": "https://bstz.it/p/hello/",
            "url": "https://dev.to/u/hello-abc1",
            "published": False,
        }
    ]
    responses.add(responses.GET, LISTING_URL, json=page1, status=200)
    responses.add(responses.GET, LISTING_URL, json=page2, status=200)

    code, out = _run(tmp_path)
    assert code == 0, out
    # zero POST/PUT
    assert all(c.request.method == "GET" for c in responses.calls)
    state = json.loads((tmp_path / ".crosspost" / "state.json").read_text())
    assert state["hello"]["devto_article_id"] == 777


@responses.activate
def test_us1_dry_run_adoption_is_reported_but_no_state_written(tmp_path: Path):
    _write_hello(tmp_path)
    _register_default_listing(
        [
            {
                "id": 777,
                "canonical_url": "https://bstz.it/p/hello/",
                "url": "https://dev.to/u/hello-abc1",
                "published": False,
            }
        ]
    )
    code, out = _run(tmp_path, extra_args=["--dry-run"])
    assert code == 0, out
    # listing GET still happens
    assert any(c.request.method == "GET" for c in responses.calls)
    assert "(dry-run) would adopt https://dev.to/u/hello-abc1" in out
    assert not (tmp_path / ".crosspost" / "state.json").exists()


@responses.activate
def test_us1_dry_run_listing_failure_still_fails(tmp_path: Path):
    _write_hello(tmp_path)
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})

    import scripts.crosspost.devto as devto_mod

    _orig = devto_mod.SERVER_RETRY_SLEEP_SECONDS
    devto_mod.SERVER_RETRY_SLEEP_SECONDS = 0
    try:
        code, out = _run(tmp_path, extra_args=["--dry-run"])
    finally:
        devto_mod.SERVER_RETRY_SLEEP_SECONDS = _orig

    assert code == 1
    assert "dev.to listing unavailable:" in out
    assert not (tmp_path / ".crosspost" / "state.json").exists()
