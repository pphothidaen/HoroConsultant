"""Fresh release-cycle contract for the local independent-roots IDQ MVP.

The reconstructed MVP-010 tests remain immutable historical evidence.  This
small cohort binds the release-intended queue, worker, supervisor, and capacity
surfaces from a clean committed tree where the three IDQ runtime modules do not
exist yet.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path


EXPECTED_ACCOUNT_CAPS = {
    "codex1": 2,
    "codex2": 2,
    "agy1": 3,
    "agy2": 3,
}


def _field(value: object, name: str):
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _capacity_policy() -> dict:
    path = Path(__file__).parents[1] / ".agents/config/s3_capacity_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_capacity_policy_is_the_four_account_positive_control() -> None:
    capacity = importlib.import_module("scripts.multiagent_capacity")

    policy = capacity.validate_capacity_policy(_capacity_policy())

    assert {
        alias: account["max_workers"]
        for alias, account in policy["accounts"].items()
    } == EXPECTED_ACCOUNT_CAPS
    assert policy["accounts"]["codex1"]["provider"] == "codex"
    assert policy["accounts"]["agy1"]["provider"] == "agy"


def test_queue_claim_and_capacity_lease_bind_the_same_request_and_alias(
    tmp_path: Path,
) -> None:
    capacity = importlib.import_module("scripts.multiagent_capacity")
    policy = capacity.validate_capacity_policy(_capacity_policy())
    capacity_lease = capacity.acquire_lease(
        tmp_path / "capacity",
        account="codex1",
        request_id="idq-release-cycle-1",
        owner="root-a-instance",
        lane=1,
        request_budget=1,
        model_quality_floor="gpt-5.6-luna",
        policy=policy,
        now=100,
        ttl_seconds=120,
    )
    durable_queue = importlib.import_module("scripts.multiagent_durable_queue")
    store = durable_queue.DurableQueue(tmp_path / "queue" / "queue.sqlite3")
    submitted = store.submit(
        request_id="idq-release-cycle-1",
        idempotency_key="idq-release-cycle-key-1",
        payload={"objective": "inspect repository read-only"},
        root="A",
        alias="codex1",
        work_mode="read_only",
        attempt=1,
        retry_budget=1,
    )

    claimed = store.claim(
        root="A",
        instance_id="root-a-instance",
        aliases={"codex1", "codex2"},
    )

    assert _field(submitted, "request_id") == capacity_lease.request_id
    assert _field(claimed, "request_id") == capacity_lease.request_id
    assert _field(claimed, "alias") == capacity_lease.account == "codex1"
    assert capacity_lease.ttl_seconds == 120


def test_worker_root_policy_matches_capacity_without_cross_account_borrowing() -> None:
    capacity = importlib.import_module("scripts.multiagent_capacity")
    policy = capacity.validate_capacity_policy(_capacity_policy())
    worker = importlib.import_module("scripts.multiagent_root_worker")

    root_a = worker.RootPolicy.for_root("A")
    root_b = worker.RootPolicy.for_root("B")

    assert set(root_a.aliases) == {"codex1", "codex2"}
    assert set(root_b.aliases) == {"agy1", "agy2"}
    assert dict(root_a.account_caps) == {
        alias: policy["accounts"][alias]["max_workers"] for alias in root_a.aliases
    }
    assert dict(root_b.account_caps) == {
        alias: policy["accounts"][alias]["max_workers"] for alias in root_b.aliases
    }
    assert set(root_a.aliases).isdisjoint(root_b.aliases)


class _FakeProcess:
    next_pid = 51000

    def __init__(self, root: str, instance_id: str) -> None:
        type(self).next_pid += 1
        self.pid = type(self).next_pid
        self.root = root
        self.instance_id = instance_id
        self.alive = True

    def poll(self):
        return None if self.alive else 0

    def terminate(self) -> None:
        self.alive = False

    def kill(self) -> None:
        self.alive = False


class _ProcessFactory:
    def __init__(self) -> None:
        self.processes: list[_FakeProcess] = []

    def __call__(self, *, root: str, instance_id: str, **_kwargs) -> _FakeProcess:
        process = _FakeProcess(root, instance_id)
        self.processes.append(process)
        return process

    def probe(self, pid: int) -> bool:
        return any(process.pid == pid and process.alive for process in self.processes)


def test_supervisor_starts_two_independent_restartable_roots(tmp_path: Path) -> None:
    supervisor_module = importlib.import_module("scripts.multiagent_root_supervisor")
    factory = _ProcessFactory()
    supervisor = supervisor_module.RootSupervisor(
        state_dir=tmp_path / "state",
        process_factory=factory,
        pid_probe=factory.probe,
    )
    supervisor.init()

    status = supervisor.start()
    roots = {_field(item, "root"): item for item in _field(status, "roots")}

    assert set(roots) == {"A", "B"}
    assert _field(roots["A"], "pid") != _field(roots["B"], "pid")
    assert _field(roots["A"], "instance_id") != _field(roots["B"], "instance_id")
    assert all(_field(item, "detached") is True for item in roots.values())
