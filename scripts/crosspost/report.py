from __future__ import annotations

from dataclasses import dataclass, field

OK = "OK"
SKIP = "SKIP"
FAIL = "FAIL"

_OUTCOME_PAD = 6


@dataclass
class _Line:
    outcome: str
    slug: str
    text: str


@dataclass
class ReportCounts:
    created: int = 0
    updated: int = 0
    adopted: int = 0
    skipped: int = 0
    failed: int = 0

    @property
    def ok(self) -> int:
        return self.created + self.updated + self.adopted

    @property
    def total(self) -> int:
        return self.ok + self.skipped + self.failed


@dataclass
class Report:
    _lines: list[_Line] = field(default_factory=list)
    counts: ReportCounts = field(default_factory=ReportCounts)

    def record_created(self, slug: str, *, url: str, dry_run: bool = False) -> None:
        text = f"(dry-run) would create {url}" if dry_run else f"created draft {url}"
        self._lines.append(_Line(OK, slug, text))
        self.counts.created += 1

    def record_updated(self, slug: str, *, url: str, dry_run: bool = False) -> None:
        text = (
            f"(dry-run) would update {url}"
            if dry_run
            else f"updated (body hash changed) {url}"
        )
        self._lines.append(_Line(OK, slug, text))
        self.counts.updated += 1

    def record_adopted(self, slug: str, *, url: str, dry_run: bool = False) -> None:
        text = f"(dry-run) would adopt {url}" if dry_run else f"adopted {url}"
        self._lines.append(_Line(OK, slug, text))
        self.counts.adopted += 1

    def record_skip(self, slug: str, reason: str) -> None:
        self._lines.append(_Line(SKIP, slug, reason))
        self.counts.skipped += 1

    def record_fail(self, slug: str, reason: str) -> None:
        self._lines.append(_Line(FAIL, slug, reason))
        self.counts.failed += 1

    def _sorted(self) -> list[_Line]:
        return sorted(self._lines, key=lambda ln: ln.slug)

    @property
    def exit_code(self) -> int:
        return 1 if self.counts.failed else 0

    def _summary_body(self) -> str:
        c = self.counts
        return (
            f"{c.created} created, {c.updated} updated, {c.adopted} adopted, "
            f"{c.skipped} skipped, {c.failed} failed (of {c.total} candidates)"
        )

    def render_stdout(self) -> str:
        rows = [
            f"{ln.outcome:<{_OUTCOME_PAD}}{ln.slug}  {ln.text}"
            for ln in self._sorted()
        ]
        rows.append(f"-- summary: {self._summary_body()}")
        return "\n".join(rows) + "\n"

    def render_github_summary(self) -> str:
        rows = [
            "| Outcome | Slug | Detail |",
            "|---|---|---|",
        ]
        for ln in self._sorted():
            rows.append(f"| {ln.outcome} | {ln.slug} | {ln.text} |")
        rows.append("")
        rows.append(f"**Summary:** {self._summary_body()}")
        return "\n".join(rows) + "\n"
