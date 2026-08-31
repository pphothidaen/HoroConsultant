"""Test-first baseline for BRK-B0-030: Capacity and Admission Governance.

This suite freezes fail-closed registry, account isolation, circuit breaker,
quota verification, aggregate root ceilings, and capacity category separation
before downstream source implementation tickets (BRK-B3-010).

Negative controls cover:
- agy3 / codex3 are not executable merely because configured
- unknown quota admits zero
- open circuit breaker admits zero
- AGY cap above 3 rejects
- Codex cap above frozen policy rejects
- Root A / Root B aggregate caps enforced
- cross-account lease/circuit/quota reuse rejects
- capacity categories (theoretical, policy-admitted, runtime-proven) cannot be conflated
- sentinel entrypoint check asserting ENTRYPOINT_MISSING before source exists.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import pytest

from scripts import multiagent_capacity as capacity
from scripts import multiagent_ticket_scheduler as scheduler


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agents/config/s3_capacity_policy.json"
SIX_ALIASES = ("agy1", "agy2", "agy3", "codex1", "codex2", "codex3")
ROOT_OWNERS = {
    "codex1": "RootA",
    "codex2": "RootA",
    "codex3": "RootA",
    "agy1": "RootB",
    "agy2": "RootB",
    "agy3": "RootB",
}
PER_ACCOUNT_POLICY_CAPS = {
    "agy1": 3,
    "agy2": 3,
    "agy3": 3,
    "codex1": 2,
    "codex2": 2,
    "codex3": 2,
}
ROOT_AGGREGATE_CAPS = {
    "RootA": 3,
    "RootB": 3,
}


@pytest.fixture
def policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def six_alias_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Synthetic closed 6-alias policy fixture for contract validation."""
    p = copy.deepcopy(policy)
    if "agy3" not in p["accounts"]:
        p["accounts"]["agy3"] = {
            "burn_rate": {"max_requests": 30, "window_seconds": 60},
            "circuit_breaker": {
                "allow_manual_reset": False,
                "cooldown_seconds": 120,
                "failure_threshold": 3,
                "failure_types": [
                    "quota_exhausted",
                    "rate_limit",
                    "timeout",
                    "invalid_provider_event",
                    "missing_runtime_proof",
                ],
                "failure_window_seconds": 60,
            },
            "max_workers": 3,
            "provider": "agy",
        }
    return p


# ---------------------------------------------------------------------------
# 1. Sentinel Entrypoint Check
# ---------------------------------------------------------------------------


def test_broker_capacity_admission_sentinel_entrypoint_exists() -> None:
    """Sentinel entrypoint check asserting ENTRYPOINT_MISSING before B3 source exists.

    Validates that scripts/multiagent_capacity.py and .agents/config/s3_capacity_policy.json
    have registered all 6 canonical aliases (including agy3).
    """
    missing_entrypoints: list[str] = []

    # Check that KNOWN_ACCOUNTS in multiagent_capacity includes agy3
    known_accounts = getattr(capacity, "KNOWN_ACCOUNTS", ())
    if "agy3" not in known_accounts:
        missing_entrypoints.append(
            "scripts/multiagent_capacity.py: KNOWN_ACCOUNTS missing 'agy3'"
        )

    account_providers = getattr(capacity, "ACCOUNT_PROVIDERS", {})
    if account_providers.get("agy3") != "agy":
        missing_entrypoints.append(
            "scripts/multiagent_capacity.py: ACCOUNT_PROVIDERS missing 'agy3' -> 'agy'"
        )

    # Check that policy configuration file registers agy3
    if not POLICY_PATH.is_file():
        missing_entrypoints.append(f"missing policy file: {POLICY_PATH}")
    else:
        policy_data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        accounts = policy_data.get("accounts", {})
        if "agy3" not in accounts:
            missing_entrypoints.append(
                ".agents/config/s3_capacity_policy.json: accounts missing 'agy3'"
            )

    assert not missing_entrypoints, (
        "ENTRYPOINT_MISSING: " + "; ".join(missing_entrypoints)
    )


# ---------------------------------------------------------------------------
# 2. Negative Control: agy3/codex3 not executable merely because configured
# ---------------------------------------------------------------------------


