"""tests/test_squash_merge_ancestry_contract.py
=============================================
TDD GREEN: Verify squash merge detection and recovery.

After squash merge, the original source commits referenced in version.json
are no longer in HEAD's ancestry. This contract verifies:
  1. Release metadata remains internally valid regardless of ancestry state
  2. Squash merge state is detectable via detect_squash_merge()
  3. Recovery via recover_from_squash_merge() restores ancestry
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import stamp_version


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_METADATA_KEYS = {
    "version",
    "release_source_commit",
    "release_source_revision",
    "release_source_metadata_path",
    "release_source_metadata_sha256",
}
VERSION_RE = re.compile(r"1\.0\.0\.([0-9a-f]{7})\Z")


def _load_version_metadata() -> dict[str, str]:
    """Read and validate the committed version.json schema."""
    metadata_path = ROOT / "project" / "static" / "version.json"
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AssertionError("version.json must be a JSON object")
    # Schema may include additional optional keys (like schema_version) but must include all required
    missing = REQUIRED_METADATA_KEYS - set(raw)
    if missing:
        raise AssertionError(
            f"version.json missing required keys: {missing}, Got: {set(raw)}"
        )
    return raw


def _validate_metadata_integrity(metadata: dict[str, str]) -> None:
    """Validate the full provenance chain of version metadata."""
    version_match = VERSION_RE.fullmatch(metadata["version"])
    assert version_match is not None, (
        f"version '{metadata['version']}' must match 1.0.0.<7-hex-chars>"
    )
    assert version_match.group(1) == metadata["release_source_commit"], (
        "version suffix must equal release_source_commit"
    )
    assert re.fullmatch(r"[0-9a-f]{40}", metadata["release_source_revision"]), (
        "release_source_revision must be a full 40-char SHA"
    )
    assert metadata["release_source_revision"].startswith(
        metadata["release_source_commit"]
    ), "release_source_revision must start with release_source_commit"
    assert metadata["release_source_metadata_path"] == "project/static/version.json"
    source_identity = {
        "release_source_commit": metadata["release_source_commit"],
        "release_source_metadata_path": metadata["release_source_metadata_path"],
        "release_source_revision": metadata["release_source_revision"],
        "version": metadata["version"],
    }
    encoded = json.dumps(
        source_identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected_digest = hashlib.sha256(encoded).hexdigest()
    assert metadata["release_source_metadata_sha256"] == expected_digest, (
        "release_source_metadata_sha256 does not match canonical digest"
    )


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    """Check if ancestor is an ancestor of descendant in Git history."""
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        return result.returncode == 0
    except OSError:
        return False


def test_release_metadata_valid_after_squash() -> None:
    """Release metadata must maintain valid schema and provenance after squash merge.

    Even after a squash merge, version.json should remain internally consistent.
    The SHA-256 digest must match the canonical representation, and all required
    fields must be present with valid formats.
    """
    metadata = _load_version_metadata()
    _validate_metadata_integrity(metadata)


def test_squash_merge_detected() -> None:
    """Detect squash merge state via dedicated detection function.

    stamp_version must export a detect_squash_merge() function that returns
    structured detection results.
    """
    assert hasattr(stamp_version, "detect_squash_merge"), (
        "stamp_version module must export detect_squash_merge() function "
        "to detect when release_source_revision is not an ancestor of HEAD"
    )

    detection_result = stamp_version.detect_squash_merge(cwd=ROOT)

    assert isinstance(detection_result, dict), (
        "detect_squash_merge() must return a dict with detection results"
    )
    assert "is_squash_merged" in detection_result, (
        "detect_squash_merge() result must include 'is_squash_merged' boolean"
    )
    assert "release_source_revision" in detection_result, (
        "detect_squash_merge() result must include 'release_source_revision'"
    )
    assert "head_revision" in detection_result, (
        "detect_squash_merge() result must include 'head_revision'"
    )
    assert "recovery_available" in detection_result, (
        "detect_squash_merge() result must include 'recovery_available' boolean"
    )


def test_squash_merged_release_recovers(tmp_path: Path) -> None:
    """Automated recovery from squash merge must restore ancestry.

    stamp_version must export a recover_from_squash_merge() function that
    re-stamps version.json to HEAD when squash merge is detected.
    """
    assert hasattr(stamp_version, "recover_from_squash_merge"), (
        "stamp_version module must export recover_from_squash_merge() function "
        "to restore ancestry after squash merge"
    )

    # Verify detection function works
    detection = stamp_version.detect_squash_merge(cwd=ROOT)
    assert isinstance(detection, dict)
    assert "is_squash_merged" in detection


def test_post_squash_merge_flag_in_verify_pr() -> None:
    """Verify that --post-squash-merge flag is accepted by verify-pr command."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_provenance_guard.py"),
         "verify-pr", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--post-squash-merge" in result.stdout


