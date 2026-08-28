from __future__ import annotations

import json
import multiprocessing
import os
import shlex
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command

ORIGINAL_CLAIM_STORE = command._secure_claim_directory


@pytest.fixture(autouse=True)
def _isolated_claim_store(tmp_path, monkeypatch):
    """Every executable fixture uses a writable, explicit in-project state root."""

    monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: tmp_path / "claim-store")


@pytest.fixture(autouse=True)
def _isolated_account_homes(tmp_path, monkeypatch):
    """Create only owned 0700 account-home directories; never auth material."""

    monkeypatch.setenv("HOME", str(tmp_path))
    for name in (".codex-one", ".agy-one", ".agy-two"):
        home = tmp_path / name
        home.mkdir(mode=0o700, exist_ok=True)
        home.chmod(0o700)


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "routes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "runtime": {
                    "approved_for_execution": True,
                    "protocol_version": 2,
                },
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
                    "agy2": {
                        "cli": "agy", "command": "agy-two",
                        "home_env": "AGY_HOME", "home_path": "${HOME}/.agy-two",
                    },
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


def _policy() -> dict[str, object]:
    return command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")


def _decision(**overrides: object) -> dict[str, object]:
    """Return a small, valid v1 decision for the local codex1 test route."""

    decision: dict[str, object] = {
        "schema_version": 1,
        "ticket": "TICKET-ADAPT-TEST",
        "phase": "implementation",
        "scope_rank": 1,
        "complexity_rank": 1,
        "risk_rank": 1,
        "ambiguity_rank": 1,
        "evidence_burden_rank": 1,
        "quota_band": "healthy",
        "work_mode": "mutation",
        "selected_alias": "codex1",
        "selected_model": "gpt-5.6-luna",
        "selected_effort": "medium",
        "rationale": "bounded regression coverage",
        "policy_version": _policy()["policy_version"],
        "planning_to_medium_confirmed": True,
        "hitl_approved": False,
    }
    decision.update(overrides)
    return decision


def _decision_path(tmp_path: Path, **overrides: object) -> Path:
    path = tmp_path / "dispatch-decision.json"
    path.write_text(json.dumps(_decision(**overrides)), encoding="utf-8")
    return path


def _scheduling_snapshot(
    *,
    ticket_id: str = "TICKET-ADAPT-TEST",
    owner: str = "developer",
    ownership: str = command.DEFAULT_OWNERSHIP,
) -> dict[str, object]:
    """Return the smallest executable Rule 11 checkpoint for a test lane."""

    return {
        "schema_version": 1,
        "tickets": [
            {
                "ticket_id": ticket_id,
                "severity": "HIGH",
                "work_effort": "M",
                "status": "READY",
                "dependencies": [],
                "blockers": [],
                "owner": owner,
                "ownership": [ownership],
                "quota_passed": True,
                "hitl_passed": True,
                "rule18_decision_valid": True,
            }
        ],
        "reservations": [],
    }


def _scheduling_snapshot_path(tmp_path: Path, **overrides: object) -> Path:
    path = tmp_path / "scheduling-snapshot.json"
    path.write_text(json.dumps(_scheduling_snapshot(**overrides)), encoding="utf-8")
    return path


def _execute_args(config_path: Path, decision_path: Path, tmp_path: Path) -> list[str]:
    scheduling_snapshot_path = _scheduling_snapshot_path(tmp_path)
    return [
        "--config",
        str(config_path),
        "--role",
        "developer",
        "--objective",
        "Execute safely",
        "--project-dir",
        str(tmp_path),
        "--decision",
        str(decision_path),
        "--policy",
        str(ROOT / ".agents/config/multiagent_model_policy.yaml"),
        "--scheduling-snapshot",
        str(scheduling_snapshot_path),
        "--execute",
    ]


def _valid_result_stdout() -> str:
    return _codex_stdout(_work_result())


def _work_result(status: str = "DONE") -> dict[str, object]:
    return {
        "status": status,
        "scope_owned": ["tests only"],
        "evidence": {
            "commands": ["python3 -m pytest -q tests/test_multiagent_prompt_command.py"],
            "outcomes": ["focused contract check completed"],
            "artifacts": [],
        },
        "findings": ["provider-native v2 result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "retain the receipt",
    }


def _jsonl(*events: dict[str, object]) -> str:
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _codex_stdout(result: dict[str, object], thread_id: str = "thread-safe-1") -> str:
    return _jsonl(
        {"type": "thread.started", "thread_id": thread_id},
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(result, separators=(",", ":")),
            },
        },
        {"type": "turn.completed"},
    )


def _agy_stdout(result: dict[str, object], conversation_id: str = "agy-safe-1") -> str:
    """Synthetic official AGY stream-json output; no external provider data."""

    return _jsonl(
        {"event": "init", "conversation_id": conversation_id, "init": {}},
        {
            "event": "step_update",
            "step_update": {"conversation_id": conversation_id, "state": "ACTIVE"},
        },
        {
            "event": "result",
            "result": {
                "conversation_id": conversation_id,
                "status": "SUCCESS",
                "structured_output": result,
            },
        },
    )


def _read_only_codex_invocation(tmp_path: Path, *, attempt_id: int = 3):
    config_path = _config(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["roles"]["developer"]["sandbox"] = "read-only"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    route = command.resolve_route(config, "developer")
    decision = _decision(work_mode="read_only")
    return command.build_invocation(
        route,
        command.render_prompt(objective="Read-only v2 verification"),
        tmp_path,
        decision=decision,
        model_policy=_policy(),
        attempt_id=attempt_id,
        objective="Read-only v2 verification",
        ownership="repository review only",
        runtime_config_path=config_path,
        runtime_config_approved=True,
        scheduling_snapshot=_scheduling_snapshot(ownership="repository review only"),
        claim_store_override=str(tmp_path / "claim-store"),
    )


def _hold_cross_process_claim(invocation, claim_root: str, ready, release, outcome) -> None:
    """Acquire one real claim in a child process until the parent checks it."""

    claim_dir = Path(claim_root)
    claim_dir.mkdir(mode=0o700)
    command._secure_claim_directory = lambda _invocation: claim_dir
    try:
        command._acquire_dispatch_claim(invocation)
    except Exception as exc:  # pragma: no cover - surfaced through outcome
        outcome.put(("error", type(exc).__name__, getattr(exc, "code", None)))
    else:
        outcome.put(("acquired",))
        ready.set()
        release.wait(timeout=10)


def _active_claimed_process(tmp_path: Path, monkeypatch, invocation, *, returncode: int = 0):
    """Exercise the real acquire/lock/spawn path and return its live claim."""

    invocation = replace(
        invocation,
        claim_store_override=str(tmp_path / "claim-store"),
    )
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, returncode, stdout=_valid_result_stdout(), stderr=""
        ),
    )
    return invocation, command._execute_invocation_locked(invocation)


def _finalized_claimed_process(tmp_path: Path, monkeypatch, invocation, *, returncode: int = 0):
    """Return open persisted-completed proof for receipt mutation tests."""

    invocation, result = _active_claimed_process(
        tmp_path, monkeypatch, invocation, returncode=returncode
    )
    provider_result = command.parse_provider_result(invocation, result.stdout)
    claim = result._dispatch_claim  # type: ignore[attr-defined]
    result._dispatch_claim_sha256 = command._finalize_dispatch_claim(  # type: ignore[attr-defined]
        claim, "completed", result, provider_result
    )
    return invocation, result, provider_result


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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(command.shutil, "which", lambda executable: f"/usr/bin/{executable}")
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    result = command.main(_execute_args(config_path, decision_path, tmp_path))
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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(command.shutil, "which", lambda executable: f"/usr/bin/{executable}")
    objective = "ลับมาก\n$(touch /tmp/must-not-run); 'quoted'"
    observed = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = objective
    result = command.main(args)
    output = capsys.readouterr().out
    assert result == 0
    assert observed["input"].startswith(command.render_prompt(objective=objective))
    assert "Dispatch governance evidence" in observed["input"]
    assert all(objective not in argument for argument in observed["argv"])
    completed_text = "{" + output.split("\n{", 1)[1].split("\n[OK]", 1)[0]
    completed = json.loads(completed_text)
    assert completed["execution_receipt"]["objective"] == objective
    assert completed["work_result"] == _work_result()
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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setattr(
        command,
        "execute_invocation",
        lambda invocation: (_ for _ in ()).throw(FileNotFoundError("not installed")),
    )
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = "Run"
    result = command.main(args)
    assert result == 127
    assert "Unable to start configured codex executable" in capsys.readouterr().err


