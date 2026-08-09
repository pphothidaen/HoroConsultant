# project/tests/test_agent_configurations.py
# ===========================================================================
# Computational Metaphysics Engine — Agent Configuration & Discovery Test
# ===========================================================================

import json
import os
from pathlib import Path

import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ANTIGRAVITY_AGENTS_DIR = os.path.join(ROOT_DIR, ".antigravity/agents")
AGENTS_AGENTS_DIR = os.path.join(ROOT_DIR, ".agents/agents")
SETTINGS_FILE = os.path.join(ROOT_DIR, "settings.json")


def test_settings_json_default_agent():
    """Verify settings.json specifies orchestrator as default_agent and Gemini 3.6 Flash (High)."""
    assert os.path.exists(SETTINGS_FILE), f"Missing {SETTINGS_FILE}"
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
    assert settings.get("default_agent") == "orchestrator"
    assert settings.get("models", {}).get("default") == "Gemini 3.6 Flash (High)"


def test_default_agent_is_an_explicit_orchestrator_router():
    """Verify Codex's root profile explicitly plans and routes incoming work."""
    default_agent_path = os.path.join(AGENTS_AGENTS_DIR, "default", "agent.json")
    with open(default_agent_path, "r", encoding="utf-8") as f:
        default_agent = json.load(f)

    assert default_agent["name"] == "default"
    assert "Default Orchestrator Router" in default_agent["role"]
    prompt = default_agent["system_prompt"]
    for stage in ("Classify", "Plan", "Delegate", "Synthesize", "Verify"):
        assert stage in prompt
    assert "distinct file or responsibility ownership" in prompt


def test_agy_default_agent_uses_the_orchestrator_router_contract():
    """Verify the AGY source profile uses the same default routing contract."""
    default_agent_path = os.path.join(ANTIGRAVITY_AGENTS_DIR, "default.agent")
    with open(default_agent_path, "r", encoding="utf-8") as f:
        default_agent = yaml.safe_load(f)

    assert "Default Orchestrator Router" in default_agent["display_name"]
    prompt = default_agent["system_prompt"]
    for stage in ("Classify", "Plan", "Delegate", "Synthesize", "Verify"):
        assert stage in prompt
    assert default_agent["fallback_agent"] == "orchestrator"


def test_default_agent_markdown_has_no_trailing_blank_line():
    """Verify the AGY synchronizer normalizes a block prompt's final newline."""
    default_agent_path = os.path.join(AGENTS_AGENTS_DIR, "default", "agent.md")
    with open(default_agent_path, "r", encoding="utf-8") as f:
        rendered_agent = f.read()

    assert not rendered_agent.endswith("\n\n")


def test_pytest_does_not_collect_project_local_worktrees():
    """Keep release audits from collecting duplicate tests in .worktrees/."""
    pytest_config = (Path(ROOT_DIR) / "pytest.ini").read_text(encoding="utf-8")

    assert ".worktrees" in pytest_config


def test_antigravity_default_agent_file():
    """Verify .antigravity/agents/default.agent structure and fields."""
    default_agent_path = os.path.join(ANTIGRAVITY_AGENTS_DIR, "default.agent")
    with open(default_agent_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert data["name"] == "default" or "default" in data["name"]
    assert "Default Agent" in data.get("display_name", "") or "Master Orchestrator" in data.get("display_name", "")
    assert "Gemini 3.6 Flash" in data["model"] or "Claude 3.7 Sonnet" in data["model"] or "CODEX_PRO" in data["model"] or "codex" in data["model"].lower()
    assert data.get("thinking") is True
    assert "bazi-calculator" in data.get("tools", [])
    assert "rag-search" in data.get("tools", [])
    assert data.get("fallback_agent") in ["orchestrator", "default"]


def test_antigravity_agents_parsing():
    """Verify all .agent files in .antigravity/agents/ parse valid YAML."""
    agent_files = [f for f in os.listdir(ANTIGRAVITY_AGENTS_DIR) if f.endswith(".agent")]
    assert len(agent_files) >= 16, f"Should have at least 16 .agent files in .antigravity/agents, found {len(agent_files)}"
    
    for filename in agent_files:
        filepath = os.path.join(ANTIGRAVITY_AGENTS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"Failed to parse dict from {filename}"
        assert "name" in data, f"Missing 'name' in {filename}"
        normalized_stem = filename[:-6].replace("-", "_")
        normalized_data_name = data['name'].replace("-", "_")
        assert normalized_stem == normalized_data_name, f"Mismatch between filename '{filename}' and internal name '{data['name']}'"
        assert "model" in data or "provider" in data, f"Missing model info in {filename}"
        assert "system_prompt" in data, f"Missing 'system_prompt' in {filename}"


def test_agents_dir_sync_both_formats():
    """Verify .agents/agents/ contains both folder/agent.md and top-level .md files for all 16 agents."""
    agent_names = [
        "business_analyst", "code_reviewer", "default", "developer", "devops",
        "ming_xue_master", "numerology_master", "orchestrator", "prediction_validator",
        "pu_shi_master", "qa_tester", "san_shi_master", "thai_vedic_master",
        "western_astro_master", "xiang_xue_master", "ze_ji_master"
    ]
    for name in agent_names:
        folder_md = os.path.join(AGENTS_AGENTS_DIR, name, "agent.md")
        toplevel_md = os.path.join(AGENTS_AGENTS_DIR, f"{name}.md")
        assert os.path.exists(folder_md), f"Missing {folder_md}"
        assert os.path.exists(toplevel_md), f"Missing {toplevel_md}"
