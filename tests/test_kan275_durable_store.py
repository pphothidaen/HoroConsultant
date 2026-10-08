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


# --------------------------------------------------------------------------- #
# KAN-275 M7: the d1 backend (production). These exercise the REST transport
# with a stubbed HTTP layer — no network, no credentials.
# --------------------------------------------------------------------------- #


def _stub_d1(monkeypatch):
    """Capture D1 REST calls and replay canned rows."""
    calls: list[dict] = []
    stored: dict[str, str] = {}

    def fake_request(url: str, payload: dict, token: str) -> dict:
        calls.append({"url": url, "payload": payload, "token": token})
        sql = payload.get("sql", "")
        params = payload.get("params", [])
        if sql.strip().upper().startswith("SELECT"):
            key = params[0] if params else None
            if key in stored:
                return {"success": True, "result": [{"results": [{"v": stored[key]}]}]}
            return {"success": True, "result": [{"results": []}]}
        # INSERT OR REPLACE
        stored[params[0]] = params[1]
        return {"success": True, "result": [{"results": []}]}

    monkeypatch.setattr("scripts.durable_store._d1_request", fake_request)
    return calls, stored


def _d1_store(monkeypatch, **env):
    for k, v in {
        "HORO_DURABLE_STORE": "d1",
        "HORO_D1_DATABASE_ID": "eafa3062-4418-4831-94f6-5a8f23701cdd",
        "CLOUDFLARE_ACCOUNT_ID": "bda49e4e77e00609cb1ef68561b0d9eb",
        "CLOUDFLARE_D1_API_TOKEN": "test-token-not-real",
    }.items():
        monkeypatch.setenv(k, v)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return DurableStore.from_env()


def test_d1_backend_round_trips_bookkeeping(monkeypatch) -> None:
    calls, stored = _stub_d1(monkeypatch)
    store = _d1_store(monkeypatch)

    assert store.backend == "d1"
    store.begin_run(run_key="sync-2026-10-08", owner="render-1")
    store.heartbeat(run_key="sync-2026-10-08", step="download", detail="2/5")
    store.complete_run(run_key="sync-2026-10-08", vectors=135)

    state = store.read()
    assert state["last_success"]["run_key"] == "sync-2026-10-08"
    assert state["last_success"]["vectors"] == 135
    assert state["last_success"]["heartbeat"]["step"] == "download"

    # the write really went to D1, and the row is keyed under "state"
    assert "state" in stored
    writes = [c for c in calls if not c["payload"]["sql"].strip().upper().startswith("SELECT")]
    assert len(writes) == 3
    assert all(c["payload"]["sql"].strip().upper().startswith("INSERT OR REPLACE") for c in writes)
    assert all(c["payload"]["params"][0] == "state" for c in writes)


def test_d1_backend_refuses_a_second_concurrent_run(monkeypatch) -> None:
    _stub_d1(monkeypatch)
    store = _d1_store(monkeypatch)
    store.begin_run(run_key="sync-2026-10-08", owner="render-1")
    with pytest.raises(LeaseHeldError):
        store.begin_run(run_key="sync-2026-10-08", owner="render-2")


def test_d1_backend_targets_the_configured_account_and_database(monkeypatch) -> None:
    calls, _ = _stub_d1(monkeypatch)
    store = _d1_store(monkeypatch)
    store.read()
    assert calls, "expected at least one D1 request"
    url = calls[0]["url"]
    assert "bda49e4e77e00609cb1ef68561b0d9eb" in url
    assert "eafa3062-4418-4831-94f6-5a8f23701cdd" in url
    assert url.endswith("/query")


def test_d1_backend_missing_database_id_fails_loudly(monkeypatch) -> None:
    monkeypatch.setenv("HORO_DURABLE_STORE", "d1")
    monkeypatch.delenv("HORO_D1_DATABASE_ID", raising=False)
    with pytest.raises(KeyError):
        DurableStore.from_env()


def test_d1_backend_requires_a_token(monkeypatch) -> None:
    _stub_d1(monkeypatch)
    store = _d1_store(monkeypatch)
    monkeypatch.delenv("CLOUDFLARE_D1_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="CLOUDFLARE_D1_API_TOKEN"):
        store.read()
