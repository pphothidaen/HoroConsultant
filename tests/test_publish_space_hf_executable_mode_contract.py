"""Regression contract for the frozen 100644 HF Docker payload baseline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.publish_space_hf as publisher


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repo,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


def test_tracked_release_files_rejects_executable_payload_source(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "release-repo"
    script = repo / "scripts" / "entrypoint.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/bin/sh\nexec python3 -m project.main\n", encoding="utf-8")
    script.chmod(0o755)

    _git(repo.parent, "init", "--quiet", str(repo))
    _git(repo, "config", "user.email", "qa@example.invalid")
    _git(repo, "config", "user.name", "Publisher QA")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "add", "scripts/entrypoint.sh")
    _git(repo, "commit", "--quiet", "-m", "freeze executable payload")
    packaging_commit = _git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(publisher, "ROOT", repo)

    with pytest.raises(publisher.PublisherError) as error:
        publisher._tracked_release_files(packaging_commit)

    assert error.value.code == "INVALID_PAYLOAD_FILE"


def test_committed_release_payload_uses_only_regular_100644_sources() -> None:
    packaging_commit = _git(ROOT, "rev-parse", "HEAD")
    records = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", "--full-tree", packaging_commit],
        cwd=ROOT,
    ).split(b"\0")
    invalid: list[tuple[str, str]] = []

    for record in records:
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, _oid = metadata.split(b" ", 2)
        path = raw_path.decode("utf-8")
        if publisher._payload_destination(path) is None:
            continue
        if mode != b"100644" or object_type != b"blob":
            invalid.append((path, mode.decode("ascii")))

    assert invalid == []
