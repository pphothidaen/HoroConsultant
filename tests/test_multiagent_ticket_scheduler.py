"""Rule 11 scheduler regression coverage for TICKET-PRIORITY-003."""

from __future__ import annotations

from dataclasses import replace
from itertools import combinations
import json
from pathlib import Path

import pytest

import scripts.multiagent_prompt_command as command
import scripts.multiagent_ticket_scheduler as scheduler


ROOT = Path(__file__).resolve().parents[1]


def _ticket(ticket_id: str, **overrides: object) -> dict[str, object]:
    ticket: dict[str, object] = {
        "ticket_id": ticket_id,
        "severity": "HIGH",
        "work_effort": "M",
        "status": "READY",
        "dependencies": [],
        "blockers": [],
        "owner": "developer",
        "ownership": [ticket_id],
        "quota_passed": True,
        "hitl_passed": True,
        "rule18_decision_valid": True,
    }
    ticket.update(overrides)
    return ticket


def _snapshot(*tickets: dict[str, object], reservations: list[dict[str, object]] | None = None):
    return scheduler.validate_snapshot(
        {"schema_version": 1, "tickets": list(tickets), "reservations": reservations or []}
    )


def _reservation(ticket: dict[str, object]) -> dict[str, object]:
    return {
        "ticket_id": ticket["ticket_id"],
        "owner": ticket["owner"],
        "ownership": ticket["ownership"],
    }


@pytest.mark.parametrize("higher,lower", tuple(combinations(("CRITICAL", "HIGH", "MEDIUM", "LOW"), 2)))
def test_severity_pairs_sort_descending_before_all_other_fields(higher, lower):
    snapshot = _snapshot(
        _ticket("TICKET-LOW-ID", severity=lower, work_effort="XS"),
        _ticket("TICKET-HIGH-ID", severity=higher, work_effort="XL"),
    )

    assert scheduler.select_tickets(snapshot)[0].ticket.ticket_id == "TICKET-HIGH-ID"


@pytest.mark.parametrize("smaller,larger", tuple(combinations(("XS", "S", "M", "L", "XL"), 2)))
def test_work_effort_pairs_sort_ascending_within_same_severity(smaller, larger):
    snapshot = _snapshot(
        _ticket("TICKET-LARGER", work_effort=larger),
        _ticket("TICKET-SMALLER", work_effort=smaller),
    )

    assert scheduler.select_tickets(snapshot)[0].ticket.ticket_id == "TICKET-SMALLER"


def test_exact_ticket_id_ascii_ties_are_deterministic():
    snapshot = _snapshot(
        _ticket("TICKET-a"),
        _ticket("TICKET-A"),
        _ticket("TICKET-9"),
    )

    assert [item.ticket.ticket_id for item in scheduler.select_tickets(snapshot, 3)] == [
        "TICKET-9",
        "TICKET-A",
        "TICKET-a",
    ]


def test_empty_eligible_set_returns_no_selection_and_dispatch_blocks():
    snapshot = _snapshot(_ticket("TICKET-DONE", status="DONE"))

    assert scheduler.select_tickets(snapshot) == ()
    with pytest.raises(scheduler.SchedulingError, match="no ticket is execution-eligible") as exc:
        scheduler.enforce_dispatch(
            snapshot,
            ticket_id="TICKET-DONE",
            owner="developer",
            ownership=("TICKET-DONE",),
            decision_valid=True,
        )
    assert exc.value.code == "NO_ELIGIBLE_TICKET"


