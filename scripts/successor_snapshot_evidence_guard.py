#!/usr/bin/env python3
"""Successor Snapshot Evidence Guard.

Standalone verification CLI for non-TDD reconstructed evidence manifests.
Emits structured JSON with fail-closed integrity status and diagnostic issues.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import jsonschema

FLAGS = (
    "historical_combined_compliance",
    "combined_test_baseline_verified",
    "successor_verified",
    "source_admission",
    "commit_authorized",
    "successor_commit_authorized",
    "release_authorized",
)

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / ".agents"
    / "schemas"
    / "successor-snapshot-evidence-v1.schema.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_safe_canonical_path(p: Any) -> bool:
    if not isinstance(p, str) or not p:
        return False
    if p.startswith("/") or p.startswith("./") or "\\" in p:
        return False
    parts = p.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return True


def parse_iso8601(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def git_env() -> dict[str, str]:
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    return env


def git_show_blob(repo: Path, commit: str, rel_path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{rel_path}"],
        capture_output=True,
        env=git_env(),
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_diff_binary(repo: Path, commit: str, rel_path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", commit, "--", rel_path],
        capture_output=True,
        env=git_env(),
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def matches_manifest_path(receipt_path_str: str, manifest_path: Path, repo: Path) -> bool:
    if not isinstance(receipt_path_str, str) or not receipt_path_str:
        return False
    if receipt_path_str == manifest_path.name:
        return True
    try:
        if manifest_path.resolve().is_relative_to(repo.resolve()):
            if str(manifest_path.resolve().relative_to(repo.resolve())) == receipt_path_str:
                return True
    except Exception:
        pass
    try:
        if manifest_path.resolve() == (repo / receipt_path_str).resolve():
            return True
    except Exception:
        pass
    try:
        if manifest_path.resolve() == Path(receipt_path_str).resolve():
            return True
    except Exception:
        pass
    return False


def verify(
    repo: Path,
    manifest_path: Path,
    receipt_path: Path,
    expected_parent: str,
    expected_head: str,
    now_str: str,
) -> tuple[dict[str, Any], int]:
    report: dict[str, Any] = {
        "provenance_status": "NON_TDD_RECONSTRUCTED",
        "acceptance_status": "BLOCKED",
        "flags": {f: False for f in FLAGS},
        "integrity_status": "PASSED",
        "inventory_path_count": 0,
        "actual_delta_path_count": 0,
        "issues": [],
    }
    issues: list[str] = []

    dt_now: datetime | None = None
    try:
        dt_now = parse_iso8601(now_str)
    except Exception as exc:
        issues.append(f"INVALID_NOW_TIMESTAMP: {exc}")

    manifest_raw: bytes = b""
    manifest: dict[str, Any] | None = None
    if not manifest_path.is_file():
        issues.append(f"MANIFEST_NOT_FOUND: {manifest_path}")
    else:
        try:
            manifest_raw = manifest_path.read_bytes()
            manifest = json.loads(manifest_raw)
            if not isinstance(manifest, dict):
                issues.append("MANIFEST_NOT_OBJECT: top-level manifest must be a JSON object")
                manifest = None
        except Exception as exc:
            issues.append(f"MANIFEST_MALFORMED_JSON: {exc}")

    receipt: dict[str, Any] | None = None
    if not receipt_path.is_file():
        issues.append(f"RECEIPT_NOT_FOUND: {receipt_path}")
    else:
        try:
            receipt_raw = receipt_path.read_bytes()
            receipt = json.loads(receipt_raw)
            if not isinstance(receipt, dict):
                issues.append("RECEIPT_NOT_OBJECT: top-level receipt must be a JSON object")
                receipt = None
        except Exception as exc:
            issues.append(f"RECEIPT_MALFORMED_JSON: {exc}")

    if manifest is None:
        report["integrity_status"] = "FAILED"
        report["issues"] = sorted(set(issues))
        return report, 1

    candidate_inventory = manifest.get("candidate_inventory")
    if isinstance(candidate_inventory, list):
        report["inventory_path_count"] = len(candidate_inventory)
    elif isinstance(manifest.get("inventory_path_count"), int):
        report["inventory_path_count"] = manifest.get("inventory_path_count", 0)

    actual_delta = manifest.get("actual_proposed_commit_delta")
    if isinstance(actual_delta, dict) and isinstance(actual_delta.get("inventory_delta"), list):
        report["actual_delta_path_count"] = len(actual_delta["inventory_delta"])

    if "manifest_sha256" in manifest:
        issues.append("MANIFEST_SELF_HASH_FORBIDDEN: manifest must not contain self-hash manifest_sha256")

    if SCHEMA_PATH.is_file():
        try:
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
            validator = jsonschema.Draft202012Validator(schema)
            for err in validator.iter_errors(manifest):
                loc = "/".join(str(p) for p in err.path)
                issues.append(f"SCHEMA_VALIDATION_ERROR: {err.message} at '{loc}'")
        except Exception as exc:
            issues.append(f"SCHEMA_CHECK_FAILED: {exc}")
    else:
        issues.append(f"SCHEMA_FILE_MISSING: {SCHEMA_PATH}")

    if manifest.get("provenance_status") != "NON_TDD_RECONSTRUCTED":
        issues.append(f"PROVENANCE_STATUS_INVALID: expected NON_TDD_RECONSTRUCTED, got {manifest.get('provenance_status')}")
    if manifest.get("disposition") != "BLOCKED":
        issues.append(f"DISPOSITION_INVALID: expected BLOCKED, got {manifest.get('disposition')}")

    manifest_flags = manifest.get("flags")
    if not isinstance(manifest_flags, dict):
        issues.append("FLAGS_INVALID: flags must be an object")
    else:
        for f in FLAGS:
            if manifest_flags.get(f) is not False:
                issues.append(f"FLAG_ADMISSION_FORBIDDEN: flag '{f}' must be false")

    if manifest.get("baseline_parent") != expected_parent:
        issues.append(f"PARENT_MISMATCH: expected {expected_parent}, got {manifest.get('baseline_parent')}")
    if manifest.get("observed_head") != expected_head:
        issues.append(f"HEAD_MISMATCH: expected {expected_head}, got {manifest.get('observed_head')}")

    if receipt is not None:
        actual_manifest_sha = sha256_bytes(manifest_raw)
        if receipt.get("manifest_sha256") != actual_manifest_sha:
            issues.append(f"RECEIPT_HASH_MISMATCH: expected {actual_manifest_sha}, got {receipt.get('manifest_sha256')}")

        if not matches_manifest_path(receipt.get("manifest_path", ""), manifest_path, repo):
            issues.append(f"RECEIPT_PATH_MISMATCH: receipt path '{receipt.get('manifest_path')}' does not match manifest '{manifest_path}'")

        if receipt.get("ticket_id") != manifest.get("ticket_id"):
            issues.append(f"RECEIPT_TICKET_MISMATCH: expected {manifest.get('ticket_id')}, got {receipt.get('ticket_id')}")

        if receipt.get("baseline_parent") != expected_parent or receipt.get("baseline_parent") != manifest.get("baseline_parent"):
            issues.append(f"RECEIPT_PARENT_MISMATCH: expected {expected_parent}, got {receipt.get('baseline_parent')}")

        if receipt.get("observed_head") != expected_head or receipt.get("observed_head") != manifest.get("observed_head"):
            issues.append(f"RECEIPT_HEAD_MISMATCH: expected {expected_head}, got {receipt.get('observed_head')}")

        expected_snapshot_name = manifest.get("source_config_test_snapshot", {}).get("name")
        if receipt.get("snapshot_name") != expected_snapshot_name:
            issues.append(f"RECEIPT_SNAPSHOT_MISMATCH: expected {expected_snapshot_name}, got {receipt.get('snapshot_name')}")

        if dt_now is not None:
            try:
                obs_ts = receipt.get("observed_at")
                exp_ts = receipt.get("expires_at")
                if not obs_ts or not exp_ts:
                    issues.append("RECEIPT_TIMESTAMPS_MISSING: observed_at and expires_at required")
                else:
                    dt_obs = parse_iso8601(obs_ts)
                    dt_exp = parse_iso8601(exp_ts)
                    if dt_obs > dt_now:
                        issues.append(f"RECEIPT_FUTURE: observed_at {obs_ts} > now {now_str}")
                    if dt_exp <= dt_now:
                        issues.append(f"RECEIPT_STALE: expires_at {exp_ts} <= now {now_str}")
            except Exception as exc:
                issues.append(f"RECEIPT_TIMESTAMP_PARSE_ERROR: {exc}")

        if isinstance(candidate_inventory, list):
            inv_paths = [r.get("path") for r in candidate_inventory if isinstance(r, dict)]
            if receipt.get("inventory_paths") != inv_paths:
                issues.append("RECEIPT_INVENTORY_MISMATCH: receipt inventory_paths does not match candidate_inventory")

    actually_changed_paths: dict[str, str] = {}
    if not isinstance(candidate_inventory, list):
        issues.append("INVENTORY_INVALID: candidate_inventory must be a list")
    else:
        if len(candidate_inventory) != manifest.get("inventory_path_count"):
            issues.append(f"INVENTORY_COUNT_MISMATCH: manifest count {manifest.get('inventory_path_count')} != actual {len(candidate_inventory)}")

        seen_paths: set[str] = set()

        for idx, row in enumerate(candidate_inventory):
            if not isinstance(row, dict):
                issues.append(f"INVENTORY_ROW_NOT_OBJECT: row {idx}")
                continue
            p = row.get("path")
            if not is_safe_canonical_path(p):
                issues.append(f"UNSAFE_PATH: '{p}' is unsafe or not canonical")
                continue
            if p in seen_paths:
                issues.append(f"DUPLICATE_PATH: '{p}' appears multiple times in candidate_inventory")
            seen_paths.add(p)

            if row.get("classification") != "NON_TDD_RECONSTRUCTED":
                issues.append(f"PER_PATH_PROMOTION: '{p}' classification '{row.get('classification')}' != NON_TDD_RECONSTRUCTED")

            target_file = repo / p
            if target_file.is_symlink():
                issues.append(f"SYMLINK_FORBIDDEN: '{p}' is a symlink")
                continue
            if not target_file.is_file():
                issues.append(f"FILE_MISSING: '{p}' does not exist as a regular file in repository")
                continue

            actual_worktree_sha = sha256_bytes(target_file.read_bytes())
            if actual_worktree_sha != row.get("sha256"):
                issues.append(f"HASH_TAMPER: '{p}' worktree sha256 {actual_worktree_sha} != manifest {row.get('sha256')}")

            head_blob = git_show_blob(repo, expected_head, p)
            actual_head_sha = sha256_bytes(head_blob) if head_blob is not None else ""
            if actual_head_sha != row.get("head_sha256"):
                issues.append(f"HEAD_HASH_LIE: '{p}' HEAD sha256 {actual_head_sha} != manifest {row.get('head_sha256')}")

            is_changed = (actual_worktree_sha != actual_head_sha)
            if bool(row.get("changed_against_head")) != is_changed:
                issues.append(f"CHANGED_FLAG_LIE: '{p}' changed_against_head is {row.get('changed_against_head')} but actually {is_changed}")

            if is_changed:
                actually_changed_paths[p] = actual_worktree_sha

        if not isinstance(actual_delta, dict):
            issues.append("DELTA_INVALID: actual_proposed_commit_delta must be an object")
        else:
            if actual_delta.get("against_head") != expected_head:
                issues.append(f"DELTA_ANCHOR_MISMATCH: expected {expected_head}, got {actual_delta.get('against_head')}")

            inv_delta = actual_delta.get("inventory_delta")
            if not isinstance(inv_delta, list):
                issues.append("INVENTORY_DELTA_INVALID: inventory_delta must be a list")
            else:
                delta_paths = set()
                for d in inv_delta:
                    if isinstance(d, dict):
                        dp = d.get("path")
                        delta_paths.add(dp)
                        if dp in actually_changed_paths:
                            if d.get("sha256") != actually_changed_paths[dp]:
                                issues.append(f"DELTA_HASH_MISMATCH: '{dp}' delta sha256 != candidate sha256")

                if delta_paths != set(actually_changed_paths.keys()):
                    issues.append(f"DELTA_PATHS_MISMATCH: actual changes {sorted(actually_changed_paths.keys())} != delta {sorted(delta_paths)}")

            allowlist = set(actual_delta.get("changed_path_allowlist", []))
            if not set(actually_changed_paths.keys()).issubset(allowlist):
                issues.append(f"UNAUTHORIZED_DELTA: actual changes not in allowlist: {sorted(set(actually_changed_paths.keys()) - allowlist)}")

        snapshot = manifest.get("source_config_test_snapshot")
        if not isinstance(snapshot, dict):
            issues.append("SNAPSHOT_INVALID: source_config_test_snapshot must be an object")
        else:
            snap_files = snapshot.get("files")
            if not isinstance(snap_files, list):
                issues.append("SNAPSHOT_FILES_INVALID: source_config_test_snapshot.files must be a list")
            else:
                snap_map = {}
                snap_kinds = set()
                for f in snap_files:
                    if isinstance(f, dict):
                        fp = f.get("path")
                        snap_map[fp] = f.get("sha256")
                        snap_kinds.add(f.get("kind"))

                inv_map = {r.get("path"): r.get("sha256") for r in candidate_inventory if isinstance(r, dict)}
                if snap_map != inv_map:
                    issues.append("SNAPSHOT_TAMPER: snapshot files do not match candidate inventory paths/hashes")

                for req_kind in ("source", "config", "test"):
                    if req_kind not in snap_kinds:
                        issues.append(f"SNAPSHOT_MISSING_{req_kind.upper()}: snapshot missing required kind '{req_kind}'")

    predecessors = manifest.get("predecessors")
    if not isinstance(predecessors, list):
        issues.append("PREDECESSORS_INVALID: predecessors must be a list")
    else:
        for pred in predecessors:
            if not isinstance(pred, dict):
                issues.append("PREDECESSOR_INVALID: predecessor item must be an object")
                continue
            ppath = pred.get("path")
            psha = pred.get("sha256")
            pcommit = pred.get("commit")
            blob = git_show_blob(repo, pcommit, ppath)
            if blob is None:
                issues.append(f"PREDECESSOR_MISSING: commit {pcommit} path {ppath} could not be retrieved")
            else:
                actual_sha = sha256_bytes(blob)
                if actual_sha != psha:
                    issues.append(f"PREDECESSOR_HASH_MISMATCH: commit {pcommit} path {ppath} expected {psha}, got {actual_sha}")

    ownership = manifest.get("ownership_transfer")
    if not isinstance(ownership, dict):
        issues.append("OWNERSHIP_MISSING: ownership_transfer is required and must be an object")
    else:
        if ownership.get("parent_accepted") is not True:
            issues.append("OWNERSHIP_NOT_ACCEPTED: parent_accepted must be true")
        if ownership.get("classification") != "NON_TDD_RECONSTRUCTED":
            issues.append(f"OWNERSHIP_PROMOTION: classification '{ownership.get('classification')}' != NON_TDD_RECONSTRUCTED")
        if ownership.get("reachable_commit") is not None:
            issues.append(f"REACHABLE_HISTORY_CLAIM: reachable_commit must be null, got {ownership.get('reachable_commit')}")

        opath = ownership.get("path")
        ofile = repo / opath if opath else None
        if ofile and ofile.is_symlink():
            issues.append(f"SYMLINK_FORBIDDEN: ownership path '{opath}' is a symlink")
        elif ofile and ofile.is_file():
            actual_wsha = sha256_bytes(ofile.read_bytes())
            if actual_wsha != ownership.get("worktree_sha256"):
                issues.append(f"OWNERSHIP_FILE_HASH_MISMATCH: worktree sha256 {actual_wsha} != {ownership.get('worktree_sha256')}")
        else:
            issues.append(f"OWNERSHIP_FILE_NOT_FOUND: '{opath}' not found as a regular file")

        diff_bytes = git_diff_binary(repo, expected_head, opath)
        if diff_bytes is None:
            issues.append(f"OWNERSHIP_DIFF_FAILED: failed to compute git diff for '{opath}'")
        else:
            actual_diff_sha = sha256_bytes(diff_bytes)
            if actual_diff_sha != ownership.get("diff_sha256"):
                issues.append(f"OWNERSHIP_PATCH_HASH_MISMATCH: diff sha256 {actual_diff_sha} != {ownership.get('diff_sha256')}")

    if issues:
        report["integrity_status"] = "FAILED"
        report["issues"] = sorted(set(issues))
        return report, 1

    report["integrity_status"] = "PASSED"
    report["actual_delta_path_count"] = len(actually_changed_paths)
    report["issues"] = []
    return report, 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Successor Snapshot Evidence Guard")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--repo", required=True, type=Path, help="Repository root path")
    verify_parser.add_argument("--manifest", required=True, type=Path, help="Manifest file path")
    verify_parser.add_argument("--receipt", required=True, type=Path, help="Receipt file path")
    verify_parser.add_argument("--expected-parent", required=True, help="Expected baseline parent commit SHA")
    verify_parser.add_argument("--expected-head", required=True, help="Expected observed HEAD commit SHA")
    verify_parser.add_argument("--now", required=True, help="Current ISO 8601 timestamp for freshness check")

    args = parser.parse_args()
    if args.subcommand == "verify":
        report, exit_code = verify(
            repo=args.repo.resolve(),
            manifest_path=args.manifest,
            receipt_path=args.receipt,
            expected_parent=args.expected_parent,
            expected_head=args.expected_head,
            now_str=args.now,
        )
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
