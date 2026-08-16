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


def _is_disabled(skill_file: Path) -> bool:
    content = skill_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    fm = yaml.safe_load(parts[1])
    return bool(fm.get("disabled")) or str(fm.get("description", "")).lstrip().startswith("DISABLED —")


def _active_skills() -> list[str]:
    names = []
    for skill_name in EXPECTED_SKILLS:
        skill_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        if skill_file.exists() and not _is_disabled(skill_file):
            names.append(skill_name)
    return names


def _agent_skill_refs() -> set[str]:
    refs = set()
    agent_dirs = [
        ROOT_DIR / ".agents" / "agents",
        ROOT_DIR / ".antigravity" / "agents",
        ROOT_DIR / ".codex" / "agents",
    ]

    for agent_dir in agent_dirs:
        for path in agent_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".json", ".md", ".yaml", ".toml", ".agent"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for skill_name in EXPECTED_SKILLS:
                if skill_name in text:
                    refs.add(skill_name)
    return refs


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
    """Verify total combined character length of active skill descriptions is under 800 chars."""
    active_skills = _active_skills()
    assert len(active_skills) > 0, "No active skills found for aggregate context budget check"

    total_desc_len = 0
    for skill_name in active_skills:
        skill_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        fm = yaml.safe_load(parts[1])
        desc = str(fm["description"]).strip()
        total_desc_len += len(desc)
    
    assert total_desc_len < 800, f"Total skill descriptions aggregate length ({total_desc_len}) exceeds 800 chars budget"


def test_disabled_skills_are_not_active_dependencies():
    """Unused skills should be explicitly marked disabled so they do not consume budget."""
    active_refs = _agent_skill_refs()
    active_skills = _active_skills()

    for skill_name in EXPECTED_SKILLS:
        skill_file = AGENTS_SKILLS_DIR / skill_name / "SKILL.md"
        disabled = _is_disabled(skill_file)
        if skill_name in active_refs:
            assert not disabled, f"Skill '{skill_name}' is referenced by an agent/manifest but marked disabled"
            assert skill_name in active_skills, f"Skill '{skill_name}' was not included in active budget calculation"
        else:
            assert disabled, f"Unused skill '{skill_name}' must be explicitly marked disabled to avoid budget pressure"


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
