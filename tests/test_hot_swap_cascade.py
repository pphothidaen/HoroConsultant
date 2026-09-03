"""Unit tests for Smart Hot-Swap Failover Cascade Router & Rule 17 Invariant."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

import pytest

from project.core.hot_swap_router import (
    DEFAULT_HOST_ACCOUNT,
    SmartHotSwapRouter,
)
from project.core.quota_registry import (
    REASON_429,
    QuotaCooldownRegistry,
)


@pytest.fixture
def mock_registry(tmp_path: Path) -> QuotaCooldownRegistry:
    storage_path = tmp_path / "quota_registry_hotswap.json"
    return QuotaCooldownRegistry(storage_path=storage_path, auto_init_defaults=True)


def test_rule17_host_account_never_selected_for_worker(mock_registry: QuotaCooldownRegistry) -> None:
    """Test that host account (agy2) is never returned as worker candidate."""
    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1", "agy1", "agy2"],
    )

    candidates = router.get_candidate_auxiliary_accounts(current_time=1000.0)
    assert "agy2" not in candidates
    assert set(candidates) == {"codex2", "codex3", "codex1", "agy1"}


def test_select_worker_healthy_cascade(mock_registry: QuotaCooldownRegistry) -> None:
    """Test selecting first healthy worker in auxiliary cascade."""
    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1", "agy1"],
    )

    decision = router.select_worker_account("TICKET-DEV-001", current_time=1000.0)
    assert decision.action == "DISPATCH"
    assert decision.selected_account == "codex2"
    assert decision.is_host_account is False


def test_skips_accounts_in_cooldown(mock_registry: QuotaCooldownRegistry) -> None:
    """Test that accounts in active cooldown are skipped."""
    now = 2000.0
    mock_registry.trip_circuit("codex2", reason=REASON_429, cooldown_seconds=120.0, current_time=now)
    mock_registry.trip_circuit("codex3", reason=REASON_429, cooldown_seconds=120.0, current_time=now)

    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1", "agy1"],
    )

    decision = router.select_worker_account("TICKET-DEV-002", current_time=now)
    assert decision.action == "DISPATCH"
    assert decision.selected_account == "codex1"
    assert "codex2" in decision.fallback_chain_attempted
    assert "codex3" in decision.fallback_chain_attempted


def test_exhausted_auxiliary_fails_closed_to_needs_hitl_preserving_host(mock_registry: QuotaCooldownRegistry) -> None:
    """Test fail-closed behavior to NEEDS_HITL when all auxiliary workers are exhausted."""
    now = 3000.0
    for alias in ["codex2", "codex3", "codex1", "agy1"]:
        mock_registry.trip_circuit(alias, reason=REASON_429, cooldown_seconds=300.0, current_time=now)

    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1", "agy1"],
    )

    decision = router.select_worker_account("TICKET-DEV-003", current_time=now)
    assert decision.action == "NEEDS_HITL"
    assert decision.selected_account is None
    assert decision.is_host_account is True  # Preserving host
    assert "Rule 17" in decision.reason


def test_execute_with_failover_success_on_retry(mock_registry: QuotaCooldownRegistry) -> None:
    """Test execute_with_failover successfully fails over when first worker trips."""
    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1"],
    )

    attempts = []

    def mock_worker(account_id: str) -> Tuple[bool, Any]:
        attempts.append(account_id)
        if account_id == "codex2":
            # First account fails with 429
            return False, "Rate limit exceeded (HTTP 429)"
        return True, f"Execution completed on {account_id}"

    res = router.execute_with_failover("TICKET-DEV-004", mock_worker, current_time=4000.0)

    assert res["status"] == "SUCCESS"
    assert res["final_account"] == "codex3"
    assert attempts == ["codex2", "codex3"]

    # Verify codex2 was tripped in registry
    st = mock_registry.get_account_state("codex2", current_time=4000.0)
    assert st is not None
    assert st.cooldown_active is True


def test_token_burn_rate_ranking(mock_registry: QuotaCooldownRegistry) -> None:
    """Test that candidate accounts are sorted by lowest 1h token burn rate."""
    load_table = {
        "codex2": {"tokens_1h": 5000000},
        "codex3": {"tokens_1h": 100000},  # Lower load
        "codex1": {"tokens_1h": 8000000},
        "agy1": {"tokens_1h": 200000},
    }

    def fake_burn_rate_provider(alias: str) -> dict[str, Any]:
        return load_table.get(alias, {"tokens_1h": 0})

    router = SmartHotSwapRouter(
        registry=mock_registry,
        host_account="agy2",
        auxiliary_accounts=["codex2", "codex3", "codex1", "agy1"],
        burn_rate_provider=fake_burn_rate_provider,
    )

    candidates = router.get_candidate_auxiliary_accounts(current_time=5000.0)
    assert candidates[0] == "codex3"  # 100,000 tokens
    assert candidates[1] == "agy1"    # 200,000 tokens
