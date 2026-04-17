from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from scripts.crosspost.devto import (
    ArticleMissingError,
    CredentialError,
    DevToClient,
    DevToError,
    ListingError,
    RateLimitError,
    ServerError,
)
from scripts.crosspost.posts import (
    BlogPost,
    HugoConfigError,
    PostDiscoveryError,
    discover_posts,
    load_hugo_config,
)
from scripts.crosspost.reconcile import (
    DevToArticleSummary,
    ReconciledAction,
    build_canonical_index,
    normalize_canonical_url,
    reconcile,
)
from scripts.crosspost.report import Report
from scripts.crosspost.state import StateError, load_state, save_state, update_entry


class Classification(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SKIP_DRAFT = "SKIP_DRAFT"
    SKIP_SCHEDULED = "SKIP_SCHEDULED"
    SKIP_UNCHANGED = "SKIP_UNCHANGED"
    SKIP_OPT_OUT = "SKIP_OPT_OUT"


@dataclass
class ClassifyResult:
    action: Classification
    reason: str


def classify_post(post: BlogPost, state: dict, now: datetime) -> ClassifyResult:
    if post.crosspost_enabled is False:
        return ClassifyResult(Classification.SKIP_OPT_OUT, "opt-out (crosspost: false)")
    if post.is_draft:
        return ClassifyResult(Classification.SKIP_DRAFT, "draft")
    if post.date > now:
        return ClassifyResult(
            Classification.SKIP_SCHEDULED, f"scheduled for {post.date.isoformat()}"
        )
    entry = state.get(post.slug)
    if entry is None:
        return ClassifyResult(Classification.CREATE, "new post")
    if entry.get("last_body_sha256") == post.content_hash:
        return ClassifyResult(Classification.SKIP_UNCHANGED, "unchanged")
    return ClassifyResult(Classification.UPDATE, "body hash changed")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.crosspost",
        description="Cross-post blog posts to dev.to.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not call dev.to or write state.")
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated slugs to restrict processing to.",
    )
    parser.add_argument("--content-dir", type=str, default="content/post")
    parser.add_argument("--state-file", type=str, default=".crosspost/state.json")
    parser.add_argument(
        "--hugo-config",
        type=str,
        default="hugo.yaml",
        help="Path to Hugo site config (for baseurl + permalinks).",
    )
    return parser.parse_args(argv)


def _append_github_summary(summary_md: str, env: dict) -> None:
    path = env.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(summary_md)


def _filter_only(posts: Iterable[BlogPost], only: str) -> list[BlogPost]:
    if not only.strip():
        return list(posts)
    wanted = {s.strip() for s in only.split(",") if s.strip()}
    return [p for p in posts if p.slug in wanted]


def _fetch_listing(
    client: DevToClient | None,
) -> tuple[list[DevToArticleSummary] | None, str | None]:
    """Returns (summaries, None) on success; (None, error_detail) on failure."""
    if client is None:
        return [], None
    try:
        raw = client.list_my_articles()
    except CredentialError as exc:
        return None, str(exc)
    except (ListingError, RateLimitError, ServerError) as exc:
        return None, str(exc)

    summaries = [
        DevToArticleSummary(
            id=int(item["id"]),
            canonical_url_raw=item.get("canonical_url"),
            canonical_url_norm=normalize_canonical_url(item.get("canonical_url")),
            url=str(item.get("url", "")),
            published=bool(item.get("published", False)),
        )
        for item in raw
    ]
    return summaries, None


