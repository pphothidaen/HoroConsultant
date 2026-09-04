from __future__ import annotations

import ast
import base64
import copy
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ENTRYPOINT = ROOT / "scripts" / "context_handoff.py"
_FIXTURE_ENTRYPOINT = ROOT / "tests" / "fixtures" / "context_handoff" / "context_handoff.py"
ENTRYPOINT = _DEFAULT_ENTRYPOINT if _DEFAULT_ENTRYPOINT.is_file() else _FIXTURE_ENTRYPOINT

_DEFAULT_POLICY = ROOT / ".agents" / "config" / "context_handoff_v1.json"
_FIXTURE_POLICY = ROOT / "tests" / "fixtures" / "context_handoff" / "context_handoff_v1.json"
POLICY_PATH = _DEFAULT_POLICY if _DEFAULT_POLICY.is_file() else _FIXTURE_POLICY


def _truncate_file(path: Path, size: int) -> None:
    with path.open("r+b") as f:
        f.truncate(size)

HANDOFF_START = "<!-- HANDOFF-SNAPSHOT-V1:START -->"
HANDOFF_END = "<!-- HANDOFF-SNAPSHOT-V1:END -->"

SNAPSHOT_KEYS = {
    "schema_version",
    "created_at",
    "runtime",
    "ticket_id",
    "reason",
    "objective",
    "summary",
    "next_action",
    "authority",
    "lanes",
    "dirty_paths",
    "risks",
    "decisions",
    "clear_ready",
}
LANE_KEYS = {"id", "owner", "status", "summary", "next_action"}
DECISION_KEYS = {
    "schema_version",
    "runtime",
    "event",
    "signal",
    "level",
    "notify",
    "recommendation",
    "clear_ready",
}
SIGNAL_KEYS = {"kind", "source", "value", "limit", "normalized_percent"}

EXPECTED_POLICY = {
    "schema_version": "context-handoff-policy-v1",
    "input_limits": {"hook_bytes": 64 * 1024},
    "output_limits": {
        "handoff_bytes": 16 * 1024,
        "rehydrate_bytes": 4 * 1024,
        "additional_context_bytes": 4 * 1024,
    },
    "thresholds": {
        "percent": {"alert": 40, "snapshot": 45, "critical": 80},
        "transcript_bytes": {
            "alert": 400 * 1024,
            "snapshot": 450 * 1024,
            "critical": 900 * 1024,
        },
    },
    "signal_precedence": [
        "token_count",
        "percent",
        "transcript_stat_bytes",
        "label_bytes",
        "UNKNOWN",
    ],
    "normalized_state_channel": {
        "kind": "json_file",
        "path_environment": "CONTEXT_HANDOFF_STATE_FILE",
        "cli_flag": "--state-file",
        "max_bytes": 64 * 1024,
        "unset_behavior": "empty_state",
    },
    "authority": {
        "current_state": "ATOMIC_TICKET.md",
        "implementation_plan": "plans/plan.md",
        "derived_handoff": "HANDOFF.md",
    },
    "runtimes": ["codex", "claude", "agy"],
    "operations": ["hook", "snapshot", "rehydrate", "validate"],
    "operator_only_actions": ["compact", "clear", "reset"],
    "codex_hooks": {
        "scope": "non-managed_project_hooks",
        "trust": "native_user_review_exact_current_hash",
        "unreviewed_or_changed": "skip",
        "repository_bypass_policy": "never_invoke_or_recommend",
    },
}


def _require_entrypoint() -> None:
    assert ENTRYPOINT.is_file() and ENTRYPOINT.stat().st_size > 0, "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"