def test_missing_project_directory_is_rejected(tmp_path):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    with pytest.raises(command.ConfigurationError, match="project_dir"):
        command.build_invocation(route, "prompt", tmp_path / "missing")


def test_execute_preflight_requires_configured_home_directory(tmp_path, monkeypatch):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(
        route, "prompt", tmp_path, decision=_decision(), model_policy=_policy()
    )
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    missing = replace(route, home_path=str(tmp_path / "missing-home"))
    with pytest.raises(command.ConfigurationError, match="ACCOUNT_HOME_INVALID"):
        command.validate_execution_preflight(replace(invocation, route=missing))


def test_safe_account_home_requires_no_marker_or_credential_files(tmp_path, monkeypatch):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(
        route, "prompt", tmp_path, decision=_decision(), model_policy=_policy()
    )
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    assert list((tmp_path / ".codex-one").iterdir()) == []
    command.validate_execution_preflight(invocation)


@pytest.mark.parametrize("shape", ["final_symlink", "intermediate_symlink", "not_directory"])
def test_account_home_rejects_symlinked_or_nondirectory_paths(tmp_path, monkeypatch, shape):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    target = tmp_path / "safe-target"
    target.mkdir(mode=0o700)
    target.chmod(0o700)
    if shape == "final_symlink":
        home = tmp_path / "final-link"
        home.symlink_to(target, target_is_directory=True)
    elif shape == "intermediate_symlink":
        intermediate = tmp_path / "intermediate-link"
        intermediate.symlink_to(tmp_path, target_is_directory=True)
        home = intermediate / "safe-target"
    else:
        home = tmp_path / "not-a-directory"
        home.write_text("safe", encoding="ascii")
        home.chmod(0o600)
    invocation = command.build_invocation(route, "prompt", tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    with pytest.raises(command.ConfigurationError) as exc:
        command.validate_execution_preflight(replace(invocation, route=replace(route, home_path=str(home))))
    assert str(exc.value) == "ACCOUNT_HOME_INVALID"
    assert str(exc.value).isascii()


def test_account_home_rejects_unsafe_mode_wrong_owner_and_inode_race(tmp_path, monkeypatch):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(route, "prompt", tmp_path)
    home = tmp_path / ".codex-one"
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    home.chmod(0o722)
    with pytest.raises(command.ConfigurationError, match="ACCOUNT_HOME_INVALID"):
        command.validate_execution_preflight(invocation)
    home.chmod(0o700)

    original_fstat = command.os.fstat

    def foreign_owner(descriptor):
        value = original_fstat(descriptor)
        if (value.st_dev, value.st_ino) == (home.stat().st_dev, home.stat().st_ino):
            fields = list(value)
            fields[4] = value.st_uid + 1
            return os.stat_result(fields)
        return value

    monkeypatch.setattr(command.os, "fstat", foreign_owner)
    with pytest.raises(command.ConfigurationError, match="ACCOUNT_HOME_INVALID"):
        command.validate_execution_preflight(invocation)
    monkeypatch.setattr(command.os, "fstat", original_fstat)

    descriptor, identity = command._open_isolated_account_home(invocation)
    other = tmp_path / ".agy-one"
    other_fd = os.open(other, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    other_stat = os.fstat(other_fd)
    monkeypatch.setattr(
        command, "_open_account_home_path",
        lambda _path: (other_fd, (other_stat.st_dev, other_stat.st_ino)),
    )
    try:
        with pytest.raises(command.ConfigurationError, match="ACCOUNT_HOME_INVALID"):
            command._verify_isolated_account_home(invocation, descriptor, identity)
    finally:
        os.close(descriptor)


def test_missing_home_path_is_execute_only_failure_but_dry_run_still_renders(tmp_path, monkeypatch, capsys):
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["accounts"]["codex1"].pop("home_env")
    config["accounts"]["codex1"].pop("home_path")
    path = tmp_path / "missing-home-routes.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    decision = _decision_path(tmp_path)
    snapshot = _scheduling_snapshot_path(tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    assert command.main([
        "--config", str(path), "--role", "developer", "--objective", "safe",
        "--project-dir", str(tmp_path), "--decision", str(decision),
        "--policy", str(ROOT / ".agents/config/multiagent_model_policy.yaml"),
        "--scheduling-snapshot", str(snapshot), "--execute",
    ]) == 127
    assert capsys.readouterr().err == "[ERROR] Unable to start configured codex executable.\n"
    assert command.main([
        "--config", str(path), "--role", "developer", "--objective", "safe",
        "--project-dir", str(tmp_path), "--print-command",
    ]) == 0
    assert "rendered-route-not-execution-proof" in capsys.readouterr().out


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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(command.shutil, "which", lambda executable: f"/usr/bin/{executable}")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs["cwd"], kwargs["env"]["CODEX_HOME"], kwargs["input"]))
        return subprocess.CompletedProcess(
            argv, 0, stdout=_valid_result_stdout(), stderr=""
        )

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = "one dispatch"
    assert command.main(args) == 0
    assert len(calls) == 1
    argv, cwd, home, stdin = calls[0]
    assert argv[0] == "codex"
    assert cwd == str(tmp_path)
    assert home == str(tmp_path / ".codex-one")
    assert stdin.startswith("You are a sub-agent")


def test_nonzero_exit_is_normalized_and_reported(tmp_path, monkeypatch, capsys):
    typed_failure = _codex_stdout(_work_result("BLOCKED"))
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 23, stdout=typed_failure, stderr="safe failure"
        ),
    )
    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = "fails"
    result = command.main(args)
    assert result == 23
    assert "exited with code 23" in capsys.readouterr().err


def test_native_auth_failure_remains_child_authority_and_public_streams_are_elided(
    tmp_path, monkeypatch, capsys
):
    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    args = _execute_args(config_path, decision_path, tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 1, _codex_stdout(_work_result("BLOCKED")), "native authentication denied"
        ),
    )
    assert command.main(args) == 1
    captured = capsys.readouterr()
    assert "native authentication denied" not in captured.out + captured.err
    assert "[ERROR] Sub-agent command exited with code 1." in captured.err


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
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(
        route,
        "prompt",
        tmp_path,
        decision=_decision(),
        model_policy=_policy(),
        runtime_config_path=_config(tmp_path),
        runtime_config_approved=True,
        scheduling_snapshot=_scheduling_snapshot(),
    )
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")

    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(kwargs.get("args", args[0]), timeout=1)

    monkeypatch.setattr(command.subprocess, "run", timed_out)
    with pytest.raises(subprocess.TimeoutExpired):
        command.execute_invocation(invocation)


def test_unavailable_cli_is_rejected_before_account_process_start(tmp_path, monkeypatch):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "developer")
    invocation = command.build_invocation(
        route,
        "prompt",
        tmp_path,
        decision=_decision(),
        model_policy=_policy(),
        scheduling_snapshot=_scheduling_snapshot(),
    )
    monkeypatch.setattr(command.shutil, "which", lambda executable: None)
    with pytest.raises(command.ConfigurationError, match="executable is unavailable"):
        command.execute_invocation(invocation)


