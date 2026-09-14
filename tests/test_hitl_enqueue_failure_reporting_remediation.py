"""RED baseline for truthful HITL enqueue status reporting.

The unified-reading API must only report a queued human review after the
review item has been persisted successfully.  Storage failures must not be
swallowed while leaving a misleading queued status in the response.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from project.core.unified_reading_engine import UnifiedReadingRequest
from project.hitl_router import HITL_EXTERNAL_ITEMS_KEY
from project.routers.unified_reading_router import create_unified_reading


def _request() -> UnifiedReadingRequest:
    return UnifiedReadingRequest(
        birth_date=date(1990, 6, 15),
        birth_time=None,
        unknown_hour=False,
        birth_place="Bangkok",
        latitude=13.75,
        longitude=100.5,
        timezone="Asia/Bangkok",
        target_year=2026,
        force_human_review=True,
    )


def test_successful_hitl_enqueue_reports_queued_and_is_retrievable(tmp_path: Path) -> None:
    """A successful persistence operation produces a retrievable review item."""
    db_path = tmp_path / "hitl_reviews.json"

    with patch("project.hitl_router.HITL_DB_PATH", db_path):
        response = create_unified_reading(_request())

    assert response.hitl_routing["status"] == "QUEUED_FOR_HUMAN_REVIEW"
    persisted = json.loads(db_path.read_text(encoding="utf-8"))
    item = persisted[HITL_EXTERNAL_ITEMS_KEY].get(response.request_id)
    assert item is not None
    assert item["item_id"] == response.request_id
    assert item["required_human_review"] is True


def test_failed_hitl_enqueue_is_not_reported_as_queued(tmp_path: Path) -> None:
    """A persistence failure must produce a non-queued public status."""
    db_path = tmp_path / "hitl_reviews.json"

    with (
        patch("project.hitl_router.HITL_DB_PATH", db_path),
        patch(
            "project.hitl_router.save_hitl_db",
            side_effect=OSError("simulated HITL persistence failure"),
        ),
    ):
        response = create_unified_reading(_request())

    assert response.hitl_routing["status"] != "QUEUED_FOR_HUMAN_REVIEW"
