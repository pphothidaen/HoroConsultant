"""Regression coverage for the post-completion branch lifecycle guard."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "branch_lifecycle_guard.py"


def _git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _load_guard():
    assert GUARD.is_file(), "branch lifecycle guard is missing"
    spec = importlib.util.spec_from_file_location("branch_lifecycle_guard", GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "qa@example.test")
    _git(tmp_path, "config", "user.name", "QA")
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "baseline")
    _git(tmp_path, "checkout", "-b", "feature/close-lifecycle")
    (tmp_path / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(tmp_path, "add", "feature.txt")
    _git(tmp_path, "commit", "-m", "feature")
    return tmp_path


def test_rejects_local_branch_deletion_before_main_contains_it(repository: Path) -> None:
    guard = _load_guard()

    allowed, reason = guard.validate_delete_command(
        "git branch --delete feature/close-lifecycle", repo=repository
    )

    assert allowed is False
    assert "not merged into main" in reason


def test_allows_local_branch_deletion_only_after_main_contains_it(repository: Path) -> None:
    guard = _load_guard()
    _git(repository, "checkout", "main")
    _git(repository, "merge", "--no-ff", "feature/close-lifecycle", "-m", "merge feature")

    allowed, reason = guard.validate_delete_command(
        "git branch -d feature/close-lifecycle", repo=repository
    )

    assert allowed is True
    assert "merged into main" in reason


def test_rejects_protected_branch_deletion(repository: Path) -> None:
    guard = _load_guard()

    allowed, reason = guard.validate_delete_command("git branch -D main", repo=repository)

    assert allowed is False
    assert "protected" in reason
