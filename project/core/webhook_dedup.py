"""Webhook Idempotency and Delivery Deduplication / Coalescing (AT-11).

Guarantees at-least-once processing safety by deduplicating delivery IDs
and coalescing same-ticket event bursts to prevent duplicate worker spawns.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DeliveryRecord:
    """Record of a processed webhook delivery."""

    delivery_id: str
    ticket_id: str
    payload_hash: str
    processed_at: float


class WebhookDeduplicator:
    """Deduplicates incoming webhook events with TTL caching and burst coalescing."""

    def __init__(
        self,
        dedup_ttl_seconds: float = 3600.0,
        coalesce_window_seconds: float = 5.0,
    ) -> None:
        self._ttl = dedup_ttl_seconds
        self._coalesce_window = coalesce_window_seconds
        # delivery_id -> DeliveryRecord
        self._deliveries: Dict[str, DeliveryRecord] = {}
        # ticket_id -> last_event_timestamp
        self._last_ticket_event: Dict[str, float] = {}

    def _compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        """Compute SHA-256 hash over normalized payload."""
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def check_and_record(
        self,
        delivery_id: str,
        ticket_id: str,
        payload: Dict[str, Any],
        current_time: Optional[float] = None,
    ) -> tuple[bool, Optional[str]]:
        """Check if delivery is a duplicate or burst event.

        Returns:
            (is_duplicate, reason)
        """
        now = current_time if current_time is not None else time.time()
        self._prune_expired(now)

        # 1. Exact Delivery ID duplicate check
        if delivery_id in self._deliveries:
            prev = self._deliveries[delivery_id]
            return True, f"Duplicate delivery_id '{delivery_id}' (processed {now - prev.processed_at:.1f}s ago)"

        # 2. Burst Coalescing Check for same ticket
        last_time = self._last_ticket_event.get(ticket_id)
        if last_time is not None and (now - last_time) < self._coalesce_window:
            return True, f"Burst coalesced for ticket '{ticket_id}' ({now - last_time:.2f}s < {self._coalesce_window}s window)"

        # Record new delivery
        payload_hash = self._compute_payload_hash(payload)
        rec = DeliveryRecord(
            delivery_id=delivery_id,
            ticket_id=ticket_id,
            payload_hash=payload_hash,
            processed_at=now,
        )
        self._deliveries[delivery_id] = rec
        self._last_ticket_event[ticket_id] = now
        return False, None

    def _prune_expired(self, current_time: float) -> None:
        """Prune deliveries older than TTL."""
        cutoff = current_time - self._ttl
        expired_ids = [did for did, rec in self._deliveries.items() if rec.processed_at < cutoff]
        for did in expired_ids:
            self._deliveries.pop(did, None)
