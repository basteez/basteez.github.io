from __future__ import annotations

import yaml

from .models import PostFile


class FrontmatterError(ValueError):
    """Raised when a post file's frontmatter cannot be parsed."""


def parse(text: str, path: str = "<string>") -> PostFile:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise FrontmatterError(f"{path}: missing leading frontmatter delimiter")

    # Split off the opening '---' line.
    _, _, rest = text.partition("\n")
    terminator_marker = "\n---"
    # Find the closing '---' that appears on its own line.
    lines = rest.splitlines(keepends=True)
    terminator_index = None
    consumed = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        if stripped == "---":
            terminator_index = i
            break
        consumed += len(line)
    del terminator_marker
    if terminator_index is None:
        raise FrontmatterError(f"{path}: missing closing '---' delimiter")

    yaml_block = "".join(lines[:terminator_index])
    body = "".join(lines[terminator_index + 1 :])

    try:
        data = yaml.safe_load(yaml_block) if yaml_block.strip() else {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"{path}: invalid YAML frontmatter: {exc}") from exc

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise FrontmatterError(
            f"{path}: frontmatter must be a mapping, got {type(data).__name__}"
        )

    return PostFile(path=path, frontmatter=data, body=body)
