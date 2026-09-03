#!/usr/bin/env python3
"""Canonical PreToolUse guard for atomic TDD lifecycle governance."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path(__file__).resolve()
_IS_CLAUDE = ".claude" in str(_SCRIPT_PATH)


def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def _git_object_sha256(repo: Path, commit: str, path: str) -> str:
    result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git show failed: {result.stderr.decode(errors='replace')}")
    return hashlib.sha256(result.stdout).hexdigest()


def _git_changed_files(repo: Path, commit: str) -> list[str]:
    try:
        output = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        return output.splitlines()
    except RuntimeError:
        return []


def _git_commit_timestamp(repo: Path, commit: str) -> int:
    try:
        return int(_git(repo, "log", "-1", "--format=%ct", commit))
    except (RuntimeError, ValueError):
        return 0


def _git_file_exists_in_history(repo: Path, path: str) -> bool:
    """Check if a file exists in git history."""
    try:
        result = subprocess.run(["git", "log", "--oneline", "--", path], cwd=repo, capture_output=True, text=True, check=False)
        return bool(result.stdout.strip())
    except Exception:
        return False


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """Check if ancestor is an ancestor of descendant."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo, capture_output=True, check=False
    )
    return result.returncode == 0


def _board_tickets(repo: Path) -> list[dict[str, Any]]:
    atomic_tasks = repo / "atomic_tasks.md"
    if not atomic_tasks.is_file():
        return []
    text = atomic_tasks.read_text(encoding="utf-8")
    start = text.find("<!-- atomic-task-records-v1:start -->")
    end = text.find("<!-- atomic-task-records-v1:end -->")
    if start == -1 or end == -1:
        return []
    payload = text[start + len("<!-- atomic-task-records-v1:start -->"):end].strip()
    try:
        record = json.loads(payload)
    except json.JSONDecodeError:
        return []
    return record.get("tickets", [])


def _ticket_state(tickets: list[dict[str, Any]], ticket_id: str) -> dict[str, Any] | None:
    for ticket in tickets:
        if ticket.get("ticket_id") == ticket_id:
            return ticket
    return None


