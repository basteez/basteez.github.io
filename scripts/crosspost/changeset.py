from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from .models import ChangesetEntry
from .posts import is_post_path


ZERO_SHA = "0" * 40
_log = logging.getLogger(__name__)


def _git(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _diff(
    range_spec: str, cwd: Optional[Path], diff_filter: str
) -> list[ChangesetEntry]:
    result = _git(
        "diff", "--name-status", f"--diff-filter={diff_filter}", range_spec, cwd=cwd
    )
    entries: list[ChangesetEntry] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        if status.startswith("R") or status.startswith("C"):
            continue
        if not is_post_path(path):
            continue
        entries.append(ChangesetEntry(path=path, status=status))
    return entries


def _diff_touched(
    range_spec: str, cwd: Optional[Path]
) -> list[ChangesetEntry]:
    return _diff(range_spec, cwd, "AM")


def _merge_base(a: str, b: str, cwd: Optional[Path]) -> Optional[str]:
    try:
        result = _git("merge-base", a, b, cwd=cwd)
    except subprocess.CalledProcessError:
        return None
    return result.stdout.strip() or None


def _commits_in_range(
    range_spec: str, cwd: Optional[Path]
) -> list[str]:
    result = _git("rev-list", range_spec, cwd=cwd)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def resolve_touched_posts(
    before: str,
    after: str,
    cwd: Optional[Path | str] = None,
) -> list[ChangesetEntry]:
    """Return the union of touched (added or modified) post files in before..after.

    - First-push (before == ZERO_SHA) → diff after^..after only.
    - before == after → empty range.
    - Force-push (no merge-base) → fall back to after^..after.
    - Renames (R*) and copies (C*) are excluded.
    - Only paths matching is_post_path() are returned.
    """
    return _resolve(before, after, cwd, _diff_touched)


def _resolve(
    before: str,
    after: str,
    cwd: Optional[Path | str],
    diff_fn,
) -> list[ChangesetEntry]:
    cwd_path = Path(cwd) if cwd is not None else None

    if before == after:
        return []

    if before == ZERO_SHA:
        range_spec = f"{after}^..{after}"
        return _uniq(diff_fn(range_spec, cwd_path))

    mb = _merge_base(before, after, cwd_path)
    if mb is None:
        _log.warning(
            "no merge-base between %s and %s; falling back to %s^..%s",
            before,
            after,
            after,
            after,
        )
        range_spec = f"{after}^..{after}"
        return _uniq(diff_fn(range_spec, cwd_path))

    aggregate = diff_fn(f"{before}..{after}", cwd_path)

    per_commit: list[ChangesetEntry] = []
    for sha in _commits_in_range(f"{before}..{after}", cwd_path):
        per_commit.extend(diff_fn(f"{sha}^..{sha}", cwd_path))

    return _uniq(aggregate + per_commit)


def _uniq(entries: list[ChangesetEntry]) -> list[ChangesetEntry]:
    seen: set[str] = set()
    out: list[ChangesetEntry] = []
    for e in entries:
        if e.path in seen:
            continue
        seen.add(e.path)
        out.append(e)
    return out
