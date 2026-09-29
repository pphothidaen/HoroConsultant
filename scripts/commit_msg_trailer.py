#!/usr/bin/env python3
"""Append a `Test-Baseline: <sha>` trailer to a commit message -- KAN-179.

Invoked by .githooks/prepare-commit-msg. The existing .githooks/commit-msg
hook stays strictly read-only; this is a separate, dedicated hook.

WHY THIS EXISTS
    scripts/test_provenance_guard.py emits SOURCE_COMMIT_MISSING_BASELINE_TRAILER
    for any commit AFTER a manifest's baseline that touches one of that
    manifest's `allowed_source_paths` without carrying the exact trailer
    `Test-Baseline: <baseline>`. The baseline is the manifest's unique add-commit
    (_find_baseline). This hook computes and appends that trailer automatically.

THE TDD SHAPE THIS SUPPORTS (and why "staged manifest" is the wrong trigger)
    RED commit   : stages the test file AND the manifest -> becomes the baseline.
    GREEN commit : stages only SOURCE files, no manifest.
    Only the GREEN commit needs the trailer. Requiring a staged manifest would
    therefore never fire in practice, so the trigger is instead: the staged
    source paths are covered by a committed manifest's allowed_source_paths.

DESIGN CONTRACT -- never guess a baseline
    The trailer is appended ONLY when ALL hold:
      1. Subject is not merge/release/governance/build/revert/fixup.
      2. No `Test-Baseline:` trailer is already present.
      3. At least one staged path is a real source path (not a test, manifest,
         or docs-only path).
      4. EXACTLY ONE committed manifest's allowed_source_paths covers those
         staged source paths. Zero or more than one => no-op, because the
         baseline would be ambiguous.
      5. That manifest has EXACTLY ONE add-commit in history (same definition
         the verifier uses), so the trailer names the baseline the guard will
         actually check against.

    If any condition fails the message is returned BYTE-IDENTICAL. This helper
    never raises into the commit path: a failure must not block or corrupt a
    commit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TRAILER_PREFIX = "Test-Baseline:"
MANIFEST_PREFIX = "plans/test_provenance/"

# Keep in sync with TEST_PREFIXES in scripts/test_provenance_guard.py.
TEST_PREFIXES = (
    "tests/",
    "project/tests/",
    "TDD-HORO-v3.0/tests/",
    "tools/agent-broker/Tests/",
)

# Keep in sync with DOC_PREFIXES / DOC_FILES in scripts/test_provenance_guard.py.
DOC_PREFIXES = (
    "docs/",
    "plans/",
    ".agents/",
    ".agy/",
    ".antigravity/",
    ".claude/",
    ".codex/",
    ".github/workflows/",
)

# Keep in sync with the release/governance bypass list in the guard.
BYPASS_SUBJECT_PREFIXES = (
    "feat(release):",
    "docs(release):",
    "docs(governance):",
    "fix(governance):",
    "build(hf):",
    "merge:",
    "Merge",
    "Revert",
    "fixup!",
    "squash!",
    "amend!",
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True
    )


def _staged_paths(repo: Path) -> list[str]:
    """Paths this commit will contain.

    NOTE (KAN-179): during `prepare-commit-msg` git has NOT yet populated the
    index relative to the new HEAD -- `git diff --cached` returns nothing, and
    `git status` is already clean. The content of the commit is therefore
    recovered from the index itself (`git diff --cached` against HEAD, falling
    back to the index tree vs HEAD) rather than from the worktree, so untracked
    scratch files are never mistaken for commit content.
    """
    # Preferred: index vs HEAD (works once HEAD exists).
    result = _git(repo, "diff", "--cached", "--name-only")
    if result.returncode == 0:
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if paths:
            return paths

    # Fallback: read the index tree directly and diff it against HEAD.
    head = _git(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        return []
    diff = _git(repo, "diff", "--name-only", head.stdout.strip(), "--cached")
    if diff.returncode != 0:
        return []
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _is_test_path(path: str) -> bool:
    return path.startswith(TEST_PREFIXES)


def _is_manifest_path(path: str) -> bool:
    return path.startswith(MANIFEST_PREFIX) and path.endswith(".json")


def _is_docs_only_path(path: str) -> bool:
    return path.endswith(".md") or path.startswith(DOC_PREFIXES)


def _is_source_path(path: str) -> bool:
    """A real source path: not a test, not a manifest, not documentation."""
    return not (
        _is_test_path(path) or _is_manifest_path(path) or _is_docs_only_path(path)
    )


def _matches_allowed(path: str, patterns) -> bool:
    """Same semantics as _matches_allowed in scripts/test_provenance_guard.py."""
    for raw in patterns or []:
        if not isinstance(raw, str):
            continue
        pattern = _normalize(raw)
        if pattern.endswith("/") and path.startswith(pattern):
            return True
        if path == pattern or path.startswith(pattern.rstrip("/") + "/"):
            return True
    return False


def _find_baseline(repo: Path, manifest_path: str) -> str | None:
    """Exactly one add-commit, else None. Mirrors the guard's _find_baseline."""
    result = _git(repo, "log", "--diff-filter=A", "--format=%H", "--", manifest_path)
    if result.returncode != 0:
        return None
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(commits) != 1:
        return None
    return commits[0]


