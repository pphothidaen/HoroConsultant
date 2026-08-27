from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNCED_SKILLS = ("orchestrator-delegation", "qa-e2e-testing")


def test_changed_governance_skills_match_generated_antigravity_mirrors() -> None:
    for skill_name in SYNCED_SKILLS:
        canonical = ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
        mirror = ROOT / ".antigravity" / "skills" / skill_name / "SKILL.md"
        assert mirror.read_bytes() == canonical.read_bytes(), skill_name


def test_full_ai_agent_ecosystem_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/sync_ai_agent_ecosystem.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
