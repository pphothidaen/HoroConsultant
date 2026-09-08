"""Remediation tests for Package 06: 12 distinct topic-based guidance.

Each of the 12 canonical topics must produce unique, evidence-grounded
summary and guidance text.  Topics referencing specific domains (career,
finance, love) must include the relevant domain score data.
"""

from __future__ import annotations

from datetime import date

import pytest

from project.core.unified_reading_engine import (
    CANONICAL_TOPIC_IDS,
    UnifiedReadingRequest,
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
# 1. All 12 guidance strings are distinct
# ---------------------------------------------------------------------------
def test_all_guidance_strings_are_distinct() -> None:
    """No two topics may share the same guidance text."""
    resp = create_unified_reading(_make_request())
    guidances = [t.guidance for t in resp.topics]
    assert len(guidances) == 12
    assert len(set(guidances)) == 12, (
        f"Expected 12 distinct guidance strings, got {len(set(guidances))} unique"
    )


# ---------------------------------------------------------------------------
# 2. All 12 summary strings are distinct
# ---------------------------------------------------------------------------
def test_all_summary_strings_are_distinct() -> None:
    """No two topics may share the same summary text."""
    resp = create_unified_reading(_make_request())
    summaries = [t.summary for t in resp.topics]
    assert len(summaries) == 12
    assert len(set(summaries)) == 12, (
        f"Expected 12 distinct summary strings, got {len(set(summaries))} unique"
    )


# ---------------------------------------------------------------------------
# 3. Career topic references career data
# ---------------------------------------------------------------------------
def test_career_topic_references_career_domain() -> None:
    resp = create_unified_reading(_make_request())
    career_topic = next(t for t in resp.topics if t.topic_id == "career_business")
    assert "career" in career_topic.summary.lower(), (
        "Career topic summary must reference career data"
    )
    assert "career" in career_topic.guidance.lower() or "month" in career_topic.guidance.lower(), (
        "Career topic guidance must reference career timing"
    )


# ---------------------------------------------------------------------------
# 4. Finance topic references finance data
# ---------------------------------------------------------------------------
def test_finance_topic_references_finance_domain() -> None:
    resp = create_unified_reading(_make_request())
    finance_topic = next(t for t in resp.topics if t.topic_id == "finance")
    assert "finance" in finance_topic.summary.lower(), (
        "Finance topic summary must reference finance data"
    )


# ---------------------------------------------------------------------------
# 5. Love topic references love/relationship data
# ---------------------------------------------------------------------------
def test_love_topic_references_love_domain() -> None:
    resp = create_unified_reading(_make_request())
    love_topic = next(t for t in resp.topics if t.topic_id == "love_relationships")
    assert "love" in love_topic.summary.lower() or "relationship" in love_topic.summary.lower(), (
        "Love topic summary must reference relationship data"
    )


# ---------------------------------------------------------------------------
# 6. Past pattern topic adapts when no patterns available (child)
# ---------------------------------------------------------------------------
def test_past_pattern_topic_adapts_for_child() -> None:
    """A child with no past patterns gets a distinct message."""
    resp = create_unified_reading(_make_request(
        birth_date=date(2020, 1, 1),
        target_year=2026,
    ))
    pp_topic = next(t for t in resp.topics if t.topic_id == "past_pattern_calibration")
    assert "no past pattern" in pp_topic.summary.lower() or "insufficient" in pp_topic.summary.lower(), (
        f"Child past-pattern summary must indicate no patterns: {pp_topic.summary}"
    )


# ---------------------------------------------------------------------------
# 7. Topic order and IDs match canonical contract
# ---------------------------------------------------------------------------
def test_topic_order_matches_canonical() -> None:
    resp = create_unified_reading(_make_request())
    assert len(resp.topics) == 12
    for idx, topic in enumerate(resp.topics):
        assert topic.topic_id == CANONICAL_TOPIC_IDS[idx], (
            f"Topic {idx} id mismatch: {topic.topic_id} != {CANONICAL_TOPIC_IDS[idx]}"
        )
        assert topic.order == idx + 1


# ---------------------------------------------------------------------------
# 8. Different request parameters produce different guidance content
# ---------------------------------------------------------------------------
def test_different_inputs_produce_different_guidance() -> None:
    """Two different birth dates should produce different topic guidance
    (since scores differ)."""
    resp_a = create_unified_reading(_make_request(birth_date=date(1990, 6, 15)))
    resp_b = create_unified_reading(_make_request(birth_date=date(1985, 1, 1)))

    # At least some topics should differ (career, finance, etc.)
    different_count = sum(
        1 for a, b in zip(resp_a.topics, resp_b.topics)
        if a.guidance != b.guidance
    )
    assert different_count >= 6, (
        f"At least 6 topics should differ between different inputs, got {different_count}"
    )
