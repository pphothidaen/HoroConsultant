"""Tests for Claude Code command governance artifacts."""

from __future__ import annotations

import json
import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path

import yaml
import pytest


ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
HOOK = CLAUDE_DIR / "hooks" / "pre_tool_guard.py"
ORCHESTRATOR_HOOK = CLAUDE_DIR / "hooks" / "orchestrator_only_guard.py"
ADAPTIVE_HOOK = CLAUDE_DIR / "hooks" / "adaptive_dispatch_guard.py"
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


def load_orchestrator_hook():
    """Load the hook for waiver-order regression coverage without executing it."""

    hook_dir = str(ORCHESTRATOR_HOOK.parent)
    sys.path.insert(0, hook_dir)
    try:
        spec = importlib.util.spec_from_file_location(
            "orchestrator_only_guard_regression", ORCHESTRATOR_HOOK
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(hook_dir)


def load_adaptive_hook():
    spec = importlib.util.spec_from_file_location("adaptive_dispatch_guard_regression", ADAPTIVE_HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_orchestrator_guard_blocks_invalid_execute_but_allows_planning_dry_run() -> None:
    config = ROOT / ".agents/config/multiagent_prompt_command.example.yaml"
    invalid_execute = (
        f"python3 scripts/multiagent_prompt_command.py --config {config} "
        "--role orchestrator_support --objective blocked --execute"
    )
    assert_denied(
        run_orchestrator_hook(
            {"tool_name": "Bash", "tool_input": {"command": invalid_execute}, "cwd": str(ROOT)},
            enabled=True,
        )
    )

    planning_dry_run = (
        f"python3 scripts/multiagent_prompt_command.py --config {config} "
        "--role orchestrator_support --objective plan --print-command"
    )
    assert run_orchestrator_hook(
        {"tool_name": "Bash", "tool_input": {"command": planning_dry_run}, "cwd": str(ROOT)},
        enabled=True,
    ) == {}


def test_orchestrator_guard_cannot_bypass_required_scheduling_snapshot() -> None:
    command = (
        "python3 scripts/multiagent_prompt_command.py --config "
        ".agents/config/multiagent_prompt_command.example.yaml "
        "--role orchestrator_support --objective blocked "
        "--decision project/tests/artifacts/priority_scheduling/decision_priority_003.json "
        "--execute"
    )

    assert_denied(
        run_orchestrator_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)},
            enabled=True,
        )
    )


def test_orchestrator_guard_denies_direct_codex_and_agy_child_execution() -> None:
    for direct_child in (
        "codex exec -C . --skip-git-repo-check -",
        "agy --mode plan --print --input-format text --output-format json",
    ):
        assert_denied(
            run_orchestrator_hook(
                {"tool_name": "Bash", "tool_input": {"command": direct_child}},
                enabled=True,
            )
        )


def test_dispatcher_composition_redirection_control_and_prefixes_are_denied(monkeypatch) -> None:
    guard = load_adaptive_hook()
    monkeypatch.setattr(guard, "_validate", lambda argv, event: None)
    base = "python3 scripts/multiagent_prompt_command.py --config routes.yaml --execute"

    for command in (
        f"{base} > receipt.json",
        f"{base} && true",
        f"{base} | tee receipt.json",
        f"env {base}",
    ):
        invocations, dispatch_only = guard._execute_argvs(command)
        assert invocations
        assert dispatch_only is False
        with pytest.raises(ValueError, match="standalone"):
            guard.enforce_adaptive_dispatch({"tool_input": {"command": command}})


def test_orchestrator_guard_denies_shell_indirection_and_direct_child_variants() -> None:
    unsafe_commands = (
        "$(codex exec -C . -)",
        "echo <(agy --mode plan --print)",
        "bash -c 'codex exec -C . -'",
        "CHILD=codex; $CHILD exec -C . -",
        "'codex' exec -C . -",
        "/usr/local/bin/agy --mode plan --print",
    )
    for command in unsafe_commands:
        assert_denied(
            run_orchestrator_hook(
                {"tool_name": "Bash", "tool_input": {"command": command}}, enabled=True
            )
        )

    assert run_orchestrator_hook(
        {"tool_name": "Bash", "tool_input": {"command": "printf safe"}}, enabled=True
    ) == {}


