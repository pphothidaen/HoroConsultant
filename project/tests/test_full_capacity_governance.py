from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sqlite3
import stat
import subprocess
import sys
import time
import types
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
AGENTS_HOOK = ROOT / ".agents" / "hooks" / "full_capacity_guard.py"
CLAUDE_HOOK = ROOT / ".claude" / "hooks" / "full_capacity_guard.py"
TEST_HARNESS = ROOT / ".agents" / "hooks" / "full_capacity_test_harness.py"
CONFIG_PATH = ROOT / ".agents" / "config" / "full_capacity_guard.v2.json"
SCHEMA_PATH = ROOT / ".agents" / "schemas" / "full-capacity-governance-v2.schema.json"
EXECUTION_TOOL_VARIANTS = (
    "Task",
    "task",
    "TASK",
    "Bash",
    "bash",
    "BASH",
    "run_command",
    "RUN_COMMAND",
    "shell",
    "SHELL",
    "terminal.exec",
    "Terminal.Exec",
    "TERMINAL.EXEC",
)


def _load_guard():
    spec = importlib.util.spec_from_file_location(
        "test_full_capacity_guard_v2", AGENTS_HOOK
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


@pytest.fixture
def guard_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    state = tmp_path / "state"
    monkeypatch.setattr(
        guard,
        "evaluate_event",
        lambda event: guard._evaluate_event_for_test(event, state),
    )
    return state


def _policy_context():
    return guard._load_policy(guard._load_config())


def _rule18(ticket_id: str, *, alias: str = "codex1", work_mode: str = "read_only"):
    policy = _policy_context()
    if alias.startswith("agy"):
        model = "gemini-3.7-flash-medium"
        effort = "medium"
    else:
        model = "gpt-5.6-luna"
        effort = "medium"
    decision = {
        "schema_version": 1,
        "ticket": ticket_id,
        "phase": "implementation",
        "scope_rank": 1,
        "complexity_rank": 1,
        "risk_rank": 1,
        "ambiguity_rank": 1,
        "evidence_burden_rank": 1,
        "quota_band": "healthy",
        "work_mode": work_mode,
        "selected_alias": alias,
        "selected_model": model,
        "selected_effort": effort,
        "rationale": "bounded Stage A fixture",
        "policy_version": policy.version,
        "planning_to_medium_confirmed": True,
        "hitl_approved": False,
    }
    validated = policy.validator.validate_dispatch_decision(decision, policy.policy)
    return dict(validated.decision), validated.digest


def _window(lease: int = 120) -> dict[str, Any]:
    started = datetime(2026, 8, 26, 0, 0, tzinfo=timezone.utc)
    deadline = started + timedelta(seconds=lease)
    return {
        "lease_seconds": lease,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "deadline_at": deadline.isoformat().replace("+00:00", "Z"),
        "termination_mode": "NATURAL_EXIT_ONLY",
        "preemption_policy": "NEVER",
        "background": False,
        "daemon": False,
    }


def _short_profile(window: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_mode": "READ_ONLY",
        "evidence_bearing": True,
        "freeze_independent": True,
        "provider_mode": "NONE",
        "provider_authorization_id": None,
        "provider_authorization_sha256": None,
        "provider_evidence_id": None,
        "provider_evidence_sha256": None,
        "lease_seconds": window["lease_seconds"],
        "started_at": window["started_at"],
        "deadline_at": window["deadline_at"],
        "natural_termination": True,
        "termination_mode": window["termination_mode"],
        "preemption_policy": window["preemption_policy"],
        "background": window["background"],
        "daemon": window["daemon"],
        "wall_clock_enforcement": "NOT_PROVEN",
        "natural_exit_enforcement": "NOT_PROVEN",
    }


def _authorization(
    *,
    session_id: str,
    ticket_id: str,
    alias: str,
    role: str,
    ownership: list[str],
    decision_sha256: str,
) -> dict[str, Any]:
    policy = _policy_context()
    value = {
        "schema_version": "capacity-provider-authorization-v2",
        "state": "STRUCTURALLY_BOUND_NOT_PROVEN",
        "authorization_id": f"auth-{ticket_id}",
        "authorization_sha256": "",
        "evidence_id": f"evidence-{ticket_id}",
        "evidence_sha256": guard._sha256({"ticket": ticket_id, "kind": "fixture"}),
        "provider": guard.ALIAS_PROVIDER[alias],
        "account_alias": alias,
        "session_id": session_id,
        "ticket_id": ticket_id,
        "role": role,
        "ownership_sha256": guard._sha256(ownership),
        "decision_sha256": decision_sha256,
        "policy_version": policy.version,
        "policy_sha256": policy.digest,
    }
    unsigned = dict(value)
    unsigned.pop("authorization_sha256")
    value["authorization_sha256"] = guard._sha256(unsigned)
    return value


def _ticket(
    ticket_id: str,
    *,
    session_id: str = "session-stage-a",
    severity: str = "HIGH",
    work_effort: str = "S",
    status: str = "READY",
    dependencies: list[str] | None = None,
    blockers: list[str] | None = None,
    owner: str = "developer",
    ownership: list[str] | None = None,
    quota_passed: bool = True,
    hitl_passed: bool = True,
    lane_type: str = "review",
    lane_role: str = "OTHER",
    required_role: str = "developer",
    alias: str = "codex1",
    decision_present: bool = True,
    authorize: bool = True,
    lease: int = 120,
) -> dict[str, Any]:
    policy = _policy_context()
    resources = ownership or [f"evidence/{ticket_id}.json"]
    window = _window(lease)
    decision: dict[str, Any] | None
    decision_sha256: str | None
    if decision_present:
        decision, decision_sha256 = _rule18(
            ticket_id,
            alias=alias,
            work_mode="mutation" if lane_type == "implementation" else "read_only",
        )
    else:
        decision = None
        decision_sha256 = None
    authorization = None
    if authorize and decision_sha256 is not None and lane_role != "SHORT_FALLBACK":
        authorization = _authorization(
            session_id=session_id,
            ticket_id=ticket_id,
            alias=alias,
            role=required_role,
            ownership=resources,
            decision_sha256=decision_sha256,
        )
    return {
        "ticket_id": ticket_id,
        "severity": severity,
        "work_effort": work_effort,
        "status": status,
        "dependencies": dependencies or [],
        "blockers": blockers or [],
        "owner": owner,
        "ownership": resources,
        "quota_passed": quota_passed,
        "hitl_passed": hitl_passed,
        "lane_type": lane_type,
        "lane_role": lane_role,
        "required_role": required_role,
        "rule18_decision": decision,
        "decision_sha256": decision_sha256,
        "policy_version": policy.version,
        "policy_sha256": policy.digest,
        "execution_window": window,
        "short_fallback": _short_profile(window)
        if lane_role == "SHORT_FALLBACK"
        else None,
        "provider_authorization": authorization,
    }


def _ownership_entry(ticket: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": ticket["ticket_id"],
        "owner": ticket["owner"],
        "ownership": list(ticket["ownership"]),
        "lane_role": ticket["lane_role"],
        "state": "ACTIVE",
    }


def _dispatch(ticket: Mapping[str, Any]) -> dict[str, Any]:
    authorization = ticket["provider_authorization"]
    if authorization is None:
        auth = (None, None, None, None)
    else:
        auth = (
            authorization["authorization_id"],
            authorization["authorization_sha256"],
            authorization["evidence_id"],
            authorization["evidence_sha256"],
        )
    execution_alias = (
        "native"
        if ticket["lane_role"] == "SHORT_FALLBACK"
        else ticket["rule18_decision"]["selected_alias"]
    )
    return {
        "ticket_id": ticket["ticket_id"],
        "lane_type": ticket["lane_type"],
        "lane_role": ticket["lane_role"],
        "required_role": ticket["required_role"],
        "execution_alias": execution_alias,
        "owner": ticket["owner"],
        "ownership": list(ticket["ownership"]),
        "decision_sha256": ticket["decision_sha256"],
        "policy_version": ticket["policy_version"],
        "policy_sha256": ticket["policy_sha256"],
        "execution_window_sha256": guard._sha256(ticket["execution_window"]),
        "short_fallback_sha256": (
            guard._sha256(ticket["short_fallback"])
            if ticket["short_fallback"] is not None
            else None
        ),
        "authorization_id": auth[0],
        "authorization_sha256": auth[1],
        "provider_evidence_id": auth[2],
        "provider_evidence_sha256": auth[3],
    }


def _handoff(
    *,
    sources: list[str] | None = None,
    source_state: str = "NONE",
    qa_ticket_id: str | None = None,
    qa_state: str = "NONE",
    running_fallbacks: list[str] | None = None,
    priority: bool = False,
) -> dict[str, Any]:
    value = {
        "source_ticket_ids": sources or [],
        "source_state": source_state,
        "qa_ticket_id": qa_ticket_id,
        "qa_state": qa_state,
        "running_fallback_ticket_ids": running_fallbacks or [],
        "qa_next_slot_priority": priority,
        "handoff_sha256": "",
    }
    unsigned = dict(value)
    unsigned.pop("handoff_sha256")
    value["handoff_sha256"] = guard._sha256(unsigned)
    return value


def _capacity_exception(
    *,
    residual_slots: int,
    expected: list[dict[str, Any]],
    capacity_snapshot_sha256: str,
    scheduler_snapshot_sha256: str,
    policy_sha256: str,
) -> dict[str, Any]:
    reasons = {"NO_USEFUL_INDEPENDENT_LANE"}
    for candidate in expected:
        reasons.update(candidate["reason_codes"])
    return {
        "type": "NO_SAFE_USEFUL_LANE",
        "residual_slots": residual_slots,
        "reasons": sorted(reasons),
        "rejected_candidates": expected,
        "evidence": {
            "rejected_candidates": len(expected),
            "capacity_snapshot_sha256": capacity_snapshot_sha256,
            "scheduler_snapshot_sha256": scheduler_snapshot_sha256,
            "policy_sha256": policy_sha256,
        },
    }


def _seal(payload: dict[str, Any]) -> None:
    event_type = guard._normalize_event_type(payload)
    record = payload["governance_record"]
    record["capacity_snapshot_sha256"] = guard._capacity_snapshot_sha256(
        payload, event_type
    )
    record["decision_sha256"] = guard._sha256(payload["decision"])
    record["record_sha256"] = ""
    unsigned = dict(record)
    unsigned.pop("record_sha256")
    record["record_sha256"] = guard._sha256(unsigned)
    payload["capacity_record_sha256"] = record["record_sha256"]


def _build_payload(
    tickets: list[dict[str, Any]],
    *,
    session_id: str = "session-stage-a",
    sequence: int = 1,
    previous_record: str = "GENESIS",
    max_slots: int = 1,
    active: list[dict[str, Any]] | None = None,
    event_type: str = "checkpoint",
    action: str | None = None,
    alias_candidates: Mapping[str, str | None] | None = None,
    handoff: dict[str, Any] | None = None,
    lifecycle_phase: str = "CHECKPOINT",
    lifecycle_status: str | None = None,
    tool_name: str | None = None,
    tool_use_id: str | None = None,
    tool_input_sha256: str | None = None,
    pre_dispatch_record_sha256: str | None = None,
    tool_result_sha256: str | None = None,
    provider_executing: bool = False,
) -> dict[str, Any]:
    config = guard._load_config()
    policy = _policy_context()
    active_entries = active or []
    reservations = [
        {
            "ticket_id": entry["ticket_id"],
            "owner": entry["owner"],
            "ownership": entry["ownership"],
        }
        for entry in active_entries
    ]
    scheduler_value = {
        "schema_version": 1,
        "tickets": [
            {
                "ticket_id": item["ticket_id"],
                "severity": item["severity"],
                "work_effort": item["work_effort"],
                "status": item["status"],
                "dependencies": item["dependencies"],
                "blockers": item["blockers"],
                "owner": item["owner"],
                "ownership": item["ownership"],
                "quota_passed": item["quota_passed"],
                "hitl_passed": item["hitl_passed"],
                "rule18_decision_valid": item["rule18_decision"] is not None,
            }
            for item in tickets
        ],
        "reservations": reservations,
    }
    scheduler = policy.scheduler.validate_snapshot(scheduler_value)
    selections = policy.scheduler.select_tickets(
        scheduler, capacity=max(1, len(tickets))
    )
    actionable = tuple(selection.ticket.ticket_id for selection in selections)
    active_slots = len(active_entries)
    idle_slots = max_slots - active_slots
    by_id = {item["ticket_id"]: item for item in tickets}
    unfinished = any(
        item["status"] not in guard.TERMINAL_TICKET_STATES for item in tickets
    )
    if action is None:
        if actionable and idle_slots > 0:
            action = (
                "REFILL"
                if event_type in {"agent_completed", "agent_failed"}
                else "DISPATCH"
            )
        elif unfinished and idle_slots > 0:
            action = guard.REPLAN_ACTION
        elif unfinished:
            action = "CONTINUE"
        else:
            action = "TERMINAL"
    dispatch_ids = (
        actionable[: min(idle_slots, len(actionable))]
        if action in guard.ACTIVE_ACTIONS
        else ()
    )
    dispatches = [_dispatch(by_id[ticket_id]) for ticket_id in dispatch_ids]
    decision = {
        "action": action,
        "recomputed": event_type in {"agent_completed", "agent_failed"},
        "dispatches": dispatches,
        "decomposition": [],
        "capacity_exception": None,
        "residual_capacity_exception": None,
    }
    if action == "DECOMPOSE_AND_DISPATCH":
        decision["decomposition"] = list(dispatch_ids)
    payload: dict[str, Any] = {
        "schema_version": guard.GOVERNANCE_SCHEMA_VERSION,
        "scope": "orchestrator",
        "event_type": event_type,
        "session_id": session_id,
        "checkpoint_sequence": sequence,
        "previous_checkpoint_sequence": sequence - 1,
        "previous_capacity_record_sha256": previous_record,
        "max_slots": max_slots,
        "active_slots": active_slots,
        "ticket_snapshot": tickets,
        "ownership_snapshot": active_entries,
        "actionable_work": list(actionable),
        "decision": decision,
        "governance_record": {},
        "capacity_record_sha256": "",
    }
    capacity_digest = guard._capacity_snapshot_sha256(payload, event_type)
    validated_tickets = guard._validate_tickets(payload, config=config, policy=policy)
    active_ids = frozenset(entry["ticket_id"] for entry in active_entries)
    reserved = tuple(
        resource for entry in active_entries for resource in entry["ownership"]
    )
    reserved_after = list(reserved)
    for ticket_id in dispatch_ids:
        reserved_after.extend(by_id[ticket_id]["ownership"])
    if action == guard.REPLAN_ACTION:
        expected = guard._expected_rejected_candidates(
            tickets=validated_tickets,
            active_ticket_ids=active_ids,
            dispatched_ids=frozenset(),
            actionable=actionable,
            reserved_resources=reserved,
        )
        decision["capacity_exception"] = _capacity_exception(
            residual_slots=idle_slots,
            expected=expected,
            capacity_snapshot_sha256=capacity_digest,
            scheduler_snapshot_sha256=scheduler.digest,
            policy_sha256=policy.digest,
        )
    elif idle_slots - len(dispatch_ids) > 0 and dispatch_ids:
        expected = guard._expected_rejected_candidates(
            tickets=validated_tickets,
            active_ticket_ids=active_ids,
            dispatched_ids=frozenset(dispatch_ids),
            actionable=actionable,
            reserved_resources=reserved_after,
        )
        decision["residual_capacity_exception"] = _capacity_exception(
            residual_slots=idle_slots - len(dispatch_ids),
            expected=expected,
            capacity_snapshot_sha256=capacity_digest,
            scheduler_snapshot_sha256=scheduler.digest,
            policy_sha256=policy.digest,
        )

    aliases = dict(alias_candidates or {"agy1": None, "agy2": None})
    qa_priority_ticket = None
    if handoff is not None and handoff["qa_next_slot_priority"]:
        qa_priority_ticket = handoff["qa_ticket_id"]
    evaluations = []
    for alias in guard.EXPECTED_ALIASES:
        candidate = aliases.get(alias)
        authorization = (
            validated_tickets[candidate].authorization if candidate else None
        )
        bindings = guard._authorization_bindings(authorization)
        evaluations.append(
            {
                "alias": alias,
                "evaluation": "EVALUATED",
                "eligibility": "NOT_ELIGIBLE",
                "dispatched": False,
                "candidate_ticket_id": candidate,
                "reason_codes": list(
                    guard._alias_reasons(
                        alias=alias,
                        candidate_id=candidate,
                        tickets=validated_tickets,
                        actionable=actionable,
                        reserved_resources=reserved,
                        qa_priority_ticket=qa_priority_ticket,
                    )
                ),
                "authorization_id": bindings[0],
                "authorization_sha256": bindings[1],
                "provider_evidence_id": bindings[2],
                "provider_evidence_sha256": bindings[3],
                "receipt": None,
            }
        )
    if lifecycle_status is None:
        if any(
            item["execution_alias"] in guard.EXPECTED_ALIASES for item in dispatches
        ):
            lifecycle_status = "BLOCKED_ALIAS_RUNTIME_PROOF"
        elif dispatches or provider_executing:
            lifecycle_status = "BLOCKED_AUTHORITATIVE_SNAPSHOT"
        elif event_type == "terminal":
            lifecycle_status = "TERMINAL"
        else:
            lifecycle_status = "OBSERVED"
    record = {
        "schema_version": guard.GOVERNANCE_SCHEMA_VERSION,
        "config_sha256": config.digest,
        "session_id": session_id,
        "sequence": sequence,
        "previous_sequence": sequence - 1,
        "previous_record_sha256": previous_record,
        "lifecycle_phase": lifecycle_phase,
        "lifecycle_status": lifecycle_status,
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "tool_input_sha256": tool_input_sha256,
        "pre_dispatch_record_sha256": pre_dispatch_record_sha256,
        "tool_result_sha256": tool_result_sha256,
        "capacity_snapshot_sha256": capacity_digest,
        "scheduler_snapshot_sha256": scheduler.digest,
        "policy_version": policy.version,
        "policy_sha256": policy.digest,
        "dependency_digests": dict(config.dependency_digests),
        "dependency_manifest_sha256": config.dependency_manifest_sha256,
        "decision_sha256": guard._sha256(decision),
        "alias_evaluations": evaluations,
        "fairness": {
            "strategy": "LEAST_RECENTLY_SERVED_AFTER_GATES",
            "last_served_sequence": {"agy1": 0, "agy2": 0},
            "eligible_order": [],
            "selected_aliases": [],
            "rule11_selection_sha256": guard._sha256(list(actionable)),
        },
        "source_qa_handoff": handoff or _handoff(),
        "proof_boundaries": {
            field: "NOT_PROVEN" for field in guard.PROOF_BOUNDARY_FIELDS
        },
        "record_sha256": "",
    }
    payload["governance_record"] = record
    _seal(payload)
    return payload


def _direct_event(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"capacity_decision": {"full_capacity": payload}}


def _validation_state(payload: Mapping[str, Any]):
    extracted, context = guard._extract_event(_direct_event(payload))
    assert extracted is not None
    return guard._validate_payload(extracted, context)


def _pre_event(
    tickets: list[dict[str, Any]],
    *,
    tool_name: str = "Task",
    tool_use_id: str = "tool-stage-a-1",
    alias_candidates: Mapping[str, str | None] | None = None,
    handoff: dict[str, Any] | None = None,
    max_slots: int = 1,
    active: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_tool_name = guard._normalized_tool_name(tool_name)
    assert normalized_tool_name is not None
    bare_input: dict[str, Any] = (
        {"prompt": "bounded Stage A fixture"}
        if normalized_tool_name == "Task"
        else {"command": "codex exec bounded"}
    )
    payload = _build_payload(
        tickets,
        event_type="dispatch",
        alias_candidates=alias_candidates,
        handoff=handoff,
        max_slots=max_slots,
        active=active,
        lifecycle_phase="PRE_DISPATCH",
        tool_name=normalized_tool_name,
        tool_use_id=tool_use_id,
        tool_input_sha256=guard._sha256(bare_input),
        provider_executing=True,
    )
    tool_input = dict(bare_input)
    tool_input["capacity_decision"] = {"full_capacity": payload}
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "tool_input": tool_input,
    }


def _run_hook(
    path: Path, event: Mapping[str, Any], state_dir: Path
) -> subprocess.CompletedProcess[str]:
    command = (
        [sys.executable, str(TEST_HARNESS), "evaluate", str(state_dir)]
        if path == AGENTS_HOOK
        else [sys.executable, str(path)]
    )
    return subprocess.run(
        command,
        cwd=ROOT,
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=False,
    )


def _violation(result: subprocess.CompletedProcess[str]) -> str:
    return json.loads(result.stdout)["reason"].rsplit(": ", 1)[-1]


def _seed_synthetic_ledger(state_directory: Path, rows: int) -> None:
    config = guard._load_config()
    connection = guard._ledger_connect(config, internal_test_directory=state_directory)
    try:
        guard._initialize_ledger(connection, config)
        session_sha = guard._sha256("synthetic-performance-session")
        previous_record = guard.GENESIS_RECORD
        previous_global = guard.GENESIS_GLOBAL
        recorded_at = guard._utc_now()
        last_record = ""
        for sequence in range(1, rows + 1):
            record_sha = guard._sha256(
                {"kind": "synthetic-capacity-record", "sequence": sequence}
            )
            material = {
                "global_sequence": sequence,
                "session_id_sha256": session_sha,
                "checkpoint_sequence": sequence,
                "previous_record_sha256": previous_record,
                "record_sha256": record_sha,
                "phase": "CHECKPOINT",
                "status": "OBSERVED",
                "tool_name_sha256": None,
                "tool_use_id_sha256": None,
                "input_record_sha256": None,
                "tool_input_sha256": None,
                "tool_result_sha256": None,
                "recorded_at": recorded_at,
                "previous_global_sha256": previous_global,
            }
            global_sha = guard._sha256(material)
            connection.execute(
                "INSERT INTO lifecycle_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    sequence,
                    session_sha,
                    sequence,
                    previous_record,
                    record_sha,
                    "CHECKPOINT",
                    "OBSERVED",
                    None,
                    None,
                    None,
                    None,
                    None,
                    recorded_at,
                    previous_global,
                    global_sha,
                ),
            )
            previous_record = record_sha
            previous_global = global_sha
            last_record = record_sha
        connection.execute(
            "INSERT INTO session_heads VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_sha,
                rows,
                last_record,
                "CHECKPOINT",
                "OBSERVED",
                None,
                None,
                recorded_at,
            ),
        )
        connection.execute(
            "UPDATE ledger_meta SET global_sequence = ?, record_count = ?, "
            "session_count = 1, global_head_sha256 = ?, first_recorded_at = ?, "
            "last_recorded_at = ? WHERE singleton = 1",
            (rows, rows, previous_global, recorded_at, recorded_at),
        )
        connection.execute("COMMIT")
    finally:
        connection.close()


