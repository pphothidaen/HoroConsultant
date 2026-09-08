"""Tests for TICKET-HLITE-REVIEW-REMEDIATION-20260907-04: Child Birth Date HTTP 500 Fix.

Covers:
- Child birth_date=2020-05-15 with target_year=2026 must NOT return HTTP 500
- Insufficient history for young persons handled gracefully
- _candidate_years returns valid (possibly empty) list for children
- past_patterns min_length relaxed for young persons
- Future birth_date relative to target_year handled explicitly
- target_year < birth_year handled explicitly
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _child_request_payload() -> dict[str, Any]:
    """Request payload for a child born 2020-05-15 targeting 2026."""
    return {
        "birth_date": "2020-05-15",
        "birth_time": "10:00",
        "unknown_hour": False,
        "birth_place": "Bangkok, Thailand",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
        "gender_at_birth": "male",
        "target_year": 2026,
        "locale": "th-TH",
        "display_name": "Child Test",
        "primary_focus_question": None,
        "force_human_review": False,
    }


def _future_birth_request_payload() -> dict[str, Any]:
    """Request payload with birth_date in the future relative to target_year."""
    return {
        "birth_date": "2030-01-01",
        "birth_time": "10:00",
        "unknown_hour": False,
        "birth_place": "Bangkok, Thailand",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
        "gender_at_birth": "female",
        "target_year": 2026,
        "locale": "th-TH",
        "display_name": "Future Birth Test",
        "primary_focus_question": None,
        "force_human_review": False,
    }


def _target_before_birth_payload() -> dict[str, Any]:
    """Request payload with target_year before birth_year."""
    return {
        "birth_date": "2000-06-15",
        "birth_time": "08:00",
        "unknown_hour": False,
        "birth_place": "Bangkok, Thailand",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
        "gender_at_birth": "male",
        "target_year": 1995,
        "locale": "th-TH",
        "display_name": "Target Before Birth Test",
        "primary_focus_question": None,
        "force_human_review": False,
    }


# ---------------------------------------------------------------------------
# Test 1: Child birth date must NOT cause HTTP 500
# ---------------------------------------------------------------------------

def test_child_birth_date_2020_target_2026_no_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /unified-reading with birth_date=2020-05-15, target_year=2026 must NOT return 500."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.routers.unified_reading_router import unified_reading_router

    app = FastAPI()
    app.include_router(unified_reading_router, prefix="/api/v3")

    with TestClient(app) as client:
        response = client.post("/api/v3/unified-reading", json=_child_request_payload())

    # Must NOT be 500 - this is the core bug
    assert response.status_code != 500, (
        f"Child birth date caused HTTP 500: {response.text}"
    )
    assert response.status_code == 200, (
        f"Expected 200 for child request, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Test 2: Insufficient history for young persons gives explicit indication
# ---------------------------------------------------------------------------

def test_young_person_insufficient_history_explicit_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """When history is insufficient (child <8 years old), the response should
    explicitly indicate limited history rather than crash."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.routers.unified_reading_router import unified_reading_router

    app = FastAPI()
    app.include_router(unified_reading_router, prefix="/api/v3")

    with TestClient(app) as client:
        response = client.post("/api/v3/unified-reading", json=_child_request_payload())

    assert response.status_code == 200
    payload = response.json()

    # past_patterns should be a list (possibly empty for young persons)
    past_patterns = payload.get("past_patterns", None)
    assert isinstance(past_patterns, list), "past_patterns must be a list"

    # For a ~6 year old child, there should be fewer than 3 patterns (or empty)
    assert len(past_patterns) < 3, (
        f"Child aged ~6 should have fewer than 3 past patterns, got {len(past_patterns)}"
    )

    # When past_patterns is empty, the API must explicitly explain why
    if len(past_patterns) == 0:
        reason = payload.get("insufficient_history_reason")
        assert reason is not None, (
            "Empty past_patterns must include an insufficient_history_reason"
        )
        assert "insufficient history" in reason.lower(), (
            f"Reason must mention 'insufficient history', got: {reason}"
        )


# ---------------------------------------------------------------------------
# Test 3: _candidate_years for child returns valid or empty list
# ---------------------------------------------------------------------------

def test_candidate_years_child_returns_valid_or_empty() -> None:
    """_candidate_years(2020, 2026, seed=42) should return a valid list
    (possibly empty) without error."""
    from project.core.past_pattern_calibrator import _candidate_years

    # Should NOT raise an error
    result = _candidate_years(2020, 2026, seed=42)

    assert isinstance(result, list), f"Expected list, got {type(result)}"
    # For a child born 2020 targeting 2026 (max_age=5), no preferred ages
    # (all >= 16) work and fallback can't reach 3 candidates cleanly.
    # The function should return a valid list — empty is acceptable.
    for year in result:
        assert isinstance(year, int)
        assert year < 2026, f"Candidate year {year} must be before target year 2026"
        assert year >= 2020, f"Candidate year {year} must be >= birth year 2020"


