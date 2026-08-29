"""Frozen public contract for the single-host durable multi-agent queue.

These tests intentionally exercise only the public store surface plus SQLite's
observable state.  They do not prescribe a particular query layout or ORM.
"""

from __future__ import annotations

import importlib
import json
import os
import sqlite3
import stat
import threading
from collections.abc import Mapping
from pathlib import Path

import pytest


@pytest.fixture
def dq():
    return importlib.import_module("scripts.multiagent_durable_queue")


@pytest.fixture
def store(dq, tmp_path: Path):
    return dq.DurableQueue(tmp_path / "state" / "durable-queue.sqlite3")


def _field(value: object, name: str):
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _submit(
    store,
    request_id: str = "req-1",
    *,
    key: str = "idem-1",
    alias: str = "codex1",
    root: str = "A",
    payload: Mapping[str, object] | None = None,
    retry_budget: int = 1,
):
    return store.submit(
        request_id=request_id,
        idempotency_key=key,
        payload=dict(payload or {"objective": "read repository status"}),
        root=root,
        alias=alias,
        work_mode="read_only",
        attempt=1,
        retry_budget=retry_budget,
    )


def _claim(store, *, root: str = "A", instance: str = "root-a-1"):
    aliases = {"codex1", "codex2"} if root == "A" else {"agy1", "agy2"}
    return store.claim(root=root, instance_id=instance, aliases=aliases)


