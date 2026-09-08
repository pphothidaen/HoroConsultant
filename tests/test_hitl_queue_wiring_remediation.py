"""Remediation tests for Package 03: HITL queue wiring.

When ``hitl_routing.status`` is ``QUEUED_FOR_HUMAN_REVIEW``, the unified
reading router must enqueue a retrievable review item via the HITL router.
The enqueue must be idempotent and must not break the reading on failure.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from project.core.unified_reading_engine import UnifiedReadingRequest
from project.hitl_router import (
    HITL_EXTERNAL_ITEMS_KEY,
    load_hitl_db,
    save_hitl_db,
)
from project.routers.unified_reading_router import create_unified_reading


def _make_request(**overrides: object) -> UnifiedReadingRequest:
    defaults = {
        "birth_date": date(1990, 6, 15),
        "birth_time": None,
        "unknown_hour": False,
        "birth_place": "Bangkok",
        "latitude": 13.75,
        "longitude": 100.5,
        "timezone": "Asia/Bangkok",
        "target_year": 2026,
    }
    defaults.update(overrides)
    return UnifiedReadingRequest(**defaults)


# ---------------------------------------------------------------------------
# 1. Force human review triggers HITL enqueue
# ---------------------------------------------------------------------------
def test_force_human_review_enqueues_hitl_item(tmp_path: Any) -> None:
    """When force_human_review=True, the reading must create an HITL item."""
    db_path = tmp_path / "hitl_reviews.json"

    with patch("project.hitl_router.HITL_DB_PATH", db_path):
        request = _make_request(force_human_review=True)
        resp = create_unified_reading(request)

        # Verify response still succeeds
        assert resp.request_id is not None
        assert resp.hitl_routing["status"] == "QUEUED_FOR_HUMAN_REVIEW"

        # Verify HITL item was enqueued
        hitl_db = json.loads(db_path.read_text(encoding="utf-8"))
        external_items = hitl_db.get(HITL_EXTERNAL_ITEMS_KEY, {})
        assert len(external_items) >= 1, "At least one HITL item must be enqueued"

        # The item should use the response request_id
        item = external_items.get(resp.request_id)
        assert item is not None, (
            f"HITL item with id {resp.request_id} must exist, "
            f"found: {list(external_items.keys())}"
        )
        assert item["source_domain"] == "horo-lite-unified-reading"
        assert item["required_human_review"] is True
        assert "force_human_review" in str(item.get("notes", ""))


# ---------------------------------------------------------------------------
# 2. Idempotent re-enqueue (same request → same item, not duplicate)
# ---------------------------------------------------------------------------
def test_hitl_enqueue_is_idempotent(tmp_path: Any) -> None:
    """Calling the reading twice with the same parameters must not duplicate."""
    db_path = tmp_path / "hitl_reviews.json"

    with patch("project.hitl_router.HITL_DB_PATH", db_path):
        request = _make_request(force_human_review=True)
        resp1 = create_unified_reading(request)
        resp2 = create_unified_reading(request)

        assert resp1.request_id == resp2.request_id

        hitl_db = json.loads(db_path.read_text(encoding="utf-8"))
        external_items = hitl_db.get(HITL_EXTERNAL_ITEMS_KEY, {})
        # Must have exactly 1 item, not 2
        matching = [k for k in external_items if k == resp1.request_id]
        assert len(matching) == 1, (
            f"Expected exactly 1 HITL item for repeated request, got {len(matching)}"
        )


# ---------------------------------------------------------------------------
# 3. No enqueue when HITL is NOT_REQUIRED
# ---------------------------------------------------------------------------
def test_no_hitl_enqueue_when_not_required(tmp_path: Any) -> None:
    """Normal requests without HITL triggers must not enqueue."""
    db_path = tmp_path / "hitl_reviews.json"

    with patch("project.hitl_router.HITL_DB_PATH", db_path):
        # Use a request that won't trigger HITL (known hour, no force)
        from datetime import time
        request = _make_request(
            birth_time=time(10, 30),
            unknown_hour=False,
            force_human_review=False,
        )
        resp = create_unified_reading(request)

        if resp.hitl_routing["status"] == "NOT_REQUIRED":
            # If HITL is not required, no external item should exist
            if db_path.exists():
                hitl_db = json.loads(db_path.read_text(encoding="utf-8"))
                external_items = hitl_db.get(HITL_EXTERNAL_ITEMS_KEY, {})
                assert resp.request_id not in external_items, (
                    "Reading without HITL trigger must not enqueue"
                )


# ---------------------------------------------------------------------------
# 4. Enqueue failure does not break the reading response
# ---------------------------------------------------------------------------
def test_enqueue_failure_does_not_break_reading() -> None:
    """Even if the HITL storage fails, the reading must still return."""
    with patch(
        "project.routers.unified_reading_router.upsert_external_hitl_item",
        side_effect=RuntimeError("Storage unavailable"),
    ):
        request = _make_request(force_human_review=True)
        # Must not raise
        resp = create_unified_reading(request)
        assert resp.request_id is not None
        assert resp.hitl_routing["status"] == "QUEUED_FOR_HUMAN_REVIEW"


# ---------------------------------------------------------------------------
# 5. Conflict-triggered HITL includes conflict metadata
# ---------------------------------------------------------------------------
def test_conflict_triggered_hitl_includes_metadata(tmp_path: Any) -> None:
    """A reading with tradition conflicts must enqueue with conflict details."""
    db_path = tmp_path / "hitl_reviews.json"

    # Build fixture claims with genuine conflict (career spread=7)
    claims_per_month = [
        {
            "month": m,
            "tradition_claims": {
                "thai_suriyayart": {"career_score": 9, "finance_score": 5, "love_score": 5, "claim": "strong"},
                "bazi_liu_yue": {"career_score": 2, "finance_score": 5, "love_score": 5, "claim": "weak"},
                "zi_wei": {"career_score": 2, "finance_score": 5, "love_score": 5, "claim": "cautious"},
            },
        }
        for m in range(1, 13)
    ]

    with patch("project.hitl_router.HITL_DB_PATH", db_path):
        request = _make_request()
        # Inject fixture claims via the request object
        object.__setattr__(request, "tradition_monthly_claims", claims_per_month)
        resp = create_unified_reading(request)

        assert resp.hitl_routing["status"] == "QUEUED_FOR_HUMAN_REVIEW"

        hitl_db = json.loads(db_path.read_text(encoding="utf-8"))
        external_items = hitl_db.get(HITL_EXTERNAL_ITEMS_KEY, {})
        item = external_items.get(resp.request_id)
        assert item is not None, "Conflict-triggered reading must enqueue"
        assert item["conflict_detected"] is True
