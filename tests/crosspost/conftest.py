from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

import pytest
import responses as responses_lib


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "posts"


class GitRepo:
    def __init__(self, path: Path) -> None:
        self.path = path

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.path,
            check=check,
            capture_output=True,
            text=True,
        )

    def write(self, rel_path: str, content: str) -> Path:
        full = self.path / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return full

    def add_all(self) -> None:
        self.run("add", "-A")

    def commit(self, message: str) -> str:
        self.run("commit", "-m", message)
        return self.head()

    def head(self) -> str:
        return self.run("rev-parse", "HEAD").stdout.strip()

    def mv(self, src: str, dst: str) -> None:
        self.run("mv", src, dst)


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Callable[[], GitRepo]:
    def _factory() -> GitRepo:
        repo_dir = tmp_path / f"repo-{os.urandom(4).hex()}"
        repo_dir.mkdir()
        repo = GitRepo(repo_dir)
        repo.run("init", "-b", "main")
        repo.run("config", "user.email", "test@example.com")
        repo.run("config", "user.name", "Test")
        repo.run("config", "commit.gpgsign", "false")
        return repo

    return _factory


@pytest.fixture
def devto_responses():
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def sample_post_fixture() -> Callable[[str], str]:
    def _load(name: str) -> str:
        return (FIXTURES_DIR / name).read_text()

    return _load