def _connect(store) -> sqlite3.Connection:
    connection = sqlite3.connect(str(store.path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection


def _set_lease_deadline(store, request_id: str, expression: str) -> None:
    with _connect(store) as connection:
        connection.execute(
            f"UPDATE leases SET expires_at = {expression} WHERE request_id = ?",
            (request_id,),
        )


def test_v1_migration_is_idempotent_and_has_closed_schema(dq, tmp_path: Path) -> None:
    path = tmp_path / "state" / "queue.sqlite3"
    first = dq.DurableQueue(path)
    first.close()
    second = dq.DurableQueue(path)

    with _connect(second) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        migrations = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()

    assert {
        "jobs",
        "leases",
        "results",
        "outbox",
        "root_instances",
        "risk_acceptances",
        "schema_migrations",
    } <= tables
    assert [row[0] for row in migrations] == [1]


def test_database_pragmas_and_private_file_modes_are_enforced(store) -> None:
    _submit(store)
    with _connect(store) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert str(journal_mode).lower() == "wal"
    assert foreign_keys == 1
    assert synchronous == 2  # SQLite's numeric value for FULL.
    assert busy_timeout == 5000
    assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700
    for path in store.path.parent.glob(f"{store.path.name}*"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, path


def test_same_idempotency_key_and_digest_returns_original_job(store) -> None:
    first = _submit(store)
    again = _submit(store, request_id="req-different")

    assert _field(again, "request_id") == _field(first, "request_id") == "req-1"
    with _connect(store) as connection:
        assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1


def test_same_idempotency_key_with_different_digest_is_rejected(dq, store) -> None:
    _submit(store, payload={"objective": "first"})

    with pytest.raises(dq.IdempotencyConflict):
        _submit(store, request_id="req-2", payload={"objective": "different"})


def test_claim_race_has_one_winner_and_uses_monotonic_fence(dq, tmp_path: Path) -> None:
    path = tmp_path / "race" / "queue.sqlite3"
    creator = dq.DurableQueue(path)
    _submit(creator)
    creator.close()
    barrier = threading.Barrier(2)
    claims: list[object] = []

    def contender(instance: str) -> None:
        candidate = dq.DurableQueue(path)
        barrier.wait()
        claim = _claim(candidate, instance=instance)
        if claim is not None:
            claims.append(claim)
        candidate.close()

    threads = [
        threading.Thread(target=contender, args=("root-a-1",)),
        threading.Thread(target=contender, args=("root-a-2",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert all(not thread.is_alive() for thread in threads)
    assert len(claims) == 1
    assert _field(claims[0], "fence") == 1


def test_claim_lease_uses_database_clock_and_locked_120_second_ttl(store) -> None:
    _submit(store)
    claim = _claim(store)

    with _connect(store) as connection:
        delta = connection.execute(
            "SELECT (julianday(expires_at) - julianday(claimed_at)) * 86400 "
            "FROM leases WHERE request_id = ?",
            ("req-1",),
        ).fetchone()[0]
        encloses_db_now = connection.execute(
            "SELECT claimed_at <= CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP <= expires_at "
            "FROM leases WHERE request_id = ?",
            ("req-1",),
        ).fetchone()[0]

    assert claim is not None
    assert delta == pytest.approx(120, abs=0.01)
    assert encloses_db_now == 1


@pytest.mark.parametrize(
    ("root", "alias", "eligible"),
    [
        ("A", "codex1", True),
        ("A", "agy1", False),
        ("B", "agy2", True),
        ("B", "codex2", False),
    ],
)
def test_claim_enforces_root_and_account_predicates(store, root, alias, eligible) -> None:
    expected_root = "A" if alias.startswith("codex") else "B"
    _submit(store, alias=alias, root=expected_root)

    claim = _claim(store, root=root, instance=f"root-{root.lower()}-1")

    assert (claim is not None) is eligible


def test_heartbeat_renews_at_40_seconds_and_rejects_stale_fence(dq, store) -> None:
    _submit(store)
    claim = _claim(store)

    renewed = store.heartbeat(
        request_id="req-1",
        fence=_field(claim, "fence"),
        instance_id="root-a-1",
    )
    with _connect(store) as connection:
        interval = connection.execute(
            "SELECT heartbeat_interval_seconds FROM leases WHERE request_id = ?",
            ("req-1",),
        ).fetchone()[0]

    assert renewed is True
    assert interval == 40
    with pytest.raises(dq.StaleFenceError):
        store.heartbeat(request_id="req-1", fence=0, instance_id="root-a-1")


@pytest.mark.parametrize("state", ["CLAIMED", "PREPARED"])
def test_expired_pre_start_lease_requeues_within_retry_budget(store, state) -> None:
    _submit(store, retry_budget=1)
    claim = _claim(store)
    store.transition("req-1", _field(claim, "fence"), state)
    _set_lease_deadline(store, "req-1", "datetime('now', '-1 second')")

    recovery = store.recover_expired()
    job = store.get_job("req-1")

    assert [_field(item, "request_id") for item in recovery] == ["req-1"]
    assert _field(job, "state") == "QUEUED"
    assert _field(job, "attempt") == 2


@pytest.mark.parametrize("state", ["STARTING", "RUNNING"])
def test_expired_post_start_lease_becomes_unknown_without_retry(store, state) -> None:
    _submit(store, retry_budget=3)
    claim = _claim(store)
    store.transition("req-1", _field(claim, "fence"), state)
    _set_lease_deadline(store, "req-1", "datetime('now', '-1 second')")

    store.recover_expired()
    job = store.get_job("req-1")

    assert _field(job, "state") == "UNKNOWN"
    assert _field(job, "attempt") == 1
    assert _claim(store) is None


def test_zero_grace_recovers_at_exact_database_deadline(store) -> None:
    _submit(store)
    _claim(store)
    _set_lease_deadline(store, "req-1", "CURRENT_TIMESTAMP")

    store.recover_expired()

    assert _field(store.get_job("req-1"), "state") == "QUEUED"


def test_exhausted_pre_start_retry_budget_dead_letters(store) -> None:
    _submit(store, retry_budget=0)
    _claim(store)
    _set_lease_deadline(store, "req-1", "datetime('now', '-1 second')")

    store.recover_expired()

    assert _field(store.get_job("req-1"), "state") == "DEAD_LETTER"


def test_reclaim_increments_fence_and_stale_result_is_rejected(dq, store) -> None:
    _submit(store, retry_budget=1)
    first = _claim(store, instance="root-a-old")
    _set_lease_deadline(store, "req-1", "datetime('now', '-1 second')")
    store.recover_expired()
    second = _claim(store, instance="root-a-new")

    assert _field(second, "fence") > _field(first, "fence")
    with pytest.raises(dq.StaleFenceError):
        store.complete(
            request_id="req-1",
            fence=_field(first, "fence"),
            instance_id="root-a-old",
            result={"status": "DONE", "findings": []},
            receipt={"protocol_version": 2},
        )


def test_result_and_outbox_commit_atomically(store) -> None:
    _submit(store)
    claim = _claim(store)
    with _connect(store) as connection:
        connection.execute(
            "CREATE TRIGGER abort_outbox BEFORE INSERT ON outbox "
            "BEGIN SELECT RAISE(ABORT, 'forced outbox failure'); END"
        )

    with pytest.raises(sqlite3.DatabaseError, match="forced outbox failure"):
        store.complete(
            request_id="req-1",
            fence=_field(claim, "fence"),
            instance_id="root-a-1",
            result={"status": "DONE", "findings": []},
            receipt={"protocol_version": 2},
        )

    with _connect(store) as connection:
        assert connection.execute("SELECT count(*) FROM results").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    assert _field(store.get_job("req-1"), "state") not in {"DONE", "FAILED"}


def test_outbox_replays_from_durable_cursor_without_loss_or_duplicates(store) -> None:
    for number in range(3):
        _submit(store, request_id=f"req-{number}", key=f"key-{number}")
        claim = _claim(store)
        store.complete(
            request_id=f"req-{number}",
            fence=_field(claim, "fence"),
            instance_id="root-a-1",
            result={"status": "DONE", "findings": []},
            receipt={"protocol_version": 2},
        )

    first_page = store.read_outbox(after_cursor=0, limit=2)
    replay = store.read_outbox(after_cursor=0, limit=2)
    cursor = _field(first_page[-1], "cursor")
    second_page = store.read_outbox(after_cursor=cursor, limit=2)

    assert [(_field(x, "cursor"), _field(x, "request_id")) for x in replay] == [
        (_field(x, "cursor"), _field(x, "request_id")) for x in first_page
    ]
    combined = first_page + second_page
    assert len({_field(item, "cursor") for item in combined}) == 3
    assert {_field(item, "request_id") for item in combined} == {
        "req-0",
        "req-1",
        "req-2",
    }


@pytest.mark.parametrize("forbidden", ["stdout", "stderr", "raw_stream", "events"])
def test_raw_provider_stream_fields_are_rejected_and_never_persisted(
    dq, store, forbidden
) -> None:
    marker = f"RAW-PROVIDER-STREAM-{forbidden}"
    _submit(store)
    claim = _claim(store)

    with pytest.raises(dq.UnsafePersistenceError):
        store.complete(
            request_id="req-1",
            fence=_field(claim, "fence"),
            instance_id="root-a-1",
            result={"status": "DONE", forbidden: marker},
            receipt={"protocol_version": 2},
        )

    store.close()
    persisted = b"".join(
        path.read_bytes()
        for path in store.path.parent.glob(f"{store.path.name}*")
        if path.is_file()
    )
    assert marker.encode() not in persisted
    assert json.dumps({forbidden: marker}).encode() not in persisted


def test_database_artifacts_are_owner_only_even_under_permissive_umask(dq, tmp_path) -> None:
    old_umask = os.umask(0)
    try:
        private_store = dq.DurableQueue(tmp_path / "permissive" / "queue.sqlite3")
        _submit(private_store)
    finally:
        os.umask(old_umask)

    assert stat.S_IMODE(private_store.path.parent.stat().st_mode) == 0o700
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o600
        for path in private_store.path.parent.glob(f"{private_store.path.name}*")
    )
