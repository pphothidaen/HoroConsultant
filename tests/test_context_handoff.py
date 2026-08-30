from __future__ import annotations

import ast
import base64
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "context_handoff.py"
POLICY_PATH = ROOT / ".agents" / "config" / "context_handoff_v1.json"

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
    "authority": {
        "current_state": "PROJECT_TASKS.md",
        "implementation_plan": "plans/plan.md",
        "derived_handoff": "HANDOFF.md",
    },
    "runtimes": ["codex", "claude", "agy"],
    "operations": ["hook", "snapshot", "rehydrate", "validate"],
    "operator_only_actions": ["compact", "clear", "reset"],
    "codex_trust": {
        "trusted_project_required": True,
        "untrusted_behavior": "deny",
        "bypass_allowed": False,
    },
}


def _require_entrypoint() -> None:
    assert ENTRYPOINT.is_file(), "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"


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
        "next_action": "Read PROJECT_TASKS.md and plans/plan.md before resuming.",
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


def _decode_handoff(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert text.count(HANDOFF_START) == 1
    assert text.count(HANDOFF_END) == 1
    encoded = text.split(HANDOFF_START, 1)[1].split(HANDOFF_END, 1)[0].strip()
    value = json.loads(encoded)
    assert isinstance(value, dict)
    return raw, value


def _hook_decision(payload: dict[str, Any]) -> dict[str, Any]:
    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        payload=payload,
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
    assert ENTRYPOINT.is_file(), "CONTEXT_HANDOFF_ENTRYPOINT_MISSING"


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
    raw = b'{"padding":"' + (b"x" * (64 * 1024)) + b'"}'
    assert len(raw) > 64 * 1024

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        raw_input=raw,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert "HOOK_INPUT_TOO_LARGE" in _stderr(result)


def test_signal_precedence_is_tokens_then_percent_then_stat_bytes_then_unknown() -> None:
    token_decision = _hook_decision(
        {
            "usage": {
                "tokens": {"used": 500, "limit": 1000},
                "percent": 90,
                "transcript_stat_bytes": 950 * 1024,
                "label": "999 KiB",
            },
            "last_notified_level": "NORMAL",
            "lanes": [],
        }
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
            "usage": {"percent": 80, "transcript_stat_bytes": 100 * 1024},
            "last_notified_level": "NORMAL",
            "lanes": [],
        }
    )
    assert percent_decision["signal"]["kind"] == "percent"
    assert percent_decision["signal"]["source"] == "percent"
    assert percent_decision["signal"]["normalized_percent"] == 80
    assert percent_decision["level"] == "CRITICAL"

    bytes_decision = _hook_decision(
        {
            "usage": {"transcript_stat_bytes": 450 * 1024},
            "last_notified_level": "NORMAL",
            "lanes": [],
        }
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


@pytest.mark.parametrize(
    ("usage", "expected_level"),
    [
        ({"percent": 39}, "NORMAL"),
        ({"percent": 40}, "ALERT"),
        ({"percent": 44}, "ALERT"),
        ({"percent": 45}, "SNAPSHOT"),
        ({"percent": 79}, "SNAPSHOT"),
        ({"percent": 80}, "CRITICAL"),
        ({"transcript_stat_bytes": 399 * 1024}, "NORMAL"),
        ({"transcript_stat_bytes": 400 * 1024}, "ALERT"),
        ({"transcript_stat_bytes": 449 * 1024}, "ALERT"),
        ({"transcript_stat_bytes": 450 * 1024}, "SNAPSHOT"),
        ({"transcript_stat_bytes": 899 * 1024}, "SNAPSHOT"),
        ({"transcript_stat_bytes": 900 * 1024}, "CRITICAL"),
    ],
)
def test_default_threshold_boundaries(
    usage: dict[str, int],
    expected_level: str,
) -> None:
    decision = _hook_decision(
        {"usage": usage, "last_notified_level": "NORMAL", "lanes": []}
    )
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


def test_running_or_unknown_lanes_force_clear_ready_false() -> None:
    for status in ("RUNNING", "UNKNOWN"):
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


def test_hook_never_reads_transcript_content(tmp_path: Path) -> None:
    transcript_fifo = tmp_path / "raw-transcript.fifo"
    os.mkfifo(transcript_fifo)
    payload = {
        "usage": {"percent": 45, "transcript_stat_bytes": 450 * 1024},
        "transcript_path": str(transcript_fifo),
        "last_notified_level": "ALERT",
        "lanes": [],
    }

    result = _invoke(
        "hook",
        "--runtime",
        "codex",
        "--event",
        "Stop",
        payload=payload,
        timeout=2.0,
    )

    decision = _json_stdout(result)
    assert decision["signal"]["source"] == "percent"
    assert decision["level"] == "SNAPSHOT"


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
    assert "PROJECT_TASKS.md" in text
    assert "plans/plan.md" in text
    assert "derived" in text.casefold()
    assert "non-authoritative" in text.casefold()

    validation = _invoke("validate", "--input", str(output))
    report = _json_stdout(validation)
    assert report["valid"] is True
    assert report["snapshot_schema"] == "HandoffSnapshotV1"
    assert report["bytes"] == len(raw)


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


def _sensitive_payloads() -> list[tuple[str, dict[str, Any]]]:
    secret = _snapshot_payload()
    secret["summary"] = "credential=" + "sk" + "-" + ("A" * 48)

    high_entropy = _snapshot_payload()
    deterministic_bytes = bytes(range(33, 127))
    high_entropy["summary"] = "opaque=" + base64.b64encode(deterministic_bytes).decode("ascii")

    raw_session = _snapshot_payload()
    raw_session["session"] = {"messages": [{"role": "user", "content": "raw"}]}

    raw_prompt = _snapshot_payload()
    raw_prompt["prompt"] = "verbatim user prompt must not be retained"

    raw_env = _snapshot_payload()
    raw_env["env"] = {"CONTEXT_TEST_TOKEN": "must-not-be-retained"}

    absolute_home = _snapshot_payload()
    absolute_home["summary"] = "private path /Users/example/.codex/auth.json"

    return [
        ("secret", secret),
        ("high-entropy", high_entropy),
        ("raw-session", raw_session),
        ("raw-prompt", raw_prompt),
        ("raw-env", raw_env),
        ("absolute-home", absolute_home),
    ]


@pytest.mark.parametrize(("case_name", "payload"), _sensitive_payloads())
def test_sensitive_or_raw_input_is_rejected_before_any_temp_write(
    tmp_path: Path,
    case_name: str,
    payload: dict[str, Any],
) -> None:
    case_dir = tmp_path / case_name
    case_dir.mkdir()
    output = case_dir / "HANDOFF.md"

    result = _snapshot(output, payload)

    assert result.returncode == 2
    assert "SENSITIVE_INPUT_REJECTED" in _stderr(result)
    assert result.stdout == b""
    assert list(case_dir.iterdir()) == []


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
    assert source.find("fsync") < source.find("replace")

    output = tmp_path / "HANDOFF.md"
    initial = _snapshot_payload(lanes=[_lane("CTX-INITIAL", status="RUNNING")])
    assert _snapshot(output, initial).returncode == 0
    before = output.read_bytes()

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
        assert output.read_bytes() == before


def test_rehydrate_is_bounded_and_legacy_handoffs_are_refused(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical.md"
    payload = _snapshot_payload(lanes=[_lane("CTX-020-CORE", status="RUNNING")])
    payload["summary"] = "bounded rehydration context " * 350
    assert _snapshot(canonical, payload).returncode == 0

    rehydrated = _invoke(
        "rehydrate",
        "--input",
        str(canonical),
        "--max-bytes",
        str(64 * 1024),
    )
    assert rehydrated.returncode == 0, _stderr(rehydrated)
    assert 0 < len(rehydrated.stdout) <= 4 * 1024
    rehydrated_text = rehydrated.stdout.decode("utf-8")
    assert "PROJECT_TASKS.md" in rehydrated_text
    assert "plans/plan.md" in rehydrated_text

    legacy = tmp_path / "legacy.md"
    legacy_bytes = b"# HANDOFF\n\nLegacy free-form session notes.\n"
    legacy.write_bytes(legacy_bytes)
    for operation in ("validate", "rehydrate"):
        refused = _invoke(operation, "--input", str(legacy))
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


def test_no_automatic_compact_clear_reset_or_hook_trust_bypass_path() -> None:
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

    critical = _hook_decision(
        {
            "usage": {"percent": 95},
            "last_notified_level": "SNAPSHOT",
            "lanes": [],
        }
    )
    assert critical["level"] == "CRITICAL"
    assert "operator" in critical["recommendation"].casefold()
    assert critical["recommendation"].casefold().startswith("operator_")
