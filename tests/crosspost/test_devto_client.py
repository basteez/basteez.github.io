from __future__ import annotations

import json

import pytest
import responses

from scripts.crosspost.devto import (
    ArticleMissingError,
    CredentialError,
    DevToClient,
    ListingError,
    RateLimitError,
    ServerError,
    ValidationError,
)

API = "https://dev.to/api"


def make_client() -> DevToClient:
    return DevToClient(api_key="secret-key")


@responses.activate
def test_create_article_sends_published_false_and_returns_id_url():
    responses.add(
        responses.POST,
        f"{API}/articles",
        json={"id": 42, "url": "https://dev.to/u/hello-abc1", "published": False},
        status=201,
    )
    client = make_client()
    out = client.create_article(
        title="Hello",
        body_markdown="body",
        tags=["hugo"],
        canonical_url="https://bstz.it/p/hello/",
    )
    assert out["id"] == 42
    assert out["url"] == "https://dev.to/u/hello-abc1"
    call = responses.calls[0]
    assert call.request.headers["api-key"] == "secret-key"
    body = json.loads(call.request.body)
    assert body["article"]["published"] is False
    assert body["article"]["title"] == "Hello"
    assert body["article"]["canonical_url"] == "https://bstz.it/p/hello/"


@responses.activate
def test_update_article_omits_published_key():
    responses.add(
        responses.PUT,
        f"{API}/articles/42",
        json={"id": 42, "url": "https://dev.to/u/hello-abc1", "published": True},
        status=200,
    )
    client = make_client()
    client.update_article(
        id=42,
        title="Hello",
        body_markdown="body",
        tags=["hugo"],
        canonical_url="https://bstz.it/p/hello/",
    )
    body = json.loads(responses.calls[0].request.body)
    assert "published" not in body["article"]


@responses.activate
def test_401_raises_credential_error():
    responses.add(responses.POST, f"{API}/articles", status=401, json={"error": "bad key"})
    with pytest.raises(CredentialError):
        make_client().create_article(
            title="t", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
        )


@responses.activate
def test_403_raises_credential_error():
    responses.add(responses.POST, f"{API}/articles", status=403, json={"error": "forbidden"})
    with pytest.raises(CredentialError):
        make_client().create_article(
            title="t", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
        )


@responses.activate
def test_422_raises_validation_error_with_errors_body():
    responses.add(
        responses.POST,
        f"{API}/articles",
        status=422,
        json={"errors": {"title": ["can't be blank"]}},
    )
    with pytest.raises(ValidationError) as exc:
        make_client().create_article(
            title="", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
        )
    assert "title" in str(exc.value)


@responses.activate
def test_429_retry_after_then_fail():
    responses.add(
        responses.POST,
        f"{API}/articles",
        status=429,
        headers={"Retry-After": "0"},
        json={"error": "slow down"},
    )
    responses.add(
        responses.POST,
        f"{API}/articles",
        status=429,
        headers={"Retry-After": "0"},
        json={"error": "slow down"},
    )
    with pytest.raises(RateLimitError):
        make_client().create_article(
            title="t", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
        )
    assert len(responses.calls) == 2


@responses.activate
def test_429_then_success_on_retry():
    responses.add(
        responses.POST,
        f"{API}/articles",
        status=429,
        headers={"Retry-After": "0"},
        json={"error": "slow down"},
    )
    responses.add(
        responses.POST,
        f"{API}/articles",
        status=201,
        json={"id": 1, "url": "https://dev.to/u/a", "published": False},
    )
    out = make_client().create_article(
        title="t", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
    )
    assert out["id"] == 1
    assert len(responses.calls) == 2


@responses.activate
def test_5xx_retry_then_fail(monkeypatch):
    import scripts.crosspost.devto as devto_mod

    monkeypatch.setattr(devto_mod, "SERVER_RETRY_SLEEP_SECONDS", 0)
    responses.add(responses.POST, f"{API}/articles", status=500, json={"error": "boom"})
    responses.add(responses.POST, f"{API}/articles", status=500, json={"error": "boom"})
    with pytest.raises(ServerError):
        make_client().create_article(
            title="t", body_markdown="b", tags=[], canonical_url="https://bstz.it/p/a/"
        )
    assert len(responses.calls) == 2


@responses.activate
def test_404_on_update_raises_article_missing_error():
    responses.add(responses.PUT, f"{API}/articles/9999", status=404, json={"error": "not found"})
    with pytest.raises(ArticleMissingError):
        make_client().update_article(
            id=9999,
            title="t",
            body_markdown="b",
            tags=[],
            canonical_url="https://bstz.it/p/a/",
        )


LISTING_URL = f"{API}/articles/me/all"