def test_unrelated_events_pass_and_execution_capable_events_require_envelopes(
    guard_context: Path,
) -> None:
    assert (
        guard.evaluate_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file": "x"},
            }
        )
        is None
    )
    for command in ("git status --short", "echo bounded-check", "echo codex"):
        assert (
            guard.evaluate_event(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "tool-shell-envelope-required",
                    "tool_input": {"command": command},
                }
            )
            == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"
        )
    assert (
        guard.evaluate_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Task",
                "tool_use_id": "tool-missing",
                "tool_input": {"prompt": "run child"},
            }
        )
        == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"
    )
    assert (
        guard.evaluate_event(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_use_id": "tool-missing-bash",
                "tool_input": {"command": "agy run"},
            }
        )
        == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"
    )
    for tool_name, command in (
        ("Bash", "'/usr/local/bin/agy' run"),
        ("Bash", "python3 scripts/multiagent_prompt_command.py --execute"),
        ("Bash", "git status && codex exec bounded"),
        ("terminal.exec", "bash -lc 'env MODE=test /opt/agy run'"),
    ):
        assert (
            guard.evaluate_event(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": tool_name,
                    "tool_use_id": f"tool-provider-{tool_name}",
                    "tool_input": {"command": command},
                }
            )
            == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"
        )


