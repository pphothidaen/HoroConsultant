"""Regression tests for low-quota account handoff governance."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "agent_quota_status_guard.py"
PRE_TOOL = ROOT / ".agents" / "hooks" / "pre_tool_check.py"


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "AGENT_QUOTA_REMAINING_PERCENT",
        "AI_AGENT_QUOTA_REMAINING_PERCENT",
        "CODEX_QUOTA_REMAINING_PERCENT",
        "CODEX_REMAINING_QUOTA_PERCENT",
    ):
        env.pop(key, None)
    return env


def test_quota_guard_requires_handoff_below_ten_percent() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--remaining-percent",
            "9",
            "--json",
            "--enforce",
        ],
        cwd=ROOT,
        env=_clean_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["handoff_required"] is True
    assert payload["docs_ok"] is True
    assert payload["remaining_percent"] == 9.0


def test_quota_guard_accepts_status_text_above_threshold() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--status-text",
            "/status quota remaining 42%",
            "--json",
        ],
        cwd=ROOT,
        env=_clean_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["handoff_required"] is False
    assert payload["remaining_percent"] == 42.0


def test_pre_tool_hook_runs_quota_guard_for_status_command() -> None:
    env = _clean_env()
    env["AGENT_QUOTA_REMAINING_PERCENT"] = "9"
    result = subprocess.run(
        [sys.executable, str(PRE_TOOL), "/status"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Pre-Tool Hook Audit: PASSED" in result.stdout