@pytest.mark.parametrize("role", ["developer", "researcher"])
def test_all_configured_review_roles_accept_safe_empty_account_homes(tmp_path, monkeypatch, role):
    route = command.resolve_route(command.load_config(_config(tmp_path)), role)
    invocation = command.build_invocation(route, "prompt", tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/fake")
    command.validate_execution_preflight(invocation)


def test_real_agy_argument_order_is_verified_with_fake_executable(tmp_path, monkeypatch):
    capture = tmp_path / "agy-argv.txt"
    stdin_capture = tmp_path / "agy-stdin.json"
    fake = tmp_path / "agy-fake"
    terminal = _agy_stdout(_work_result())
    fake.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$@\" > \"$CAPTURE\"\n"
        "cat > \"$INPUT_CAPTURE\"\n"
        f"printf '%s' '{terminal}'\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | 0o100)
    monkeypatch.setenv("CAPTURE", str(capture))
    monkeypatch.setenv("INPUT_CAPTURE", str(stdin_capture))
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["accounts"]["agy2"]["command"] = str(fake)
    config["roles"]["researcher"].update(
        {
            "alias": "agy2",
            "model": "gemini-3.1-pro-high",
            "mode": "plan",
            "sandbox": True,
            "effort": "high",
        }
    )
    route = command.resolve_route(config, "researcher")
    prompt = command.render_prompt(objective="fake AGY invocation")
    invocation = command.build_invocation(
        route,
        prompt,
        tmp_path,
        decision=_decision(
            selected_alias="agy2",
            selected_model="gemini-3.1-pro-high",
            selected_effort="high",
            scope_rank=2,
        ),
        model_policy=_policy(),
        runtime_config_path=_config(tmp_path),
        runtime_config_approved=True,
        scheduling_snapshot=_scheduling_snapshot(owner="researcher"),
    )

    outcome = command.execute_invocation(invocation)

    assert outcome.process.returncode == 0
    assert outcome.process.stdout == "[PROVIDER_STDOUT_ELIDED]"
    assert outcome.completed["work_result"] == _work_result()
    captured_argv = capture.read_text(encoding="utf-8").splitlines()
    assert captured_argv[:-1] == [
        "--mode",
        "plan",
        "--sandbox",
        "--model",
        "gemini-3.1-pro-high",
        "--effort",
        "high",
        "--print",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--json-schema",
    ]
    assert Path(captured_argv[-1]).name == "work-result-v2.provider.json"
    assert "fake AGY invocation" not in captured_argv
    sent_event = json.loads(stdin_capture.read_text(encoding="utf-8"))
    assert sent_event == json.loads(invocation.prompt_stdin)
    assert set(sent_event) == {"event", "message"}
    assert sent_event["event"] == "user"
    assert set(sent_event["message"]) == {"content"}
    assert sent_event["message"]["content"].startswith(prompt)


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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setattr(command.shutil, "which", lambda executable: None)

    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = "Run bounded terminal task"
    result = command.main(args)

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
    decision_path = _decision_path(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(command.shutil, "which", lambda executable: f"/usr/bin/{executable}")

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv, 0, stdout=_valid_result_stdout(), stderr="child-session=safe-123"
        )

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    assert (
        command.main(_execute_args(config_path, decision_path, tmp_path))
        == 0
    )

    output = capsys.readouterr().out
    assert '"alias": "codex1"' in output
    assert '"execution_receipt"' in output
    assert '"adapter": "codex-jsonl-output-schema-v2"' in output
    assert '"exit_code": 0' in output
    assert '"work_result"' in output


def test_execute_rejects_missing_dispatch_decision_but_legacy_dry_run_warns(
    tmp_path, capsys
):
    config_path = _config(tmp_path)
    base = [
        "--config", str(config_path), "--role", "developer", "--objective", "legacy",
        "--project-dir", str(tmp_path),
    ]

    assert command.main(base) == 0
    dry_run = capsys.readouterr()
    assert "Legacy v1 dry-run" in dry_run.err
    assert "rendered-route-not-execution-proof" in dry_run.out

    assert command.main([*base, "--execute"]) == 2
    assert "DISPATCH_DECISION_INVALID" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"selected_model": "gpt-5.6-luna", "selected_effort": "max"},
            "unsupported model/effort combination",
        ),
        (
            {
                "scope_rank": 2,
                "selected_model": "gpt-5.6-luna",
                "selected_effort": "medium",
            },
            "below required floor",
        ),
    ],
)
def test_policy_rejects_unsupported_or_below_floor_profiles(overrides, message):
    with pytest.raises(command.DispatchDecisionError, match=message):
        command.validate_dispatch_decision(_decision(**overrides), _policy())


def test_cli_override_cannot_disagree_with_decision(tmp_path, capsys):
    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("--execute"):args.index("--execute")] = ["--model", "gpt-5.6-terra"]

    assert command.main(args) == 2
    assert "DISPATCH_DECISION_INVALID" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["risk_rank", "ambiguity_rank"])
@pytest.mark.parametrize("work_mode", ["mutation", "read_only"])
def test_critical_risk_or_ambiguity_requires_hitl_for_every_work_mode(field, work_mode):
    decision = _decision(
        work_mode=work_mode,
        selected_model="gpt-5.6-sol",
        selected_effort="high",
        **{field: 3},
    )

    with pytest.raises(command.DispatchDecisionError, match="critical risk or ambiguity") as exc:
        command.validate_dispatch_decision(decision, _policy())

    assert exc.value.status == "NEEDS_HITL"


@pytest.mark.parametrize("quota_band", ["below_10_percent", "unknown"])
def test_low_or_unknown_quota_blocks_broad_work(quota_band):
    decision = _decision(scope_rank=2, quota_band=quota_band)

    with pytest.raises(command.DispatchDecisionError, match="quota"):
        command.validate_dispatch_decision(decision, _policy())


def test_execution_requires_root_medium_confirmation_but_valid_confirmation_passes():
    blocked = _decision(planning_to_medium_confirmed=False)
    with pytest.raises(command.DispatchDecisionError, match="root medium confirmation") as exc:
        command.validate_dispatch_decision(blocked, _policy())
    assert exc.value.status == "NEEDS_HITL"

    validated = command.validate_dispatch_decision(_decision(), _policy())
    assert validated.quality_floor == 1
    assert validated.decision["planning_to_medium_confirmed"] is True

    planning = _decision(
        phase="planning",
        scope_rank=3,
        complexity_rank=3,
        evidence_burden_rank=3,
        selected_model="gpt-5.6-sol",
        selected_effort="xhigh",
        planning_to_medium_confirmed=False,
    )
    assert command.validate_dispatch_decision(planning, _policy()).quality_floor == 3


def test_confirmed_medium_root_does_not_cap_independent_high_effort_child():
    decision = _decision(
        scope_rank=3,
        phase="implementation",
        selected_model="gpt-5.6-sol",
        selected_effort="high",
        planning_to_medium_confirmed=True,
    )

    validated = command.validate_dispatch_decision(decision, _policy())

    assert validated.quality_floor == 3
    assert validated.model_quality_rank == 3
    assert validated.decision["selected_effort"] == "high"


def test_dry_run_receipt_binds_policy_digest_model_and_effort(tmp_path, capsys):
    config_path = _config(tmp_path)
    decision = _decision()
    decision_path = _decision_path(tmp_path)
    args = _execute_args(config_path, decision_path, tmp_path)[:-1]

    assert command.main(args) == 0
    rendered_text = capsys.readouterr().out.split("\n[OK]", 1)[0]
    receipt = json.loads(rendered_text)["dispatch_receipt"]
    expected = command.validate_dispatch_decision(decision, _policy())
    assert receipt["policy_version"] == decision["policy_version"]
    assert receipt["decision_sha256"] == expected.digest
    assert receipt["model"] == decision["selected_model"]
    assert receipt["effort"] == decision["selected_effort"]


