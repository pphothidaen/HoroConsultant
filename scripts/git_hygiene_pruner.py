#!/usr/bin/env python3
"""Git hygiene pruner.

Safely detects and prunes local git branches that have already been merged into
a target branch (default: origin/main or main).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTECTED_BRANCHES: set[str] = {
    "main",
    "master",
    "HEAD",
    "dev",
    "develop",
}


def run_git(args: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    """Execute a git command in the target repository directory."""
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repository(repo: Path) -> bool:
    """Check if the given directory is a valid git repository."""
    result = run_git(["rev-parse", "--is-inside-work-tree"], repo)
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_current_branch(repo: Path) -> str | None:
    """Return the currently checked-out branch name, or None if in detached HEAD."""
    result = run_git(["branch", "--show-current"], repo)
    if result.returncode == 0:
        branch = result.stdout.strip()
        if branch:
            return branch
    return None


def get_local_branches(repo: Path) -> list[str]:
    """Return list of all local branch names."""
    result = run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads/"], repo)
    if result.returncode != 0:
        return []
    branches = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return branches


def resolve_target_ref(repo: Path, target: str) -> str | None:
    """Resolve target branch name to an existing git reference.

    If target is 'origin/main' and doesn't exist, attempts fallback to 'main' or 'master'.
    """
    candidates = [
        target,
        f"refs/remotes/{target}",
        f"refs/heads/{target}",
    ]
    for candidate in candidates:
        if run_git(["rev-parse", "--verify", "--quiet", candidate], repo).returncode == 0:
            return candidate

    if target in {"origin/main", "refs/remotes/origin/main"}:
        fallbacks = ["refs/heads/main", "main", "refs/remotes/origin/master", "refs/heads/master", "master"]
        for fallback in fallbacks:
            if run_git(["rev-parse", "--verify", "--quiet", fallback], repo).returncode == 0:
                return fallback

    return None


def run_remote_prune(repo: Path, verbose: bool = False) -> bool:
    """Run remote prune on origin if remote is configured."""
    remotes = run_git(["remote"], repo)
    if remotes.returncode != 0 or "origin" not in remotes.stdout.split():
        if verbose:
            print("[INFO] Remote 'origin' not configured; skipping remote prune.")
        return True

    res = run_git(["fetch", "--prune", "origin"], repo)
    if res.returncode == 0:
        print("[OK] Remote prune completed against origin.")
        return True
    else:
        print(f"[WARNING] Remote prune failed: {res.stderr.strip() or res.stdout.strip()}")
        return False


def is_branch_merged(repo: Path, branch: str, target_ref: str) -> bool:
    """Check if the given branch is merged (ancestor of) target_ref."""
    branch_ref = f"refs/heads/{branch}"
    res = run_git(["merge-base", "--is-ancestor", branch_ref, target_ref], repo)
    return res.returncode == 0


def delete_local_branch(repo: Path, branch: str) -> tuple[bool, str]:
    """Safely delete a local branch using -d, with -D fallback only if ancestry is verified."""
    res_d = run_git(["branch", "-d", branch], repo)
    if res_d.returncode == 0:
        return True, res_d.stdout.strip()

    res_D = run_git(["branch", "-D", branch], repo)
    if res_D.returncode == 0:
        return True, res_D.stdout.strip()

    err_msg = res_D.stderr.strip() or res_d.stderr.strip() or "Deletion failed."
    return False, err_msg


def prune_git_hygiene(
    repo: Path,
    target: str = "origin/main",
    dry_run: bool = False,
    prune_remote: bool = False,
    verbose: bool = False,
    protected_branches: set[str] | None = None,
) -> dict[str, Any]:
    """Execute git hygiene pruning on local branches."""
    repo = repo.resolve()
    protected = set(PROTECTED_BRANCHES)
    if protected_branches:
        protected.update(protected_branches)

    report: dict[str, Any] = {
        "success": False,
        "repo": str(repo),
        "target": target,
        "resolved_target": None,
        "dry_run": dry_run,
        "deleted": [],
        "dry_run_candidates": [],
        "preserved_unmerged": [],
        "skipped_protected": [],
        "errors": [],
    }

    if not is_git_repository(repo):
        err = f"Directory is not a valid git repository: {repo}"
        print(f"[ERROR] {err}")
        report["errors"].append(err)
        return report

    if prune_remote:
        run_remote_prune(repo, verbose=verbose)

    resolved_target = resolve_target_ref(repo, target)
    if not resolved_target:
        err = f"Target ref '{target}' could not be resolved in {repo}"
        print(f"[ERROR] {err}")
        report["errors"].append(err)
        return report

    report["resolved_target"] = resolved_target
    print(f"[INFO] Target integration ref: {resolved_target}")

    current_branch = get_current_branch(repo)
    if current_branch:
        protected.add(current_branch)
        if verbose:
            print(f"[INFO] Current checked-out branch (protected): {current_branch}")

    local_branches = get_local_branches(repo)
    if verbose:
        print(f"[INFO] Found {len(local_branches)} local branch(es).")

    for branch in local_branches:
        if branch in protected or branch == target or branch == resolved_target:
            report["skipped_protected"].append(branch)
            if verbose:
                print(f"[INFO] Skipping protected branch: {branch}")
            continue

        if is_branch_merged(repo, branch, resolved_target):
            if dry_run:
                report["dry_run_candidates"].append(branch)
                print(f"[DRY-RUN] Local branch '{branch}' is merged into '{resolved_target}' and would be deleted.")
            else:
                success, msg = delete_local_branch(repo, branch)
                if success:
                    report["deleted"].append(branch)
                    print(f"[OK] Deleted merged local branch: {branch}")
                else:
                    err = f"Failed to delete branch '{branch}': {msg}"
                    report["errors"].append(err)
                    print(f"[ERROR] {err}")
        else:
            report["preserved_unmerged"].append(branch)
            if verbose:
                print(f"[INFO] Branch '{branch}' is not merged into '{resolved_target}'; preserving.")

    report["success"] = len(report["errors"]) == 0
    summary_mode = "DRY-RUN" if dry_run else "DONE"
    print(
        f"[INFO] Git hygiene pruner summary [{summary_mode}]: "
        f"deleted={len(report['deleted'])}, "
        f"dry_run={len(report['dry_run_candidates'])}, "
        f"preserved={len(report['preserved_unmerged'])}, "
        f"protected={len(report['skipped_protected'])}, "
        f"errors={len(report['errors'])}"
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely detect and prune local git branches merged into target branch."
    )
    parser.add_argument(
        "--target",
        type=str,
        default="origin/main",
        help="Target branch to compare against (default: origin/main with fallback to main).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate pruning without deleting any branches.",
    )
    parser.add_argument(
        "--prune-remote",
        action="store_true",
        help="Fetch and prune remote tracking references from origin first.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to the git repository (default: current working directory).",
    )

    args = parser.parse_args()

    result = prune_git_hygiene(
        repo=args.repo,
        target=args.target,
        dry_run=args.dry_run,
        prune_remote=args.prune_remote,
        verbose=args.verbose,
    )

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
