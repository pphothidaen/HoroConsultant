"""Regression tests for cross-platform AI agent ecosystem sync."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

from scripts import sync_sdlc_agents as sdlc_sync


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


def test_nested_agent_json_is_canonical_over_stale_antigravity_and_loose_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "workspace"
    agents_dir = root / ".agents" / "agents"
    antigravity_dir = root / ".antigravity" / "agents"
    canonical_role_dir = agents_dir / "qa_fixture"
    canonical_role_dir.mkdir(parents=True)
    antigravity_dir.mkdir(parents=True)
    temporary_home = tmp_path / "home"
    temporary_home.mkdir()

    canonical_agent = {
        "name": "qa_fixture",
        "role": "Canonical QA Fixture",
        "model": "canonical-model",
        "thinking_effort": "High",
        "description": "Nested JSON is the canonical source.",
        "tools": ["qa-e2e-testing", "hf-static-release-verification"],
        "system_prompt": "Use only canonical unsuffixed tool identifiers.",
    }
    canonical_bytes = (json.dumps(canonical_agent, indent=2) + "\n").encode("utf-8")
    canonical_json = canonical_role_dir / "agent.json"
    canonical_json.write_bytes(canonical_bytes)

    (antigravity_dir / "qa_fixture.agent").write_text(
        yaml.safe_dump(
            {
                "name": "qa_fixture",
                "display_name": "Stale Antigravity Fixture",
                "model": "stale-model",
                "effort": "low",
                "tools": ["stale-tool.skill"],
                "system_prompt": "This stale file must never be authoritative.",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (agents_dir / "qa_fixture.md").write_text(
        "---\nname: qa_fixture\ntools:\n  - loose-tool.skill\n---\n\nLoose stale prompt.\n",
        encoding="utf-8",
    )
    # A loose generated artifact may exist, but must never compete with the
    # nested canonical source when the synchronizer selects authority.
    (agents_dir / "qa_fixture.json").write_text(
        json.dumps({"name": "qa_fixture", "tools": ["loose-tool.skill"]}),
        encoding="utf-8",
    )

    monkeypatch.setattr(sdlc_sync, "ROOT", root)
    monkeypatch.setattr(sdlc_sync, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(sdlc_sync, "ANTIGRAVITY_DIR", antigravity_dir)
    monkeypatch.setattr(sdlc_sync.Path, "home", classmethod(lambda cls: temporary_home))

    sync_result = sdlc_sync.sync_all_agents(check_only=False)
    nested_after_sync = canonical_json.read_bytes()
    regenerated_loose_json = json.loads(
        (agents_dir / "qa_fixture.json").read_text(encoding="utf-8")
    )
    loose_md = (agents_dir / "qa_fixture.md").read_text(encoding="utf-8")
    regenerated_loose_md = yaml.safe_load(loose_md.split("---", 2)[1])
    generated_antigravity = yaml.safe_load(
        (antigravity_dir / "qa_fixture.agent").read_text(encoding="utf-8")
    )

    (antigravity_dir / "qa_fixture.agent").write_text(
        yaml.safe_dump(
            {**generated_antigravity, "model": "drifted-model"}, sort_keys=False
        ),
        encoding="utf-8",
    )
    check_result = sdlc_sync.sync_all_agents(check_only=True)

    assert sync_result is True
    assert nested_after_sync == canonical_bytes
    assert regenerated_loose_json["tools"] == canonical_agent["tools"]
    assert regenerated_loose_json["system_prompt"] == canonical_agent["system_prompt"]
    assert regenerated_loose_md["tools"] == canonical_agent["tools"]
    assert canonical_agent["system_prompt"] in loose_md
    assert generated_antigravity["model"] == canonical_agent["model"]
    assert generated_antigravity["system_prompt"] == canonical_agent["system_prompt"]
    assert generated_antigravity["tools"] == canonical_agent["tools"]
    assert all(not tool.endswith(".skill") for tool in generated_antigravity["tools"])
    assert check_result is False


def test_check_cli_dispatch_uses_python_canonical_authority_even_when_rust_binary_exists(
    tmp_path: Path, monkeypatch
) -> None:
    stale_rust_binary = tmp_path / "rust_core" / "target" / "release" / "sync_sdlc_agents"
    stale_rust_binary.parent.mkdir(parents=True)
    stale_rust_binary.write_text("stale binary must not be executed", encoding="utf-8")
    calls: list[tuple[bool, bool]] = []

    def fake_sync_all_agents(*, check_only: bool = False, list_only: bool = False) -> bool:
        calls.append((check_only, list_only))
        return False

    def subprocess_must_not_run(*args, **kwargs):
        raise AssertionError("--check must not dispatch the stale Rust synchronizer")

    monkeypatch.setattr(sdlc_sync, "ROOT", tmp_path)
    monkeypatch.setattr(sdlc_sync, "sync_all_agents", fake_sync_all_agents)
    monkeypatch.setattr(
        sdlc_sync,
        "subprocess",
        type("NoSubprocess", (), {"run": staticmethod(subprocess_must_not_run)}),
        raising=False,
    )

    assert sdlc_sync.main(["--check"]) == 1
    assert calls == [(True, False)]


@pytest.mark.parametrize(
    ("field", "invalid_value", "remove_field"),
    (
        ("name", "", False),
        ("role", "", False),
        ("model", "", False),
        ("thinking_effort", "", False),
        ("description", "", False),
        ("system_prompt", "", False),
        ("name", None, True),
        ("role", None, True),
        ("model", None, True),
        ("thinking_effort", None, True),
        ("description", None, True),
        ("system_prompt", None, True),
        ("name", None, False),
        ("role", None, False),
        ("model", None, False),
        ("thinking_effort", None, False),
        ("description", None, False),
        ("system_prompt", None, False),
        ("tools", None, True),
        ("tools", [], False),
        ("tools", ["valid-tool", ""], False),
        ("tools", "not-a-list", False),
    ),
)
def test_invalid_canonical_json_fails_before_any_generated_output_write(
    tmp_path: Path, monkeypatch, field: str, invalid_value: object, remove_field: bool
) -> None:
    root = tmp_path / "workspace"
    agents_dir = root / ".agents" / "agents"
    antigravity_dir = root / ".antigravity" / "agents"
    role_dir = agents_dir / "qa_fixture"
    role_dir.mkdir(parents=True)
    antigravity_dir.mkdir(parents=True)
    temporary_home = tmp_path / "home"
    temporary_home.mkdir()
    canonical = {
        "name": "qa_fixture",
        "role": "Canonical QA Fixture",
        "model": "canonical-model",
        "thinking_effort": "High",
        "description": "A valid canonical description.",
        "tools": ["qa-e2e-testing"],
        "system_prompt": "A valid canonical system prompt.",
    }
    if remove_field:
        canonical.pop(field)
    else:
        canonical[field] = invalid_value
    canonical_json = role_dir / "agent.json"
    canonical_json.write_text(json.dumps(canonical), encoding="utf-8")
    stale_antigravity = antigravity_dir / "qa_fixture.agent"
    stale_antigravity.write_text(
        yaml.safe_dump(
            {
                "name": "qa_fixture",
                "display_name": "stale output",
                "model": "stale-model",
                "effort": "low",
                "tools": ["stale-tool.skill"],
                "system_prompt": "stale output",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    loose_json = agents_dir / "qa_fixture.json"
    loose_md = agents_dir / "qa_fixture.md"
    loose_json.write_text('{"sentinel": "must remain"}\n', encoding="utf-8")
    loose_md.write_text("sentinel markdown must remain\n", encoding="utf-8")
    before = {
        path: path.read_bytes()
        for path in (canonical_json, stale_antigravity, loose_json, loose_md)
    }

    monkeypatch.setattr(sdlc_sync, "ROOT", root)
    monkeypatch.setattr(sdlc_sync, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(sdlc_sync, "ANTIGRAVITY_DIR", antigravity_dir)
    monkeypatch.setattr(sdlc_sync.Path, "home", classmethod(lambda cls: temporary_home))

    sync_result = sdlc_sync.sync_all_agents(check_only=False)
    after = {path: path.read_bytes() for path in before}

    assert sync_result is False
    assert after == before


def test_check_only_skill_sync_is_read_only_and_rejects_missing_canonical_skills(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "workspace"
    antigravity_skills = root / ".antigravity" / "skills"
    monkeypatch.setattr(sdlc_sync, "ROOT", root)

    result = sdlc_sync.sync_skills(check_only=True)

    assert result == 1
    assert not antigravity_skills.exists()


def test_optional_canonical_runtime_settings_round_trip_to_all_generated_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "workspace"
    agents_dir = root / ".agents" / "agents"
    antigravity_dir = root / ".antigravity" / "agents"
    role_dir = agents_dir / "orchestrator"
    role_dir.mkdir(parents=True)
    antigravity_dir.mkdir(parents=True)
    temporary_home = tmp_path / "home"
    temporary_home.mkdir()
    canonical = {
        "name": "orchestrator",
        "role": "Canonical Orchestrator",
        "model": "canonical-model",
        "thinking_effort": "High",
        "description": "Optional runtime settings must be preserved.",
        "tools": ["orchestrator-delegation"],
        "system_prompt": "Preserve optional runtime settings exactly.",
        "thinking": True,
        "fallback_agent": "qa_tester",
    }
    (role_dir / "agent.json").write_text(json.dumps(canonical), encoding="utf-8")

    monkeypatch.setattr(sdlc_sync, "ROOT", root)
    monkeypatch.setattr(sdlc_sync, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(sdlc_sync, "ANTIGRAVITY_DIR", antigravity_dir)
    monkeypatch.setattr(sdlc_sync.Path, "home", classmethod(lambda cls: temporary_home))

    assert sdlc_sync.sync_all_agents(check_only=False) is True

    antigravity = yaml.safe_load(
        (antigravity_dir / "orchestrator.agent").read_text(encoding="utf-8")
    )
    loose_json = json.loads((agents_dir / "orchestrator.json").read_text(encoding="utf-8"))
    loose_md = (agents_dir / "orchestrator.md").read_text(encoding="utf-8")
    markdown_frontmatter = yaml.safe_load(loose_md.split("---", 2)[1])

    for generated in (antigravity, loose_json, markdown_frontmatter):
        assert generated["thinking"] is True
        assert generated["fallback_agent"] == "qa_tester"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    (
        ("thinking", "true"),
        ("thinking", 1),
        ("fallback_agent", "../qa"),
        ("fallback_agent", "/tmp/qa"),
        ("fallback_agent", "qa/test"),
        ("fallback_agent", r"qa\test"),
        ("fallback_agent", "."),
        ("fallback_agent", ".."),
        ("fallback_agent", ""),
        ("fallback_agent", 3),
    ),
)
def test_invalid_optional_runtime_settings_fail_before_generated_writes(
    tmp_path: Path, monkeypatch, field: str, invalid_value: object
) -> None:
    root = tmp_path / "workspace"
    agents_dir = root / ".agents" / "agents"
    antigravity_dir = root / ".antigravity" / "agents"
    role_dir = agents_dir / "qa_fixture"
    role_dir.mkdir(parents=True)
    antigravity_dir.mkdir(parents=True)
    temporary_home = tmp_path / "home"
    temporary_home.mkdir()
    canonical = {
        "name": "qa_fixture",
        "role": "Canonical QA Fixture",
        "model": "canonical-model",
        "thinking_effort": "High",
        "description": "Optional runtime setting validation.",
        "tools": ["qa-e2e-testing"],
        "system_prompt": "Reject invalid optional runtime settings.",
        "thinking": True,
        "fallback_agent": "qa_tester",
    }
    canonical[field] = invalid_value
    canonical_json = role_dir / "agent.json"
    canonical_json.write_text(json.dumps(canonical), encoding="utf-8")
    generated_yaml = antigravity_dir / "qa_fixture.agent"
    generated_json = agents_dir / "qa_fixture.json"
    generated_md = agents_dir / "qa_fixture.md"
    for path in (generated_yaml, generated_json, generated_md):
        path.write_text(f"sentinel {path.name}\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in (canonical_json, generated_yaml, generated_json, generated_md)}

    monkeypatch.setattr(sdlc_sync, "ROOT", root)
    monkeypatch.setattr(sdlc_sync, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(sdlc_sync, "ANTIGRAVITY_DIR", antigravity_dir)
    monkeypatch.setattr(sdlc_sync.Path, "home", classmethod(lambda cls: temporary_home))

    result = sdlc_sync.sync_all_agents(check_only=False)
    after = {path: path.read_bytes() for path in before}

    assert result is False
    assert after == before
