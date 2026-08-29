"""Black-box contract for the developer role's adaptive routing defaults."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _normalized(text: object) -> str:
    return " ".join(str(text).casefold().split())


def _markdown(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.relative_to(ROOT)} needs YAML frontmatter"
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter) or {}
    assert isinstance(metadata, dict)
    return metadata, body.strip()


def test_developer_defaults_to_luna_without_weakening_release_roles() -> None:
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    assert settings["models"]["developer"] == "gpt-5.6-luna"
    assert settings["models"]["devops"] == "gpt-5.3-codex"
    assert settings["models"]["code_reviewer"] == "gpt-5.3-codex"

    source = yaml.safe_load(
        (ROOT / ".antigravity" / "agents" / "developer.agent").read_text(
            encoding="utf-8"
        )
    )
    assert source["model"] == "gpt-5.6-luna"
    assert str(source["effort"]).casefold() == "medium"
    prompt = _normalized(source["system_prompt"])
    for contract in (
        "gpt-5.6-luna",
        "medium effort by default",
        "rank 0",
        "rank 1",
        "adaptive routing escalates rank 2",
        "gpt-5.6-terra",
        "rank 3",
        "gpt-5.6-sol",
        "static metadata is routing intent and never runtime proof",
    ):
        assert contract in prompt


def test_versioned_policy_retains_the_luna_terra_sol_quality_floors() -> None:
    policy = yaml.safe_load(
        (ROOT / ".agents" / "config" / "multiagent_model_policy.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert policy["quality_floors"] == {
        0: {"profile": "gpt-5.6-luna/low"},
        1: {"profile": "gpt-5.6-luna/medium"},
        2: {"profile": "gpt-5.6-terra/high"},
        3: {"profile": "gpt-5.6-sol/high"},
    }


def test_developer_catalog_and_generated_mirrors_match_the_source() -> None:
    source = yaml.safe_load(
        (ROOT / ".antigravity" / "agents" / "developer.agent").read_text(
            encoding="utf-8"
        )
    )
    source_prompt = str(source["system_prompt"])

    catalog = (ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
    developer_lines = [
        line for line in catalog.splitlines() if "**`developer`**" in line
    ]
    assert developer_lines
    assert all("gpt-5.6-luna" in line for line in developer_lines)
    assert all("gpt-5.3-codex" not in line for line in developer_lines)
    routing_rules = _normalized(catalog.split("Model Routing Rules", 1)[1])
    for contract in (
        "gpt-5.6-luna` at medium effort",
        "rank-0/rank-1",
        "rank 2 to `gpt-5.6-terra` at high effort",
        "rank 3 to `gpt-5.6-sol` at high effort",
    ):
        assert contract in routing_rules

    json_paths = (
        ROOT / ".agents" / "agents" / "developer.json",
        ROOT / ".agents" / "agents" / "developer" / "agent.json",
    )
    generated_json = [json.loads(path.read_text(encoding="utf-8")) for path in json_paths]
    assert generated_json[0] == generated_json[1]
    assert generated_json[0]["model"] == source["model"]
    assert generated_json[0]["thinking_effort"].casefold() == str(
        source["effort"]
    ).casefold()
    assert generated_json[0]["system_prompt"] == source_prompt

    markdown_paths = (
        ROOT / ".agents" / "agents" / "developer.md",
        ROOT / ".agents" / "agents" / "developer" / "agent.md",
    )
    generated_markdown = [path.read_text(encoding="utf-8") for path in markdown_paths]
    assert generated_markdown[0] == generated_markdown[1]
    markdown_metadata, markdown_body = _markdown(markdown_paths[0])
    assert markdown_metadata["model"] == source["model"]
    assert str(markdown_metadata["thinking_effort"]).casefold() == str(
        source["effort"]
    ).casefold()
    assert markdown_body == source_prompt.strip()

    codex = tomllib.loads(
        (ROOT / ".codex" / "agents" / "developer.toml").read_text(encoding="utf-8")
    )
    assert codex["developer_instructions"].startswith(source_prompt.rstrip())

    sync = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_ai_agent_ecosystem.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert sync.returncode == 0, sync.stdout + sync.stderr
