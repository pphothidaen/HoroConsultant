"""Tests for Claude Code command governance artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
HOOK = CLAUDE_DIR / "hooks" / "pre_tool_guard.py"
ORCHESTRATOR_HOOK = CLAUDE_DIR / "hooks" / "orchestrator_only_guard.py"
RULES_DIR = CLAUDE_DIR / "rules"


def run_hook(payload: dict[str, object]) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def run_orchestrator_hook(payload: dict[str, object], *, enabled: bool) -> dict[str, object]:
    environment = {**__import__("os").environ}
    if enabled:
        environment["HORO_ORCHESTRATOR_ONLY"] = "1"
    else:
        environment.pop("HORO_ORCHESTRATOR_ONLY", None)
    result = subprocess.run(
        [sys.executable, str(ORCHESTRATOR_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout) if result.stdout else {}


def assert_denied(output: dict[str, object]) -> None:
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert hook_output["permissionDecisionReason"]


def test_claude_settings_json_registers_pretooluse_guard() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    pretooluse = settings["hooks"]["PreToolUse"]

    assert pretooluse
    matcher = "|".join(group["matcher"] for group in pretooluse)
    for tool_name in ("Bash", "Read", "Edit", "Write", "MultiEdit", "Glob", "Grep"):
        assert tool_name in matcher
    commands = " ".join(
        hook["command"]
        for matcher_group in pretooluse
        for hook in matcher_group["hooks"]
    )
    assert "pre_tool_guard.py" in commands
    assert "orchestrator_only_guard.py" in commands


def test_pretooluse_guard_denies_secret_file_reads_without_opening_file() -> None:
    output = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": ".env"},
        }
    )

    assert_denied(output)


def test_pretooluse_guard_denies_destructive_bash_commands() -> None:
    output = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
        }
    )

    assert_denied(output)


def test_pretooluse_guard_denies_token_retrieval_commands() -> None:
    output = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "gh auth token"},
        }
    )

    assert_denied(output)


def test_orchestrator_guard_blocks_root_implementation_and_git_mutation() -> None:
    for payload in (
        {"tool_name": "Edit", "tool_input": {"file_path": "project/main.py"}},
        {"tool_name": "Bash", "tool_input": {"command": "python3 -m pytest -q"}},
        {"tool_name": "Bash", "tool_input": {"command": "git commit -m guarded"}},
    ):
        assert_denied(run_orchestrator_hook(payload, enabled=True))


def test_orchestrator_guard_allows_monitoring_and_unmarked_sessions() -> None:
    assert run_orchestrator_hook(
        {"tool_name": "Bash", "tool_input": {"command": "git status --short"}}, enabled=True
    ) == {}
    assert run_orchestrator_hook(
        {"tool_name": "Bash", "tool_input": {"command": "git commit -m child"}}, enabled=False
    ) == {}


def test_claude_rules_have_context_paths_frontmatter() -> None:
    rule_files = sorted(RULES_DIR.glob("*.md"))
    assert rule_files

    for rule_file in rule_files:
        content = rule_file.read_text(encoding="utf-8")
        assert content.startswith("---\n"), f"missing frontmatter: {rule_file}"
        _, frontmatter, _ = content.split("---", 2)
        data = yaml.safe_load(frontmatter)
        assert data["description"], f"missing description: {rule_file}"
        assert data["paths"], f"missing paths: {rule_file}"
        assert isinstance(data["paths"], list), f"paths must be list: {rule_file}"


def test_global_claude_context_references_local_override_not_secret_content() -> None:
    content = (CLAUDE_DIR / "CLAUDE.md").read_text(encoding="utf-8")

    assert ".claude/rules/*.md" in content
    assert "never read `.env`" in content
