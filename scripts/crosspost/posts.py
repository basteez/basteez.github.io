from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import parse
from .models import PostFile


_SINGLE_FILE = re.compile(r"^content/post/[^/]+\.md$")
_BUNDLE = re.compile(r"^content/post/[^/]+/index\.md$")


def is_post_path(path: str) -> bool:
    if _SINGLE_FILE.match(path):
        return True
    if _BUNDLE.match(path):
        return True
    return False


def load_post(path: str, root: Path | str | None = None) -> PostFile:
    base = Path(root) if root is not None else Path.cwd()
    text = (base / path).read_text(encoding="utf-8")
    return parse(text, path=path)
