from __future__ import annotations

from scripts.crosspost.models import PostOutcome, RunSummary
from scripts.crosspost.report import format_step_summary


HEADER = "| File | Title | Result | Detail |\n| ---- | ----- | ------ | ------ |\n"


def test_format_step_summary_empty_outcomes_returns_header_only():
    summary = RunSummary(outcomes=[], global_failure=None)
    out = format_step_summary(summary, "a" * 40, "b" * 40)
    assert out == HEADER


def test_format_step_summary_row_per_outcome():
    summary = RunSummary(
        outcomes=[
            PostOutcome(
                path="content/post/a.md",
                title="Alpha",
                result="drafted",
                detail="devto_id=1",
            ),
            PostOutcome(
                path="content/post/b.md",
                title="Beta",
                result="skipped_exists",
                detail="title matches existing dev.to article",
            ),
            PostOutcome(
                path="content/post/c.md",
                title="Gamma",
                result="skipped_draft",
                detail="draft=true",
            ),
        ],
        global_failure=None,
    )
    out = format_step_summary(summary, "x", "y")
    lines = out.splitlines()
    assert lines[0] == "| File | Title | Result | Detail |"
    assert lines[1] == "| ---- | ----- | ------ | ------ |"
    assert lines[2] == (
        "| `content/post/a.md` | Alpha | drafted | devto_id=1 |"
    )
    assert lines[3] == (
        "| `content/post/b.md` | Beta | skipped_exists | "
        "title matches existing dev.to article |"
    )
    assert lines[4] == (
        "| `content/post/c.md` | Gamma | skipped_draft | draft=true |"
    )


def test_format_step_summary_escapes_pipes_in_cells():
    summary = RunSummary(
        outcomes=[
            PostOutcome(
                path="content/post/p.md",
                title="A | piped | title",
                result="drafted",
                detail="extra | with | bars",
            )
        ],
        global_failure=None,
    )
    out = format_step_summary(summary, "x", "y")
    row = out.splitlines()[2]
    assert r"A \| piped \| title" in row
    assert r"extra \| with \| bars" in row
    # After stripping escaped pipes, only the 5 column separators remain.
    assert row.replace(r"\|", "").count("|") == 5


def test_format_step_summary_empty_title_and_detail_render_as_empty_cells():
    summary = RunSummary(
        outcomes=[
            PostOutcome(
                path="content/post/p.md",
                title=None,
                result="skipped_invalid",
                detail="",
            )
        ],
        global_failure=None,
    )
    out = format_step_summary(summary, "x", "y")
    row = out.splitlines()[2]
    assert row == "| `content/post/p.md` |  | skipped_invalid |  |"