def _invoke(
    operation: str,
    *args: str,
    payload: dict[str, Any] | None = None,
    raw_input: bytes | None = None,
    timeout: float = 5.0,
) -> subprocess.CompletedProcess[bytes]:
    _require_entrypoint()
    if raw_input is not None and payload is not None:
        raise AssertionError("test helper accepts payload or raw_input, not both")
    if payload is not None:
        raw_input = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), operation, *args],
        cwd=ROOT,
        input=raw_input,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _json_stdout(result: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    value = json.loads(result.stdout.decode("utf-8"))
    assert isinstance(value, dict)
    return value


def _stderr(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stderr.decode("utf-8", errors="replace")


def _lane(
    lane_id: str,
    *,
    status: str = "READY",
    owner: str = "developer",
) -> dict[str, str]:
    return {
        "id": lane_id,
        "owner": owner,
        "status": status,
        "summary": f"Bounded state for {lane_id}",
        "next_action": f"Continue {lane_id} only after its gate is green",
    }


def _snapshot_payload(
    *,
    runtime: str = "codex",
    lanes: list[dict[str, str]] | None = None,
    clear_ready: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": "HandoffSnapshotV1",
        "created_at": "2026-08-30T00:00:00Z",
        "runtime": runtime,
        "ticket_id": "CTX-010-RED",
        "reason": "manual",
        "objective": "Preserve bounded cross-runtime context without authority drift",
        "summary": "The handoff capsule is derived state and contains no raw transcript.",
        "next_action": "Read atomic_tasks.md and plans/plan.md before resuming.",
        "authority": EXPECTED_POLICY["authority"].copy(),
        "lanes": list(lanes or []),
        "dirty_paths": ["tests/test_context_handoff.py"],
        "risks": ["Do not treat local hook output as provider proof."],
        "decisions": ["Operator approval is required before clear, compact, or reset."],
        "clear_ready": clear_ready,
    }


def _snapshot(
    output: Path,
    payload: dict[str, Any],
    *extra_args: str,
) -> subprocess.CompletedProcess[bytes]:
    return _invoke("snapshot", "--output", str(output), *extra_args, payload=payload)


def _start_snapshot(
    output: Path,
    payload: dict[str, Any],
    *extra_args: str,
) -> subprocess.Popen[bytes]:
    _require_entrypoint()
    return subprocess.Popen(
        [
            sys.executable,
            str(ENTRYPOINT),
            "snapshot",
            "--output",
            str(output),
            *extra_args,
        ],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _finish_concurrent_snapshots(
    pending: list[tuple[subprocess.Popen[bytes], dict[str, Any]]],
) -> list[subprocess.CompletedProcess[bytes]]:
    for process, payload in pending:
        assert process.stdin is not None
        process.stdin.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        process.stdin.close()

    completed: list[subprocess.CompletedProcess[bytes]] = []
    for process, _ in pending:
        assert process.stdout is not None
        assert process.stderr is not None
        stdout = process.stdout.read()
        stderr = process.stderr.read()
        returncode = process.wait(timeout=5)
        completed.append(
            subprocess.CompletedProcess(process.args, returncode, stdout, stderr)
        )
    return completed


def _decode_handoff(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert text.count(HANDOFF_START) == 1
    assert text.count(HANDOFF_END) == 1
    encoded = text.split(HANDOFF_START, 1)[1].split(HANDOFF_END, 1)[0].strip()
    value = json.loads(encoded)
    assert isinstance(value, dict)
    return raw, value


def _replace_leaf(value: dict[str, Any], path: tuple[str | int, ...], leaf: str) -> None:
    target: Any = value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = leaf


def _temp_artifacts(output: Path) -> list[Path]:
    return sorted(output.parent.glob(f".{output.name}.*"))


def _hook_decision(
    payload: dict[str, Any],
    *,
    transcript_path: str | None = None,
) -> dict[str, Any]:
    native_payload = {
        "session_id": "codex-session-core-canary",
        "transcript_path": transcript_path,
        "cwd": "/workspace/HoroConsultant",
        "hook_event_name": "Stop",
        "model": "gpt-5.6-sol",
        "permission_mode": "default",
        "turn_id": "codex-turn-core-canary",
        "stop_hook_active": False,
        "last_assistant_message": "bounded assistant summary",
    }
    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(payload, separators=(",", ":")),
        payload=native_payload,
    )
    decision = _json_stdout(result)
    assert set(decision) == DECISION_KEYS
    assert decision["schema_version"] == "ContextHandoffDecisionV1"
    assert set(decision["signal"]) == SIGNAL_KEYS
    return decision


def _status_bytes() -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def test_context_handoff_entrypoint_missing_before_source() -> None:
    assert ENTRYPOINT.is_file() and ENTRYPOINT.stat().st_size > 0, "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"


def test_cli_exposes_exact_operations_and_uses_only_the_standard_library() -> None:
    _require_entrypoint()
    help_result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0, help_result.stderr
    for operation in ("hook", "snapshot", "rehydrate", "validate"):
        assert operation in help_result.stdout

    source = ENTRYPOINT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    non_stdlib = sorted(
        name
        for name in imported_roots
        if name != "__future__" and name not in sys.stdlib_module_names
    )
    assert non_stdlib == [], f"context handoff engine imports non-stdlib modules: {non_stdlib}"
    assert "subprocess" not in imported_roots, "engine must not launch git, clear, compact, or reset commands"


def test_canonical_policy_is_closed_and_freezes_limits_precedence_and_authority() -> None:
    assert POLICY_PATH.is_file(), "CONTEXT_HANDOFF_POLICY_MISSING"
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    assert policy == EXPECTED_POLICY


def test_hook_rejects_input_over_64_kib() -> None:
    canary = ("oversize-canary-" + ("Q" * 80)).encode("ascii")
    raw = b'{"padding":"' + canary + (b"x" * (64 * 1024)) + b'"}'
    assert len(raw) > 64 * 1024

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        raw_input=raw,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert "HOOK_INPUT_TOO_LARGE" in _stderr(result)
    assert canary not in result.stderr
    assert b"oversize-canary" not in result.stderr


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b"null",
        b'\xff{"usage":{}}',
        b'{"usage":{},"diagnostic_canary":"malformed-canary-' + (b"Z" * 64),
    ],
    ids=["truncated", "array", "null", "invalid-utf8", "non-echo-canary"],
)
def test_hook_rejects_malformed_or_non_object_input_without_echo(raw: bytes) -> None:
    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        raw_input=raw,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert "HOOK_INPUT_INVALID" in _stderr(result)
    if b"malformed-canary" in raw:
        assert b"malformed-canary" not in result.stderr


def test_signal_precedence_is_tokens_then_percent_then_stat_bytes_then_unknown(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_bytes(b"")
    _truncate_file(transcript, 950 * 1024)
    token_decision = _hook_decision(
        {
            "usage": {
                "tokens": {"used": 500, "limit": 1000},
                "percent": 90,
                "label": "999 KiB",
            },
            "last_notified_level": "NORMAL",
            "lanes": [],
        },
        transcript_path=str(transcript),
    )
    assert token_decision["signal"] == {
        "kind": "tokens",
        "source": "token_count",
        "value": 500,
        "limit": 1000,
        "normalized_percent": 50,
    }
    assert token_decision["level"] == "SNAPSHOT"

    percent_decision = _hook_decision(
        {
            "usage": {"percent": 80, "label": "100 KiB"},
            "last_notified_level": "NORMAL",
            "lanes": [],
        },
        transcript_path=str(transcript),
    )
    assert percent_decision["signal"]["kind"] == "percent"
    assert percent_decision["signal"]["source"] == "percent"
    assert percent_decision["signal"]["normalized_percent"] == 80
    assert percent_decision["level"] == "CRITICAL"

    critical_bytes_decision = _hook_decision(
        {"usage": {}, "last_notified_level": "NORMAL", "lanes": []},
        transcript_path=str(transcript),
    )
    assert critical_bytes_decision["signal"] == {
        "kind": "bytes",
        "source": "transcript_stat_bytes",
        "value": 950 * 1024,
        "limit": None,
        "normalized_percent": None,
    }
    assert critical_bytes_decision["level"] == "CRITICAL"

    _truncate_file(transcript, 450 * 1024)
    bytes_decision = _hook_decision(
        {"usage": {}, "last_notified_level": "NORMAL", "lanes": []},
        transcript_path=str(transcript),
    )
    assert bytes_decision["signal"] == {
        "kind": "bytes",
        "source": "transcript_stat_bytes",
        "value": 450 * 1024,
        "limit": None,
        "normalized_percent": None,
    }
    assert bytes_decision["level"] == "SNAPSHOT"

    unknown_decision = _hook_decision(
        {"usage": {}, "last_notified_level": "NORMAL", "lanes": []}
    )
    assert unknown_decision["signal"] == {
        "kind": "UNKNOWN",
        "source": "UNKNOWN",
        "value": None,
        "limit": None,
        "normalized_percent": None,
    }
    assert unknown_decision["level"] == "UNKNOWN"
    assert unknown_decision["clear_ready"] is False


def test_label_bytes_are_a_transcript_size_fallback_and_never_a_percent() -> None:
    decision = _hook_decision(
        {
            "usage": {"label": "460 KiB"},
            "last_notified_level": "NORMAL",
            "lanes": [],
        }
    )

    assert decision["signal"] == {
        "kind": "bytes",
        "source": "label_bytes",
        "value": 460 * 1024,
        "limit": None,
        "normalized_percent": None,
    }
    assert decision["level"] == "SNAPSHOT"


@pytest.mark.parametrize("label", ["1 B", "999 KiB", "80%", "unknown", "999999999 GiB"])
def test_transcript_stat_bytes_precede_every_supplied_label(
    tmp_path: Path,
    label: str,
) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_bytes(b"")
    _truncate_file(transcript, 400 * 1024)
    decision = _hook_decision(
        {
            "usage": {
                "label": label,
            },
            "last_notified_level": "NORMAL",
            "lanes": [],
        },
        transcript_path=str(transcript),
    )

    assert decision["signal"] == {
        "kind": "bytes",
        "source": "transcript_stat_bytes",
        "value": 400 * 1024,
        "limit": None,
        "normalized_percent": None,
    }
    assert decision["level"] == "ALERT"


@pytest.mark.parametrize(
    ("usage", "expected_level"),
    [
        ({"tokens": {"used": 39, "limit": 100}}, "NORMAL"),
        ({"tokens": {"used": 40, "limit": 100}}, "ALERT"),
        ({"tokens": {"used": 44, "limit": 100}}, "ALERT"),
        ({"tokens": {"used": 45, "limit": 100}}, "SNAPSHOT"),
        ({"tokens": {"used": 79, "limit": 100}}, "SNAPSHOT"),
        ({"tokens": {"used": 80, "limit": 100}}, "CRITICAL"),
        ({"percent": 39}, "NORMAL"),
        ({"percent": 40}, "ALERT"),
        ({"percent": 44}, "ALERT"),
        ({"percent": 45}, "SNAPSHOT"),
        ({"percent": 79}, "SNAPSHOT"),
        ({"percent": 80}, "CRITICAL"),
    ],
)
def test_default_threshold_boundaries(
    usage: dict[str, Any],
    expected_level: str,
) -> None:
    decision = _hook_decision(
        {"usage": usage, "last_notified_level": "NORMAL", "lanes": []}
    )
    assert decision["level"] == expected_level


@pytest.mark.parametrize(
    ("size_kib", "expected_level"),
    [
        (399, "NORMAL"),
        (400, "ALERT"),
        (449, "ALERT"),
        (450, "SNAPSHOT"),
        (899, "SNAPSHOT"),
        (900, "CRITICAL"),
    ],
)
def test_regular_transcript_stat_boundaries_are_derived_without_reading(
    tmp_path: Path,
    size_kib: int,
    expected_level: str,
) -> None:
    transcript = tmp_path / f"transcript-{size_kib}.jsonl"
    transcript.write_bytes(b"")
    _truncate_file(transcript, size_kib * 1024)
    transcript.chmod(0)
    native = {
        "session_id": f"codex-session-stat-{size_kib}-canary",
        "transcript_path": str(transcript),
        "cwd": str(tmp_path),
        "hook_event_name": "Stop",
        "model": "gpt-5.6-sol",
        "permission_mode": "default",
        "turn_id": f"codex-turn-stat-{size_kib}-canary",
        "stop_hook_active": False,
        "last_assistant_message": "bounded assistant summary",
    }
    state = {"usage": {}, "last_notified_level": "NORMAL", "lanes": []}

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(state, separators=(",", ":")),
        payload=native,
    )

    decision = _json_stdout(result)
    assert decision["signal"] == {
        "kind": "bytes",
        "source": "transcript_stat_bytes",
        "value": size_kib * 1024,
        "limit": None,
        "normalized_percent": None,
    }
    assert decision["level"] == expected_level


@pytest.mark.parametrize(
    ("percent", "last_level", "expected_level", "notify"),
    [
        (40, "NORMAL", "ALERT", True),
        (44, "ALERT", "ALERT", False),
        (45, "ALERT", "SNAPSHOT", True),
        (79, "SNAPSHOT", "SNAPSHOT", False),
        (80, "SNAPSHOT", "CRITICAL", True),
        (95, "CRITICAL", "CRITICAL", False),
    ],
)
def test_notifications_realert_only_on_a_new_boundary(
    percent: int,
    last_level: str,
    expected_level: str,
    notify: bool,
) -> None:
    decision = _hook_decision(
        {
            "usage": {"percent": percent},
            "last_notified_level": last_level,
            "lanes": [],
        }
    )
    assert decision["level"] == expected_level
    assert decision["notify"] is notify


@pytest.mark.parametrize("status", ["READY", "BLOCKED", "RUNNING", "UNKNOWN"])
def test_every_unresolved_lane_status_forces_clear_ready_false(status: str) -> None:
    decision = _hook_decision(
        {
            "usage": {"percent": 80},
            "last_notified_level": "SNAPSHOT",
            "lanes": [_lane("CTX-ACTIVE", status=status)],
        }
    )

    assert decision["level"] == "CRITICAL"
    assert decision["clear_ready"] is False
    assert "operator" in decision["recommendation"].casefold()


def test_fifo_transcript_is_never_opened_or_read_and_fails_unknown(tmp_path: Path) -> None:
    transcript_fifo = tmp_path / "raw-transcript.fifo"
    os.mkfifo(transcript_fifo)
    native = {
        "session_id": "codex-session-fifo-canary",
        "transcript_path": str(transcript_fifo),
        "cwd": str(tmp_path),
        "hook_event_name": "Stop",
        "model": "gpt-5.6-sol",
        "permission_mode": "default",
        "turn_id": "codex-turn-fifo-canary",
        "stop_hook_active": False,
        "last_assistant_message": "bounded assistant summary",
    }

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(
            {"usage": {}, "last_notified_level": "ALERT", "lanes": []},
            separators=(",", ":"),
        ),
        payload=native,
        timeout=2.0,
    )

    decision = _json_stdout(result)
    assert decision["signal"]["source"] == "UNKNOWN"
    assert decision["level"] == "UNKNOWN"
    assert decision["clear_ready"] is False


