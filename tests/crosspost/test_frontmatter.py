from __future__ import annotations

import pytest

from scripts.crosspost.frontmatter import FrontmatterError, parse


def test_draft_false_is_publishable(sample_post_fixture):
    post = parse(sample_post_fixture("draft_false_singlefile.md"))
    assert post.frontmatter["title"] == "Single File Post"
    assert post.frontmatter["draft"] is False
    assert post.is_publishable is True
    assert "Body of a single-file post." in post.body
    assert "---" not in post.body.splitlines()[0]


def test_draft_true_skipped(sample_post_fixture):
    post = parse(sample_post_fixture("draft_true.md"))
    assert post.is_publishable is False
    assert post.frontmatter.get("draft") is True


def test_missing_draft_key_skipped(sample_post_fixture):
    post = parse(sample_post_fixture("draft_missing.md"))
    assert post.is_publishable is False
    assert "draft" not in post.frontmatter


def test_string_false_not_publishable():
    text = '---\ntitle: "Stringy"\ndraft: "false"\n---\nbody\n'
    post = parse(text)
    assert post.frontmatter["draft"] == "false"
    assert post.is_publishable is False


def test_non_boolean_draft_not_publishable():
    text = "---\ntitle: Foo\ndraft: 0\n---\nbody\n"
    post = parse(text)
    assert post.is_publishable is False


def test_missing_title_not_publishable(sample_post_fixture):
    post = parse(sample_post_fixture("missing_title.md"))
    assert post.title is None
    assert post.is_publishable is False


def test_body_strip_correctness():
    text = "---\ntitle: T\ndraft: false\n---\nline 1\nline 2\n"
    post = parse(text)
    assert post.body == "line 1\nline 2\n"


def test_malformed_yaml_raises(sample_post_fixture):
    with pytest.raises(FrontmatterError):
        parse(sample_post_fixture("malformed_yaml.md"))


def test_missing_terminator_raises():
    text = "---\ntitle: Foo\ndraft: false\nbody without terminator\n"
    with pytest.raises(FrontmatterError):
        parse(text)


def test_no_frontmatter_raises(sample_post_fixture):
    with pytest.raises(FrontmatterError):
        parse(sample_post_fixture("no_frontmatter.md"))


def test_non_mapping_frontmatter_raises():
    text = "---\n- just\n- a\n- list\n---\nbody\n"
    with pytest.raises(FrontmatterError):
        parse(text)


def test_empty_title_string_not_publishable():
    text = '---\ntitle: ""\ndraft: false\n---\nbody\n'
    post = parse(text)
    assert post.title is None
    assert post.is_publishable is False
