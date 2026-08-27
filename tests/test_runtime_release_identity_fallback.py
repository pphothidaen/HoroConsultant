from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from project.core import config


def _metadata(commit: str, revision: str) -> dict[str, str]:
    source = {
        "release_source_commit": commit,
        "release_source_metadata_path": "project/static/version.json",
        "release_source_revision": revision,
        "version": f"1.0.0.{commit}",
    }
    canonical = json.dumps(
        source,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "version": source["version"],
        "release_source_commit": commit,
        "release_source_revision": revision,
        "release_source_metadata_path": source[
            "release_source_metadata_path"
        ],
        "release_source_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def test_runtime_identity_falls_back_to_valid_baked_release_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commit = "abcdef0"
    revision = "abcdef0123456789abcdef0123456789abcdef01"
    metadata_path = tmp_path / "project" / "static" / "version.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        json.dumps(_metadata(commit, revision), indent=2) + "\n",
        encoding="utf-8",
    )
    for name in (
        "GIT_COMMIT_HASH",
        "VERCEL_GIT_COMMIT_SHA",
        "HF_COMMIT_SHA",
        "COMMIT_REF",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        config.subprocess,
        "check_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.CalledProcessError(128, args[0])
        ),
    )
    config.get_git_commit_hash.cache_clear()

    try:
        assert config.get_git_commit_hash() == commit
        assert config.get_app_version() == f"1.0.0.{commit}"
    finally:
        config.get_git_commit_hash.cache_clear()


def test_runtime_identity_rejects_tampered_baked_release_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    metadata = _metadata(
        "abcdef0", "abcdef0123456789abcdef0123456789abcdef01"
    )
    metadata["release_source_metadata_sha256"] = "0" * 64
    metadata_path = tmp_path / "project" / "static" / "version.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    for name in (
        "GIT_COMMIT_HASH",
        "VERCEL_GIT_COMMIT_SHA",
        "HF_COMMIT_SHA",
        "COMMIT_REF",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        config.subprocess,
        "check_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.CalledProcessError(128, args[0])
        ),
    )
    config.get_git_commit_hash.cache_clear()

    try:
        assert config.get_git_commit_hash() == "unknown"
    finally:
        config.get_git_commit_hash.cache_clear()