def test_provider_catalog_controls_pairs_not_static_role_metadata(tmp_path):
    config = command.load_config(_config(tmp_path))
    agy_route = command.resolve_route(
        config,
        "researcher",
        model_override="gemini-3.1-pro-high",
        effort_override="high",
    )
    agy_decision = _decision(
        selected_alias="agy1",
        selected_model="gemini-3.1-pro-high",
        selected_effort="high",
        scope_rank=2,
    )
    assert command.validate_dispatch_decision(agy_decision, _policy(), agy_route).model_quality_rank == 2

    with pytest.raises(command.DispatchDecisionError, match="unsupported model/effort combination"):
        command.validate_dispatch_decision(
            _decision(
                selected_model="gemini-3.1-pro-low", selected_effort="high"
            ),
            _policy(),
        )
    codex_route = command.resolve_route(config, "developer")
    with pytest.raises(command.DispatchDecisionError, match="provider"):
        command.validate_dispatch_decision(agy_decision, _policy(), codex_route)


@pytest.mark.parametrize("field", ["availability", "deprecated", "fallback_order"])
def test_capability_catalog_requires_runtime_status_and_fallback_metadata(field):
    """Catalog metadata is a fail-closed runtime contract, not documentation."""

    policy = deepcopy(_policy())
    del policy["models"]["gpt-5.6-luna"][field]

    with pytest.raises(command.ConfigurationError, match=field):
        command.validate_dispatch_decision(_decision(), policy)


def test_provider_schema_is_strict_codex_compatible_subset():
    schema = command._provider_compatible_work_result_schema(
        ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json"
    )

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == command.RESULT_FIELDS
    assert "oneOf" not in json.dumps(schema)
    for field in ("scope_owned", "findings", "changed_files"):
        assert schema["properties"][field]["type"] == "array"
        assert schema["properties"][field]["items"]["type"] == "string"
    assert schema["properties"]["scope_owned"]["items"]["minLength"] == 1
    evidence = schema["properties"]["evidence"]
    assert evidence["additionalProperties"] is False
    for field in ("commands", "outcomes", "artifacts"):
        assert evidence["properties"][field] == {
            "type": "array",
            "items": {"type": "string"},
        }


def test_valid_provider_native_codex_jsonl_and_agy_stream_json(tmp_path):
    codex_invocation = _read_only_codex_invocation(tmp_path)
    work_result = _work_result()
    codex = command.parse_provider_result(
        codex_invocation, _codex_stdout(work_result, "codex-session-3")
    )
    assert codex.work_result == work_result
    assert codex.adapter == "codex-jsonl-output-schema-v2"
    assert codex.process_or_session_id == "codex-session-3"

    agy_config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    agy_config["roles"]["researcher"].update(
        {
            "model": "gemini-3.1-pro-high",
            "effort": "high",
            "mode": "plan",
            "sandbox": True,
        }
    )
    agy_route = command.resolve_route(agy_config, "researcher")
    agy_invocation = command.build_invocation(
        agy_route,
        command.render_prompt(objective="AGY stream check"),
        tmp_path,
        decision=_decision(
            selected_alias="agy1",
            selected_model="gemini-3.1-pro-high",
            selected_effort="high",
            scope_rank=2,
        ),
        model_policy=_policy(),
        attempt_id=3,
        runtime_config_path=_config(tmp_path),
        runtime_config_approved=True,
    )
    agy = command.parse_provider_result(
        agy_invocation, _agy_stdout(work_result, "agy-session-3")
    )
    assert agy.work_result == work_result
    assert agy.adapter == "agy-stream-json-schema-v2"
    assert agy.process_or_session_id == "agy-session-3"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("scope_owned", ["ok", 7], r"scope_owned\[1\] must be a string"),
        ("findings", {"claim": "bad"}, "findings must be text or a list"),
        ("changed_files", [None], r"changed_files\[0\] must be a string"),
        ("evidence", [], "evidence must be a mapping"),
    ],
)
def test_work_result_rejects_non_string_arrays_and_evidence_types(
    field, value, message
):
    result = _work_result()
    result[field] = value
    with pytest.raises(command.ConfigurationError, match=message):
        command.normalize_result(result)


@pytest.mark.parametrize("evidence_field", ["commands", "outcomes", "artifacts"])
def test_work_result_evidence_requires_string_arrays(evidence_field):
    result = _work_result()
    result["evidence"][evidence_field] = "not-an-array"
    with pytest.raises(command.ConfigurationError, match=f"evidence.{evidence_field}"):
        command.normalize_result(result)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("bare prose", "malformed JSON"),
        (
            _jsonl(
                {"type": "thread.started", "thread_id": "one"},
                {"type": "turn.completed"},
                {"type": "turn.completed"},
            ),
            "unambiguous terminal",
        ),
        (
            _jsonl(
                {"type": "thread.started", "thread_id": "one"},
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "plain prose"},
                },
                {"type": "turn.completed"},
            ),
            "exactly one structured final",
        ),
        (
            _jsonl(
                {"type": "thread.started", "thread_id": "one"},
                {
                    "type": "item.completed",
                    "item": {
                        "type": "agent_message",
                        "text": json.dumps(_work_result()),
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "agent_message",
                        "text": json.dumps(_work_result()),
                    },
                },
                {"type": "turn.completed"},
            ),
            "exactly one structured final",
        ),
    ],
)
def test_codex_adapter_rejects_malformed_ambiguous_and_bare_prose(
    tmp_path, payload, message
):
    with pytest.raises(command.ConfigurationError, match=message):
        command.parse_provider_result(_read_only_codex_invocation(tmp_path), payload)


@pytest.mark.parametrize(
    "payload",
    [
        _jsonl(
            {"type": "result", "conversation_id": "agy-1", "response": _work_result()}
        ),
        _jsonl(
            {"type": "init", "conversation_id": "agy-1"},
            {"type": "result", "conversation_id": "agy-1", "response": _work_result()},
            {"type": "result", "conversation_id": "agy-1", "response": _work_result()},
        ),
        _jsonl(
            {"type": "init", "conversation_id": "agy-1"},
            {"type": "result", "conversation_id": "agy-1", "response": "bare prose"},
        ),
    ],
)
def test_agy_adapter_rejects_malformed_or_ambiguous_streams(tmp_path, payload):
    config = command.load_config(_config(tmp_path))
    route = command.resolve_route(config, "researcher")
    invocation = command.build_invocation(route, "legacy parse fixture", tmp_path)
    with pytest.raises(command.ConfigurationError):
        command.parse_provider_result(invocation, payload)


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (_jsonl({"type": "init", "conversation_id": "safe"}), "terminal_shape"),
        (
            _jsonl(
                {"event": "init", "conversation_id": "safe", "init": {}},
                {"event": "result", "result": {"conversation_id": "safe", "status": "SUCCESS", "structured_output": _work_result()}},
                {"event": "step_update", "step_update": {"conversation_id": "safe", "state": "DONE"}},
            ),
            "terminal_shape",
        ),
        (
            _jsonl(
                {"event": "init", "conversation_id": "safe", "init": {}},
                {"event": "result", "result": {"conversation_id": "other", "status": "SUCCESS", "structured_output": _work_result()}},
            ),
            "thread_id",
        ),
        (
            _jsonl(
                {"event": "init", "conversation_id": "safe", "init": {}},
                {"event": "result", "result": {"conversation_id": "safe", "status": "SUCCESS", "response": _work_result()}},
            ),
            "work_result_validation",
        ),
        (
            '{"event":"init","event":"init","conversation_id":"safe","init":{}}\n',
            "terminal_shape",
        ),
        (
            '{"event":"init","conversation_id":"safe","init":NaN}\n',
            "terminal_shape",
        ),
    ],
)
def test_official_agy_adapter_rejects_legacy_nonfinite_duplicate_postterminal_and_session_tampering(
    tmp_path, payload, reason
):
    route = command.resolve_route(command.load_config(_config(tmp_path)), "researcher")
    invocation = command.build_invocation(route, "safe parser fixture", tmp_path)
    with pytest.raises(command.ProviderParseError) as exc:
        command.parse_provider_result(invocation, payload)
    assert exc.value.provider_parse_reason == reason


