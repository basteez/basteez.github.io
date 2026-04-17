from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path


class StateError(Exception):
    pass


def load_state(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise StateError(f"malformed state JSON at {p}: {exc}") from exc


def _serialize(data: dict) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def save_state(path: str | Path, data: dict) -> bool:
    p = Path(path)
    new_text = _serialize(data)
    if p.exists() and p.read_text() == new_text:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new_text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)
    return True


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def update_entry(
    state: dict,
    slug: str,
    devto_article_id: int,
    devto_url: str,
    content_hash: str,
    commit_sha: str,
) -> dict:
    existing = state.get(slug, {})
    created_at = existing.get("created_at") or _now_iso()
    updated_at = _now_iso()
    state[slug] = {
        "devto_article_id": devto_article_id,
        "devto_url": devto_url,
        "last_synced_commit": commit_sha,
        "last_body_sha256": content_hash,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    return state
