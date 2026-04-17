from __future__ import annotations

from scripts.crosspost.models import DevtoArticle, PostFile
from scripts.crosspost.reconcile import (
    build_title_index,
    decide,
    normalize_title,
)


def _article(id_: int, title: str, published: bool = True) -> DevtoArticle:
    return DevtoArticle(
        id=id_, title=title, published=published, url=f"https://dev.to/x/{id_}"
    )


def _post(title: str, draft_false: bool = True) -> PostFile:
    fm = {"title": title}
    if draft_false:
        fm["draft"] = False
    return PostFile(path=f"content/post/2026-04-17-{id(title)}.md", frontmatter=fm, body="body")


def test_normalize_title_handles_case_and_whitespace():
    assert normalize_title("  My  Post  ") == "my post"
    assert normalize_title("My Post") == normalize_title("my post")
    assert normalize_title("MY POST") == normalize_title("my post")


def test_normalize_title_nfc():
    # "é" composed vs "e" + combining acute
    composed = "Café"
    decomposed = "Cafe\u0301"
    assert normalize_title(composed) == normalize_title(decomposed)


def test_build_title_index_builds_normalized_set():
    index = build_title_index([_article(1, "Alpha"), _article(2, "  BETA  ")])
    assert index.contains("alpha")
    assert index.contains("beta")
    assert not index.contains("gamma")


def test_decide_skipped_exists_exact():
    index = build_title_index([_article(1, "My Post")])
    assert decide(_post("My Post"), index) == "skipped_exists"


def test_decide_skipped_exists_case_difference():
    index = build_title_index([_article(1, "My Post")])
    assert decide(_post("my post"), index) == "skipped_exists"


def test_decide_skipped_exists_whitespace_trim():
    index = build_title_index([_article(1, "My Post")])
    assert decide(_post("  My Post  "), index) == "skipped_exists"


def test_decide_skipped_exists_internal_whitespace_collapse():
    index = build_title_index([_article(1, "My  Post")])
    assert decide(_post("My Post"), index) == "skipped_exists"


def test_decide_skipped_exists_nfc_variants():
    index = build_title_index([_article(1, "Café")])
    assert decide(_post("Cafe\u0301"), index) == "skipped_exists"


def test_decide_published_only_match():
    index = build_title_index([_article(1, "Pub Only", published=True)])
    assert decide(_post("pub only"), index) == "skipped_exists"


def test_decide_unpublished_only_match():
    index = build_title_index([_article(1, "Draft Only", published=False)])
    assert decide(_post("draft only"), index) == "skipped_exists"


def test_decide_drafted_when_no_match():
    index = build_title_index([_article(1, "Existing")])
    assert decide(_post("New Post"), index) == "drafted"


def test_in_run_dedup_two_same_title():
    index = build_title_index([])
    first = _post("Same Title")
    second = _post("Same Title")
    assert decide(first, index) == "drafted"
    index.add(first.title or "")
    assert decide(second, index) == "skipped_exists"
