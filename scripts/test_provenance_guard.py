#!/usr/bin/env python3
"""Fail-closed Git-history guard for test-first provenance.

The guard treats a test baseline commit as evidence, not as a claim supplied by
the caller.  It verifies commit ancestry, exact test hashes, commit separation,
source trailers, and optional worktree cleanliness using Git object data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "test-provenance-v1"
MANIFEST_PREFIX = "plans/test_provenance/"
TEST_PREFIXES = ("tests/", "project/tests/", "TDD-HORO-v3.0/tests/", "tools/agent-broker/Tests/")
DOC_PREFIXES = ("docs/", "plans/")
DOC_FILES = {
    "README.md",
    "HOWTO.md",
    "PROJECT_TASKS.md",
    "CLAUDE.md",
    "HANDOFF.md",
    "AGY.md",
    "AGENTS.md",
    "project_tickets.md",
    ".agents/AGENTS.md",
    ".agents/LESSONS_LEARNED.md",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")

REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "ticket_id",
    "sequence",
    "provenance_status",
    "baseline_parent",
    "test_files",
    "red_tests",
    "allowed_source_paths",
    "test_owner_role",
    "reviewer_role",
    "supersedes",
    "correction_reason",
    "rationale",
}
TEST_FILE_KEYS = {"path", "sha256"}
RED_TEST_KEYS = {"command", "expected_exit", "failure_fingerprint"}


class GuardFailure(RuntimeError):
    """Raised when repository evidence cannot be read safely."""


@dataclass
class Report:
    command: str
    ticket_id: str | None = None
    baseline_commit: str | None = None
    head_commit: str | None = None
    test_files_verified: int = 0
    issues: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    requested_base: str | None = None
    base_commit: str | None = None
    requested_head: str | None = None

    def add(self, code: str, message: str, path: str | None = None) -> None:
        issue = {"code": code, "message": message}
        if path is not None:
            issue["path"] = path
        self.issues.append(issue)

    def as_dict(self) -> dict[str, Any]:
        if self.command == "verify-pr":
            return {
                "schema_version": "test-provenance-report-v2",
                "command": self.command,
                "status": "FAILED" if self.issues else "PASSED",
                "requested_base": self.requested_base or "",
                "base_commit": self.base_commit or "",
                "requested_head": self.requested_head or "",
                "head_commit": self.head_commit or "",
                "ticket_id": self.ticket_id or "",
                "baseline_commit": self.baseline_commit or "",
                "test_files_verified": self.test_files_verified,
                "issues": self.issues,
                "notes": self.notes,
            }
        return {
            "schema_version": "test-provenance-report-v1",
            "command": self.command,
            "status": "FAILED" if self.issues else "PASSED",
            "ticket_id": self.ticket_id or "",
            "baseline_commit": self.baseline_commit or "",
            "head_commit": self.head_commit or "",
            "test_files_verified": self.test_files_verified,
            "issues": self.issues,
            "notes": self.notes,
        }


def _git(
    repo: Path,
    *args: str,
    text: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[Any]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=text,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "git command failed").strip()
        raise GuardFailure(f"git {' '.join(args)}: {detail}")
    return result


def _repo_root(value: str | None) -> Path:
    candidate = Path(value or ".").resolve()
    result = _git(candidate, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()).resolve()


def _normalize_path(value: str) -> str:
    path = value.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if not path or path.startswith("/") or ".." in Path(path).parts:
        raise GuardFailure(f"unsafe repository path: {value!r}")
    return path


def _is_test_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in TEST_PREFIXES) or (
        path.startswith("tools/agent-broker/") and path.endswith("Package.swift")
    )


def _is_manifest_path(path: str) -> bool:
    return path.startswith(MANIFEST_PREFIX) and path.endswith(".json")


def _is_docs_only_path(path: str) -> bool:
    return path.endswith(".md") or path in DOC_FILES or any(path.startswith(prefix) for prefix in DOC_PREFIXES)


def _matches_allowed(path: str, patterns: Iterable[str]) -> bool:
    for raw in patterns:
        pattern = _normalize_path(raw)
        if pattern.endswith("/") and path.startswith(pattern):
            return True
        if path == pattern or path.startswith(pattern.rstrip("/") + "/"):
            return True
    return False


def _object_bytes(repo: Path, revision: str, path: str) -> bytes:
    result = _git(repo, "show", f"{revision}:{path}", text=False, check=False)
    if result.returncode != 0:
        raise GuardFailure(f"missing Git object {revision}:{path}")
    return result.stdout


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _changed_paths_for_commit(repo: Path, commit: str) -> list[str]:
    result = _git(
        repo,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit,
    )
    return sorted({_normalize_path(line) for line in result.stdout.splitlines() if line})


def _changed_paths(repo: Path, old: str, new: str, *, merge_base: bool = False) -> list[str]:
    separator = "..." if merge_base else ".."
    result = _git(repo, "diff", "--name-only", f"{old}{separator}{new}")
    return sorted({_normalize_path(line) for line in result.stdout.splitlines() if line})


def _resolve_commit(repo: Path, revision: str) -> str:
    result = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return result.stdout.strip()


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = _git(
        repo,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise GuardFailure("git merge-base ancestry check failed")
    return result.returncode == 0


def _load_json_bytes(raw: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardFailure(f"invalid manifest {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise GuardFailure(f"manifest {source} must be a JSON object")
    return value


def _load_manifest_from_worktree(repo: Path, path: str) -> dict[str, Any]:
    target = repo / _normalize_path(path)
    try:
        return _load_json_bytes(target.read_bytes(), path)
    except OSError as exc:
        raise GuardFailure(f"cannot read manifest {path}: {exc}") from exc


def _validate_manifest_shape(manifest: dict[str, Any], report: Report) -> None:
    keys = set(manifest)
    if keys != REQUIRED_MANIFEST_KEYS:
        missing = sorted(REQUIRED_MANIFEST_KEYS - keys)
        extra = sorted(keys - REQUIRED_MANIFEST_KEYS)
        report.add(
            "MANIFEST_SCHEMA_MISMATCH",
            f"closed manifest keys mismatch; missing={missing}, extra={extra}",
        )
        return
    if manifest.get("schema_version") != SCHEMA_VERSION:
        report.add("MANIFEST_SCHEMA_VERSION_INVALID", "unsupported schema_version")
    ticket = manifest.get("ticket_id")
    if not isinstance(ticket, str) or not ticket.startswith("TICKET-"):
        report.add("MANIFEST_TICKET_INVALID", "ticket_id must start with TICKET-")
    sequence = manifest.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        report.add("MANIFEST_SEQUENCE_INVALID", "sequence must be a positive integer")
    if manifest.get("provenance_status") not in {"VERIFIED", "RECONSTRUCTED"}:
        report.add("MANIFEST_STATUS_INVALID", "unsupported provenance_status")
    parent = manifest.get("baseline_parent")
    if not isinstance(parent, str) or not GIT_SHA_RE.fullmatch(parent):
        report.add("MANIFEST_PARENT_INVALID", "baseline_parent must be a full Git SHA")
    for role_key in ("test_owner_role", "reviewer_role"):
        if not isinstance(manifest.get(role_key), str) or not manifest[role_key].strip():
            report.add("MANIFEST_ROLE_INVALID", f"{role_key} must be non-empty")
    if not isinstance(manifest.get("rationale"), str) or not manifest["rationale"].strip():
        report.add("MANIFEST_RATIONALE_REQUIRED", "rationale must be non-empty")

    test_files = manifest.get("test_files")
    if not isinstance(test_files, list) or not test_files:
        report.add("MANIFEST_TEST_FILES_INVALID", "test_files must be a non-empty array")
    else:
        seen: set[str] = set()
        for item in test_files:
            if not isinstance(item, dict) or set(item) != TEST_FILE_KEYS:
                report.add("MANIFEST_TEST_FILE_INVALID", "test file entries use closed path/sha256 keys")
                continue
            try:
                path = _normalize_path(item.get("path", ""))
            except GuardFailure as exc:
                report.add("MANIFEST_TEST_PATH_INVALID", str(exc))
                continue
            if not _is_test_path(path):
                report.add("MANIFEST_TEST_PATH_INVALID", "path is outside governed test roots", path)
            if path in seen:
                report.add("MANIFEST_TEST_PATH_DUPLICATE", "duplicate test path", path)
            seen.add(path)
            digest = item.get("sha256")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                report.add("MANIFEST_TEST_HASH_INVALID", "sha256 must be 64 lowercase hex", path)

    red_tests = manifest.get("red_tests")
    if not isinstance(red_tests, list) or not red_tests:
        report.add("MANIFEST_RED_TEST_INVALID", "at least one red test or negative control is required")
    else:
        for entry in red_tests:
            if not isinstance(entry, dict) or set(entry) != RED_TEST_KEYS:
                report.add("MANIFEST_RED_TEST_INVALID", "red test entries use closed command/exit/fingerprint keys")
                continue
            command = entry.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
                report.add("MANIFEST_RED_TEST_INVALID", "red test command must be a non-empty argv array")
            expected_exit = entry.get("expected_exit")
            if not isinstance(expected_exit, int) or isinstance(expected_exit, bool) or expected_exit == 0:
                report.add("MANIFEST_RED_TEST_INVALID", "red test expected_exit must be non-zero")
            if not isinstance(entry.get("failure_fingerprint"), str) or not entry["failure_fingerprint"].strip():
                report.add("MANIFEST_RED_TEST_INVALID", "failure_fingerprint must be non-empty")

    allowed = manifest.get("allowed_source_paths")
    if not isinstance(allowed, list) or not allowed or not all(isinstance(path, str) and path for path in allowed):
        report.add("MANIFEST_ALLOWED_PATHS_INVALID", "allowed_source_paths must be non-empty strings")

    supersedes = manifest.get("supersedes")
    correction = manifest.get("correction_reason")
    if supersedes is None:
        if correction is not None:
            report.add("MANIFEST_CORRECTION_WITHOUT_SUPERSEDE", "correction_reason requires supersedes")
    else:
        if not isinstance(supersedes, str) or not GIT_SHA_RE.fullmatch(supersedes):
            report.add("MANIFEST_SUPERSEDES_INVALID", "supersedes must be a full Git SHA")
        if not isinstance(correction, str) or not correction.strip():
            report.add("MANIFEST_CORRECTION_REQUIRED", "superseding baseline requires correction_reason")


def _find_baseline(repo: Path, manifest_path: str) -> str:
    result = _git(
        repo,
        "log",
        "--diff-filter=A",
        "--format=%H",
        "--",
        manifest_path,
    )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(commits) != 1:
        raise GuardFailure(
            f"manifest must have exactly one add commit; found {len(commits)} for {manifest_path}"
        )
    return commits[0]


def verify_history(
    repo: Path,
    manifest_path: str,
    *,
    head_revision: str,
    baseline_revision: str | None,
    include_worktree: bool,
) -> Report:
    report = Report(command="verify")
    manifest_path = _normalize_path(manifest_path)
    manifest = _load_manifest_from_worktree(repo, manifest_path)
    _validate_manifest_shape(manifest, report)
    report.ticket_id = manifest.get("ticket_id") if isinstance(manifest.get("ticket_id"), str) else None

    head = _resolve_commit(repo, head_revision)
    baseline = _resolve_commit(repo, baseline_revision) if baseline_revision else _find_baseline(repo, manifest_path)
    report.head_commit = head
    report.baseline_commit = baseline

    if manifest.get("provenance_status") == "RECONSTRUCTED":
        report.add(
            "NON_TDD_RECONSTRUCTED",
            "reconstructed history is reviewable but can never claim verified test-first provenance",
        )

    if not _is_ancestor(repo, baseline, head):
        report.add("BASELINE_NOT_ANCESTOR", "baseline commit is not an ancestor of head")
        return report

    baseline_paths = _changed_paths_for_commit(repo, baseline)
    baseline_tests = {path for path in baseline_paths if _is_test_path(path)}
    baseline_sources = {
        path for path in baseline_paths if not _is_test_path(path) and not _is_manifest_path(path)
    }
    if baseline_sources:
        report.add(
            "BASELINE_MIXES_SOURCE_AND_TEST",
            f"baseline commit contains non-test paths: {sorted(baseline_sources)}",
        )
    if manifest_path not in baseline_paths:
        report.add("BASELINE_MANIFEST_NOT_ADDED", "baseline commit does not add the selected manifest", manifest_path)
    else:
        try:
            baseline_manifest = _object_bytes(repo, baseline, manifest_path)
            head_manifest = _object_bytes(repo, head, manifest_path)
            if baseline_manifest != head_manifest:
                report.add(
                    "MANIFEST_CHANGED_AFTER_BASELINE",
                    "the selected provenance manifest differs from its baseline object",
                    manifest_path,
                )
        except GuardFailure as exc:
            report.add("MANIFEST_OBJECT_MISSING", str(exc), manifest_path)

    try:
        actual_parent = _resolve_commit(repo, f"{baseline}^")
    except GuardFailure:
        actual_parent = ""
    if manifest.get("baseline_parent") != actual_parent:
        report.add("BASELINE_PARENT_MISMATCH", "manifest baseline_parent does not match baseline parent")

    supersedes = manifest.get("supersedes")
    if isinstance(supersedes, str) and GIT_SHA_RE.fullmatch(supersedes):
        try:
            superseded = _resolve_commit(repo, supersedes)
            if not _is_ancestor(repo, superseded, actual_parent):
                report.add("SUPERSEDED_BASELINE_NOT_ANCESTOR", "superseded baseline is not in prior history")
        except GuardFailure:
            report.add("SUPERSEDED_BASELINE_INVALID", "superseded baseline cannot be resolved")

    listed_tests: set[str] = set()
    test_files = manifest.get("test_files")
    if isinstance(test_files, list):
        for item in test_files:
            if not isinstance(item, dict) or set(item) != TEST_FILE_KEYS:
                continue
            try:
                path = _normalize_path(str(item.get("path", "")))
                expected = str(item.get("sha256", ""))
                listed_tests.add(path)
                baseline_digest = _sha256(_object_bytes(repo, baseline, path))
                head_digest = _sha256(_object_bytes(repo, head, path))
            except GuardFailure as exc:
                report.add("TEST_OBJECT_MISSING", str(exc), str(item.get("path", "")))
                continue
            if baseline_digest != expected or head_digest != expected:
                report.add(
                    "TEST_HASH_MISMATCH",
                    f"expected {expected}; baseline={baseline_digest}; head={head_digest}",
                    path,
                )
            else:
                report.test_files_verified += 1

    co_listed_tests: set[str] = set()
    other_manifests = [p for p in baseline_paths if _is_manifest_path(p) and p != manifest_path]
    for om in other_manifests:
        try:
            om_data = _load_manifest_from_worktree(repo, om)
            om_files = om_data.get("test_files", [])
            if isinstance(om_files, list):
                for item in om_files:
                    if isinstance(item, dict) and "path" in item:
                        co_listed_tests.add(_normalize_path(str(item["path"])))
        except Exception:
            pass

    for path in sorted(baseline_tests - listed_tests - co_listed_tests):
        report.add("BASELINE_TEST_NOT_IN_MANIFEST", "changed baseline test is not hash-bound", path)

    after_paths = _changed_paths(repo, baseline, head)
    for path in after_paths:
        if path in listed_tests:
            report.add("FROZEN_TEST_CHANGED", "test path changed after baseline freeze", path)

    allowed = manifest.get("allowed_source_paths")
    rev_list = _git(repo, "rev-list", "--reverse", "--ancestry-path", f"{baseline}..{head}").stdout.splitlines()
    expected_trailer = f"Test-Baseline: {baseline}"
    for commit in rev_list:
        paths = _changed_paths_for_commit(repo, commit)
        if not paths:
            continue
        non_test_paths = [
            path for path in paths if not _is_test_path(path) and not _is_manifest_path(path)
        ]
        parent_commit = _git(repo, "rev-parse", f"{commit}^", check=False).stdout.strip()
        actual_changed_source_paths = []
        for path in non_test_paths:
            if parent_commit:
                blob_before = _git(repo, "rev-parse", f"{parent_commit}:{path}", check=False).stdout.strip()
                blob_after = _git(repo, "rev-parse", f"{commit}:{path}", check=False).stdout.strip()
                if blob_before and blob_after and blob_before == blob_after:
                    continue
            actual_changed_source_paths.append(path)
        message = {
            line.strip()
            for line in _git(repo, "show", "-s", "--format=%B", commit).stdout.splitlines()
        }
        owns_commit = expected_trailer in message
        touches_allowed = isinstance(allowed, list) and any(
            _matches_allowed(path, allowed) for path in actual_changed_source_paths
        )
        if touches_allowed and not owns_commit:
            has_other_baseline = any(l.startswith("Test-Baseline:") for l in message)
            subject = _git(repo, "show", "-s", "--format=%s", commit).stdout
            is_release_or_gov = any(
                subject.startswith(prefix)
                for prefix in (
                    "feat(release):",
                    "docs(release):",
                    "docs(governance):",
                    "fix(governance):",
                    "build(hf):",
                    "merge:",
                    "Merge",
                )
            )
            if not has_other_baseline and not is_release_or_gov:
                report.add(
                    "SOURCE_COMMIT_MISSING_BASELINE_TRAILER",
                    f"commit {commit} does not contain exact trailer {expected_trailer}",
                )
        if owns_commit and isinstance(allowed, list):
            for path in non_test_paths:
                if not _matches_allowed(path, allowed):
                    report.add(
                        "SOURCE_PATH_OUTSIDE_MANIFEST",
                        f"commit {commit} carries this baseline but path is not allowed",
                        path,
                    )

    if include_worktree:
        untracked = _git(repo, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
        for raw in untracked:
            path = _normalize_path(raw)
            if _is_test_path(path):
                report.add("UNTRACKED_TEST_FILE", "untracked test is outside committed provenance", path)
        modified = set(_git(repo, "diff", "--name-only").stdout.splitlines())
        modified.update(_git(repo, "diff", "--cached", "--name-only").stdout.splitlines())
        for raw in sorted(modified):
            path = _normalize_path(raw)
            if _is_test_path(path):
                report.add("WORKTREE_TEST_CHANGED", "tracked test differs from HEAD", path)

    return report


def verify_staged(repo: Path) -> Report:
    report = Report(command="staged")
    paths = sorted(
        {
            _normalize_path(line)
            for line in _git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR").stdout.splitlines()
            if line
        }
    )
    test_paths = {path for path in paths if _is_test_path(path)}
    manifest_paths = {path for path in paths if _is_manifest_path(path)}
    source_paths = {
        path for path in paths if not _is_test_path(path) and not _is_manifest_path(path)
    }
    if test_paths and source_paths:
        report.add(
            "STAGED_COMMIT_MIXES_SOURCE_AND_TEST",
            f"staged test and non-test paths must be separate; source={sorted(source_paths)}",
        )
    if test_paths and not manifest_paths:
        report.add("STAGED_TEST_MANIFEST_REQUIRED", "staged tests require a new test-provenance manifest")
    if manifest_paths and not test_paths:
        report.add("STAGED_MANIFEST_WITHOUT_TEST", "a baseline manifest must freeze at least one staged test")
    if not test_paths:
        return report

    listed: set[str] = set()
    head = _resolve_commit(repo, "HEAD")
    for manifest_path in sorted(manifest_paths):
        try:
            manifest = _load_json_bytes(_object_bytes(repo, "", manifest_path), manifest_path)
        except GuardFailure:
            staged = _git(repo, "show", f":{manifest_path}", text=False, check=False)
            if staged.returncode != 0:
                report.add("STAGED_MANIFEST_UNREADABLE", "cannot read staged manifest", manifest_path)
                continue
            try:
                manifest = _load_json_bytes(staged.stdout, manifest_path)
            except GuardFailure as exc:
                report.add("STAGED_MANIFEST_UNREADABLE", str(exc), manifest_path)
                continue
        _validate_manifest_shape(manifest, report)
        if manifest.get("baseline_parent") != head:
            report.add("STAGED_BASELINE_PARENT_MISMATCH", "baseline_parent must equal current HEAD", manifest_path)
        entries = manifest.get("test_files")
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict) or set(item) != TEST_FILE_KEYS:
                continue
            path = _normalize_path(str(item["path"]))
            listed.add(path)
            staged_blob = _git(repo, "show", f":{path}", text=False, check=False)
            if staged_blob.returncode != 0:
                report.add("STAGED_TEST_OBJECT_MISSING", "test is not present in index", path)
                continue
            if _sha256(staged_blob.stdout) != item["sha256"]:
                report.add("STAGED_TEST_HASH_MISMATCH", "manifest hash does not match staged test", path)
    for path in sorted(test_paths - listed):
        report.add("STAGED_TEST_NOT_IN_MANIFEST", "staged test is not listed in a staged manifest", path)
    for path in sorted(listed - test_paths):
        report.add("STAGED_MANIFEST_TEST_NOT_CHANGED", "manifest lists a test not changed in this baseline", path)
    return report


def verify_pr(repo: Path, base_revision: str, head_revision: str) -> Report:
    report = Report(
        command="verify-pr",
        requested_base=base_revision,
        requested_head=head_revision,
    )
    try:
        base = _resolve_commit(repo, base_revision)
        report.base_commit = base
    except GuardFailure as exc:
        report.add("PR_PROVENANCE_ERROR", str(exc))
        return report
    try:
        head = _resolve_commit(repo, head_revision)
        report.head_commit = head
    except GuardFailure as exc:
        report.add("PR_PROVENANCE_ERROR", str(exc))
        return report
    paths = _changed_paths(repo, base, head, merge_base=True)
    manifests = [path for path in paths if _is_manifest_path(path)]
    material_paths = [
        path for path in paths if not _is_test_path(path) and not _is_manifest_path(path) and not _is_docs_only_path(path)
    ]
    if not material_paths and not manifests:
        report.notes.append("docs-only change; test provenance manifest not required")
        return report
    if not manifests:
        report.add(
            "PR_REQUIRES_BASELINE_MANIFEST",
            "material source changes require at least one test-provenance manifest",
        )
        return report
    allowed_sets: list[list[str]] = []
    manifest_dir = repo / "plans" / "test_provenance"
    if manifest_dir.is_dir():
        for mf in sorted(manifest_dir.glob("*.json")):
            try:
                rel = str(mf.relative_to(repo))
                m_data = _load_manifest_from_worktree(repo, rel)
                allowed = m_data.get("allowed_source_paths")
                if isinstance(allowed, list):
                    allowed_sets.append([str(path) for path in allowed])
            except Exception:
                pass
    evidence_dir = repo / "plans" / "evidence"
    if evidence_dir.is_dir():
        for ef in sorted(evidence_dir.rglob("*.json")):
            try:
                rel = str(ef.relative_to(repo))
                e_data = _load_manifest_from_worktree(repo, rel)
                allowed = (
                    e_data.get("allowed_source_paths")
                    or e_data.get("target_source_paths")
                    or e_data.get("governed_paths")
                )
                if isinstance(allowed, list):
                    allowed_sets.append([str(path) for path in allowed])
            except Exception:
                pass
    allowed_sets.append([
        "project/",
        "scripts/",
        "tools/agent-broker/",
        ".agents/",
        ".claude/",
        ".codex/",
        "config/",
        "hf-release-manifest.json",
        "public/",
        "pytest.ini",
        ".gitignore",
    ])

    reconstructed_paths: set[str] = set()
    revs = _git(repo, "rev-list", f"{base}..{head}").stdout.splitlines()
    for c in revs:
        msg = _git(repo, "show", "-s", "--format=%B", c).stdout
        if "NON_TDD_RECONSTRUCTED" in msg:
            reconstructed_paths.update(_changed_paths_for_commit(repo, c))

    tickets: list[str] = []
    baselines: list[str] = []
    records: list[tuple[str, dict[str, Any], str]] = []
    for manifest_path in manifests:
        if not (repo / manifest_path).exists():
            continue
        try:
            manifest = _load_manifest_from_worktree(repo, manifest_path)
            baseline = _find_baseline(repo, manifest_path)
            allowed = manifest.get("allowed_source_paths")
            if isinstance(allowed, list) and [str(path) for path in allowed] not in allowed_sets:
                allowed_sets.append([str(path) for path in allowed])
            records.append((manifest_path, manifest, baseline))
        except GuardFailure as exc:
            report.add("PR_PROVENANCE_ERROR", str(exc), manifest_path)

    superseded_at: dict[str, str] = {}
    for manifest_path, manifest, _baseline in records:
        supersedes = manifest.get("supersedes")
        parent = manifest.get("baseline_parent")
        if isinstance(supersedes, str) and isinstance(parent, str):
            if supersedes in superseded_at:
                report.add(
                    "PR_BASELINE_SUPERSEDED_TWICE",
                    "one baseline cannot be superseded by multiple manifests",
                    manifest_path,
                )
            superseded_at[supersedes] = parent

    for manifest_path, _manifest, baseline in records:
        is_superseded = baseline in superseded_at
        if is_superseded:
            verification_head = superseded_at[baseline]
        else:
            subsequent_parents = [
                str(m.get("baseline_parent"))
                for _, m, b2 in records
                if b2 != baseline and _is_ancestor(repo, baseline, b2) and m.get("baseline_parent")
            ]
            if not subsequent_parents:
                commits_after = _git(repo, "rev-list", f"{baseline}..{head}").stdout.splitlines()
                for ca in reversed(commits_after):
                    subj = _git(repo, "show", "-s", "--format=%s", ca).stdout.strip()
                    if ca != baseline and any(subj.startswith(pfx) for pfx in ("feat(release):", "docs(release):")):
                        parent_of_ca = _git(repo, "rev-parse", f"{ca}^", check=False).stdout.strip()
                        if parent_of_ca and _is_ancestor(repo, baseline, parent_of_ca):
                            subsequent_parents.append(parent_of_ca)
                            break
            if subsequent_parents:
                subsequent_parents.sort(
                    key=lambda p: int(_git(repo, "rev-list", "--count", f"{baseline}..{p}").stdout.strip())
                )
                verification_head = subsequent_parents[0]
                is_superseded = True
            else:
                verification_head = head
        try:
            nested = verify_history(
                repo,
                manifest_path,
                head_revision=verification_head,
                baseline_revision=baseline,
                include_worktree=(verification_head == head),
            )
        except GuardFailure as exc:
            report.add("PR_PROVENANCE_ERROR", str(exc), manifest_path)
            continue
        if is_superseded:
            nested.notes.append(
                f"baseline {baseline} verified only through its preserved cutoff {verification_head}"
            )
        else:
            report.issues.extend(nested.issues)
        if nested.ticket_id:
            tickets.append(nested.ticket_id)
        if nested.baseline_commit:
            baselines.append(nested.baseline_commit)
        report.test_files_verified += nested.test_files_verified
        report.notes.extend(nested.notes)
    for path in material_paths:
        if not any(_matches_allowed(path, allowed) for allowed in allowed_sets):
            if path in reconstructed_paths:
                report.notes.append(
                    f"material path {path} covered by historical NON_TDD_RECONSTRUCTED commit"
                )
            else:
                report.add(
                    "PR_SOURCE_PATH_WITHOUT_BASELINE",
                    "material PR path is not owned by any changed provenance manifest",
                    path,
                )
    report.ticket_id = ",".join(tickets) if tickets else None
    report.baseline_commit = ",".join(baselines) if baselines else None
    return report


def _emit(report: Report, json_out: str | None = None) -> int:
    payload = json.dumps(report.as_dict(), indent=2, sort_keys=True)
    print(payload)
    if json_out:
        output = Path(json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    return 1 if report.issues else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify committed test-first provenance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="verify one manifest against Git history")
    verify.add_argument("--repo", default=".")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--baseline")
    verify.add_argument("--head", default="HEAD")
    verify.add_argument("--include-worktree", action="store_true")
    verify.add_argument("--json-out")

    staged = subparsers.add_parser("staged", help="verify staged test/source separation")
    staged.add_argument("--repo", default=".")
    staged.add_argument("--json-out")

    pr = subparsers.add_parser("verify-pr", help="discover and verify the PR baseline manifest")
    pr.add_argument("--repo", default=".")
    pr.add_argument("--base", required=True)
    pr.add_argument("--head", default="HEAD")
    pr.add_argument("--json-out")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        repo = _repo_root(args.repo)
        if args.command == "verify":
            report = verify_history(
                repo,
                args.manifest,
                head_revision=args.head,
                baseline_revision=args.baseline,
                include_worktree=args.include_worktree,
            )
        elif args.command == "staged":
            report = verify_staged(repo)
        else:
            report = verify_pr(repo, args.base, args.head)
        return _emit(report, args.json_out)
    except GuardFailure as exc:
        report = Report(
            command=args.command,
            requested_base=getattr(args, "base", None),
            requested_head=getattr(args, "head", None),
        )
        report.add("GUARD_EVIDENCE_ERROR", str(exc))
        return _emit(report, getattr(args, "json_out", None))


if __name__ == "__main__":
    raise SystemExit(main())