@pytest.mark.parametrize(
    "field,value",
    [
        ("dependencies", ["TICKET-DEPENDENCY"]),
        ("blockers", ["explicit blocker"]),
        ("quota_passed", False),
        ("hitl_passed", False),
        ("rule18_decision_valid", False),
    ],
)
def test_lower_severity_runs_when_higher_severity_is_independently_ineligible(field, value):
    dependency = _ticket("TICKET-DEPENDENCY", status="BLOCKED")
    high = _ticket("TICKET-HIGH", severity="CRITICAL", **{field: value})
    low = _ticket("TICKET-LOW", severity="LOW")
    snapshot = _snapshot(high, low, dependency)

    assert scheduler.select_tickets(snapshot)[0].ticket.ticket_id == "TICKET-LOW"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda ticket: ticket.pop("severity"),
        lambda ticket: ticket.update(severity="URGENT"),
        lambda ticket: ticket.pop("work_effort"),
        lambda ticket: ticket.update(work_effort="TINY"),
        lambda ticket: ticket.pop("status"),
        lambda ticket: ticket.update(status="RUNNING"),
        lambda ticket: ticket.update(ticket_id="ticket-non-ascii-é"),
    ],
)
def test_invalid_or_missing_scheduling_metadata_fails_closed(mutate):
    ticket = _ticket("TICKET-METADATA")
    mutate(ticket)

    with pytest.raises(scheduler.SchedulingError) as exc:
        _snapshot(ticket)
    assert exc.value.code == "INVALID_SCHEDULING_METADATA"


def test_duplicate_ticket_id_fails_closed():
    with pytest.raises(scheduler.SchedulingError, match="duplicate Ticket ID") as exc:
        _snapshot(_ticket("TICKET-DUP"), _ticket("TICKET-DUP"))
    assert exc.value.code == "INVALID_SCHEDULING_METADATA"


@pytest.mark.parametrize(
    "ticket,reservations",
    [
        (_ticket("TICKET-DEPENDENT", dependencies=["TICKET-UPSTREAM"]), []),
        (_ticket("TICKET-BLOCKED", blockers=["operator hold"]), []),
        (
            _ticket("TICKET-CONFLICT", ownership=["shared"]),
            [_reservation(_ticket("TICKET-RESERVED", ownership=["shared"]))],
        ),
        (_ticket("TICKET-DONE", status="DONE"), []),
        (_ticket("TICKET-BLOCKED-STATUS", status="BLOCKED"), []),
        (_ticket("TICKET-QUOTA", quota_passed=False), []),
        (_ticket("TICKET-HITL", hitl_passed=False), []),
        (_ticket("TICKET-RULE18", rule18_decision_valid=False), []),
    ],
)
def test_each_execution_eligibility_exclusion_removes_ticket(ticket, reservations):
    tickets = [ticket]
    if ticket["ticket_id"] == "TICKET-DEPENDENT":
        tickets.append(_ticket("TICKET-UPSTREAM", status="BLOCKED"))
    if reservations:
        tickets.append(_ticket("TICKET-RESERVED", ownership=["shared"]))
    snapshot = _snapshot(*tickets, reservations=reservations)

    assert scheduler.select_tickets(snapshot) == ()


def test_combined_exclusions_remain_excluded_without_comparator_fallback():
    high = _ticket(
        "TICKET-HIGH",
        severity="CRITICAL",
        dependencies=["TICKET-UPSTREAM"],
        blockers=["blocker"],
        quota_passed=False,
        hitl_passed=False,
        rule18_decision_valid=False,
        ownership=["shared"],
    )
    reserved = _ticket("TICKET-RESERVED", ownership=["shared"])
    low = _ticket("TICKET-LOW", severity="LOW")
    snapshot = _snapshot(
        high,
        reserved,
        low,
        _ticket("TICKET-UPSTREAM", status="BLOCKED"),
        reservations=[_reservation(reserved)],
    )

    assert scheduler.select_tickets(snapshot)[0].ticket.ticket_id == "TICKET-LOW"


def test_multi_selection_reserves_then_recomputes_ownership_conflicts():
    first = _ticket("TICKET-FIRST", severity="CRITICAL", ownership=["shared"])
    excluded_after_reservation = _ticket("TICKET-CONFLICT", severity="HIGH", ownership=["shared"])
    independent = _ticket("TICKET-INDEPENDENT", severity="LOW", ownership=["other"])
    snapshot = _snapshot(first, excluded_after_reservation, independent)

    selections = scheduler.select_tickets(snapshot, capacity=2)

    assert [selection.ticket.ticket_id for selection in selections] == [
        "TICKET-FIRST",
        "TICKET-INDEPENDENT",
    ]
    assert [item.ticket_id for item in selections[-1].reservations] == [
        "TICKET-FIRST",
        "TICKET-INDEPENDENT",
    ]


