from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError


TOPIC_IDS = [
    "personal_overview_strengths",
    "past_pattern_calibration",
    "annual_overview",
    "career_business",
    "finance",
    "love_relationships",
    "health_wellbeing",
    "family_surrounding_people",
    "opportunities_caution_periods",
    "twelve_month_roadmap",
    "top_priorities_cautions",
    "export_sharing_actions",
]


def _topic_modules() -> list[dict]:
    return [
        {
            "topic_id": topic_id,
            "order": index,
            "title": f"Topic {index}",
            "summary": f"Deterministic summary for topic {index}",
            "guidance": f"User-facing guidance for topic {index}",
            "confidence": "HIGH",
            "evidence_refs": ["thai_suriyayart", "bazi_liu_yue", "horo_v3_consensus"],
        }
        for index, topic_id in enumerate(TOPIC_IDS, start=1)
    ]


def _monthly_scores() -> list[dict]:
    return [
        {
            "month": month,
            "career_score": ((month + 2) % 10) + 1,
            "finance_score": ((month + 5) % 10) + 1,
            "love_score": ((month + 7) % 10) + 1,
            "confidence": "HIGH",
            "score_basis": {
                "thai_suriyayart": "Jupiter/Saturn/Rahu transit house evidence",
                "bazi_liu_yue": "60-JiaZi monthly cycle evidence",
            },
            "reasons": [
                "Thai Suriyayart transit evidence is present",
                "BaZi monthly-cycle evidence is present",
            ],
        }
        for month in range(1, 13)
    ]


def _past_patterns() -> list[dict]:
    return [
        {
            "pattern_id": "career_shift_2016_2017",
            "year_range": [2016, 2017],
            "age_range": [25, 26],
            "theme": "career_shift",
            "deterministic_basis": ["saturn_square", "da_yun_transition"],
            "sensitive_category": False,
            "allowed_feedback": ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
            "user_feedback": None,
        },
        {
            "pattern_id": "relocation_2019_2020",
            "year_range": [2019, 2020],
            "age_range": [28, 29],
            "theme": "relocation",
            "deterministic_basis": ["jupiter_return_window"],
            "sensitive_category": False,
            "allowed_feedback": ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
            "user_feedback": "จำไม่ได้",
        },
        {
            "pattern_id": "education_2011_2012",
            "year_range": [2011, 2012],
            "age_range": [20, 21],
            "theme": "education",
            "deterministic_basis": ["bazi_ten_year_luck_shift"],
            "sensitive_category": False,
            "allowed_feedback": ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
            "user_feedback": "ตรงบางส่วน",
        },
    ]


def _request_payload() -> dict:
    return {
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "unknown_hour": False,
        "birth_place": "Bangkok, Thailand",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
        "gender_at_birth": "female",
        "target_year": 2026,
        "locale": "th-TH",
        "display_name": "QA Baseline",
        "primary_focus_question": "ภาพรวมปีนี้ควรระวังเรื่องใด",
        "force_human_review": False,
    }


def _response_payload() -> dict:
    return {
        "schema_version": "horo_lite_unified_reading.v1",
        "request_id": "qa-baseline-001",
        "target_year": 2026,
        "topics": _topic_modules(),
        "monthly_scores": _monthly_scores(),
        "past_patterns": _past_patterns(),
        "consensus_metadata": {
            "engine_version": "horo_v3_consensus",
            "consensus_score": 0.82,
            "traditions_considered": ["thai_suriyayart", "bazi", "zi_wei"],
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
            "review_queue_id": None,
        },
        "llm_metadata": {
            "source": "ai_agent_llm",
            "model_used": "gemini-or-qwen-contract-placeholder",
            "facts_mutable_by_llm": False,
        },
    }


def test_unified_reading_schema_contract() -> None:
    from project.core.unified_reading_engine import (
        MonthlyScoreItem,
        PastPatternCandidate,
        TopicModule,
        UnifiedReadingRequest,
        UnifiedReadingResponse,
    )

    request = UnifiedReadingRequest.model_validate(_request_payload())
    assert request.birth_date.isoformat() == "1990-05-15"
    assert request.unknown_hour is False
    assert request.target_year == 2026
    assert request.force_human_review is False

    topic = TopicModule.model_validate(_topic_modules()[0])
    assert topic.topic_id == TOPIC_IDS[0]
    assert topic.order == 1
    assert "horo_v3_consensus" in topic.evidence_refs

    score = MonthlyScoreItem.model_validate(_monthly_scores()[0])
    assert score.month == 1
    assert 1 <= score.career_score <= 10
    assert 1 <= score.finance_score <= 10
    assert 1 <= score.love_score <= 10
    assert score.reasons

    pattern = PastPatternCandidate.model_validate(_past_patterns()[0])
    assert pattern.theme == "career_shift"
    assert pattern.sensitive_category is False
    assert pattern.allowed_feedback == ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]

    response = UnifiedReadingResponse.model_validate(_response_payload())
    assert response.schema_version == "horo_lite_unified_reading.v1"
    assert [topic.topic_id for topic in response.topics] == TOPIC_IDS
    assert [topic.order for topic in response.topics] == list(range(1, 13))
    assert len(response.monthly_scores) == 12
    assert {score.month for score in response.monthly_scores} == set(range(1, 13))
    for monthly_score in response.monthly_scores:
        assert 1 <= monthly_score.career_score <= 10
        assert 1 <= monthly_score.finance_score <= 10
        assert 1 <= monthly_score.love_score <= 10
        assert monthly_score.reasons
        assert monthly_score.score_basis
    assert 3 <= len(response.past_patterns) <= 5
    assert all(pattern.sensitive_category is False for pattern in response.past_patterns)
    assert response.consensus_metadata["consensus_score"] >= 0.75
    assert response.consensus_metadata["engine_version"] == "horo_v3_consensus"
    assert response.hitl_flags["required_human_review"] is False
    assert response.hitl_routing["status"] == "NOT_REQUIRED"
    assert response.llm_metadata["source"] == "ai_agent_llm"
    assert response.llm_metadata["facts_mutable_by_llm"] is False

    invalid_topic_count = deepcopy(_response_payload())
    invalid_topic_count["topics"] = invalid_topic_count["topics"][:-1]
    with pytest.raises(ValidationError):
        UnifiedReadingResponse.model_validate(invalid_topic_count)

    invalid_score_bounds = deepcopy(_response_payload())
    invalid_score_bounds["monthly_scores"][0]["career_score"] = 0
    invalid_score_bounds["monthly_scores"][1]["finance_score"] = 11
    invalid_score_bounds["monthly_scores"][2]["love_score"] = 12
    with pytest.raises(ValidationError):
        UnifiedReadingResponse.model_validate(invalid_score_bounds)

    invalid_sensitive_pattern = deepcopy(_response_payload())
    invalid_sensitive_pattern["past_patterns"][0]["theme"] = "death_or_illness"
    invalid_sensitive_pattern["past_patterns"][0]["sensitive_category"] = True
    with pytest.raises(ValidationError):
        UnifiedReadingResponse.model_validate(invalid_sensitive_pattern)

    invalid_hitl_low_consensus = deepcopy(_response_payload())
    invalid_hitl_low_consensus["consensus_metadata"]["consensus_score"] = 0.74
    invalid_hitl_low_consensus["hitl_flags"]["low_consensus"] = True
    invalid_hitl_low_consensus["hitl_flags"]["required_human_review"] = True
    invalid_hitl_low_consensus["hitl_routing"]["status"] = "NOT_REQUIRED"
    with pytest.raises(ValidationError):
        UnifiedReadingResponse.model_validate(invalid_hitl_low_consensus)
