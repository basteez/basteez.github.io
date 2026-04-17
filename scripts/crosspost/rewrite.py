from __future__ import annotations

import re
from urllib.parse import urljoin

_SKIP_PREFIXES = ("http://", "https://", "data:", "mailto:", "#")

_MD_IMG = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)(\))")
_HTML_SRC = re.compile(r'(<img\b[^>]*?\bsrc\s*=\s*")([^"]+)(")', re.IGNORECASE)


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def _resolve(target: str, post_base_url: str, site_base_url: str) -> str:
    if target.startswith(_SKIP_PREFIXES):
        return target
    if target.startswith("/"):
        return urljoin(_ensure_trailing_slash(site_base_url), target.lstrip("/"))
    cleaned = target[2:] if target.startswith("./") else target
    return urljoin(_ensure_trailing_slash(post_base_url), cleaned)


def rewrite_body(markdown: str, post_base_url: str, site_base_url: str) -> str:
    def _md(m: re.Match) -> str:
        prefix, target, suffix = m.group(1), m.group(2), m.group(3)
        return prefix + _resolve(target, post_base_url, site_base_url) + suffix

    def _html(m: re.Match) -> str:
        prefix, target, suffix = m.group(1), m.group(2), m.group(3)
        return prefix + _resolve(target, post_base_url, site_base_url) + suffix

    out = _MD_IMG.sub(_md, markdown)
    out = _HTML_SRC.sub(_html, out)
    return out