def test_doing_ticket_continuation_is_bound_to_its_matching_reservation():
    doing = _ticket("TICKET-DOING", status="DOING", ownership=["owned"])
    snapshot = _snapshot(doing, reservations=[_reservation(doing)])

    continuation = scheduler.enforce_dispatch(
        snapshot,
        ticket_id="TICKET-DOING",
        owner="developer",
        ownership=("owned",),
        decision_valid=True,
    )

    assert continuation.continued_reservation is True
    with pytest.raises(scheduler.SchedulingError, match="lacks an ownership reservation") as exc:
        scheduler.enforce_dispatch(
            _snapshot(doing),
            ticket_id="TICKET-DOING",
            owner="developer",
            ownership=("owned",),
            decision_valid=True,
        )
    assert exc.value.code == "INVALID_SCHEDULING_METADATA"


def test_doing_work_is_not_preempted_by_new_ticket_selection():
    doing = _ticket("TICKET-DOING", severity="CRITICAL", status="DOING", ownership=["owned"])
    ready = _ticket("TICKET-READY", severity="LOW", ownership=["fresh"])
    snapshot = _snapshot(doing, ready, reservations=[_reservation(doing)])

    assert scheduler.select_tickets(snapshot)[0].ticket.ticket_id == "TICKET-READY"
    assert scheduler.enforce_dispatch(
        snapshot,
        ticket_id="TICKET-DOING",
        owner="developer",
        ownership=("owned",),
        decision_valid=True,
    ).continued_reservation is True


@pytest.mark.parametrize(
    ("claimed", "reserved"),
    [
        ("project/tests", "project/tests/test_scheduler.py"),
        ("project/tests/test_scheduler.py", "project/tests"),
        ("project//tests/./scheduler.py", "project/tests/scheduler.py"),
        ("C:/Users/QA/Work", "c:/users/qa/work/child.py"),
    ],
)
def test_canonical_ownership_parent_child_separator_and_dot_overlap(claimed, reserved):
    candidate = _ticket("TICKET-CANDIDATE", ownership=[claimed])
    active = _ticket("TICKET-ACTIVE", ownership=[reserved])
    snapshot = _snapshot(candidate, active, reservations=[_reservation(active)])

    assert scheduler.select_tickets(snapshot) == ()


@pytest.mark.parametrize("resource", [".", "..", "../outside", "/"])
def test_unsafe_broad_ownership_resource_fails_closed(resource):
    with pytest.raises(scheduler.SchedulingError, match="unsafe broad resource") as exc:
        _snapshot(_ticket("TICKET-UNSAFE", ownership=[resource]))
    assert exc.value.code == "INVALID_SCHEDULING_METADATA"


@pytest.mark.parametrize(
    "model,effort",
    [("gpt-5.6-luna", "low"), ("gpt-5.6-terra", "high"), ("gpt-5.6-sol", "xhigh")],
)
def test_model_and_reasoning_effort_do_not_change_rule11_order(model, effort):
    snapshot = _snapshot(
        _ticket("TICKET-SMALL", work_effort="S"),
        _ticket("TICKET-LARGE", work_effort="XL"),
    )
    decision = {"ticket": "TICKET-SMALL", "selected_model": model, "selected_effort": effort}

    assert command.validate_scheduling_dispatch(
        {
            "schema_version": 1,
            "tickets": [
                _ticket("TICKET-SMALL", work_effort="S"),
                _ticket("TICKET-LARGE", work_effort="XL"),
            ],
            "reservations": [],
        },
        decision,
        role="developer",
        ownership="TICKET-SMALL",
    ) == snapshot.digest


