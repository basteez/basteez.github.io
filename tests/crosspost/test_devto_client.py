from __future__ import annotations

import json

import pytest
import requests

from scripts.crosspost.devto import (
    AuthRejected,
    DevtoClient,
    NonRetryable,
    RetryExhausted,
)


BASE = "https://dev.to/api"


def _article(id_: int, title: str, published: bool = True) -> dict:
    return {
        "id": id_,
        "title": title,
        "published": published,
        "url": f"https://dev.to/test/{id_}",
    }


def test_list_published_paginates_until_empty(devto_responses):
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/published",
        json=[_article(1, "One"), _article(2, "Two")],
        status=200,
    )
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/published",
        json=[_article(3, "Three")],
        status=200,
    )
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/published",
        json=[],
        status=200,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    articles = list(client.list_published())
    assert [a.id for a in articles] == [1, 2, 3]


def test_list_unpublished_paginates_until_empty(devto_responses):
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/unpublished",
        json=[_article(10, "Draft A", published=False)],
        status=200,
    )
    devto_responses.add(
        devto_responses.GET,
        f"{BASE}/articles/me/unpublished",
        json=[],
        status=200,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    articles = list(client.list_unpublished())
    assert [a.id for a in articles] == [10]
    assert articles[0].published is False


def test_create_article_posts_expected_payload(devto_responses):
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"id": 42, "title": "T", "published": False, "url": "https://x/42"},
        status=201,
    )
    client = DevtoClient(api_key="secret-key", base_url=BASE)
    article = client.create_article("T", "body")
    assert article.id == 42

    call = devto_responses.calls[0]
    payload = json.loads(call.request.body)
    assert payload == {
        "article": {
            "title": "T",
            "body_markdown": "body",
            "published": False,
        }
    }
    assert call.request.headers["api-key"] == "secret-key"


def test_create_article_422_raises_non_retryable(devto_responses):
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"error": "body_markdown: is invalid"},
        status=422,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    with pytest.raises(NonRetryable):
        client.create_article("T", "body")


# --- Retry helper tests (T022) ---


def test_retry_honors_retry_after_on_429(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        status=429,
        headers={"Retry-After": "2"},
        body="throttled",
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"id": 1, "title": "T", "published": False, "url": "x"},
        status=201,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    article = client.create_article("T", "body")
    assert article.id == 1
    assert sleeps and abs(sleeps[0] - 2.0) < 1e-9


def test_retry_exhausts_on_5xx_with_fixed_backoff(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    for _ in range(3):
        devto_responses.add(
            devto_responses.POST,
            f"{BASE}/articles",
            status=500,
            body="server exploded",
        )
    client = DevtoClient(api_key="k", base_url=BASE)
    with pytest.raises(RetryExhausted):
        client.create_article("T", "body")
    assert sleeps == [1.0, 3.0]


def test_retry_on_connection_error(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        body=requests.exceptions.ConnectionError("reset"),
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"id": 7, "title": "T", "published": False, "url": "x"},
        status=201,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    article = client.create_article("T", "body")
    assert article.id == 7
    assert sleeps == [1.0]


def test_retry_on_timeout(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        body=requests.exceptions.Timeout("slow"),
    )
    devto_responses.add(
        devto_responses.POST,
        f"{BASE}/articles",
        json={"id": 8, "title": "T", "published": False, "url": "x"},
        status=201,
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    assert client.create_article("T", "body").id == 8
    assert sleeps == [1.0]


def test_422_fails_fast_without_retry(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    devto_responses.add(
        devto_responses.POST, f"{BASE}/articles", json={"e": "bad"}, status=422
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    with pytest.raises(NonRetryable):
        client.create_article("T", "body")
    assert sleeps == []


def test_404_fails_fast_without_retry(devto_responses, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: sleeps.append(s))

    devto_responses.add(
        devto_responses.POST, f"{BASE}/articles", status=404, body="not found"
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    with pytest.raises(NonRetryable):
        client.create_article("T", "body")
    assert sleeps == []


def test_401_raises_auth_rejected(devto_responses, monkeypatch):
    monkeypatch.setattr("scripts.crosspost.devto.time.sleep", lambda s: None)
    devto_responses.add(
        devto_responses.POST, f"{BASE}/articles", status=401, body="nope"
    )
    client = DevtoClient(api_key="k", base_url=BASE)
    with pytest.raises(AuthRejected):
        client.create_article("T", "body")