def test_agy_decoded_and_encoded_prompt_echoes_are_redacted_before_receipt_evidence(tmp_path, monkeypatch):
    pii = "email=person@example.com; user_id=123456; /Users/person/private; 192.0.2.42"
    config = yaml.safe_load(_config(tmp_path).read_text(encoding="utf-8"))
    config["roles"]["researcher"].update(
        {"model": "gemini-3.1-pro-high", "effort": "high", "mode": "plan", "sandbox": True}
    )
    route = command.resolve_route(config, "researcher")
    invocation = command.build_invocation(
        route, command.render_prompt(objective=pii, ownership="tests/safe.py"), tmp_path,
        decision=_decision(selected_alias="agy1", selected_model="gemini-3.1-pro-high", selected_effort="high", scope_rank=2, work_mode="read_only"),
        model_policy=_policy(), objective=pii, ownership="tests/safe.py",
        runtime_config_path=_config(tmp_path), runtime_config_approved=True,
        scheduling_snapshot=_scheduling_snapshot(owner="researcher", ownership="tests/safe.py"),
    )
    echoed = _work_result()
    echoed["findings"] = [pii, invocation.prompt_stdin]
    parsed = command.parse_provider_result(invocation, _agy_stdout(echoed))
    rendered = json.dumps(parsed.work_result)
    for forbidden in ("person@example.com", "123456", "/Users/person", "192.0.2.42", '"event":"user"'):
        assert forbidden not in rendered
    assert "<PROMPT_REDACTED>" in rendered

    observed: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        return subprocess.CompletedProcess(
            argv, 0, _agy_stdout(echoed), "email=person@example.com"
        )

    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(command.subprocess, "run", fake_run)
    outcome = command.execute_invocation(
        replace(invocation, claim_store_override=str(tmp_path / "pii-ledger"))
    )
    public = json.dumps(outcome.completed)
    durable = "\n".join(
        path.read_text(encoding="ascii", errors="ignore")
        for path in (tmp_path / "pii-ledger").rglob("*") if path.is_file()
    )
    for forbidden in ("person@example.com", "123456", "/Users/person", "192.0.2.42"):
        assert forbidden not in public + durable + " ".join(observed["argv"])
    assert outcome.process.stdout == "[PROVIDER_STDOUT_ELIDED]"
    assert outcome.process.stderr == "[PROVIDER_STDERR_ELIDED]"


def test_provider_stream_and_work_result_reject_secret_bearing_output(tmp_path):
    result = _work_result()
    result["findings"] = ["authorization: Bearer abcdefghijklmnop"]
    with pytest.raises(command.ConfigurationError, match="secret-bearing"):
        command.parse_provider_result(
            _read_only_codex_invocation(tmp_path), _codex_stdout(result)
        )


def test_nonzero_without_typed_failure_result_is_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(command, "execute_invocation", lambda invocation: (_ for _ in ()).throw(command.ExecutionContractError("terminal_shape")))
    args = _execute_args(_config(tmp_path), _decision_path(tmp_path), tmp_path)
    assert command.main(args) == 3
    output = capsys.readouterr()
    assert "invalid-child-result-contract" in output.out
    assert "Invalid sub-agent result contract" in output.err


@pytest.mark.parametrize("provider_parse_reason", sorted(command.PROVIDER_PARSE_REASONS))
def test_invalid_provider_contract_emits_only_content_free_parse_reason(
    tmp_path, monkeypatch, capsys, provider_parse_reason
):
    """Every provider rejection taxonomy value must remain safe to serialize."""

    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    prompt_sentinel = "PROMPT-BODY-MUST-NOT-APPEAR"
    raw_payload_sentinel = "RAW-PROVIDER-PAYLOAD-MUST-NOT-APPEAR"
    provider_id_sentinel = "provider-session-id-must-not-appear"
    exception_sentinel = "PARSER-EXCEPTION-MUST-NOT-APPEAR"
    secret_sentinel = "authorization: Bearer abcdefghijklmnop"
    raw_provider_output = _jsonl(
        {
            "type": "thread.started",
            "thread_id": provider_id_sentinel,
            "payload": raw_payload_sentinel,
            "credential": secret_sentinel,
        }
    )

    monkeypatch.setattr(command, "execute_invocation", lambda invocation: (_ for _ in ()).throw(command.ExecutionContractError(provider_parse_reason)))

    def reject_provider_result(invocation, payload):
        assert payload == raw_provider_output
        raise command.ProviderParseError(
            provider_parse_reason,
            (
                f"{exception_sentinel}: {raw_payload_sentinel}; "
                f"prompt={invocation.prompt_stdin}; path={tmp_path}; "
                f"id={provider_id_sentinel}; secret={secret_sentinel}"
            ),
        )

    monkeypatch.setattr(command, "parse_provider_result", reject_provider_result)
    args = _execute_args(config_path, decision_path, tmp_path)
    args[args.index("Execute safely")] = prompt_sentinel

    assert command.main(args) == 3
    captured = capsys.readouterr()
    first_document, second_document = captured.out.split("\n{", 1)
    rendered_route = json.loads(first_document)
    blocked_result = json.loads("{" + second_document)

    assert rendered_route["status"] == "rendered-route-not-execution-proof"
    assert blocked_result["status"] == "BLOCKED"
    assert blocked_result["execution_evidence"] == {
        "source": "child-ran-invalid-result-contract",
        "failure_class": "invalid-child-result-contract",
        "provider_parse_reason": provider_parse_reason,
    }
    assert "execution_receipt" not in blocked_result
    assert "work_result" not in blocked_result
    assert "Invalid sub-agent result contract" in captured.err

    combined_output = captured.out + captured.err
    for forbidden in (
        exception_sentinel,
        raw_payload_sentinel,
        prompt_sentinel,
        str(tmp_path),
        provider_id_sentinel,
        secret_sentinel,
    ):
        assert forbidden not in combined_output


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("protocol_version", 1),
        ("attempt_id", 2),
        ("alias", "codex2"),
        ("dispatch_identity", "0" * 64),
        ("decision_sha256", "1" * 64),
        ("output_sha256", "2" * 64),
        ("work_result_sha256", "3" * 64),
    ],
)
def test_execution_receipt_rejects_identity_and_digest_tampering(
    tmp_path, monkeypatch, field, replacement
):
    invocation, process, provider_result = _finalized_claimed_process(
        tmp_path, monkeypatch, _read_only_codex_invocation(tmp_path, attempt_id=3)
    )
    try:
        receipt = command._build_execution_receipt(
            invocation, process, provider_result,
            started_at="2026-08-25T10:00:00Z", ended_at="2026-08-25T10:00:01Z",
        )
        receipt[field] = replacement
        with pytest.raises(command.ConfigurationError, match=field):
            command.validate_execution_receipt(
                receipt, provider_result.work_result, invocation, process.stdout, result=process
            )
    finally:
        command._release_dispatch_claim(process._dispatch_claim)  # type: ignore[attr-defined]


