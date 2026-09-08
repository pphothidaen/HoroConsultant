"""Unified Horo Lite reading API adapter for v3 routes."""

from __future__ import annotations

import hashlib
import json
import logging
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
from project.hitl_router import upsert_external_hitl_item


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
        kwargs: dict[str, Any] = {
            "month": int(month["month"]),
            "career_score": _score_from_month(month, "career"),
            "finance_score": _score_from_month(month, "finance"),
            "love_score": _score_from_month(month, "love"),
            "confidence": _api_confidence(month.get("confidence")),
            "score_basis": dict(month.get("score_basis") or {}),
            "reasons": list(month.get("reasons") or ["Deterministic annual timing evidence is present"]),
        }
        # Preserve uncertainty ranges when present (unknown_hour=True).
        for domain in ("career", "finance", "love"):
            score_range = month.get(f"{domain}_score_range")
            if isinstance(score_range, list | tuple) and len(score_range) == 2:
                kwargs[f"{domain}_score_range"] = [int(score_range[0]), int(score_range[1])]
        scores.append(MonthlyScoreItem(**kwargs))
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
    weakest_month = min(
        monthly_scores,
        key=lambda item: item.career_score + item.finance_score + item.love_score,
    ).month

    best_career_month = max(monthly_scores, key=lambda i: i.career_score).month
    best_finance_month = max(monthly_scores, key=lambda i: i.finance_score).month
    best_love_month = max(monthly_scores, key=lambda i: i.love_score).month
    worst_career_month = min(monthly_scores, key=lambda i: i.career_score).month
    worst_finance_month = min(monthly_scores, key=lambda i: i.finance_score).month
    worst_love_month = min(monthly_scores, key=lambda i: i.love_score).month

    num_patterns = len(pattern_payload.get("candidates", []))
    overall_avg = (average_career + average_finance + average_love) / 3.0

    evidence_refs = [
        "project.core.annual_timing_engine",
        str(annual_timing.get("engine_version", "annual_timing_proxy.v1")),
        str(pattern_payload.get("engine_version", "past_pattern_calibrator.v1")),
        "horo_v3_consensus",
    ]

    # Each topic gets distinct, evidence-grounded summary and guidance.
    topic_content: dict[str, tuple[str, str]] = {
        "personal_overview_strengths": (
            f"Overall profile for {request.target_year}: average scores are "
            f"career {average_career:.1f}/10, finance {average_finance:.1f}/10, "
            f"love {average_love:.1f}/10 across 12 months.",
            f"Month {strongest_month} is your peak period with the highest combined scores. "
            f"Month {weakest_month} requires extra vigilance. Focus strengths on the domains "
            f"that score above 6 to build momentum.",
        ),
        "past_pattern_calibration": (
            f"Past pattern analysis identified {num_patterns} calibration "
            f"candidate(s) from historical cycle positions."
            if num_patterns > 0
            else "No past pattern candidates available for calibration due to insufficient history.",
            "Review each past pattern candidate honestly — your feedback refines the accuracy "
            "of future readings. Select the response that best matches your memory."
            if num_patterns > 0
            else "Past patterns will become available as more life-cycle data accumulates.",
        ),
        "annual_overview": (
            f"Annual trajectory for {request.target_year}: combined average "
            f"{overall_avg:.1f}/10. Strongest month is {strongest_month}, "
            f"weakest is {weakest_month}.",
            f"Plan major decisions around month {strongest_month} when all three domains "
            f"peak together. Reserve month {weakest_month} for review and preparation "
            f"rather than new commitments.",
        ),
        "career_business": (
            f"Career average {average_career:.1f}/10 for {request.target_year}. "
            f"Best career month: {best_career_month}, "
            f"most cautious: {worst_career_month}.",
            f"Pursue promotions, launches, or negotiations in month {best_career_month} "
            f"when career energy peaks. In month {worst_career_month}, focus on skill "
            f"building and relationship maintenance rather than high-stakes moves.",
        ),
        "finance": (
            f"Finance average {average_finance:.1f}/10 for {request.target_year}. "
            f"Best finance month: {best_finance_month}, "
            f"most cautious: {worst_finance_month}.",
            f"Month {best_finance_month} favors investments, contract signings, and "
            f"revenue-generating activities. Exercise spending discipline in month "
            f"{worst_finance_month} and avoid large unplanned commitments.",
        ),
        "love_relationships": (
            f"Love and relationships average {average_love:.1f}/10 for {request.target_year}. "
            f"Best relationship month: {best_love_month}, "
            f"most cautious: {worst_love_month}.",
            f"Month {best_love_month} is ideal for deepening bonds, important conversations, "
            f"or meeting new people. In month {worst_love_month}, practice patience and avoid "
            f"confrontational discussions.",
        ),
        "health_wellbeing": (
            f"Health outlook derived from cross-domain stress indicators for "
            f"{request.target_year}. Lower combined scores in month {weakest_month} "
            f"may correlate with elevated stress.",
            f"Schedule health check-ups and rest periods around month {weakest_month}. "
            f"Month {strongest_month} supports active lifestyle goals and new fitness routines.",
        ),
        "family_surrounding_people": (
            f"Family dynamics for {request.target_year}: relationship energy averages "
            f"{average_love:.1f}/10 while career demands average {average_career:.1f}/10.",
            f"Balance family time against career peaks — month {best_career_month} may pull "
            f"attention from family. Dedicate month {best_love_month} to quality family "
            f"interactions and relationship nurturing.",
        ),
        "opportunities_caution_periods": (
            f"Opportunity windows for {request.target_year}: month {strongest_month} "
            f"presents the best combined conditions. Caution period: month {weakest_month}.",
            f"Seize opportunities in month {strongest_month} when career ({best_career_month}), "
            f"finance ({best_finance_month}), and relationship ({best_love_month}) energies "
            f"converge. Approach month {weakest_month} with contingency plans.",
        ),
        "twelve_month_roadmap": (
            f"Month-by-month roadmap for {request.target_year}: 12 months scored across "
            f"career, finance, and love with confidence from consensus arbitration.",
            f"Q1 (months 1-3): establish foundations. Q2 (months 4-6): execute on strengths "
            f"near month {strongest_month}. Q3 (months 7-9): consolidate gains. "
            f"Q4 (months 10-12): review progress and plan the next cycle.",
        ),
        "top_priorities_cautions": (
            f"Priority ranking for {request.target_year}: "
            + (
                f"career leads at {average_career:.1f}/10"
                if average_career >= average_finance and average_career >= average_love
                else (
                    f"finance leads at {average_finance:.1f}/10"
                    if average_finance >= average_love
                    else f"relationships lead at {average_love:.1f}/10"
                )
            )
            + f". Top caution month: {weakest_month}.",
            f"Prioritize the leading domain and use it to support weaker areas. "
            f"Key caution: do not overextend in month {weakest_month} — prepare buffers "
            f"in the preceding month.",
        ),
        "export_sharing_actions": (
            f"Reading export for {request.target_year}: {num_patterns} past pattern(s), "
            f"12 monthly scores, consensus-verified by {annual_timing.get('engine_version', 'v1')}.",
            "Save or share this reading for future reference. Monthly scores and past "
            "pattern feedback are portable across export formats.",
        ),
    }

    topics: list[TopicModule] = []
    for order, topic_id in enumerate(CANONICAL_TOPIC_IDS, start=1):
        title = _TOPIC_TITLES[topic_id]
        summary, guidance = topic_content[topic_id]
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

    candidates = list(pattern_payload.get("candidates", []))
    insufficient_reason: str | None = None
    if not candidates:
        birth_year = request.birth_date.year
        age_at_target = request.target_year - birth_year
        insufficient_reason = (
            f"Person is approximately {age_at_target} years old at target year "
            f"{request.target_year}; insufficient history for past-pattern analysis "
            f"(minimum age ~8 required)"
        )

    hitl_flags_dict = dict(annual_timing.get("hitl_flags") or {})
    hitl_routing_dict = dict(annual_timing.get("hitl_routing") or {})

    response = UnifiedReadingResponse(
        request_id=_request_id_for(request),
        target_year=request.target_year,
        topics=topics,
        monthly_scores=monthly_scores,
        past_patterns=candidates,
        insufficient_history_reason=insufficient_reason,
        consensus_metadata=dict(annual_timing.get("consensus_metadata") or {}),
        hitl_flags=hitl_flags_dict,
        hitl_routing=hitl_routing_dict,
        llm_metadata={
            "source": "deterministic_copy_transformer",
            "model_used": None,
            "translation_requested": llm_enabled,
            "translation_enabled_by_env": llm_enabled,
            "facts_mutable_by_llm": False,
            "network_call_performed": False,
            "deterministic_facts_source": "project.core.annual_timing_engine",
        },
    )
    validated = UnifiedReadingResponse.model_validate(_plain(response))

    # Enqueue HITL review item when routing requires human review.
    if hitl_routing_dict.get("status") == "QUEUED_FOR_HUMAN_REVIEW":
        if not _enqueue_hitl_review(request, validated, hitl_flags_dict, hitl_routing_dict):
            validated.hitl_routing["status"] = "HITL_ENQUEUE_FAILED"
            validated.hitl_routing["reason"] = "hitl_persistence_failed"
            validated.hitl_routing["queued"] = False

    return validated


