from __future__ import annotations

from .models import PostOutcome, RunSummary


def format_outcome(outcome: PostOutcome) -> str:
    path = outcome.path
    title = outcome.title
    tag = f"[{outcome.result}]"
    detail = outcome.detail

    if outcome.result == "drafted":
        suffix = f'title="{title}"'
        if detail:
            suffix = f"{suffix} {detail}"
        return f"{tag} {path} — {suffix}"
    if outcome.result == "skipped_exists":
        return f'{tag} {path} — title="{title}"'
    if outcome.result == "skipped_draft":
        return f"{tag} {path} — {detail or 'draft=true'}"
    if outcome.result == "skipped_invalid":
        return f'{tag} {path} — reason="{detail}"' if detail else f"{tag} {path}"
    if outcome.result == "skipped_rename":
        return f'{tag} {path} — reason="{detail or "git reports rename"}"'
    if outcome.result == "error":
        return f"{tag} {path} — {detail}" if detail else f"{tag} {path}"
    return f"{tag} {path}"


_STEP_SUMMARY_HEADER = (
    "| File | Title | Result | Detail |\n"
    "| ---- | ----- | ------ | ------ |\n"
)


def _escape_cell(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def format_step_summary(summary: RunSummary, before: str, after: str) -> str:
    del before, after
    rows: list[str] = []
    for outcome in summary.outcomes:
        title_cell = _escape_cell(outcome.title)
        detail_cell = _escape_cell(outcome.detail)
        rows.append(
            f"| `{outcome.path}` | {title_cell} | {outcome.result} | {detail_cell} |"
        )
    if not rows:
        return _STEP_SUMMARY_HEADER
    return _STEP_SUMMARY_HEADER + "\n".join(rows) + "\n"


def format_summary(summary: RunSummary, before: str, after: str) -> str:
    drafted = sum(1 for o in summary.outcomes if o.result == "drafted")
    errors = sum(1 for o in summary.outcomes if o.result == "error")
    skipped = sum(
        1
        for o in summary.outcomes
        if o.result
        in ("skipped_exists", "skipped_draft", "skipped_invalid", "skipped_rename")
    )
    return (
        f"summary: drafted={drafted} skipped={skipped} errors={errors} "
        f"range={before}..{after}"
    )
