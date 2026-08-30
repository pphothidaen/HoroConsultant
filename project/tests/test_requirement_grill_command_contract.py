"""Black-box contract for the canonical ``/grill-me`` intake command."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _markdown(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.relative_to(ROOT)} needs YAML frontmatter"
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter) or {}
    assert isinstance(metadata, dict)
    return metadata, body.strip()


def _normalized(text: object) -> str:
    return " ".join(str(text).casefold().split())


def test_grill_me_command_is_intake_only_and_fail_closed() -> None:
    command_path = ROOT / ".agents" / "commands" / "grill-me.md"
    assert command_path.is_file(), "missing canonical command .agents/commands/grill-me.md"

    metadata, body = _markdown(command_path)
    assert metadata["argument-hint"] == "<task or change request>"
    assert "requirement intake" in _normalized(metadata["description"])

    normalized = _normalized(body)
    for contract in (
        "$arguments",
        ".agents/skills/requirement-grill-gate/skill.md",
        'what outcome should `/grill-me` define?',
        "assess all nine dimensions",
        "ask exactly one question per interaction",
        "approved",
        "waived",
        "blocked",
        "do not plan, implement, delegate implementation",
        "unless the current request explicitly authorizes that artifact",
    ):
        assert contract in normalized


def test_requirement_grill_skill_defines_one_closed_nine_dimension_gate() -> None:
    skill_path = ROOT / ".agents" / "skills" / "requirement-grill-gate" / "SKILL.md"
    metadata, body = _markdown(skill_path)
    normalized = _normalized(body)

    assert metadata == {
        "name": "requirement-grill-gate",
        "description": (
            "Run fail-closed 9-dimension intake before planning, delegation, "
            "or implementation."
        ),
    }
    for dimension in range(1, 10):
        assert re.search(rf"\bD{dimension}\b", body), f"D{dimension} is not assessed"
    for contract in (
        "business_analyst` owns the canonical command and skill contract",
        "the only valid terminal states are `approved`, `waived`, and `blocked`",
        "what outcome should `/grill-me` define?",
        "ask exactly one owner-facing question per interaction",
        "by default, return the report in conversation only",
        "authorized next phase",
        "do not begin the next phase",
    ):
        assert contract in normalized


def test_business_analyst_ownership_and_generated_mirrors_are_synchronized() -> None:
    source_paths = (
        ROOT / ".antigravity" / "agents" / "business-analyst.agent",
        ROOT / ".antigravity" / "agents" / "business_analyst.agent",
    )
    sources = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in source_paths]
    assert sources[0] == sources[1]
    source = sources[0]
    assert isinstance(source, dict)
    assert "requirement-grill-gate" in source["tools"]
    source_prompt = str(source["system_prompt"])
    assert "own the canonical `/grill-me` command" in _normalized(source_prompt)

    json_paths = (
        ROOT / ".agents" / "agents" / "business_analyst.json",
        ROOT / ".agents" / "agents" / "business_analyst" / "agent.json",
    )
    generated_json = [json.loads(path.read_text(encoding="utf-8")) for path in json_paths]
    assert generated_json[0] == generated_json[1]
    assert generated_json[0]["tools"] == source["tools"]
    assert generated_json[0]["system_prompt"] == source_prompt

    markdown_paths = (
        ROOT / ".agents" / "agents" / "business_analyst.md",
        ROOT / ".agents" / "agents" / "business_analyst" / "agent.md",
    )
    generated_markdown = [path.read_text(encoding="utf-8") for path in markdown_paths]
    assert generated_markdown[0] == generated_markdown[1]
    markdown_metadata, markdown_body = _markdown(markdown_paths[0])
    assert markdown_metadata["tools"] == source["tools"]
    assert markdown_body == source_prompt.strip()

    codex = tomllib.loads(
        (ROOT / ".codex" / "agents" / "business_analyst.toml").read_text(
            encoding="utf-8"
        )
    )
    assert codex["developer_instructions"].startswith(source_prompt.rstrip())
    assert "$requirement-grill-gate" in codex["developer_instructions"]

    skill = (ROOT / ".agents" / "skills" / "requirement-grill-gate" / "SKILL.md")
    skill_mirror = (
        ROOT / ".antigravity" / "skills" / "requirement-grill-gate" / "SKILL.md"
    )
    assert skill.read_bytes() == skill_mirror.read_bytes()

    catalog = (ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
    assert "BSA-owned `/grill-me`" in catalog
