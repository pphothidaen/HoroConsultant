"""Regression tests for cross-platform AI agent ecosystem sync."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml


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
        "HF Static release governance",
    ):
        assert expected_gate in result.stdout


def test_developer_role_defaults_to_luna_with_adaptive_escalation() -> None:
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    assert settings["models"]["developer"] == "gpt-5.6-luna"

    source = yaml.safe_load(
        (ROOT / ".antigravity" / "agents" / "developer.agent").read_text(
            encoding="utf-8"
        )
    )
    assert source["model"] == "gpt-5.6-luna"
    assert str(source["effort"]).casefold() == "medium"

    source_prompt = str(source["system_prompt"])
    normalized_prompt = " ".join(source_prompt.casefold().split())
    for expected_contract in (
        "gpt-5.6-luna",
        "medium",
        "rank 0",
        "rank 1",
        "adaptive",
        "gpt-5.6-terra",
        "rank 2",
        "gpt-5.6-sol",
        "rank 3",
        "high",
    ):
        assert expected_contract in normalized_prompt

    generated_json = json.loads(
        (ROOT / ".agents" / "agents" / "developer" / "agent.json").read_text(
            encoding="utf-8"
        )
    )
    assert generated_json["model"] == source["model"]
    assert generated_json["thinking_effort"].casefold() == source["effort"].casefold()
    assert generated_json["system_prompt"] == source_prompt

    generated_toml = tomllib.loads(
        (ROOT / ".codex" / "agents" / "developer.toml").read_text(encoding="utf-8")
    )
    assert source_prompt in generated_toml["developer_instructions"]

    model_policy = yaml.safe_load(
        (ROOT / ".agents" / "config" / "multiagent_model_policy.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert model_policy["quality_floors"][1]["profile"] == "gpt-5.6-luna/medium"
    assert model_policy["quality_floors"][2]["profile"] == "gpt-5.6-terra/high"
    assert model_policy["quality_floors"][3]["profile"] == "gpt-5.6-sol/high"

    agent_catalog = (ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
    developer_lines = [
        line for line in agent_catalog.splitlines() if "**`developer`**" in line
    ]
    assert developer_lines
    assert all("gpt-5.6-luna" in line for line in developer_lines)
    assert all("gpt-5.3-codex" not in line for line in developer_lines)
    assert (
        "| **`devops` / `code_reviewer`** | Release & safety gates | "
        "`gpt-5.3-codex-spark` | **High** |" in agent_catalog
    )
    assert (
        "| **`devops`** | DevOps & Release Agent | `gpt-5.3-codex-spark` |" in agent_catalog
    )
    assert (
        "| **`code_reviewer`** | Pre-Deployment Safety Auditor | "
        "`gpt-5.3-codex-spark` |" in agent_catalog
    )