def _listing_item(id: int, canonical_url: str | None = None, url: str | None = None, published: bool = True) -> dict:
    return {
        "id": id,
        "canonical_url": canonical_url,
        "url": url or f"https://dev.to/u/post-{id}",
        "published": published,
        "title": f"Article {id}",
    }


@responses.activate
def test_list_my_articles_single_page_terminates():
    responses.add(
        responses.GET,
        LISTING_URL,
        json=[_listing_item(1, "https://bstz.it/p/one/")],
        status=200,
    )
    out = make_client().list_my_articles()
    assert len(out) == 1
    assert out[0]["id"] == 1
    assert out[0]["canonical_url"] == "https://bstz.it/p/one/"
    assert out[0]["url"] == "https://dev.to/u/post-1"
    assert out[0]["published"] is True


@responses.activate
def test_list_my_articles_paginates_in_order_and_stops_on_short_page():
    page1 = [_listing_item(i, f"https://bstz.it/p/{i}/") for i in range(1, 101)]
    page2 = [_listing_item(i, f"https://bstz.it/p/{i}/") for i in range(101, 201)]
    page3 = [_listing_item(i, f"https://bstz.it/p/{i}/") for i in range(201, 238)]
    responses.add(responses.GET, LISTING_URL, json=page1, status=200)
    responses.add(responses.GET, LISTING_URL, json=page2, status=200)
    responses.add(responses.GET, LISTING_URL, json=page3, status=200)
    out = make_client().list_my_articles()
    assert [a["id"] for a in out] == list(range(1, 238))
    assert len(responses.calls) == 3
    q1 = responses.calls[0].request.url
    assert "page=1" in q1 and "per_page=100" in q1
    assert "page=2" in responses.calls[1].request.url
    assert "page=3" in responses.calls[2].request.url


@responses.activate
def test_list_my_articles_exact_multiple_of_per_page_terminates_on_empty_page():
    page1 = [_listing_item(i, f"https://bstz.it/p/{i}/") for i in range(1, 101)]
    responses.add(responses.GET, LISTING_URL, json=page1, status=200)
    responses.add(responses.GET, LISTING_URL, json=[], status=200)
    out = make_client().list_my_articles()
    assert len(out) == 100
    assert len(responses.calls) == 2


@responses.activate
def test_list_my_articles_sends_required_headers():
    responses.add(responses.GET, LISTING_URL, json=[], status=200)
    make_client().list_my_articles()
    req = responses.calls[0].request
    assert req.headers["api-key"] == "secret-key"
    assert req.headers["accept"] == "application/vnd.forem.api-v1+json"


@responses.activate
def test_list_my_articles_401_raises_credential_error():
    responses.add(responses.GET, LISTING_URL, status=401, json={"error": "bad key"})
    with pytest.raises(CredentialError):
        make_client().list_my_articles()


@responses.activate
def test_list_my_articles_403_raises_credential_error():
    responses.add(responses.GET, LISTING_URL, status=403, json={"error": "forbidden"})
    with pytest.raises(CredentialError):
        make_client().list_my_articles()


@responses.activate
def test_list_my_articles_429_retries_once_then_rate_limit_error():
    responses.add(responses.GET, LISTING_URL, status=429, headers={"Retry-After": "0"})
    responses.add(responses.GET, LISTING_URL, status=429, headers={"Retry-After": "0"})
    with pytest.raises(RateLimitError):
        make_client().list_my_articles()
    assert len(responses.calls) == 2


@responses.activate
def test_list_my_articles_5xx_retries_once_then_server_error(monkeypatch):
    import scripts.crosspost.devto as devto_mod

    monkeypatch.setattr(devto_mod, "SERVER_RETRY_SLEEP_SECONDS", 0)
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})
    responses.add(responses.GET, LISTING_URL, status=500, json={"error": "boom"})
    with pytest.raises(ServerError):
        make_client().list_my_articles()
    assert len(responses.calls) == 2


@responses.activate
def test_list_my_articles_timeout_raises_listing_error(monkeypatch):
    def _boom(*args, **kwargs):
        import requests as _r

        raise _r.ConnectionError("network down")

    client = make_client()
    monkeypatch.setattr(client._session, "get", _boom)
    with pytest.raises(ListingError):
        client.list_my_articles()


@responses.activate
def test_list_my_articles_non_array_body_raises_listing_error():
    responses.add(responses.GET, LISTING_URL, json={"error": "not a list"}, status=200)
    with pytest.raises(ListingError):
        make_client().list_my_articles()


@responses.activate
def test_list_my_articles_element_missing_id_raises_listing_error():
    responses.add(
        responses.GET,
        LISTING_URL,
        json=[{"canonical_url": "https://bstz.it/p/a/", "url": "u"}],
        status=200,
    )
    with pytest.raises(ListingError):
        make_client().list_my_articles()