def test_unavailable_transcript_path_fails_unknown_without_echo(tmp_path: Path) -> None:
    missing = tmp_path / "missing-session-transcript-canary.jsonl"
    native = {
        "session_id": "codex-session-missing-canary",
        "transcript_path": str(missing),
        "cwd": str(tmp_path),
        "hook_event_name": "Stop",
        "model": "gpt-5.6-sol",
        "permission_mode": "default",
        "turn_id": "codex-turn-missing-canary",
        "stop_hook_active": False,
        "last_assistant_message": "bounded assistant summary",
    }
    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(
            {"usage": {}, "last_notified_level": "NORMAL", "lanes": []},
            separators=(",", ":"),
        ),
        payload=native,
    )

    decision = _json_stdout(result)
    assert decision["level"] == "UNKNOWN"
    diagnostics = result.stdout + result.stderr
    assert str(missing).encode() not in diagnostics
    assert native["session_id"].encode() not in diagnostics


def test_transcript_stat_bytes_cannot_be_forged_in_normalized_state() -> None:
    state = {
        "usage": {"transcript_stat_bytes": 900 * 1024},
        "last_notified_level": "NORMAL",
        "lanes": [],
    }
    native = {
        "session_id": "codex-session-forged-stat-canary",
        "transcript_path": None,
        "cwd": "/workspace/HoroConsultant",
        "hook_event_name": "Stop",
        "model": "gpt-5.6-sol",
        "permission_mode": "default",
        "turn_id": "codex-turn-forged-stat-canary",
        "stop_hook_active": False,
        "last_assistant_message": "bounded assistant summary",
    }

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(state, separators=(",", ":")),
        payload=native,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert "NORMALIZED_STATE_INVALID" in _stderr(result)


