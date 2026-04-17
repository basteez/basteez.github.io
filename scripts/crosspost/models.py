from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


PostResult = Literal[
    "skipped_exists",
    "drafted",
    "skipped_draft",
    "skipped_rename",
    "skipped_invalid",
    "error",
]


@dataclass(frozen=True)
class ChangesetEntry:
    path: str
    status: str


@dataclass
class PostFile:
    path: str
    frontmatter: dict[str, Any]
    body: str

    @property
    def title(self) -> Optional[str]:
        value = self.frontmatter.get("title")
        if isinstance(value, str) and value.strip():
            return value
        return None

    @property
    def is_publishable(self) -> bool:
        return self.frontmatter.get("draft") is False and self.title is not None


@dataclass(frozen=True)
class DevtoArticle:
    id: int
    title: str
    published: bool
    url: str


@dataclass
class TitleIndex:
    normalized_set: set[str] = field(default_factory=set)

    def contains(self, title: str) -> bool:
        from .reconcile import normalize_title

        return normalize_title(title) in self.normalized_set

    def add(self, title: str) -> None:
        from .reconcile import normalize_title

        self.normalized_set.add(normalize_title(title))


@dataclass
class PostOutcome:
    path: str
    title: Optional[str]
    result: PostResult
    detail: str = ""


@dataclass
class RunSummary:
    outcomes: list[PostOutcome] = field(default_factory=list)
    global_failure: Optional[str] = None

    @property
    def exit_code(self) -> int:
        return 0 if self.global_failure is None else 1
