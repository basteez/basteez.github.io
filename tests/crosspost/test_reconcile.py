from __future__ import annotations

from dataclasses import dataclass

import pytest

from scripts.crosspost.reconcile import (
    DevToArticleSummary,
    ReconciledAction,
    build_canonical_index,
    normalize_canonical_url,
    reconcile,
)


@dataclass
class _FakePost:
    slug: str
    canonical_url: str


# ---------------------------------------------------------------------------
# normalize_canonical_url — T003
# ---------------------------------------------------------------------------


def test_normalize_passthrough_simple_slug():
    assert normalize_canonical_url("https://bstz.it/p/slug/") == "https://bstz.it/p/slug/"


def test_normalize_strips_surrounding_whitespace():
    assert normalize_canonical_url("  https://bstz.it/p/slug/  ") == "https://bstz.it/p/slug/"


def test_normalize_lowercases_scheme_and_host_preserves_path_case():
    assert (
        normalize_canonical_url("HTTPS://BSTZ.IT/p/Slug/")
        == "https://bstz.it/p/Slug/"
    )


def test_normalize_adds_missing_trailing_slash():
    assert normalize_canonical_url("https://bstz.it/p/slug") == "https://bstz.it/p/slug/"


def test_normalize_collapses_multiple_trailing_slashes():
    assert normalize_canonical_url("https://bstz.it/p/slug///") == "https://bstz.it/p/slug/"


@pytest.mark.parametrize(
    "raw",
    [None, "", "   ", "http://bstz.it/p/slug/", "ftp://bstz.it/p/slug/", "mailto:x@y"],
)
def test_normalize_returns_none_for_invalid(raw):
    assert normalize_canonical_url(raw) is None


def test_normalize_host_only_gets_root_path():
    assert normalize_canonical_url("https://bstz.it") == "https://bstz.it/"


def test_normalize_preserves_query_string():
    out = normalize_canonical_url("https://bstz.it/p/slug/?q=1")
    assert "?q=1" in out


def test_normalize_preserves_fragment():
    out = normalize_canonical_url("https://bstz.it/p/slug/#section")
    assert "#section" in out


# ---------------------------------------------------------------------------
# build_canonical_index — T004
# ---------------------------------------------------------------------------


def _sum(id: int, canonical_raw: str | None, url: str | None = None) -> DevToArticleSummary:
    return DevToArticleSummary(
        id=id,
        canonical_url_raw=canonical_raw,
        canonical_url_norm=normalize_canonical_url(canonical_raw),
        url=url or f"https://dev.to/u/post-{id}",
        published=True,
    )


def test_build_index_empty():
    assert build_canonical_index([]) == {}


def test_build_index_excludes_null_empty_and_non_https():
    items = [
        _sum(1, None),
        _sum(2, ""),
        _sum(3, "http://bstz.it/p/a/"),
        _sum(4, "https://bstz.it/p/kept/"),
    ]
    idx = build_canonical_index(items)
    assert idx == {"https://bstz.it/p/kept/": [4]}


def test_build_index_duplicates_preserved_in_listing_order():
    items = [
        _sum(111, "https://bstz.it/p/dup/"),
        _sum(222, "https://bstz.it/p/dup/"),
    ]
    idx = build_canonical_index(items)
    assert idx["https://bstz.it/p/dup/"] == [111, 222]


def test_build_index_collapses_cosmetic_variants():
    items = [
        _sum(1, "HTTPS://BSTZ.IT/p/slug"),
        _sum(2, "  https://bstz.it/p/slug///  "),
    ]
    idx = build_canonical_index(items)
    assert list(idx.keys()) == ["https://bstz.it/p/slug/"]
    assert idx["https://bstz.it/p/slug/"] == [1, 2]


def test_build_index_values_are_lists_not_sets():
    idx = build_canonical_index([_sum(1, "https://bstz.it/p/a/")])
    val = idx["https://bstz.it/p/a/"]
    assert isinstance(val, list)


# ---------------------------------------------------------------------------
# reconcile() decision table — T005
# ---------------------------------------------------------------------------


CANON = "https://bstz.it/p/hello/"


def _post(canonical: str = CANON) -> _FakePost:
    return _FakePost(slug="hello", canonical_url=canonical)


def _lookup(summaries: list[DevToArticleSummary]) -> dict[int, DevToArticleSummary]:
    return {s.id: s for s in summaries}


def test_reconcile_no_state_no_matches_is_create():
    res = reconcile(_post(), None, {}, {})
    assert res.action is ReconciledAction.CREATE


def test_reconcile_no_state_one_match_is_adopt_with_id_and_url():
    s = _sum(101, CANON, url="https://dev.to/u/hello-abc1")
    idx = build_canonical_index([s])
    res = reconcile(_post(), None, idx, _lookup([s]))
    assert res.action is ReconciledAction.ADOPT
    assert res.devto_article_id == 101
    assert res.devto_url == "https://dev.to/u/hello-abc1"


def test_reconcile_no_state_multi_match_is_fail_multiple_matches_sorted_ids_preserved():
    s1 = _sum(111, CANON)
    s2 = _sum(222, CANON)
    idx = build_canonical_index([s1, s2])
    res = reconcile(_post(), None, idx, _lookup([s1, s2]))
    assert res.action is ReconciledAction.FAIL_MULTIPLE_MATCHES
    assert res.conflicting_ids == [111, 222]
    assert "111" in res.reason and "222" in res.reason
    assert "delete duplicates" in res.reason


def test_reconcile_state_no_match_is_update():
    state_entry = {"devto_article_id": 101}
    res = reconcile(_post(), state_entry, {}, {})
    assert res.action is ReconciledAction.UPDATE


def test_reconcile_state_matches_single_id_equal_is_update():
    s = _sum(101, CANON)
    idx = build_canonical_index([s])
    res = reconcile(_post(), {"devto_article_id": 101}, idx, _lookup([s]))
    assert res.action is ReconciledAction.UPDATE


def test_reconcile_state_matches_single_id_diff_is_fail_id_mismatch():
    s = _sum(222, CANON)
    idx = build_canonical_index([s])
    res = reconcile(_post(), {"devto_article_id": 111}, idx, _lookup([s]))
    assert res.action is ReconciledAction.FAIL_ID_MISMATCH
    assert res.conflicting_ids == [111, 222]
    assert "111" in res.reason and "222" in res.reason
    assert "reconcile manually" in res.reason


def test_reconcile_state_in_multi_match_is_update():
    s1 = _sum(111, CANON)
    s2 = _sum(222, CANON)
    idx = build_canonical_index([s1, s2])
    res = reconcile(_post(), {"devto_article_id": 111}, idx, _lookup([s1, s2]))
    assert res.action is ReconciledAction.UPDATE


def test_reconcile_state_not_in_multi_match_is_fail_id_mismatch():
    s1 = _sum(222, CANON)
    s2 = _sum(333, CANON)
    idx = build_canonical_index([s1, s2])
    res = reconcile(_post(), {"devto_article_id": 111}, idx, _lookup([s1, s2]))
    assert res.action is ReconciledAction.FAIL_ID_MISMATCH
    assert res.conflicting_ids == [111, 222, 333]
    assert "222" in res.reason and "333" in res.reason


def test_reconcile_rejects_skip_classifications_as_precondition():
    with pytest.raises(ValueError):
        reconcile(_post(), None, {}, {}, prior_action=ReconciledAction.SKIP_UNCHANGED)