def test_snapshot_writes_closed_canonical_handoff_with_authority_pointers(
    tmp_path: Path,
) -> None:
    output = tmp_path / "HANDOFF.md"
    payload = _snapshot_payload(lanes=[_lane("CTX-020-CORE", status="RUNNING")])

    result = _snapshot(output, payload)

    assert result.returncode == 0, _stderr(result)
    raw, snapshot = _decode_handoff(output)
    assert len(raw) <= 16 * 1024
    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["schema_version"] == "HandoffSnapshotV1"
    assert snapshot["authority"] == EXPECTED_POLICY["authority"]
    assert snapshot["clear_ready"] is False
    assert all(set(lane) == LANE_KEYS for lane in snapshot["lanes"])
    text = raw.decode("utf-8")
    assert "atomic_tasks.md" in text
    assert "plans/plan.md" in text
    assert "derived" in text.casefold()
    assert "non-authoritative" in text.casefold()

    validation = _invoke("validate", "--input", str(output))
    report = _json_stdout(validation)
    assert report["valid"] is True
    assert report["snapshot_schema"] == "HandoffSnapshotV1"
    assert report["bytes"] == len(raw)


@pytest.mark.parametrize("status", ["READY", "BLOCKED", "RUNNING", "UNKNOWN"])
def test_snapshot_denies_clear_for_every_unresolved_lane_status(
    tmp_path: Path,
    status: str,
) -> None:
    output = tmp_path / f"{status}.md"
    payload = _snapshot_payload(
        lanes=[_lane(f"CTX-{status}", status=status)],
        clear_ready=True,
    )

    result = _snapshot(output, payload)

    assert result.returncode == 0, _stderr(result)
    _, snapshot = _decode_handoff(output)
    assert snapshot["clear_ready"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"unexpected": "field"},
        {"schema_version": "HandoffSnapshotV0"},
        {"lanes": [{**_lane("CTX-X"), "unexpected": "field"}]},
        {"lanes": [_lane("CTX-X", status="NOT_A_STATE")]},
    ],
)
def test_snapshot_schema_is_closed_and_fails_before_output(
    tmp_path: Path,
    mutation: dict[str, Any],
) -> None:
    payload = _snapshot_payload()
    payload.update(mutation)
    output = tmp_path / "HANDOFF.md"

    result = _snapshot(output, payload)

    assert result.returncode == 2
    assert "SNAPSHOT_SCHEMA_INVALID" in _stderr(result)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_snapshot_is_canonical_deterministic_and_capped_at_16_kib(tmp_path: Path) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    payload = _snapshot_payload(lanes=[_lane("CTX-020-CORE")])
    payload["summary"] = "bounded context " * 500

    first_result = _snapshot(first, payload)
    second_result = _snapshot(second, payload)

    assert first_result.returncode == 0, _stderr(first_result)
    assert second_result.returncode == 0, _stderr(second_result)
    assert first.read_bytes() == second.read_bytes()
    assert len(first.read_bytes()) <= 16 * 1024

    oversized = tmp_path / "oversized.md"
    too_large = _snapshot_payload()
    too_large["summary"] = "bounded context " * 2000
    rejected = _snapshot(oversized, too_large)
    assert rejected.returncode == 2
    assert "HANDOFF_TOO_LARGE" in _stderr(rejected)
    assert not oversized.exists()
    assert not any(path.name.startswith(f".{oversized.name}.") for path in tmp_path.iterdir())


