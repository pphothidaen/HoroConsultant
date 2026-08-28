"""RED contract for the provider-native, one-shot IDQ-MVP-080 adapter.

This is deliberately a fake-subprocess-only test seam.  It authorizes neither
network access nor a real provider account: the eventual adapter may accept an
injected ``run_subprocess`` solely for deterministic local verification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

import scripts.multiagent_prompt_command as command


TICKET = "IDQ-MVP-080"
ALIASES = {"codex1": "codex", "codex2": "codex", "agy1": "agy", "agy2": "agy"}
RAW_SENTINEL = "sk-live-provider-output-must-never-persist"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _config() -> dict[str, object]:
    return {
        "activation_prohibited": True,
        "dispatcher_execution": "CLOSED",
        "idq_mvp_080": {
            "ticket": TICKET,
            "aliases": {
                alias: {
                    "provider": provider,
                    "attempt": 1,
                    "work_mode": "read_only",
                    "automatic_retry": False,
                    "fallback": False,
                }
                for alias, provider in ALIASES.items()
            },
        },
    }


def _request(alias: str) -> dict[str, object]:
    return {
        "ticket": TICKET,
        "alias": alias,
        "provider": ALIASES[alias],
        "attempt": 1,
        "work_mode": "read_only",
        "automatic_retry": False,
        "fallback": False,
        "decision_sha256": _digest(f"decision:{alias}"),
        "qobs_artifact_sha256": _digest(f"qobs:{alias}"),
        "qobs_quota_band": "constrained",
        "nonce_sha256": _digest(f"nonce:{alias}"),
        "scheduling_snapshot_sha256": _digest(f"snapshot:{alias}"),
        "resolved_executable_sha256": _digest(f"executable:{alias}"),
        "account_identity_sha256": _digest(f"account:{alias}"),
        "lease_risk_sha256": _digest(f"lease:{alias}"),
    }


def _context(request: dict[str, object]) -> dict[str, object]:
    return {
        "qobs": {"known": True, "quota_band": "constrained", "sha256": request["qobs_artifact_sha256"]},
        "decision": {"fresh": True, "sha256": request["decision_sha256"]},
        "scheduling_snapshot": {"non_placeholder": True, "sha256": request["scheduling_snapshot_sha256"]},
        "resolved_executable": {"safe": True, "sha256": request["resolved_executable_sha256"]},
        "account_identity": {"safe": True, "sha256": request["account_identity_sha256"]},
        "nonce": {"unused": True, "sha256": request["nonce_sha256"]},
        "runtime": (
            {"read_only": True, "sandbox": "read-only"}
            if request["provider"] == "codex"
            else {"read_only": True, "mode": "plan", "sandbox": True}
        ),
    }


def _work_result(status: str = "DONE") -> dict[str, object]:
    return {
        "status": status,
        "scope_owned": ["read-only repository inventory"],
        "evidence": {"commands": [], "outcomes": ["fake native output"], "artifacts": []},
        "findings": ["fake typed result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "stop",
    }


def _codex_jsonl(result: dict[str, object], *, final: bool = True) -> str:
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": "codex-test-080"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(result)}},
    ]
    if final:
        events.append({"type": "turn.completed"})
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _agy_jsonl(result: dict[str, object], *, final: bool = True) -> str:
    events: list[dict[str, object]] = [
        {"event": "init", "conversation_id": "agy-test-080", "init": {}},
    ]
    if final:
        events.append(
            {
                "event": "result",
                "result": {
                    "conversation_id": "agy-test-080",
                    "status": "SUCCESS",
                    "structured_output": result,
                },
            }
        )
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _expected_argv(alias: str) -> tuple[str, ...]:
    root = str(command.REPOSITORY_ROOT)
    if ALIASES[alias] == "codex":
        return ("codex", "exec", "-C", root, "-s", "read-only", "--json", "-")
    return (
        "agy", "--mode", "plan", "--sandbox", "--print",
        "--input-format", "stream-json", "--output-format", "stream-json",
    )


def _fake_runner(payload: str, *, exit_code: int = 0) -> tuple[list[tuple[tuple[Any, ...], dict[str, Any]]], Any]:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        argv = tuple(args[0] if args else kwargs["args"])
        return subprocess.CompletedProcess(argv, exit_code, stdout=payload, stderr="")

    return calls, runner


@pytest.mark.parametrize("alias", tuple(ALIASES))
def test_adapter_runs_only_exact_provider_native_read_only_argv_after_marker(
    tmp_path: Path, alias: str
) -> None:
    request = _request(alias)
    events: list[str] = []
    original_admission = command.validate_idq_mvp_080_execution_admission
    original_consume = command._consume_idq_mvp_080_marker

    def observe_admission(*args: object, **kwargs: object) -> object:
        events.append("admission")
        return original_admission(*args, **kwargs)

    def observe_consume(*args: object, **kwargs: object) -> None:
        events.append("marker")
        return original_consume(*args, **kwargs)

    # The adapter must preserve this final preflight -> marker -> process order.
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(command, "validate_idq_mvp_080_execution_admission", observe_admission)
    monkeypatch.setattr(command, "_consume_idq_mvp_080_marker", observe_consume)
    payload = _codex_jsonl(_work_result()) if ALIASES[alias] == "codex" else _agy_jsonl(_work_result())
    calls, runner = _fake_runner(payload)
    try:
        completed = command.execute_idq_mvp_080_provider_adapter(
            _config(), request, _context(request), tmp_path, runner
        )
    finally:
        monkeypatch.undo()

    assert events == ["admission", "marker"]
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert tuple(args[0]) == _expected_argv(alias)
    assert kwargs["shell"] is False
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.PIPE
    assert completed["work_result"] == _work_result()
    receipt = completed["receipt"]
    assert receipt["ticket"] == TICKET
    assert receipt["alias"] == alias
    assert receipt["provider"] == ALIASES[alias]
    for field in ("decision_sha256", "qobs_artifact_sha256", "nonce_sha256", "scheduling_snapshot_sha256"):
        assert receipt[field] == request[field]
    assert completed["output_evidence"] == {
        "output_bytes": len(payload.encode("utf-8")),
        "output_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "process_or_session_id": f"{ALIASES[alias]}-test-080",
    }
    assert RAW_SENTINEL not in json.dumps(completed, sort_keys=True)
    assert not any(RAW_SENTINEL.encode("utf-8") in path.read_bytes() for path in tmp_path.rglob("*" ) if path.is_file())


@pytest.mark.parametrize(
    ("payload", "exit_code"),
    [
        (RAW_SENTINEL, 0),
        (_codex_jsonl(_work_result(), final=False), 0),
        (_agy_jsonl(_work_result(), final=False), 0),
        (_codex_jsonl(_work_result(), final=True), 1),
    ],
)
def test_adapter_rejects_raw_malformed_or_nonzero_done_streams_without_persisting_them(
    tmp_path: Path, payload: str, exit_code: int
) -> None:
    calls, runner = _fake_runner(payload, exit_code=exit_code)
    with pytest.raises(command.ConfigurationError):
        command.execute_idq_mvp_080_provider_adapter(
            _config(), _request("codex1"), _context(_request("codex1")), tmp_path, runner
        )
    assert len(calls) == 1
    assert not any(payload.encode("utf-8") in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file())


def test_adapter_accepts_nonzero_only_with_a_typed_terminal_failure(tmp_path: Path) -> None:
    request = _request("agy1")
    payload = _agy_jsonl(_work_result("BLOCKED"))
    calls, runner = _fake_runner(payload, exit_code=9)
    completed = command.execute_idq_mvp_080_provider_adapter(
        _config(), request, _context(request), tmp_path, runner
    )
    assert len(calls) == 1
    assert completed["work_result"]["status"] == "BLOCKED"
    assert completed["receipt"]["exit_code"] == 9
