# project/tests/test_skill_configurations.py
# ===========================================================================
# Skill Context Budget & Governance Spec Test Suite
# ===========================================================================

import os
from pathlib import Path
import yaml
import pytest

from scripts.sync_sdlc_agents import sync_skills

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENTS_SKILLS_DIR = ROOT_DIR / ".agents" / "skills"
ANTIGRAVITY_SKILLS_DIR = ROOT_DIR / ".antigravity" / "skills"

EXPECTED_SKILLS = [
    "ai-inference-verifier",
    "bazi-calculator",
    "bsa-doc-skill-management",
    "devops-deployment",
    "kaggle-manager",
    "qa-e2e-testing",
    "rag-search",
    "sdlc-aisdlc-workflow",
]


def test_all_expected_skills_exist():
    """Verify all expected skills are present in .agents/skills/."""
    assert AGENTS_SKILLS_DIR.exists(), f"Missing directory: {AGENTS_SKILLS_DIR}"
    skill_dirs = [d.name for d in AGENTS_SKILLS_DIR.iterdir() if d.is_dir()]
    for expected in EXPECTED_SKILLS:
        assert expected in skill_dirs, f"Expected skill '{expected}' not found in {AGENTS_SKILLS_DIR}"


def test_skill_frontmatter_and_context_budget():
    """Verify each skill has valid YAML frontmatter and its description is <= 100 chars (context budget)."""
    for skill_name in EXPECTED_SKILLS:
        skill_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing SKILL.md for {skill_name}"
        
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"SKILL.md in {skill_name} must start with YAML frontmatter delimiter '---'"
        
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"SKILL.md in {skill_name} has invalid YAML frontmatter structure"
        
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict), f"Frontmatter in {skill_file} is not a valid YAML mapping"
        assert "name" in fm, f"Frontmatter in {skill_file} missing 'name'"
        assert "description" in fm, f"Frontmatter in {skill_file} missing 'description'"
        
        assert fm["name"] == skill_name, f"Frontmatter name '{fm['name']}' does not match directory '{skill_name}'"
        
        desc = str(fm["description"]).strip()
        assert len(desc) > 0, f"Description for {skill_name} is empty"
        assert len(desc) <= 100, (
            f"Description for '{skill_name}' exceeds context budget: {len(desc)} chars > 100 chars limit. "
            f"Desc: '{desc}'"
        )
        assert "\n" not in desc, f"Description for '{skill_name}' must be a concise single line"


def test_total_skill_context_budget_aggregate():
    """Verify total combined character length of all skill descriptions is under 800 chars."""
    total_desc_len = 0
    for skill_name in EXPECTED_SKILLS:
        skill_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        fm = yaml.safe_load(parts[1])
        desc = str(fm["description"]).strip()
        total_desc_len += len(desc)
    
    assert total_desc_len < 800, f"Total skill descriptions aggregate length ({total_desc_len}) exceeds 800 chars budget"


def test_antigravity_skills_parity():
    """Verify .antigravity/skills/ matches .agents/skills/ exactly."""
    for skill_name in EXPECTED_SKILLS:
        source_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        target_file = ANTIGRAVITY_SKILLS_DIR / skill_name / "SKILL.md"
        
        assert target_file.exists(), f"Missing synced skill in .antigravity/skills/{skill_name}/SKILL.md"
        assert target_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
            f"Mismatch between source skill and synced .antigravity skill for '{skill_name}'"
        )


def test_sync_skills_check_zero_mismatches():
    """Verify sync_skills in check mode returns 0 mismatches."""
    mismatches = sync_skills(check_only=True)
    assert mismatches == 0, f"sync_skills(check_only=True) reported {mismatches} mismatches"