@pytest.mark.parametrize(
    ("case_name", "expected_error"),
    [
        ("malformed", "SNAPSHOT_SCHEMA_INVALID"),
        ("secret", "SENSITIVE_INPUT_REJECTED"),
        ("oversize", "HANDOFF_TOO_LARGE"),
    ],
)
def test_rejected_snapshot_preserves_preexisting_handoff_byte_for_byte(
    tmp_path: Path,
    case_name: str,
    expected_error: str,
) -> None:
    output = tmp_path / "HANDOFF.md"
    initial = _snapshot_payload(lanes=[_lane("CTX-EXISTING", status="RUNNING")])
    assert _snapshot(output, initial).returncode == 0
    before = output.read_bytes()
    before_inode = output.stat().st_ino

    payload = _snapshot_payload(lanes=[_lane("CTX-INCOMING")])
    if case_name == "malformed":
        payload["unexpected"] = "closed schema"
    elif case_name == "secret":
        payload["summary"] = "credential=" + "sk" + "-" + ("Q" * 64)
    else:
        payload["summary"] = "bounded oversize context " * 3000

    result = _snapshot(output, payload)

    assert result.returncode == 2
    assert expected_error in _stderr(result)
    assert result.stdout == b""
    assert output.read_bytes() == before
    assert output.stat().st_ino == before_inode
    assert _temp_artifacts(output) == []


def _bulky_lanes(prefix: str, count: int) -> list[dict[str, str]]:
    lanes: list[dict[str, str]] = []
    for index in range(count):
        lane = _lane(f"{prefix}-{index:02d}", status="BLOCKED")
        lane["summary"] = (
            f"Bounded unresolved state for {prefix}-{index:02d}; " * 8
        ).strip()
        lane["next_action"] = (
            f"Wait for the explicit dependency gate for {prefix}-{index:02d}; " * 8
        ).strip()
        lanes.append(lane)
    return lanes


def test_merge_over_cap_preserves_preexisting_handoff_and_cleans_temp(
    tmp_path: Path,
) -> None:
    output = tmp_path / "HANDOFF.md"
    initial = _snapshot_payload(lanes=_bulky_lanes("EXISTING", 14))
    initial_result = _snapshot(output, initial)
    assert initial_result.returncode == 0, _stderr(initial_result)
    before = output.read_bytes()
    assert 8 * 1024 < len(before) <= 16 * 1024
    before_inode = output.stat().st_ino

    incoming = _snapshot_payload(
        runtime="claude",
        lanes=_bulky_lanes("INCOMING", 14),
    )
    assert len(json.dumps(incoming).encode("utf-8")) < 16 * 1024
    result = _snapshot(output, incoming)

    assert result.returncode == 2
    assert "HANDOFF_TOO_LARGE" in _stderr(result)
    assert result.stdout == b""
    assert output.read_bytes() == before
    assert output.stat().st_ino == before_inode
    assert _temp_artifacts(output) == []


def test_snapshot_merges_active_lanes_without_loss_and_conflicts_fail_closed(
    tmp_path: Path,
) -> None:
    output = tmp_path / "HANDOFF.md"
    first_payload = _snapshot_payload(
        lanes=[
            _lane("CTX-020-CORE", status="RUNNING"),
            _lane("CTX-030-ADAPTERS", status="BLOCKED"),
        ]
    )
    assert _snapshot(output, first_payload).returncode == 0

    second_payload = _snapshot_payload(
        runtime="claude",
        lanes=[_lane("CTX-040-POLICY", status="READY", owner="skill_rule_owner")],
    )
    merged_result = _snapshot(output, second_payload)
    assert merged_result.returncode == 0, _stderr(merged_result)
    _, merged = _decode_handoff(output)
    assert {lane["id"] for lane in merged["lanes"]} == {
        "CTX-020-CORE",
        "CTX-030-ADAPTERS",
        "CTX-040-POLICY",
    }
    assert merged["clear_ready"] is False

    before_conflict = output.read_bytes()
    conflicting = _snapshot_payload(
        lanes=[_lane("CTX-020-CORE", status="RUNNING", owner="different-owner")]
    )
    conflict_result = _snapshot(output, conflicting)
    assert conflict_result.returncode == 2
    assert "HANDOFF_LANE_CONFLICT" in _stderr(conflict_result)
    assert output.read_bytes() == before_conflict
    assert not any(path.name.startswith(f".{output.name}.") for path in tmp_path.iterdir())


def test_concurrent_disjoint_lane_writers_preserve_the_complete_union(
    tmp_path: Path,
) -> None:
    output = tmp_path / "HANDOFF.md"
    assert _snapshot(output, _snapshot_payload()).returncode == 0
    lane_ids = [f"CTX-CONCURRENT-{index}" for index in range(6)]
    pending = [
        (
            _start_snapshot(output, payload, "--lock-timeout", "2"),
            payload,
        )
        for payload in (
            _snapshot_payload(
                runtime=("codex", "claude", "agy")[index % 3],
                lanes=[_lane(lane_id, status="RUNNING")],
            )
            for index, lane_id in enumerate(lane_ids)
        )
    ]

    results = _finish_concurrent_snapshots(pending)

    assert [result.returncode for result in results] == [0] * len(results), [
        _stderr(result) for result in results
    ]
    _, merged = _decode_handoff(output)
    assert [lane["id"] for lane in merged["lanes"]] == sorted(lane_ids)
    assert len(merged["lanes"]) == len(lane_ids)
    assert merged["clear_ready"] is False
    assert _temp_artifacts(output) == []


