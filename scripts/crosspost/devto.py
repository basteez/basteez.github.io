from __future__ import annotations

import time
from typing import Any

import requests

API_BASE = "https://dev.to/api"
SERVER_RETRY_SLEEP_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 30


class DevToError(Exception):
    pass


class CredentialError(DevToError):
    pass


class ValidationError(DevToError):
    def __init__(self, message: str, errors: Any = None):
        super().__init__(message)
        self.errors = errors


class ArticleMissingError(DevToError):
    pass


class RateLimitError(DevToError):
    pass


class ServerError(DevToError):
    pass


class ListingError(DevToError):
    pass


class DevToClient:
    def __init__(self, api_key: str, base_url: str = API_BASE):
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "api-key": api_key,
                "accept": "application/vnd.forem.api-v1+json",
                "content-type": "application/json",
            }
        )

    def _parse_errors(self, resp: requests.Response) -> Any:
        try:
            return resp.json().get("errors") or resp.json().get("error")
        except Exception:
            return resp.text

    def _request(
        self, method: str, url: str, payload: dict, *, allow_404: bool = False
    ) -> dict:
        for attempt in (1, 2):
            resp = self._session.request(
                method, url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
            )
            status = resp.status_code
            if 200 <= status < 300:
                try:
                    return resp.json()
                except ValueError as exc:
                    raise DevToError(f"non-JSON success body from {url}: {exc}") from exc
            if status in (401, 403):
                raise CredentialError(
                    "dev.to credential rejected — regenerate and update the DEVTO_API_KEY secret."
                )
            if status == 404 and allow_404:
                raise ArticleMissingError(f"dev.to article not found at {url}")
            if status == 422:
                errors = self._parse_errors(resp)
                raise ValidationError(
                    f"dev.to rejected payload with 422: {errors}", errors=errors
                )
            if status == 429:
                if attempt == 2:
                    raise RateLimitError("dev.to rate-limited twice — aborting")
                retry_after = int(resp.headers.get("Retry-After", "1") or "1")
                time.sleep(retry_after)
                continue
            if 500 <= status < 600:
                if attempt == 2:
                    raise ServerError(
                        f"dev.to server error {status} after retry"
                    )
                time.sleep(SERVER_RETRY_SLEEP_SECONDS)
                continue
            raise DevToError(f"unexpected dev.to response {status}: {resp.text}")
        raise DevToError("exhausted retries without raising")

    def create_article(
        self,
        title: str,
        body_markdown: str,
        tags: list[str],
        canonical_url: str,
    ) -> dict:
        payload = {
            "article": {
                "title": title,
                "body_markdown": body_markdown,
                "published": False,
                "tags": tags,
                "canonical_url": canonical_url,
            }
        }
        return self._request("POST", f"{self._base}/articles", payload)

    def update_article(
        self,
        id: int,
        title: str,
        body_markdown: str,
        tags: list[str],
        canonical_url: str,
    ) -> dict:
        payload = {
            "article": {
                "title": title,
                "body_markdown": body_markdown,
                "tags": tags,
                "canonical_url": canonical_url,
            }
        }
        return self._request(
            "PUT", f"{self._base}/articles/{id}", payload, allow_404=True
        )

    def _get_page(self, page: int, per_page: int) -> list:
        url = f"{self._base}/articles/me/all"
        params = {"page": page, "per_page": per_page}
        for attempt in (1, 2):
            try:
                resp = self._session.get(
                    url, params=params, timeout=REQUEST_TIMEOUT_SECONDS
                )
            except requests.RequestException as exc:
                raise ListingError(f"dev.to listing request failed: {exc}") from exc
            status = resp.status_code
            if 200 <= status < 300:
                try:
                    body = resp.json()
                except ValueError as exc:
                    raise ListingError(
                        f"dev.to listing returned non-JSON body: {exc}"
                    ) from exc
                if not isinstance(body, list):
                    raise ListingError(
                        f"dev.to listing returned non-array body: {type(body).__name__}"
                    )
                return body
            if status in (401, 403):
                raise CredentialError(
                    "dev.to credential rejected — regenerate and update the DEVTO_API_KEY secret."
                )
            if status == 429:
                if attempt == 2:
                    raise RateLimitError("dev.to rate-limited twice — aborting")
                retry_after = int(resp.headers.get("Retry-After", "1") or "1")
                time.sleep(retry_after)
                continue
            if 500 <= status < 600:
                if attempt == 2:
                    raise ServerError(
                        f"dev.to server error {status} after retry"
                    )
                time.sleep(SERVER_RETRY_SLEEP_SECONDS)
                continue
            raise ListingError(
                f"unexpected dev.to listing response {status}: {resp.text}"
            )
        raise ListingError("exhausted retries without raising")

    def list_my_articles(self) -> list[dict]:
        per_page = 100
        page = 1
        out: list[dict] = []
        while True:
            batch = self._get_page(page, per_page)
            for item in batch:
                if not isinstance(item, dict):
                    raise ListingError(
                        f"dev.to listing element is not an object: {type(item).__name__}"
                    )
                raw_id = item.get("id")
                if not isinstance(raw_id, int) or isinstance(raw_id, bool):
                    raise ListingError(
                        f"dev.to listing element has non-integer id: {raw_id!r}"
                    )
                out.append(
                    {
                        "id": raw_id,
                        "url": str(item.get("url", "")),
                        "canonical_url": item.get("canonical_url"),
                        "published": bool(item.get("published", False)),
                    }
                )
            if len(batch) < per_page:
                break
            page += 1
        return out
