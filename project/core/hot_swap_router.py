#!/usr/bin/env python3
"""Smart Hot-Swap Failover Cascade Router.

Enforces Rule 17 Host Account Preservation Invariant:
- Master brain host session is preserved as the LAST to exhaust.
- Child worker tickets are routed to auxiliary accounts (codex2, codex3, codex1, agy1) first.
- Quarantined accounts in active cooldown are automatically skipped via QuotaCooldownRegistry.
- Fail closed with NEEDS_HITL if all auxiliary workers are exhausted and host drops below floor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from project.core.quota_registry import (
    REASON_429,
    REASON_USAGE_EXCEEDED,
    STATE_NORMAL,
    QuotaCooldownRegistry,
    get_quota_registry,
)

logger = logging.getLogger(__name__)

DEFAULT_HOST_ACCOUNT = "agy2"
AUXILIARY_WORKER_PREFERENCE_ORDER = [
    "codex2",
    "codex3",
    "codex1",
    "agy1",
]


@dataclass
class HotSwapDecision:
    selected_account: Optional[str]
    is_host_account: bool
    fallback_chain_attempted: list[str]
    action: str  # "DISPATCH", "NEEDS_HITL", "BLOCKED_COOLDOWN"
    reason: str
    decision_timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_account": self.selected_account,
            "is_host_account": self.is_host_account,
            "fallback_chain_attempted": self.fallback_chain_attempted,
            "action": self.action,
            "reason": self.reason,
            "decision_timestamp": self.decision_timestamp,
        }


class SmartHotSwapRouter:
    """Intelligent failover router implementing Rule 17 host account preservation."""

    def __init__(
        self,
        registry: Optional[QuotaCooldownRegistry] = None,
        host_account: str = DEFAULT_HOST_ACCOUNT,
        auxiliary_accounts: Optional[list[str]] = None,
        burn_rate_provider: Optional[Callable[[str], dict[str, Any]]] = None,
    ) -> None:
        self.registry = registry or get_quota_registry()
        self.host_account = host_account
        self.auxiliary_accounts = list(auxiliary_accounts) if auxiliary_accounts else list(AUXILIARY_WORKER_PREFERENCE_ORDER)
        self.burn_rate_provider = burn_rate_provider

    def get_candidate_auxiliary_accounts(self, current_time: Optional[float] = None) -> list[str]:
        """Return healthy auxiliary worker accounts sorted by health preference."""
        now = current_time if current_time is not None else time.time()
        healthy_candidates = []

        for alias in self.auxiliary_accounts:
            # Rule 17: Never treat host as auxiliary worker candidate
            if alias == self.host_account:
                continue

            state = self.registry.get_account_state(alias, current_time=now)
            if state is None:
                # Unregistered account, default to candidate
                healthy_candidates.append((alias, 0))
                continue

            if state.state == STATE_NORMAL and not state.cooldown_active:
                # Rank by recent token load if provider available
                token_load = 0
                if self.burn_rate_provider:
                    try:
                        load_info = self.burn_rate_provider(alias)
                        token_load = int(load_info.get("tokens_1h", 0))
                    except Exception:
                        token_load = 0
                healthy_candidates.append((alias, token_load))

        # Sort by lowest token load, preserving auxiliary preference order as secondary key
        healthy_candidates.sort(key=lambda x: x[1])
        return [alias for alias, _ in healthy_candidates]

    def select_worker_account(
        self,
        ticket_id: str,
        excluded_accounts: Optional[list[str]] = None,
        current_time: Optional[float] = None,
    ) -> HotSwapDecision:
        """Select healthiest auxiliary worker account for a child ticket, respecting Rule 17."""
        now = current_time if current_time is not None else time.time()
        excluded = set(excluded_accounts or [])
        attempted: list[str] = []

        # Evaluate all auxiliary accounts in preference order
        candidate_ranks = self.get_candidate_auxiliary_accounts(current_time=now)
        candidate_set = set(candidate_ranks)

        for alias in self.auxiliary_accounts:
            if alias == self.host_account:
                continue
            attempted.append(alias)
            if alias in excluded:
                continue
            if alias in candidate_set:
                return HotSwapDecision(
                    selected_account=alias,
                    is_host_account=False,
                    fallback_chain_attempted=attempted,
                    action="DISPATCH",
                    reason=f"[OK] Selected healthy auxiliary worker {alias} for ticket {ticket_id}",
                    decision_timestamp=now,
                )

        # All auxiliary accounts exhausted or in cooldown
        # Check host account status under Rule 17
        host_state = self.registry.get_account_state(self.host_account, current_time=now)
        host_cooldown = host_state.cooldown_active if host_state else False

        if host_cooldown:
            return HotSwapDecision(
                selected_account=None,
                is_host_account=True,
                fallback_chain_attempted=attempted,
                action="NEEDS_HITL",
                reason=f"[BLOCKED] All auxiliary workers and host account {self.host_account} are in cooldown. Escalating to HITL.",
                decision_timestamp=now,
            )

        # Rule 17 Invariant: Host account must NOT run child worker tickets without explicit user authorization
        return HotSwapDecision(
            selected_account=None,
            is_host_account=True,
            fallback_chain_attempted=attempted,
            action="NEEDS_HITL",
            reason=f"[BLOCKED] All auxiliary workers {self.auxiliary_accounts} are exhausted/in cooldown. Host account {self.host_account} preserved as last-to-exhaust under Rule 17. Escalating to HITL.",
            decision_timestamp=now,
        )

    def handle_worker_trip(
        self,
        account_id: str,
        reason: str = REASON_429,
        cooldown_seconds: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> None:
        """Record worker account trip into QuotaCooldownRegistry."""
        now = current_time if current_time is not None else time.time()
        self.registry.trip_circuit(
            account_id=account_id,
            reason=reason,
            cooldown_seconds=cooldown_seconds,
            current_time=now,
        )
        logger.warning(
            f"[TRIP] Worker account {account_id} tripped ({reason}). Circuit OPEN in registry."
        )

    def execute_with_failover(
        self,
        ticket_id: str,
        worker_fn: Callable[[str], Tuple[bool, Any]],
        max_failover_attempts: int = 3,
        current_time: Optional[float] = None,
    ) -> dict[str, Any]:
        """Execute worker task with automatic hot-swap failover cascade across auxiliary accounts."""
        now = current_time if current_time is not None else time.time()
        excluded: list[str] = []
        history: list[dict[str, Any]] = []

        for attempt in range(1, max_failover_attempts + 1):
            decision = self.select_worker_account(ticket_id, excluded_accounts=excluded, current_time=now)
            if decision.action != "DISPATCH" or not decision.selected_account:
                return {
                    "status": "FAILED",
                    "action": decision.action,
                    "reason": decision.reason,
                    "history": history,
                    "final_account": None,
                }

            account_id = decision.selected_account
            try:
                success, result = worker_fn(account_id)
                if success:
                    history.append({
                        "attempt": attempt,
                        "account_id": account_id,
                        "status": "SUCCESS",
                        "result": result,
                    })
                    return {
                        "status": "SUCCESS",
                        "action": "COMPLETED",
                        "final_account": account_id,
                        "result": result,
                        "history": history,
                    }
                else:
                    # Worker failed (e.g. rate limited during execution)
                    self.handle_worker_trip(account_id, reason=REASON_429, current_time=now)
                    excluded.append(account_id)
                    history.append({
                        "attempt": attempt,
                        "account_id": account_id,
                        "status": "FAILED",
                        "error": str(result),
                    })
            except Exception as exc:
                self.handle_worker_trip(account_id, reason=REASON_USAGE_EXCEEDED, current_time=now)
                excluded.append(account_id)
                history.append({
                    "attempt": attempt,
                    "account_id": account_id,
                    "status": "EXCEPTION",
                    "error": str(exc),
                })

        return {
            "status": "EXHAUSTED",
            "action": "NEEDS_HITL",
            "reason": f"Exceeded maximum failover attempts ({max_failover_attempts}).",
            "history": history,
            "final_account": None,
        }
