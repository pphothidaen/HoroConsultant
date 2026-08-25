from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
import subprocess

import pytest
import yaml

from scripts import multiagent_prompt_command as command


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "routes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "accounts": {
                    "codex1": {
                        "cli": "codex",
                        "command": "codex",
                        "home_env": "CODEX_HOME",
                        "home_path": "${HOME}/.codex-one",
                    },
                    "codex2": {"cli": "codex", "command": "/opt/bin/codex"},
                    "agy1": {
                        "cli": "agy",
                        "command": "agy",
                        "home_env": "AGY_HOME",
                        "home_path": "${HOME}/.agy-one",
                    },
                    "agy2": {"cli": "agy", "command": "agy-two"},
                },
                "roles": {
                    "developer": {
                        "alias": "codex1",
                        "cli": "codex",
                        "model": "gpt-5.6-luna",
                        "effort": "medium",
                        "sandbox": "workspace-write",
                    },
                    "researcher": {
                        "alias": "agy1",
                        "cli": "agy",
                        "model": "gemini-pro",
                        "mode": "plan",
                        "sandbox": True,
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _valid_result_stdout() -> str:
    return json.dumps(
        {
            "status": "DONE",
            "scope_owned": "tests only",
            "evidence": {"commands": [], "outcomes": [], "artifacts": []},
            "findings": "none",
            "changed_files": "none",
            "residual_risk": "none",
            "recommended_next_action": "none",
        }
    )


def test_codex_defaults_produce_exact_argv_and_account_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", "/Users/tester")
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    prompt = command.render_prompt(objective="Implement T-1")
    invocation = command.build_invocation(route, prompt, tmp_path)

    assert invocation.argv == (
        "codex",
        "exec",
        "-C",
        str(tmp_path),
        "-s",
        "workspace-write",
        "-m",
        "gpt-5.6-luna",
        "-c",
        'model_reasoning_effort="medium"',
        "-",
    )
    assert invocation.prompt_stdin == prompt
    assert prompt not in invocation.argv
    assert invocation.env_overrides == {"CODEX_HOME": "/Users/tester/.codex-one"}


def test_orchestrator_override_uses_registered_alias(tmp_path):
    config = command.load_config(_config(tmp_path))
    route = command.resolve_route(
        config,
        "developer",
        alias_override="codex2",
        cli_override="codex",
        model_override="gpt-5.6-sol",
        effort_override="high",
    )
    assert route.alias == "codex2"
    assert route.command == "/opt/bin/codex"
    assert route.model == "gpt-5.6-sol"
    assert route.effort == "high"


def test_agy_argv_preserves_unicode_newline_and_shell_characters(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", "/Users/tester")
    route = command.resolve_route(command.load_config(_config(tmp_path)), "researcher")
    objective = "ตรวจสอบบรรทัดแรก\n$(touch /tmp/not-run); 'quoted'"
    prompt = command.render_prompt(objective=objective, ownership="read only")
    invocation = command.build_invocation(route, prompt, tmp_path)

    assert invocation.argv == (
        "agy",
        "--mode",
        "plan",
        "--sandbox",
        "--model",
        "gemini-pro",
        "--print",
        "--input-format",
        "text",
        "--output-format",
        "json",
    )
    assert invocation.prompt_stdin == prompt
    assert all("$(touch /tmp/not-run)" not in arg for arg in invocation.argv)
    assert invocation.env_overrides == {"AGY_HOME": "/Users/tester/.agy-one"}


def test_prompt_has_ownership_coordination_and_result_contract():
    prompt = command.render_prompt(
        objective="Fix release gate",
        ownership="scripts/gate.py only",
        boundaries="No deployment",
        evidence="pytest output",
        stop_condition="Stop on missing fixture",
    )
    assert "Ownership: scripts/gate.py only" in prompt
    assert command.COORDINATION_SENTENCE in prompt
    assert "status: DONE | BLOCKED | NEEDS_HITL" in prompt
    assert "scope_owned:" in prompt
    assert "recommended_next_action:" in prompt


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("mode", "default", "unsupported AGY mode"),
        ("effort", "xhigh", "unsupported AGY reasoning effort"),
        ("sandbox", "workspace-write", "AGY sandbox must be true or false"),
    ],
)
def test_agy_options_are_validated_against_installed_cli_contract(
    tmp_path, field, value, message
):
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["roles"]["researcher"][field] = value
    with pytest.raises(command.ConfigurationError, match=message):
        command.resolve_route(config, "researcher")


@pytest.mark.parametrize(
    ("role", "alias", "cli", "message"),
    [
        ("missing", None, None, "unknown role"),
        ("developer", "unknown", None, "unknown account alias"),
        ("developer", None, "agy", "registered for codex"),
    ],
)
def test_missing_role_unknown_alias_and_invalid_cli_are_rejected(
    tmp_path, role, alias, cli, message
):
    with pytest.raises(command.ConfigurationError, match=message):
        command.resolve_route(
            command.load_config(_config(tmp_path)),
            role,
            alias_override=alias,
            cli_override=cli,
        )


def test_dry_run_never_starts_subprocess(tmp_path, monkeypatch, capsys):
    config_path = _config(tmp_path)
    started = False

    def fail_if_started(*args, **kwargs):
        nonlocal started
        started = True
        raise AssertionError("subprocess must not run")

    monkeypatch.setattr(command.subprocess, "run", fail_if_started)
    result = command.main(
        [
            "--config",
            str(config_path),
            "--role",
            "developer",
            "--objective",
            "TOP-SECRET malicious $(touch /tmp/not-run)",
            "--project-dir",
            str(tmp_path),
        ]
    )
    assert result == 0
    assert started is False
    output = capsys.readouterr().out
    assert "rendered-route-not-execution-proof" in output
    assert "Dry-run only" in output
    assert "TOP-SECRET" not in output
    assert "$(touch /tmp/not-run)" not in output
    assert ".codex-one" not in output
    assert "CODEX_HOME" in output
    assert "<PROMPT_STDIN>" in output


def test_execute_uses_argv_cwd_and_process_local_env(tmp_path, monkeypatch):
    config_path = _config(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex-one").mkdir()
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    result = command.main(
        [
            "--config",
            str(config_path),
            "--role",
            "developer",
            "--objective",
            "Execute safely",
            "--project-dir",
            str(tmp_path),
            "--execute",
        ]
    )
    assert result == 0
    assert observed["argv"][0:4] == ["codex", "exec", "-C", str(tmp_path)]
    assert observed["cwd"] == str(tmp_path)
    assert observed["shell"] is False
    assert observed["env"]["CODEX_HOME"] == str(tmp_path / ".codex-one")
    assert observed["argv"][-1] == "-"
    assert "Execute safely" not in observed["argv"]
    assert "Objective: Execute safely" in observed["input"]


def test_execute_transports_malicious_unicode_prompt_byte_for_byte_on_stdin(
    tmp_path, monkeypatch, capsys
):
    config_path = _config(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex-one").mkdir()
    objective = "ลับมาก\n$(touch /tmp/must-not-run); 'quoted'"
    expected_prompt = command.render_prompt(objective=objective)
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    result = command.main(
        [
            "--config",
            str(config_path),
            "--role",
            "developer",
            "--objective",
            objective,
            "--project-dir",
            str(tmp_path),
            "--execute",
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert observed["input"] == expected_prompt
    assert all(objective not in argument for argument in observed["argv"])
    assert "ลับมาก" not in output
    assert "$(touch /tmp/must-not-run)" not in output
    assert str(tmp_path / ".codex-one") not in output
    assert observed["shell"] is False


def test_cli_dry_run_prints_valid_json_route_before_status(tmp_path, capsys):
    result = command.main(
        [
            "--config",
            str(_config(tmp_path)),
            "--role",
            "researcher",
            "--objective",
            "Thai: ตรวจสอบ",
            "--print-command",
        ]
    )
    assert result == 0
    output = capsys.readouterr().out
    payload_text = output.split("\n[OK]", 1)[0]
    payload = json.loads(payload_text)
    assert payload["alias"] == "agy1"
    assert payload["status"] == "rendered-route-not-execution-proof"


def test_repository_example_resolves_every_role(monkeypatch):
    monkeypatch.setenv("HOME", "/Users/tester")
    config = command.load_config(
        Path(".agents/config/multiagent_prompt_command.example.yaml")
    )
    routes = {role: command.resolve_route(config, role) for role in config["roles"]}
    assert {route.cli for route in routes.values()} == {"codex", "agy"}
    assert {route.alias for route in routes.values()} == {
        "codex1",
        "codex2",
        "agy1",
        "agy2",
    }


def test_execute_reports_missing_executable_without_traceback(tmp_path, monkeypatch, capsys):
    config_path = _config(tmp_path)
    monkeypatch.setattr(
        command,
        "execute_invocation",
        lambda invocation: (_ for _ in ()).throw(FileNotFoundError("not installed")),
    )
    result = command.main(
        [
            "--config",
            str(config_path),
            "--role",
            "developer",
            "--objective",
            "Run",
            "--execute",
        ]
    )
    assert result == 127
    assert "Unable to start configured codex executable" in capsys.readouterr().err


def test_missing_project_directory_is_rejected(tmp_path):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    with pytest.raises(command.ConfigurationError, match="project_dir"):
        command.build_invocation(route, "prompt", tmp_path / "missing")


def test_execute_preflight_requires_configured_home_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(route, "prompt", tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    with pytest.raises(command.ConfigurationError, match="CODEX_HOME"):
        command.validate_execution_preflight(invocation)


@pytest.mark.parametrize(
    "home_path",
    ["~/.codex", "$CODEX_HOME/other", "relative/path", "${TOKEN}/bad"],
)
def test_unsafe_home_expansion_is_rejected(tmp_path, home_path):
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["accounts"]["codex1"]["home_path"] = home_path
    with pytest.raises(command.ConfigurationError):
        command.resolve_route(config, "developer")


@pytest.mark.parametrize(
    ("alias", "cli", "command_name"),
    [
        ("codex1", "codex", "codex"),
        ("codex2", "codex", "/opt/bin/codex"),
        ("agy1", "agy", "agy"),
        ("agy2", "agy", "agy-two"),
    ],
)
def test_all_registered_accounts_resolve_to_their_own_command(
    tmp_path, alias, cli, command_name
):
    route = command.resolve_route(
        command.load_config(_config(tmp_path)),
        "developer" if cli == "codex" else "researcher",
        alias_override=alias,
    )
    assert (route.alias, route.cli, route.command) == (alias, cli, command_name)


def test_prompt_is_stdin_only_even_when_objective_contains_cli_tokens(tmp_path):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    prompt = command.render_prompt(objective="--model evil; $(touch pwned)")
    invocation = command.build_invocation(route, prompt, tmp_path)

    assert invocation.prompt_stdin == prompt
    assert "--model evil" not in invocation.argv
    assert "pwned" not in " ".join(invocation.argv)
    assert invocation.argv[-1] == "-"


def test_dry_run_normalizes_route_evidence_without_prompt_or_home_leak(
    tmp_path, capsys
):
    result = command.main(
        [
            "--config",
            str(_config(tmp_path)),
            "--role",
            "developer",
            "--objective",
            "private objective",
            "--project-dir",
            str(tmp_path),
            "--print-command",
        ]
    )
    assert result == 0
    payload = json.loads(capsys.readouterr().out.split("\n[OK]", 1)[0])
    assert payload == {
        "status": "rendered-route-not-execution-proof",
        "role": "developer",
        "alias": "codex1",
        "cli": "codex",
        "cwd": "<PROJECT_DIR>",
        "env_keys": ["CODEX_HOME"],
        "argv": [
            "codex",
            "exec",
            "-C",
            "<PROJECT_DIR>",
            "-s",
            "workspace-write",
            "-m",
            "gpt-5.6-luna",
            "-c",
            'model_reasoning_effort="medium"',
            "-",
            "<PROMPT_STDIN>",
        ],
        "command": shlex.join(
            [
                "codex",
                "exec",
                "-C",
                "<PROJECT_DIR>",
                "-s",
                "workspace-write",
                "-m",
                "gpt-5.6-luna",
                "-c",
                'model_reasoning_effort="medium"',
                "-",
                "<PROMPT_STDIN>",
            ]
        ),
    }


def test_human_review_states_are_explicit_in_shared_result_contract():
    prompt = command.render_prompt(objective="Review ambiguous interpretation")
    for state in ("DONE", "BLOCKED", "NEEDS_HITL"):
        assert state in prompt
    assert "recommended_next_action:" in prompt
    assert "changed_files:" in prompt
    assert "residual_risk:" in prompt


def test_duplicate_dispatch_is_one_subprocess_with_account_session_evidence(
    tmp_path, monkeypatch
):
    config_path = _config(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex-one").mkdir()
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs["cwd"], kwargs["env"]["CODEX_HOME"], kwargs["input"]))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    args = [
        "--config",
        str(config_path),
        "--role",
        "developer",
        "--objective",
        "one dispatch",
        "--project-dir",
        str(tmp_path),
        "--execute",
    ]
    assert command.main(args) == 0
    assert len(calls) == 1
    argv, cwd, home, stdin = calls[0]
    assert argv[0] == "codex"
    assert cwd == str(tmp_path)
    assert home == str(tmp_path / ".codex-one")
    assert stdin.startswith("You are a sub-agent")


def test_nonzero_exit_is_normalized_and_reported(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        command,
        "execute_invocation",
        lambda invocation: subprocess.CompletedProcess(invocation.argv, 23),
    )
    result = command.main(
        [
            "--config",
            str(_config(tmp_path)),
            "--role",
            "developer",
            "--objective",
            "fails",
            "--project-dir",
            str(tmp_path),
            "--execute",
        ]
    )
    assert result == 23
    assert "exited with code 23" in capsys.readouterr().err


def test_empty_success_stdout_requires_missing_result_evidence_not_done():
    result = command.normalize_result("", returncode=0)

    assert result["status"] == "BLOCKED"
    assert result["status"] != "DONE"
    assert result["evidence"]["outcomes"] == [
        "subprocess exit code: 0",
        "sub-agent returned empty stdout; result contract was not emitted",
    ]
    assert result["findings"] == [
        "No canonical sub-agent result was available to verify."
    ]


def test_timeout_from_account_process_is_not_silently_normalized(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex-one").mkdir()
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(route, "prompt", tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")

    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(kwargs.get("args", args[0]), timeout=1)

    monkeypatch.setattr(command.subprocess, "run", timed_out)
    with pytest.raises(subprocess.TimeoutExpired):
        command.execute_invocation(invocation)


def test_unavailable_cli_is_rejected_before_account_process_start(tmp_path, monkeypatch):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(route, "prompt", tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: None)
    with pytest.raises(command.ConfigurationError, match="executable is unavailable"):
        command.execute_invocation(invocation)


def test_real_agy_argument_order_is_verified_with_fake_executable(tmp_path, monkeypatch):
    capture = tmp_path / "agy-argv.txt"
    fake = tmp_path / "agy-fake"
    fake.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CAPTURE\"\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | 0o100)
    monkeypatch.setenv("CAPTURE", str(capture))
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["accounts"]["agy2"]["command"] = str(fake)
    config["roles"]["researcher"].update(
        {"alias": "agy2", "model": "gemini-pro", "mode": "plan", "sandbox": True, "effort": "medium"}
    )
    route = command.resolve_route(config, "researcher")
    prompt = command.render_prompt(objective="fake AGY invocation")
    invocation = command.build_invocation(route, prompt, tmp_path)

    result = command.execute_invocation(invocation)

    assert result.returncode == 0
    assert capture.read_text(encoding="utf-8").splitlines() == [
        "--mode",
        "plan",
        "--sandbox",
        "--model",
        "gemini-pro",
        "--effort",
        "medium",
        "--print",
        "--input-format",
        "text",
        "--output-format",
        "json",
    ]


@pytest.mark.parametrize(
    "policy_path",
    [
        Path(".agents/rules/17-multi-account-agent-orchestration.md"),
        Path(".agents/skills/multi-account-agent-orchestration/SKILL.md"),
    ],
)
def test_terminal_dispatch_policy_requires_a_governed_account_alias(policy_path):
    """Governance must make the terminal routing choice explicit and finite."""

    policy = policy_path.read_text(encoding="utf-8").lower()

    assert "bounded terminal dispatch" in policy
    assert "explicitly select" in policy
    for alias in ("codex1", "codex2", "agy1", "agy2"):
        assert alias in policy


def test_config_cannot_register_an_alias_outside_the_governed_account_set(tmp_path):
    """A YAML label must not extend the approved terminal account allowlist."""

    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["accounts"]["rogue"] = {"cli": "codex", "command": "codex"}
    config["roles"]["developer"]["alias"] = "rogue"

    with pytest.raises(command.ConfigurationError, match="approved account alias"):
        command.resolve_route(config, "developer")


def test_unavailable_selected_alias_returns_canonical_blocked_result(
    tmp_path, monkeypatch, capsys
):
    """A missing account executable is a blocked dispatch, never execution proof."""

    config_path = _config(tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: None)

    result = command.main(
        [
            "--config",
            str(config_path),
            "--role",
            "developer",
            "--objective",
            "Run bounded terminal task",
            "--project-dir",
            str(tmp_path),
            "--execute",
        ]
    )

    output = capsys.readouterr()
    assert result != 0
    assert '"status": "BLOCKED"' in output.out
    assert "rendered-route-not-execution-proof" in output.out
    assert "Unable to start configured codex executable" in output.err


def test_completed_process_evidence_is_emitted_separately_from_route_label(
    tmp_path, monkeypatch, capsys
):
    """A configured alias is routing intent; process evidence must be explicit."""

    config_path = _config(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex-one").mkdir()

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv, 0, stdout=_valid_result_stdout(), stderr="child-session=safe-123"
        )

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    assert (
        command.main(
            [
                "--config",
                str(config_path),
                "--role",
                "developer",
                "--objective",
                "Run bounded terminal task",
                "--project-dir",
                str(tmp_path),
                "--execute",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert '"alias": "codex1"' in output
    assert '"execution_evidence"' in output
    assert '"source": "actual-subprocess-result"' in output
    assert '"returncode": 0' in output
