from __future__ import annotations

from scripts.crosspost.report import Report


def test_created_line_includes_devto_url():
    r = Report()
    r.record_created("hello", url="https://dev.to/u/hello")
    out = r.render_stdout()
    assert "OK" in out
    assert "hello" in out
    assert "created draft" in out
    assert "https://dev.to/u/hello" in out


def test_updated_line_format():
    r = Report()
    r.record_updated("hello", url="https://dev.to/u/hello")
    out = r.render_stdout()
    assert "updated (body hash changed)" in out
    assert "https://dev.to/u/hello" in out


def test_adopted_line_format_no_leading_created_or_updated_word():
    r = Report()
    r.record_adopted("hello", url="https://dev.to/u/hello-xxxx")
    out = r.render_stdout()
    lines = [ln for ln in out.splitlines() if ln.startswith("OK")]
    assert len(lines) == 1
    line = lines[0]
    assert "adopted https://dev.to/u/hello-xxxx" in line
    assert "created" not in line
    assert "updated" not in line


def test_adopted_counter_is_distinct_from_created_and_updated():
    r = Report()
    r.record_created("a", url="u1")
    r.record_updated("b", url="u2")
    r.record_adopted("c", url="u3")
    assert r.counts.created == 1
    assert r.counts.updated == 1
    assert r.counts.adopted == 1


def test_adopted_dry_run_line_format():
    r = Report()
    r.record_adopted("hello", url="https://dev.to/u/hello-xxxx", dry_run=True)
    out = r.render_stdout()
    assert "(dry-run) would adopt https://dev.to/u/hello-xxxx" in out


def test_adopted_line_starts_with_OK_prefix():
    r = Report()
    r.record_adopted("hello", url="https://dev.to/u/hello")
    out = r.render_stdout()
    lines = [ln for ln in out.splitlines() if ln.startswith("OK")]
    assert len(lines) == 1


def test_skip_reasons_variants():
    r = Report()
    r.record_skip("a", "draft")
    r.record_skip("b", "opt-out (crosspost: false)")
    r.record_skip("c", "unchanged")
    r.record_skip("d", "scheduled for 2026-05-01T00:00:00+00:00")
    out = r.render_stdout()
    assert "draft" in out
    assert "opt-out (crosspost: false)" in out
    assert "unchanged" in out
    assert "scheduled for 2026-05-01T00:00:00+00:00" in out


def test_fail_line_emits_reason_and_nonzero_exit():
    r = Report()
    r.record_fail("broken", "dev.to article 9999 not found")
    assert "FAIL" in r.render_stdout()
    assert r.exit_code == 1


def test_slug_sorted_output():
    r = Report()
    r.record_created("zeta", url="u")
    r.record_skip("alpha", "draft")
    r.record_fail("mid", "boom")
    out_lines = [
        ln for ln in r.render_stdout().splitlines() if ln.startswith(("OK", "SKIP", "FAIL"))
    ]
    slugs = [ln.split()[1] for ln in out_lines]
    assert slugs == ["alpha", "mid", "zeta"]


def test_summary_footer_exact_format():
    r = Report()
    r.record_created("a", url="u")
    r.record_updated("b", url="u")
    r.record_updated("c", url="u")
    r.record_adopted("d", url="u")
    r.record_skip("e", "draft")
    r.record_skip("f", "opt-out")
    r.record_skip("g", "unchanged")
    out = r.render_stdout()
    assert (
        "-- summary: 1 created, 2 updated, 1 adopted, 3 skipped, 0 failed (of 7 candidates)"
        in out
    )


def test_exit_code_zero_when_no_fails():
    r = Report()
    r.record_created("a", url="u")
    r.record_skip("b", "draft")
    assert r.exit_code == 0


def test_github_summary_markdown_table_for_adopted():
    r = Report()
    r.record_adopted("a", url="https://dev.to/u/a-xxxx")
    md = r.render_github_summary()
    assert "| OK | a | adopted https://dev.to/u/a-xxxx |" in md


def test_github_summary_markdown_mirrors_stdout_summary():
    r = Report()
    r.record_created("a", url="u")
    r.record_updated("b", url="u")
    r.record_adopted("c", url="u")
    r.record_skip("d", "draft")
    md = r.render_github_summary()
    assert (
        "**Summary:** 1 created, 1 updated, 1 adopted, 1 skipped, 0 failed (of 4 candidates)"
        in md
    )
