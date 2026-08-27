"""Regression contract for executable files in the HF Docker payload."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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


def test_tracked_release_files_accepts_matching_regular_executable(
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

    files = publisher._tracked_release_files(packaging_commit)

    assert [(item.path, item.source_path, item.data) for item in files] == [
        (
            "scripts/entrypoint.sh",
            "scripts/entrypoint.sh",
            b"#!/bin/sh\nexec python3 -m project.main\n",
        )
    ]
