"""Frozen behavior for independent Root A / Root B worker daemons."""

from __future__ import annotations

import importlib
import threading
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import pytest


@pytest.fixture
def dq():
    return importlib.import_module("scripts.multiagent_durable_queue")


@pytest.fixture
def worker_module():
    return importlib.import_module("scripts.multiagent_root_worker")


@pytest.fixture
def store(dq, tmp_path: Path):
    return dq.DurableQueue(tmp_path / "worker-state" / "queue.sqlite3")


def _field(value: object, name: str):
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _submit(store, number: int, alias: str, root: str):
    return store.submit(
        request_id=f"req-{root}-{alias}-{number}",
        idempotency_key=f"key-{root}-{alias}-{number}",
        payload={"objective": f"read-only task {number}"},
        root=root,
        alias=alias,
        work_mode="read_only",
        attempt=1,
        retry_budget=1,
    )


class RecordingDispatcher:
    def __init__(self) -> None:
        self.aliases: list[str] = []

    def __call__(self, job, lifecycle) -> tuple[dict, dict]:
        self.aliases.append(_field(job, "alias"))
        lifecycle.prepared()
        lifecycle.starting()
        lifecycle.provider_started()
        return (
            {"status": "DONE", "findings": [], "changed_files": []},
            {"protocol_version": 2, "provider_session_id": "safe-session"},
        )


class BlockingDispatcher(RecordingDispatcher):
    def __init__(self) -> None:
        super().__init__()
        self.release = threading.Event()
        self.started = threading.Event()
        self.lock = threading.Lock()
        self.active = Counter()
        self.max_active = Counter()

    def __call__(self, job, lifecycle):
        alias = _field(job, "alias")
        lifecycle.prepared()
        lifecycle.starting()
        lifecycle.provider_started()
        with self.lock:
            self.aliases.append(alias)
            self.active[alias] += 1
            self.active["all"] += 1
            self.max_active[alias] = max(self.max_active[alias], self.active[alias])
            self.max_active["all"] = max(self.max_active["all"], self.active["all"])
            self.started.set()
        self.release.wait(timeout=5)
        with self.lock:
            self.active[alias] -= 1
            self.active["all"] -= 1
        return (
            {"status": "DONE", "findings": [], "changed_files": []},
            {"protocol_version": 2, "provider_session_id": f"session-{alias}"},
        )


def _worker(worker_module, store, root: str, dispatcher, **kwargs):
    return worker_module.RootWorker(
        store=store,
        root=root,
        instance_id=f"root-{root.lower()}-instance",
        dispatcher=dispatcher,
        **kwargs,
    )


def test_root_policies_lock_aliases_pool_size_and_account_caps(worker_module) -> None:
    root_a = worker_module.RootPolicy.for_root("A")
    root_b = worker_module.RootPolicy.for_root("B")

    assert set(root_a.aliases) == {"codex1", "codex2"}
    assert set(root_b.aliases) == {"agy1", "agy2"}
    assert root_a.max_workers == root_b.max_workers == 3
    assert dict(root_a.account_caps) == {"codex1": 2, "codex2": 2}
    assert dict(root_b.account_caps) == {"agy1": 3, "agy2": 3}


@pytest.mark.parametrize("invalid", ["", "C", "codex1", None])
def test_unknown_root_is_rejected(worker_module, invalid) -> None:
    with pytest.raises((ValueError, TypeError)):
        worker_module.RootPolicy.for_root(invalid)


def test_root_a_never_claims_agy_and_root_b_never_claims_codex(
    worker_module, store
) -> None:
    _submit(store, 1, "codex1", "A")
    _submit(store, 2, "agy1", "B")
    codex_dispatch = RecordingDispatcher()
    agy_dispatch = RecordingDispatcher()
    root_a = _worker(worker_module, store, "A", codex_dispatch)
    root_b = _worker(worker_module, store, "B", agy_dispatch)

    root_a.poll_once()
    root_b.poll_once()
    root_a.wait_idle(timeout=5)
    root_b.wait_idle(timeout=5)

    assert codex_dispatch.aliases == ["codex1"]
    assert agy_dispatch.aliases == ["agy1"]


def test_each_root_pool_never_exceeds_three_concurrent_workers(worker_module, store) -> None:
    for number in range(6):
        _submit(store, number, "agy1" if number % 2 else "agy2", "B")
    dispatcher = BlockingDispatcher()
    root = _worker(worker_module, store, "B", dispatcher)

    assert root.poll_once() == 3
    assert dispatcher.started.wait(timeout=2)
    assert root.poll_once() == 0
    assert dispatcher.max_active["all"] <= 3
    dispatcher.release.set()
    root.wait_idle(timeout=5)


