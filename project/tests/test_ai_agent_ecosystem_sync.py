"""Regression tests for cross-platform AI agent ecosystem sync."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = ROOT / "scripts" / "sync_ai_agent_ecosystem.py"


def test_ai_agent_ecosystem_sync_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for expected_gate in (
        "claude hooks",
        "claude rules",
        "Antigravity/Gemini/AGY sync",
        "Codex/OpenAI sync",
        "hermes/thClaws contract",
    ):
        assert expected_gate in result.stdout