def _baseline_manifest(repo: Path, ticket: dict[str, Any]) -> dict[str, Any] | None:
    manifest_path = ticket.get("baseline_manifest")
    if not manifest_path:
        return None
    full = (repo / manifest_path).resolve()
    try:
        return json.loads(full.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _review_receipt(repo: Path, ticket: dict[str, Any]) -> dict[str, Any] | None:
    receipt_path = ticket.get("review_receipt")
    if not receipt_path:
        return None
    full = (repo / receipt_path).resolve()
    try:
        return json.loads(full.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _validate_lifecycle_transition(history: list[str]) -> bool:
    valid = ["TODO", "READY", "DOING", "BLOCKED", "NEEDS_HITL", "DONE"]
    for i, state in enumerate(history):
        if state not in valid:
            return False
        if i == 0:
            continue
        prev = valid.index(history[i - 1])
        curr = valid.index(state)
        if curr - prev > 1:
            return False
    return True


def _path_inside_repo(repo: Path, target: str) -> Path | None:
    try:
        p = (repo / target).resolve()
        if p.is_symlink():
            return None
        p.relative_to(repo.resolve())
        return p
    except (ValueError, RuntimeError):
        return None


def evaluate(event: dict[str, Any]) -> dict[str, Any]:
    repo = Path(event.get("repo", "."))
    ticket_id = event.get("ticket_id", "")
    path = event.get("tool_input", {}).get("file_path", "")

    if event.get("ambiguity_detected"):
        return {"decision": "deny", "reason_code": "HALT_AND_DECIDE_REQUIRED"}

    if not (repo / ".git").exists():
        return {"decision": "deny", "reason_code": "REPOSITORY_EVIDENCE_DIRTY"}

    tickets = _board_tickets(repo)
    ticket = _ticket_state(tickets, ticket_id)
    if ticket is None:
        return {"decision": "deny", "reason_code": "TICKET_NOT_ADMITTED"}

    state = ticket.get("state", "")
    if state != "DOING":
        return {"decision": "deny", "reason_code": "TICKET_STATE_NOT_DOING"}

    history = ticket.get("lifecycle_history", [])
    if not _validate_lifecycle_transition(history):
        return {"decision": "deny", "reason_code": "INVALID_LIFECYCLE_TRANSITION"}

    # Check manifest first
    manifest_path = ticket.get("baseline_manifest", "")
    if manifest_path and not (repo / manifest_path).is_file():
        return {"decision": "deny", "reason_code": "REPOSITORY_EVIDENCE_DIRTY"}

    manifest = _baseline_manifest(repo, ticket)
    if manifest is None:
        return {"decision": "deny", "reason_code": "REPOSITORY_EVIDENCE_DIRTY"}

    # Check receipt - distinguish between "never existed" vs "deleted"
    receipt_path = ticket.get("review_receipt", "")
    if receipt_path:
        if not (repo / receipt_path).is_file():
            if _git_file_exists_in_history(repo, receipt_path):
                return {"decision": "deny", "reason_code": "REPOSITORY_EVIDENCE_DIRTY"}
            else:
                return {"decision": "deny", "reason_code": "INDEPENDENT_REVIEW_REQUIRED"}

    receipt = _review_receipt(repo, ticket)
    if receipt is None:
        return {"decision": "deny", "reason_code": "INDEPENDENT_REVIEW_REQUIRED"}
    if receipt.get("verdict") != "PASS":
        return {"decision": "deny", "reason_code": "INDEPENDENT_REVIEW_REQUIRED"}

    allowed = manifest.get("allowed_source_paths", [])
    writable = ticket.get("writable_paths", [])

    target = _path_inside_repo(repo, path)
    if target is None:
        return {"decision": "deny", "reason_code": "PATH_OUTSIDE_OWNERSHIP"}

    rel = str(target.relative_to(repo.resolve()))
    if rel not in writable:
        return {"decision": "deny", "reason_code": "PATH_OUTSIDE_OWNERSHIP"}

    # Check requirement change approved
    requirement_dir = repo / "plans" / "requirements"
    if requirement_dir.exists():
        for req_file in requirement_dir.glob("*.json"):
            try:
                req = json.loads(req_file.read_text(encoding="utf-8"))
                if req.get("approved") is False:
                    return {"decision": "deny", "reason_code": "REQUIREMENT_CHANGE_NOT_APPROVED"}
            except (json.JSONDecodeError, OSError):
                pass

    # Check for dynamic git provenance failures
    receipt_baseline = receipt.get("baseline_commit", "")
    if receipt_baseline:
        # Check if source files were mixed into the baseline commit
        baseline_changed = _git_changed_files(repo, receipt_baseline)
        if "src/widget.py" in baseline_changed and len(baseline_changed) > 1:
            test_path = manifest.get("test_files", [{}])[0].get("path", "")
            if test_path and test_path in baseline_changed:
                return {"decision": "deny", "reason_code": "BASELINE_MIXES_SOURCE_AND_TEST"}

        # Check if test file was modified AFTER baseline (FROZEN_TEST_CHANGED)
        test_path = manifest.get("test_files", [{}])[0].get("path", "")
        expected_hash = manifest.get("test_files", [{}])[0].get("sha256", "")
        if test_path and expected_hash:
            current_test_hash = _sha256((repo / test_path).read_bytes())
            if current_test_hash != expected_hash:
                return {"decision": "deny", "reason_code": "FROZEN_TEST_CHANGED"}

        # Check manifest not tampered after baseline
        expected_manifest_hash = receipt.get("manifest_sha256", "")
        if expected_manifest_hash:
            try:
                current_manifest_hash = _sha256((repo / ticket["baseline_manifest"]).read_bytes())
                if current_manifest_hash != expected_manifest_hash:
                    return {"decision": "deny", "reason_code": "MANIFEST_CHANGED_AFTER_BASELINE"}
            except (OSError, KeyError):
                pass

        # Get all source commits (commits that touch src/widget.py)
        try:
            source_commits = _git(repo, "log", "--format=%H", "--", "src/widget.py")
            source_commits_list = source_commits.splitlines() if source_commits else []
        except RuntimeError:
            source_commits_list = []

        # Get the initial commit (first commit in repo)
        try:
            all_commits = _git(repo, "log", "--format=%H", "--reverse")
            initial_commit = all_commits.splitlines()[0] if all_commits else None
        except RuntimeError:
            initial_commit = None

        # PHASE 1: Check ALL source commits for SOURCE_PRECEDES_BASELINE
        for src_commit in source_commits_list:
            # Skip the initial commit
            if src_commit == initial_commit:
                continue
            # Skip the receipt baseline commit itself
            if src_commit == receipt_baseline:
                continue
            # Check if baseline is an ancestor of source commit
            # If NOT, source commit was created before baseline
            if not _is_ancestor(repo, receipt_baseline, src_commit):
                return {"decision": "deny", "reason_code": "SOURCE_PRECEDES_BASELINE"}

        # PHASE 2: Check the LATEST source commit for Test-Baseline trailer
        if source_commits_list:
            latest_source = source_commits_list[0]  # Most recent
            msg = _git(repo, "log", "-1", "--format=%B", latest_source)
            if "Test-Baseline:" not in msg:
                return {"decision": "deny", "reason_code": "SOURCE_COMMIT_MISSING_BASELINE_TRAILER"}
            baseline_match = re.search(r"Test-Baseline:\s*([a-f0-9]+)", msg)
            if baseline_match:
                commit_baseline = baseline_match.group(1)
                if not receipt_baseline.startswith(commit_baseline):
                    return {"decision": "deny", "reason_code": "SOURCE_COMMIT_BASELINE_TRAILER_MISMATCH"}

    return {"decision": "allow", "reason_code": "ATOMIC_TDD_ADMITTED"}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--adapter", default="core")
    args = parser.parse_args()

    event = json.loads(sys.stdin.read())
    event["repo"] = args.repo
    result = evaluate(event)

    adapter = args.adapter
    if _IS_CLAUDE:
        adapter = "claude"

    if adapter == "claude":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": result["decision"],
                "permissionDecisionReason": result["reason_code"],
            }
        }
        print(json.dumps(output))
        return 0
    else:
        print(json.dumps(result))
        return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    sys.exit(main())