def test_snapshot_and_decision_digest_tampering_block_before_subprocess(tmp_path, monkeypatch):
    config = {
        "runtime": {"approved_for_execution": True, "protocol_version": 2},
        "accounts": {"codex1": {"cli": "codex", "command": "codex"}},
        "roles": {
            "developer": {
                "alias": "codex1",
                "cli": "codex",
                "model": "gpt-5.6-luna",
                "effort": "medium",
                "sandbox": "workspace-write",
            }
        },
    }
    route = command.resolve_route(config, "developer")
    policy = command.load_model_policy(ROOT / ".agents/config/multiagent_model_policy.yaml")
    decision = {
        "schema_version": 1, "ticket": "TICKET-ADAPT-TEST", "phase": "implementation",
        "scope_rank": 1, "complexity_rank": 1, "risk_rank": 1, "ambiguity_rank": 1,
        "evidence_burden_rank": 1, "quota_band": "healthy", "work_mode": "mutation",
        "selected_alias": "codex1", "selected_model": "gpt-5.6-luna", "selected_effort": "medium",
        "rationale": "scheduler digest regression", "policy_version": policy["policy_version"],
        "planning_to_medium_confirmed": True, "hitl_approved": False,
    }
    snapshot = {
        "schema_version": 1,
        "tickets": [_ticket("TICKET-ADAPT-TEST", ownership=["owned"])],
        "reservations": [],
    }
    invocation = command.build_invocation(
        route,
        command.render_prompt(objective="digest check", ownership="owned"),
        tmp_path,
        decision=decision,
        model_policy=policy,
        objective="digest check",
        ownership="owned",
        scheduling_snapshot=snapshot,
    )
    monkeypatch.setattr(command.subprocess, "run", lambda *args, **kwargs: pytest.fail("subprocess"))
    invocation.scheduling_snapshot["tickets"][0]["severity"] = "LOW"
    with pytest.raises(scheduler.SchedulingError, match="missing or stale"):
        command._validated_invocation_schedule(
            invocation, command.validate_dispatch_decision(invocation.decision, policy, route)
        )

    clean = replace(invocation, scheduling_snapshot=snapshot)
    clean.decision["rationale"] = "tampered dispatch decision"
    with pytest.raises(command.DispatchDecisionError, match="missing or stale"):
        command._validated_invocation_decision(clean)


def test_invalid_metadata_is_blocked_before_subprocess_creation(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "runtime:\n  approved_for_execution: true\n  protocol_version: 2\naccounts:\n  codex1:\n    cli: codex\nroles:\n  developer:\n    alias: codex1\n    cli: codex\n    model: gpt-5.6-luna\n    effort: medium\n    sandbox: workspace-write\n",
        encoding="utf-8",
    )
    policy_path = ROOT / ".agents/config/multiagent_model_policy.yaml"
    policy = command.load_model_policy(policy_path)
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1, "ticket": "TICKET-ADAPT-TEST", "phase": "implementation",
                "scope_rank": 1, "complexity_rank": 1, "risk_rank": 1, "ambiguity_rank": 1,
                "evidence_burden_rank": 1, "quota_band": "healthy", "work_mode": "mutation",
                "selected_alias": "codex1", "selected_model": "gpt-5.6-luna", "selected_effort": "medium",
                "rationale": "invalid metadata gate", "policy_version": policy["policy_version"],
                "planning_to_medium_confirmed": True, "hitl_approved": False,
            }
        ),
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "invalid-snapshot.json"
    snapshot_path.write_text(
        json.dumps({"schema_version": 1, "tickets": [{"ticket_id": "TICKET-ADAPT-TEST"}], "reservations": []}),
        encoding="utf-8",
    )
    started = False

    def fail_if_started(*args, **kwargs):
        nonlocal started
        started = True
        pytest.fail("invalid scheduling metadata reached subprocess creation")

    monkeypatch.setattr(command.subprocess, "run", fail_if_started)
    assert command.main([
        "--config", str(config_path), "--role", "developer", "--objective", "blocked",
        "--project-dir", str(tmp_path), "--decision", str(decision_path), "--policy", str(policy_path),
        "--scheduling-snapshot", str(snapshot_path), "--execute",
    ]) == 5
    assert started is False
    assert "INVALID_SCHEDULING_METADATA" in capsys.readouterr().err


def test_capacity_admission_keeps_selected_route_account_local(tmp_path):
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    ticket = _ticket("TICKET-CAPACITY", ownership=["owned/capacity.py"])
    lease = scheduler.admit_dispatch_capacity(
        _snapshot(ticket),
        ticket_id="TICKET-CAPACITY",
        owner="developer",
        ownership=("owned/capacity.py",),
        decision_valid=True,
        store_path=str(tmp_path / "capacity"),
        account="codex1",
        request_id="capacity-ticket-1",
        lane=1,
        request_budget=1,
        model_quality_floor="1",
        policy=policy,
    )

    assert lease.account == "codex1"
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            _snapshot(ticket),
            ticket_id="TICKET-CAPACITY",
            owner="developer",
            ownership=("owned/capacity.py",),
            decision_valid=True,
            store_path=str(tmp_path / "capacity"),
            account="codex1",
            request_id="capacity-ticket-1",
            lane=1,
            request_budget=1,
            model_quality_floor="1",
            policy=policy,
        )
    assert exc.value.code == "CAPACITY_REQUEST_ALREADY_LEASED"