@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize("tool_name", ["Bash", "run_command", "shell", "terminal.exec"])
@pytest.mark.parametrize(
    "command",
    [
        "echo codex",
        "printf '%s' agy1",
        "rg multiagent_prompt_command.py",
        "echo safe; true",
        "echo safe && true",
        "echo $CAPACITY_COMMAND",
        "echo $(whoami)",
        "echo `whoami`",
        "ls *.py",
        "printf safe\nuname -a",
        "sh -c 'echo safe'",
        "bash -lc 'echo safe'",
        "eval 'echo safe'",
        "xargs echo safe",
        "find . -exec echo {} ;",
        "make test",
        "python -m pytest",
        "python -c 'print(1)'",
        "node -e 'console.log(1)'",
        "ruby -e 'puts 1'",
        "perl -e 'print 1'",
        "uv run pytest",
        "poetry run pytest",
        "env TOOL=codex $TOOL exec",
        "cat README.md",
        "echo 'unterminated",
    ],
)
def test_suspicious_or_unproven_shell_commands_require_both_hook_envelopes(
    guard_context: Path, hook_name: str, tool_name: str, command: str
) -> None:
    event = {
        "hook_event_name": hook_name,
        "tool_name": tool_name,
        "tool_use_id": "tool-conservative-envelope",
        "tool_input": {"command": command},
    }
    if hook_name == "PostToolUse":
        event["tool_response"] = {"result": "not inspected"}
    assert guard.evaluate_event(event) == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"


@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize("tool_name", ["Bash", "run_command", "shell", "terminal.exec"])
@pytest.mark.parametrize(
    "command",
    [
        "pwd",
        "/bin/pwd -P",
        "git status",
        "git status --short --branch",
        "echo bounded-check",
        "printf '%s\\n' bounded-check",
        "ls -la",
        "uname -a",
        "whoami",
    ],
)
def test_all_simple_shell_commands_require_both_hook_envelopes(
    guard_context: Path, hook_name: str, tool_name: str, command: str
) -> None:
    event = {
        "hook_event_name": hook_name,
        "tool_name": tool_name,
        "tool_use_id": "tool-simple-envelope-required",
        "tool_input": {"command": command},
    }
    if hook_name == "PostToolUse":
        event["tool_response"] = {"result": "not inspected"}
    assert guard.evaluate_event(event) == "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize(
    "command",
    [
        "pwd",
        "echo bounded-check",
        "git status --short",
        "/bin/pwd -P",
        "sh -c 'echo safe'",
        "bash -lc 'echo safe'",
        "eval 'echo safe'",
        "xargs echo safe",
        "find . -exec echo {} ;",
        "python -m pytest",
    ],
)
def test_both_registered_hooks_require_pre_and_post_shell_envelopes(
    tmp_path: Path, hook_path: Path, hook_name: str, command: str
) -> None:
    event = {
        "hook_event_name": hook_name,
        "tool_name": "Bash",
        "tool_use_id": "tool-both-hooks-envelope-required",
        "tool_input": {"command": command},
    }
    if hook_name == "PostToolUse":
        event["tool_response"] = {"result": "not inspected"}
    result = _run_hook(hook_path, event, tmp_path / hook_path.parent.name)
    assert result.returncode == 2
    assert "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED" in result.stdout


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize("shape", ["top", "nested"])
@pytest.mark.parametrize("tool_name", EXECUTION_TOOL_VARIANTS)
def test_all_execution_aliases_and_casing_require_envelopes_in_both_hooks(
    tmp_path: Path,
    hook_path: Path,
    hook_name: str,
    shape: str,
    tool_name: str,
) -> None:
    normalized = guard._normalized_tool_name(tool_name)
    tool_input = (
        {"prompt": "bounded child"} if normalized == "Task" else {"command": "pwd"}
    )
    event: dict[str, Any] = {
        "hook_event_name": hook_name,
        "tool_use_id": "tool-alias-envelope-required",
    }
    if shape == "top":
        event.update({"tool_name": tool_name, "tool_input": tool_input})
        if hook_name == "PostToolUse":
            event["tool_response"] = {"result": "not inspected"}
    else:
        event["toolCall"] = {"name": tool_name, "args": tool_input}
        if hook_name == "PostToolUse":
            event["toolResult"] = {"result": "not inspected"}
    result = _run_hook(
        hook_path,
        event,
        tmp_path / f"{hook_path.parent.name}-{shape}-{tool_name.casefold()}",
    )
    assert result.returncode == 2
    assert "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED" in result.stdout


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize(
    ("top_name", "nested_name", "tool_input"),
    [
        ("Task", "tAsK", {"prompt": "bounded child"}),
        ("Bash", "bAsH", {"command": "pwd"}),
        ("run_command", "RUN_COMMAND", {"command": "pwd"}),
        ("shell", "SHELL", {"command": "pwd"}),
        ("Terminal.Exec", "terminal.exec", {"command": "pwd"}),
    ],
)
def test_equivalent_dual_execution_shapes_reach_envelope_gate(
    tmp_path: Path,
    hook_path: Path,
    hook_name: str,
    top_name: str,
    nested_name: str,
    tool_input: dict[str, Any],
) -> None:
    event = {
        "hook_event_name": hook_name,
        "tool_use_id": "tool-equivalent-dual",
        "tool_name": top_name,
        "tool_input": dict(tool_input),
        "toolCall": {"name": nested_name, "args": dict(reversed(tool_input.items()))},
    }
    if hook_name == "PostToolUse":
        event["tool_response"] = {"result": "same", "code": 0}
        event["toolResult"] = {"code": 0, "result": "same"}
    result = _run_hook(hook_path, event, tmp_path / hook_path.parent.name)
    assert result.returncode == 2
    assert "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED" in result.stdout


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize("shape", ["top", "nested", "dual"])
def test_unknown_tools_pass_through_both_hooks(
    tmp_path: Path, hook_path: Path, hook_name: str, shape: str
) -> None:
    tool_input = {"query": "content-free-unknown-tool"}
    event: dict[str, Any] = {
        "hook_event_name": hook_name,
        "tool_use_id": "tool-unknown-pass-through",
    }
    if shape in {"top", "dual"}:
        event.update({"tool_name": "UnknownTool", "tool_input": dict(tool_input)})
    if shape in {"nested", "dual"}:
        event["toolCall"] = {"name": "UnknownTool", "args": dict(tool_input)}
    if hook_name == "PostToolUse":
        if shape in {"top", "dual"}:
            event["tool_response"] = {"result": "same"}
        if shape in {"nested", "dual"}:
            event["toolResult"] = {"result": "same"}
    result = _run_hook(hook_path, event, tmp_path / hook_path.parent.name)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