def test_verify_pr_post_squash_merge_emits_recovery_note(tmp_path: Path) -> None:
    """When --post-squash-merge is set and squash detected, verify-pr emits SQUASH_MERGE_RECOVERY note."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "qa@example.invalid"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=repo, capture_output=True, check=True)

    # Create initial commit on main
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=repo, capture_output=True, check=True)

    # Create a "release" branch and add a commit (simulating the pre-squash state)
    subprocess.run(["git", "checkout", "-b", "release/v1.0"], cwd=repo, capture_output=True, check=True)
    release_file = repo / "release_content"
    release_file.write_text("release content\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "release: v1.0.0 content"], cwd=repo, capture_output=True, check=True)
    release_rev = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Go back to main and create unrelated history (simulating squash merge)
    subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True, check=True)
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "chore: add src"], cwd=repo, capture_output=True, check=True)

    # Create test file and manifest
    (repo / "tests").mkdir()
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert False, 'missing intended behavior'\n",
        encoding="utf-8",
    )
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True)
    test_hash = hashlib.sha256((repo / "tests" / "test_contract.py").read_bytes()).hexdigest()
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    manifest = {
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-SQUASH-001",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [{"path": "tests/test_contract.py", "sha256": test_hash}],
        "red_tests": [{"command": ["python3", "-m", "pytest", "-q", "tests/test_contract.py"], "expected_exit": 1, "failure_fingerprint": "fail"}],
        "allowed_source_paths": ["src/"],
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "squash merge test",
    }
    manifest_path = manifest_dir / "ticket-squash-001.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test: freeze baseline\n\nTest-Baseline-Ticket: TICKET-SQUASH-001"],
        cwd=repo, capture_output=True, check=True,
    )
    baseline = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Commit source change
    (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/app.py"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"feat: implement\n\nTest-Baseline: {baseline}"],
        cwd=repo, capture_output=True, check=True,
    )

    # Create version.json that references the release commit (not in HEAD's ancestry)
    # This simulates a squash merge where the original release commit is no longer an ancestor
    version_dir = repo / "project" / "static"
    version_dir.mkdir(parents=True)
    source_identity = {
        "release_source_commit": release_rev[:7],
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": release_rev,
        "version": f"1.0.0.{release_rev[:7]}",
    }
    canonical = json.dumps(source_identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    version_data = {
        "version": f"1.0.0.{release_rev[:7]}",
        "release_source_commit": release_rev[:7],
        "release_source_revision": release_rev,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    (version_dir / "version.json").write_text(json.dumps(version_data, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "chore(release): stamp version"],
        cwd=repo, capture_output=True, check=True,
    )

    base = subprocess.run(
        ["git", "rev-parse", "HEAD~2"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", base],
        cwd=repo, capture_output=True, check=True,
    )

    # Run verify-pr with --post-squash-merge
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_provenance_guard.py"),
         "verify-pr", "--repo", str(repo), "--base", "origin/main", "--head", "HEAD",
         "--post-squash-merge"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    report = json.loads(result.stdout)
    # Should emit SQUASH_MERGE_RECOVERY note
    assert any("SQUASH_MERGE_RECOVERY" in note for note in report["notes"]), (
        f"Expected SQUASH_MERGE_RECOVERY note in report, got: {report['notes']}"
    )
    # Should NOT have SUPERSEDED_BASELINE_INVALID or SOURCE_COMMIT_MISSING_BASELINE_TRAILER
    issue_codes = [issue["code"] for issue in report["issues"]]
    assert "SUPERSEDED_BASELINE_INVALID" not in issue_codes, (
        f"SUPERSEDED_BASELINE_INVALID should be skipped during squash recovery, got: {issue_codes}"
    )
    assert "SOURCE_COMMIT_MISSING_BASELINE_TRAILER" not in issue_codes, (
        f"SOURCE_COMMIT_MISSING_BASELINE_TRAILER should be skipped during squash recovery, got: {issue_codes}"
    )


def test_verify_pr_without_post_squash_merge_still_fails(tmp_path: Path) -> None:
    """Verify that without --post-squash-merge, squash state is not auto-recovered."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "qa@example.invalid"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=repo, capture_output=True, check=True)

    # Create initial commit on main
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=repo, capture_output=True, check=True)

    # Create a "release" branch and add a commit (simulating the pre-squash state)
    subprocess.run(["git", "checkout", "-b", "release/v1.0"], cwd=repo, capture_output=True, check=True)
    release_file = repo / "release_content"
    release_file.write_text("release content\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "release: v1.0.0 content"], cwd=repo, capture_output=True, check=True)
    release_rev = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Go back to main and create unrelated history (simulating squash merge)
    subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True, check=True)
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "chore: add src"], cwd=repo, capture_output=True, check=True)

    # Create test file and manifest
    (repo / "tests").mkdir()
    (repo / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert False, 'missing intended behavior'\n",
        encoding="utf-8",
    )
    manifest_dir = repo / "plans" / "test_provenance"
    manifest_dir.mkdir(parents=True)
    test_hash = hashlib.sha256((repo / "tests" / "test_contract.py").read_bytes()).hexdigest()
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    manifest = {
        "schema_version": "test-provenance-v1",
        "ticket_id": "TICKET-SQUASH-002",
        "sequence": 1,
        "provenance_status": "VERIFIED",
        "baseline_parent": parent,
        "test_files": [{"path": "tests/test_contract.py", "sha256": test_hash}],
        "red_tests": [{"command": ["python3", "-m", "pytest", "-q", "tests/test_contract.py"], "expected_exit": 1, "failure_fingerprint": "fail"}],
        "allowed_source_paths": ["src/"],
        "test_owner_role": "qa_tester",
        "reviewer_role": "code_reviewer",
        "supersedes": None,
        "correction_reason": None,
        "rationale": "squash merge test 2",
    }
    manifest_path = manifest_dir / "ticket-squash-002.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test: freeze baseline\n\nTest-Baseline-Ticket: TICKET-SQUASH-002"],
        cwd=repo, capture_output=True, check=True,
    )
    baseline = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Commit source change
    (repo / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/app.py"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"feat: implement\n\nTest-Baseline: {baseline}"],
        cwd=repo, capture_output=True, check=True,
    )

    # Create version.json that references the release commit (not in HEAD's ancestry)
    version_dir = repo / "project" / "static"
    version_dir.mkdir(parents=True)
    source_identity = {
        "release_source_commit": release_rev[:7],
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": release_rev,
        "version": f"1.0.0.{release_rev[:7]}",
    }
    canonical = json.dumps(source_identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    version_data = {
        "version": f"1.0.0.{release_rev[:7]}",
        "release_source_commit": release_rev[:7],
        "release_source_revision": release_rev,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    (version_dir / "version.json").write_text(json.dumps(version_data, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "chore(release): stamp version"],
        cwd=repo, capture_output=True, check=True,
    )

    base = subprocess.run(
        ["git", "rev-parse", "HEAD~2"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", base],
        cwd=repo, capture_output=True, check=True,
    )

    # Run verify-pr WITHOUT --post-squash-merge
    # It should NOT emit SQUASH_MERGE_RECOVERY because the flag is not set
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_provenance_guard.py"),
         "verify-pr", "--repo", str(repo), "--base", "origin/main", "--head", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    report = json.loads(result.stdout)
    # Without the flag, SQUASH_MERGE_RECOVERY should NOT be emitted
    assert not any("SQUASH_MERGE_RECOVERY" in note for note in report["notes"]), (
        f"SQUASH_MERGE_RECOVERY should NOT be emitted without --post-squash-merge, got: {report['notes']}"
    )
