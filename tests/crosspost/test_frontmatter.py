from __future__ import annotations

from datetime import UTC, datetime
from textwrap import dedent

import pytest

from scripts.crosspost.frontmatter import Frontmatter, FrontmatterError, parse_frontmatter


def test_splits_yaml_from_body():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        ---

        Body goes here.
        """
    )
    fm, body = parse_frontmatter(raw)
    assert isinstance(fm, Frontmatter)
    assert body.strip() == "Body goes here."


def test_required_title_missing_raises():
    raw = dedent(
        """\
        ---
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    with pytest.raises(FrontmatterError, match="title"):
        parse_frontmatter(raw)


def test_required_date_missing_raises():
    raw = dedent(
        """\
        ---
        title: "Hello"
        ---

        body
        """
    )
    with pytest.raises(FrontmatterError, match="date"):
        parse_frontmatter(raw)


def test_tags_default_to_empty_list():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.tags == []


def test_draft_default_false():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.is_draft is False


def test_crosspost_default_true():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.crosspost_enabled is True


def test_crosspost_false_opt_out():
    raw = dedent(
        """\
        ---
        title: "Private"
        date: 2026-04-17T10:00:00Z
        crosspost: false
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.crosspost_enabled is False


def test_draft_true_marks_draft():
    raw = dedent(
        """\
        ---
        title: "WIP"
        date: 2026-04-17T10:00:00Z
        draft: true
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.is_draft is True


def test_tags_and_categories_parsed():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        tags:
          - hugo
          - golang
        categories:
          - dev
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert fm.tags == ["hugo", "golang"]
    assert fm.categories == ["dev"]


def test_date_parsed_as_datetime_with_tz():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert isinstance(fm.date, datetime)
    assert fm.date.tzinfo is not None
    assert fm.date == datetime(2026, 4, 17, 10, 0, 0, tzinfo=UTC)


def test_missing_frontmatter_fences_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("just a body, no frontmatter")


def test_empty_title_raises():
    raw = dedent(
        """\
        ---
        title: ""
        date: 2026-04-17T10:00:00Z
        ---

        body
        """
    )
    with pytest.raises(FrontmatterError, match="title"):
        parse_frontmatter(raw)


def test_date_only_string_parsed():
    raw = dedent(
        """\
        ---
        title: "Hello"
        date: 2026-04-17
        ---

        body
        """
    )
    fm, _ = parse_frontmatter(raw)
    assert isinstance(fm.date, datetime)
    assert fm.date.tzinfo is not None
