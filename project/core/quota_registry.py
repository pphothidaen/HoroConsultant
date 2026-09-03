#!/usr/bin/env python3
"""Quota Cooldown Registry & Time-To-Reset (TTR) Calculation Engine.

Provides thread-safe state tracking, dynamic TTR calculation, state machine
transitions (NORMAL -> OPEN -> HALF_OPEN -> NORMAL), exponential backoff,
and atomic disk persistence for all multi-account and AI provider endpoints.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional

DEFAULT_ACCOUNTS: list[dict[str, str]] = [
    {"account_id": "codex1", "provider": "codex"},
    {"account_id": "codex2", "provider": "codex"},
    {"account_id": "codex3", "provider": "codex"},
    {"account_id": "agy1", "provider": "agy"},
    {"account_id": "agy2", "provider": "agy"},
    {"account_id": "gemini_flash", "provider": "gemini"},
    {"account_id": "gemini_pro", "provider": "gemini"},
    {"account_id": "cloudflare_ai", "provider": "cloudflare"},
    {"account_id": "huggingface_router", "provider": "hf"},
]

# State Constants
STATE_NORMAL = "NORMAL"
STATE_OPEN = "OPEN"
STATE_HALF_OPEN = "HALF_OPEN"

# Trip Reasons
REASON_429 = "HTTP_429_RATE_LIMIT"
REASON_USAGE_EXCEEDED = "USAGE_LIMIT_EXCEEDED"
REASON_TOKEN_BURN = "TOKEN_BURN_EXHAUSTION"
REASON_CANARY_FAILURE = "MICRO_CANARY_FAILURE"
REASON_MANUAL = "MANUAL_QUARANTINE"

DEFAULT_COOLDOWN_SECONDS = 60.0
MAX_COOLDOWN_SECONDS = 3600.0


@dataclass
class AccountQuotaState:
    account_id: str
    provider: str
    state: str = STATE_NORMAL
    cooldown_active: bool = False
    tripped_at: float = 0.0
    tripped_at_iso: str = ""
    cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS
    reset_timestamp: float = 0.0
    concurrency_limit: int = 3
    trip_reason: Optional[str] = None
    fail_count: int = 0
    last_probe_at: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def calculate_ttr(self, current_time: Optional[float] = None) -> float:
        """Calculate dynamic Time-To-Reset in seconds using wall-clock delta."""
        now = current_time if current_time is not None else time.time()
        if self.state == STATE_NORMAL:
            return 0.0
        return max(0.0, self.reset_timestamp - now)

    def to_dict(self, current_time: Optional[float] = None) -> dict[str, Any]:
        data = asdict(self)
        data["ttr_seconds"] = self.calculate_ttr(current_time)
        return data


class QuotaCooldownRegistry:
    """Thread-safe centralized registry for multi-account quota states and TTR."""

    def __init__(self, storage_path: Optional[Path | str] = None, auto_init_defaults: bool = True) -> None:
        self._lock = threading.RLock()
        self._accounts: dict[str, AccountQuotaState] = {}
        if storage_path is not None:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).resolve().parents[2] / "project" / "core" / "quota_registry.json"

        if auto_init_defaults:
            for item in DEFAULT_ACCOUNTS:
                self.register_account(item["account_id"], item["provider"])

        self.load()

    def register_account(
        self,
        account_id: str,
        provider: str,
        initial_concurrency: int = 3,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AccountQuotaState:
        with self._lock:
            if account_id not in self._accounts:
                self._accounts[account_id] = AccountQuotaState(
                    account_id=account_id,
                    provider=provider,
                    concurrency_limit=initial_concurrency,
                    metadata=metadata or {},
                )
            return self._accounts[account_id]

    def get_account_state(self, account_id: str, current_time: Optional[float] = None) -> Optional[AccountQuotaState]:
        with self._lock:
            acct = self._accounts.get(account_id)
            if not acct:
                return None
            self._evaluate_state_transition(acct, current_time)
            return acct

    def get_ttr(self, account_id: str, current_time: Optional[float] = None) -> float:
        with self._lock:
            acct = self.get_account_state(account_id, current_time)
            if not acct:
                return 0.0
            return acct.calculate_ttr(current_time)

    def trip_circuit(
        self,
        account_id: str,
        reason: str = REASON_429,
        cooldown_seconds: Optional[float] = None,
        reset_timestamp: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> AccountQuotaState:
        """Trip circuit breaker for an account, entering OPEN state."""
        now = current_time if current_time is not None else time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            acct = self._accounts.get(account_id)
            if not acct:
                acct = self.register_account(account_id, "unknown")

            acct.fail_count += 1
            if cooldown_seconds is not None:
                duration = max(1.0, float(cooldown_seconds))
            else:
                multiplier = 2 ** max(0, acct.fail_count - 1)
                duration = min(DEFAULT_COOLDOWN_SECONDS * multiplier, MAX_COOLDOWN_SECONDS)

            acct.cooldown_seconds = duration
            if reset_timestamp is not None:
                acct.reset_timestamp = float(reset_timestamp)
            else:
                acct.reset_timestamp = now + duration

            acct.state = STATE_OPEN
            acct.cooldown_active = True
            acct.tripped_at = now
            acct.tripped_at_iso = now_iso
            acct.concurrency_limit = 0
            acct.trip_reason = reason

            self.save(current_time=now)
            return acct

    def probe_half_open(self, account_id: str, current_time: Optional[float] = None) -> bool:
        """Transition account to HALF_OPEN if TTR has expired."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            acct = self._accounts.get(account_id)
            if not acct:
                return False
            self._evaluate_state_transition(acct, now)
            if acct.state == STATE_HALF_OPEN:
                acct.last_probe_at = now
                self.save(current_time=now)
                return True
            return False

    def record_probe_success(self, account_id: str, restored_concurrency: int = 3, current_time: Optional[float] = None) -> AccountQuotaState:
        """Record successful canary probe, restoring account to NORMAL state."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            acct = self._accounts.get(account_id)
            if not acct:
                acct = self.register_account(account_id, "unknown")

            acct.state = STATE_NORMAL
            acct.cooldown_active = False
            acct.fail_count = 0
            acct.cooldown_seconds = DEFAULT_COOLDOWN_SECONDS
            acct.reset_timestamp = 0.0
            acct.concurrency_limit = restored_concurrency
            acct.trip_reason = None
            self.save(current_time=now)
            return acct

    def record_probe_failure(
        self,
        account_id: str,
        reason: str = REASON_CANARY_FAILURE,
        current_time: Optional[float] = None,
    ) -> AccountQuotaState:
        """Record failed canary probe, applying exponential backoff and returning to OPEN."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            acct = self._accounts.get(account_id)
            if not acct:
                acct = self.register_account(account_id, "unknown")

            acct.fail_count += 1
            next_duration = min(acct.cooldown_seconds * 2.0, MAX_COOLDOWN_SECONDS)
            acct.cooldown_seconds = next_duration
            acct.reset_timestamp = now + next_duration
            acct.state = STATE_OPEN
            acct.cooldown_active = True
            acct.concurrency_limit = 0
            acct.trip_reason = reason
            acct.last_probe_at = now
            self.save(current_time=now)
            return acct

    def get_healthy_accounts(self, provider: Optional[str] = None, current_time: Optional[float] = None) -> list[AccountQuotaState]:
        """Return list of accounts currently in NORMAL state."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            results = []
            for acct in self._accounts.values():
                self._evaluate_state_transition(acct, now)
                if acct.state == STATE_NORMAL and not acct.cooldown_active:
                    if provider is None or acct.provider == provider:
                        results.append(acct)
            return results

    def get_accounts_in_cooldown(self, current_time: Optional[float] = None) -> list[AccountQuotaState]:
        """Return list of accounts currently in OPEN or HALF_OPEN state."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            results = []
            for acct in self._accounts.values():
                self._evaluate_state_transition(acct, now)
                if acct.state in (STATE_OPEN, STATE_HALF_OPEN):
                    results.append(acct)
            return results

    def _evaluate_state_transition(self, acct: AccountQuotaState, current_time: Optional[float] = None) -> None:
        """Internal helper to automatically shift OPEN -> HALF_OPEN when TTR reaches zero."""
        now = current_time if current_time is not None else time.time()
        if acct.state == STATE_OPEN:
            if acct.calculate_ttr(now) <= 0.0:
                acct.state = STATE_HALF_OPEN
                acct.concurrency_limit = 0

    def export_status(self, current_time: Optional[float] = None) -> dict[str, Any]:
        """Export registry state snapshot with pure ASCII metrics."""
        now = current_time if current_time is not None else time.time()
        with self._lock:
            accounts_data = {}
            total = len(self._accounts)
            normal_cnt = 0
            open_cnt = 0
            half_open_cnt = 0

            for aid, acct in self._accounts.items():
                self._evaluate_state_transition(acct, now)
                d = acct.to_dict(now)
                accounts_data[aid] = d
                if acct.state == STATE_NORMAL:
                    normal_cnt += 1
                elif acct.state == STATE_OPEN:
                    open_cnt += 1
                elif acct.state == STATE_HALF_OPEN:
                    half_open_cnt += 1

            return {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_accounts": total,
                "healthy_count": normal_cnt,
                "cooldown_open_count": open_cnt,
                "half_open_count": half_open_cnt,
                "accounts": accounts_data,
            }

    def save(self, current_time: Optional[float] = None) -> None:
        """Persist state to storage_path atomically."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot = self.export_status(current_time=current_time)
            target_dir = self.storage_path.parent
            with tempfile.NamedTemporaryFile("w", dir=target_dir, delete=False, encoding="utf-8") as tf:
                json.dump(snapshot, tf, indent=2)
                temp_name = tf.name
            os.replace(temp_name, self.storage_path)
        except Exception:
            pass

    def load(self) -> None:
        """Load state from storage_path if present."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_accounts = data.get("accounts", {})
            with self._lock:
                for aid, d in raw_accounts.items():
                    self._accounts[aid] = AccountQuotaState(
                        account_id=aid,
                        provider=d.get("provider", "unknown"),
                        state=d.get("state", STATE_NORMAL),
                        cooldown_active=d.get("cooldown_active", False),
                        tripped_at=d.get("tripped_at", 0.0),
                        tripped_at_iso=d.get("tripped_at_iso", ""),
                        cooldown_seconds=d.get("cooldown_seconds", DEFAULT_COOLDOWN_SECONDS),
                        reset_timestamp=d.get("reset_timestamp", 0.0),
                        concurrency_limit=d.get("concurrency_limit", 3),
                        trip_reason=d.get("trip_reason"),
                        fail_count=d.get("fail_count", 0),
                        last_probe_at=d.get("last_probe_at"),
                        metadata=d.get("metadata", {}),
                    )
        except Exception:
            pass


_GLOBAL_REGISTRY: Optional[QuotaCooldownRegistry] = None
_GLOBAL_LOCK = threading.Lock()


def get_quota_registry(storage_path: Optional[Path | str] = None) -> QuotaCooldownRegistry:
    """Get or initialize singleton QuotaCooldownRegistry instance."""
    global _GLOBAL_REGISTRY
    with _GLOBAL_LOCK:
        if _GLOBAL_REGISTRY is None:
            _GLOBAL_REGISTRY = QuotaCooldownRegistry(storage_path=storage_path)
        return _GLOBAL_REGISTRY