@pytest.mark.parametrize("hook_name", ["PreToolUse", "PostToolUse"])
@pytest.mark.parametrize(
    "event",
    [
        {
            "tool_name": "Read",
            "tool_input": {"marker": "conflicting-name-marker"},
            "toolCall": {
                "name": "Bash",
                "args": {"marker": "conflicting-name-marker"},
            },
        },
        {
            "tool_name": "Bash",
            "tool_input": {"marker": "conflicting-input-left"},
            "toolCall": {
                "name": "bAsH",
                "args": {"marker": "conflicting-input-right"},
            },
        },
        {
            "tool_name": "Read",
            "tool_input": {"marker": "partial-dual-marker"},
            "toolCall": {"name": "Read"},
        },
    ],
)
def test_conflicting_or_partial_dual_tool_shapes_fail_content_free(
    tmp_path: Path,
    hook_path: Path,
    hook_name: str,
    event: dict[str, Any],
) -> None:
    value = {
        "hook_event_name": hook_name,
        "tool_use_id": "tool-envelope-conflict",
        **event,
    }
    if hook_name == "PostToolUse":
        value["tool_response"] = {"result": "same"}
        value["toolResult"] = {"result": "same"}
    result = _run_hook(hook_path, value, tmp_path / hook_path.parent.name)
    assert result.returncode == 2
    assert "CAPACITY_TOOL_ENVELOPE_CONFLICT" in result.stdout
    assert "marker" not in result.stdout


@pytest.mark.parametrize("hook_path", [AGENTS_HOOK, CLAUDE_HOOK])
def test_conflicting_dual_post_responses_fail_before_unknown_tool_pass_through(
    tmp_path: Path, hook_path: Path
) -> None:
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "UnknownTool",
        "tool_input": {"query": "response-conflict-input-marker"},
        "toolCall": {
            "name": "UnknownTool",
            "args": {"query": "response-conflict-input-marker"},
        },
        "tool_response": {"result": "response-conflict-left-marker"},
        "toolResult": {"result": "response-conflict-right-marker"},
        "tool_use_id": "tool-response-conflict",
    }
    result = _run_hook(hook_path, event, tmp_path / hook_path.parent.name)
    assert result.returncode == 2
    assert "CAPACITY_TOOL_ENVELOPE_CONFLICT" in result.stdout
    assert "response-conflict" not in result.stdout


def test_exact_no_safe_exception_and_cross_process_replay_guard(tmp_path: Path) -> None:
    ticket = _ticket("TICKET-BLOCKED", decision_present=False, authorize=False)
    payload = _build_payload([ticket])
    assert payload["decision"]["capacity_exception"]["type"] == "NO_SAFE_USEFUL_LANE"
    assert payload["decision"]["capacity_exception"]["rejected_candidates"] == [
        {
            "ticket_id": "TICKET-BLOCKED",
            "reason_codes": ["INVALID_RULE18_DECISION", "NOT_SELECTED_BY_RULE11"],
        }
    ]
    event = _direct_event(payload)
    state = tmp_path / "state"
    first = _run_hook(AGENTS_HOOK, event, state)
    assert first.returncode == 0, first.stdout + first.stderr
    second = _run_hook(AGENTS_HOOK, event, state)
    assert second.returncode == 2
    assert _violation(second) == "CAPACITY_CHECKPOINT_STALE_OR_REPLAYED"
    assert stat.S_IMODE(state.stat().st_mode) == 0o700
    assert stat.S_IMODE((state / "lifecycle.sqlite3").stat().st_mode) == 0o600


def test_rule11_uses_severity_effort_ascii_and_rejects_nonprefix(
    guard_context: Path,
) -> None:
    tickets = [
        _ticket("TICKET-Z", severity="CRITICAL", work_effort="S"),
        _ticket("TICKET-B", severity="CRITICAL", work_effort="XS"),
        _ticket("TICKET-A", severity="CRITICAL", work_effort="XS"),
        _ticket("TICKET-HIGH", severity="HIGH", work_effort="XS"),
    ]
    payload = _build_payload(tickets, max_slots=2)
    assert payload["actionable_work"] == [
        "TICKET-A",
        "TICKET-B",
        "TICKET-Z",
        "TICKET-HIGH",
    ]
    payload["decision"]["dispatches"].reverse()
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload)) == "CAPACITY_RULE11_ORDER_INVALID"
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda payload: payload["ticket_snapshot"][0].update({"unknown": True}),
            "CAPACITY_TICKET_SNAPSHOT_INVALID",
        ),
        (
            lambda payload: payload["decision"].update({"cancel": False}),
            "CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN",
        ),
        (
            lambda payload: payload["governance_record"].update({"unknown": True}),
            "CAPACITY_GOVERNANCE_RECORD_INVALID",
        ),
        (
            lambda payload: payload["ticket_snapshot"][0].update(
                {"rule11_passed": True}
            ),
            "CAPACITY_TICKET_SNAPSHOT_INVALID",
        ),
        (
            lambda payload: payload["ticket_snapshot"][0].update(
                {"rule18_passed": True}
            ),
            "CAPACITY_TICKET_SNAPSHOT_INVALID",
        ),
        (
            lambda payload: payload.update({"snapshot_complete": True}),
            "CAPACITY_PAYLOAD_SCHEMA_INVALID",
        ),
        (
            lambda payload: payload["governance_record"].update(
                {"proof_override": True}
            ),
            "CAPACITY_GOVERNANCE_RECORD_INVALID",
        ),
        (
            lambda payload: payload["governance_record"]["alias_evaluations"][0].update(
                {"runtime_success": True}
            ),
            "CAPACITY_ALIAS_EVALUATIONS_INVALID",
        ),
        (
            lambda payload: payload["governance_record"]["alias_evaluations"][0].update(
                {"alias": "agy3"}
            ),
            "CAPACITY_ALIAS_EVALUATIONS_INVALID",
        ),
    ],
)
def test_closed_schemas_and_forbidden_controls(
    guard_context: Path, mutation, expected: str
) -> None:
    payload = _build_payload(
        [_ticket("TICKET-CLOSED", decision_present=False, authorize=False)]
    )
    mutation(payload)
    _seal(payload)
    assert guard.evaluate_event(_direct_event(payload)) == expected


def test_complete_rule18_and_policy_binding_are_authoritative(
    guard_context: Path,
) -> None:
    payload = _build_payload([_ticket("TICKET-R18")])
    payload["ticket_snapshot"][0]["rule18_decision"]["unknown"] = True
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_RULE18_DECISION_INVALID"
    )

    payload = _build_payload([_ticket("TICKET-POLICY")])
    payload["ticket_snapshot"][0]["policy_sha256"] = "0" * 64
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_POLICY_BINDING_INVALID"
    )


def test_alias_reasons_are_exact_sorted_and_positive_claims_fail_closed(
    guard_context: Path,
) -> None:
    payload = _build_payload(
        [_ticket("TICKET-ALIAS", decision_present=False, authorize=False)]
    )
    entry = payload["governance_record"]["alias_evaluations"][0]
    assert entry["reason_codes"] == [
        "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE",
        "NO_CANDIDATE_TICKET",
    ]
    entry["reason_codes"].pop()
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload)) == "CAPACITY_ALIAS_REASONS_INVALID"
    )

    payload = _build_payload(
        [_ticket("TICKET-ALIAS-2", decision_present=False, authorize=False)]
    )
    entry = payload["governance_record"]["alias_evaluations"][0]
    entry["eligibility"] = "ELIGIBLE"
    entry["receipt"] = {"caller_created": True}
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"
    )