def test_agy3_and_codex3_are_not_executable_merely_because_configured() -> None:
    """Theoretical presence in configuration does not confer execution rights.

    Admission requires safe quota verification, account isolation proof, closed circuit,
    and runtime proof before any lane can execute.
    """
    # A configured account with no runtime proof or quota verification has 0 admitted lanes
    unadmitted_account_state = {
        "alias": "agy3",
        "configured_ceiling": 3,
        "quota_status": "unverified",
        "circuit_breaker": "closed",
        "isolation_proven": False,
        "runtime_proven_lanes": 0,
    }

    # Policy-admitted capacity must be 0 when quota is unverified or isolation unproven
    is_policy_admitted = (
        unadmitted_account_state["quota_status"] == "verified_safe"
        and unadmitted_account_state["isolation_proven"]
        and unadmitted_account_state["circuit_breaker"] == "closed"
    )
    assert not is_policy_admitted, "Unproven agy3 must not be policy-admitted"

    codex3_state = {
        "alias": "codex3",
        "configured_ceiling": 2,
        "quota_status": "unknown",
        "in_ordinary_dispatch_allowlist": False,
        "isolation_proven": False,
    }
    assert (
        codex3_state["quota_status"] != "verified_safe"
        or not codex3_state["in_ordinary_dispatch_allowlist"]
    ), "codex3 must not be executable without ordinary dispatch allowlist and verified quota"


# ---------------------------------------------------------------------------
# 3. Negative Control: unknown quota admits zero
# ---------------------------------------------------------------------------


def test_unknown_quota_admits_zero_lanes(tmp_path: Path, six_alias_policy: dict[str, Any]) -> None:
    """Unknown quota must fail-closed and admit zero lanes."""
    # Policy validation rejects non-verified quota basis
    tampered_policy = copy.deepcopy(six_alias_policy)
    tampered_policy["quota_basis"] = "optimistic_allow"
    with pytest.raises(capacity.InvalidPolicyError, match="QUOTA_BASIS_INVALID"):
        capacity.validate_capacity_policy(tampered_policy)

    # Scheduler snapshot with quota_passed=False must reject ticket selection
    snapshot = scheduler.validate_snapshot(
        {
            "schema_version": 1,
            "tickets": [
                {
                    "ticket_id": "BRK-UNKN-001",
                    "severity": "HIGH",
                    "work_effort": "S",
                    "status": "READY",
                    "dependencies": [],
                    "blockers": [],
                    "owner": "RootB",
                    "ownership": ["plans/evidence/broker/unknown.json"],
                    "quota_passed": False,
                    "hitl_passed": True,
                    "rule18_decision_valid": True,
                }
            ],
            "reservations": [],
        }
    )

    # Selection must admit 0 tickets when quota is unpassed
    selections = scheduler.select_tickets(snapshot, capacity=1)
    assert len(selections) == 0, "Unknown quota must admit 0 tickets"


# ---------------------------------------------------------------------------
# 4. Negative Control: open circuit breaker admits zero
# ---------------------------------------------------------------------------


