#!/usr/bin/env python3
"""Read-only guard for deleting completed feature branches.

Deletion is allowed only after the named branch is an ancestor of the protected
integration branch.  The guard intentionally does not merge, push, fetch, or
delete anything; CI and the PR provider remain the authoritative merge gate.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


PROTECTED_BRANCHES = ("main", "master")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )


def _ref_exists(repo: Path, ref: str) -> bool:
    return _git(repo, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def _integration_ref(repo: Path, *, remote: bool) -> str | None:
    candidates = ("refs/remotes/origin/main", "refs/heads/main") if remote else ("refs/heads/main",)
    return next((ref for ref in candidates if _ref_exists(repo, ref)), None)


def _deleted_branches(command: str) -> tuple[list[str], bool]:
    """Return named local/remote branch deletions and whether they target a remote."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return [], False
    for index, token in enumerate(tokens):
        if token != "git" or index + 2 >= len(tokens):
            continue
        operation = tokens[index + 1 :]
        if operation[0] == "branch" and any(flag in {"-d", "-D", "--delete"} for flag in operation[1:]):
            delete_at = next(i for i, flag in enumerate(operation[1:], 1) if flag in {"-d", "-D", "--delete"})
            return [item for item in operation[delete_at + 1 :] if not item.startswith("-")], False
        if operation[0] == "push" and "--delete" in operation:
            delete_at = operation.index("--delete")
            return [item for item in operation[delete_at + 1 :] if not item.startswith("-")], True
    return [], False


def validate_delete_command(command: str, *, repo: Path) -> tuple[bool, str]:
    """Fail closed when a branch deletion is not proven merged into main."""
    branches, remote = _deleted_branches(command)
    if not branches:
        return True, "no branch deletion requested"
    integration = _integration_ref(repo, remote=remote)
    if integration is None:
        return False, "main integration reference is unavailable"
    current = _git(repo, "branch", "--show-current").stdout.strip()
    for branch in branches:
        if branch in PROTECTED_BRANCHES:
            return False, f"protected branch cannot be deleted: {branch}"
        ref = f"refs/heads/{branch}"
        if not _ref_exists(repo, ref):
            return False, f"branch is unavailable for merge verification: {branch}"
        if _git(repo, "merge-base", "--is-ancestor", ref, integration).returncode != 0:
            return False, f"branch is not merged into main: {branch}"
        if branch == current:
            return False, f"current branch cannot be deleted: {branch}"
    return True, "branch is merged into main and may be deleted"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-command", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    allowed, reason = validate_delete_command(args.check_command, repo=args.repo.resolve())
    print(f"[OK] {reason}" if allowed else f"[ERROR] {reason}")
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
