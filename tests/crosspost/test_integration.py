from __future__ import annotations

import json

from scripts.crosspost.__main__ import run


BASE = "https://dev.to/api"


def _silence_sleep(monkeypatch):
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: None)


def _post_body(title: str) -> str:
    return f'---\ntitle: "{title}"\ndate: 2026-04-17\ndraft: false\n---\nHello {title}.\n'


def _write_post(repo, rel_path: str, title: str) -> None:
    repo.write(rel_path, _post_body(title))


def test_first_push_creates_draft(
    tmp_git_repo, devto_responses, monkeypatch, capsys
):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    _write_post(repo, "content/post/2026-04-17-foo/index.md", "Foo")
    repo.add_all()
    after = repo.commit("add foo")

    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/published", json=[], status=200
    )
    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/unpublished", json=[], status=200
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={
            "id": 42,
            "title": "Foo",
            "published": False,
            "url": "https://dev.to/test/42",
        },
        status=201,
    )

    monkeypatch.setenv("DEVTO_API_KEY", "test-key")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)

    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )

    assert exit_code == 0

    post_calls = [c for c in devto_responses.calls if c.request.method == "POST"]
    assert len(post_calls) == 1
    payload = json.loads(post_calls[0].request.body)
    assert payload["article"]["published"] is False
    assert payload["article"]["title"] == "Foo"

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "[drafted]" in combined
    assert "drafted=1" in combined


def test_idempotent_rerun(tmp_git_repo, devto_responses, monkeypatch, capsys):
    """Second run on the same commits skips when title already exists."""
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    _write_post(repo, "content/post/2026-04-17-foo/index.md", "My Post")
    repo.add_all()
    after = repo.commit("add foo")

    # Dev.to already has an article with a title that matches (case + whitespace variant).
    existing_article = {
        "id": 7,
        "title": "  my post  ",
        "published": True,
        "url": "https://dev.to/test/7",
    }
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/published",
        json=[existing_article],
        status=200,
    )
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/published",
        json=[],
        status=200,
    )
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/unpublished",
        json=[],
        status=200,
    )

    monkeypatch.setenv("DEVTO_API_KEY", "test-key")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)

    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )

    assert exit_code == 0
    post_calls = [c for c in devto_responses.calls if c.request.method == "POST"]
    assert post_calls == []

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "[skipped_exists]" in combined
    assert "drafted=0" in combined


def test_two_posts_same_title_second_skipped(
    tmp_git_repo, devto_responses, monkeypatch
):
    """In-run dedup: first create succeeds, second with same title is skipped."""
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    _write_post(repo, "content/post/2026-04-17-a/index.md", "Shared Title")
    _write_post(repo, "content/post/2026-04-17-b/index.md", "Shared Title")
    repo.add_all()
    after = repo.commit("add both")

    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/published", json=[], status=200
    )
    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/unpublished", json=[], status=200
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={
            "id": 100,
            "title": "Shared Title",
            "published": False,
            "url": "https://dev.to/test/100",
        },
        status=201,
    )

    monkeypatch.setenv("DEVTO_API_KEY", "test-key")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)

    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 0

    post_calls = [c for c in devto_responses.calls if c.request.method == "POST"]
    assert len(post_calls) == 1


# --- T023: error classification integration tests ---


def test_missing_api_key_global_failure(tmp_git_repo, monkeypatch, capsys):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")
    _write_post(repo, "content/post/2026-04-17-foo/index.md", "Foo")
    repo.add_all()
    after = repo.commit("add foo")

    monkeypatch.delenv("DEVTO_API_KEY", raising=False)
    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "global_failure: missing DEVTO_API_KEY" in captured.err


def test_list_articles_503_exhausts_is_global_failure(
    tmp_git_repo, devto_responses, monkeypatch, capsys
):
    _silence_sleep(monkeypatch)
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")
    _write_post(repo, "content/post/2026-04-17-foo/index.md", "Foo")
    repo.add_all()
    after = repo.commit("add foo")

    for _ in range(3):
        devto_responses.add(
            devto_responses.GET,
            f"{BASE}/articles/me/published",
            status=503,
            body="no",
        )

    monkeypatch.setenv("DEVTO_API_KEY", "k")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)
    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "global_failure" in captured.err


def test_401_on_create_is_global_failure(
    tmp_git_repo, devto_responses, monkeypatch, capsys
):
    _silence_sleep(monkeypatch)
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")
    _write_post(repo, "content/post/2026-04-17-foo/index.md", "Foo")
    repo.add_all()
    after = repo.commit("add foo")

    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/published", json=[], status=200
    )
    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/unpublished", json=[], status=200
    )
    devto_responses.add(
        devto_responses.POST, f"{BASE}/articles", status=401, body="nope"
    )

    monkeypatch.setenv("DEVTO_API_KEY", "bad")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)
    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "global_failure" in captured.err


def test_single_422_is_per_post_error_not_global(
    tmp_git_repo, devto_responses, monkeypatch, capsys
):
    _silence_sleep(monkeypatch)
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")
    _write_post(repo, "content/post/2026-04-17-a/index.md", "A Post")
    _write_post(repo, "content/post/2026-04-17-b/index.md", "B Post")
    repo.add_all()
    after = repo.commit("add both")

    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/published", json=[], status=200
    )
    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/unpublished", json=[], status=200
    )
    # One 422 and one success — order depends on discovery order (sorted by path).
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"error": "bad"},
        status=422,
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"id": 99, "title": "B Post", "published": False, "url": "x"},
        status=201,
    )

    monkeypatch.setenv("DEVTO_API_KEY", "k")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)
    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[error]" in captured.out
    assert "[drafted]" in captured.out


def test_all_creates_retry_exhausted_is_global_failure(
    tmp_git_repo, devto_responses, monkeypatch, capsys
):
    _silence_sleep(monkeypatch)
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")
    _write_post(repo, "content/post/2026-04-17-a/index.md", "A Post")
    repo.add_all()
    after = repo.commit("add a")

    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/published", json=[], status=200
    )
    devto_responses.add(
        devto_responses.GET, f"{BASE}/articles/me/unpublished", json=[], status=200
    )
    for _ in range(3):
        devto_responses.add(
            devto_responses.POST, f"{BASE}/articles", status=503, body="down"
        )

    monkeypatch.setenv("DEVTO_API_KEY", "k")
    monkeypatch.setenv("DEVTO_API_BASE", BASE)
    exit_code = run(
        [
            "--before",
            before,
            "--after",
            after,
            "--repo-root",
            str(repo.path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "global_failure" in captured.err