def test_execution_receipt_accepts_bound_attempt_three_pair(tmp_path, monkeypatch):
    invocation, process = _active_claimed_process(
        tmp_path, monkeypatch, _read_only_codex_invocation(tmp_path, attempt_id=3)
    )
    provider_result = command.parse_provider_result(invocation, process.stdout)
    completed = command._completed_result_contract(
        invocation,
        process,
        provider_result,
        started_at="2026-08-25T10:00:00Z",
        ended_at="2026-08-25T10:00:01Z",
    )
    assert completed["execution_receipt"]["attempt_id"] == 3
    assert completed["execution_receipt"]["process_or_session_id"] == "thread-safe-1"
    assert completed["work_result"] == _work_result()


def test_provider_schema_rejects_weakened_or_unsupported_shape(tmp_path):
    schema = json.loads(
        (ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    schema["additionalProperties"] = True
    path = tmp_path / "weakened.schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(command.ConfigurationError, match="closed object"):
        command._provider_compatible_work_result_schema(path)


@pytest.mark.parametrize(
    ("approved", "runtime_name", "sandbox", "message"),
    [
        (False, "runtime.yaml", "read-only", "approved runtime config"),
        (True, "routes.example.yaml", "read-only", "example or missing"),
        (True, "runtime.yaml", "workspace-write", "sandbox=read-only"),
    ],
)
def test_read_only_dispatch_gate_is_effective_not_prompt_only(
    tmp_path, monkeypatch, approved, runtime_name, sandbox, message
):
    monkeypatch.setenv("HOME", str(tmp_path))
    config_path = _config(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["roles"]["developer"]["sandbox"] = sandbox
    route = command.resolve_route(config, "developer")
    runtime_path = tmp_path / runtime_name
    if ".example." not in runtime_name:
        runtime_path.write_text("runtime: true\n", encoding="utf-8")
    invocation = command.build_invocation(
        route,
        command.render_prompt(objective="Read-only gate"),
        tmp_path,
        decision=_decision(work_mode="read_only"),
        model_policy=_policy(),
        runtime_config_path=runtime_path,
        runtime_config_approved=approved,
    )
    monkeypatch.setattr(command.shutil, "which", lambda executable: "/usr/bin/codex")
    with pytest.raises(command.ConfigurationError, match=message):
        command.validate_execution_preflight(invocation)


def test_completed_claim_and_attempt_replay_block_before_a_second_subprocess(tmp_path, monkeypatch):
    invocation = _read_only_codex_invocation(tmp_path, attempt_id=1)
    claim_root = tmp_path / "isolated-claims"
    claim_root.mkdir(mode=0o700)
    monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: claim_root)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    runs = []

    def fake_run(*args, **kwargs):
        runs.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    outcome = command.execute_invocation(invocation)
    assert isinstance(outcome, command.ExecutionOutcome)
    assert outcome.completed["execution_receipt"]["dispatch_claim_key"]

    validated = command.validate_dispatch_decision(
        invocation.decision, invocation.model_policy, invocation.route
    )
    replay = replace(
        invocation,
        attempt_id=2,
        prompt_stdin=invocation.prompt_stdin.replace(
            command._decision_prompt_evidence(validated, 1),
            command._decision_prompt_evidence(validated, 2),
        ),
    )
    assert command._dispatch_claim_key(replay) == command._dispatch_claim_key(invocation)
    with pytest.raises(command.SchedulingError, match="already executed") as exc:
        command.execute_invocation(replay)
    assert exc.value.code == "DUPLICATE_DISPATCH_CLAIM"
    assert len(runs) == 1


def test_cross_process_active_claim_blocks_second_subprocess(tmp_path, monkeypatch):
    invocation = _read_only_codex_invocation(tmp_path)
    claim_root = tmp_path / "cross-process-claims"
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    outcome = context.Queue()
    child = context.Process(
        target=_hold_cross_process_claim,
        args=(invocation, str(claim_root), ready, release, outcome),
    )
    child.start()
    try:
        assert ready.wait(timeout=10), outcome.get(timeout=1)
        assert outcome.get(timeout=1) == ("acquired",)
        monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: claim_root)
        monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
        monkeypatch.setattr(
            command.subprocess,
            "run",
            lambda *args, **kwargs: pytest.fail("concurrent claim reached subprocess"),
        )
        with pytest.raises(command.SchedulingError, match="already active") as exc:
            command.execute_invocation(invocation)
        assert exc.value.code == "CONCURRENT_DISPATCH_CLAIM"
    finally:
        release.set()
        child.join(timeout=10)
        if child.is_alive():  # pragma: no cover - defensive cleanup for a stuck child
            child.terminate()
            child.join(timeout=5)
    assert child.exitcode == 0


@pytest.mark.parametrize(
    ("state", "created_at", "raw", "expected_code"),
    [
        ("completed", None, None, "CONCURRENT_DISPATCH_CLAIM"),
        ("active", None, None, "CONCURRENT_DISPATCH_CLAIM"),
        ("active", "2000-01-01T00:00:00Z", None, "CONCURRENT_DISPATCH_CLAIM"),
        ("unknown", None, None, "CONCURRENT_DISPATCH_CLAIM"),
        ("active", None, b"not-json", "CONCURRENT_DISPATCH_CLAIM"),
    ],
)
def test_claim_states_fail_closed_with_typed_results(
    tmp_path, monkeypatch, state, created_at, raw, expected_code
):
    invocation = _read_only_codex_invocation(tmp_path)
    claim_root = tmp_path / "typed-claims"
    claim_root.mkdir(mode=0o700)
    monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: claim_root)
    claim = command._acquire_dispatch_claim(invocation)
    if raw is not None:
        claim.path.write_bytes(raw)
    else:
        record = dict(claim.record)
        record["state"] = state
        if created_at:
            record["created_at"] = created_at
            record["updated_at"] = created_at
        claim.path.write_text(json.dumps(record), encoding="ascii")

    try:
        with pytest.raises(command.SchedulingError) as exc:
            command._acquire_dispatch_claim(invocation)
        assert exc.value.code == expected_code
    finally:
        command._release_dispatch_claim(claim)


def test_final_persisted_claim_recheck_rejects_tampering(tmp_path, monkeypatch):
    invocation = _read_only_codex_invocation(tmp_path)
    claim_root = tmp_path / "recheck-claims"
    claim_root.mkdir(mode=0o700)
    monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: claim_root)
    claim = command._acquire_dispatch_claim(invocation)
    tampered = dict(claim.record)
    tampered["state"] = "completed"
    claim.path.write_text(json.dumps(tampered), encoding="ascii")

    with pytest.raises(command.SchedulingError, match="terminal claim timestamp is invalid") as exc:
        command._verify_dispatch_claim(claim)
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_personal_data_is_redacted_from_preview_receipt_result_and_mapping_keys(tmp_path, monkeypatch):
    invocation = _read_only_codex_invocation(tmp_path)
    personal = (
        "email=person@example.com; user_id=123456; /Users/person/private; "
        "192.0.2.42"
    )
    pii_invocation = command.build_invocation(
        invocation.route,
        command.render_prompt(objective=personal, ownership=personal),
        tmp_path,
        decision=invocation.decision,
        model_policy=invocation.model_policy,
        attempt_id=invocation.attempt_id,
        objective=personal,
        ownership=personal,
        runtime_config_path=invocation.runtime_config_path,
        runtime_config_approved=True,
        work_result_schema_path=invocation.work_result_schema_path,
        scheduling_snapshot=_scheduling_snapshot(ownership=personal),
    )
    preview = command._redact_preview(personal, pii_invocation)
    assert "person@example.com" not in preview
    assert "123456" not in preview
    assert "/Users/person" not in preview
    assert "192.0.2.42" not in preview

    invocation, process, provider_result = _finalized_claimed_process(
        tmp_path, monkeypatch, pii_invocation
    )
    try:
        receipt = command._build_execution_receipt(
            invocation, process, provider_result,
            started_at="2026-08-25T10:00:00Z", ended_at="2026-08-25T10:00:01Z",
        )
        result = command._redact_result_value(
            {personal: {"personal": personal}}, pii_invocation
        )
        rendered = json.dumps({"preview": preview, "receipt": receipt, "result": result})
        for forbidden in ("person@example.com", "123456", "/Users/person", "192.0.2.42"):
            assert forbidden not in rendered
        assert "<EMAIL_REDACTED>" in rendered
        assert "<PERSONAL_ID_REDACTED>" in rendered
        assert "<USER_HOME_REDACTED>" in rendered
        assert "<IP_REDACTED>" in rendered
    finally:
        command._release_dispatch_claim(process._dispatch_claim)  # type: ignore[attr-defined]


