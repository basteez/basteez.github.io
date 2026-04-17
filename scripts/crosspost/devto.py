from __future__ import annotations

import os
import time
from typing import Callable, Iterator, TypeVar

import requests

from .models import DevtoArticle


DEFAULT_BASE_URL = "https://dev.to/api"
PER_PAGE = 1000
USER_AGENT = "basteez-crosspost/1.0 (+https://github.com/basteez/basteez.github.io)"

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1.0, 3.0, 9.0)  # delays before attempts 2, 3 (and 4 if ever raised).

T = TypeVar("T")


class DevtoError(Exception):
    """Base class for dev.to client errors."""


class AuthRejected(DevtoError):
    """401/403 from dev.to — api key is broken globally."""


class NonRetryable(DevtoError):
    """4xx (other than 401/403/429) — caller's fault, no retry."""


class RetryExhausted(DevtoError):
    """Transient failure (429/5xx/network) that exceeded the retry budget."""


class _Retryable(DevtoError):
    """Internal marker: this attempt hit a transient error. Retry until budget."""

    def __init__(self, reason: str, retry_after: float | None = None) -> None:
        super().__init__(reason)
        self.retry_after = retry_after


_RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


def _parse_retry_after(response: requests.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _classify_response(response: requests.Response) -> None:
    status = response.status_code
    if 200 <= status < 300:
        return
    if status in (401, 403):
        raise AuthRejected(f"auth rejected: {status} {response.text}")
    if status == 429:
        raise _Retryable(
            f"rate limited: {response.text}",
            retry_after=_parse_retry_after(response),
        )
    if 500 <= status < 600:
        raise _Retryable(f"server error: {status} {response.text}")
    raise NonRetryable(f"non-retryable error: {status} {response.text}")


def _retry(call: Callable[[], T]) -> T:
    last_exc: _Retryable | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return call()
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = _Retryable(f"network error: {exc}")
        except _Retryable as exc:
            last_exc = exc
        if attempt >= MAX_ATTEMPTS:
            break
        delay = (
            last_exc.retry_after
            if last_exc.retry_after is not None
            else BACKOFF_SECONDS[attempt - 1]
        )
        time.sleep(delay)
    assert last_exc is not None
    raise RetryExhausted(str(last_exc))


def _article_from_json(raw: dict) -> DevtoArticle:
    return DevtoArticle(
        id=int(raw["id"]),
        title=str(raw.get("title", "")),
        published=bool(raw.get("published", False)),
        url=str(raw.get("url", "")),
    )


class DevtoClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url or os.environ.get("DEVTO_API_BASE", DEFAULT_BASE_URL)
        self.session = session or requests.Session()

    def _headers(self, post: bool = False) -> dict[str, str]:
        headers = {
            "api-key": self.api_key,
            "accept": "application/vnd.forem.api-v1+json",
            "user-agent": USER_AGENT,
        }
        if post:
            headers["content-type"] = "application/json"
        return headers

    def _get_json(self, path: str, params: dict[str, int]) -> list[dict]:
        def call() -> list[dict]:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers(),
            )
            _classify_response(response)
            body = response.json()
            if not isinstance(body, list):
                raise NonRetryable(f"expected list from {path}, got {type(body)}")
            return body

        return _retry(call)

    def _paginate(self, path: str) -> Iterator[DevtoArticle]:
        page = 1
        while True:
            body = self._get_json(path, {"page": page, "per_page": PER_PAGE})
            if not body:
                return
            for raw in body:
                yield _article_from_json(raw)
            page += 1

    def list_published(self) -> Iterator[DevtoArticle]:
        yield from self._paginate("/articles/me/published")

    def list_unpublished(self) -> Iterator[DevtoArticle]:
        yield from self._paginate("/articles/me/unpublished")

    def create_article(self, title: str, body_markdown: str) -> DevtoArticle:
        payload = {
            "article": {
                "title": title,
                "body_markdown": body_markdown,
                "published": False,
            }
        }

        def call() -> DevtoArticle:
            response = self.session.post(
                f"{self.base_url}/articles",
                json=payload,
                headers=self._headers(post=True),
            )
            _classify_response(response)
            return _article_from_json(response.json())

        return _retry(call)
