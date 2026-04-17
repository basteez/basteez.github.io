from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time

import yaml


class FrontmatterError(Exception):
    pass


@dataclass
class Frontmatter:
    title: str
    date: datetime
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    is_draft: bool = False
    crosspost_enabled: bool = True
    slug: str | None = None


def _split(content: str) -> tuple[str, str]:
    if not content.startswith("---"):
        raise FrontmatterError("missing opening '---' frontmatter fence")
    rest = content[3:]
    if rest.startswith("\n"):
        rest = rest[1:]
    end = rest.find("\n---")
    if end == -1:
        raise FrontmatterError("missing closing '---' frontmatter fence")
    yaml_text = rest[:end]
    body = rest[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    return yaml_text, body


def _coerce_date(raw) -> datetime:
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=UTC)
        return raw
    if isinstance(raw, date):
        return datetime.combine(raw, time.min, tzinfo=UTC)
    if isinstance(raw, str):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise FrontmatterError(f"unparseable date: {raw!r}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    raise FrontmatterError(f"unsupported date type: {type(raw).__name__}")


def parse_frontmatter(
    content: str, fallback_date: datetime | None = None
) -> tuple[Frontmatter, str]:
    yaml_text, body = _split(content)
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter must be a mapping")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise FrontmatterError("missing or empty 'title' in frontmatter")

    if "date" in data:
        parsed_date = _coerce_date(data["date"])
    elif fallback_date is not None:
        parsed_date = fallback_date if fallback_date.tzinfo else fallback_date.replace(tzinfo=UTC)
    else:
        raise FrontmatterError("missing 'date' in frontmatter")

    tags_raw = data.get("tags") or []
    if not isinstance(tags_raw, list):
        raise FrontmatterError("'tags' must be a list")
    tags = [str(t) for t in tags_raw]

    cats_raw = data.get("categories") or []
    if not isinstance(cats_raw, list):
        raise FrontmatterError("'categories' must be a list")
    categories = [str(c) for c in cats_raw]

    is_draft = bool(data.get("draft", False))
    crosspost_enabled = bool(data.get("crosspost", True))

    slug_override = data.get("slug")
    if slug_override is not None and not isinstance(slug_override, str):
        raise FrontmatterError("'slug' must be a string")

    return (
        Frontmatter(
            title=title,
            date=parsed_date,
            tags=tags,
            categories=categories,
            is_draft=is_draft,
            crosspost_enabled=crosspost_enabled,
            slug=slug_override,
        ),
        body,
    )
