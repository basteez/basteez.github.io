from __future__ import annotations

from scripts.crosspost.changeset import (
    ZERO_SHA,
    resolve_touched_posts,
)


def _post_body(title: str, draft: bool = False) -> str:
    flag = "true" if draft else "false"
    return f"---\ntitle: {title}\ndraft: {flag}\n---\nbody\n"


def test_single_commit_add(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    repo.write("content/post/2026-04-17-foo/index.md", _post_body("Foo"))
    repo.add_all()
    after = repo.commit("add foo")

    entries = resolve_touched_posts(before, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-17-foo/index.md" in paths
    assert all(e.status.startswith("A") for e in entries)


def test_multi_commit_push_unions_adds(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    repo.write("content/post/2026-04-10-a.md", _post_body("A"))
    repo.add_all()
    repo.commit("add a")

    repo.write("content/post/2026-04-11-b/index.md", _post_body("B"))
    repo.add_all()
    after = repo.commit("add b")

    entries = resolve_touched_posts(before, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-10-a.md" in paths
    assert "content/post/2026-04-11-b/index.md" in paths


def test_rename_filtered_out(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("content/post/2026-04-10-old.md", _post_body("Old"))
    repo.add_all()
    before = repo.commit("init with post")

    repo.mv(
        "content/post/2026-04-10-old.md",
        "content/post/2026-04-10-renamed.md",
    )
    repo.add_all()
    after = repo.commit("rename post")

    entries = resolve_touched_posts(before, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-10-renamed.md" not in paths


def test_zero_before_falls_back_to_tip_commit(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    repo.commit("init")

    repo.write("content/post/2026-04-20-new.md", _post_body("New"))
    repo.add_all()
    after = repo.commit("add new")

    entries = resolve_touched_posts(ZERO_SHA, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-20-new.md" in paths


def test_before_equals_after_is_empty(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("content/post/2026-04-01-x.md", _post_body("X"))
    repo.add_all()
    sha = repo.commit("init")

    entries = resolve_touched_posts(sha, sha, cwd=repo.path)
    assert entries == []


def test_non_post_paths_filtered(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    repo.write("content/post/2026-04-17-foo/index.md", _post_body("Foo"))
    repo.write("content/post/2026-04-17-foo/image.png", "fake png")
    repo.write("content/page/about.md", _post_body("About"))
    repo.write("themes/custom/layout.html", "<html></html>")
    repo.add_all()
    after = repo.commit("add mix")

    entries = resolve_touched_posts(before, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-17-foo/index.md" in paths
    assert "content/post/2026-04-17-foo/image.png" not in paths
    assert "content/page/about.md" not in paths
    assert "themes/custom/layout.html" not in paths


def test_touched_includes_modified_draft_flip(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    repo.commit("init")

    repo.write("content/post/flip.md", _post_body("Flip", draft=True))
    repo.add_all()
    before = repo.commit("add flip as draft")

    repo.write("content/post/flip.md", _post_body("Flip", draft=False))
    repo.add_all()
    after = repo.commit("publish flip")

    touched = resolve_touched_posts(before, after, cwd=repo.path)
    assert len(touched) == 1
    assert touched[0].path == "content/post/flip.md"
    assert touched[0].status == "M"


def test_touched_union_dedups_add_then_modify(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    repo.write("content/post/p.md", _post_body("P", draft=True))
    repo.add_all()
    repo.commit("add p as draft")

    repo.write("content/post/p.md", _post_body("P", draft=False))
    repo.add_all()
    after = repo.commit("publish p")

    touched = resolve_touched_posts(before, after, cwd=repo.path)
    paths = [e.path for e in touched]
    assert paths.count("content/post/p.md") == 1


def test_touched_includes_single_file_post(tmp_git_repo):
    repo = tmp_git_repo()
    repo.write("README.md", "readme\n")
    repo.add_all()
    before = repo.commit("init")

    repo.write("content/post/2026-04-18-single.md", _post_body("Single"))
    repo.write("content/post/bundle/index.md", _post_body("Bundle"))
    repo.write("README.md", "readme\nupdated\n")
    repo.add_all()
    after = repo.commit("add single + bundle, edit readme")

    entries = resolve_touched_posts(before, after, cwd=repo.path)
    paths = {e.path for e in entries}
    assert "content/post/2026-04-18-single.md" in paths
    assert "content/post/bundle/index.md" in paths
    assert "README.md" not in paths

    single = next(
        e for e in entries if e.path == "content/post/2026-04-18-single.md"
    )
    assert single.status == "A"
