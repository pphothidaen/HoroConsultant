"""Unit and integration test suite for QuotaCooldownRegistry & TTR Engine."""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time

import pytest

from project.core.quota_registry import (
    DEFAULT_COOLDOWN_SECONDS,
    MAX_COOLDOWN_SECONDS,
    REASON_429,
    REASON_CANARY_FAILURE,
    STATE_HALF_OPEN,
    STATE_NORMAL,
    STATE_OPEN,
    AccountQuotaState,
    QuotaCooldownRegistry,
)


@pytest.fixture
def temp_registry(tmp_path: Path) -> QuotaCooldownRegistry:
    storage_path = tmp_path / "quota_registry_test.json"
    return QuotaCooldownRegistry(storage_path=storage_path, auto_init_defaults=True)


def test_initial_registry_defaults(temp_registry: QuotaCooldownRegistry) -> None:
    """Test that all default accounts are registered in NORMAL state."""
    status = temp_registry.export_status()
    assert status["total_accounts"] >= 9
    assert status["healthy_count"] == status["total_accounts"]
    assert status["cooldown_open_count"] == 0

    for aid in ["codex1", "codex2", "codex3", "agy1", "agy2", "gemini_flash"]:
        st = temp_registry.get_account_state(aid)
        assert st is not None
        assert st.state == STATE_NORMAL
        assert st.cooldown_active is False
        assert st.calculate_ttr() == 0.0
        assert st.concurrency_limit == 3


def test_trip_circuit_and_ttr(temp_registry: QuotaCooldownRegistry) -> None:
    """Test circuit tripping into OPEN state and dynamic TTR calculation."""
    now = 1000.0
    acct = temp_registry.trip_circuit("codex1", reason=REASON_429, cooldown_seconds=60.0, current_time=now)

    assert acct.state == STATE_OPEN
    assert acct.cooldown_active is True
    assert acct.tripped_at == now
    assert acct.reset_timestamp == 1060.0
    assert acct.concurrency_limit == 0
    assert acct.trip_reason == REASON_429

    # TTR checks at different timestamps
    assert temp_registry.get_ttr("codex1", current_time=1000.0) == 60.0
    assert temp_registry.get_ttr("codex1", current_time=1030.0) == 30.0
    assert temp_registry.get_ttr("codex1", current_time=1060.0) == 0.0
    assert temp_registry.get_ttr("codex1", current_time=1100.0) == 0.0


def test_automatic_transition_to_half_open(temp_registry: QuotaCooldownRegistry) -> None:
    """Test automatic shift from OPEN to HALF_OPEN when TTR reaches zero."""
    now = 2000.0
    temp_registry.trip_circuit("codex2", reason=REASON_429, cooldown_seconds=50.0, current_time=now)

    # At now + 40s -> Still OPEN
    st_before = temp_registry.get_account_state("codex2", current_time=now + 40.0)
    assert st_before is not None
    assert st_before.state == STATE_OPEN

    # At now + 50s -> HALF_OPEN
    st_after = temp_registry.get_account_state("codex2", current_time=now + 50.0)
    assert st_after is not None
    assert st_after.state == STATE_HALF_OPEN
    assert st_after.concurrency_limit == 0


def test_record_probe_success(temp_registry: QuotaCooldownRegistry) -> None:
    """Test canary probe success restores account to NORMAL."""
    now = 3000.0
    temp_registry.trip_circuit("codex3", cooldown_seconds=30.0, current_time=now)

    # Fast-forward to HALF_OPEN
    temp_registry.probe_half_open("codex3", current_time=now + 35.0)

    # Success
    restored = temp_registry.record_probe_success("codex3", restored_concurrency=3)
    assert restored.state == STATE_NORMAL
    assert restored.cooldown_active is False
    assert restored.fail_count == 0
    assert restored.concurrency_limit == 3
    assert restored.trip_reason is None
    assert temp_registry.get_ttr("codex3") == 0.0


def test_record_probe_failure_exponential_backoff(temp_registry: QuotaCooldownRegistry) -> None:
    """Test canary probe failure triggers exponential backoff."""
    now = 4000.0
    temp_registry.trip_circuit("agy1", cooldown_seconds=60.0, current_time=now)

    # Probe fail 1
    failed1 = temp_registry.record_probe_failure("agy1", reason=REASON_CANARY_FAILURE, current_time=now + 60.0)
    assert failed1.state == STATE_OPEN
    assert failed1.fail_count == 2
    assert failed1.cooldown_seconds == 120.0
    assert failed1.reset_timestamp == now + 60.0 + 120.0

    # Probe fail 2
    failed2 = temp_registry.record_probe_failure("agy1", current_time=now + 180.0)
    assert failed2.fail_count == 3
    assert failed2.cooldown_seconds == 240.0
    assert failed2.reset_timestamp == now + 180.0 + 240.0


def test_healthy_and_cooldown_filters(temp_registry: QuotaCooldownRegistry) -> None:
    """Test filtering healthy vs quarantined accounts."""
    temp_registry.trip_circuit("codex1", cooldown_seconds=100.0, current_time=5000.0)
    temp_registry.trip_circuit("agy1", cooldown_seconds=100.0, current_time=5000.0)

    healthy = temp_registry.get_healthy_accounts(current_time=5000.0)
    healthy_ids = {a.account_id for a in healthy}
    assert "codex1" not in healthy_ids
    assert "agy1" not in healthy_ids
    assert "codex2" in healthy_ids
    assert "agy2" in healthy_ids

    # Provider specific filter
    healthy_codex = temp_registry.get_healthy_accounts(provider="codex", current_time=5000.0)
    assert len(healthy_codex) == 2
    assert {a.account_id for a in healthy_codex} == {"codex2", "codex3"}

    cooldown = temp_registry.get_accounts_in_cooldown(current_time=5000.0)
    assert {a.account_id for a in cooldown} == {"codex1", "agy1"}


def test_atomic_persistence_and_reload(tmp_path: Path) -> None:
    """Test that registry state is saved atomically and reloads cleanly."""
    storage_path = tmp_path / "persistent_registry.json"
    r1 = QuotaCooldownRegistry(storage_path=storage_path, auto_init_defaults=True)
    r1.trip_circuit("codex2", reason="TEST_REASON", cooldown_seconds=150.0, current_time=6000.0)

    assert storage_path.exists()

    # Load in separate instance
    r2 = QuotaCooldownRegistry(storage_path=storage_path, auto_init_defaults=False)
    acct2 = r2.get_account_state("codex2", current_time=6050.0)
    assert acct2 is not None
    assert acct2.state == STATE_OPEN
    assert acct2.trip_reason == "TEST_REASON"
    assert acct2.calculate_ttr(current_time=6050.0) == 100.0


def test_thread_safety_concurrent_trips(temp_registry: QuotaCooldownRegistry) -> None:
    """Test concurrent thread safety without exceptions or data corruption."""
    threads = []
    errors = []

    def worker(account_id: str, t_offset: float) -> None:
        try:
            for i in range(10):
                temp_registry.trip_circuit(account_id, cooldown_seconds=10.0 + i, current_time=7000.0 + t_offset)
                temp_registry.probe_half_open(account_id, current_time=7020.0 + t_offset)
                temp_registry.record_probe_success(account_id)
        except Exception as exc:
            errors.append(exc)

    for i in range(8):
        aid = f"codex{1 + (i % 3)}"
        t = threading.Thread(target=worker, args=(aid, float(i)))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0
    status = temp_registry.export_status()
    assert status["total_accounts"] >= 9
