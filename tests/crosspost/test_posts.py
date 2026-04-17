from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.crosspost.posts import (
    HugoConfigError,
    derive_slug,
    discover_posts,
    load_hugo_config,
)


def test_slug_from_frontmatter_override(tmp_path: Path):
    path = tmp_path / "2026-04-17-file-name.md"
    assert derive_slug(path, frontmatter_slug="custom-slug") == "custom-slug"


def test_slug_strips_date_prefix_from_filename(tmp_path: Path):
    path = tmp_path / "2026-04-17-my-post.md"
    assert derive_slug(path, frontmatter_slug=None) == "my-post"


def test_slug_from_page_bundle_directory(tmp_path: Path):
    path = tmp_path / "2026-04-17-my-post" / "index.md"
    assert derive_slug(path, frontmatter_slug=None) == "my-post"


def test_slug_without_date_prefix(tmp_path: Path):
    path = tmp_path / "just-a-post.md"
    assert derive_slug(path, frontmatter_slug=None) == "just-a-post"


def test_slug_malformed_raises(tmp_path: Path):
    path = tmp_path / "2026-04-17-NotValid.md"
    with pytest.raises(Exception, match="slug"):
        derive_slug(path, frontmatter_slug=None)


def test_hugo_config_extracts_baseurl_and_permalink(hugo_config: Path):
    baseurl, permalink = load_hugo_config(hugo_config)
    assert baseurl == "https://bstz.it"
    assert permalink == "/p/:slug/"


def test_hugo_config_missing_baseurl_raises(tmp_path: Path):
    cfg = tmp_path / "hugo.yaml"
    cfg.write_text("permalinks:\n  post: /p/:slug/\n")
    with pytest.raises(HugoConfigError, match="baseurl"):
        load_hugo_config(cfg)


def test_hugo_config_missing_permalink_raises(tmp_path: Path):
    cfg = tmp_path / "hugo.yaml"
    cfg.write_text("baseurl: https://bstz.it\n")
    with pytest.raises(HugoConfigError, match="permalinks"):
        load_hugo_config(cfg)


def _body(title="T", date="2026-04-17T10:00:00Z", tags=None, extra=""):
    lines = ["---", f'title: "{title}"', f"date: {date}"]
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {t}" for t in tags)
    if extra:
        lines.append(extra)
    lines.append("---")
    lines.append("")
    lines.append("Body.")
    lines.append("")
    return "\n".join(lines)


def test_discover_posts_flat_md_file(content_tree: Path, write_post):
    write_post(content_tree, "2026-04-17-hello.md", _body("Hello"))
    posts = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    assert len(posts) == 1
    p = posts[0]
    assert p.slug == "hello"
    assert p.canonical_url == "https://bstz.it/p/hello/"


def test_discover_posts_page_bundle(content_tree: Path, write_post):
    write_post(content_tree, "2026-04-17-hello/index.md", _body("Hello"))
    posts = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    assert len(posts) == 1
    assert posts[0].slug == "hello"


def test_discover_posts_duplicate_slug_raises(content_tree: Path, write_post):
    write_post(content_tree, "2026-04-17-hello.md", _body("Hello"))
    write_post(content_tree, "2026-04-18-hello/index.md", _body("Hello 2"))
    with pytest.raises(Exception, match="duplicate"):
        discover_posts(content_tree, "https://bstz.it", "/p/:slug/")


def test_discover_posts_content_hash_deterministic(content_tree: Path, write_post):
    write_post(content_tree, "2026-04-17-hello.md", _body("Hello", tags=["a", "b"]))
    posts_a = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    posts_b = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    assert posts_a[0].content_hash == posts_b[0].content_hash


def test_discover_posts_rewrites_relative_images(content_tree: Path, write_post):
    body = dedent(
        """\
        ---
        title: "Img"
        date: 2026-04-17T10:00:00Z
        ---

        ![pic](./img/x.png)
        """
    )
    write_post(content_tree, "2026-04-17-img.md", body)
    posts = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    assert "https://bstz.it/p/img/img/x.png" in posts[0].body_markdown_rewritten


def test_discover_posts_skips_non_markdown(content_tree: Path, write_post):
    write_post(content_tree, "2026-04-17-hello.md", _body("Hello"))
    (content_tree / "README.txt").write_text("not a post")
    posts = discover_posts(content_tree, "https://bstz.it", "/p/:slug/")
    assert len(posts) == 1
