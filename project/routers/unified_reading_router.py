"""Unified Horo Lite reading API adapter for v3 routes."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from fastapi import APIRouter

from project.core.annual_timing_engine import calculate_annual_timing
from project.core.past_pattern_calibrator import generate_past_pattern_candidates
from project.core.unified_reading_engine import (
    CANONICAL_TOPIC_IDS,
    MonthlyScoreItem,
    TopicModule,
    UnifiedReadingRequest,
    UnifiedReadingResponse,
)


unified_reading_router = APIRouter(tags=["Horo Lite Unified Reading"])

_TOPIC_TITLES: dict[str, str] = {
    "personal_overview_strengths": "Personal overview and strengths",
    "past_pattern_calibration": "Past pattern calibration",
    "annual_overview": "Annual overview",
    "career_business": "Career and business",
    "finance": "Finance",
    "love_relationships": "Love and relationships",
    "health_wellbeing": "Health and wellbeing",
    "family_surrounding_people": "Family and surrounding people",
    "opportunities_caution_periods": "Opportunities and caution periods",
    "twelve_month_roadmap": "Twelve month roadmap",
    "top_priorities_cautions": "Top priorities and cautions",
    "export_sharing_actions": "Export and sharing actions",
}


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _request_id_for(request: UnifiedReadingRequest) -> str:
    payload = json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"unified-reading-{digest}"


def _score_from_month(month: dict[str, Any], domain: str) -> int:
    score = month.get(f"{domain}_score")
    if isinstance(score, int):
        return score
    if isinstance(score, float):
        return int(score)

    score_range = month.get(f"{domain}_score_range") or month.get(f"{domain}_range")
    if isinstance(score_range, list | tuple) and len(score_range) == 2:
        lower, upper = score_range
        if isinstance(lower, int | float) and isinstance(upper, int | float):
            return max(1, min(10, int(round((float(lower) + float(upper)) / 2.0))))

    return 5


def _api_confidence(value: Any) -> str:
    normalized = str(value or "").upper()
    if normalized in {"HIGH", "MEDIUM", "LOW"}:
        return normalized
    return "LOW" if normalized == "ESTIMATED" else "MEDIUM"


def _monthly_scores(annual_timing: dict[str, Any]) -> list[MonthlyScoreItem]:
    scores: list[MonthlyScoreItem] = []
    for raw_month in annual_timing.get("monthly_scores", []):
        month = dict(raw_month)
        scores.append(
            MonthlyScoreItem(
                month=int(month["month"]),
                career_score=_score_from_month(month, "career"),
                finance_score=_score_from_month(month, "finance"),
                love_score=_score_from_month(month, "love"),
                confidence=_api_confidence(month.get("confidence")),
                score_basis=dict(month.get("score_basis") or {}),
                reasons=list(month.get("reasons") or ["Deterministic annual timing evidence is present"]),
            )
        )
    return scores


def _topic_modules(
    request: UnifiedReadingRequest,
    monthly_scores: list[MonthlyScoreItem],
    annual_timing: dict[str, Any],
    pattern_payload: dict[str, Any],
) -> list[TopicModule]:
    average_career = sum(item.career_score for item in monthly_scores) / len(monthly_scores)
    average_finance = sum(item.finance_score for item in monthly_scores) / len(monthly_scores)
    average_love = sum(item.love_score for item in monthly_scores) / len(monthly_scores)
    strongest_month = max(
        monthly_scores,
        key=lambda item: item.career_score + item.finance_score + item.love_score,
    ).month
    evidence_refs = [
        "project.core.annual_timing_engine",
        str(annual_timing.get("engine_version", "annual_timing_proxy.v1")),
        str(pattern_payload.get("engine_version", "past_pattern_calibrator.v1")),
        "horo_v3_consensus",
    ]

    topics: list[TopicModule] = []
    for order, topic_id in enumerate(CANONICAL_TOPIC_IDS, start=1):
        title = _TOPIC_TITLES[topic_id]
        summary = (
            f"{title} for {request.target_year}: deterministic scores average "
            f"career {average_career:.1f}, finance {average_finance:.1f}, love {average_love:.1f}."
        )
        guidance = (
            f"Use month {strongest_month} as the strongest planning reference and review "
            "lower scoring months with extra preparation."
        )
        topics.append(
            TopicModule(
                topic_id=topic_id,
                order=order,
                title=title,
                summary=summary,
                guidance=guidance,
                confidence=_api_confidence(annual_timing.get("overall_confidence")),
                evidence_refs=evidence_refs,
            )
        )
    return topics


def _llm_translation_enabled() -> bool:
    values = (
        os.getenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED"),
        os.getenv("HORO_LITE_LLM_TRANSLATION_ENABLED"),
    )
    return any(str(value).lower() in {"1", "true", "yes", "on"} for value in values if value is not None)


@unified_reading_router.post("/unified-reading", response_model=UnifiedReadingResponse)
def create_unified_reading(request: UnifiedReadingRequest) -> UnifiedReadingResponse:
    """Return a deterministic unified reading without mutating core facts."""

    annual_timing = calculate_annual_timing(request)
    pattern_payload = generate_past_pattern_candidates(request)
    monthly_scores = _monthly_scores(annual_timing)
    topics = _topic_modules(request, monthly_scores, annual_timing, pattern_payload)
    llm_enabled = _llm_translation_enabled()

    response = UnifiedReadingResponse(
        request_id=_request_id_for(request),
        target_year=request.target_year,
        topics=topics,
        monthly_scores=monthly_scores,
        past_patterns=list(pattern_payload.get("candidates", [])),
        consensus_metadata=dict(annual_timing.get("consensus_metadata") or {}),
        hitl_flags=dict(annual_timing.get("hitl_flags") or {}),
        hitl_routing=dict(annual_timing.get("hitl_routing") or {}),
        llm_metadata={
            "source": "deterministic_copy_transformer" if not llm_enabled else "ai_agent_llm",
            "model_used": None if not llm_enabled else "disabled_for_unified_reading_guardrail",
            "translation_enabled": llm_enabled,
            "facts_mutable_by_llm": False,
            "network_call_performed": False,
            "deterministic_facts_source": "project.core.annual_timing_engine",
        },
    )
    return UnifiedReadingResponse.model_validate(_plain(response))