def test_concurrent_same_lane_conflict_has_one_winner_and_one_failure(
    tmp_path: Path,
) -> None:
    output = tmp_path / "HANDOFF.md"
    assert _snapshot(output, _snapshot_payload()).returncode == 0
    first = _snapshot_payload(
        lanes=[_lane("CTX-SAME-LANE", status="RUNNING", owner="developer-a")]
    )
    second = _snapshot_payload(
        lanes=[_lane("CTX-SAME-LANE", status="RUNNING", owner="developer-b")]
    )
    pending = [
        (_start_snapshot(output, first, "--lock-timeout", "2"), first),
        (_start_snapshot(output, second, "--lock-timeout", "2"), second),
    ]

    results = _finish_concurrent_snapshots(pending)

    assert sorted(result.returncode for result in results) == [0, 2]
    loser = next(result for result in results if result.returncode == 2)
    assert loser.stdout == b""
    assert "HANDOFF_LANE_CONFLICT" in _stderr(loser)
    _, merged = _decode_handoff(output)
    assert len(merged["lanes"]) == 1
    assert merged["lanes"][0]["id"] == "CTX-SAME-LANE"
    assert merged["lanes"][0]["owner"] in {"developer-a", "developer-b"}
    assert _temp_artifacts(output) == []


def test_dirty_paths_are_informational_and_snapshot_does_not_mutate_git(tmp_path: Path) -> None:
    before = _status_bytes()
    output = tmp_path / "HANDOFF.md"
    payload = _snapshot_payload()
    payload["dirty_paths"] = ["owned/path.py", "untracked/note.txt"]

    result = _snapshot(output, payload)

    assert result.returncode == 0, _stderr(result)
    after = _status_bytes()
    assert after == before
    _, snapshot = _decode_handoff(output)
    assert snapshot["dirty_paths"] == ["owned/path.py", "untracked/note.txt"]


SENSITIVE_LEAF_PATHS: tuple[tuple[str | int, ...], ...] = (
    ("schema_version",),
    ("created_at",),
    ("runtime",),
    ("ticket_id",),
    ("reason",),
    ("objective",),
    ("summary",),
    ("next_action",),
    ("authority", "current_state"),
    ("authority", "implementation_plan"),
    ("authority", "derived_handoff"),
    ("lanes", 0, "id"),
    ("lanes", 0, "owner"),
    ("lanes", 0, "status"),
    ("lanes", 0, "summary"),
    ("lanes", 0, "next_action"),
    ("dirty_paths", 0),
    ("risks", 0),
    ("decisions", 0),
)


def _sensitive_canaries() -> tuple[tuple[str, str], ...]:
    secret = "credential=" + "sk" + "-" + ("Qa" * 32)
    deterministic_bytes = bytes(range(33, 127))
    high_entropy = "opaque=" + base64.b64encode(deterministic_bytes).decode("ascii")
    return (("secret", secret), ("high-entropy", high_entropy))


@pytest.mark.parametrize("leaf_path", SENSITIVE_LEAF_PATHS, ids=lambda p: "-".join(map(str, p)))
@pytest.mark.parametrize(
    ("canary_kind", "canary"),
    _sensitive_canaries(),
    ids=["secret", "high-entropy"],
)
def test_recursive_sensitive_scan_covers_every_allowed_string_leaf_without_echo(
    tmp_path: Path,
    leaf_path: tuple[str | int, ...],
    canary_kind: str,
    canary: str,
) -> None:
    payload = _snapshot_payload(lanes=[_lane("CTX-SENSITIVE")])
    payload = copy.deepcopy(payload)
    _replace_leaf(payload, leaf_path, canary)
    output = tmp_path / canary_kind / "HANDOFF.md"
    output.parent.mkdir()

    result = _snapshot(output, payload)

    diagnostics = result.stdout + result.stderr
    assert result.returncode == 2
    assert result.stdout == b""
    expected_error = (
        "SNAPSHOT_SCHEMA_INVALID"
        if leaf_path in (("schema_version",), ("lanes", 0, "status"))
        else "SENSITIVE_INPUT_REJECTED"
    )
    assert expected_error in _stderr(result)
    encoded_canary = canary.encode("utf-8")
    for fragment in (encoded_canary, encoded_canary.split(b"=", 1)[-1], encoded_canary[-24:]):
        assert fragment not in diagnostics
    assert not output.exists()
    assert _temp_artifacts(output) == []


@pytest.mark.parametrize("field", ["session", "prompt", "env"])
def test_raw_session_prompt_or_environment_is_rejected_without_echo_or_write(
    tmp_path: Path,
    field: str,
) -> None:
    canary = "raw-input-canary-" + ("R" * 48)
    payload = _snapshot_payload()
    payload[field] = {"nested": [{"content": canary}]}
    output = tmp_path / field / "HANDOFF.md"
    output.parent.mkdir()

    result = _snapshot(output, payload)

    assert result.returncode == 2
    assert result.stdout == b""
    assert "SENSITIVE_INPUT_REJECTED" in _stderr(result)
    assert canary.encode("utf-8") not in result.stderr
    assert canary[-24:].encode("utf-8") not in result.stderr
    assert not output.exists()
    assert _temp_artifacts(output) == []