@pytest.mark.parametrize(
    ("root", "alias", "cap"),
    [("A", "codex1", 2), ("A", "codex2", 2), ("B", "agy1", 3), ("B", "agy2", 3)],
)
def test_account_caps_are_enforced_inside_root_pool(
    worker_module, dq, tmp_path, root, alias, cap
) -> None:
    local_store = dq.DurableQueue(tmp_path / f"cap-{alias}" / "queue.sqlite3")
    for number in range(5):
        _submit(local_store, number, alias, root)
    dispatcher = BlockingDispatcher()
    daemon = _worker(worker_module, local_store, root, dispatcher)

    daemon.poll_once()
    assert dispatcher.started.wait(timeout=2)

    assert dispatcher.max_active[alias] <= cap
    dispatcher.release.set()
    daemon.wait_idle(timeout=5)


def test_backpressure_denial_leaves_job_queued_and_does_not_dispatch(
    worker_module, store
) -> None:
    _submit(store, 1, "codex1", "A")
    dispatcher = RecordingDispatcher()
    root = _worker(
        worker_module,
        store,
        "A",
        dispatcher,
        admission=lambda job: worker_module.AdmissionDecision(
            allowed=False, code="BACKPRESSURE"
        ),
    )

    assert root.poll_once() == 0
    assert dispatcher.aliases == []
    assert _field(store.get_job("req-A-codex1-1"), "state") == "QUEUED"


def test_open_circuit_leaves_job_queued_without_cross_alias_fallback(
    worker_module, store
) -> None:
    _submit(store, 1, "codex1", "A")
    dispatcher = RecordingDispatcher()

    def admission(job):
        assert _field(job, "alias") == "codex1"
        return worker_module.AdmissionDecision(allowed=False, code="CIRCUIT_OPEN")

    root = _worker(worker_module, store, "A", dispatcher, admission=admission)
    root.poll_once()

    assert dispatcher.aliases == []
    assert _field(store.get_job("req-A-codex1-1"), "alias") == "codex1"
    assert _field(store.get_job("req-A-codex1-1"), "state") == "QUEUED"


def test_root_and_worker_heartbeats_are_persisted_with_fence(worker_module, store) -> None:
    root = _worker(worker_module, store, "A", RecordingDispatcher())

    registration = root.register()
    heartbeat = root.heartbeat_once()
    persisted = store.get_root_instance("root-a-instance")

    assert _field(registration, "fence") >= 1
    assert _field(heartbeat, "fence") == _field(registration, "fence")
    assert _field(persisted, "root") == "A"
    assert _field(persisted, "heartbeat_at") is not None


def test_stale_root_fence_cannot_heartbeat_or_write_result(
    worker_module, dq, store
) -> None:
    old = _worker(worker_module, store, "A", RecordingDispatcher())
    first = old.register()
    replacement = _worker(worker_module, store, "A", RecordingDispatcher())
    second = replacement.register(replace_stale=True)

    assert _field(second, "fence") > _field(first, "fence")
    with pytest.raises(dq.StaleFenceError):
        old.heartbeat_once()


@pytest.mark.parametrize(
    ("phase", "expected_state", "expected_attempt"),
    [
        ("prepared", "QUEUED", 2),
        ("starting", "UNKNOWN", 1),
        ("provider_started", "UNKNOWN", 1),
    ],
)
def test_worker_crash_semantics_depend_on_provider_start_boundary(
    worker_module, store, phase, expected_state, expected_attempt
) -> None:
    _submit(store, 1, "codex1", "A")
    worker_module.run_crash_fixture(
        store=store,
        root="A",
        instance_id="root-a-crash",
        request_id="req-A-codex1-1",
        crash_after=phase,
    )

    store.recover_expired(force_instance_id="root-a-crash")
    job = store.get_job("req-A-codex1-1")

    assert _field(job, "state") == expected_state
    assert _field(job, "attempt") == expected_attempt


def test_blocked_auth_and_executable_are_terminal_typed_results(
    worker_module, store
) -> None:
    for number, code in enumerate(("BLOCKED_AUTH", "BLOCKED_EXECUTABLE"), start=1):
        _submit(store, number, "codex1", "A")

        def blocked(_job, _lifecycle, code=code):
            raise worker_module.DispatchBlocked(code)

        root = _worker(worker_module, store, "A", blocked)
        root.poll_once()
        root.wait_idle(timeout=5)
        job = store.get_job(f"req-A-codex1-{number}")
        result = store.get_result(f"req-A-codex1-{number}")
        assert _field(job, "state") == "BLOCKED"
        assert _field(result, "status") == code


def test_dispatch_exception_never_falls_back_to_another_alias(worker_module, store) -> None:
    _submit(store, 1, "codex1", "A")
    attempted: list[str] = []

    def failing(job, lifecycle):
        attempted.append(_field(job, "alias"))
        lifecycle.prepared()
        raise RuntimeError("provider unavailable")

    root = _worker(worker_module, store, "A", failing)
    root.poll_once()
    root.wait_idle(timeout=5)

    assert attempted == ["codex1"]
    assert _field(store.get_job("req-A-codex1-1"), "alias") == "codex1"
