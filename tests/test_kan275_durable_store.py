"""KAN-275: the nightly sync must write its bookkeeping to a durable store.

The defect: scripts/sync_gdrive_vault.py writes the vault and the vector-store
metadata to a container-local path. On Render's free tier the filesystem is
ephemeral and the instance spins down after 15 minutes idle, so the synced
output is discarded while the status file still reports success — the same
silent-success failure class as KAN-273.

These tests pin the durable contract: an idempotency key, a lease with a fencing
token, and a heartbeat, all persisted through a pluggable store. The `local`
backend is exercised here; the `d1` backend shares the same interface.
"""
from pathlib import Path

import pytest

from scripts.durable_store import DurableStore, LeaseHeldError


def test_local_backend_round_trips_bookkeeping(tmp_path: Path) -> None:
    store = DurableStore.local(tmp_path / "state.json")
    store.begin_run(run_key="sync-2026-10-08", owner="render-1")
    store.heartbeat(run_key="sync-2026-10-08", step="download", detail="2/5 folders")
    store.complete_run(run_key="sync-2026-10-08", vectors=135)

    state = store.read()
    assert state["last_success"]["run_key"] == "sync-2026-10-08"
    assert state["last_success"]["vectors"] == 135
    assert state["last_success"]["heartbeat"]["step"] == "download"


def test_a_second_concurrent_run_is_refused(tmp_path: Path) -> None:
    store = DurableStore.local(tmp_path / "state.json")
    store.begin_run(run_key="sync-2026-10-08", owner="render-1")
    with pytest.raises(LeaseHeldError):
        store.begin_run(run_key="sync-2026-10-08", owner="render-2")


def test_an_expired_lease_can_be_taken_over_with_a_higher_fence(tmp_path: Path) -> None:
    store = DurableStore.local(tmp_path / "state.json")
    first = store.begin_run(run_key="sync-2026-10-08", owner="render-1", lease_seconds=0)
    second = store.begin_run(run_key="sync-2026-10-08", owner="render-2", lease_seconds=60)
    assert second["fencing_token"] > first["fencing_token"]


def test_an_unreachable_store_fails_loudly(tmp_path: Path) -> None:
    store = DurableStore.local(tmp_path / "no-such-dir" / "state.json")
    with pytest.raises(OSError):
        store.begin_run(run_key="sync-2026-10-08", owner="render-1")


def test_a_stale_heartbeat_is_detectable(tmp_path: Path) -> None:
    store = DurableStore.local(tmp_path / "state.json")
    store.begin_run(run_key="sync-2026-10-08", owner="render-1")
    assert store.is_stale(max_age_seconds=0) is True
