from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from scripts.crosspost.frontmatter import parse_frontmatter
from scripts.crosspost.rewrite import rewrite_body


def _filename_date(path: Path) -> datetime | None:
    base = path.parent.name if path.name == "index.md" else path.stem
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", base)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=UTC)
    except ValueError:
        return None

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
_TAG_NORMALIZE_RE = re.compile(r"[^a-z0-9]")
DEVTO_TAG_LIMIT = 4


class HugoConfigError(Exception):
    pass


class PostDiscoveryError(Exception):
    pass


@dataclass
class BlogPost:
    source_path: Path
    slug: str
    title: str
    date: datetime
    tags: list[str]
    categories: list[str]
    is_draft: bool
    crosspost_enabled: bool
    body_markdown_raw: str
    body_markdown_rewritten: str
    canonical_url: str
    content_hash: str


def load_hugo_config(path: str | Path) -> tuple[str, str]:
    p = Path(path)
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise HugoConfigError(f"invalid hugo config YAML at {p}: {exc}") from exc
    baseurl = data.get("baseurl")
    if not isinstance(baseurl, str) or not baseurl.strip():
        raise HugoConfigError("hugo config missing 'baseurl'")
    permalinks = data.get("permalinks")
    if not isinstance(permalinks, dict) or "post" not in permalinks:
        raise HugoConfigError("hugo config missing 'permalinks.post'")
    return baseurl.rstrip("/"), str(permalinks["post"])


def _raw_slug(source_path: Path) -> str:
    if source_path.name == "index.md":
        base = source_path.parent.name
    else:
        base = source_path.stem
    return _DATE_PREFIX_RE.sub("", base)


def derive_slug(source_path: Path, frontmatter_slug: str | None) -> str:
    candidate = frontmatter_slug if frontmatter_slug else _raw_slug(source_path)
    if not _SLUG_RE.match(candidate):
        raise PostDiscoveryError(
            f"malformed slug {candidate!r} from {source_path} — must match {_SLUG_RE.pattern}"
        )
    return candidate


def _render_canonical(site_base_url: str, permalink_pattern: str, slug: str) -> str:
    path = permalink_pattern.replace(":slug", slug)
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return f"{site_base_url.rstrip('/')}{path}"


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        normalized = _TAG_NORMALIZE_RE.sub("", t.lower())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
        if len(out) == DEVTO_TAG_LIMIT:
            break
    return out


def _content_hash(title: str, tags: list[str], canonical_url: str, body: str) -> str:
    h = hashlib.sha256()
    h.update(title.encode("utf-8"))
    h.update(b"\x1f")
    for tag in sorted(tags):
        h.update(tag.encode("utf-8"))
        h.update(b"\x1e")
    h.update(b"\x1f")
    h.update(canonical_url.encode("utf-8"))
    h.update(b"\x1f")
    h.update(body.encode("utf-8"))
    return h.hexdigest()


def _iter_markdown_files(content_dir: Path):
    yield from sorted(content_dir.rglob("*.md"))


def discover_posts(
    content_dir: str | Path,
    site_base_url: str,
    permalink_pattern: str,
) -> list[BlogPost]:
    content_dir = Path(content_dir)
    if not content_dir.exists():
        raise PostDiscoveryError(f"content dir not found: {content_dir}")
    posts: dict[str, BlogPost] = {}
    for md_path in _iter_markdown_files(content_dir):
        raw = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw, fallback_date=_filename_date(md_path))
        slug = derive_slug(md_path, fm.slug)
        if slug in posts:
            raise PostDiscoveryError(
                f"duplicate slug {slug!r}: {posts[slug].source_path} and {md_path}"
            )
        canonical_url = _render_canonical(site_base_url, permalink_pattern, slug)
        post_base_url = canonical_url
        body_rewritten = rewrite_body(body, post_base_url, site_base_url)
        normalized_tags = normalize_tags(fm.tags)
        content_hash = _content_hash(fm.title, normalized_tags, canonical_url, body_rewritten)
        posts[slug] = BlogPost(
            source_path=md_path,
            slug=slug,
            title=fm.title,
            date=fm.date,
            tags=normalized_tags,
            categories=fm.categories,
            is_draft=fm.is_draft,
            crosspost_enabled=fm.crosspost_enabled,
            body_markdown_raw=body,
            body_markdown_rewritten=body_rewritten,
            canonical_url=canonical_url,
            content_hash=content_hash,
        )
    return sorted(posts.values(), key=lambda p: p.slug)
