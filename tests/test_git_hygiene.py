"""Tests for git_hygiene_pruner script."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRUNER_SCRIPT = ROOT / "scripts" / "git_hygiene_pruner.py"


def _load_pruner_module():
    assert PRUNER_SCRIPT.is_file(), f"Pruner script missing at {PRUNER_SCRIPT}"
    spec = importlib.util.spec_from_file_location("git_hygiene_pruner", PRUNER_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Git command failed: git {' '.join(args)}\nstdout: {res.stdout}\nstderr: {res.stderr}"
    return res


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Fixture creating a standard test git repository with main branch."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "dev@example.test")
    _git(repo, "config", "user.name", "Dev Test")
    (repo / "README.md").write_text("initial commit\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial commit on main")
    return repo


def test_dry_run_identifies_merged_branch_without_deleting(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create feature branch, add commit, and merge into main
    _git(git_repo, "checkout", "-b", "feature/merged-alpha")
    (git_repo / "alpha.txt").write_text("alpha\n", encoding="utf-8")
    _git(git_repo, "add", "alpha.txt")
    _git(git_repo, "commit", "-m", "commit alpha")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/merged-alpha", "-m", "merge alpha")

    # Run dry run
    result = pruner.prune_git_hygiene(repo=git_repo, target="main", dry_run=True, verbose=True)

    assert result["success"] is True
    assert "feature/merged-alpha" in result["dry_run_candidates"]
    assert len(result["deleted"]) == 0

    # Verify branch still exists in local branches
    branches = pruner.get_local_branches(git_repo)
    assert "feature/merged-alpha" in branches


def test_prunes_merged_local_branches_without_dry_run(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create feature branch, add commit, and merge into main
    _git(git_repo, "checkout", "-b", "feature/merged-beta")
    (git_repo / "beta.txt").write_text("beta\n", encoding="utf-8")
    _git(git_repo, "add", "beta.txt")
    _git(git_repo, "commit", "-m", "commit beta")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/merged-beta", "-m", "merge beta")

    # Run pruning
    result = pruner.prune_git_hygiene(repo=git_repo, target="main", dry_run=False, verbose=True)

    assert result["success"] is True
    assert "feature/merged-beta" in result["deleted"]

    # Verify branch was deleted
    branches = pruner.get_local_branches(git_repo)
    assert "feature/merged-beta" not in branches


def test_preserves_unmerged_local_branches(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create unmerged feature branch
    _git(git_repo, "checkout", "-b", "feature/unmerged-gamma")
    (git_repo / "gamma.txt").write_text("gamma\n", encoding="utf-8")
    _git(git_repo, "add", "gamma.txt")
    _git(git_repo, "commit", "-m", "commit gamma")

    _git(git_repo, "checkout", "main")

    # Run pruning
    result = pruner.prune_git_hygiene(repo=git_repo, target="main", dry_run=False, verbose=True)

    assert result["success"] is True
    assert "feature/unmerged-gamma" in result["preserved_unmerged"]
    assert "feature/unmerged-gamma" not in result["deleted"]

    # Verify branch still exists
    branches = pruner.get_local_branches(git_repo)
    assert "feature/unmerged-gamma" in branches


def test_preserves_protected_branches(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create protected branches
    for b in ["dev", "develop", "master"]:
        _git(git_repo, "checkout", "-b", b)

    _git(git_repo, "checkout", "main")

    result = pruner.prune_git_hygiene(repo=git_repo, target="main", dry_run=False, verbose=True)

    assert result["success"] is True
    for b in ["main", "master", "dev", "develop"]:
        assert b in result["skipped_protected"]
        assert b not in result["deleted"]

    branches = pruner.get_local_branches(git_repo)
    for b in ["main", "master", "dev", "develop"]:
        assert b in branches


def test_preserves_currently_checked_out_branch(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create branch and merge to main, but stay checked out on this branch
    _git(git_repo, "checkout", "-b", "feature/active-on-it")
    (git_repo / "active.txt").write_text("active\n", encoding="utf-8")
    _git(git_repo, "add", "active.txt")
    _git(git_repo, "commit", "-m", "commit active")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/active-on-it", "-m", "merge active")

    # Switch back to feature/active-on-it
    _git(git_repo, "checkout", "feature/active-on-it")

    result = pruner.prune_git_hygiene(repo=git_repo, target="main", dry_run=False, verbose=True)

    assert result["success"] is True
    assert "feature/active-on-it" in result["skipped_protected"]
    assert "feature/active-on-it" not in result["deleted"]

    branches = pruner.get_local_branches(git_repo)
    assert "feature/active-on-it" in branches


def test_origin_main_fallback_to_local_main(git_repo: Path) -> None:
    pruner = _load_pruner_module()

    # Create merged branch
    _git(git_repo, "checkout", "-b", "feature/fallback-test")
    (git_repo / "fb.txt").write_text("fb\n", encoding="utf-8")
    _git(git_repo, "add", "fb.txt")
    _git(git_repo, "commit", "-m", "commit fb")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/fallback-test", "-m", "merge fb")

    # Target is origin/main by default, but no remote exists. It should fall back to local main.
    result = pruner.prune_git_hygiene(repo=git_repo, target="origin/main", dry_run=False)

    assert result["success"] is True
    assert "feature/fallback-test" in result["deleted"]


def test_cli_invocation_dry_run(git_repo: Path) -> None:
    _git(git_repo, "checkout", "-b", "feature/cli-dry")
    (git_repo / "c1.txt").write_text("c1\n", encoding="utf-8")
    _git(git_repo, "add", "c1.txt")
    _git(git_repo, "commit", "-m", "commit c1")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/cli-dry", "-m", "merge c1")

    proc = subprocess.run(
        [
            sys.executable,
            str(PRUNER_SCRIPT),
            "--repo",
            str(git_repo),
            "--target",
            "main",
            "--dry-run",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "[DRY-RUN] Local branch 'feature/cli-dry' is merged" in proc.stdout
    assert "[INFO] Git hygiene pruner summary [DRY-RUN]" in proc.stdout

    # Verify pure ASCII output
    assert proc.stdout.isascii()
    assert proc.stderr.isascii()


def test_cli_invocation_actual_prune(git_repo: Path) -> None:
    _git(git_repo, "checkout", "-b", "feature/cli-prune")
    (git_repo / "c2.txt").write_text("c2\n", encoding="utf-8")
    _git(git_repo, "add", "c2.txt")
    _git(git_repo, "commit", "-m", "commit c2")

    _git(git_repo, "checkout", "main")
    _git(git_repo, "merge", "--no-ff", "feature/cli-prune", "-m", "merge c2")

    proc = subprocess.run(
        [
            sys.executable,
            str(PRUNER_SCRIPT),
            "--repo",
            str(git_repo),
            "--target",
            "main",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "[OK] Deleted merged local branch: feature/cli-prune" in proc.stdout
    assert "[INFO] Git hygiene pruner summary [DONE]" in proc.stdout


def test_cli_invalid_repo(tmp_path: Path) -> None:
    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()

    proc = subprocess.run(
        [
            sys.executable,
            str(PRUNER_SCRIPT),
            "--repo",
            str(non_git_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "[ERROR]" in proc.stdout


def test_cli_unresolvable_target(git_repo: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(PRUNER_SCRIPT),
            "--repo",
            str(git_repo),
            "--target",
            "non-existent-target-branch-xyz",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "[ERROR]" in proc.stdout
    assert "could not be resolved" in proc.stdout


def test_remote_prune_handling(tmp_path: Path) -> None:
    # Create a bare remote repo
    bare_remote = tmp_path / "remote.git"
    bare_remote.mkdir()
    _git(bare_remote, "init", "--bare", "-b", "main")

    # Clone local repo from bare remote
    local_repo = tmp_path / "local_repo"
    subprocess.run(["git", "clone", str(bare_remote), str(local_repo)], capture_output=True, text=True, check=True)
    _git(local_repo, "config", "user.email", "dev@example.test")
    _git(local_repo, "config", "user.name", "Dev Test")

    # Push initial commit to main
    (local_repo / "README.md").write_text("remote test\n", encoding="utf-8")
    _git(local_repo, "add", "README.md")
    _git(local_repo, "commit", "-m", "initial commit")
    _git(local_repo, "push", "origin", "main")

    # Create feature branch, push to origin, merge to main on origin
    _git(local_repo, "checkout", "-b", "feature/remote-synced")
    (local_repo / "feature.txt").write_text("feature content\n", encoding="utf-8")
    _git(local_repo, "add", "feature.txt")
    _git(local_repo, "commit", "-m", "commit feature")
    _git(local_repo, "push", "origin", "feature/remote-synced")

    # Merge into main locally and push
    _git(local_repo, "checkout", "main")
    _git(local_repo, "merge", "--no-ff", "feature/remote-synced", "-m", "merge remote synced")
    _git(local_repo, "push", "origin", "main")

    # Delete the branch on remote to simulate PR merge & remote branch cleanup
    _git(local_repo, "push", "origin", "--delete", "feature/remote-synced")

    # Run pruner with --prune-remote and target origin/main
    proc = subprocess.run(
        [
            sys.executable,
            str(PRUNER_SCRIPT),
            "--repo",
            str(local_repo),
            "--target",
            "origin/main",
            "--prune-remote",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "[OK] Remote prune completed against origin." in proc.stdout
    assert "[OK] Deleted merged local branch: feature/remote-synced" in proc.stdout