def _enqueue_hitl_review(
    request: UnifiedReadingRequest,
    response: UnifiedReadingResponse,
    hitl_flags: dict[str, Any],
    hitl_routing: dict[str, Any],
) -> bool:
    """Create a retrievable HITL review item from a unified reading.

    This is idempotent — the same request_id maps to the same HITL item,
    so re-requesting the same reading upserts rather than duplicating.
    """
    trigger_reasons = hitl_routing.get("trigger_reasons", [])
    consensus_score = hitl_routing.get("consensus_score")

    question = (
        f"Unified reading for target year {request.target_year}, "
        f"birth {request.birth_date.isoformat()}, place {request.birth_place}. "
        f"HITL triggers: {', '.join(trigger_reasons) if trigger_reasons else 'unspecified'}."
    )

    try:
        upsert_external_hitl_item({
            "item_id": response.request_id,
            "source_domain": "horo-lite-unified-reading",
            "source_id": response.request_id,
            "source_title": f"Unified Reading {request.target_year}",
            "category": "unified_reading_review",
            "question": question,
            "required_human_review": True,
            "conflict_detected": hitl_flags.get("conflict_detected", False),
            "conflicting_domains": hitl_routing.get("conflicting_domains", []),
            "consensus_score": consensus_score,
            "hitl_routing": hitl_routing,
            "notes": f"Auto-enqueued from unified reading router. Triggers: {trigger_reasons}",
        })
        return True
    except Exception:
        # Enqueue failure must not break the reading response.
        logging.getLogger("unified_reading_router").warning(
            "Failed to enqueue HITL review item for %s", response.request_id,
            exc_info=True,
        )
        return False
