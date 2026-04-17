from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
import responses

LISTING_URL = "https://dev.to/api/articles/me/all"


@pytest.fixture
def fake_devto_listing():
    def _register(pages: list[list[dict]]) -> None:
        for idx, page in enumerate(pages, start=1):
            responses.add(
                responses.GET,
                LISTING_URL,
                json=page,
                status=200,
                match=[
                    responses.matchers.query_param_matcher(
                        {"page": str(idx), "per_page": "100"}
                    )
                ],
            )

    return _register


@pytest.fixture
def sample_frontmatter_body() -> str:
    return dedent(
        """\
        ---
        title: "Hello world"
        date: 2026-04-17T10:00:00Z
        tags:
          - hugo
          - testing
        categories:
          - dev
        ---

        Body text.
        """
    )


@pytest.fixture
def content_tree(tmp_path: Path) -> Path:
    root = tmp_path / "content" / "post"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def hugo_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "hugo.yaml"
    cfg.write_text(
        dedent(
            """\
            baseurl: https://bstz.it
            permalinks:
              post: /p/:slug/
            """
        )
    )
    return cfg


@pytest.fixture
def write_post():
    def _write(content_dir: Path, slug_dir_or_file: str, body: str) -> Path:
        target = content_dir / slug_dir_or_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        return target

    return _write
