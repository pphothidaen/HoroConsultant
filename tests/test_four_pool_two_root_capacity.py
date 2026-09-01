"""Provider-free regression for the two-root, seven-pool S3 topology.

These tests exercise only local capacity leases and scheduler admission.  The
configured caps are governance limits, not provider-native capacity proof.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import multiagent_capacity as capacity
from scripts import multiagent_ticket_scheduler as scheduler


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agents/config/s3_capacity_policy.json"
ACCOUNTS = ("codex1", "codex2", "codex3", "agy1", "agy2", "agy3", "agy4")
ROOT_OWNER = {
    "codex1": "RootA",
    "codex2": "RootA",
    "codex3": "RootA",
    "agy1": "RootB",
    "agy2": "RootB",
    "agy3": "RootB",
    "agy4": "RootB",
}
HARD_LOCAL_CAPS = {"codex1": 2, "codex2": 2, "codex3": 2, "agy1": 3, "agy2": 3, "agy3": 3, "agy4": 3}
S3_OPERATING_TARGET_LANES = (1, 2)


@pytest.fixture
def policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _acquire(
    store: Path,
    policy: dict[str, object],
    account: str,
    lane: int,
    *,
    request_suffix: str = "base",
) -> capacity.CapacityLease:
    return capacity.acquire_lease(
        store,
        account=account,
        request_id=f"{account}-{request_suffix}-lane-{lane}",
        owner=ROOT_OWNER[account],
        lane=lane,
        request_budget=1,
        model_quality_floor="1",
        policy=policy,
        now=100,
    )


def _fill_to_hard_caps(
    store: Path, policy: dict[str, object]
) -> dict[str, list[capacity.CapacityLease]]:
    return {
        account: [
            _acquire(store, policy, account, lane)
            for lane in range(1, HARD_LOCAL_CAPS[account] + 1)
        ]
        for account in ACCOUNTS
    }


def _provider_state() -> dict[str, object]:
    return {
        "providers": {
            "codex": {"state": "healthy"},
            "agy": {"state": "healthy"},
        },
        "accounts": {
            account: {"state": "healthy"} for account in ACCOUNTS
        },
    }


def _scheduler_snapshot(
    *, ticket_id: str, owner: str, ownership: str
) -> scheduler.SchedulingSnapshot:
    return scheduler.validate_snapshot(
        {
            "schema_version": 1,
            "tickets": [
                {
                    "ticket_id": ticket_id,
                    "severity": "HIGH",
                    "work_effort": "S",
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
    )


def test_minimum_floor_has_one_isolated_lease_per_pool_and_two_root_ownership(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    leases = {
        account: _acquire(tmp_path, policy, account, 1, request_suffix="floor")
        for account in ACCOUNTS
    }

    assert len(leases) == 7
    assert {lease.account for lease in leases.values()} == set(ACCOUNTS)
    assert {lease.pool for lease in leases.values()} == set(ACCOUNTS)
    for account, lease in leases.items():
        assert lease.owner == ROOT_OWNER[account]
        assert lease.provider == ("codex" if account.startswith("codex") else "agy")

    snapshot = capacity.capacity_snapshot(tmp_path, policy=policy, now=101)
    assert sum(item["active_workers"] for item in snapshot["accounts"].values()) == 7
    assert all(snapshot["accounts"][account]["active_workers"] == 1 for account in ACCOUNTS)


def test_hard_local_caps_sum_to_eighteen_and_each_next_lease_is_rejected(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    normalized = capacity.validate_capacity_policy(policy)
    assert {
        account: normalized["accounts"][account]["max_workers"]
        for account in ACCOUNTS
    } == HARD_LOCAL_CAPS

    leases = _fill_to_hard_caps(tmp_path, policy)
    assert sum(len(items) for items in leases.values()) == 18
    snapshot = capacity.capacity_snapshot(tmp_path, policy=policy, now=101)
    assert sum(item["active_workers"] for item in snapshot["accounts"].values()) == 18
    assert all(snapshot["accounts"][account]["available_workers"] == 0 for account in ACCOUNTS)

    for account in ACCOUNTS:
        with pytest.raises(capacity.LeaseRejectedError) as exc:
            _acquire(
                tmp_path,
                policy,
                account,
                HARD_LOCAL_CAPS[account] + 1,
                request_suffix="over",
            )
        assert exc.value.code == "OVER_CAPACITY"


def test_release_opens_only_the_released_account_pool(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    leases = _fill_to_hard_caps(tmp_path, policy)
    released_account = "agy1"
    capacity.release_lease(
        tmp_path,
        leases[released_account][0],
        policy=policy,
        now=101,
    )

    reopened = capacity.acquire_lease(
        tmp_path,
        account=released_account,
        request_id="agy1-reopened",
        owner="RootB",
        lane=1,
        request_budget=1,
        model_quality_floor="1",
        policy=policy,
        now=102,
    )
    assert reopened.account == released_account

    for account in set(ACCOUNTS) - {released_account}:
        with pytest.raises(capacity.LeaseRejectedError) as exc:
            _acquire(
                tmp_path,
                policy,
                account,
                HARD_LOCAL_CAPS[account] + 1,
                request_suffix="still-full",
            )
        assert exc.value.code == "OVER_CAPACITY"

    snapshot = capacity.capacity_snapshot(tmp_path, policy=policy, now=103)
    assert sum(item["active_workers"] for item in snapshot["accounts"].values()) == 18
    assert all(snapshot["accounts"][account]["available_workers"] == 0 for account in ACCOUNTS)


def test_s3_operating_target_is_separate_from_hard_caps_and_runtime_proof(
    policy: dict[str, object]
) -> None:
    normalized = capacity.validate_capacity_policy(policy)

    assert S3_OPERATING_TARGET_LANES == (1, 2)
    assert all(
        S3_OPERATING_TARGET_LANES[-1]
        <= normalized["accounts"][account]["max_workers"]
        for account in ACCOUNTS
    )
    assert normalized["accounts"]["agy1"]["max_workers"] == 3
    assert normalized["accounts"]["agy2"]["max_workers"] == 3
    assert normalized["accounts"]["agy3"]["max_workers"] == 3
    assert normalized["accounts"]["agy4"]["max_workers"] == 3
    assert normalized["accounts"]["codex1"]["max_workers"] == 2
    assert normalized["accounts"]["codex2"]["max_workers"] == 2
    assert normalized["accounts"]["codex3"]["max_workers"] == 2
    assert normalized["quota_source"] == "configured_placeholder"
    assert "not a provider execution receipt" in capacity.CapacityLease.__doc__.lower()


def test_scheduler_caller_reaches_sum_of_local_caps_without_global_native_ceiling(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    leases: list[capacity.CapacityLease] = []
    for account in ACCOUNTS:
        provider = "codex" if account.startswith("codex") else "agy"
        root_b_role = {"agy1": "primary", "agy2": "secondary"}.get(account)
        for lane in range(1, HARD_LOCAL_CAPS[account] + 1):
            ticket_id = f"TICKET-{account.upper()}-{lane}"
            ownership = f"capacity/{account}/{lane}"
            leases.append(
                scheduler.admit_dispatch_capacity(
                    _scheduler_snapshot(
                        ticket_id=ticket_id,
                        owner=ROOT_OWNER[account],
                        ownership=ownership,
                    ),
                    ticket_id=ticket_id,
                    owner=ROOT_OWNER[account],
                    ownership=(ownership,),
                    decision_valid=True,
                    store_path=str(tmp_path),
                    account=account,
                    request_id=f"scheduler-{account}-{lane}",
                    lane=lane,
                    request_budget=1,
                    model_quality_floor="1",
                    policy=policy,
                    provider=provider,
                    provider_account_state=_provider_state(),
                    root_b_role=root_b_role,
                    attempt=1,
                    retry_request_id=f"retry-{account}-{lane}",
                )
            )

    assert len(leases) == sum(HARD_LOCAL_CAPS.values()) == 18
    snapshot = capacity.capacity_snapshot(tmp_path, policy=policy, now=101)
    assert sum(item["active_workers"] for item in snapshot["accounts"].values()) == 18
    assert snapshot["accounts"]["agy1"]["max_workers"] == 3
    assert snapshot["accounts"]["agy2"]["max_workers"] == 3
    assert snapshot["accounts"]["agy3"]["max_workers"] == 3
    assert snapshot["accounts"]["agy4"]["max_workers"] == 3
    assert snapshot["accounts"]["codex3"]["max_workers"] == 2
    assert all(lease.request_budget == 1 for lease in leases)