# ---------------------------------------------------------------------------
# Test 4: past_patterns min_length relaxed for young persons
# ---------------------------------------------------------------------------

def test_past_patterns_min_length_relaxed_for_young() -> None:
    """For young persons, past_patterns may have fewer than 3 candidates;
    the response schema should handle this gracefully."""
    from project.core.unified_reading_engine import (
        UnifiedReadingResponse,
        PastPatternCandidate,
    )

    # Construct a minimal valid response with 0 past patterns
    # This should NOT raise a ValidationError for young persons
    response_data = _minimal_response_data(past_patterns=[])

    # This currently fails because min_length=3 on past_patterns field
    validated = UnifiedReadingResponse.model_validate(response_data)
    assert validated.past_patterns == []


# ---------------------------------------------------------------------------
# Test 5: Future birth date relative to target_year handled explicitly
# ---------------------------------------------------------------------------

def test_future_birth_date_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """birth_date in the future relative to target_year should be handled
    explicitly (not crash with 500)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.routers.unified_reading_router import unified_reading_router

    app = FastAPI()
    app.include_router(unified_reading_router, prefix="/api/v3")

    with TestClient(app) as client:
        response = client.post("/api/v3/unified-reading", json=_future_birth_request_payload())

    # Must NOT be 500
    assert response.status_code != 500, (
        f"Future birth date caused HTTP 500: {response.text}"
    )
    # Should be a 422 validation error (birth_date after target_year)
    assert response.status_code == 422, (
        f"Expected 422 for future birth date, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Test 6: target_year before birth_year handled explicitly
# ---------------------------------------------------------------------------

def test_target_year_before_birth_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """target_year < birth_year should be handled explicitly (not crash with 500)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.routers.unified_reading_router import unified_reading_router

    app = FastAPI()
    app.include_router(unified_reading_router, prefix="/api/v3")

    with TestClient(app) as client:
        response = client.post("/api/v3/unified-reading", json=_target_before_birth_payload())

    # Must NOT be 500
    assert response.status_code != 500, (
        f"target_year before birth caused HTTP 500: {response.text}"
    )
    # Should be a 422 validation error
    assert response.status_code == 422, (
        f"Expected 422 for target_year<birth_year, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Helpers for building minimal valid response data
# ---------------------------------------------------------------------------

def _minimal_response_data(
    *,
    past_patterns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid UnifiedReadingResponse dict for schema testing."""
    from project.core.unified_reading_engine import (
        CANONICAL_TOPIC_IDS,
        ALLOWED_FEEDBACK_CHOICES,
    )

    topics = []
    for order, topic_id in enumerate(CANONICAL_TOPIC_IDS, start=1):
        topics.append({
            "topic_id": topic_id,
            "order": order,
            "title": f"Title {topic_id}",
            "summary": f"Summary for {topic_id}",
            "guidance": f"Guidance for {topic_id}",
            "confidence": "MEDIUM",
            "evidence_refs": ["test_evidence"],
        })

    monthly_scores = []
    for month in range(1, 13):
        monthly_scores.append({
            "month": month,
            "career_score": 5,
            "finance_score": 5,
            "love_score": 5,
            "confidence": "MEDIUM",
            "score_basis": {"test": True},
            "reasons": ["Test reason"],
        })

    if past_patterns is None:
        past_patterns = [
            {
                "pattern_id": f"education_{2000+i}_{2001+i}",
                "year_range": [2000 + i, 2001 + i],
                "age_range": [10 + i, 11 + i],
                "theme": "education",
                "deterministic_basis": ["bazi_resource_cycle"],
                "sensitive_category": False,
                "allowed_feedback": list(ALLOWED_FEEDBACK_CHOICES),
                "user_feedback": None,
            }
            for i in range(3)
        ]

    return {
        "schema_version": "horo_lite_unified_reading.v1",
        "request_id": "test-child-001",
        "target_year": 2026,
        "topics": topics,
        "monthly_scores": monthly_scores,
        "past_patterns": past_patterns,
        "consensus_metadata": {
            "consensus_score": 0.85,
            "traditions_considered": ["thai_suriyayart", "bazi"],
            "tradition_conflicts": [],
            "arbitration_status": "CONSENSUS_ACCEPTED",
        },
        "hitl_flags": {
            "required_human_review": False,
            "low_consensus": False,
            "tradition_conflict": False,
            "force_human_review": False,
            "uncertain_birth_time": False,
        },
        "hitl_routing": {
            "status": "NOT_REQUIRED",
            "reasons": [],
        },
        "llm_metadata": {
            "source": "deterministic_copy_transformer",
            "model_used": None,
            "translation_requested": False,
            "translation_enabled_by_env": False,
            "facts_mutable_by_llm": False,
            "network_call_performed": False,
            "deterministic_facts_source": "project.core.annual_timing_engine",
        },
    }