def run(argv: list[str], env: dict) -> int:
    args = _parse_args(argv)

    dry_run = bool(args.dry_run)
    api_key = (env.get("DEVTO_API_KEY") or "").strip()
    if not dry_run and not api_key:
        print(
            "pre-flight: dev.to credential missing — set DEVTO_API_KEY",
            flush=True,
        )
        return 1

    report = Report()

    try:
        baseurl, permalink_pattern = load_hugo_config(args.hugo_config)
    except (HugoConfigError, FileNotFoundError, OSError) as exc:
        print(f"pre-flight: hugo config error: {exc}", flush=True)
        return 1

    try:
        state = load_state(args.state_file)
    except StateError as exc:
        print(f"pre-flight: state file error: {exc}", flush=True)
        return 1

    try:
        posts = discover_posts(args.content_dir, baseurl, permalink_pattern)
    except (PostDiscoveryError, FileNotFoundError, OSError) as exc:
        print(f"pre-flight: content discovery error: {exc}", flush=True)
        return 1

    posts = _filter_only(posts, args.only)

    known_slugs = {p.slug for p in posts}
    for orphan in sorted(state.keys() - known_slugs):
        report.record_skip(orphan, "orphan (no matching post on disk)")

    # Under --dry-run we still need a client to fetch the listing (read-only), but only
    # if we have an api key. Without a key, fall back to an empty listing and proceed —
    # the adoption path is a no-op if no key is available for a dry run.
    client: DevToClient | None
    if not dry_run:
        client = DevToClient(api_key)
    elif api_key:
        client = DevToClient(api_key)
    else:
        client = None

    summaries, listing_error = _fetch_listing(client)
    if summaries is None:
        index: dict[str, list[int]] = {}
        article_lookup: dict[int, DevToArticleSummary] = {}
    else:
        index = build_canonical_index(summaries)
        article_lookup = {s.id: s for s in summaries}

    commit_sha = env.get("GITHUB_SHA", "local")
    now = datetime.now(UTC)

    state_modified = False

    for post in posts:
        result = classify_post(post, state, now)
        if result.action in (
            Classification.SKIP_DRAFT,
            Classification.SKIP_SCHEDULED,
            Classification.SKIP_UNCHANGED,
            Classification.SKIP_OPT_OUT,
        ):
            report.record_skip(post.slug, result.reason)
            continue

        if listing_error is not None:
            report.record_fail(
                post.slug, f"dev.to listing unavailable: {listing_error}"
            )
            continue

        refined = reconcile(post, state.get(post.slug), index, article_lookup)

        if refined.action is ReconciledAction.ADOPT:
            if dry_run:
                report.record_adopted(
                    post.slug, url=refined.devto_url or "", dry_run=True
                )
            else:
                update_entry(
                    state,
                    slug=post.slug,
                    devto_article_id=int(refined.devto_article_id),
                    devto_url=str(refined.devto_url or ""),
                    content_hash=post.content_hash,
                    commit_sha=commit_sha,
                )
                state_modified = True
                report.record_adopted(
                    post.slug, url=str(refined.devto_url or "")
                )
            continue

        if refined.action in (
            ReconciledAction.FAIL_MULTIPLE_MATCHES,
            ReconciledAction.FAIL_ID_MISMATCH,
        ):
            report.record_fail(post.slug, refined.reason)
            continue

        if dry_run:
            if refined.action is ReconciledAction.CREATE:
                report.record_created(post.slug, url="(dry-run)", dry_run=True)
            else:
                report.record_updated(post.slug, url="(dry-run)", dry_run=True)
            continue

        try:
            if refined.action is ReconciledAction.CREATE:
                resp = client.create_article(
                    title=post.title,
                    body_markdown=post.body_markdown_rewritten,
                    tags=post.tags,
                    canonical_url=post.canonical_url,
                )
                update_entry(
                    state,
                    slug=post.slug,
                    devto_article_id=int(resp["id"]),
                    devto_url=str(resp["url"]),
                    content_hash=post.content_hash,
                    commit_sha=commit_sha,
                )
                state_modified = True
                report.record_created(post.slug, url=str(resp["url"]))
            else:  # UPDATE
                entry = state[post.slug]
                article_id = int(entry["devto_article_id"])
                resp = client.update_article(
                    id=article_id,
                    title=post.title,
                    body_markdown=post.body_markdown_rewritten,
                    tags=post.tags,
                    canonical_url=post.canonical_url,
                )
                result_url = str(resp.get("url", entry.get("devto_url", "")))
                update_entry(
                    state,
                    slug=post.slug,
                    devto_article_id=article_id,
                    devto_url=result_url,
                    content_hash=post.content_hash,
                    commit_sha=commit_sha,
                )
                state_modified = True
                report.record_updated(post.slug, url=result_url)
        except ArticleMissingError:
            entry = state.get(post.slug, {})
            article_id = entry.get("devto_article_id", "?")
            report.record_fail(
                post.slug,
                f"dev.to article {article_id} not found — remove state entry for `{post.slug}` or recreate manually",
            )
        except CredentialError as exc:
            report.record_fail(post.slug, str(exc))
        except DevToError as exc:
            report.record_fail(post.slug, f"dev.to error: {exc}")

    stdout = report.render_stdout()
    sys.stdout.write(stdout)
    sys.stdout.flush()

    if env.get("GITHUB_STEP_SUMMARY"):
        _append_github_summary(report.render_github_summary(), env)

    if not dry_run and state_modified:
        save_state(args.state_file, state)

    return report.exit_code


def main() -> int:
    return run(sys.argv[1:], dict(os.environ))


if __name__ == "__main__":
    raise SystemExit(main())
