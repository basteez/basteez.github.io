from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .changeset import resolve_touched_posts
from .devto import (
    AuthRejected,
    DevtoClient,
    NonRetryable,
    RetryExhausted,
)
from .frontmatter import FrontmatterError, parse as parse_frontmatter
from .models import PostFile, PostOutcome, RunSummary
from .reconcile import build_title_index
from .report import format_outcome, format_step_summary, format_summary


def _log(message: str) -> None:
    print(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.crosspost",
        description="Mirror new Hugo posts to dev.to as drafts.",
    )
    parser.add_argument("--before", required=True, help="Start (exclusive) SHA.")
    parser.add_argument("--after", required=True, help="End (inclusive) SHA.")
    parser.add_argument(
        "--post-dir",
        default="content/post",
        help="Post directory root (default: content/post).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip POST /articles calls; log what would happen.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (default: cwd). For tests.",
    )
    return parser


def _maybe_write_step_summary(summary: RunSummary, before: str, after: str) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    text = format_step_summary(summary, before, after)
    with open(target, "a", encoding="utf-8") as fp:
        fp.write(text)


def _load_post(path: str, repo_root: Path) -> tuple[Optional[PostFile], Optional[str]]:
    try:
        text = (repo_root / path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, f'file not found: {path}'
    try:
        post = parse_frontmatter(text, path=path)
    except FrontmatterError as exc:
        return None, str(exc)
    return post, None


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()
    summary = RunSummary()

    api_key = os.environ.get("DEVTO_API_KEY", "")
    if not api_key:
        summary.global_failure = "missing DEVTO_API_KEY"
        _log(format_summary(summary, args.before, args.after))
        print(f"global_failure: {summary.global_failure}", file=sys.stderr)
        return 1

    if args.before == args.after:
        _log("nothing to do: before == after")
        _log(format_summary(summary, args.before, args.after))
        return 0

    entries = resolve_touched_posts(args.before, args.after, cwd=repo_root)

    # Stage 1: load and eligibility-filter.
    publishable: list[PostFile] = []
    for entry in entries:
        post, err = _load_post(entry.path, repo_root)
        if post is None:
            summary.outcomes.append(
                PostOutcome(
                    path=entry.path,
                    title=None,
                    result="skipped_invalid",
                    detail=err or "unknown error",
                )
            )
            continue

        if post.title is None:
            summary.outcomes.append(
                PostOutcome(
                    path=entry.path,
                    title=None,
                    result="skipped_invalid",
                    detail="missing title",
                )
            )
            continue

        if post.frontmatter.get("draft") is not False:
            summary.outcomes.append(
                PostOutcome(
                    path=entry.path,
                    title=post.title,
                    result="skipped_draft",
                    detail="draft=true",
                )
            )
            continue

        publishable.append(post)

    # Short-circuit if nothing publishable — skip network entirely.
    if not publishable and not entries:
        _log(
            f"no candidate post files in push range {args.before}..{args.after}"
        )
        _log(format_summary(summary, args.before, args.after))
        _maybe_write_step_summary(summary, args.before, args.after)
        return 0

    client = DevtoClient(api_key=api_key)

    # Stage 2: fetch existing articles to build the dedup index.
    articles: list = []
    if publishable:
        try:
            articles.extend(client.list_published())
            articles.extend(client.list_unpublished())
        except AuthRejected as exc:
            summary.global_failure = f"auth rejected while listing articles: {exc}"
        except RetryExhausted as exc:
            summary.global_failure = f"list-articles exhausted retries: {exc}"

    if summary.global_failure is not None:
        for outcome in summary.outcomes:
            _log(format_outcome(outcome))
        _log(format_summary(summary, args.before, args.after))
        _maybe_write_step_summary(summary, args.before, args.after)
        print(f"global_failure: {summary.global_failure}", file=sys.stderr)
        return 1

    index = build_title_index(articles)

    # Stage 3: create drafts (or simulate in dry-run).
    create_attempts = 0
    create_successes = 0
    create_retry_exhausted = 0

    for post in publishable:
        title = post.title or ""
        if index.contains(title):
            summary.outcomes.append(
                PostOutcome(
                    path=post.path,
                    title=title,
                    result="skipped_exists",
                    detail="title matches existing dev.to article",
                )
            )
            continue

        if args.dry_run:
            summary.outcomes.append(
                PostOutcome(
                    path=post.path,
                    title=title,
                    result="drafted",
                    detail="(dry-run)",
                )
            )
            index.add(title)
            continue

        create_attempts += 1
        try:
            created = client.create_article(title=title, body_markdown=post.body)
        except AuthRejected as exc:
            summary.global_failure = f"auth rejected on create: {exc}"
            break
        except NonRetryable as exc:
            summary.outcomes.append(
                PostOutcome(
                    path=post.path,
                    title=title,
                    result="error",
                    detail=str(exc),
                )
            )
            continue
        except RetryExhausted as exc:
            create_retry_exhausted += 1
            summary.outcomes.append(
                PostOutcome(
                    path=post.path,
                    title=title,
                    result="error",
                    detail=f"retry exhausted: {exc}",
                )
            )
            continue

        create_successes += 1
        summary.outcomes.append(
            PostOutcome(
                path=post.path,
                title=title,
                result="drafted",
                detail=f"devto_id={created.id}",
            )
        )
        index.add(title)

    # Promote "all creates failed" to global failure (US3 / research §R9).
    if (
        summary.global_failure is None
        and create_attempts > 0
        and create_successes == 0
        and create_retry_exhausted > 0
    ):
        summary.global_failure = (
            f"all {create_attempts} create attempts exhausted retries"
        )

    for outcome in summary.outcomes:
        _log(format_outcome(outcome))
    if not entries:
        _log(
            f"no candidate post files in push range {args.before}..{args.after}"
        )
    _log(format_summary(summary, args.before, args.after))
    _maybe_write_step_summary(summary, args.before, args.after)
    if summary.global_failure is not None:
        print(f"global_failure: {summary.global_failure}", file=sys.stderr)
        return 1
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