@pytest.mark.parametrize(
    ("pressure", "expected_code"),
    (
        ("burn", "CAPACITY_BURN_RATE_EXCEEDED"),
        ("block", "CAPACITY_BACKPRESSURE_BLOCKED"),
        ("queue", "CAPACITY_BACKPRESSURE_QUEUED"),
        ("circuit", "CAPACITY_CIRCUIT_OPEN"),
    ),
)
def test_capacity_pressure_rejects_only_the_selected_account(  # noqa: PLR0915
    tmp_path, pressure, expected_code
):
    """S3/S4/S5 pressure never permits cross-account fallback."""

    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    store = tmp_path / "capacity"
    ticket = _ticket("TICKET-PRESSURE", ownership=["owned/pressure.py"])
    common = {
        "snapshot": _snapshot(ticket),
        "ticket_id": "TICKET-PRESSURE",
        "owner": "developer",
        "ownership": ("owned/pressure.py",),
        "decision_valid": True,
        "store_path": str(store),
        "lane": 1,
        "request_budget": 1,
        "model_quality_floor": "1",
        "policy": policy,
    }

    if pressure == "burn":
        burner = scheduler.capacity.acquire_lease(
            store,
            account="codex1",
            request_id="burner",
            owner="developer",
            lane=2,
            request_budget=policy["accounts"]["codex1"]["burn_rate"]["max_requests"],
            model_quality_floor="1",
            policy=policy,
        )
        consumed = scheduler.capacity.consume_lease(
            store, burner, requests=burner.request_budget, policy=policy
        )
        scheduler.capacity.release_lease(store, consumed, policy=policy)
    elif pressure in {"block", "queue"}:
        scheduler.capacity.set_backpressure(
            store, account="codex1", mode=pressure, policy=policy
        )
    else:
        threshold = policy["accounts"]["codex1"]["circuit_breaker"]["failure_threshold"]
        for _ in range(threshold):
            scheduler.capacity.record_failure(
                store, account="codex1", failure_type="timeout", policy=policy
            )

    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            **common, account="codex1", request_id=f"blocked-{pressure}"
        )
    assert exc.value.code == expected_code

    # A safe, separately owned pool remains usable but is never selected as a
    # fallback for the rejected codex1 request.
    isolated = scheduler.admit_dispatch_capacity(
        **common, account="codex2", request_id=f"isolated-{pressure}"
    )
    assert isolated.account == "codex2"


def _healthy_state(provider: str = "agy", account: str = "agy1") -> dict[str, object]:
    return {"providers": {provider: {"state": "healthy"}}, "accounts": {account: {"state": "healthy"}}}


@pytest.mark.parametrize(
    ("state", "code"),
    [
        ({}, "PROVIDER_ACCOUNT_STATE_UNKNOWN"),
        (_healthy_state(account="agy1") | {"accounts": {"agy1": {"state": "exhausted"}}}, "PROVIDER_ACCOUNT_EXHAUSTED"),
    ],
)
def test_provider_account_state_is_required_and_exhaustion_blocks_admission(tmp_path, state, code):
    ticket = _ticket("TICKET-STATE", ownership=["state-owned"])
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            _snapshot(ticket), ticket_id=ticket["ticket_id"], owner="developer",
            ownership=("state-owned",), decision_valid=True,
            store_path=str(tmp_path / "capacity"), account="agy1", request_id="state-1",
            lane=1, request_budget=1, model_quality_floor="1", policy=policy,
            provider="agy", provider_account_state=state,
        )
    assert exc.value.code == code