def test_alias_reasons_include_dependency_and_selected_ownership_gates(
    guard_context: Path,
) -> None:
    dependency = _ticket("TICKET-DEPENDENCY", severity="CRITICAL", work_effort="XS")
    dependent = _ticket(
        "TICKET-DEPENDENT",
        dependencies=["TICKET-DEPENDENCY"],
        alias="agy1",
    )
    payload = _build_payload(
        [dependency, dependent],
        max_slots=2,
        alias_candidates={"agy1": "TICKET-DEPENDENT", "agy2": None},
    )
    assert payload["governance_record"]["alias_evaluations"][0]["reason_codes"] == [
        "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE",
        "DEPENDENCY_BLOCKED",
        "NOT_SELECTED_BY_RULE11",
    ]
    assert guard.evaluate_event(_direct_event(payload)) == (
        "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    )

    selected = _ticket(
        "TICKET-SELECTED",
        session_id="session-conflict",
        severity="CRITICAL",
        work_effort="XS",
        ownership=["src/shared"],
    )
    conflicting = _ticket(
        "TICKET-CONFLICTING",
        session_id="session-conflict",
        alias="agy1",
        ownership=["src/shared/file.py"],
    )
    payload = _build_payload(
        [selected, conflicting],
        session_id="session-conflict",
        max_slots=2,
        alias_candidates={"agy1": "TICKET-CONFLICTING", "agy2": None},
    )
    assert payload["actionable_work"] == ["TICKET-SELECTED"]
    assert payload["governance_record"]["alias_evaluations"][0]["reason_codes"] == [
        "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE",
        "NOT_SELECTED_BY_RULE11",
        "OWNERSHIP_CONFLICT",
    ]
    assert guard.evaluate_event(_direct_event(payload)) == (
        "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    )


def test_positive_agy_and_other_provider_dispatches_are_disabled(
    tmp_path: Path,
) -> None:
    agy_ticket = _ticket("TICKET-AGY", alias="agy1")
    agy_event = _pre_event(
        [agy_ticket], alias_candidates={"agy1": "TICKET-AGY", "agy2": None}
    )
    agy_result = _run_hook(AGENTS_HOOK, agy_event, tmp_path / "agy-state")
    assert agy_result.returncode == 2
    assert _violation(agy_result) == "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"
    evaluation = agy_event["tool_input"]["capacity_decision"]["full_capacity"][
        "governance_record"
    ]["alias_evaluations"][0]
    assert evaluation["reason_codes"] == ["CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"]
    assert evaluation["receipt"] is None

    codex_event = _pre_event([_ticket("TICKET-CODEX")])
    codex_result = _run_hook(AGENTS_HOOK, codex_event, tmp_path / "codex-state")
    assert codex_result.returncode == 2
    assert _violation(codex_result) == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"


@pytest.mark.parametrize(
    ("tool_name", "nested_name"),
    [
        ("bAsH", "Bash"),
        ("RUN_COMMAND", "run_command"),
        ("Shell", "SHELL"),
        ("Terminal.Exec", "terminal.exec"),
    ],
)
@pytest.mark.parametrize("shape", ["top", "nested", "dual"])
def test_governed_shell_records_still_block_until_authoritative_snapshot(
    guard_context: Path, tool_name: str, nested_name: str, shape: str
) -> None:
    event = _pre_event(
        [_ticket(f"TICKET-GOVERNED-{tool_name.replace('.', '-').upper()}")],
        tool_name=tool_name,
        tool_use_id=f"tool-governed-{tool_name.replace('.', '-')}",
    )
    if shape in {"nested", "dual"}:
        event["toolCall"] = {
            "name": nested_name,
            "args": dict(event["tool_input"]),
        }
    if shape == "nested":
        event.pop("tool_name")
        event.pop("tool_input")
    assert guard.evaluate_event(event) == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"


def test_snapshot_and_runtime_proof_remain_structural_not_proven(
    guard_context: Path,
) -> None:
    payload = _build_payload([_ticket("TICKET-SNAPSHOT")])
    payload["actionable_work"] = []
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_ACTIONABLE_WORK_INCOMPLETE"
    )

    payload = _build_payload(
        [_ticket("TICKET-PROOF", decision_present=False, authorize=False)],
        session_id="session-proof",
    )
    payload["governance_record"]["proof_boundaries"]["authoritative_snapshot"] = (
        "PROVEN"
    )
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_RUNTIME_PROOF_OVERCLAIM"
    )

    payload = _build_payload(
        [_ticket("TICKET-EVENT", decision_present=False, authorize=False)],
        session_id="session-event",
    )
    payload["event_type"] = "provider_completed"
    assert guard.evaluate_event(_direct_event(payload)) == "CAPACITY_EVENT_INVALID"


def test_provider_authorization_and_evidence_are_bound(guard_context: Path) -> None:
    event = _pre_event([_ticket("TICKET-AUTH")])
    payload = event["tool_input"]["capacity_decision"]["full_capacity"]
    payload["ticket_snapshot"][0]["provider_authorization"]["evidence_sha256"] = (
        "0" * 64
    )
    assert guard.evaluate_event(event) == "CAPACITY_PROVIDER_AUTHORIZATION_INVALID"

    event = _pre_event([_ticket("TICKET-AUTH-ALIAS")])
    payload = event["tool_input"]["capacity_decision"]["full_capacity"]
    authorization = payload["ticket_snapshot"][0]["provider_authorization"]
    authorization["account_alias"] = "agy1"
    authorization["provider"] = "agy"
    unsigned = dict(authorization)
    unsigned.pop("authorization_sha256")
    authorization["authorization_sha256"] = guard._sha256(unsigned)
    assert guard.evaluate_event(event) == "CAPACITY_PROVIDER_AUTHORIZATION_INVALID"

    event = _pre_event([_ticket("TICKET-AUTH-DISPATCH")])
    payload = event["tool_input"]["capacity_decision"]["full_capacity"]
    authorization = payload["ticket_snapshot"][0]["provider_authorization"]
    authorization["authorization_id"] = "auth-rebound"
    unsigned = dict(authorization)
    unsigned.pop("authorization_sha256")
    authorization["authorization_sha256"] = guard._sha256(unsigned)
    _seal(payload)
    assert guard.evaluate_event(event) == "CAPACITY_DISPATCH_BINDING_INVALID"


def test_alias_evaluation_binds_authorization_and_evidence_ids(
    guard_context: Path,
) -> None:
    ticket = _ticket("TICKET-AUTH-EVALUATION", alias="agy1")
    event = _pre_event(
        [ticket],
        alias_candidates={"agy1": "TICKET-AUTH-EVALUATION", "agy2": None},
    )
    payload = event["tool_input"]["capacity_decision"]["full_capacity"]
    authorization = payload["ticket_snapshot"][0]["provider_authorization"]
    authorization["evidence_id"] = "evidence-rebound"
    unsigned = dict(authorization)
    unsigned.pop("authorization_sha256")
    authorization["authorization_sha256"] = guard._sha256(unsigned)
    dispatch = payload["decision"]["dispatches"][0]
    dispatch["authorization_sha256"] = authorization["authorization_sha256"]
    dispatch["provider_evidence_id"] = authorization["evidence_id"]
    _seal(payload)
    assert guard.evaluate_event(event) == "CAPACITY_ALIAS_BINDING_INVALID"


def test_short_fallback_bounds_and_natural_exit_only(guard_context: Path) -> None:
    short = _ticket(
        "TICKET-SHORT",
        lane_type="fallback",
        lane_role="SHORT_FALLBACK",
        required_role="qa_tester",
        authorize=False,
    )
    event = _pre_event([short])
    assert guard.evaluate_event(event) == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"

    too_long_event = _pre_event(
        [
            _ticket(
                "TICKET-LONG",
                lane_type="fallback",
                lane_role="SHORT_FALLBACK",
                required_role="qa_tester",
                authorize=False,
            )
        ]
    )
    too_long_payload = too_long_event["tool_input"]["capacity_decision"][
        "full_capacity"
    ]
    too_long = too_long_payload["ticket_snapshot"][0]
    too_long["execution_window"]["lease_seconds"] = 301
    too_long["execution_window"]["deadline_at"] = "2026-08-26T00:05:01Z"
    too_long["short_fallback"]["lease_seconds"] = 301
    too_long["short_fallback"]["deadline_at"] = "2026-08-26T00:05:01Z"
    too_long_payload["decision"]["dispatches"][0]["execution_window_sha256"] = (
        guard._sha256(too_long["execution_window"])
    )
    too_long_payload["decision"]["dispatches"][0]["short_fallback_sha256"] = (
        guard._sha256(too_long["short_fallback"])
    )
    _seal(too_long_payload)
    assert (
        guard.evaluate_event(too_long_event) == "CAPACITY_SHORT_FALLBACK_LEASE_INVALID"
    )

    deadline_event = _pre_event(
        [
            _ticket(
                "TICKET-DEADLINE",
                lane_type="fallback",
                lane_role="SHORT_FALLBACK",
                required_role="qa_tester",
                authorize=False,
            )
        ]
    )
    deadline_payload = deadline_event["tool_input"]["capacity_decision"][
        "full_capacity"
    ]
    deadline_ticket = deadline_payload["ticket_snapshot"][0]
    deadline_ticket["execution_window"]["deadline_at"] = "2026-08-26T00:03:00Z"
    deadline_payload["decision"]["dispatches"][0]["execution_window_sha256"] = (
        guard._sha256(deadline_ticket["execution_window"])
    )
    _seal(deadline_payload)
    assert guard.evaluate_event(deadline_event) == "CAPACITY_EXECUTION_WINDOW_INVALID"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("termination_mode", "FORCED"),
        ("preemption_policy", "ON_QA_READY"),
        ("background", True),
        ("daemon", True),
    ],
)
def test_short_fallback_rejects_forced_or_background_execution(
    guard_context: Path, field: str, value: object
) -> None:
    event = _pre_event(
        [
            _ticket(
                f"TICKET-SHORT-{field.upper()}",
                lane_type="fallback",
                lane_role="SHORT_FALLBACK",
                required_role="qa_tester",
                authorize=False,
            )
        ]
    )
    payload = event["tool_input"]["capacity_decision"]["full_capacity"]
    payload["ticket_snapshot"][0]["execution_window"][field] = value
    _seal(payload)
    assert guard.evaluate_event(event) == "CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN"


@pytest.mark.parametrize("key", sorted(guard.FORBIDDEN_CONTROL_KEYS))
def test_every_cancellation_or_preemption_control_is_rejected(
    guard_context: Path, key: str
) -> None:
    payload = _build_payload(
        [
            _ticket(
                f"TICKET-CONTROL-{key.upper()}", decision_present=False, authorize=False
            )
        ]
    )
    payload["ticket_snapshot"][0]["execution_window"][key] = False
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN"
    )


def test_blocked_pre_dispatch_cannot_be_forged_into_post_result(tmp_path: Path) -> None:
    pre = _pre_event([_ticket("TICKET-LIFECYCLE")], tool_use_id="tool-lifecycle")
    state = tmp_path / "state"
    pre_result = _run_hook(AGENTS_HOOK, pre, state)
    assert _violation(pre_result) == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    pre_payload = pre["tool_input"]["capacity_decision"]["full_capacity"]
    terminal_ticket = _ticket("TICKET-LIFECYCLE", status="DONE")
    bare_input = {"prompt": "bounded Stage A fixture"}
    bare_result = {"result": "done"}
    post_payload = _build_payload(
        [terminal_ticket],
        sequence=2,
        previous_record=pre_payload["capacity_record_sha256"],
        event_type="agent_completed",
        lifecycle_phase="POST_RESULT",
        lifecycle_status="BLOCKED_AUTHORITATIVE_SNAPSHOT",
        tool_name="Task",
        tool_use_id="tool-lifecycle",
        tool_input_sha256=guard._sha256(bare_input),
        pre_dispatch_record_sha256=pre_payload["capacity_record_sha256"],
        tool_result_sha256=guard._sha256(bare_result),
        provider_executing=True,
    )
    tool_input = dict(bare_input)
    tool_input["capacity_decision"] = {"full_capacity": pre_payload}
    tool_response = dict(bare_result)
    tool_response["capacity_decision"] = {"full_capacity": post_payload}
    post = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Task",
        "tool_use_id": "tool-lifecycle",
        "tool_input": tool_input,
        "tool_response": tool_response,
    }
    result = _run_hook(AGENTS_HOOK, post, state)
    assert result.returncode == 2
    assert _violation(result) == "CAPACITY_LIFECYCLE_OUT_OF_ORDER"


