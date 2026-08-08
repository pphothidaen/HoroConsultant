# project/tests/test_agent_configurations.py
# ===========================================================================
# Computational Metaphysics Engine — Agent Configuration & Discovery Test
# ===========================================================================

import os
import json
import yaml
import pytest

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


def test_antigravity_default_agent_file():
    """Verify .antigravity/agents/default.agent structure and fields."""
    default_agent_path = os.path.join(ANTIGRAVITY_AGENTS_DIR, "default.agent")
    assert os.path.exists(default_agent_path), f"Missing {default_agent_path}"
    
    with open(default_agent_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert "Default Agent" in data["name"] or "Master Orchestrator" in data["name"]
    assert "Gemini 3.6 Flash" in data["model"]
    assert data.get("thinking") is True
    assert "bazi-calculator" in data.get("tools", [])
    assert "rag-search" in data.get("tools", [])
    assert data.get("fallback_agent") in ["orchestrator", "default"]


def test_antigravity_agents_parsing():
    """Verify all .agent files in .antigravity/agents/ parse valid YAML."""
    agent_files = [f for f in os.listdir(ANTIGRAVITY_AGENTS_DIR) if f.endswith(".agent")]
    assert len(agent_files) >= 5, "Should have at least 5 .agent files"
    
    for filename in agent_files:
        filepath = os.path.join(ANTIGRAVITY_AGENTS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"Failed to parse dict from {filename}"
        assert "name" in data, f"Missing 'name' in {filename}"
        assert "model" in data or "provider" in data, f"Missing model info in {filename}"
        assert "system_prompt" in data, f"Missing 'system_prompt' in {filename}"


def test_agents_directory_markdown_files():
    """Verify all agent subdirectories in .agents/agents contain lowercase agent.md with frontmatter."""
    subdirs = [d for d in os.listdir(AGENTS_AGENTS_DIR) if os.path.isdir(os.path.join(AGENTS_AGENTS_DIR, d))]
    assert len(subdirs) >= 15, f"Expected 15 agent directories, found {len(subdirs)}"

    for subdir in subdirs:
        dir_files = os.listdir(os.path.join(AGENTS_AGENTS_DIR, subdir))
        assert "agent.md" in dir_files, f"Missing lowercase agent.md in .agents/agents/{subdir}"
        assert "AGENT.md" not in dir_files, f"Found duplicate uppercase AGENT.md in .agents/agents/{subdir}"

        agent_md_path = os.path.join(AGENTS_AGENTS_DIR, subdir, "agent.md")

        # Verify YAML frontmatter parsing
        with open(agent_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert content.startswith("---"), f"Missing YAML frontmatter start in {subdir}/agent.md"
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"Invalid YAML frontmatter block in {subdir}/agent.md"

        frontmatter = yaml.safe_load(parts[1])
        assert "name" in frontmatter, f"Missing 'name' in frontmatter of {subdir}/agent.md"
        assert "role" in frontmatter, f"Missing 'role' in frontmatter of {subdir}/agent.md"
        assert "model" in frontmatter, f"Missing 'model' in frontmatter of {subdir}/agent.md"