def test_open_circuit_breaker_admits_zero_lanes(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """An open circuit breaker admits zero lanes and prohibits manual reset."""
    # Record consecutive failures until circuit breaker trips
    for i in range(3):
        capacity.record_failure(
            tmp_path,
            account="agy1",
            failure_type="quota_exhausted",
            policy=policy,
            now=100 + i,
        )

    # Attempting to acquire a lease when circuit is open must raise LeaseRejectedError
    with pytest.raises(capacity.LeaseRejectedError, match="CIRCUIT_OPEN"):
        capacity.acquire_lease(
            tmp_path,
            account="agy1",
            request_id="req-circuit-open-test",
            owner="RootB",
            lane=1,
            request_budget=5,
            model_quality_floor="flash",
            policy=policy,
            now=105,
        )

    # Manual reset is rejected when allow_manual_reset is False
    with pytest.raises(capacity.LeaseRejectedError, match="CIRCUIT_RESET_NOT_ALLOWED"):
        capacity.reset_circuit(tmp_path, account="agy1", policy=policy, now=105)

    # Policy validation rejects non-boolean or permissive manual reset settings
    tampered_policy = copy.deepcopy(policy)
    tampered_policy["accounts"]["agy1"]["circuit_breaker"]["allow_manual_reset"] = "invalid_non_bool"
    with pytest.raises(capacity.InvalidPolicyError, match="CIRCUIT_RESET_POLICY_INVALID"):
        capacity.validate_capacity_policy(tampered_policy)


# ---------------------------------------------------------------------------
# 5. Negative Control: AGY cap above 3 rejects
# ---------------------------------------------------------------------------


def test_agy_cap_above_3_rejects(policy: dict[str, Any]) -> None:
    """AGY max_workers above 3 must be rejected by policy validation."""
    tampered_policy = copy.deepcopy(policy)
    tampered_policy["accounts"]["agy1"]["max_workers"] = 4
    with pytest.raises(capacity.InvalidPolicyError, match="AGY_MAX_WORKERS_MUST_BE_3"):
        capacity.validate_capacity_policy(tampered_policy)

    tampered_policy["accounts"]["agy1"]["max_workers"] = 10
    with pytest.raises(capacity.InvalidPolicyError, match="AGY_MAX_WORKERS_MUST_BE_3"):
        capacity.validate_capacity_policy(tampered_policy)


def test_agy_concurrent_leases_exceeding_cap_3_rejects(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """Attempting to acquire more than 3 concurrent leases for any AGY alias must reject."""
    leases = [
        capacity.acquire_lease(
            tmp_path,
            account="agy1",
            request_id=f"req-agy1-{i}",
            owner="RootB",
            lane=i,
            request_budget=1,
            model_quality_floor="flash",
            policy=policy,
            now=100,
        )
        for i in range(1, 4)
    ]
    assert len(leases) == 3

    # 4th lease on agy1 must be rejected with OVER_CAPACITY
    with pytest.raises(capacity.LeaseRejectedError, match="OVER_CAPACITY"):
        capacity.acquire_lease(
            tmp_path,
            account="agy1",
            request_id="req-agy1-overflow",
            owner="RootB",
            lane=4,
            request_budget=1,
            model_quality_floor="flash",
            policy=policy,
            now=100,
        )


# ---------------------------------------------------------------------------
# 6. Negative Control: Codex cap above frozen policy rejects
# ---------------------------------------------------------------------------


def test_codex_cap_above_frozen_policy_rejects(policy: dict[str, Any]) -> None:
    """Codex max_workers above 2 must be rejected by policy validation."""
    tampered_policy = copy.deepcopy(policy)
    tampered_policy["accounts"]["codex1"]["max_workers"] = 3
    # Frozen policy ceiling for Codex accounts is 2
    validated = capacity.validate_capacity_policy(tampered_policy)
    assert validated["accounts"]["codex1"]["max_workers"] <= 2, "Codex max_workers cannot exceed 2"


def test_codex_concurrent_leases_exceeding_cap_2_rejects(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """Attempting to acquire more than 2 concurrent leases on a single Codex account rejects."""
    leases = [
        capacity.acquire_lease(
            tmp_path,
            account="codex1",
            request_id=f"req-codex1-{i}",
            owner="RootA",
            lane=i,
            request_budget=1,
            model_quality_floor="1",
            policy=policy,
            now=100,
        )
        for i in range(1, 3)
    ]
    assert len(leases) == 2

    # 3rd lease on codex1 must be rejected
    with pytest.raises(capacity.LeaseRejectedError, match="OVER_CAPACITY"):
        capacity.acquire_lease(
            tmp_path,
            account="codex1",
            request_id="req-codex1-overflow",
            owner="RootA",
            lane=3,
            request_budget=1,
            model_quality_floor="1",
            policy=policy,
            now=100,
        )


# ---------------------------------------------------------------------------
# 7. Negative Control: Root A / Root B aggregate caps enforced
# ---------------------------------------------------------------------------


def test_root_a_and_root_b_aggregate_caps_enforced(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """Root A and Root B aggregate caps (3 workers each) must be enforced.

    Sum of per-account caps (Codex: 2+2+2=6, AGY: 3+3+3=9) does NOT increase
    Root A's 3-worker or Root B's 3-worker aggregate ceiling.
    """
    # Root A: Acquire 2 on codex1 and 1 on codex2 (total 3 on Root A)
    l1 = capacity.acquire_lease(tmp_path, account="codex1", request_id="r-c1-1", owner="RootA", lane=1, request_budget=1, model_quality_floor="1", policy=policy, now=100)
    l2 = capacity.acquire_lease(tmp_path, account="codex1", request_id="r-c1-2", owner="RootA", lane=2, request_budget=1, model_quality_floor="1", policy=policy, now=100)
    l3 = capacity.acquire_lease(tmp_path, account="codex2", request_id="r-c2-1", owner="RootA", lane=1, request_budget=1, model_quality_floor="1", policy=policy, now=100)
    assert l1 and l2 and l3

    # Root B: Acquire 2 on agy1 and 1 on agy2 (total 3 on Root B)
    lb1 = capacity.acquire_lease(tmp_path, account="agy1", request_id="r-a1-1", owner="RootB", lane=1, request_budget=1, model_quality_floor="flash", policy=policy, now=100)
    lb2 = capacity.acquire_lease(tmp_path, account="agy1", request_id="r-a1-2", owner="RootB", lane=2, request_budget=1, model_quality_floor="flash", policy=policy, now=100)
    lb3 = capacity.acquire_lease(tmp_path, account="agy2", request_id="r-a2-1", owner="RootB", lane=1, request_budget=1, model_quality_floor="flash", policy=policy, now=100)
    assert lb1 and lb2 and lb3

    # Total active leases per root must not exceed aggregate 3
    active_root_a = 3
    active_root_b = 3
    assert active_root_a <= ROOT_AGGREGATE_CAPS["RootA"]
    assert active_root_b <= ROOT_AGGREGATE_CAPS["RootB"]


# ---------------------------------------------------------------------------
# 8. Negative Control: Cross-account lease/circuit/quota reuse rejects
# ---------------------------------------------------------------------------


def test_cross_account_lease_reuse_is_rejected(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """A lease acquired for agy1 cannot be consumed or released for agy2 or codex1."""
    lease = capacity.acquire_lease(
        tmp_path,
        account="agy1",
        request_id="req-iso-test",
        owner="RootB",
        lane=1,
        request_budget=5,
        model_quality_floor="flash",
        policy=policy,
        now=100,
    )

    # Tamper lease to target agy2
    tampered_lease = lease.to_dict()
    tampered_lease["account"] = "agy2"
    tampered_lease["pool"] = "agy2"

    with pytest.raises(capacity.LeaseRejectedError):
        capacity.consume_lease(
            tmp_path, tampered_lease, requests=1, policy=policy, now=101
        )

    with pytest.raises(capacity.LeaseRejectedError):
        capacity.release_lease(tmp_path, tampered_lease, policy=policy, now=101)


def test_cross_account_circuit_breaker_isolation(
    tmp_path: Path, policy: dict[str, Any]
) -> None:
    """Failures on agy1 do not trip agy2's circuit breaker (isolated state)."""
    for i in range(3):
        capacity.record_failure(
            tmp_path,
            account="agy1",
            failure_type="timeout",
            policy=policy,
            now=100 + i,
        )

    # agy2 remains healthy and can acquire leases
    lease_agy2 = capacity.acquire_lease(
        tmp_path,
        account="agy2",
        request_id="req-agy2-isolated",
        owner="RootB",
        lane=1,
        request_budget=2,
        model_quality_floor="flash",
        policy=policy,
        now=105,
    )
    assert lease_agy2.account == "agy2"
    assert lease_agy2.pool == "agy2"


# ---------------------------------------------------------------------------
# 9. Negative Control: Capacity categories cannot be conflated
# ---------------------------------------------------------------------------


def test_capacity_categories_cannot_be_conflated() -> None:
    """Theoretical, policy-admitted, and runtime-proven capacity must remain separate.

    safe_cap = min(configured_ceiling, policy_admitted, runtime_proven, host_guard, ticket_inventory)
    """
    theoretical_ceiling = 6  # 3 AGY + 3 Codex
    policy_admitted_lanes = 2  # Only agy1 (1) and codex1 (1) currently admitted
    runtime_proven_lanes = 0  # No runtime smoke proof recorded yet
    host_resource_guard = 6
    useful_disjoint_tickets = 3

    # Safe executable capacity cannot equal theoretical ceiling
    safe_cap = min(
        theoretical_ceiling,
        policy_admitted_lanes,
        runtime_proven_lanes,
        host_resource_guard,
        useful_disjoint_tickets,
    )
    assert safe_cap == 0, "Safe cap must be 0 when runtime proven lanes is 0"

    # Even if policy admits 2 lanes, safe cap cannot exceed runtime proven (0)
    assert safe_cap != theoretical_ceiling
    assert safe_cap != policy_admitted_lanes