def test_post_result_binds_exact_tool_input_and_pre_record(guard_context: Path) -> None:
    pre = _pre_event([_ticket("TICKET-POST-BIND")], tool_use_id="tool-post-bind")
    pre_payload = pre["tool_input"]["capacity_decision"]["full_capacity"]
    bare_input = {"prompt": "bounded Stage A fixture"}
    bare_result = {"result": "done"}
    post_payload = _build_payload(
        [_ticket("TICKET-POST-BIND", status="DONE")],
        sequence=2,
        previous_record=pre_payload["capacity_record_sha256"],
        event_type="agent_completed",
        lifecycle_phase="POST_RESULT",
        lifecycle_status="BLOCKED_AUTHORITATIVE_SNAPSHOT",
        tool_name="Task",
        tool_use_id="tool-post-bind",
        tool_input_sha256="0" * 64,
        pre_dispatch_record_sha256=pre_payload["capacity_record_sha256"],
        tool_result_sha256=guard._sha256(bare_result),
        provider_executing=True,
    )
    tool_input = dict(bare_input)
    tool_input["capacity_decision"] = {"full_capacity": pre_payload}
    tool_response = dict(bare_result)
    tool_response["capacity_decision"] = {"full_capacity": post_payload}
    post = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Task",
        "tool_use_id": "tool-post-bind",
        "tool_input": tool_input,
        "tool_response": tool_response,
    }
    assert guard.evaluate_event(post) == "CAPACITY_LIFECYCLE_BINDING_INVALID"


def test_sqlite_detects_anchored_deletion_and_trigger_tamper(tmp_path: Path) -> None:
    first = _build_payload(
        [_ticket("TICKET-LEDGER", decision_present=False, authorize=False)]
    )
    state = tmp_path / "state"
    assert _run_hook(AGENTS_HOOK, _direct_event(first), state).returncode == 0
    database = state / "lifecycle.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER lifecycle_records_no_delete")
        connection.execute("DELETE FROM lifecycle_records")
        connection.commit()
    second = _build_payload(
        [_ticket("TICKET-LEDGER", decision_present=False, authorize=False)],
        sequence=2,
        previous_record=first["capacity_record_sha256"],
    )
    result = _run_hook(AGENTS_HOOK, _direct_event(second), state)
    assert result.returncode == 2
    assert _violation(result) == "CAPACITY_LEDGER_TAMPER_DETECTED"


def test_sqlite_path_rejects_symlinks_and_stores_no_raw_identifiers(
    tmp_path: Path,
) -> None:
    payload = _build_payload(
        [_ticket("TICKET-CONTENT-FREE", decision_present=False, authorize=False)],
        session_id="session-content-free",
    )
    state = tmp_path / "state"
    result = _run_hook(AGENTS_HOOK, _direct_event(payload), state)
    assert result.returncode == 0, result.stdout + result.stderr
    database_bytes = (state / "lifecycle.sqlite3").read_bytes()
    assert b"session-content-free" not in database_bytes
    assert b"TICKET-CONTENT-FREE" not in database_bytes

    target = tmp_path / "real-state"
    target.mkdir(mode=0o700)
    symlink = tmp_path / "linked-state"
    symlink.symlink_to(target, target_is_directory=True)
    linked = _run_hook(AGENTS_HOOK, _direct_event(payload), symlink)
    assert linked.returncode == 2
    assert _violation(linked) == "CAPACITY_LEDGER_PATH_INVALID"