def test_absolute_home_path_is_rejected_without_diagnostic_echo(tmp_path: Path) -> None:
    private_path = "/Users/example/.codex/auth.json"
    payload = _snapshot_payload()
    payload["summary"] = private_path
    output = tmp_path / "HANDOFF.md"

    result = _snapshot(output, payload)

    assert result.returncode == 2
    assert "SENSITIVE_INPUT_REJECTED" in _stderr(result)
    assert private_path.encode("utf-8") not in result.stderr
    assert result.stdout == b""
    assert not output.exists()


def test_hook_recursive_sensitive_input_fails_closed_without_echo() -> None:
    canary = "credential=" + "sk" + "-" + ("HookQa" * 12)
    lane = _lane("CTX-HOOK-SENSITIVE")
    lane["next_action"] = canary
    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        "--native",
        "--state-json",
        json.dumps(
            {
                "usage": {"percent": 45},
                "last_notified_level": "ALERT",
                "lanes": [lane],
            },
            separators=(",", ":"),
        ),
        payload={
            "session_id": "codex-session-sensitive-canary",
            "transcript_path": None,
            "cwd": "/workspace/HoroConsultant",
            "hook_event_name": "Stop",
            "model": "gpt-5.6-sol",
            "permission_mode": "default",
            "turn_id": "codex-turn-sensitive-canary",
            "stop_hook_active": False,
            "last_assistant_message": "bounded assistant summary",
        },
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert "SENSITIVE_INPUT_REJECTED" in _stderr(result)
    assert canary.encode("utf-8") not in result.stderr
    assert ("sk" + "-").encode("ascii") not in result.stderr


def test_atomic_writer_uses_temp_fsync_replace_and_lock_contention_exit_3(
    tmp_path: Path,
) -> None:
    _require_entrypoint()
    source = ENTRYPOINT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    call_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            call_names.append(node.func.attr)
        elif isinstance(node.func, ast.Name):
            call_names.append(node.func.id)
    assert "fsync" in call_names
    assert "replace" in call_names
    assert "flock" in call_names
    assert "mkstemp" in call_names or "NamedTemporaryFile" in call_names
    assert source.find("os.fsync") < source.find("os.replace")

    output = tmp_path / "HANDOFF.md"
    initial = _snapshot_payload(lanes=[_lane("CTX-INITIAL", status="RUNNING")])
    assert _snapshot(output, initial).returncode == 0
    before = output.read_bytes()
    before_inode = output.stat().st_ino

    lock_path = Path(f"{output}.lock")
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        contender = _snapshot(
            output,
            _snapshot_payload(lanes=[_lane("CTX-CONTENDER")]),
            "--lock-timeout",
            "0",
        )
        assert contender.returncode == 3
        assert "HANDOFF_LOCK_CONTENDED" in _stderr(contender)
        assert contender.stdout == b""
        assert output.read_bytes() == before
        assert output.stat().st_ino == before_inode

    replacement = _snapshot(
        output,
        _snapshot_payload(lanes=[_lane("CTX-REPLACEMENT", status="BLOCKED")]),
    )
    assert replacement.returncode == 0, _stderr(replacement)
    assert output.stat().st_ino != before_inode
    raw, merged = _decode_handoff(output)
    assert raw != before
    assert {lane["id"] for lane in merged["lanes"]} == {
        "CTX-INITIAL",
        "CTX-REPLACEMENT",
    }
    assert _temp_artifacts(output) == []
    validation = _invoke("validate", "--input", str(output))
    assert _json_stdout(validation)["valid"] is True


def test_atomic_writer_runtime_trace_proves_lock_temp_fsync_replace_order(
    tmp_path: Path,
) -> None:
    _require_entrypoint()
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    trace_path = tmp_path / "atomic.trace"
    sitecustomize = probe_dir / "sitecustomize.py"
    sitecustomize.write_text(
        """
import fcntl
import os
import tempfile

_trace = os.environ["CTX_ATOMIC_TRACE"]
_real_flock = fcntl.flock
_real_fsync = os.fsync
_real_replace = os.replace
_real_mkstemp = tempfile.mkstemp
_real_named_temporary_file = tempfile.NamedTemporaryFile

def _record(operation, detail=""):
    with open(_trace, "a", encoding="utf-8") as handle:
        handle.write(f"{operation}|{detail}\\n")

def _flock(fd, operation):
    _record("flock", str(operation))
    return _real_flock(fd, operation)

def _fsync(fd):
    _record("fsync", str(fd))
    return _real_fsync(fd)

def _replace(source, destination):
    _record("replace", f"{source}|{destination}")
    return _real_replace(source, destination)

def _mkstemp(*args, **kwargs):
    fd, path = _real_mkstemp(*args, **kwargs)
    _record("temp", path)
    return fd, path

def _named_temporary_file(*args, **kwargs):
    value = _real_named_temporary_file(*args, **kwargs)
    _record("temp", value.name)
    return value

fcntl.flock = _flock
os.fsync = _fsync
os.replace = _replace
tempfile.mkstemp = _mkstemp
tempfile.NamedTemporaryFile = _named_temporary_file
""".lstrip(),
        encoding="utf-8",
    )
    output = tmp_path / "HANDOFF.md"
    environment = os.environ.copy()
    environment["CTX_ATOMIC_TRACE"] = str(trace_path)
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(probe_dir)
        if not existing_pythonpath
        else str(probe_dir) + os.pathsep + existing_pythonpath
    )
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "snapshot", "--output", str(output)],
        cwd=ROOT,
        input=json.dumps(_snapshot_payload(), separators=(",", ":")).encode("utf-8"),
        capture_output=True,
        check=False,
        timeout=5,
        env=environment,
    )

    assert result.returncode == 0, _stderr(result)
    trace = trace_path.read_text(encoding="utf-8").splitlines()
    operations = [line.split("|", 1)[0] for line in trace]
    lock_index = operations.index("flock")
    temp_index = operations.index("temp")
    fsync_index = operations.index("fsync")
    replace_index = operations.index("replace")
    assert lock_index < temp_index < fsync_index < replace_index
    replace_record = trace[replace_index].split("|", 1)[1]
    source, destination = replace_record.rsplit("|", 1)
    assert Path(source) != output
    assert Path(destination) == output
    assert Path(source).parent == output.parent
    assert not Path(source).exists()
    assert _temp_artifacts(output) == []
    assert _json_stdout(_invoke("validate", "--input", str(output)))["valid"] is True


