from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.crosspost.state import StateError, load_state, save_state, update_entry


def test_load_missing_file_returns_empty_dict(tmp_path: Path):
    assert load_state(tmp_path / "nope.json") == {}


def test_load_malformed_json_raises(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text("{not json")
    with pytest.raises(StateError):
        load_state(p)


def test_save_writes_sorted_keys_two_space_indent_trailing_newline(tmp_path: Path):
    p = tmp_path / "state.json"
    data = {
        "zzz": {"devto_article_id": 2},
        "aaa": {"devto_article_id": 1},
    }
    save_state(p, data)
    text = p.read_text()
    assert text.endswith("\n")
    keys_in_order = [line.strip().split('"')[1] for line in text.splitlines() if line.startswith('  "')]
    assert keys_in_order == ["aaa", "zzz"]
    assert '  "aaa"' in text


def test_save_no_write_when_content_unchanged(tmp_path: Path):
    p = tmp_path / "state.json"
    data = {"a": {"devto_article_id": 1}}
    save_state(p, data)
    mtime_first = p.stat().st_mtime_ns
    save_state(p, data)
    mtime_second = p.stat().st_mtime_ns
    assert mtime_first == mtime_second


def test_save_writes_when_content_changes(tmp_path: Path):
    p = tmp_path / "state.json"
    save_state(p, {"a": {"devto_article_id": 1}})
    save_state(p, {"a": {"devto_article_id": 2}})
    loaded = json.loads(p.read_text())
    assert loaded["a"]["devto_article_id"] == 2


def test_save_is_atomic_no_partial_file(tmp_path: Path):
    p = tmp_path / "state.json"
    data = {"slug": {"devto_article_id": 7}}
    save_state(p, data)
    assert p.exists()
    assert json.loads(p.read_text()) == data
    assert not list(tmp_path.glob("*.tmp"))


def test_update_entry_adds_new(tmp_path: Path):
    state: dict = {}
    updated = update_entry(
        state,
        slug="hello",
        devto_article_id=123,
        devto_url="https://dev.to/u/hello",
        content_hash="abc",
        commit_sha="deadbeef",
    )
    assert updated["hello"]["devto_article_id"] == 123
    assert updated["hello"]["created_at"] == updated["hello"]["updated_at"]
    assert updated["hello"]["last_body_sha256"] == "abc"
    assert updated["hello"]["last_synced_commit"] == "deadbeef"


def test_update_entry_preserves_created_at_on_update(tmp_path: Path):
    state: dict = {}
    first = update_entry(
        state,
        slug="hello",
        devto_article_id=123,
        devto_url="https://dev.to/u/hello",
        content_hash="abc",
        commit_sha="commit1",
    )
    created_at = first["hello"]["created_at"]

    second = update_entry(
        first,
        slug="hello",
        devto_article_id=123,
        devto_url="https://dev.to/u/hello",
        content_hash="def",
        commit_sha="commit2",
    )
    assert second["hello"]["created_at"] == created_at
    assert second["hello"]["updated_at"] != created_at or second["hello"]["last_body_sha256"] == "def"
    assert second["hello"]["last_body_sha256"] == "def"
    assert second["hello"]["last_synced_commit"] == "commit2"


def test_roundtrip_preserves_all_fields(tmp_path: Path):
    p = tmp_path / "state.json"
    entry = {
        "slug-a": {
            "devto_article_id": 1,
            "devto_url": "https://dev.to/u/a",
            "last_synced_commit": "abcd1234",
            "last_body_sha256": "f" * 64,
            "created_at": "2026-04-17T10:22:15Z",
            "updated_at": "2026-04-17T10:22:15Z",
        }
    }
    save_state(p, entry)
    assert load_state(p) == entry