def test_claim_store_uses_namespaced_state_outside_worktree_or_safe_override(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    invocation = replace(_read_only_codex_invocation(worktree), claim_store_override=None)
    store = ORIGINAL_CLAIM_STORE(invocation)
    try:
        assert store.path.is_absolute()
        assert store.path.is_relative_to(tmp_path / "home")
        assert not store.path.is_relative_to(worktree)
        assert not (worktree / ".horo").exists()
    finally:
        store.close()

    for override in ("relative", str(tmp_path.parent / "outside")):
        with pytest.raises(command.SchedulingError) as exc:
            ORIGINAL_CLAIM_STORE(replace(invocation, claim_store_override=override))
        assert exc.value.code == "INVALID_CLAIM_STORE"


def test_claim_files_are_0600_and_parent_fsync_is_observable(tmp_path, monkeypatch):
    invocation = replace(
        _read_only_codex_invocation(tmp_path), claim_store_override=str(tmp_path / "claims")
    )
    fsync_calls = []
    original_fsync = command.os.fsync
    monkeypatch.setattr(command.os, "fsync", lambda descriptor: fsync_calls.append(descriptor) or original_fsync(descriptor))
    claim = command._acquire_dispatch_claim(invocation)
    try:
        assert claim.path.stat().st_mode & 0o777 == 0o600
        assert fsync_calls
    finally:
        command._release_dispatch_claim(claim)


def test_lock_lifetime_and_toctou_recheck_cover_spawn_parse_and_deleted_entry(tmp_path, monkeypatch):
    invocation, process = _active_claimed_process(
        tmp_path, monkeypatch, _read_only_codex_invocation(tmp_path)
    )
    claim = process._dispatch_claim  # type: ignore[attr-defined]
    assert claim.closed is False
    provider_result = command.parse_provider_result(invocation, process.stdout)
    assert claim.closed is False
    completed = command._completed_result_contract(
        invocation, process, provider_result,
        started_at="2026-08-25T10:00:00Z", ended_at="2026-08-25T10:00:01Z",
    )
    assert completed["execution_receipt"]["dispatch_claim_key"] == claim.key
    assert claim.closed is True

    invocation = replace(
        _read_only_codex_invocation(tmp_path), claim_store_override=str(tmp_path / "toctou")
    )
    monkeypatch.setattr(command, "_secure_claim_directory", lambda _invocation: tmp_path / "toctou")
    claim = command._acquire_dispatch_claim(invocation)
    try:
        claim.path.unlink()
        with pytest.raises((command.SchedulingError, OSError)):
            command._verify_dispatch_claim(claim)
        with pytest.raises(command.SchedulingError):
            command._acquire_dispatch_claim(invocation)
    finally:
        command._release_dispatch_claim(claim)


@pytest.mark.parametrize("kind", ["symlink", "fifo", "large", "mode", "hardlink"])
def test_claim_reader_rejects_unsafe_file_types_and_sizes(tmp_path, kind):
    store = tmp_path / "claims"
    store.mkdir(mode=0o700)
    path = store / "unsafe.json"
    if kind == "symlink":
        path.symlink_to(tmp_path / "missing-target")
    elif kind == "fifo":
        os.mkfifo(path, 0o600)
    elif kind == "mode":
        path.write_text("{}", encoding="ascii")
        path.chmod(0o644)
    elif kind == "hardlink":
        original = store / "original.json"
        original.write_text("{}", encoding="ascii")
        original.chmod(0o600)
        os.link(original, path)
    else:
        path.write_bytes(b"x" * (command.MAX_DISPATCH_CLAIM_BYTES + 1))
        path.chmod(0o600)
    with pytest.raises(command.SchedulingError) as exc:
        command._read_dispatch_claim(path)
    assert exc.value.code == "INVALID_DISPATCH_CLAIM"


def test_claim_file_open_flags_require_nofollow_nonblock_and_fstat_validation():
    flags = command._file_open_flags(os.O_RDONLY)
    assert flags & getattr(os, "O_NOFOLLOW", 0)
    assert flags & getattr(os, "O_NONBLOCK", 0)


def test_completed_claim_binds_receipt_and_rejects_missing_or_mismatched_proof(tmp_path, monkeypatch):
    invocation, process, provider_result = _finalized_claimed_process(
        tmp_path, monkeypatch, _read_only_codex_invocation(tmp_path)
    )
    try:
        receipt = command._build_execution_receipt(
            invocation, process, provider_result,
            started_at="2026-08-25T10:00:00Z", ended_at="2026-08-25T10:00:01Z",
        )
        persisted = process._dispatch_claim.record  # type: ignore[attr-defined]
        for field in (
            "dispatch_identity", "route_sha256", "ownership_tokens_sha256",
            "ownership_key_id", "started_at", "ended_at", "transport_status",
            "output_sha256", "work_result_sha256",
        ):
            assert persisted[field]
        assert command.validate_execution_receipt(
            receipt, provider_result.work_result, invocation, process.stdout, result=process
        )["dispatch_claim_key"] == persisted["claim_key"]
        for field, value in (("dispatch_claim_key", None), ("dispatch_claim_sha256", "0" * 64)):
            tampered = dict(receipt)
            if value is None:
                del tampered[field]
            else:
                tampered[field] = value
            with pytest.raises(command.ConfigurationError):
                command.validate_execution_receipt(
                    tampered, provider_result.work_result, invocation, process.stdout, result=process
                )
    finally:
        command._release_dispatch_claim(process._dispatch_claim)  # type: ignore[attr-defined]


def test_startup_config_yaml_and_os_errors_are_sanitized(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "person@example.com" / "bad.yaml"
    monkeypatch.setattr(command, "load_config", lambda path: (_ for _ in ()).throw(OSError(str(config_path))))
    assert command.main([
        "--config", str(config_path), "--role", "developer", "--objective", "/Users/person 192.0.2.42"
    ]) == 2
    output = capsys.readouterr().err
    assert output == "[ERROR] BLOCKED: CONFIG_IO_ERROR\n"
    assert all(item not in output for item in (str(config_path), "person@example.com", "/Users/person", "192.0.2.42"))

    monkeypatch.setattr(command, "load_config", lambda path: (_ for _ in ()).throw(yaml.YAMLError("/Users/person person@example.com")))
    assert command.main([
        "--config", str(config_path), "--role", "developer", "--objective", "safe"
    ]) == 2
    output = capsys.readouterr().err
    assert output == "[ERROR] BLOCKED: CONFIG_PARSE_ERROR\n"


def _capacity_bound_invocation(tmp_path: Path):
    invocation = _read_only_codex_invocation(tmp_path, attempt_id=7)
    Path(invocation.claim_store_override).mkdir(mode=0o700)
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    quality_floor = str(command.validate_dispatch_decision(
        invocation.decision, invocation.model_policy, invocation.route
    ).quality_floor)
    store = tmp_path / "capacity-store"
    lease = command.capacity.acquire_lease(
        store,
        account="codex1",
        request_id="capacity-dispatch-7",
        owner="developer",
        lane=7,
        request_budget=2,
        model_quality_floor=quality_floor,
        policy=policy,
    )
    return replace(
        invocation,
        capacity_lease=lease,
        capacity_store_path=str(store),
        capacity_policy=policy,
        capacity_request_id="capacity-dispatch-7",
        capacity_required=True,
    )


def test_capacity_missing_tampered_and_mismatched_leases_block_before_spawn(tmp_path, monkeypatch):
    for index, kind in enumerate(("missing", "expired", "mismatched", "tampered")):
        invocation_root = tmp_path / str(index)
        invocation_root.mkdir()
        invocation = _capacity_bound_invocation(invocation_root)
        if kind == "missing":
            invalid = replace(invocation, capacity_lease=None)
        elif kind == "expired":
            expired = command.capacity.acquire_lease(
                invocation.capacity_store_path,
                account="codex1",
                request_id="expired-dispatch-7",
                owner="developer",
                lane=7,
                request_budget=1,
                model_quality_floor=str(command.validate_dispatch_decision(
                    invocation.decision, invocation.model_policy, invocation.route
                ).quality_floor),
                policy=invocation.capacity_policy,
                now=1,
            )
            invalid = replace(
                invocation, capacity_lease=expired, capacity_request_id="expired-dispatch-7"
            )
        elif kind == "mismatched":
            invalid = replace(invocation, capacity_request_id="wrong-request")
        else:
            invalid = replace(
                invocation,
                capacity_lease={**invocation.capacity_lease.to_dict(), "owner": "tampered"},
            )
        validated = command.validate_dispatch_decision(
            invalid.decision, invalid.model_policy, invalid.route
        )
        with pytest.raises(command.SchedulingError, match="capacity lease"):
            command._consume_spawn_capacity(invalid, validated)


def test_capacity_is_consumed_at_spawn_and_released_after_process(tmp_path, monkeypatch):
    invocation = _capacity_bound_invocation(tmp_path)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    observed: list[int] = []

    def fake_run(*args, **kwargs):
        state = json.loads((Path(invocation.capacity_store_path) / ".capacity.json").read_text())
        observed.append(next(iter(state["leases"].values()))["requests_used"])
        return subprocess.CompletedProcess(args[0], 0, stdout=_valid_result_stdout(), stderr="")

    monkeypatch.setattr(command.subprocess, "run", fake_run)
    outcome = command.execute_invocation(invocation)
    assert outcome.process.returncode == 0
    assert observed == [1]
    state = json.loads((Path(invocation.capacity_store_path) / ".capacity.json").read_text())
    assert state["leases"] == {}
    with pytest.raises(command.capacity.LeaseRejectedError, match="REPLAY_REJECTED"):
        command.capacity.consume_lease(
            invocation.capacity_store_path, invocation.capacity_lease, requests=1,
            policy=invocation.capacity_policy,
        )


@pytest.mark.parametrize("fault", ("missing", "expired", "tampered", "mismatched"))
def test_main_execute_rejects_bad_capacity_before_subprocess_and_releases_admission(
    tmp_path, monkeypatch, fault
):
    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    original_replace = command.replace
    captured: dict[str, object] = {}

    def inject_bad_capacity(value, **changes):
        if changes.get("capacity_required") is True:
            lease = changes["capacity_lease"]
            store = changes["capacity_store_path"]
            policy = changes["capacity_policy"]
            captured.update(store=store, policy=policy, lease=lease)
            if fault == "missing":
                changes["capacity_lease"] = None
            elif fault == "mismatched":
                changes["capacity_request_id"] = "wrong-request"
            elif fault == "tampered":
                changes["capacity_lease"] = {**lease.to_dict(), "owner": "tampered"}
            else:
                changes["capacity_lease"] = command.capacity.acquire_lease(
                    store,
                    account="codex1",
                    request_id="expired-main-dispatch",
                    owner="developer",
                    lane=1,
                    request_budget=1,
                    model_quality_floor=lease.model_quality_floor,
                    policy=policy,
                    now=1,
                )
                changes["capacity_request_id"] = "expired-main-dispatch"
        return original_replace(value, **changes)

    monkeypatch.setattr(command, "replace", inject_bad_capacity)
    monkeypatch.setattr(command, "validate_execution_preflight", lambda _invocation: None)
    monkeypatch.setattr(command.subprocess, "run", lambda *args, **kwargs: pytest.fail("spawned"))
    assert command.main(_execute_args(config_path, decision_path, tmp_path)) == 5
    assert captured
    fresh = command.capacity.acquire_lease(
        captured["store"], account="codex1", request_id=f"reusable-{fault}",
        owner="developer", lane=1, request_budget=1,
        model_quality_floor=captured["lease"].model_quality_floor,
        policy=captured["policy"],
    )
    command.capacity.release_lease(captured["store"], fresh, policy=captured["policy"])


def test_main_execute_releases_admission_when_preflight_fails(tmp_path, monkeypatch):
    config_path = _config(tmp_path)
    decision_path = _decision_path(tmp_path)
    captured: dict[str, object] = {}
    original_admit = command.admit_dispatch_capacity

    def capture_admission(*args, **kwargs):
        lease = original_admit(*args, **kwargs)
        captured.update(lease=lease, store=kwargs["store_path"], policy=kwargs["policy"])
        return lease

    monkeypatch.setattr(command, "admit_dispatch_capacity", capture_admission)
    monkeypatch.setattr(
        command, "validate_execution_preflight",
        lambda _invocation: (_ for _ in ()).throw(command.ConfigurationError("preflight failed")),
    )
    monkeypatch.setattr(command.subprocess, "run", lambda *args, **kwargs: pytest.fail("spawned"))
    assert command.main(_execute_args(config_path, decision_path, tmp_path)) == 127
    fresh = command.capacity.acquire_lease(
        captured["store"], account="codex1", request_id="reusable-preflight",
        owner="developer", lane=1, request_budget=1,
        model_quality_floor=captured["lease"].model_quality_floor,
        policy=captured["policy"],
    )
    command.capacity.release_lease(captured["store"], fresh, policy=captured["policy"])


@pytest.mark.parametrize(
    ("pressure", "expected_code"),
    (
        ("burn", "CAPACITY_BURN_RATE_EXCEEDED"),
        ("block", "CAPACITY_BACKPRESSURE_BLOCKED"),
        ("queue", "CAPACITY_BACKPRESSURE_QUEUED"),
        ("circuit", "CAPACITY_CIRCUIT_OPEN"),
    ),
)
def test_main_pressure_admission_blocks_before_subprocess(
    tmp_path, monkeypatch, capsys, pressure, expected_code
):
    """CLI admission evaluates the selected pool before executable preflight."""

    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    store = tmp_path / ".horo-capacity"
    if pressure == "burn":
        burner = command.capacity.acquire_lease(
            store,
            account="codex1",
            request_id="burner",
            owner="developer",
            lane=2,
            request_budget=policy["accounts"]["codex1"]["burn_rate"]["max_requests"],
            model_quality_floor="1",
            policy=policy,
        )
        consumed = command.capacity.consume_lease(
            store, burner, requests=burner.request_budget, policy=policy
        )
        command.capacity.release_lease(store, consumed, policy=policy)
    elif pressure in {"block", "queue"}:
        command.capacity.set_backpressure(
            store, account="codex1", mode=pressure, policy=policy
        )
    else:
        threshold = policy["accounts"]["codex1"]["circuit_breaker"]["failure_threshold"]
        for _ in range(threshold):
            command.capacity.record_failure(
                store, account="codex1", failure_type="timeout", policy=policy
            )

    monkeypatch.setattr(command.subprocess, "run", lambda *args, **kwargs: pytest.fail("spawned"))
    assert command.main(_execute_args(_config(tmp_path), _decision_path(tmp_path), tmp_path)) == 5
    assert expected_code in capsys.readouterr().err