def test_rehydrate_enforces_input_and_output_caps_and_refuses_legacy(
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "canonical.md"
    payload = _snapshot_payload(lanes=[_lane("CTX-020-CORE", status="RUNNING")])
    assert _snapshot(canonical, payload).returncode == 0

    rehydrated = _invoke(
        "rehydrate",
        "--input",
        str(canonical),
        "--max-bytes",
        str(4 * 1024),
    )
    assert rehydrated.returncode == 0, _stderr(rehydrated)
    assert 0 < len(rehydrated.stdout) <= 4 * 1024
    rehydrated_text = rehydrated.stdout.decode("utf-8")
    assert "atomic_tasks.md" in rehydrated_text
    assert "plans/plan.md" in rehydrated_text

    oversized_output_candidate = tmp_path / "oversized-output-candidate.md"
    verbose_payload = _snapshot_payload(
        lanes=[_lane("CTX-020-CORE", status="RUNNING")]
    )
    verbose_payload["summary"] = "bounded rehydration context " * 350
    verbose_snapshot = _snapshot(oversized_output_candidate, verbose_payload)
    assert verbose_snapshot.returncode == 0, _stderr(verbose_snapshot)
    oversized_output = _invoke(
        "rehydrate",
        "--input",
        str(oversized_output_candidate),
        "--max-bytes",
        str(4 * 1024),
    )
    assert oversized_output.returncode == 2
    assert oversized_output.stdout == b""
    assert "REHYDRATE_OUTPUT_TOO_LARGE" in _stderr(oversized_output)

    excessive_output_limit = _invoke(
        "rehydrate",
        "--input",
        str(canonical),
        "--max-bytes",
        str((4 * 1024) + 1),
    )
    assert excessive_output_limit.returncode == 2
    assert excessive_output_limit.stdout == b""
    assert "REHYDRATE_LIMIT_TOO_LARGE" in _stderr(excessive_output_limit)

    raw, decoded = _decode_handoff(canonical)
    oversized_decoded = copy.deepcopy(decoded)
    oversized_decoded["summary"] = "canonical bounded field " * 1500
    canonical_json = json.dumps(
        oversized_decoded,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    raw_text = raw.decode("utf-8")
    before_marker, after_start = raw_text.split(HANDOFF_START, 1)
    _, after_marker = after_start.split(HANDOFF_END, 1)
    oversized_canonical = tmp_path / "oversized-canonical.md"
    oversized_canonical.write_text(
        before_marker
        + HANDOFF_START
        + "\n"
        + canonical_json
        + "\n"
        + HANDOFF_END
        + after_marker,
        encoding="utf-8",
    )
    assert oversized_canonical.stat().st_size > 16 * 1024

    oversized_input = _invoke(
        "rehydrate",
        "--input",
        str(oversized_canonical),
        "--max-bytes",
        str(4 * 1024),
    )
    assert oversized_input.returncode == 2
    assert oversized_input.stdout == b""
    assert "HANDOFF_INPUT_TOO_LARGE" in _stderr(oversized_input)

    legacy = tmp_path / "legacy.md"
    legacy_bytes = b"# HANDOFF\n\nLegacy free-form session notes.\n"
    legacy.write_bytes(legacy_bytes)
    for operation in ("validate", "rehydrate"):
        extra_args = ["--max-bytes", str(4 * 1024)] if operation == "rehydrate" else []
        refused = _invoke(operation, "--input", str(legacy), *extra_args)
        assert refused.returncode == 2
        assert "LEGACY_HANDOFF_REFUSED" in _stderr(refused)
        assert refused.stdout == b""

    replacement = _snapshot(legacy, _snapshot_payload())
    assert replacement.returncode == 2
    assert "LEGACY_HANDOFF_REFUSED" in _stderr(replacement)
    assert legacy.read_bytes() == legacy_bytes


def test_validate_rejects_noncanonical_trailing_content(tmp_path: Path) -> None:
    output = tmp_path / "HANDOFF.md"
    assert _snapshot(output, _snapshot_payload()).returncode == 0
    original = output.read_bytes()
    output.write_bytes(original + b"unexpected trailing content\n")

    result = _invoke("validate", "--input", str(output))

    assert result.returncode == 2
    assert "HANDOFF_NONCANONICAL" in _stderr(result)


def test_no_automatic_compact_clear_reset_or_shell_feed_path() -> None:
    _require_entrypoint()
    source = ENTRYPOINT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    prohibited_calls = {
        "system",
        "popen",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "execv",
        "execve",
        "execvp",
        "execvpe",
    }
    observed: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            observed.add(node.func.attr)
        elif isinstance(node.func, ast.Name):
            observed.add(node.func.id)
    assert observed.isdisjoint(prohibited_calls)
    source_lower = source.casefold()
    for shell_feed in (
        "tmux send-keys",
        "screen -x",
        "write_stdin",
        "osascript",
        "/compact",
        "/clear",
        "/reset",
    ):
        assert shell_feed not in source_lower

    critical = _hook_decision(
        {
            "usage": {"percent": 95},
            "last_notified_level": "SNAPSHOT",
            "lanes": [],
        }
    )
    assert critical["level"] == "CRITICAL"
    assert "operator" in critical["recommendation"].casefold()
    assert "snapshot" in critical["recommendation"].casefold()
    assert critical["recommendation"].casefold().startswith("operator_")
    for automatic_action in ("/compact", "/clear", "/reset", "send-keys"):
        assert automatic_action not in critical["recommendation"].casefold()