def test_healthy_state_and_root_b_role_are_admissible_but_mismatch_is_blocked(tmp_path):
    ticket = _ticket("TICKET-ROOTB", ownership=["rootb-owned"])
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    lease = scheduler.admit_dispatch_capacity(
        _snapshot(ticket), ticket_id=ticket["ticket_id"], owner="developer",
        ownership=("rootb-owned",), decision_valid=True,
        store_path=str(tmp_path / "capacity"), account="agy1", request_id="rootb-1",
        lane=1, request_budget=1, model_quality_floor="1", policy=policy,
        provider="agy", provider_account_state=_healthy_state(), root_b_role="primary",
    )
    assert lease.account == "agy1"
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            _snapshot(ticket), ticket_id=ticket["ticket_id"], owner="developer",
            ownership=("rootb-owned",), decision_valid=True,
            store_path=str(tmp_path / "other"), account="agy1", request_id="rootb-2",
            lane=1, request_budget=1, model_quality_floor="1", policy=policy,
            provider="agy", provider_account_state=_healthy_state(), root_b_role="secondary",
        )
    assert exc.value.code == "ROOT_B_ROLE_MISMATCH"


def test_retry_limit_and_reservation_release_are_bounded(tmp_path):
    ticket = _ticket("TICKET-RETRY", ownership=["retry-owned"])
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            _snapshot(ticket), ticket_id=ticket["ticket_id"], owner="developer",
            ownership=("retry-owned",), decision_valid=True,
            store_path=str(tmp_path / "capacity"), account="agy1", request_id="retry-4",
            lane=4, request_budget=1, model_quality_floor="1", policy=policy,
            provider="agy", provider_account_state=_healthy_state(), attempt=4, retry_limit=3,
        )
    assert exc.value.code == "RETRY_LIMIT_EXCEEDED"
    reserved = scheduler.validate_snapshot({
        "schema_version": 1, "tickets": [ticket],
        "reservations": [_reservation(ticket)],
    })
    released = scheduler.release_reservation(
        reserved, ticket_id="TICKET-RETRY", owner="developer", ownership=("retry-owned",)
    )
    assert released.reservations == ()
    assert scheduler.select_tickets(released)[0].ticket.ticket_id == "TICKET-RETRY"


def test_activation_guard_is_closed_until_a_later_phase():
    with pytest.raises(scheduler.SchedulingError, match="ACTIVATION_PROHIBITED"):
        scheduler.validate_activation_state(
            activation_prohibited=True, dispatcher_execution="CLOSED"
        )
    with pytest.raises(scheduler.SchedulingError, match="ACTIVATION_PROHIBITED"):
        scheduler.validate_activation_state(
            activation_prohibited=False, dispatcher_execution="CLOSED"
        )
    scheduler.validate_activation_state(
        activation_prohibited=False, dispatcher_execution="OPEN"
    )


def test_dispatch_consumes_one_frozen_retry_slot_per_attempt_without_fallback(tmp_path):
    ticket = _ticket("TICKET-FROZEN-RETRY", ownership=["frozen-retry-owned"])
    policy = json.loads((ROOT / ".agents/config/s3_capacity_policy.json").read_text())
    store = str(tmp_path / "capacity")
    common = dict(
        snapshot=_snapshot(ticket), ticket_id=ticket["ticket_id"], owner="developer",
        ownership=("frozen-retry-owned",), decision_valid=True, store_path=store,
        account="agy1", lane=1, request_budget=1, model_quality_floor="1", policy=policy,
        provider="agy", provider_account_state=_healthy_state(),
        retry_request_id="logical-frozen-retry",
    )

    for attempt in (1, 2, 3):
        lease = scheduler.admit_dispatch_capacity(
            **common, request_id=f"attempt-{attempt}", attempt=attempt
        )
        assert lease.account == "agy1"
        scheduler.capacity.release_lease(store, lease, policy=policy)

    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            **common, request_id="attempt-4", attempt=4
        )
    assert exc.value.code == "RETRY_LIMIT_EXCEEDED"


def test_retry_limit_is_frozen_at_three_total_attempts():
    for retry_limit in (4, 3.0, True):
        with pytest.raises(scheduler.SchedulingError) as exc:
            scheduler.validate_retry_attempt(1, retry_limit=retry_limit)
        assert exc.value.code == "INVALID_RETRY_LIMIT"
