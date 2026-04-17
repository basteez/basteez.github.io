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
class Report:
    _lines: list[_Line] = field(default_factory=list)

    def record_ok(self, slug: str, *, url: str, detail: str) -> None:
        self._lines.append(_Line(OK, slug, f"{detail} {url}".strip()))

    def record_skip(self, slug: str, reason: str) -> None:
        self._lines.append(_Line(SKIP, slug, reason))

    def record_fail(self, slug: str, reason: str) -> None:
        self._lines.append(_Line(FAIL, slug, reason))

    def _sorted(self) -> list[_Line]:
        return sorted(self._lines, key=lambda ln: ln.slug)

    @property
    def counts(self) -> tuple[int, int, int]:
        ok = sum(1 for ln in self._lines if ln.outcome == OK)
        skip = sum(1 for ln in self._lines if ln.outcome == SKIP)
        fail = sum(1 for ln in self._lines if ln.outcome == FAIL)
        return ok, skip, fail

    @property
    def exit_code(self) -> int:
        _, _, fail = self.counts
        return 1 if fail else 0

    def render_stdout(self) -> str:
        rows = []
        for ln in self._sorted():
            rows.append(f"{ln.outcome:<{_OUTCOME_PAD}}{ln.slug}  {ln.text}")
        ok, skip, fail = self.counts
        total = ok + skip + fail
        rows.append(
            f"-- summary: {ok} ok, {skip} skipped, {fail} failed (of {total} candidates)"
        )
        return "\n".join(rows) + "\n"

    def render_github_summary(self) -> str:
        rows = [
            "| Outcome | Slug | Detail |",
            "|---|---|---|",
        ]
        for ln in self._sorted():
            rows.append(f"| {ln.outcome} | {ln.slug} | {ln.text} |")
        ok, skip, fail = self.counts
        total = ok + skip + fail
        rows.append("")
        rows.append(f"**Summary:** {ok} ok, {skip} skipped, {fail} failed (of {total} candidates)")
        return "\n".join(rows) + "\n"
