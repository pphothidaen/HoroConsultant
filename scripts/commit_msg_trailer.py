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
      1. Subject is not exempt per BYPASS_SUBJECT_PREFIXES, which mirrors the
         guard's is_release_or_gov list. The helper must never skip a subject
         the guard still demands a trailer for.
      2. No real `Test-Baseline: <sha>` trailer is already present. A prose
         mention inside a body line does not count.
      3. EXACTLY ONE committed manifest's allowed_source_paths covers EVERY
         staged path that is neither a test nor a manifest -- the same set the
         guard calls non_test_paths. Covering only SOME of them would make the
         guard emit SOURCE_PATH_OUTSIDE_MANIFEST, so partial coverage is a
         no-op, not a success. Zero or more than one manifest => no-op,
         because the baseline would be ambiguous.
      4. That manifest has EXACTLY ONE add-commit in history (same definition
         the verifier uses), so the trailer names the baseline the guard will
         actually check against.

    The trailer is appended as its own trailing paragraph so it is a standalone
    line. The guard compares whole stripped lines, so a trailer glued onto the
    preceding line is invisible to it.

    If any condition fails the message is returned BYTE-IDENTICAL. This helper
    never raises into the commit path: a failure must not block or corrupt a
    commit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TRAILER_PREFIX = "Test-Baseline:"
MANIFEST_PREFIX = "plans/test_provenance/"

# A real, already-present trailer: a standalone line naming a full object SHA.
# Used so body prose that merely mentions the format is not mistaken for one.
_SHA = r"[0-9a-f]{40,64}"
_TRAILER_LINE_RE = re.compile(rf"{re.escape(TRAILER_PREFIX)} {_SHA}")

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

# Keep in sync with the release/governance bypass list in the guard
# (is_release_or_gov in verify_history). This list must be a SUBSET of the
# guard's: a prefix here that the guard does NOT exempt means the helper stays
# silent on a commit the guard still demands a trailer for, which surfaces as
# SOURCE_COMMIT_MISSING_BASELINE_TRAILER.
BYPASS_SUBJECT_PREFIXES = (
    "feat(release):",
    "docs(release):",
    "docs(governance):",
    "fix(governance):",
    "build(hf):",
    "merge:",
    "Merge",
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


def _is_governed_path(path: str) -> bool:
    """A path the guard holds a trailer-carrying commit to.

    Mirrors the guard's non_test_paths filter exactly: it excludes tests and
    manifests, but NOT documentation. The guard applies SOURCE_PATH_OUTSIDE_MANIFEST
    to a docs/ file sharing the commit, so the helper must too.
    """
    return not (_is_test_path(path) or _is_manifest_path(path))


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
    """True when the subject is exempt or a real trailer is already present.

    "Real" means a standalone line of the form `Test-Baseline: <sha>`. A body
    line that merely mentions the format (e.g. prose documenting it) must not
    count, or the hook silently no-ops on a commit whose baseline is provable.
    """
    subject = message.lstrip().splitlines()[0] if message.strip() else ""
    if subject.startswith(BYPASS_SUBJECT_PREFIXES):
        return True
    return any(_TRAILER_LINE_RE.fullmatch(line.strip())
               for line in message.splitlines())


def _resolve_baseline(repo: Path, staged: list[str]) -> str | None:
    """Return the single provable baseline SHA for these staged paths, or None.

    `governed` mirrors the guard's non_test_paths: every staged path that is
    neither a test nor a manifest. The guard holds a trailer-carrying commit to
    ALL of them, so the helper requires a manifest that covers all of them too.
    Requiring only partial coverage would make the helper attach a trailer that
    the guard rejects with SOURCE_PATH_OUTSIDE_MANIFEST -- strictly worse than
    staying silent, because the commit then looks baseline-stamped while failing
    the gate.
    """
    governed = [p for p in staged if _is_governed_path(p)]
    if not governed:
        return None

    candidates: list[str] = []
    for manifest_path in _committed_manifests(repo):
        manifest = _read_manifest(repo, manifest_path)
        if not manifest:
            continue
        allowed = manifest.get("allowed_source_paths")
        if not isinstance(allowed, list):
            continue
        if all(_matches_allowed(p, allowed) for p in governed):
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
    """Return (new_message, changed). Never raises.

    The trailer goes in its own trailing paragraph so it is a standalone line.
    The guard compares whole stripped lines, so a trailer concatenated onto the
    previous line ("Ticket: KAN-179Test-Baseline: <sha>") is invisible to it and
    the commit is reported as missing its trailer.
    """
    try:
        trailer = compute_trailer(repo, message)
        if not trailer:
            return message, False
        body = message.rstrip("\n")
        if not body:
            return f"{trailer}\n", True
        return f"{body}\n\n{trailer}\n", True
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