def test_strict_allowlist_denies_encoded_decode_pipe_and_nested_execution() -> None:
    for command in (
        "printf Y29kZXggZXhlYyAt | base64 -d | sh",
        "echo 'codex exec -' | base64 --decode | bash",
        "python3 -c 'import os; os.system(\"codex exec -\")'",
        "sh -c 'python3 scripts/multiagent_prompt_command.py --execute'",
    ):
        assert_denied(
            run_orchestrator_hook(
                {"tool_name": "Bash", "tool_input": {"command": command}}, enabled=True
            )
        )

    for command in ("pwd", "git status --porcelain", "git --no-pager diff --no-ext-diff --stat"):
        assert run_orchestrator_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}, enabled=True
        ) == {}


def test_recorded_waiver_cannot_bypass_adaptive_dispatch_validation(monkeypatch, capsys) -> None:
    """Waivers cover root work only; child dispatch still needs a decision."""

    hook = load_orchestrator_hook()
    monkeypatch.setenv("HORO_ORCHESTRATOR_ONLY", "1")
    monkeypatch.setattr(hook, "has_recorded_waiver", lambda: True)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": (
                            "python3 scripts/multiagent_prompt_command.py --config "
                            ".agents/config/multiagent_prompt_command.example.yaml "
                            "--role orchestrator_support --objective blocked --execute"
                        )
                    },
                    "cwd": str(ROOT),
                }
            )
        ),
    )

    with pytest.raises(SystemExit) as exited:
        hook.main()
    assert exited.value.code == 0
    assert_denied(json.loads(capsys.readouterr().out))


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


def test_critical_path_first_markers_reach_canonical_and_provider_surfaces() -> None:
    markers = (
        "GOV_CRITICAL_PATH_FIRST_V1",
        "CRITICAL_PATH_UNLOCK=<dependency-or-gate-id>",
        "SPECULATIVE_ATOMIC_TICKET=DENY",
        "BLOCKER_EVIDENCE_ONLY=<named-blocker-id>",
        "BLOCKER_EVIDENCE_MODE=READ_ONLY",
    )
    canonical_agent = json.loads(
        (ROOT / ".agents" / "agents" / "orchestrator" / "agent.json").read_text(
            encoding="utf-8"
        )
    )
    agy_agent = yaml.safe_load(
        (ROOT / ".antigravity" / "agents" / "orchestrator.agent").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {
        "canonical Rule 11": (
            ROOT / ".agents" / "rules" / "11-orchestrator-subagent-delegation.md"
        ).read_text(encoding="utf-8"),
        "canonical orchestrator skill": (
            ROOT / ".agents" / "skills" / "orchestrator-delegation" / "SKILL.md"
        ).read_text(encoding="utf-8"),
        "canonical orchestrator prompt": canonical_agent["system_prompt"],
        "Claude rule": (
            ROOT / ".claude" / "rules" / "orchestrator-subagents.md"
        ).read_text(encoding="utf-8"),
        "AGY rule": (
            ROOT / ".agy" / "rules" / "orchestrator-subagents.md"
        ).read_text(encoding="utf-8"),
        "AGY skill": (
            ROOT
            / ".antigravity"
            / "skills"
            / "orchestrator-delegation"
            / "SKILL.md"
        ).read_text(encoding="utf-8"),
        "AGY orchestrator prompt": agy_agent["system_prompt"],
        "Codex orchestrator prompt": (
            ROOT / ".codex" / "agents" / "orchestrator.toml"
        ).read_text(encoding="utf-8"),
    }

    for surface, content in surfaces.items():
        missing = [marker for marker in markers if marker not in content]
        assert not missing, f"{surface} missing critical-path markers: {missing}"


def test_protected_dispatch_requires_named_critical_path_unlock(
    monkeypatch, capsys
) -> None:
    hook = load_orchestrator_hook()
    monkeypatch.setenv("HORO_ORCHESTRATOR_ONLY", "1")
    monkeypatch.setattr(hook, "enforce_adaptive_dispatch", lambda _event: True)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": (
                            "python3 scripts/multiagent_prompt_command.py --config routes.yaml "
                            "--role orchestrator_support --objective bounded --execute"
                        )
                    },
                }
            )
        ),
    )

    with pytest.raises(SystemExit) as exited:
        hook.main()
    assert exited.value.code == 0
    denied = json.loads(capsys.readouterr().out)
    assert_denied(denied)
    reason = denied["hookSpecificOutput"]["permissionDecisionReason"]
    assert "DEPENDENCY_UNLOCK_EVIDENCE_REQUIRED" in reason

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": (
                            "python3 scripts/multiagent_prompt_command.py --config routes.yaml "
                            "--role orchestrator_support "
                            "--objective CRITICAL_PATH_UNLOCK=GATE-053C --execute"
                        )
                    },
                }
            )
        ),
    )

    assert hook.main() == 0
    assert capsys.readouterr().out == ""
