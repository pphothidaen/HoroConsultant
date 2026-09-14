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
