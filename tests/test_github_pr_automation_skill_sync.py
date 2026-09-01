"""Keep the GitHub PR automation skill available on clean CI checkouts."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agents" / "skills" / "github-pr-automation" / "SKILL.md"
MIRROR = ROOT / ".antigravity" / "skills" / "github-pr-automation" / "SKILL.md"


def test_github_pr_automation_skill_mirror_is_tracked_and_identical() -> None:
    assert SOURCE.is_file()
    assert MIRROR.is_file()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", MIRROR.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert tracked.returncode == 0, "Antigravity skill mirror must be tracked for CI"
    assert MIRROR.read_text(encoding="utf-8") == SOURCE.read_text(encoding="utf-8")
