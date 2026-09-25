"""Unit tests for WebhookDeduplicator (AT-11)."""

import pytest

from project.core.webhook_dedup import WebhookDeduplicator


def test_webhook_dedup_first_delivery_allowed():
    dedup = WebhookDeduplicator(dedup_ttl_seconds=3600, coalesce_window_seconds=5.0)
    payload = {"event": "issue_created", "ticket": "KAN-800"}

    is_dup, reason = dedup.check_and_record(
        delivery_id="deliv-001",
        ticket_id="KAN-800",
        payload=payload,
        current_time=100.0,
    )
    assert is_dup is False
    assert reason is None


def test_webhook_dedup_exact_duplicate_rejected():
    dedup = WebhookDeduplicator(dedup_ttl_seconds=3600, coalesce_window_seconds=5.0)
    payload = {"event": "issue_created", "ticket": "KAN-800"}

    dedup.check_and_record("deliv-001", "KAN-800", payload, current_time=100.0)

    # Re-send same delivery ID
    is_dup, reason = dedup.check_and_record("deliv-001", "KAN-800", payload, current_time=102.0)
    assert is_dup is True
    assert "Duplicate delivery_id" in reason


def test_webhook_dedup_burst_coalescing():
    dedup = WebhookDeduplicator(dedup_ttl_seconds=3600, coalesce_window_seconds=5.0)
    payload1 = {"event": "issue_updated", "step": 1}
    payload2 = {"event": "issue_updated", "step": 2}

    # Event 1 at time 100.0
    is_dup1, _ = dedup.check_and_record("deliv-101", "KAN-801", payload1, current_time=100.0)
    assert is_dup1 is False

    # Event 2 at time 102.0 (different delivery ID, but same ticket within 5s window) -> Coalesced
    is_dup2, reason2 = dedup.check_and_record("deliv-102", "KAN-801", payload2, current_time=102.0)
    assert is_dup2 is True
    assert "Burst coalesced" in reason2

    # Event 3 at time 106.0 (outside 5s window) -> Allowed
    is_dup3, reason3 = dedup.check_and_record("deliv-103", "KAN-801", payload2, current_time=106.0)
    assert is_dup3 is False
    assert reason3 is None