def test_offline_full_audit_reconciles_chain_and_detects_old_record_tamper(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state"
    for session_id, ticket_id in (
        ("session-audit-a", "TICKET-AUDIT-A"),
        ("session-audit-b", "TICKET-AUDIT-B"),
    ):
        payload = _build_payload(
            [_ticket(ticket_id, decision_present=False, authorize=False)],
            session_id=session_id,
        )
        result = _run_hook(AGENTS_HOOK, _direct_event(payload), state)
        assert result.returncode == 0, result.stdout + result.stderr
    audit = subprocess.run(
        [sys.executable, str(TEST_HARNESS), "audit", str(state)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert audit.returncode == 0, audit.stdout + audit.stderr
    assert json.loads(audit.stdout) == {"status": "[OK]", "rows": 2, "sessions": 2}

    database = state / "lifecycle.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER lifecycle_records_no_update")
        connection.execute(
            "UPDATE lifecycle_records SET status = 'TERMINAL' WHERE global_sequence = 1"
        )
        connection.execute(
            guard.LEDGER_TRIGGER_STATEMENTS["lifecycle_records_no_update"]
        )
        connection.commit()
    tampered = subprocess.run(
        [sys.executable, str(TEST_HARNESS), "audit", str(state)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert tampered.returncode == 2
    assert _violation(tampered) == "CAPACITY_LEDGER_TAMPER_DETECTED"


def test_offline_audit_command_is_explicit_and_not_registered(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", [str(AGENTS_HOOK), "--offline-audit"])
    monkeypatch.setattr(guard, "offline_full_audit", lambda: {"rows": 7, "sessions": 2})
    assert guard.main() == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "[OK]",
        "rows": 7,
        "sessions": 2,
    }
    registrations = (ROOT / ".agents" / "hooks.json").read_text(encoding="utf-8")
    assert "--offline-audit" not in registrations


def test_ledger_row_session_byte_and_retention_bounds_fail_closed(
    tmp_path: Path,
) -> None:
    first_payload = _build_payload(
        [_ticket("TICKET-BOUND-A", decision_present=False, authorize=False)],
        session_id="session-bound-a",
    )
    first_state = _validation_state(first_payload)

    row_directory = tmp_path / "row-bound"
    row_config = replace(first_state.config, ledger_max_rows=1)
    guard._ledger_append(
        replace(first_state, config=row_config),
        internal_test_directory=row_directory,
    )
    second_payload = _build_payload(
        [_ticket("TICKET-BOUND-A", decision_present=False, authorize=False)],
        session_id="session-bound-a",
        sequence=2,
        previous_record=first_payload["capacity_record_sha256"],
    )
    with pytest.raises(guard.CapacityViolation) as row_error:
        guard._ledger_append(
            replace(_validation_state(second_payload), config=row_config),
            internal_test_directory=row_directory,
        )
    assert row_error.value.code == "CAPACITY_LEDGER_BOUND_EXCEEDED"

    session_directory = tmp_path / "session-bound"
    session_config = replace(first_state.config, ledger_max_sessions=1)
    guard._ledger_append(
        replace(first_state, config=session_config),
        internal_test_directory=session_directory,
    )
    other_payload = _build_payload(
        [_ticket("TICKET-BOUND-B", decision_present=False, authorize=False)],
        session_id="session-bound-b",
    )
    with pytest.raises(guard.CapacityViolation) as session_error:
        guard._ledger_append(
            replace(_validation_state(other_payload), config=session_config),
            internal_test_directory=session_directory,
        )
    assert session_error.value.code == "CAPACITY_LEDGER_BOUND_EXCEEDED"

    with pytest.raises(guard.CapacityViolation) as byte_error:
        guard._ledger_append(
            replace(
                first_state, config=replace(first_state.config, ledger_max_bytes=1)
            ),
            internal_test_directory=tmp_path / "byte-bound",
        )
    assert byte_error.value.code == "CAPACITY_LEDGER_BOUND_EXCEEDED"

    retention_directory = tmp_path / "retention-bound"
    guard._ledger_append(first_state, internal_test_directory=retention_directory)
    with sqlite3.connect(retention_directory / "lifecycle.sqlite3") as connection:
        connection.execute(
            "UPDATE ledger_meta SET first_recorded_at = '2000-01-01T00:00:00Z'"
        )
        connection.commit()
    retention_payload = _build_payload(
        [_ticket("TICKET-RETENTION", decision_present=False, authorize=False)],
        session_id="session-retention",
    )
    with pytest.raises(guard.CapacityViolation) as retention_error:
        guard._ledger_append(
            _validation_state(retention_payload),
            internal_test_directory=retention_directory,
        )
    assert retention_error.value.code == "CAPACITY_LEDGER_BOUND_EXCEEDED"


def test_large_ledger_append_is_bounded_and_offline_audit_is_periodic(
    tmp_path: Path,
) -> None:
    state_directory = tmp_path / "large-ledger"
    _seed_synthetic_ledger(state_directory, 1000)
    payload = _build_payload(
        [_ticket("TICKET-LARGE-APPEND", decision_present=False, authorize=False)],
        session_id="session-large-append",
    )
    state = _validation_state(payload)
    append_started = time.monotonic()
    guard._ledger_append(state, internal_test_directory=state_directory)
    append_elapsed = time.monotonic() - append_started
    assert append_elapsed < 2.0

    audit_started = time.monotonic()
    audit = guard._offline_full_audit(
        state.config, internal_test_directory=state_directory
    )
    audit_elapsed = time.monotonic() - audit_started
    assert audit == {"rows": 1001, "sessions": 2}
    assert audit_elapsed < 5.0
    assert (state_directory / "lifecycle.sqlite3").stat().st_size < (
        state.config.ledger_max_bytes
    )
    source = inspect.getsource(guard._ledger_append)
    assert "integrity_check" not in source
    assert "_offline_verify_ledger" not in source
    with sqlite3.connect(state_directory / "lifecycle.sqlite3") as connection:
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
    assert indexes == set(guard.LEDGER_INDEX_STATEMENTS)
    assert busy_timeout < 10_000


def test_concurrent_cross_process_fork_has_one_winner(tmp_path: Path) -> None:
    payload = _build_payload(
        [_ticket("TICKET-FORK", decision_present=False, authorize=False)]
    )
    event_text = json.dumps(_direct_event(payload))
    state = tmp_path / "state"
    processes = [
        subprocess.Popen(
            [sys.executable, str(TEST_HARNESS), "evaluate", str(state)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    results = [process.communicate(event_text, timeout=20) for process in processes]
    codes = sorted(process.returncode for process in processes)
    assert codes == [0, 2]
    assert any(
        "CAPACITY_CHECKPOINT_STALE_OR_REPLAYED" in stdout for stdout, _ in results
    )


def test_qa_waiting_and_first_released_slot_handoff(guard_context: Path) -> None:
    source = _ticket(
        "TICKET-SOURCE",
        status="DOING",
        lane_type="implementation",
        lane_role="SOURCE_EDITOR",
        ownership=["src/source.py"],
    )
    qa = _ticket(
        "TICKET-QA",
        severity="CRITICAL",
        work_effort="XS",
        dependencies=["TICKET-SOURCE"],
        lane_type="qa",
        lane_role="QA",
        required_role="qa_tester",
    )
    fallback = _ticket(
        "TICKET-FALLBACK",
        severity="LOW",
        lane_type="fallback",
        lane_role="SHORT_FALLBACK",
        required_role="qa_tester",
        authorize=False,
    )
    waiting = _pre_event(
        [source, qa, fallback],
        max_slots=2,
        active=[_ownership_entry(source)],
        handoff=_handoff(
            sources=["TICKET-SOURCE"],
            source_state="ACTIVE",
            qa_ticket_id="TICKET-QA",
            qa_state="WAITING_FOR_SOURCE_FREEZE",
        ),
    )
    assert guard.evaluate_event(waiting) == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"

    frozen_source = _ticket(
        "TICKET-SOURCE",
        status="DONE",
        lane_type="implementation",
        lane_role="SOURCE_EDITOR",
        ownership=["src/source.py"],
    )
    qa = _ticket(
        "TICKET-QA",
        severity="CRITICAL",
        work_effort="XS",
        dependencies=["TICKET-SOURCE"],
        lane_type="qa",
        lane_role="QA",
        required_role="qa_tester",
    )
    released = _pre_event(
        [frozen_source, qa, fallback],
        handoff=_handoff(
            sources=["TICKET-SOURCE"],
            source_state="FROZEN",
            qa_ticket_id="TICKET-QA",
            qa_state="ELIGIBLE",
        ),
    )
    payload = released["tool_input"]["capacity_decision"]["full_capacity"]
    assert payload["decision"]["dispatches"][0]["ticket_id"] == "TICKET-QA"
    assert (
        guard._evaluate_event_for_test(released, guard_context / "released")
        == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"
    )


def test_running_fallback_is_never_cancelled_when_qa_becomes_ready(
    guard_context: Path,
) -> None:
    source = _ticket(
        "TICKET-SOURCE-DONE",
        status="DONE",
        lane_type="implementation",
        lane_role="SOURCE_EDITOR",
    )
    qa = _ticket(
        "TICKET-QA-READY",
        dependencies=["TICKET-SOURCE-DONE"],
        lane_type="qa",
        lane_role="QA",
        required_role="qa_tester",
    )
    running = _ticket(
        "TICKET-RUNNING-FALLBACK",
        status="DOING",
        lane_type="fallback",
        lane_role="SHORT_FALLBACK",
        required_role="qa_tester",
        authorize=False,
    )
    payload = _build_payload(
        [source, qa, running],
        max_slots=1,
        active=[_ownership_entry(running)],
        handoff=_handoff(
            sources=["TICKET-SOURCE-DONE"],
            source_state="FROZEN",
            qa_ticket_id="TICKET-QA-READY",
            qa_state="ELIGIBLE",
            running_fallbacks=["TICKET-RUNNING-FALLBACK"],
            priority=True,
        ),
    )
    assert payload["decision"]["action"] == "CONTINUE"
    assert guard.evaluate_event(_direct_event(payload)) is None
    payload["decision"]["force_cancel"] = True
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_ACTIVE_PREEMPTION_FORBIDDEN"
    )


def test_claude_adapter_blocks_with_nonzero_exit_and_hook_contract() -> None:
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_use_id": "tool-adapter",
        "tool_input": {"prompt": "missing governed envelope"},
    }
    result = _run_hook(CLAUDE_HOOK, event, ROOT / "unused-test-state")
    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert (
        "CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED"
        in output["hookSpecificOutput"]["permissionDecisionReason"]
    )


def test_config_schema_and_registration_are_closed() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert config["effective_short_lane_max_seconds"] == 300
    assert config["normative_short_lane_max_seconds"] == 600
    assert config["positive_alias_runtime_proof_available"] is False
    assert config["ledger_schema_version"] == 3
    assert config["ledger_limits"] == {
        "max_rows": 4096,
        "max_sessions": 256,
        "max_bytes": 16_777_216,
        "retention_seconds": 2_592_000,
        "busy_timeout_ms": 2500,
    }
    assert config["dependency_pins"] == guard.EXPECTED_DEPENDENCY_PINS
    assert schema["additionalProperties"] is False
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - repository test image normally provides it
        jsonschema = None
    if jsonschema is not None:
        jsonschema.Draft202012Validator.check_schema(schema)

    agents_hooks = json.loads(
        (ROOT / ".agents" / "hooks.json").read_text(encoding="utf-8")
    )
    agents_capacity_command = "python3 .agents/hooks/full_capacity_guard.py"
    for phase in ("PreToolUse", "PostToolUse"):
        agents_capacity_matchers = [
            item
            for item in agents_hooks["hooks"][phase]
            if item["handler"].get("command") == agents_capacity_command
        ]
        assert len(agents_capacity_matchers) == 1
        assert agents_capacity_matchers[0]["matcher"] == ".*"
    claude = json.loads(
        (ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    capacity_command = "python3 .claude/hooks/full_capacity_guard.py"
    for phase in ("PreToolUse", "PostToolUse"):
        capacity_matchers = [
            matcher
            for matcher in claude["hooks"][phase]
            if any(hook.get("command") == capacity_command for hook in matcher["hooks"])
        ]
        assert len(capacity_matchers) == 1
        assert capacity_matchers[0]["matcher"] == ".*"
        assert [
            hook["command"]
            for hook in capacity_matchers[0]["hooks"]
            if hook.get("command") == capacity_command
        ] == [capacity_command]
    assert [
        (matcher["matcher"], [hook["command"] for hook in matcher["hooks"]])
        for matcher in claude["hooks"]["PreToolUse"]
        if not any(hook.get("command") == capacity_command for hook in matcher["hooks"])
    ] == [
        (
            "Bash",
            [
                "python3 .claude/hooks/pre_tool_guard.py",
                "python3 .claude/hooks/orchestrator_only_guard.py",
            ],
        ),
        (
            "Read|Grep|Glob|Edit|Write|MultiEdit",
            [
                "python3 .claude/hooks/pre_tool_guard.py",
                "python3 .claude/hooks/orchestrator_only_guard.py",
            ],
        ),
    ]
    assert str(TEST_HARNESS.relative_to(ROOT)) not in json.dumps(agents_hooks)
    assert str(TEST_HARNESS.relative_to(ROOT)) not in json.dumps(claude)


def test_production_state_path_ignores_former_environment_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = guard._load_config()
    expected = guard._fixed_state_directory(config)
    attempted = tmp_path / "attempted-env-state"
    monkeypatch.setenv("HORO_FULL_CAPACITY_GUARD_TEST_MODE", "1")
    monkeypatch.setenv("HORO_FULL_CAPACITY_GUARD_TEST_STATE_DIR", str(attempted))
    assert guard._fixed_state_directory(config) == expected
    assert guard._resolved_state_directory(config, None) == expected
    assert list(inspect.signature(guard.evaluate_event).parameters) == ["event"]
    source = AGENTS_HOOK.read_text(encoding="utf-8")
    assert "HORO_FULL_CAPACITY_GUARD_TEST_MODE" not in source
    assert "HORO_FULL_CAPACITY_GUARD_TEST_STATE_DIR" not in source

    environment = os.environ.copy()
    environment["HORO_FULL_CAPACITY_GUARD_TEST_MODE"] = "1"
    environment["HORO_FULL_CAPACITY_GUARD_TEST_STATE_DIR"] = str(attempted)
    unrelated = subprocess.run(
        [sys.executable, str(AGENTS_HOOK)],
        cwd=ROOT,
        input=json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_use_id": "tool-unrelated-env-ignored",
                "tool_input": {"file": "README.md"},
            }
        ),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert unrelated.returncode == 0, unrelated.stdout + unrelated.stderr
    assert not attempted.exists()


@pytest.mark.parametrize("dependency_name", guard.DEPENDENCY_NAMES)
@pytest.mark.parametrize("failure", ["tampered", "missing"])
def test_dependencies_fail_before_any_module_import(
    monkeypatch: pytest.MonkeyPatch, dependency_name: str, failure: str
) -> None:
    config = guard._load_config()
    dependency_path = config.dependency_pins[dependency_name].path
    original_read = Path.read_bytes
    import_calls: list[str] = []
    original_execute = guard._execute_verified_module

    def altered_read(path: Path) -> bytes:
        if path == dependency_path:
            if failure == "missing":
                raise FileNotFoundError(path)
            return original_read(path) + b"\n# tampered only in memory\n"
        return original_read(path)

    def observed_execute(name: str, path: Path, raw: bytes):
        import_calls.append(name)
        return original_execute(name, path, raw)

    monkeypatch.setattr(Path, "read_bytes", altered_read)
    monkeypatch.setattr(guard, "_execute_verified_module", observed_execute)
    with pytest.raises(guard.CapacityViolation) as error:
        guard._load_policy(config)
    assert error.value.code == "CAPACITY_DEPENDENCY_INTEGRITY_INVALID"
    assert import_calls == []


def test_verified_modules_ignore_and_restore_preloaded_local_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_package = types.ModuleType("scripts")
    fake_scheduler = types.ModuleType("scripts.multiagent_ticket_scheduler")
    fake_dispatcher = types.ModuleType("scripts.multiagent_prompt_command")
    fake_scheduler.validate_snapshot = lambda _value: (_ for _ in ()).throw(
        AssertionError("preloaded scheduler used")
    )
    fake_dispatcher.validate_dispatch_decision = lambda *_args: (_ for _ in ()).throw(
        AssertionError("preloaded dispatcher used")
    )
    monkeypatch.setitem(sys.modules, "scripts", fake_package)
    monkeypatch.setitem(
        sys.modules, "scripts.multiagent_ticket_scheduler", fake_scheduler
    )
    monkeypatch.setitem(
        sys.modules, "scripts.multiagent_prompt_command", fake_dispatcher
    )
    context = guard._load_policy(guard._load_config())
    assert context.scheduler is not fake_scheduler
    assert context.validator is not fake_dispatcher
    assert Path(context.scheduler.__file__) == (
        ROOT / "scripts" / "multiagent_ticket_scheduler.py"
    )
    assert Path(context.validator.__file__) == (
        ROOT / "scripts" / "multiagent_prompt_command.py"
    )
    assert sys.modules["scripts"] is fake_package
    assert sys.modules["scripts.multiagent_ticket_scheduler"] is fake_scheduler
    assert sys.modules["scripts.multiagent_prompt_command"] is fake_dispatcher


def test_config_dependency_pin_mismatch_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    value["dependency_pins"]["scheduler_validator"]["sha256"] = "0" * 64
    mismatched = tmp_path / "full_capacity_guard.v2.json"
    mismatched.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(guard, "CONFIG_PATH", mismatched)
    with pytest.raises(guard.CapacityViolation) as error:
        guard._load_config()
    assert error.value.code == "CAPACITY_CONFIG_INVALID"


def test_local_schema_registry_denies_remote_and_binds_dependency_manifest(
    guard_context: Path,
) -> None:
    from referencing.exceptions import NoSuchResource

    config = guard._load_config()
    context = guard._load_policy(config)
    with pytest.raises(NoSuchResource):
        context.schema_registry.get_or_retrieve(
            "https://unregistered.invalid/remote-schema.json"
        )

    dependency_bytes = {
        name: guard._verified_repository_file(pin.path, pin.digest)
        for name, pin in config.dependency_pins.items()
    }
    governance = json.loads(dependency_bytes["governance_schema"])
    governance["$defs"]["remoteProbe"] = {
        "$ref": "https://unregistered.invalid/remote-schema.json"
    }
    dependency_bytes["governance_schema"] = json.dumps(governance).encode("utf-8")
    with pytest.raises(guard.CapacityViolation) as registry_error:
        guard._build_local_schema_registry(config, dependency_bytes)
    assert registry_error.value.code == "CAPACITY_SCHEMA_REGISTRY_INVALID"

    payload = _build_payload(
        [_ticket("TICKET-DEPENDENCY-MANIFEST", decision_present=False, authorize=False)]
    )
    context.governance_schema_validator.validate(payload)
    assert payload["governance_record"]["dependency_digests"] == dict(
        config.dependency_digests
    )
    payload["governance_record"]["dependency_digests"]["scheduler_validator_sha256"] = (
        "0" * 64
    )
    _seal(payload)
    assert (
        guard.evaluate_event(_direct_event(payload))
        == "CAPACITY_DEPENDENCY_BINDING_INVALID"
    )


def test_same_os_principal_tamper_resistance_is_not_claimed() -> None:
    text = AGENTS_HOOK.read_text(encoding="utf-8")
    assert "not resistant" in text
    assert "same OS principal" in text
    assert "native_hook_interception" in text


def test_feature_flags_are_exact_false_stage_a_defaults() -> None:
    config = guard._load_config()
    assert config.feature_flags == {
        "enable_agy_parity": False,
        "enable_module_level_source_isolation": False,
        "enable_granular_lane_roles": False,
    }
    assert all(type(value) is bool for value in config.feature_flags.values())
    governance_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "feature_flags" not in governance_schema["properties"]


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(
            lambda flags: flags.__setitem__("enable_agy_parity", True),
            id="agy-true",
        ),
        pytest.param(
            lambda flags: flags.__setitem__(
                "enable_module_level_source_isolation", True
            ),
            id="module-isolation-true",
        ),
        pytest.param(
            lambda flags: flags.__setitem__("enable_granular_lane_roles", True),
            id="granular-roles-true",
        ),
        pytest.param(
            lambda flags: flags.__setitem__("enable_agy_parity", "false"),
            id="string",
        ),
        pytest.param(
            lambda flags: flags.__setitem__("enable_agy_parity", 0),
            id="number",
        ),
        pytest.param(
            lambda flags: flags.pop("enable_agy_parity"),
            id="missing",
        ),
        pytest.param(
            lambda flags: flags.__setitem__("unknown_flag", False),
            id="extra",
        ),
    ],
)
def test_feature_flag_config_tampering_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: Any,
) -> None:
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    mutation(value["feature_flags"])
    tampered = tmp_path / "full_capacity_guard.v2.json"
    tampered.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(guard, "CONFIG_PATH", tampered)
    with pytest.raises(guard.CapacityViolation) as error:
        guard._load_config()
    assert error.value.code == "CAPACITY_CONFIG_FEATURE_FLAGS_INVALID"


def test_granular_lane_roles_accepted_in_governance() -> None:
    assert "CORE_SOURCE_EDITOR" in guard.LANE_ROLES
    assert "API_SOURCE_EDITOR" in guard.LANE_ROLES
    assert "UI_SOURCE_EDITOR" in guard.LANE_ROLES
    assert "TEST_SOURCE_EDITOR" in guard.LANE_ROLES
    assert "DOCS_GOVERNANCE_EDITOR" in guard.LANE_ROLES
    assert guard.SOURCE_ROLES == frozenset(
        {"SOURCE_EDITOR", "CORE_SOURCE_EDITOR", "API_SOURCE_EDITOR", "UI_SOURCE_EDITOR"}
    )


def test_source_roles_in_handoff_accepted() -> None:
    payload = _build_payload(
        [
            _ticket("TICKET-CORE-001", status="DONE", lane_role="CORE_SOURCE_EDITOR"),
            _ticket("TICKET-API-001", status="DONE", lane_role="API_SOURCE_EDITOR"),
            _ticket("TICKET-QA-001", lane_role="QA"),
        ]
    )
    payload["governance_record"]["source_qa_handoff"]["source_ticket_ids"] = [
        "TICKET-API-001",
        "TICKET-CORE-001",
    ]
    payload["governance_record"]["source_qa_handoff"]["source_state"] = "FROZEN"
    payload["governance_record"]["source_qa_handoff"]["qa_ticket_id"] = "TICKET-QA-001"
    payload["governance_record"]["source_qa_handoff"]["qa_state"] = "ELIGIBLE"
    unsigned = dict(payload["governance_record"]["source_qa_handoff"])
    unsigned.pop("handoff_sha256", None)
    payload["governance_record"]["source_qa_handoff"]["handoff_sha256"] = guard._sha256(
        unsigned
    )
    _seal(payload)
    event = _direct_event(payload)
    state = guard._validate_payload(payload, guard._extract_event(event)[1])
    assert state.block_code == "CAPACITY_AUTHORITATIVE_SNAPSHOT_NOT_PROVEN"


def test_local_token_cannot_enable_positive_agy_semantics() -> None:
    config = guard._load_config()
    parity_config = replace(config, feature_flags={"enable_agy_parity": True})
    payload = _build_payload(
        [_ticket("TICKET-AGY-001", alias="agy1", lane_role="DOCS_EDITOR")],
        alias_candidates={"agy1": "TICKET-AGY-001", "agy2": None},
    )
    session_id = payload["governance_record"]["session_id"]
    entry = payload["governance_record"]["alias_evaluations"][0]
    auth_id = entry["authorization_id"]
    auth_sha = entry["authorization_sha256"]
    expected_token = guard._sha256(
        {
            "session_id": session_id,
            "ticket_id": "TICKET-AGY-001",
            "alias": "agy1",
            "authorization_id": auth_id,
            "authorization_sha256": auth_sha,
        }
    )
    policy = _policy_context()
    tickets = guard._validate_tickets(payload, config=parity_config, policy=policy)
    assert entry["reason_codes"] == ["CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"]
    guard._validate_alias_evaluations(
        payload["governance_record"],
        tickets=tickets,
        actionable=("TICKET-AGY-001",),
        reserved_resources=(),
        qa_priority_ticket=None,
        config=parity_config,
    )
    entry["eligibility"] = "ELIGIBLE"
    entry["dispatched"] = True
    entry["receipt"] = {"token_anchor": expected_token}
    _seal(payload)
    with pytest.raises(guard.CapacityViolation) as error:
        guard._validate_alias_evaluations(
            payload["governance_record"],
            tickets=tickets,
            actionable=("TICKET-AGY-001",),
            reserved_resources=(),
            qa_priority_ticket=None,
            config=parity_config,
        )
    assert error.value.code == "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"


def test_local_token_with_no_candidate_cannot_create_dispatch_metadata() -> None:
    config = guard._load_config()
    parity_config = replace(config, feature_flags={"enable_agy_parity": True})
    payload = _build_payload([_ticket("TICKET-AGY-001", lane_role="DOCS_EDITOR")])
    entry = payload["governance_record"]["alias_evaluations"][0]
    assert entry["candidate_ticket_id"] is None
    entry["eligibility"] = "ELIGIBLE"
    entry["dispatched"] = True
    entry["receipt"] = {
        "token_anchor": guard._sha256(
            {
                "session_id": payload["governance_record"]["session_id"],
                "ticket_id": None,
                "alias": "agy1",
                "authorization_id": None,
                "authorization_sha256": None,
            }
        )
    }
    _seal(payload)
    policy = _policy_context()
    tickets = guard._validate_tickets(payload, config=parity_config, policy=policy)
    with pytest.raises(guard.CapacityViolation) as error:
        guard._validate_alias_evaluations(
            payload["governance_record"],
            tickets=tickets,
            actionable=("TICKET-AGY-001",),
            reserved_resources=(),
            qa_priority_ticket=None,
            config=parity_config,
        )
    assert error.value.code == "CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE"