def _committed_manifests(repo: Path) -> list[str]:
    result = _git(repo, "ls-tree", "-r", "--name-only", "HEAD", MANIFEST_PREFIX)
    if result.returncode != 0:
        return []
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".json")
    ]


def _read_manifest(repo: Path, path: str) -> dict | None:
    result = _git(repo, "show", f"HEAD:{path}")
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def should_skip(message: str) -> bool:
    subject = message.lstrip().splitlines()[0] if message.strip() else ""
    if subject.startswith(BYPASS_SUBJECT_PREFIXES):
        return True
    return any(
        line.strip().startswith(TRAILER_PREFIX) for line in message.splitlines()
    )


def _resolve_baseline(repo: Path, staged: list[str]) -> str | None:
    """Return the single provable baseline SHA for these staged paths, or None."""
    source_paths = [p for p in staged if _is_source_path(p)]
    if not source_paths:
        return None

    candidates: list[str] = []
    for manifest_path in _committed_manifests(repo):
        manifest = _read_manifest(repo, manifest_path)
        if not manifest:
            continue
        allowed = manifest.get("allowed_source_paths")
        if not isinstance(allowed, list):
            continue
        if any(_matches_allowed(p, allowed) for p in source_paths):
            candidates.append(manifest_path)

    if len(candidates) != 1:
        # Zero: nothing governs these paths. >1: ambiguous, refuse to guess.
        return None

    return _find_baseline(repo, candidates[0])


def compute_trailer(repo: Path, message: str) -> str | None:
    """Return the full `Test-Baseline: <sha>` trailer, or None to no-op."""
    if should_skip(message):
        return None
    baseline = _resolve_baseline(repo, _staged_paths(repo))
    if not baseline:
        return None
    return f"{TRAILER_PREFIX} {baseline}"


def append_trailer(repo: Path, message: str, source: str | None = None) -> tuple[str, bool]:
    """Return (new_message, changed). Never raises."""
    try:
        trailer = compute_trailer(repo, message)
        if not trailer:
            return message, False
        body = message.rstrip("\n")
        if not body.endswith("\n\n"):
            body = body + "\n" if "\n\n" not in body else body
        return f"{body}{trailer}\n", True
    except Exception:  # fail-safe: never corrupt or block a commit
        return message, False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append a Test-Baseline trailer when it is provable."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--message-file", required=True)
    args = parser.parse_args(argv)

    path = Path(args.message_file)
    try:
        original = path.read_text(encoding="utf-8")
    except OSError:
        return 0  # never block a commit we cannot read

    updated, changed = append_trailer(Path(args.repo).resolve(), original, None)
    if changed and updated != original:
        try:
            path.write_text(updated, encoding="utf-8")
        except OSError:
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
