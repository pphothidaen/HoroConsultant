from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

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


def _canonical_digest(metadata: dict[str, str]) -> str:
    source_identity = {
        "release_source_commit": metadata["release_source_commit"],
        "release_source_metadata_path": metadata[
            "release_source_metadata_path"
        ],
        "release_source_revision": metadata["release_source_revision"],
        "version": metadata["version"],
    }
    encoded = json.dumps(
        source_identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_release_metadata(metadata: dict[str, str]) -> None:
    assert set(metadata) == REQUIRED_METADATA_KEYS
    assert all(isinstance(metadata[key], str) for key in REQUIRED_METADATA_KEYS)
    version_match = VERSION_RE.fullmatch(metadata["version"])
    assert version_match is not None
    assert version_match.group(1) == metadata["release_source_commit"]
    assert re.fullmatch(r"[0-9a-f]{40}", metadata["release_source_revision"])
    assert metadata["release_source_revision"].startswith(
        metadata["release_source_commit"]
    )
    assert (
        metadata["release_source_metadata_path"]
        == "project/static/version.json"
    )
    assert metadata["release_source_metadata_sha256"] == _canonical_digest(
        metadata
    )


def test_committed_release_metadata_is_closed_mirrored_and_ancestral() -> None:
    source = json.loads(
        (ROOT / "project" / "static" / "version.json").read_text(
            encoding="utf-8"
        )
    )
    public = json.loads(
        (ROOT / "public" / "version.json").read_text(encoding="utf-8")
    )

    assert source == public
    _assert_release_metadata(source)
    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            source["release_source_revision"],
            "HEAD",
        ],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_stamp_version_json_emits_closed_immutable_source_identity(
    tmp_path: Path,
) -> None:
    metadata_path = tmp_path / "version.json"
    revision = "abcdef0123456789abcdef0123456789abcdef01"

    changed = stamp_version.stamp_version_json(
        metadata_path,
        "1.0.0.abcdef0",
        "abcdef0",
        revision,
    )

    assert changed is True
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    _assert_release_metadata(metadata)
    assert metadata["release_source_revision"] == revision
    assert "commit" not in metadata
    assert "timestamp" not in metadata
    assert "status" not in metadata
    assert (
        stamp_version.stamp_version_json(
            metadata_path,
            "1.0.0.abcdef0",
            "abcdef0",
            revision,
            dry_run=True,
        )
        is False
    )
