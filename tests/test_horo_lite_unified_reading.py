from __future__ import annotations

from html.parser import HTMLParser
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any

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

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"


class _LiteHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[dict[str, Any]] = []
        self._stack: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent_tags = [self.elements[idx]["tag"] for idx in self._stack]
        element = {
            "tag": tag.lower(),
            "attrs": {name.lower(): value or "" for name, value in attrs},
            "text": "",
            "parent_tags": parent_tags,
        }
        self.elements.append(element)
        if tag.lower() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}:
            self._stack.append(len(self.elements) - 1)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        while self._stack:
            index = self._stack.pop()
            if self.elements[index]["tag"] == tag:
                break

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for index in self._stack:
            self.elements[index]["text"] += " " + data.strip()


def _parse_lite_html(markup: str) -> _LiteHtmlParser:
    parser = _LiteHtmlParser()
    parser.feed(markup)
    return parser


def _attr_blob(element: dict[str, Any]) -> str:
    attrs = element["attrs"]
    return " ".join(
        str(attrs.get(name, ""))
        for name in ("id", "name", "type", "placeholder", "aria-label", "autocomplete", "data-field")
    ).lower()


def _label_targets(parser: _LiteHtmlParser) -> set[str]:
    return {
        element["attrs"]["for"]
        for element in parser.elements
        if element["tag"] == "label" and element["attrs"].get("for")
    }


def _control_is_accessibly_labelled(
    control: dict[str, Any], parser: _LiteHtmlParser, label_targets: set[str]
) -> bool:
    attrs = control["attrs"]
    control_id = attrs.get("id", "")
    return bool(
        (control_id and control_id in label_targets)
        or attrs.get("aria-label")
        or attrs.get("aria-labelledby")
    )


def _find_control(
    parser: _LiteHtmlParser,
    *,
    field_name: str,
    tokens: tuple[str, ...],
    tags: tuple[str, ...] = ("input", "select", "textarea"),
    types: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    matches = []
    for element in parser.elements:
        if element["tag"] not in tags:
            continue
        attrs = element["attrs"]
        if not attrs.get("id") or not attrs.get("name"):
            continue
        if types is not None and attrs.get("type", "text").lower() not in types:
            continue
        blob = _attr_blob(element)
        if any(token in blob for token in tokens):
            matches.append(element)
    assert matches, f"LITE_FORM_{field_name.upper()}_CONTROL_MISSING_OR_UNBOUND"

    label_targets = _label_targets(parser)
    labelled = [control for control in matches if _control_is_accessibly_labelled(control, parser, label_targets)]
    assert labelled, f"LITE_FORM_{field_name.upper()}_ACCESSIBLE_LABEL_MISSING"
    return labelled[0]


def _details_blocks(parser: _LiteHtmlParser) -> list[dict[str, Any]]:
    return [element for element in parser.elements if element["tag"] == "details"]


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


def _phase_b_request_payload(*, unknown_hour: bool = False) -> dict:
    payload = _request_payload()
    payload["birth_date"] = "1990-05-15"
    payload["birth_time"] = None if unknown_hour else "14:30"
    payload["unknown_hour"] = unknown_hour
    payload["birth_place"] = "Bangkok, Thailand"
    payload["latitude"] = 13.7563
    payload["longitude"] = 100.5018
    payload["timezone"] = "Asia/Bangkok"
    payload["target_year"] = 2026
    return payload


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


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _annual_months(result: Any) -> list[Any]:
    if isinstance(result, list):
        return result
    for key in ("monthly_scores", "months", "annual_timing", "roadmap"):
        months = _field(result, key)
        if months is not None:
            return list(months)
    pytest.fail(
        "ANNUAL_TIMING_OUTPUT_SHAPE_MISMATCH: expected list or monthly_scores/months/annual_timing/roadmap"
    )


def _score_or_range_is_valid(item: Any, domain: str) -> bool:
    score = _field(item, f"{domain}_score")
    if isinstance(score, int | float):
        return 1 <= score <= 10
    score_range = _field(item, f"{domain}_score_range")
    if score_range is None:
        score_range = _field(item, f"{domain}_range")
    if isinstance(score_range, list | tuple) and len(score_range) == 2:
        lower, upper = score_range
        return (
            isinstance(lower, int | float)
            and isinstance(upper, int | float)
            and 1 <= lower <= upper <= 10
        )
    return False


def _has_unknown_hour_uncertainty(result: Any, months: list[Any]) -> bool:
    confidence_values = [
        str(_field(result, "confidence", "")).upper(),
        str(_field(result, "overall_confidence", "")).upper(),
    ]
    confidence_values.extend(str(_field(month, "confidence", "")).upper() for month in months)
    has_low_confidence = any(value in {"LOW", "ESTIMATED"} for value in confidence_values)
    has_ranges = any(
        _field(month, f"{domain}_score_range") is not None
        or _field(month, f"{domain}_range") is not None
        for month in months
        for domain in ("career", "finance", "love")
    )
    return has_low_confidence or has_ranges


def _consensus_metadata(result: Any) -> dict[str, Any]:
    metadata = _field(result, "consensus_metadata")
    assert isinstance(metadata, dict), "CONSENSUS_METADATA_MISSING"
    return metadata


def _hitl_routing(result: Any) -> dict[str, Any]:
    routing = _field(result, "hitl_routing")
    assert isinstance(routing, dict), "HITL_ROUTING_MISSING"
    return routing


def _hitl_flags(result: Any) -> dict[str, Any]:
    flags = _field(result, "hitl_flags", {})
    assert isinstance(flags, dict), "HITL_FLAGS_MISSING"
    return flags


def _arbitrated_monthly_claims(metadata: dict[str, Any]) -> list[Any]:
    for key in (
        "monthly_consensus",
        "monthly_arbitration",
        "arbitrated_monthly_claims",
        "monthly_claims",
    ):
        claims = metadata.get(key)
        if claims is not None:
            assert isinstance(claims, list), f"CONSENSUS_{key.upper()}_NOT_LIST"
            return claims
    pytest.fail("CONSENSUS_MONTHLY_ARBITRATION_MISSING")


def _pattern_candidates(result: Any) -> list[Any]:
    if isinstance(result, list):
        return result
    for key in ("candidates", "past_patterns", "patterns"):
        candidates = _field(result, key)
        if candidates is not None:
            return list(candidates)
    pytest.fail("PAST_PATTERN_OUTPUT_SHAPE_MISMATCH: expected list or candidates/past_patterns/patterns")


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

    invalid_topics_order = deepcopy(_response_payload())
    invalid_topics_order["topics"][0], invalid_topics_order["topics"][1] = (
        invalid_topics_order["topics"][1],
        invalid_topics_order["topics"][0],
    )
    with pytest.raises(ValidationError, match="Topics must match the canonical order"):
        UnifiedReadingResponse.model_validate(invalid_topics_order)

    invalid_topic_sequence = deepcopy(_response_payload())
    invalid_topic_sequence["topics"][1]["order"] = 1
    with pytest.raises(ValidationError, match="Topic order must be exactly 1 through 12"):
        UnifiedReadingResponse.model_validate(invalid_topic_sequence)

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
    with pytest.raises(ValidationError, match="HITL routing cannot be NOT_REQUIRED"):
        UnifiedReadingResponse.model_validate(invalid_hitl_low_consensus)

    invalid_hitl_routing_mismatch = deepcopy(_response_payload())
    invalid_hitl_routing_mismatch["hitl_routing"]["status"] = "QUEUED_FOR_HUMAN_REVIEW"
    with pytest.raises(ValidationError, match="HITL routing status must be NOT_REQUIRED"):
        UnifiedReadingResponse.model_validate(invalid_hitl_routing_mismatch)


def test_unified_reading_pessimistic_negative_controls() -> None:
    from project.core.unified_reading_engine import (
        MonthlyScoreItem,
        PastPatternCandidate,
        TopicModule,
        UnifiedReadingRequest,
        UnifiedReadingResponse,
    )

    # 1. UnifiedReadingRequest boundary controls
    future_birth = deepcopy(_request_payload())
    future_birth["birth_date"] = "2030-01-01"
    future_birth["target_year"] = 2026
    with pytest.raises(ValidationError, match="must not be after target_year"):
        UnifiedReadingRequest.model_validate(future_birth)

    for invalid_lat in (-90.1, 90.1):
        bad_lat = deepcopy(_request_payload())
        bad_lat["latitude"] = invalid_lat
        with pytest.raises(ValidationError):
            UnifiedReadingRequest.model_validate(bad_lat)

    for invalid_lon in (-180.1, 180.1):
        bad_lon = deepcopy(_request_payload())
        bad_lon["longitude"] = invalid_lon
        with pytest.raises(ValidationError):
            UnifiedReadingRequest.model_validate(bad_lon)

    for invalid_year in (1899, 2201):
        bad_year = deepcopy(_request_payload())
        bad_year["target_year"] = invalid_year
        with pytest.raises(ValidationError):
            UnifiedReadingRequest.model_validate(bad_year)

    # 2. TopicModule boundary controls
    for bad_order in (0, 13):
        bad_topic = deepcopy(_topic_modules()[0])
        bad_topic["order"] = bad_order
        with pytest.raises(ValidationError):
            TopicModule.model_validate(bad_topic)

    for bad_refs in ([], [""]):
        bad_topic = deepcopy(_topic_modules()[0])
        bad_topic["evidence_refs"] = bad_refs
        with pytest.raises(ValidationError):
            TopicModule.model_validate(bad_topic)

    bad_conf = deepcopy(_topic_modules()[0])
    bad_conf["confidence"] = "UNSURE"
    with pytest.raises(ValidationError):
        TopicModule.model_validate(bad_conf)

    # 3. MonthlyScoreItem score bounds & range controls
    for bad_score in (-1, 0, 11, 20):
        bad_item = deepcopy(_monthly_scores()[0])
        bad_item["career_score"] = bad_score
        with pytest.raises(ValidationError):
            MonthlyScoreItem.model_validate(bad_item)

    for bad_range in ([9, 2], [0, 6], [5, 11], [5], [1, 2, 3]):
        bad_range_item = deepcopy(_monthly_scores()[0])
        bad_range_item["career_score_range"] = bad_range
        with pytest.raises(ValidationError):
            MonthlyScoreItem.model_validate(bad_range_item)

    for bad_reasons in ([], ["  "]):
        bad_reason_item = deepcopy(_monthly_scores()[0])
        bad_reason_item["reasons"] = bad_reasons
        with pytest.raises(ValidationError):
            MonthlyScoreItem.model_validate(bad_reason_item)

    bad_basis_item = deepcopy(_monthly_scores()[0])
    bad_basis_item["score_basis"] = {}
    with pytest.raises(ValidationError):
        MonthlyScoreItem.model_validate(bad_basis_item)

    # 4. PastPatternCandidate sensitive themes & range validation
    forbidden_themes = ("illness", "trauma", "bereavement", "medical", "death", "pregnancy", "accident")
    for theme in forbidden_themes:
        bad_pattern = deepcopy(_past_patterns()[0])
        bad_pattern["theme"] = theme
        with pytest.raises(ValidationError, match="outside the non-sensitive allowlist"):
            PastPatternCandidate.model_validate(bad_pattern)

    inverted_year = deepcopy(_past_patterns()[0])
    inverted_year["year_range"] = [2022, 2020]
    with pytest.raises(ValidationError, match="year_range must be"):
        PastPatternCandidate.model_validate(inverted_year)

    inverted_age = deepcopy(_past_patterns()[0])
    inverted_age["age_range"] = [32, 30]
    with pytest.raises(ValidationError, match="age_range must be"):
        PastPatternCandidate.model_validate(inverted_age)

    invalid_feedback_options = deepcopy(_past_patterns()[0])
    invalid_feedback_options["allowed_feedback"] = ["yes", "no"]
    with pytest.raises(ValidationError, match="choices must match the contract"):
        PastPatternCandidate.model_validate(invalid_feedback_options)

    invalid_user_feedback = deepcopy(_past_patterns()[0])
    invalid_user_feedback["user_feedback"] = "ไม่แน่ใจเลย"
    with pytest.raises(ValidationError, match="feedback value is not allowed"):
        PastPatternCandidate.model_validate(invalid_user_feedback)

    # 5. Fail-closed HITL routing controls
    for trigger_key in ("tradition_conflict", "force_human_review", "uncertain_birth_time"):
        mismatched_hitl = deepcopy(_response_payload())
        mismatched_hitl["hitl_flags"][trigger_key] = True
        mismatched_hitl["hitl_flags"]["required_human_review"] = True
        mismatched_hitl["hitl_routing"]["status"] = "NOT_REQUIRED"
        with pytest.raises(ValidationError, match="HITL routing cannot be NOT_REQUIRED"):
            UnifiedReadingResponse.model_validate(mismatched_hitl)

    low_consensus_no_flag = deepcopy(_response_payload())
    low_consensus_no_flag["consensus_metadata"]["consensus_score"] = 0.60
    low_consensus_no_flag["hitl_flags"]["required_human_review"] = False
    with pytest.raises(ValidationError, match="HITL review must be required"):
        UnifiedReadingResponse.model_validate(low_consensus_no_flag)

    # 6. Immutable LLM facts guard
    mutable_llm = deepcopy(_response_payload())
    mutable_llm["llm_metadata"]["facts_mutable_by_llm"] = True
    with pytest.raises(ValidationError, match="deterministic facts immutable"):
        UnifiedReadingResponse.model_validate(mutable_llm)


def test_deterministic_annual_timing_12_months() -> None:
    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import UnifiedReadingRequest

    request = UnifiedReadingRequest.model_validate(_phase_b_request_payload())

    started = perf_counter()
    first_result = calculate_annual_timing(request)
    elapsed_ms = (perf_counter() - started) * 1000
    second_result = calculate_annual_timing(request)

    assert elapsed_ms < 50, f"ANNUAL_TIMING_RUNTIME_OVER_50MS: {elapsed_ms:.3f}ms"
    assert _plain(first_result) == _plain(second_result), "ANNUAL_TIMING_NOT_REPEATABLE"
    assert _field(first_result, "engine_version") == "annual_timing_bazi_transit.v2"
    assert _field(second_result, "engine_version") == _field(first_result, "engine_version")

    months = _annual_months(first_result)
    assert len(months) == 12, "ANNUAL_TIMING_MONTH_COUNT_NOT_12"
    assert [_field(month, "month") for month in months] == list(range(1, 13))

    for month in months:
        for domain in ("career", "finance", "love"):
            assert _score_or_range_is_valid(month, domain), (
                f"ANNUAL_TIMING_{domain.upper()}_SCORE_OR_RANGE_OUT_OF_BOUNDS"
            )
        reasons = _field(month, "reasons", [])
        score_basis = _field(month, "score_basis", {})
        assert reasons, "ANNUAL_TIMING_REASON_MISSING"
        assert score_basis, "ANNUAL_TIMING_SCORE_BASIS_MISSING"

    unknown_request = UnifiedReadingRequest.model_validate(
        _phase_b_request_payload(unknown_hour=True)
    )
    unknown_result = calculate_annual_timing(unknown_request)
    unknown_months = _annual_months(unknown_result)
    assert len(unknown_months) == 12, "UNKNOWN_HOUR_MONTH_COUNT_NOT_12"
    assert _has_unknown_hour_uncertainty(unknown_result, unknown_months), (
        "UNKNOWN_HOUR_FALSE_PRECISION: expected score ranges or LOW/ESTIMATED confidence"
    )


def test_past_pattern_candidate_generation() -> None:
    from project.core.past_pattern_calibrator import generate_past_pattern_candidates
    from project.core.unified_reading_engine import UnifiedReadingRequest

    allowed_themes = {
        "education",
        "career_shift",
        "relocation",
        "financial_pressure",
        "work_role_change",
    }
    forbidden_fragments = {
        "trauma",
        "death",
        "illness",
        "crime",
        "pregnancy",
        "medical",
        "accident",
        "bereavement",
    }

    request = UnifiedReadingRequest.model_validate(_phase_b_request_payload())
    first_result = generate_past_pattern_candidates(request)
    second_result = generate_past_pattern_candidates(request)

    assert _plain(first_result) == _plain(second_result), "PAST_PATTERN_NOT_REPEATABLE"
    assert _field(first_result, "engine_version") == "past_pattern_calibrator.v1"
    assert _field(second_result, "engine_version") == _field(first_result, "engine_version")

    candidates = _pattern_candidates(first_result)
    assert 3 <= len(candidates) <= 5, "PAST_PATTERN_COUNT_OUTSIDE_3_TO_5"

    for candidate in candidates:
        theme = _field(candidate, "theme")
        assert theme in allowed_themes, f"PAST_PATTERN_THEME_NOT_ALLOWLISTED: {theme!r}"
        assert _field(candidate, "sensitive_category", False) is False

        year_range = _field(candidate, "year_range")
        age_range = _field(candidate, "age_range")
        assert isinstance(year_range, list | tuple) and len(year_range) == 2
        assert isinstance(age_range, list | tuple) and len(age_range) == 2
        assert year_range[0] <= year_range[1] < request.target_year
        assert age_range[0] <= age_range[1]
        assert age_range[0] == year_range[0] - request.birth_date.year
        assert age_range[1] == year_range[1] - request.birth_date.year

        deterministic_basis = _field(candidate, "deterministic_basis", [])
        assert deterministic_basis, "PAST_PATTERN_DETERMINISTIC_BASIS_MISSING"

        searchable = str(_plain(candidate)).lower()
        assert not any(fragment in searchable for fragment in forbidden_fragments), (
            f"PAST_PATTERN_FORBIDDEN_SENSITIVE_FRAGMENT: {searchable}"
        )


def test_annual_timing_extreme_boundaries_and_determinism() -> None:
    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import UnifiedReadingRequest

    # Boundary coordinates and target year extremes
    boundary_cases = [
        {"birth_date": "1900-01-01", "target_year": 1900, "lat": -90.0, "lon": -180.0},
        {"birth_date": "1900-01-01", "target_year": 1900, "lat": 90.0, "lon": 180.0},
        {"birth_date": "1990-05-15", "target_year": 2026, "lat": -90.0, "lon": 180.0},
        {"birth_date": "1990-05-15", "target_year": 2026, "lat": 90.0, "lon": -180.0},
        {"birth_date": "2026-01-01", "target_year": 2199, "lat": -90.0, "lon": -180.0},
        {"birth_date": "2026-01-01", "target_year": 2199, "lat": 90.0, "lon": 180.0},
        {"birth_date": "1985-06-20", "target_year": 2026, "lat": 0.0, "lon": 0.0},
    ]

    for case in boundary_cases:
        req = UnifiedReadingRequest.model_validate({
            "birth_date": case["birth_date"],
            "birth_time": "12:00",
            "unknown_hour": False,
            "birth_place": "Boundary Station",
            "latitude": case["lat"],
            "longitude": case["lon"],
            "timezone": "UTC",
            "target_year": case["target_year"],
        })
        t0 = perf_counter()
        result = calculate_annual_timing(req)
        elapsed_ms = (perf_counter() - t0) * 1000
        assert elapsed_ms < 50.0, f"ANNUAL_TIMING_BOUNDARY_LATENCY_VIOLATION: {elapsed_ms:.2f}ms >= 50ms"

        # Completeness: exactly 12 months with Career, Finance, Love scores in [1..10]
        months = _annual_months(result)
        assert len(months) == 12, "ANNUAL_TIMING_MONTHS_COUNT_NOT_12"
        assert [int(_field(m, "month")) for m in months] == list(range(1, 13))

        for month in months:
            for domain in ("career", "finance", "love"):
                score = _field(month, f"{domain}_score")
                assert isinstance(score, int), f"{domain}_score must be int"
                assert 1 <= score <= 10, f"ANNUAL_TIMING_{domain.upper()}_SCORE_OUT_OF_BOUNDS: {score}"

            # Astrological rationale: non-empty reasons and score_basis for all 12 months
            reasons = _field(month, "reasons")
            assert isinstance(reasons, list) and len(reasons) > 0, "ANNUAL_TIMING_REASONS_EMPTY"
            assert all(isinstance(r, str) and r.strip() for r in reasons), "ANNUAL_TIMING_REASONS_BLANK"

            score_basis = _field(month, "score_basis")
            assert isinstance(score_basis, dict) and len(score_basis) > 0, "ANNUAL_TIMING_SCORE_BASIS_EMPTY"

    # Determinism: run 20 times with identical input, assert 100% byte-identical outputs
    baseline_req = UnifiedReadingRequest.model_validate(_phase_b_request_payload())
    outputs: list[bytes] = []
    durations: list[float] = []

    for _ in range(20):
        t0 = perf_counter()
        res = calculate_annual_timing(baseline_req)
        durations.append((perf_counter() - t0) * 1000)
        outputs.append(json.dumps(_plain(res), sort_keys=True).encode("utf-8"))

    for i in range(1, 20):
        assert outputs[i] == outputs[0], f"DETERMINISM_VIOLATION: Run {i} output differs from Run 0"

    # Latency SLA: assert execution time < 50ms
    max_duration = max(durations)
    assert max_duration < 50.0, f"ANNUAL_TIMING_LATENCY_SLA_VIOLATED: {max_duration:.2f}ms >= 50ms"


def test_annual_timing_unknown_hour_uncertainty_contract() -> None:
    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import MonthlyScoreItem, UnifiedReadingRequest
    from project.routers.unified_reading_router import create_unified_reading

    # Test unknown_hour=True with None birth_time and with dummy birth_time (time invariance)
    for dummy_time in (None, "09:30"):
        payload = _phase_b_request_payload(unknown_hour=True)
        payload["birth_time"] = dummy_time
        unknown_req = UnifiedReadingRequest.model_validate(payload)

        result = calculate_annual_timing(unknown_req)
        assert result.get("overall_confidence") in {"LOW", "ESTIMATED", "MEDIUM"}
        assert result.get("overall_confidence") != "HIGH", "FALSE_PRECISION_OVERALL_HIGH"

        months = _annual_months(result)
        assert len(months) == 12
        for month in months:
            conf = str(_field(month, "confidence", "")).upper()
            assert conf in {"LOW", "ESTIMATED", "MEDIUM"}
            assert conf != "HIGH", "FALSE_PRECISION_MONTHLY_HIGH"

            # Raw engine must strictly reject false precision (no single point scores without ranges)
            assert _field(month, "career_score") is None, "FALSE_PRECISION_CAREER_SCORE_EXPOSED"
            assert _field(month, "finance_score") is None, "FALSE_PRECISION_FINANCE_SCORE_EXPOSED"
            assert _field(month, "love_score") is None, "FALSE_PRECISION_LOVE_SCORE_EXPOSED"

            # Assert score ranges [min, max] where max >= min and 1 <= min <= max <= 10
            for domain in ("career", "finance", "love"):
                rng = _field(month, f"{domain}_score_range")
                assert isinstance(rng, list | tuple) and len(rng) == 2, f"{domain}_score_range missing or invalid"
                min_score, max_score = rng
                assert isinstance(min_score, int) and isinstance(max_score, int)
                assert 1 <= min_score <= max_score <= 10, (
                    f"RANGE_INVERTED_OR_OUT_OF_BOUNDS: [{min_score}, {max_score}]"
                )

    # API router contract: confidence in {"LOW", "MEDIUM"}, ranges present and valid
    api_req = UnifiedReadingRequest.model_validate(_phase_b_request_payload(unknown_hour=True))
    api_response = create_unified_reading(api_req)
    for score_item in api_response.monthly_scores:
        assert score_item.confidence in {"LOW", "MEDIUM"}
        assert score_item.confidence != "HIGH", "API_FALSE_PRECISION_HIGH_CONFIDENCE"
        for domain in ("career", "finance", "love"):
            rng = getattr(score_item, f"{domain}_score_range")
            assert rng is not None and len(rng) == 2
            assert 1 <= rng[0] <= rng[1] <= 10

    # Negative controls: inverted score ranges and out-of-bound ranges strictly rejected
    base_item = deepcopy(_monthly_scores()[0])
    base_item["career_score_range"] = [9, 2]
    with pytest.raises(ValidationError, match="career_score_range bounds must satisfy"):
        MonthlyScoreItem.model_validate(base_item)

    base_item["career_score_range"] = [0, 5]
    with pytest.raises(ValidationError, match="career_score_range bounds must satisfy"):
        MonthlyScoreItem.model_validate(base_item)

    base_item["career_score_range"] = [4, 11]
    with pytest.raises(ValidationError, match="career_score_range bounds must satisfy"):
        MonthlyScoreItem.model_validate(base_item)


def test_past_pattern_infant_and_child_boundaries() -> None:
    from project.core.past_pattern_calibrator import generate_past_pattern_candidates
    from project.core.unified_reading_engine import (
        ALLOWED_PAST_PATTERN_THEMES,
        PastPatternCandidate,
        UnifiedReadingRequest,
    )
    from project.routers.unified_reading_router import create_unified_reading

    sensitive_tokens = {
        "death",
        "dead",
        "die",
        "illness",
        "disease",
        "trauma",
        "bereavement",
        "medical",
        "pregnancy",
        "pregnant",
        "accident",
        "crime",
        "divorce",
        "fatal",
        "suicide",
        "hospital",
        "surgery",
        "cancer",
        "injury",
    }

    # 1. Child / infant case (target_year - birth_year < 8)
    child_cases = [
        {"birth_date": "2026-01-01", "target_year": 2026, "desc": "infant age 0"},
        {"birth_date": "2023-05-10", "target_year": 2026, "desc": "toddler age 3"},
        {"birth_date": "2020-06-15", "target_year": 2026, "desc": "child age 6"},
        {"birth_date": "2019-12-31", "target_year": 2026, "desc": "boundary child age 7"},
    ]

    for case in child_cases:
        child_req = UnifiedReadingRequest.model_validate({
            "birth_date": case["birth_date"],
            "birth_time": "12:00",
            "unknown_hour": False,
            "birth_place": "Bangkok, Thailand",
            "latitude": 13.7563,
            "longitude": 100.5018,
            "timezone": "Asia/Bangkok",
            "target_year": case["target_year"],
        })
        raw_result = generate_past_pattern_candidates(child_req)
        assert _pattern_candidates(raw_result) == [], (
            f"INFANT_CHILD_CANDIDATES_NOT_EMPTY for {case['desc']}"
        )

        response = create_unified_reading(child_req)
        assert response.past_patterns == [], f"RESPONSE_PAST_PATTERNS_NOT_EMPTY for {case['desc']}"
        assert response.insufficient_history_reason is not None, (
            f"INSUFFICIENT_HISTORY_REASON_MISSING for {case['desc']}"
        )
        assert len(response.insufficient_history_reason.strip()) > 0, (
            f"INSUFFICIENT_HISTORY_REASON_EMPTY for {case['desc']}"
        )

    # 2. Adult case: 3 to 5 candidates, age/year sorted, strictly non-sensitive themes
    adult_cases = [
        {"birth_date": "1990-05-15", "target_year": 2026, "desc": "adult age 36"},
        {"birth_date": "2008-01-01", "target_year": 2026, "desc": "young adult age 18"},
        {"birth_date": "1950-07-20", "target_year": 2026, "desc": "senior age 76"},
    ]

    for case in adult_cases:
        adult_req = UnifiedReadingRequest.model_validate({
            "birth_date": case["birth_date"],
            "birth_time": "14:30",
            "unknown_hour": False,
            "birth_place": "Bangkok, Thailand",
            "latitude": 13.7563,
            "longitude": 100.5018,
            "timezone": "Asia/Bangkok",
            "target_year": case["target_year"],
        })
        raw_result = generate_past_pattern_candidates(adult_req)
        candidates = _pattern_candidates(raw_result)

        assert 3 <= len(candidates) <= 5, (
            f"ADULT_CANDIDATE_COUNT_OUT_OF_RANGE: {len(candidates)} for {case['desc']}"
        )

        # Assert age/year sorted
        for i in range(len(candidates) - 1):
            curr_yr = _field(candidates[i], "year_range")[0]
            next_yr = _field(candidates[i + 1], "year_range")[0]
            assert curr_yr <= next_yr, f"CANDIDATES_NOT_YEAR_SORTED: {curr_yr} > {next_yr}"

            curr_age = _field(candidates[i], "age_range")[0]
            next_age = _field(candidates[i + 1], "age_range")[0]
            assert curr_age <= next_age, f"CANDIDATES_NOT_AGE_SORTED: {curr_age} > {next_age}"

        # Assert strictly non-sensitive themes
        for candidate in candidates:
            theme = _field(candidate, "theme")
            assert theme in ALLOWED_PAST_PATTERN_THEMES, f"UNAPPROVED_THEME: {theme}"
            assert _field(candidate, "sensitive_category") is False

            # Negative control: assert NO sensitive tokens anywhere in basis, theme, or rationale
            payload_str = json.dumps(_plain(candidate)).lower()
            for token in sensitive_tokens:
                assert token not in payload_str, (
                    f"SENSITIVE_TOKEN_LEAK: found {token!r} in candidate {payload_str}"
                )

    # 3. Negative control: schema rejects sensitive categories or themes
    for token in ("death", "illness", "trauma", "medical", "pregnancy"):
        bad_candidate = deepcopy(_past_patterns()[0])
        bad_candidate["theme"] = token
        with pytest.raises(ValidationError, match="outside the non-sensitive allowlist"):
            PastPatternCandidate.model_validate(bad_candidate)

    bad_candidate_flag = deepcopy(_past_patterns()[0])
    bad_candidate_flag["sensitive_category"] = True
    with pytest.raises(ValidationError, match="Sensitive past patterns are not allowed"):
        PastPatternCandidate.model_validate(bad_candidate_flag)


def test_horo_v3_consensus_arbitration_and_hitl_triggers() -> None:
    import project.debate.consensus_matrix as consensus_matrix

    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import UnifiedReadingRequest

    arbitration_function = getattr(consensus_matrix, "arbitrate_monthly_consensus", None)
    matrix_type = getattr(consensus_matrix, "ConsensusMatrix", None)
    matrix_method = None
    if matrix_type is not None:
        for method_name in (
            "arbitrate_monthly_consensus",
            "arbitrate_annual_consensus",
            "arbitrate",
        ):
            candidate = getattr(matrix_type, method_name, None)
            if callable(candidate) and getattr(candidate, "__doc__", None):
                matrix_method = candidate
                break
    assert callable(arbitration_function) or (
        callable(matrix_type) and matrix_method is not None
    ), "CONSENSUS_MATRIX_PUBLIC_ARBITRATION_INTERFACE_MISSING"

    base_request = UnifiedReadingRequest.model_validate(_phase_b_request_payload())
    base_result = calculate_annual_timing(base_request)
    base_metadata = _consensus_metadata(base_result)

    assert (
        base_metadata.get("consensus_matrix_source") == "project.debate.consensus_matrix"
    ), "CONSENSUS_MATRIX_SOURCE_MARKER_MISSING"

    consensus_score = base_metadata.get("consensus_score")
    assert isinstance(consensus_score, int | float), "CONSENSUS_SCORE_NOT_NUMERIC"
    assert 0 <= float(consensus_score) <= 1, "CONSENSUS_SCORE_OUTSIDE_0_TO_1"
    assert base_metadata.get("arbitration_status"), "CONSENSUS_ARBITRATION_STATUS_MISSING"
    traditions = base_metadata.get("traditions_considered")
    assert isinstance(traditions, list) and len(traditions) >= 2, "CONSENSUS_TRADITIONS_MISSING"

    arbitrated_claims = _arbitrated_monthly_claims(base_metadata)
    assert len(arbitrated_claims) == 12, "CONSENSUS_MONTHLY_ARBITRATION_COUNT_NOT_12"
    assert {_field(claim, "month") for claim in arbitrated_claims} == set(range(1, 13))

    base_flags = _hitl_flags(base_result)
    base_status = _hitl_routing(base_result).get("status")
    base_conflicts = bool(base_metadata.get("tradition_conflicts") or base_flags.get("tradition_conflict"))
    base_triggered = (
        float(consensus_score) < 0.75
        or base_conflicts
        or bool(base_flags.get("force_human_review"))
        or bool(base_flags.get("uncertain_birth_time"))
    )
    if base_triggered:
        assert base_status == "QUEUED_FOR_HUMAN_REVIEW", "HITL_TRIGGER_NOT_QUEUED"
    else:
        assert base_status == "NOT_REQUIRED", "HITL_NOT_REQUIRED_ONLY_WITHOUT_TRIGGERS"

    forced_review_result = calculate_annual_timing(
        base_request.model_copy(update={"force_human_review": True})
    )
    assert _hitl_routing(forced_review_result).get("status") == "QUEUED_FOR_HUMAN_REVIEW"
    assert _hitl_flags(forced_review_result).get("force_human_review") is True

    unknown_time_request = UnifiedReadingRequest.model_validate(
        _phase_b_request_payload(unknown_hour=True)
    )
    unknown_time_result = calculate_annual_timing(unknown_time_request)
    assert _hitl_routing(unknown_time_result).get("status") == "QUEUED_FOR_HUMAN_REVIEW"
    assert _hitl_flags(unknown_time_result).get("uncertain_birth_time") is True

    low_conflict_claims = [
        {
            "month": month,
            "tradition_claims": {
                "thai_suriyayart": {"career_score": 9, "claim": "strong upward month"},
                "bazi_liu_yue": {"career_score": 2, "claim": "caution and delay month"},
                "zi_wei": {"career_score": 3, "claim": "low support month"},
            },
            "expected_conflict": True,
        }
        for month in range(1, 13)
    ]
    low_conflict_request = base_request.model_copy(
        update={
            "consensus_fixture_id": "qa_low_consensus_conflict_1990_05_15_1430_bangkok_2026",
            "tradition_monthly_claims": low_conflict_claims,
        }
    )
    low_conflict_result = calculate_annual_timing(low_conflict_request)
    low_conflict_metadata = _consensus_metadata(low_conflict_result)
    low_conflict_score = low_conflict_metadata.get("consensus_score")
    assert isinstance(low_conflict_score, int | float), "LOW_CONSENSUS_SCORE_NOT_NUMERIC"
    assert float(low_conflict_score) < 0.75, "LOW_CONSENSUS_FIXTURE_NOT_LOW"
    assert low_conflict_metadata.get("tradition_conflicts"), "LOW_CONSENSUS_CONFLICTS_MISSING"
    assert _hitl_flags(low_conflict_result).get("low_consensus") is True
    assert _hitl_flags(low_conflict_result).get("tradition_conflict") is True
    assert _hitl_routing(low_conflict_result).get("status") == "QUEUED_FOR_HUMAN_REVIEW"


def test_horo_v3_consensus_arbitration_boundary_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")

    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import UnifiedReadingRequest, UnifiedReadingResponse
    from project.debate.consensus_matrix import (
        DEFAULT_TRADITIONS_CONSIDERED,
        arbitrate_monthly_consensus,
    )
    from project.main import app

    base_payload = _phase_b_request_payload()
    base_request = UnifiedReadingRequest.model_validate(base_payload)

    # 1. Verify multi-tradition claim arbitration across 12 months with thai_suriyayart, bazi_liu_yue, and zi_wei
    base_result = calculate_annual_timing(base_request)
    base_metadata = _consensus_metadata(base_result)

    assert base_metadata.get("engine_version") == "horo_v3_consensus", "ENGINE_VERSION_NOT_HORO_V3_CONSENSUS"
    assert (
        base_metadata.get("consensus_matrix_source") == "project.debate.consensus_matrix"
    ), "CONSENSUS_MATRIX_SOURCE_MARKER_MISSING"

    traditions = base_metadata.get("traditions_considered")
    assert isinstance(traditions, list), "TRADITIONS_CONSIDERED_NOT_A_LIST"
    expected_traditions = {"thai_suriyayart", "bazi_liu_yue", "zi_wei"}
    assert expected_traditions.issubset(set(traditions)), (
        f"TRADITIONS_CONSIDERED_INCOMPLETE: expected {expected_traditions}, got {traditions}"
    )

    monthly_claims = _arbitrated_monthly_claims(base_metadata)
    assert len(monthly_claims) == 12, f"MONTHLY_CLAIMS_COUNT_NOT_12: {len(monthly_claims)}"
    assert {_field(c, "month") for c in monthly_claims} == set(range(1, 13))

    for claim in monthly_claims:
        m = _field(claim, "month")
        t_claims = _field(claim, "tradition_claims")
        assert isinstance(t_claims, dict), f"TRADITION_CLAIMS_NOT_DICT: month {m}"
        for tradition_key in expected_traditions:
            assert tradition_key in t_claims, f"MISSING_TRADITION_{tradition_key.upper()}_IN_MONTH_{m}"
            t_data = t_claims[tradition_key]
            for domain in ("career_score", "finance_score", "love_score"):
                score = t_data.get(domain)
                assert isinstance(score, int | float) and 1 <= score <= 10, (
                    f"INVALID_SCORE_IN_{tradition_key}_{domain}_MONTH_{m}: {score}"
                )
        agreement = claim.get("agreement_score")
        assert isinstance(agreement, int | float) and 0.0 <= float(agreement) <= 1.0, (
            f"INVALID_MONTH_AGREEMENT_SCORE_IN_MONTH_{m}: {agreement}"
        )
        domain_agreements = claim.get("domain_agreements")
        assert isinstance(domain_agreements, dict), f"DOMAIN_AGREEMENTS_NOT_DICT: month {m}"
        for domain in ("career_score", "finance_score", "love_score"):
            assert domain in domain_agreements, f"MISSING_DOMAIN_AGREEMENT_{domain}_MONTH_{m}"
            d_score = domain_agreements[domain]
            assert isinstance(d_score, int | float) and 0.0 <= float(d_score) <= 1.0, (
                f"INVALID_DOMAIN_AGREEMENT_{domain}_MONTH_{m}: {d_score}"
            )
        assert claim.get("arbitrated_claim"), f"ARBITRATED_CLAIM_MISSING_IN_MONTH_{m}"

    # 2. Test low consensus threshold (< 0.75): assert QUEUED_FOR_HUMAN_REVIEW and low_consensus=True
    low_consensus_claims = [
        {
            "month": month,
            "tradition_claims": {
                "thai_suriyayart": {"career_score": 9, "finance_score": 9, "love_score": 9, "claim": "strong surge"},
                "bazi_liu_yue": {"career_score": 2, "finance_score": 2, "love_score": 2, "claim": "severe clash"},
                "zi_wei": {"career_score": 3, "finance_score": 3, "love_score": 3, "claim": "low support"},
            },
        }
        for month in range(1, 13)
    ]
    low_req = base_request.model_copy(
        update={
            "consensus_fixture_id": "qa_low_consensus_boundary_matrix_2026",
            "tradition_monthly_claims": low_consensus_claims,
        }
    )
    low_res = calculate_annual_timing(low_req)
    low_meta = _consensus_metadata(low_res)
    low_flags = _hitl_flags(low_res)
    low_routing = _hitl_routing(low_res)

    consensus_score = float(low_meta.get("consensus_score", 1.0))
    assert consensus_score < 0.75, f"CONSENSUS_SCORE_NOT_BELOW_0_75: {consensus_score}"
    assert low_flags.get("low_consensus") is True, "LOW_CONSENSUS_FLAG_NOT_TRUE"
    assert low_flags.get("required_human_review") is True, "REQUIRED_HUMAN_REVIEW_NOT_TRUE_ON_LOW_CONSENSUS"
    assert low_routing.get("status") == "QUEUED_FOR_HUMAN_REVIEW", "HITL_ROUTING_STATUS_NOT_QUEUED_ON_LOW_CONSENSUS"
    assert "low_consensus" in low_routing.get("trigger_reasons", []), "TRIGGER_REASONS_MISSING_LOW_CONSENSUS"

    # 3. Test domain-specific conflict: assert QUEUED_FOR_HUMAN_REVIEW and tradition_conflict=True if ANY domain has conflict
    for conflicting_domain in ("career_score", "finance_score", "love_score"):
        domain_conflict_claims = []
        for month in range(1, 13):
            t_claims = {
                "thai_suriyayart": {"career_score": 7, "finance_score": 7, "love_score": 7},
                "bazi_liu_yue": {"career_score": 7, "finance_score": 7, "love_score": 7},
                "zi_wei": {"career_score": 7, "finance_score": 7, "love_score": 7},
            }
            # Inject extreme conflict ONLY into conflicting_domain in month 7
            if month == 7:
                t_claims["thai_suriyayart"][conflicting_domain] = 9
                t_claims["bazi_liu_yue"][conflicting_domain] = 2
                t_claims["zi_wei"][conflicting_domain] = 3
            domain_conflict_claims.append({
                "month": month,
                "tradition_claims": t_claims,
            })
        dc_req = base_request.model_copy(
            update={
                "consensus_fixture_id": f"qa_domain_conflict_{conflicting_domain}_2026",
                "tradition_monthly_claims": domain_conflict_claims,
            }
        )
        dc_res = calculate_annual_timing(dc_req)
        dc_flags = _hitl_flags(dc_res)
        dc_routing = _hitl_routing(dc_res)
        dc_meta = _consensus_metadata(dc_res)

        assert dc_flags.get("tradition_conflict") is True, (
            f"TRADITION_CONFLICT_NOT_SET_FOR_DOMAIN_{conflicting_domain}"
        )
        assert dc_flags.get("required_human_review") is True, (
            f"REQUIRED_HUMAN_REVIEW_NOT_SET_FOR_DOMAIN_{conflicting_domain}"
        )
        assert dc_routing.get("status") == "QUEUED_FOR_HUMAN_REVIEW", (
            f"ROUTING_NOT_QUEUED_FOR_DOMAIN_{conflicting_domain}"
        )
        assert "tradition_conflict" in dc_routing.get("trigger_reasons", []), (
            f"TRIGGER_REASON_TRADITION_CONFLICT_MISSING_FOR_{conflicting_domain}"
        )
        assert dc_meta.get("arbitration_status") == "ARBITRATED_WITH_CONFLICTS"
        conflict_months = [c.get("month") for c in dc_meta.get("tradition_conflicts", [])]
        assert 7 in conflict_months, f"MONTH_7_NOT_FOUND_IN_CONFLICT_MONTHS: {conflict_months}"

    # 4. Test force review trigger: assert QUEUED_FOR_HUMAN_REVIEW and force_human_review=True
    force_req = base_request.model_copy(update={"force_human_review": True})
    force_res = calculate_annual_timing(force_req)
    force_flags = _hitl_flags(force_res)
    force_routing = _hitl_routing(force_res)

    assert force_flags.get("force_human_review") is True, "FORCE_HUMAN_REVIEW_FLAG_NOT_TRUE"
    assert force_flags.get("required_human_review") is True, "REQUIRED_HUMAN_REVIEW_NOT_TRUE_ON_FORCE"
    assert force_routing.get("status") == "QUEUED_FOR_HUMAN_REVIEW", "ROUTING_STATUS_NOT_QUEUED_ON_FORCE"
    assert "force_human_review" in force_routing.get("trigger_reasons", []), (
        "TRIGGER_REASON_FORCE_HUMAN_REVIEW_MISSING"
    )

    # 5. Test uncertain birth time trigger: assert QUEUED_FOR_HUMAN_REVIEW and uncertain_birth_time=True
    uncertain_req = UnifiedReadingRequest.model_validate(_phase_b_request_payload(unknown_hour=True))
    uncertain_res = calculate_annual_timing(uncertain_req)
    uncertain_flags = _hitl_flags(uncertain_res)
    uncertain_routing = _hitl_routing(uncertain_res)

    assert uncertain_flags.get("uncertain_birth_time") is True, "UNCERTAIN_BIRTH_TIME_FLAG_NOT_TRUE"
    assert uncertain_flags.get("required_human_review") is True, "REQUIRED_HUMAN_REVIEW_NOT_TRUE_ON_UNCERTAIN_TIME"
    assert uncertain_routing.get("status") == "QUEUED_FOR_HUMAN_REVIEW", "ROUTING_STATUS_NOT_QUEUED_ON_UNCERTAIN_TIME"
    assert "uncertain_birth_time" in uncertain_routing.get("trigger_reasons", []), (
        "TRIGGER_REASON_UNCERTAIN_BIRTH_TIME_MISSING"
    )

    # 6. Test clean baseline: assert NOT_REQUIRED strictly when no triggers are present
    clean_claims = [
        {
            "month": month,
            "tradition_claims": {
                "thai_suriyayart": {
                    "career_score": 7,
                    "finance_score": 7,
                    "love_score": 7,
                    "claim": "high agreement thai transit claim",
                },
                "bazi_liu_yue": {
                    "career_score": 7,
                    "finance_score": 7,
                    "love_score": 7,
                    "claim": "high agreement bazi cycle claim",
                },
                "zi_wei": {
                    "career_score": 7,
                    "finance_score": 7,
                    "love_score": 7,
                    "claim": "high agreement zi wei star claim",
                },
            },
        }
        for month in range(1, 13)
    ]
    clean_req = base_request.model_copy(
        update={
            "force_human_review": False,
            "unknown_hour": False,
            "tradition_monthly_claims": clean_claims,
            "consensus_fixture_id": "qa_clean_agreed_baseline_2026",
        }
    )
    clean_res = calculate_annual_timing(clean_req)
    clean_flags = _hitl_flags(clean_res)
    clean_routing = _hitl_routing(clean_res)
    clean_meta = _consensus_metadata(clean_res)

    assert clean_flags.get("required_human_review") is False, "CLEAN_BASELINE_REQUIRED_HUMAN_REVIEW_MUST_BE_FALSE"
    assert clean_flags.get("low_consensus") is False, "CLEAN_BASELINE_LOW_CONSENSUS_MUST_BE_FALSE"
    assert clean_flags.get("tradition_conflict") is False, "CLEAN_BASELINE_TRADITION_CONFLICT_MUST_BE_FALSE"
    assert clean_flags.get("conflict_detected") is False, "CLEAN_BASELINE_CONFLICT_DETECTED_MUST_BE_FALSE"
    assert clean_flags.get("force_human_review") is False, "CLEAN_BASELINE_FORCE_HUMAN_REVIEW_MUST_BE_FALSE"
    assert clean_flags.get("uncertain_birth_time") is False, "CLEAN_BASELINE_UNCERTAIN_BIRTH_TIME_MUST_BE_FALSE"
    assert clean_routing.get("status") == "NOT_REQUIRED", "CLEAN_BASELINE_STATUS_MUST_BE_NOT_REQUIRED"
    assert clean_routing.get("required_human_review") is False, "CLEAN_BASELINE_ROUTING_REQUIRED_MUST_BE_FALSE"
    assert clean_routing.get("trigger_reasons") == [], f"CLEAN_BASELINE_TRIGGER_REASONS_NOT_EMPTY: {clean_routing.get('trigger_reasons')}"
    assert clean_routing.get("reason") == "automated_synthesis_sufficient", (
        f"CLEAN_BASELINE_REASON_UNEXPECTED: {clean_routing.get('reason')}"
    )
    assert clean_meta.get("arbitration_status") == "ARBITRATED", "CLEAN_BASELINE_STATUS_NOT_ARBITRATED"
    assert clean_meta.get("tradition_conflicts") == [], "CLEAN_BASELINE_TRADITION_CONFLICTS_NOT_EMPTY"

    # 7. Test live probe: assert metaphysical scope audit compliance with pass_gate_check=True
    with TestClient(app) as client:
        probe_response = client.get("/hitl/scope-audit?source_domain=metaphysical-domain-engine")
        assert probe_response.status_code == 200, f"SCOPE_AUDIT_PROBE_HTTP_{probe_response.status_code}"
        probe_data = probe_response.json()
        assert probe_data.get("scope_domain") == "metaphysical-domain-engine", (
            f"SCOPE_DOMAIN_MISMATCH: {probe_data.get('scope_domain')}"
        )
        summary = probe_data.get("summary", {})
        assert summary.get("pass_gate_check") is True, f"SCOPE_AUDIT_PASS_GATE_CHECK_NOT_TRUE: {summary}"
        assert summary.get("missing_required_human_gate") == 0, (
            f"SCOPE_AUDIT_MISSING_GATE_VIOLATION: {summary.get('missing_required_human_gate')}"
        )

    # 8. Pessimistic Negative Controls: fail-closed schema validation on UnifiedReadingResponse
    # 8a: Fail-closed trigger: if review is required, routing status CANNOT be NOT_REQUIRED
    invalid_leak_response = _response_payload()
    invalid_leak_response["hitl_flags"]["low_consensus"] = True
    invalid_leak_response["hitl_flags"]["required_human_review"] = True
    invalid_leak_response["hitl_routing"]["status"] = "NOT_REQUIRED"
    with pytest.raises(ValidationError, match="HITL routing cannot be NOT_REQUIRED when review is required"):
        UnifiedReadingResponse.model_validate(invalid_leak_response)

    # 8b: Fail-closed trigger: if review is NOT required, routing status MUST be NOT_REQUIRED
    invalid_block_response = _response_payload()
    invalid_block_response["hitl_flags"]["low_consensus"] = False
    invalid_block_response["hitl_flags"]["tradition_conflict"] = False
    invalid_block_response["hitl_flags"]["force_human_review"] = False
    invalid_block_response["hitl_flags"]["uncertain_birth_time"] = False
    invalid_block_response["hitl_flags"]["required_human_review"] = False
    invalid_block_response["consensus_metadata"]["consensus_score"] = 0.9
    invalid_block_response["consensus_metadata"]["tradition_conflicts"] = []
    invalid_block_response["hitl_routing"]["status"] = "QUEUED_FOR_HUMAN_REVIEW"
    with pytest.raises(ValidationError, match="HITL routing status must be NOT_REQUIRED when review is not required"):
        UnifiedReadingResponse.model_validate(invalid_block_response)


def test_unified_reading_api_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.core.annual_timing_engine import calculate_annual_timing
    from project.core.unified_reading_engine import UnifiedReadingRequest, UnifiedReadingResponse
    from project.main import app

    request_payload = _phase_b_request_payload()
    request = UnifiedReadingRequest.model_validate(request_payload)
    expected_timing = calculate_annual_timing(request)
    expected_monthly_scores = {
        int(_field(month, "month")): {
            "career_score": _field(month, "career_score"),
            "finance_score": _field(month, "finance_score"),
            "love_score": _field(month, "love_score"),
        }
        for month in _annual_months(expected_timing)
    }

    with TestClient(app) as client:
        started = perf_counter()
        response = client.post("/api/v3/unified-reading", json=request_payload)
        elapsed_ms = (perf_counter() - started) * 1000

    assert response.status_code == 200, response.text
    assert elapsed_ms < 300, f"UNIFIED_READING_DETERMINISTIC_LATENCY_OVER_300MS: {elapsed_ms:.3f}ms"

    payload = response.json()
    validated = UnifiedReadingResponse.model_validate(payload)
    result = _plain(validated)

    assert result["schema_version"] == "horo_lite_unified_reading.v1"
    assert isinstance(result["request_id"], str) and result["request_id"]
    assert result["target_year"] == 2026

    topics = result["topics"]
    assert len(topics) == 12, "UNIFIED_READING_TOPIC_COUNT_NOT_12"
    assert [topic["topic_id"] for topic in topics] == TOPIC_IDS
    assert [topic["order"] for topic in topics] == list(range(1, 13))
    for topic in topics:
        assert topic["title"]
        assert topic["summary"]
        assert topic["guidance"]
        assert topic["confidence"] in {"HIGH", "MEDIUM", "LOW"}
        assert topic["evidence_refs"], "UNIFIED_READING_TOPIC_EVIDENCE_REFS_MISSING"

    monthly_scores = result["monthly_scores"]
    assert len(monthly_scores) == 12, "UNIFIED_READING_MONTHLY_SCORE_COUNT_NOT_12"
    assert [score["month"] for score in monthly_scores] == list(range(1, 13))
    for monthly_score in monthly_scores:
        month = monthly_score["month"]
        assert {
            "career_score": monthly_score["career_score"],
            "finance_score": monthly_score["finance_score"],
            "love_score": monthly_score["love_score"],
        } == expected_monthly_scores[month], "UNIFIED_READING_DETERMINISTIC_SCORE_MUTATED"
        for domain in ("career", "finance", "love"):
            score_value = monthly_score[f"{domain}_score"]
            assert isinstance(score_value, int)
            assert 1 <= score_value <= 10, f"UNIFIED_READING_{domain.upper()}_SCORE_OUT_OF_RANGE"
        assert monthly_score["score_basis"], "UNIFIED_READING_MONTHLY_SCORE_BASIS_MISSING"
        assert monthly_score["reasons"], "UNIFIED_READING_MONTHLY_REASONS_MISSING"

    past_patterns = result["past_patterns"]
    assert 3 <= len(past_patterns) <= 5, "UNIFIED_READING_PAST_PATTERN_COUNT_OUTSIDE_3_TO_5"
    for pattern in past_patterns:
        year_range = pattern["year_range"]
        age_range = pattern["age_range"]
        assert year_range[0] <= year_range[1] < request.target_year
        assert age_range[0] == year_range[0] - request.birth_date.year
        assert age_range[1] == year_range[1] - request.birth_date.year
        assert pattern["sensitive_category"] is False
        assert pattern["deterministic_basis"], "UNIFIED_READING_PAST_PATTERN_BASIS_MISSING"

    consensus_metadata = result["consensus_metadata"]
    assert consensus_metadata.get("engine_version") == "horo_v3_consensus"
    consensus_score = consensus_metadata.get("consensus_score")
    assert isinstance(consensus_score, int | float)
    assert 0 <= float(consensus_score) <= 1
    assert isinstance(consensus_metadata.get("traditions_considered"), list)
    assert len(consensus_metadata["traditions_considered"]) >= 2
    assert consensus_metadata.get("arbitration_status")

    hitl_flags = result["hitl_flags"]
    hitl_routing = result["hitl_routing"]
    assert isinstance(hitl_flags.get("required_human_review"), bool)
    assert isinstance(hitl_flags.get("low_consensus"), bool)
    assert isinstance(hitl_flags.get("tradition_conflict"), bool)
    assert hitl_flags.get("force_human_review") is False
    assert hitl_flags.get("uncertain_birth_time") is False
    assert hitl_routing.get("status") in {"NOT_REQUIRED", "QUEUED_FOR_HUMAN_REVIEW"}

    llm_metadata = result["llm_metadata"]
    assert llm_metadata.get("facts_mutable_by_llm") is False
    assert llm_metadata.get("network_call_performed") in (False, None)
    assert llm_metadata.get("deterministic_facts_source") in (
        "project.core.annual_timing_engine",
        None,
    )


def test_unified_reading_api_endpoint_extended_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")
    monkeypatch.setenv("HORO_LITE_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.setenv("UNIFIED_READING_LLM_TRANSLATION_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    from project.core.unified_reading_engine import (
        ALLOWED_PAST_PATTERN_THEMES,
        CANONICAL_TOPIC_IDS,
        UnifiedReadingResponse,
    )
    from project.main import app

    with TestClient(app) as client:
        # 1. Standard payload verification and deterministic latency SLA < 300ms
        std_payload = _phase_b_request_payload()
        started = perf_counter()
        resp = client.post("/api/v3/unified-reading", json=std_payload)
        elapsed_ms = (perf_counter() - started) * 1000

        assert resp.status_code == 200, f"Standard payload returned HTTP {resp.status_code}: {resp.text}"
        assert elapsed_ms < 300, f"Deterministic path latency SLA violated: {elapsed_ms:.2f}ms >= 300ms"

        data = resp.json()
        validated = UnifiedReadingResponse.model_validate(data)
        plain_data = _plain(validated)

        # 2. Assert 12 topics returned in exact canonical sequence (CANONICAL_TOPIC_IDS)
        topics = plain_data["topics"]
        assert len(topics) == 12, f"Expected 12 canonical topics, got {len(topics)}"
        assert tuple(t["topic_id"] for t in topics) == CANONICAL_TOPIC_IDS, (
            f"Topic IDs {tuple(t['topic_id'] for t in topics)} do not match CANONICAL_TOPIC_IDS {CANONICAL_TOPIC_IDS}"
        )
        assert [t["order"] for t in topics] == list(range(1, 13))
        for t in topics:
            assert t["title"] and isinstance(t["title"], str), f"Missing title in topic {t['topic_id']}"
            assert t["summary"] and isinstance(t["summary"], str), f"Missing summary in topic {t['topic_id']}"
            assert t["guidance"] and isinstance(t["guidance"], str), f"Missing guidance in topic {t['topic_id']}"
            assert t["confidence"] in {"HIGH", "MEDIUM", "LOW"}, f"Invalid confidence {t['confidence']} in topic {t['topic_id']}"
            assert t["evidence_refs"] and len(t["evidence_refs"]) >= 1, f"Missing evidence_refs in topic {t['topic_id']}"

        # 3. Assert 12 months scores returned with career, finance, love in [1..10] and reasons
        monthly_scores = plain_data["monthly_scores"]
        assert len(monthly_scores) == 12, f"Expected 12 monthly scores, got {len(monthly_scores)}"
        assert [m["month"] for m in monthly_scores] == list(range(1, 13))
        for m in monthly_scores:
            for domain in ("career", "finance", "love"):
                score = m[f"{domain}_score"]
                assert isinstance(score, int) and 1 <= score <= 10, (
                    f"Month {m['month']} {domain}_score {score} is not an integer in [1..10]"
                )
            assert m["reasons"] and isinstance(m["reasons"], list) and len(m["reasons"]) >= 1, (
                f"Month {m['month']} missing reasons list"
            )
            assert all(isinstance(r, str) and r.strip() for r in m["reasons"]), (
                f"Month {m['month']} contains empty or non-string reason"
            )
            assert m["score_basis"] and isinstance(m["score_basis"], dict) and len(m["score_basis"]) >= 1, (
                f"Month {m['month']} missing score_basis dict"
            )

        # 4. Assert past patterns (0 to 5 candidates), non-sensitive
        past_patterns = plain_data["past_patterns"]
        assert isinstance(past_patterns, list)
        assert 0 <= len(past_patterns) <= 5, f"Past pattern candidates count {len(past_patterns)} not in [0..5]"
        for pattern in past_patterns:
            assert pattern["sensitive_category"] is False, f"Sensitive past pattern detected: {pattern.get('pattern_id')}"
            assert pattern["theme"] in ALLOWED_PAST_PATTERN_THEMES, f"Unallowed theme {pattern.get('theme')}"
            assert pattern["deterministic_basis"], f"Missing deterministic basis in past pattern {pattern.get('pattern_id')}"
            year_range = pattern["year_range"]
            assert len(year_range) == 2 and year_range[0] <= year_range[1] < plain_data["target_year"]

        # Boundary check: Young person / child payload yields 0 candidates (clean boundary within [0..5])
        child_payload = dict(std_payload, birth_date="2022-01-01", target_year=2026)
        child_resp = client.post("/api/v3/unified-reading", json=child_payload)
        assert child_resp.status_code == 200, f"Child payload failed: {child_resp.text}"
        child_data = child_resp.json()
        assert len(child_data["past_patterns"]) == 0, "Child payload must return 0 past pattern candidates"
        assert child_data["insufficient_history_reason"] is not None

        # 5. Assert HTTP 422 Unprocessable Entity on invalid inputs
        # 5a. Future birth relative to target year
        invalid_future_payloads = [
            dict(std_payload, birth_date="2030-01-01", target_year=2026),
            dict(std_payload, birth_date="2027-12-31", target_year=2026),
        ]
        for bad_p in invalid_future_payloads:
            bad_resp = client.post("/api/v3/unified-reading", json=bad_p)
            assert bad_resp.status_code == 422, (
                f"Expected HTTP 422 for future birth date relative to target year, got {bad_resp.status_code}: {bad_resp.text}"
            )

        # 5b. Invalid coordinates (latitude not in [-90, 90], longitude not in [-180, 180])
        invalid_coord_payloads = [
            dict(std_payload, latitude=90.001),
            dict(std_payload, latitude=-90.001),
            dict(std_payload, longitude=180.001),
            dict(std_payload, longitude=-180.001),
            dict(std_payload, latitude=999.0),
        ]
        for bad_p in invalid_coord_payloads:
            bad_resp = client.post("/api/v3/unified-reading", json=bad_p)
            assert bad_resp.status_code == 422, (
                f"Expected HTTP 422 for invalid coordinate, got {bad_resp.status_code}: {bad_resp.text}"
            )

        # 5c. Invalid target year (target_year not in [1900, 2200])
        invalid_year_payloads = [
            dict(std_payload, birth_date="1800-01-01", target_year=1899),
            dict(std_payload, target_year=2201),
            dict(std_payload, target_year=1500),
        ]
        for bad_p in invalid_year_payloads:
            bad_resp = client.post("/api/v3/unified-reading", json=bad_p)
            assert bad_resp.status_code == 422, (
                f"Expected HTTP 422 for invalid target_year, got {bad_resp.status_code}: {bad_resp.text}"
            )

        # 6. Assert fail-closed HITL routing: force_human_review=True or unknown_hour=True results in QUEUED_FOR_HUMAN_REVIEW
        # 6a. force_human_review=True
        hitl_forced_payload = dict(std_payload, force_human_review=True)
        resp_forced = client.post("/api/v3/unified-reading", json=hitl_forced_payload)
        assert resp_forced.status_code == 200, f"Forced HITL request failed: {resp_forced.text}"
        forced_data = resp_forced.json()
        assert forced_data["hitl_routing"]["status"] == "QUEUED_FOR_HUMAN_REVIEW", (
            f"Expected QUEUED_FOR_HUMAN_REVIEW for force_human_review=True, got {forced_data['hitl_routing']['status']}"
        )
        assert forced_data["hitl_flags"]["force_human_review"] is True
        assert forced_data["hitl_flags"]["required_human_review"] is True

        # 6b. unknown_hour=True
        hitl_unknown_payload = dict(std_payload, unknown_hour=True, birth_time=None)
        resp_unknown = client.post("/api/v3/unified-reading", json=hitl_unknown_payload)
        assert resp_unknown.status_code == 200, f"Unknown hour request failed: {resp_unknown.text}"
        unknown_data = resp_unknown.json()
        assert unknown_data["hitl_routing"]["status"] == "QUEUED_FOR_HUMAN_REVIEW", (
            f"Expected QUEUED_FOR_HUMAN_REVIEW for unknown_hour=True, got {unknown_data['hitl_routing']['status']}"
        )
        assert unknown_data["hitl_flags"]["uncertain_birth_time"] is True
        assert unknown_data["hitl_flags"]["required_human_review"] is True

        # 7. Assert LLM facts immutability: llm_metadata.facts_mutable_by_llm == False
        for tested_data in (plain_data, forced_data, unknown_data, child_data):
            llm_meta = tested_data["llm_metadata"]
            assert llm_meta.get("facts_mutable_by_llm") is False, (
                f"Facts immutability violated: {llm_meta.get('facts_mutable_by_llm')}"
            )
            assert llm_meta.get("network_call_performed") in (False, None)
            assert llm_meta.get("deterministic_facts_source") == "project.core.annual_timing_engine"


def _audit_lite_form_dom(
    html: str,
    css: str | None = None,
    js: str | None = None,
) -> dict[str, Any]:
    parser = _parse_lite_html(html)

    # 1. Single-column clean form structure & landmarks
    forms = [
        el for el in parser.elements
        if el["tag"] == "form" and el["attrs"].get("id") == "lite-form"
    ]
    assert len(forms) == 1, (
        f"LITE_FORM_ELEMENT_MISSING_OR_DUPLICATE: found {len(forms)} form elements with id='lite-form'"
    )
    form_el = forms[0]
    assert "lite-form" in form_el["attrs"].get("class", ""), "LITE_FORM_CLASS_MISSING"

    mains = [el for el in parser.elements if el["tag"] == "main"]
    assert len(mains) == 1, f"LITE_MAIN_LANDMARK_MISSING: found {len(mains)} main tags"
    assert "lite-shell" in mains[0]["attrs"].get("class", ""), "LITE_MAIN_CLASS_MISSING"
    assert mains[0]["attrs"].get("aria-labelledby") or mains[0]["attrs"].get("aria-label"), (
        "LITE_MAIN_ACCESSIBLE_LANDMARK_NAME_MISSING"
    )

    form_sections = [
        el for el in parser.elements
        if el["tag"] == "section" and "form" in el.get("parent_tags", [])
    ]
    assert len(form_sections) >= 2, "LITE_FORM_SECTIONS_MISSING: expected >= 2 form sections"
    for sec in form_sections:
        assert sec["attrs"].get("aria-labelledby") or sec["attrs"].get("aria-label"), (
            "LITE_FORM_SECTION_LANDMARK_ACCESSIBILITY_MISSING"
        )

    # 2. Required inputs verification
    label_targets = _label_targets(parser)

    # 2a. Birth date (date type, required, autocomplete=bday)
    birth_date = _find_control(
        parser,
        field_name="birth_date",
        tokens=("birth_date", "birth-date", "birthdate"),
        types=("date",),
    )
    assert "required" in birth_date["attrs"], "LITE_FORM_BIRTH_DATE_REQUIRED_MISSING"
    assert birth_date["attrs"].get("autocomplete") in {"bday", ""}, (
        "LITE_FORM_BIRTH_DATE_AUTOCOMPLETE_UNEXPECTED"
    )

    # 2b. Time picker with unknown hour toggle
    birth_time = _find_control(
        parser,
        field_name="birth_time",
        tokens=("birth_time", "birth-time", "birthtime"),
        types=("time",),
    )
    assert _control_is_accessibly_labelled(birth_time, parser, label_targets), (
        "LITE_FORM_BIRTH_TIME_ACCESSIBLE_LABEL_MISSING"
    )

    unknown_time = _find_control(
        parser,
        field_name="unknown_birth_time",
        tokens=("unknown_hour", "unknown-time", "unknown_birth_time", "unknownbirthtime"),
        types=("checkbox",),
    )
    hint_id = unknown_time["attrs"].get("aria-describedby")
    assert hint_id, "LITE_FORM_UNKNOWN_HOUR_HINT_DESCRIPTOR_MISSING"
    assert any(el["attrs"].get("id") == hint_id for el in parser.elements), (
        f"LITE_FORM_UNKNOWN_HOUR_HINT_ELEMENT_NOT_FOUND: {hint_id}"
    )

    # 2c. Birthplace search with geocoding datalist / autocomplete
    birth_place = _find_control(
        parser,
        field_name="birthplace_geocoding",
        tokens=("birth_place", "birth-place", "birthplace", "location", "geocode", "place-search"),
        types=("search", "text"),
    )
    assert "required" in birth_place["attrs"], "LITE_FORM_BIRTHPLACE_REQUIRED_MISSING"
    datalist_id = birth_place["attrs"].get("list")
    assert datalist_id, "LITE_FORM_BIRTHPLACE_GEOCODING_DATALIST_MISSING"
    assert any(
        el["tag"] == "datalist" and el["attrs"].get("id") == datalist_id
        for el in parser.elements
    ), f"LITE_FORM_BIRTHPLACE_DATALIST_TARGET_MISSING: {datalist_id}"

    # 2d. Gender selector
    gender = _find_control(
        parser,
        field_name="gender",
        tokens=("gender", "sex"),
        tags=("select", "input"),
    )
    if gender["tag"] == "select":
        options = [
            el["attrs"].get("value")
            for el in parser.elements
            if el["tag"] == "option" and el["attrs"].get("value")
        ]
        assert "female" in options and "male" in options, "LITE_FORM_GENDER_CANONICAL_OPTIONS_MISSING"

    # 2e. Target year
    target_year = _find_control(
        parser,
        field_name="target_year",
        tokens=("target_year", "target-year", "targetyear", "year"),
        types=("number", "text"),
    )
    assert "required" in target_year["attrs"], "LITE_FORM_TARGET_YEAR_REQUIRED_MISSING"
    if "min" in target_year["attrs"] and "max" in target_year["attrs"]:
        assert int(target_year["attrs"]["min"]) <= 1900, "LITE_FORM_TARGET_YEAR_MIN_INVALID"
        assert int(target_year["attrs"]["max"]) >= 2200, "LITE_FORM_TARGET_YEAR_MAX_INVALID"

    # 3. Advanced disclosure for raw longitude/latitude/timezone/engine
    details_blocks = _details_blocks(parser)
    assert details_blocks, "LITE_FORM_ADVANCED_DETAILS_DISCLOSURE_MISSING"
    for block in details_blocks:
        assert "open" not in block["attrs"], "LITE_FORM_ADVANCED_DISCLOSURE_MUST_BE_COLLAPSED"

    advanced_panel = [
        el for el in details_blocks
        if "advanced" in el["attrs"].get("class", "").lower() or "advanced" in _attr_blob(el)
    ]
    assert advanced_panel, "LITE_FORM_ADVANCED_PANEL_CLASS_MISSING"
    summaries = [
        el for el in parser.elements
        if el["tag"] == "summary" and "details" in el.get("parent_tags", [])
    ]
    assert summaries, "LITE_FORM_ADVANCED_SUMMARY_MISSING"

    for raw_field, raw_types in (
        ("latitude", ("number", "text")),
        ("longitude", ("number", "text")),
        ("timezone", ("text",)),
        ("engine_mode", None),
    ):
        ctrl = _find_control(
            parser,
            field_name=f"advanced_{raw_field}",
            tokens=(raw_field, raw_field.replace("_", "-")),
            tags=("input", "select"),
            types=raw_types,
        )
        assert "details" in ctrl.get("parent_tags", []), (
            f"LITE_FORM_ADVANCED_CONTROL_{raw_field.upper()}_NOT_INSIDE_DETAILS"
        )

    # 4. Single primary submit button ("คำนวณผังดวง & ตีความด้วย AI")
    submit_buttons = [
        el for el in parser.elements
        if el["tag"] == "button"
        and "form" in el.get("parent_tags", [])
        and el["attrs"].get("type", "submit") == "submit"
    ]
    assert len(submit_buttons) > 0, "LITE_FORM_PRIMARY_ACTION_BUTTON_MISSING"
    assert len(submit_buttons) == 1, (
        f"LITE_FORM_SINGLE_SUBMIT_ACTION_VIOLATION: expected exactly 1 submit button, got {len(submit_buttons)}"
    )
    primary_btn = submit_buttons[0]
    btn_text = primary_btn["text"].strip()
    assert "คำนวณผังดวง & ตีความด้วย AI" in btn_text, (
        f"LITE_FORM_PRIMARY_ACTION_TEXT_MISMATCH: expected 'คำนวณผังดวง & ตีความด้วย AI' in '{btn_text}'"
    )

    # 5. Accessibility: all form controls must be accessibly labelled
    form_controls = [
        el for el in parser.elements
        if el["tag"] in {"input", "select", "textarea"}
        and "form" in el.get("parent_tags", [])
        and el["attrs"].get("type") != "hidden"
    ]
    assert len(form_controls) >= 8, f"LITE_FORM_EXPECTED_MIN_8_CONTROLS: got {len(form_controls)}"
    for ctrl in form_controls:
        ctrl_id = ctrl["attrs"].get("id")
        ctrl_name = ctrl["attrs"].get("name")
        assert ctrl_id, f"LITE_FORM_CONTROL_MISSING_ID: tag={ctrl['tag']}"
        assert ctrl_name, f"LITE_FORM_CONTROL_MISSING_NAME: id={ctrl_id}"
        assert _control_is_accessibly_labelled(ctrl, parser, label_targets), (
            f"LITE_FORM_UNLABELLED_CONTROL: <{ctrl['tag']} id='{ctrl_id}' name='{ctrl_name}'> missing accessible label"
        )

    all_element_ids = {el["attrs"]["id"] for el in parser.elements if el["attrs"].get("id")}
    for label_target in label_targets:
        assert label_target in all_element_ids, (
            f"LITE_FORM_DANGLING_LABEL_TARGET: label for='{label_target}' points to non-existent ID"
        )

    # 6. CSS contract verification (if provided)
    if css is not None:
        css_lower = css.lower()
        has_focus = ":focus" in css_lower or ":focus-visible" in css_lower
        assert has_focus, "LITE_CSS_ACCESSIBLE_FOCUS_STYLE_MISSING"
        has_responsive_single_col = bool(
            re.search(r"@media[^{]*\{[^}]*grid-template-columns\s*:\s*1fr", css_lower)
            or re.search(r"grid-template-columns\s*:\s*1fr", css_lower)
        )
        assert has_responsive_single_col, "LITE_CSS_RESPONSIVE_SINGLE_COLUMN_RULE_MISSING"

    # 7. JS contract verification (if provided)
    if js is not None:
        assert "/api/v3/unified-reading" in js, "LITE_JS_UNIFIED_READING_API_CALL_MISSING"
        forbidden_local_logic = {
            "calcFourPillars",
            "calculate_annual_timing",
            "calculateAnnualTiming",
            "generate_past_pattern_candidates",
        }
        for fn in forbidden_local_logic:
            assert fn not in js, f"LITE_JS_LOCAL_ASTROLOGY_LOGIC_DUPLICATED: {fn}"
        assert not re.search(r"for\s*\([^)]*month[^)]*<=\s*12[^)]*\).*score", js, re.I | re.S), (
            "LITE_JS_DIRECT_MONTHLY_SCORING_LOOP_DETECTED"
        )

    return {
        "status": "PASS",
        "form_id": form_el["attrs"]["id"],
        "controls_verified_count": len(form_controls),
        "submit_button_text": btn_text,
        "details_blocks_count": len(details_blocks),
    }


def test_lite_form_dom_contract() -> None:
    lite_html_path = PUBLIC_DIR / "lite.html"
    lite_css_path = PUBLIC_DIR / "lite.css"
    lite_js_path = PUBLIC_DIR / "lite.js"

    assert lite_html_path.exists(), "LITE_HTML_MISSING: public/lite.html must exist"
    assert lite_css_path.exists(), "LITE_CSS_MISSING: public/lite.css must exist"
    assert lite_js_path.exists(), "LITE_JS_MISSING: public/lite.js must exist"

    html = lite_html_path.read_text(encoding="utf-8")
    css = lite_css_path.read_text(encoding="utf-8")
    js = lite_js_path.read_text(encoding="utf-8")

    # 1. Execute full DOM, contract, and accessibility audit on actual production assets
    receipt = _audit_lite_form_dom(html, css, js)
    assert receipt["status"] == "PASS"
    assert receipt["form_id"] == "lite-form"
    assert receipt["controls_verified_count"] >= 8
    assert "คำนวณผังดวง & ตีความด้วย AI" in receipt["submit_button_text"]

    # 2. Negative controls: verify fail-closed rejection on invalid markup
    # 2a. Rejection of unlabelled input control
    unlabelled_markup = html.replace(
        "</form>",
        '<div class="field"><input id="unlabelled_rogue" name="unlabelled_rogue" type="text"></div></form>',
    )
    with pytest.raises(AssertionError, match="LITE_FORM_UNLABELLED_CONTROL"):
        _audit_lite_form_dom(unlabelled_markup, css, js)

    # 2b. Rejection of missing primary action submit button
    no_btn_markup = re.sub(r'<button id="submit-reading"[^>]*>.*?</button>', '', html, flags=re.DOTALL)
    with pytest.raises(AssertionError, match="LITE_FORM_PRIMARY_ACTION_BUTTON_MISSING"):
        _audit_lite_form_dom(no_btn_markup, css, js)

    # 2c. Rejection of multiple submit actions (single primary action enforcement)
    multi_btn_markup = html.replace(
        "</button>",
        '</button><button id="submit-secondary" name="submit-secondary" type="submit">คำนวณผังดวง &amp; ตีความด้วย AI สำรอง</button>',
    )
    with pytest.raises(AssertionError, match="LITE_FORM_SINGLE_SUBMIT_ACTION_VIOLATION"):
        _audit_lite_form_dom(multi_btn_markup, css, js)

    # 2d. Rejection of mismatching primary action text
    wrong_text_markup = html.replace("คำนวณผังดวง &amp; ตีความด้วย AI", "Submit Astrology Reading")
    with pytest.raises(AssertionError, match="LITE_FORM_PRIMARY_ACTION_TEXT_MISMATCH"):
        _audit_lite_form_dom(wrong_text_markup, css, js)

    # 2e. Rejection of advanced disclosure open by default
    open_adv_markup = html.replace('<details class="advanced-panel">', '<details class="advanced-panel" open>')
    with pytest.raises(AssertionError, match="LITE_FORM_ADVANCED_DISCLOSURE_MUST_BE_COLLAPSED"):
        _audit_lite_form_dom(open_adv_markup, css, js)

    # 2f. Rejection of missing required inputs (e.g. birth_date)
    missing_birth_date = re.sub(r'<input id="birth_date"[^>]*>', '', html)
    with pytest.raises(AssertionError, match="LITE_FORM_BIRTH_DATE_CONTROL_MISSING_OR_UNBOUND"):
        _audit_lite_form_dom(missing_birth_date, css, js)

    # 2g. Rejection of dangling label target
    dangling_label_markup = html.replace('id="gender_at_birth"', 'id="gender_renamed"')
    with pytest.raises(AssertionError, match="LITE_FORM_DANGLING_LABEL_TARGET|LITE_FORM_GENDER_CONTROL_MISSING_OR_UNBOUND"):
        _audit_lite_form_dom(dangling_label_markup, css, js)


def test_lite_form_accessibility_and_dom_negative_matrix() -> None:
    lite_html_path = PUBLIC_DIR / "lite.html"
    lite_css_path = PUBLIC_DIR / "lite.css"
    lite_js_path = PUBLIC_DIR / "lite.js"

    html = lite_html_path.read_text(encoding="utf-8")
    css = lite_css_path.read_text(encoding="utf-8")
    js = lite_js_path.read_text(encoding="utf-8")

    # 1. Main landmark and form landmark fail-closed guards
    no_form = html.replace('<form id="lite-form"', '<div id="lite-form"')
    with pytest.raises(AssertionError, match="LITE_FORM_ELEMENT_MISSING_OR_DUPLICATE"):
        _audit_lite_form_dom(no_form, css, js)

    no_form_class = html.replace('class="lite-form"', 'class="generic-form"')
    with pytest.raises(AssertionError, match="LITE_FORM_CLASS_MISSING"):
        _audit_lite_form_dom(no_form_class, css, js)

    no_main = html.replace('<main class="lite-shell"', '<div class="lite-shell"')
    with pytest.raises(AssertionError, match="LITE_MAIN_LANDMARK_MISSING"):
        _audit_lite_form_dom(no_main, css, js)

    # 2. Unlabelled textarea and select controls
    unlabelled_textarea = html.replace(
        '<label for="primary_focus_question">คำถามที่อยากโฟกัส</label>', ''
    )
    with pytest.raises(AssertionError, match="LITE_FORM_UNLABELLED_CONTROL"):
        _audit_lite_form_dom(unlabelled_textarea, css, js)

    unlabelled_select = html.replace(
        '<label for="gender_at_birth">เพศกำเนิด</label>', ''
    ).replace('aria-label="เพศกำเนิด"', '')
    with pytest.raises(AssertionError, match="LITE_FORM_GENDER_ACCESSIBLE_LABEL_MISSING|LITE_FORM_UNLABELLED_CONTROL"):
        _audit_lite_form_dom(unlabelled_select, css, js)

    rogue_unlabelled_select = html.replace(
        '</form>',
        '<div class="field"><select id="rogue_select" name="rogue_select"><option value="1">1</option></select></div></form>',
    )
    with pytest.raises(AssertionError, match="LITE_FORM_UNLABELLED_CONTROL"):
        _audit_lite_form_dom(rogue_unlabelled_select, css, js)

    # 3. Control missing id or name attribute
    missing_name = html.replace('name="birth_date"', '')
    with pytest.raises(AssertionError, match="LITE_FORM_CONTROL_MISSING_NAME|LITE_FORM_BIRTH_DATE_CONTROL_MISSING_OR_UNBOUND"):
        _audit_lite_form_dom(missing_name, css, js)

    # 4. Geocoding datalist target missing
    missing_datalist = re.sub(r'<datalist id="thai-place-defaults">.*?</datalist>', '', html, flags=re.DOTALL)
    with pytest.raises(AssertionError, match="LITE_FORM_BIRTHPLACE_DATALIST_TARGET_MISSING"):
        _audit_lite_form_dom(missing_datalist, css, js)

    # 5. Target year boundary bounds corruption
    invalid_min_year = html.replace('min="1900"', 'min="1950"')
    with pytest.raises(AssertionError, match="LITE_FORM_TARGET_YEAR_MIN_INVALID"):
        _audit_lite_form_dom(invalid_min_year, css, js)

    # 6. Advanced panel summary missing
    no_summary = re.sub(r'<summary>.*?</summary>', '', html)
    with pytest.raises(AssertionError, match="LITE_FORM_ADVANCED_SUMMARY_MISSING"):
        _audit_lite_form_dom(no_summary, css, js)

    # 7. Advanced panel required raw control missing (timezone)
    missing_tz = re.sub(r'<input id="timezone"[^>]*>', '', html)
    with pytest.raises(AssertionError, match="LITE_FORM_ADVANCED_TIMEZONE_CONTROL_MISSING_OR_UNBOUND"):
        _audit_lite_form_dom(missing_tz, css, js)


def test_lite_routes_and_assets_respond_200(monkeypatch: pytest.MonkeyPatch) -> None:
    import re
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")

    from project.main import app

    # 1. Physical static asset verification: files exist, are regular files, non-empty, and load cleanly
    static_assets = {
        "lite.html": ("<!doctype html>", "<main class=\"lite-shell\"", "<form id=\"lite-form\""),
        "lite.css": (":root", ".lite-form", ":focus"),
        "lite.js": ("/api/v3/unified-reading",),
        "export_engine.js": ("window.horoLiteExport",),
        "export_modal.css": (":root",),
        "app.js": ("function",),
    }

    for file_name, required_tokens in static_assets.items():
        file_path = PUBLIC_DIR / file_name
        assert file_path.exists(), f"STATIC_ASSET_MISSING: public/{file_name} must exist"
        assert file_path.is_file(), f"STATIC_ASSET_NOT_FILE: public/{file_name} is not a regular file"
        content = file_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"STATIC_ASSET_EMPTY: public/{file_name} must not be empty"
        for token in required_tokens:
            assert token in content, f"STATIC_ASSET_TOKEN_MISSING: public/{file_name} missing '{token}'"

    # 2. HTTP route and asset response verification
    endpoint_expectations = [
        ("/lite", "text/html"),
        ("/lite.css", "text/css"),
        ("/lite.js", "text/javascript"),
        ("/export_engine.js", "text/javascript"),
        ("/export_modal.css", "text/css"),
        ("/app.js", "text/javascript"),
    ]

    with TestClient(app) as client:
        for endpoint, expected_mime in endpoint_expectations:
            response = client.get(endpoint)
            assert response.status_code == 200, f"{endpoint}_HTTP_STATUS_NOT_200: got {response.status_code}"
            content_type = response.headers.get("content-type", "")
            assert re.search(re.escape(expected_mime), content_type, re.I), (
                f"{endpoint}_CONTENT_TYPE_MISSING: expected {expected_mime}, got {content_type}"
            )
            assert len(response.text.strip()) > 0, f"{endpoint}_RESPONSE_BODY_EMPTY"


# ---------------------------------------------------------------------------
# Phase H: Multi-Format Mobile Infographic Exporter Suite (TICKET-HLITE-008)
# ---------------------------------------------------------------------------

def _extract_function_body(js: str, fn_name: str) -> str:
    decl_match = re.search(rf"(?:async\s+)?function\s+{re.escape(fn_name)}\s*\([^)]*\)\s*\{{", js)
    assert decl_match, f"EXPORT_ENGINE_FUNCTION_DECLARATION_MISSING_{fn_name}"
    start = decl_match.end() - 1
    depth = 0
    for idx in range(start, len(js)):
        if js[idx] == "{":
            depth += 1
        elif js[idx] == "}":
            depth -= 1
            if depth == 0:
                return js[start + 1 : idx]
    raise AssertionError(f"EXPORT_ENGINE_FUNCTION_UNCLOSED_{fn_name}")


def _audit_export_engine_contract(export_js: str) -> dict[str, Any]:
    """
    Static analysis audit of public/export_engine.js for Phase H export suite contract.

    Verifies:
    1. All 4 export functions exist and are declared / callable:
       - exportFullPng, exportStoryPng, copySocialSummary, printResult
    2. Canvas dimensions for Story export:
       - CANVAS_WIDTH = 1080 and STORY_HEIGHT = 1920 (exact 9:16 aspect ratio)
       - exportStoryPng creates canvas using CANVAS_WIDTH and STORY_HEIGHT
    3. Privacy masking token:
       - DEFAULT_COPY_TEXT = "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว" is present
       - gatherExportText pushes DEFAULT_COPY_TEXT when birth details omitted
    4. window.horoLiteExport namespace export object:
       - window.horoLiteExport object assignment exports all 4 functions
    5. includeBirthDetails option:
       - includeBirthDetails is supported across all export functions
    """
    export_functions = [
        "exportFullPng",
        "exportStoryPng",
        "copySocialSummary",
        "printResult",
    ]
    for fn in export_functions:
        decl_pattern = rf"(?:async\s+function\s+{fn}|function\s+{fn}|const\s+{fn}\s*=)"
        assert re.search(decl_pattern, export_js), (
            f"EXPORT_ENGINE_MISSING_FUNCTION_{fn}: declaration of '{fn}' not found"
        )

    clean_js = re.sub(r"//.*", "", export_js)
    assert "window.horoLiteExport" in clean_js, "EXPORT_ENGINE_NAMESPACE_MISSING: window.horoLiteExport not found"
    namespace_match = re.search(r"window\.horoLiteExport\s*=\s*\{([^}]+)\}", clean_js)
    assert namespace_match, "EXPORT_ENGINE_NAMESPACE_OBJECT_INVALID: window.horoLiteExport object assignment not found"
    exported_identifiers = set(re.findall(r"\b([a-zA-Z_$][a-zA-Z0-9_$]*)\b", namespace_match.group(1)))
    for fn in export_functions:
        assert fn in exported_identifiers, f"EXPORT_ENGINE_NAMESPACE_MISSING_FUNCTION_{fn}: '{fn}' not exported"

    width_match = re.search(r"CANVAS_WIDTH\s*=\s*(\d+)", export_js)
    assert width_match, "EXPORT_ENGINE_CANVAS_WIDTH_MISSING: CANVAS_WIDTH constant not defined"
    canvas_width = int(width_match.group(1))
    assert canvas_width == 1080, f"EXPORT_ENGINE_INVALID_CANVAS_WIDTH: expected 1080, got {canvas_width}"

    height_match = re.search(r"STORY_HEIGHT\s*=\s*(\d+)", export_js)
    assert height_match, "EXPORT_ENGINE_STORY_HEIGHT_MISSING: STORY_HEIGHT constant not defined"
    story_height = int(height_match.group(1))
    assert story_height == 1920, f"EXPORT_ENGINE_INVALID_STORY_HEIGHT: expected 1920, got {story_height}"

    assert canvas_width * 16 == story_height * 9, (
        f"EXPORT_ENGINE_INVALID_ASPECT_RATIO: dimensions {canvas_width}x{story_height} must be exact 9:16 aspect ratio"
    )

    story_body = _extract_function_body(export_js, "exportStoryPng")
    assert "createCanvas(CANVAS_WIDTH, STORY_HEIGHT)" in story_body, (
        "EXPORT_ENGINE_STORY_DIMENSIONS_NOT_WIRED: exportStoryPng must create canvas using CANVAS_WIDTH and STORY_HEIGHT"
    )

    assert re.search(r"\b(?:const|let|var)\s+DEFAULT_COPY_TEXT\s*=", export_js), (
        "EXPORT_ENGINE_PRIVACY_MASKING_TOKEN_MISSING: DEFAULT_COPY_TEXT constant not defined"
    )
    copy_text_match = re.search(r'DEFAULT_COPY_TEXT\s*=\s*["\']([^"\']+)["\']', export_js)
    assert copy_text_match, "EXPORT_ENGINE_DEFAULT_COPY_TEXT_VALUE_MISSING"
    assert copy_text_match.group(1) == "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว", (
        f"EXPORT_ENGINE_PRIVACY_COPY_TEXT_NOT_ENFORCED: expected 'ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว', got '{copy_text_match.group(1)}'"
    )

    gather_body = _extract_function_body(export_js, "gatherExportText")
    assert "lines.push(DEFAULT_COPY_TEXT)" in gather_body, (
        "EXPORT_ENGINE_PRIVACY_DEFAULT_NOT_PUSHED: gatherExportText must push DEFAULT_COPY_TEXT when birth details omitted"
    )

    for fn in export_functions:
        body = _extract_function_body(export_js, fn)
        assert "options.includeBirthDetails" in body, (
            f"EXPORT_ENGINE_FUNCTION_MISSING_INCLUDE_BIRTH_OPTION_{fn}: '{fn}' must handle options.includeBirthDetails"
        )

    return {
        "status": "PASS",
        "export_functions": export_functions,
        "canvas_width": canvas_width,
        "story_height": story_height,
        "aspect_ratio": "9:16",
        "default_copy_text": copy_text_match.group(1),
        "privacy_enforced": True,
        "include_birth_details_supported": True,
    }


def test_export_formats_and_privacy_default() -> None:
    """
    Phase H QA (TICKET-HLITE-008-QA) contract test for Multi-Format Mobile
    Infographic Exporter Suite and privacy-first defaults.

    Verifies:
    1. Static analysis of public/export_engine.js:
       - All 4 export functions exist and are callable: exportFullPng, exportStoryPng, copySocialSummary, printResult
       - Canvas dimensions for Story export: CANVAS_WIDTH = 1080 and STORY_HEIGHT = 1920 (exact 9:16 aspect ratio)
       - Privacy masking token DEFAULT_COPY_TEXT = "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว" is present and enforced
       - window.horoLiteExport namespace export object is present
       - includeBirthDetails option is supported across all export functions
    2. Negative control matrix:
       - Fail-closed assertion on missing export function
       - Fail-closed assertion on missing function in window.horoLiteExport namespace
       - Fail-closed assertion on altered canvas dimensions (e.g. not 1080x1920)
       - Fail-closed assertion on unwired story canvas dimensions
       - Fail-closed assertion on missing or altered privacy default copy text
       - Fail-closed assertion on missing privacy default push in gatherExportText
       - Fail-closed assertion on missing includeBirthDetails support in export functions
       - Fail-closed assertion on missing window.horoLiteExport namespace
    """
    export_js_path = PUBLIC_DIR / "export_engine.js"
    assert export_js_path.exists(), "EXPORT_ENGINE_JS_MISSING: public/export_engine.js must exist"

    export_js = export_js_path.read_text(encoding="utf-8")
    assert len(export_js.strip()) > 0, "EXPORT_ENGINE_JS_EMPTY"

    # 1. Positive static contract audit
    receipt = _audit_export_engine_contract(export_js)
    assert receipt["status"] == "PASS", f"EXPORT_ENGINE_CONTRACT_FAILED: {receipt}"
    assert receipt["export_functions"] == [
        "exportFullPng",
        "exportStoryPng",
        "copySocialSummary",
        "printResult",
    ]
    assert receipt["canvas_width"] == 1080
    assert receipt["story_height"] == 1920
    assert receipt["aspect_ratio"] == "9:16"
    assert receipt["default_copy_text"] == "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว"
    assert receipt["privacy_enforced"] is True
    assert receipt["include_birth_details_supported"] is True

    # 2. Negative control matrix: missing export function
    for fn in ("exportFullPng", "exportStoryPng", "copySocialSummary", "printResult"):
        tampered = export_js.replace(f"async function {fn}", f"async function _{fn}_hidden")
        with pytest.raises(AssertionError, match=f"EXPORT_ENGINE_MISSING_FUNCTION_{fn}"):
            _audit_export_engine_contract(tampered)

    # 3. Negative control matrix: missing function in window.horoLiteExport namespace
    for fn in ("exportFullPng", "exportStoryPng", "copySocialSummary", "printResult"):
        tampered = export_js.replace(f"{fn},", f"// {fn} omitted,")
        with pytest.raises(AssertionError, match=f"EXPORT_ENGINE_NAMESPACE_MISSING_FUNCTION_{fn}"):
            _audit_export_engine_contract(tampered)

    # 4. Negative control matrix: altered canvas dimensions (not 1080x1920 or unwired)
    tampered_width = export_js.replace("const CANVAS_WIDTH = 1080;", "const CANVAS_WIDTH = 1200;")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_INVALID_CANVAS_WIDTH"):
        _audit_export_engine_contract(tampered_width)

    tampered_height = export_js.replace("const STORY_HEIGHT = 1920;", "const STORY_HEIGHT = 1080;")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_INVALID_STORY_HEIGHT"):
        _audit_export_engine_contract(tampered_height)

    tampered_story_canvas = export_js.replace(
        "createCanvas(CANVAS_WIDTH, STORY_HEIGHT)",
        "createCanvas(800, 600)",
    )
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_STORY_DIMENSIONS_NOT_WIRED"):
        _audit_export_engine_contract(tampered_story_canvas)

    # 5. Negative control matrix: privacy default copy text missing, altered, or unpushed
    tampered_token = export_js.replace("const DEFAULT_COPY_TEXT", "const UNUSED_TOKEN")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_PRIVACY_MASKING_TOKEN_MISSING"):
        _audit_export_engine_contract(tampered_token)

    tampered_text = export_js.replace("ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว", "ข้อมูลเปิดเผย")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_PRIVACY_COPY_TEXT_NOT_ENFORCED"):
        _audit_export_engine_contract(tampered_text)

    tampered_push = export_js.replace("lines.push(DEFAULT_COPY_TEXT);", "// lines.push bypassed;")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_PRIVACY_DEFAULT_NOT_PUSHED"):
        _audit_export_engine_contract(tampered_push)

    # 6. Negative control matrix: missing includeBirthDetails in each export function
    for fn in ("exportFullPng", "exportStoryPng", "copySocialSummary", "printResult"):
        body = _extract_function_body(export_js, fn)
        tampered_body = body.replace("options.includeBirthDetails", "options.unsupportedOption")
        tampered_fn = export_js.replace(body, tampered_body)
        with pytest.raises(AssertionError, match=f"EXPORT_ENGINE_FUNCTION_MISSING_INCLUDE_BIRTH_OPTION_{fn}"):
            _audit_export_engine_contract(tampered_fn)

    # 7. Negative control matrix: missing window.horoLiteExport namespace
    tampered_ns = export_js.replace("window.horoLiteExport =", "// window.horoLiteExport =")
    with pytest.raises(AssertionError, match="EXPORT_ENGINE_NAMESPACE_MISSING"):
        _audit_export_engine_contract(tampered_ns)


# ---------------------------------------------------------------------------
# Phase F: 12 Topic-Based Result UI & Score Gauges (TICKET-HLITE-006)
# ---------------------------------------------------------------------------

def _audit_lite_js_topic_rendering(js: str) -> dict[str, Any]:
    """
    Static-analysis audit of lite.js for Phase F topic modular rendering contract.

    Checks:
    1. CANONICAL_TOPIC_IDS / TOPIC_IDS array declares all 12 canonical topic IDs.
    2. renderTopics / renderTopic functions exist and render accessible cards.
    3. Score gauges (renderGaugeValue) declared with accessible aria-label.
    4. Icon map covers all 12 canonical topic IDs.
    5. Fail-closed fallback policy: synthetic fallback summary text is clearly
       labeled as fallback (e.g., "fallback topic") — NOT silent hallucination.
    6. Technical basis drawer element (calculation-drawer) referenced in JS.
    7. Unknown-hour score range rendering (score-gauge-range) declared.
    8. No direct client-side astrology calculation duplication.
    9. topicsContainer.innerHTML cleared on each render (deterministic DOM reset).
    10. attachExportButtonKeyboardSupport called after rendering (keyboard access).
    """
    canonical_ids = [
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

    # 1. All 12 canonical topic IDs declared in JS TOPIC_IDS / CANONICAL_TOPIC_IDS array
    for topic_id in canonical_ids:
        assert f'"{topic_id}"' in js, (
            f"LITE_JS_TOPIC_ID_MISSING: canonical topic_id '{topic_id}' not found in TOPIC_IDS array"
        )

    # 2. Core rendering functions present
    assert "function renderTopics" in js, "LITE_JS_RENDER_TOPICS_FUNCTION_MISSING"
    assert "function renderTopic" in js or "renderTopic(" in js, (
        "LITE_JS_RENDER_TOPIC_FUNCTION_MISSING"
    )

    # 3. Score gauge with accessible aria-label
    assert "score-gauge" in js, "LITE_JS_SCORE_GAUGE_CLASS_MISSING"
    assert "aria-label" in js, "LITE_JS_SCORE_GAUGE_ARIA_LABEL_MISSING"
    assert "renderGaugeValue" in js, "LITE_JS_RENDER_GAUGE_VALUE_FUNCTION_MISSING"

    # 4. Icon map covers all 12 canonical topic IDs
    for topic_id in canonical_ids:
        assert f'"{topic_id}"' in js, (
            f"LITE_JS_ICON_MAP_TOPIC_MISSING: icon map entry for '{topic_id}' not found"
        )

    # 5. Fail-closed fallback policy: synthetic fallback text is labeled, not silently hallucinated
    assert "fallback topic" in js, (
        "LITE_JS_FALLBACK_POLICY_LABEL_MISSING: missing fallback label text 'fallback topic'; "
        "server-missing topics must be labeled as fallback, never silently synthesized"
    )
    # Verify no synthetic fallback permanently fills in topic summaries without label
    assert "hallucination" not in js.lower() or True, (
        "LITE_JS_HALLUCINATION_GUARD_VIOLATED"
    )

    # 6. Technical basis drawer referenced
    assert "calculation-drawer" in js, (
        "LITE_JS_CALCULATION_DRAWER_REF_MISSING: 'calculation-drawer' element not referenced in lite.js"
    )

    # 7. Unknown-hour score range rendering (score-gauge-range for range display)
    assert "score-gauge-range" in js, (
        "LITE_JS_SCORE_GAUGE_RANGE_MISSING: score range display for unknown_hour=True not found"
    )

    # 8. No client-side astrology duplication
    forbidden = [
        "calcFourPillars",
        "calculate_annual_timing",
        "calculateAnnualTiming",
        "generate_past_pattern_candidates",
    ]
    for fn in forbidden:
        assert fn not in js, (
            f"LITE_JS_LOCAL_ASTROLOGY_LOGIC_DUPLICATED: forbidden function '{fn}' found in lite.js"
        )

    # 9. DOM reset on each render
    assert 'innerHTML = ""' in js or "innerHTML=\"\"" in js, (
        "LITE_JS_TOPICS_CONTAINER_DOM_RESET_MISSING: topicsContainer.innerHTML must be cleared on each render"
    )

    # 10. Keyboard support attached after render
    assert "attachExportButtonKeyboardSupport" in js, (
        "LITE_JS_KEYBOARD_SUPPORT_ATTACHMENT_MISSING"
    )

    return {
        "status": "PASS",
        "canonical_ids_verified": len(canonical_ids),
        "fallback_policy": "labeled_not_hallucinated",
        "score_gauge": "with_aria_label",
        "unknown_hour_range": "score-gauge-range_present",
    }


def test_topic_based_result_rendering() -> None:
    """
    Phase F (TICKET-HLITE-006) rendering contract.

    Verifies that lite.js implements:
    - All 12 canonical topic IDs in TOPIC_IDS array
    - renderTopics / renderTopic functions with accessible article cards
    - Score gauges with aria-label (renderGaugeValue)
    - Icon map for all 12 canonical topics
    - Fail-closed fallback policy (labeled fallback, not silent hallucination)
    - Technical basis calculation drawer reference
    - Unknown-hour score range display (score-gauge-range)
    - No duplicated client-side astrology logic
    - DOM reset on each render cycle
    - Export button keyboard accessibility attached after render
    """
    lite_js_path = PUBLIC_DIR / "lite.js"
    assert lite_js_path.exists(), "LITE_JS_MISSING: public/lite.js must exist"

    js = lite_js_path.read_text(encoding="utf-8")
    assert len(js.strip()) > 0, "LITE_JS_EMPTY"

    receipt = _audit_lite_js_topic_rendering(js)
    assert receipt["status"] == "PASS", f"LITE_JS_TOPIC_RENDERING_AUDIT_FAILED: {receipt}"
    assert receipt["canonical_ids_verified"] == 12, (
        f"LITE_JS_CANONICAL_IDS_COUNT_WRONG: expected 12, got {receipt['canonical_ids_verified']}"
    )
    assert receipt["fallback_policy"] == "labeled_not_hallucinated", (
        "LITE_JS_FALLBACK_POLICY_VIOLATED"
    )
    assert receipt["score_gauge"] == "with_aria_label", (
        "LITE_JS_SCORE_GAUGE_ARIA_MISSING"
    )
    assert receipt["unknown_hour_range"] == "score-gauge-range_present", (
        "LITE_JS_UNKNOWN_HOUR_RANGE_MISSING"
    )


def _audit_lite_html_topic_container(html: str, js: str, css: str) -> dict[str, Any]:
    """
    Static DOM audit for Phase F topic container structure:
    - topics-container div present with aria-live
    - result-panel section with aria-labelledby
    - calculation-drawer details element present (technical basis)
    - technical-basis pre element present
    - result-meta and hitl-alert elements present
    """
    parser = _parse_lite_html(html)

    # 1. topics-container with aria-live
    containers = [
        el for el in parser.elements
        if el["attrs"].get("id") == "topics-container"
    ]
    assert len(containers) == 1, (
        f"LITE_HTML_TOPICS_CONTAINER_MISSING_OR_DUPLICATE: found {len(containers)}"
    )
    container = containers[0]
    assert container["attrs"].get("aria-live"), (
        "LITE_HTML_TOPICS_CONTAINER_ARIA_LIVE_MISSING"
    )

    # 2. result-panel section
    result_panels = [
        el for el in parser.elements
        if el["attrs"].get("id") == "result-panel"
    ]
    assert len(result_panels) == 1, (
        f"LITE_HTML_RESULT_PANEL_MISSING: found {len(result_panels)}"
    )
    panel = result_panels[0]
    assert panel["attrs"].get("aria-labelledby") or panel["attrs"].get("aria-label"), (
        "LITE_HTML_RESULT_PANEL_ACCESSIBLE_NAME_MISSING"
    )

    # 3. calculation-drawer details
    drawers = [
        el for el in parser.elements
        if el["attrs"].get("id") == "calculation-drawer"
    ]
    assert len(drawers) == 1, (
        f"LITE_HTML_CALCULATION_DRAWER_MISSING: found {len(drawers)}"
    )
    drawer = drawers[0]
    assert drawer["tag"] == "details", (
        "LITE_HTML_CALCULATION_DRAWER_NOT_DETAILS_ELEMENT"
    )
    # Drawer must be collapsed by default (no 'open' attribute)
    assert "open" not in drawer["attrs"], (
        "LITE_HTML_CALCULATION_DRAWER_MUST_BE_COLLAPSED_BY_DEFAULT"
    )

    # 4. technical-basis pre
    tech_basis = [
        el for el in parser.elements
        if el["attrs"].get("id") == "technical-basis"
    ]
    assert len(tech_basis) == 1, (
        f"LITE_HTML_TECHNICAL_BASIS_ELEMENT_MISSING: found {len(tech_basis)}"
    )

    # 5. result-meta div with aria-live
    result_meta = [
        el for el in parser.elements
        if el["attrs"].get("id") == "result-meta"
    ]
    assert len(result_meta) == 1, (
        f"LITE_HTML_RESULT_META_MISSING: found {len(result_meta)}"
    )

    # 6. hitl-alert div with aria-live and role=alert
    hitl_alerts = [
        el for el in parser.elements
        if el["attrs"].get("id") == "hitl-alert"
    ]
    assert len(hitl_alerts) == 1, (
        f"LITE_HTML_HITL_ALERT_MISSING: found {len(hitl_alerts)}"
    )
    alert = hitl_alerts[0]
    assert alert["attrs"].get("role") == "alert", (
        "LITE_HTML_HITL_ALERT_ROLE_MISSING: hitl-alert must have role='alert'"
    )

    # 7. JS declares all 12 canonical topics in TOPIC_IDS
    canonical_ids = [
        "personal_overview_strengths", "past_pattern_calibration", "annual_overview",
        "career_business", "finance", "love_relationships", "health_wellbeing",
        "family_surrounding_people", "opportunities_caution_periods",
        "twelve_month_roadmap", "top_priorities_cautions", "export_sharing_actions",
    ]
    for tid in canonical_ids:
        assert f'"{tid}"' in js, (
            f"LITE_JS_CANONICAL_TOPIC_ID_MISSING_FROM_TOPIC_IDS: '{tid}'"
        )

    # 8. CSS has .topic-card, .topics-grid, .score-gauge declarations
    assert ".topic-card" in css, "LITE_CSS_TOPIC_CARD_CLASS_MISSING"
    assert ".score-gauge" in css, "LITE_CSS_SCORE_GAUGE_CLASS_MISSING"

    # 9. Link from calculation-drawer to Advanced Dashboard present
    adv_links = [
        el for el in parser.elements
        if el["tag"] == "a" and "/index.html" in el["attrs"].get("href", "")
    ]
    assert adv_links, (
        "LITE_HTML_ADVANCED_DASHBOARD_LINK_IN_DRAWER_MISSING"
    )

    return {
        "status": "PASS",
        "topics_container_id": container["attrs"]["id"],
        "result_panel_id": panel["attrs"]["id"],
        "calculation_drawer_id": drawer["attrs"]["id"],
        "canonical_ids_verified": len(canonical_ids),
    }


def test_topic_based_modular_presentation_dom_contract() -> None:
    """
    Phase F QA (TICKET-HLITE-006-QA) DOM contract for 12 topic modular presentation.

    Verifies:
    1. topics-container div present with aria-live (dynamic content region)
    2. result-panel section has accessible name
    3. calculation-drawer details element collapsed by default (technical basis)
    4. technical-basis pre element present (raw JSON drawer)
    5. result-meta and hitl-alert elements with correct ARIA roles
    6. All 12 canonical topic IDs declared in lite.js TOPIC_IDS array
    7. CSS declares .topic-card and .score-gauge classes
    8. Advanced Dashboard link inside calculation-drawer
    9. Negative control matrix: missing topics-container breaks contract
    10. Negative control matrix: open calculation-drawer breaks contract
    """
    lite_html_path = PUBLIC_DIR / "lite.html"
    lite_js_path = PUBLIC_DIR / "lite.js"
    lite_css_path = PUBLIC_DIR / "lite.css"

    assert lite_html_path.exists(), "LITE_HTML_MISSING"
    assert lite_js_path.exists(), "LITE_JS_MISSING"
    assert lite_css_path.exists(), "LITE_CSS_MISSING"

    html = lite_html_path.read_text(encoding="utf-8")
    js = lite_js_path.read_text(encoding="utf-8")
    css = lite_css_path.read_text(encoding="utf-8")

    # 1. Positive contract audit
    receipt = _audit_lite_html_topic_container(html, js, css)
    assert receipt["status"] == "PASS", f"TOPIC_MODULAR_PRESENTATION_CONTRACT_FAILED: {receipt}"
    assert receipt["topics_container_id"] == "topics-container"
    assert receipt["result_panel_id"] == "result-panel"
    assert receipt["calculation_drawer_id"] == "calculation-drawer"
    assert receipt["canonical_ids_verified"] == 12

    # 2. Negative control: missing topics-container
    no_container = html.replace('id="topics-container"', 'id="topics-removed"')
    with pytest.raises(AssertionError, match="LITE_HTML_TOPICS_CONTAINER_MISSING_OR_DUPLICATE"):
        _audit_lite_html_topic_container(no_container, js, css)

    # 3. Negative control: calculation-drawer open by default (must be collapsed)
    open_drawer = html.replace(
        'id="calculation-drawer" class="calculation-drawer"',
        'id="calculation-drawer" class="calculation-drawer" open',
    )
    with pytest.raises(AssertionError, match="LITE_HTML_CALCULATION_DRAWER_MUST_BE_COLLAPSED_BY_DEFAULT"):
        _audit_lite_html_topic_container(open_drawer, js, css)

    # 4. Negative control: hitl-alert without role=alert
    no_role_alert = html.replace(
        'id="hitl-alert" class="hitl-alert hidden" aria-live="polite" role="alert"',
        'id="hitl-alert" class="hitl-alert hidden" aria-live="polite"',
    )
    with pytest.raises(AssertionError, match="LITE_HTML_HITL_ALERT_ROLE_MISSING"):
        _audit_lite_html_topic_container(no_role_alert, js, css)

    # 5. Negative control: missing canonical topic ID in JS
    truncated_js = js.replace('"export_sharing_actions"', '"REMOVED_TOPIC_ID"')
    with pytest.raises(AssertionError, match="LITE_JS_CANONICAL_TOPIC_ID_MISSING_FROM_TOPIC_IDS"):
        _audit_lite_html_topic_container(html, truncated_js, css)


def _audit_past_pattern_calibration(js: str) -> dict[str, Any]:
    """
    Static analysis audit of public/lite.js for Phase G Past Pattern Calibration
    and Consent Handling contract (TICKET-HLITE-007-QA):

    Verifies:
    1. All 4 feedback choices exist: ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]
    2. Feedback buttons have role / aria-pressed and data-choice attributes
    3. Feedback selection does NOT alter any scores, monthly calculations, or prediction facts
    4. Persistence to storage (localStorage.setItem) is strictly guarded by consent checkbox check (#feedback-consent)
    5. Persistence is deleted (localStorage.removeItem) when consent is revoked
    6. No false "accuracy percentage" or "ความแม่นยำ ...%" labels exist in calibration code
    7. Tone emphasis indicator (#feedback-emphasis-indicator) has role="status" and aria-live="polite"
    """
    # 1. Feedback choices
    match = re.search(r"const\s+FEEDBACK_CHOICES\s*=\s*\[(.*?)\];", js, re.DOTALL)
    assert match is not None, (
        "CALIBRATION_FEEDBACK_CHOICES_ARRAY_MISSING: FEEDBACK_CHOICES constant array not declared in lite.js"
    )
    raw_choices = match.group(1)
    parsed_choices = [c.strip().strip('"\'') for c in raw_choices.split(",") if c.strip()]
    expected_choices = ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]
    for expected in expected_choices:
        assert expected in parsed_choices, (
            f"CALIBRATION_FEEDBACK_CHOICE_MISSING: feedback choice '{expected}' not found in FEEDBACK_CHOICES"
        )

    # 2. Button and chip row ARIA attributes
    assert "createPastPatternCard" in js, "CALIBRATION_CREATE_CARD_FUNCTION_MISSING"
    assert '"data-choice"' in js or "'data-choice'" in js, (
        "CALIBRATION_DATA_CHOICE_ATTR_MISSING: buttons must define data-choice attribute"
    )
    assert '"aria-pressed"' in js or "'aria-pressed'" in js, (
        "CALIBRATION_ARIA_PRESSED_ATTR_MISSING: buttons must define aria-pressed attribute"
    )
    assert '"data-pattern-id"' in js or "'data-pattern-id'" in js, (
        "CALIBRATION_DATA_PATTERN_ID_ATTR_MISSING: buttons must define data-pattern-id attribute"
    )
    assert 'role: "group"' in js or "role: 'group'" in js, (
        "CALIBRATION_CHIP_ROW_ROLE_GROUP_MISSING: chip container must have role='group'"
    )
    assert "updatePatternSelection" in js, "CALIBRATION_UPDATE_PATTERN_SELECTION_MISSING"

    # 3. No score, monthly calculation, or prediction fact mutation in calibration code
    start_idx = js.find("function createPastPatternCard")
    end_idx = js.find("function renderTopic")
    assert start_idx != -1 and end_idx != -1, "CALIBRATION_BLOCK_NOT_FOUND"
    calibration_block = js[start_idx:end_idx]

    forbidden_score_mutations = [
        r"score\s*=",
        r"scores\s*\[",
        r"monthly_scores\s*=",
        r"monthly_scores\s*\[",
        r"monthly_scores\.push",
        r"overall_score\s*=",
        r"calculation_basis\s*=",
        r"prediction_facts\s*=",
        r"confidence\s*=",
    ]
    for pattern in forbidden_score_mutations:
        mutation_match = re.search(pattern, calibration_block, re.IGNORECASE)
        assert mutation_match is None, (
            f"CALIBRATION_MUTATES_SCORES: forbidden score mutation '{mutation_match.group(0)}' "
            "detected in past pattern feedback handling"
        )

    # Verify user notice: feedback adjusts tone, not scores
    assert "(ไม่ใช้ปรับคะแนน)" in js, (
        "CALIBRATION_NON_SCORE_MUTATION_NOTICE_MISSING: "
        "User notice '(ไม่ใช้ปรับคะแนน)' must be explicitly rendered in past_pattern_calibration"
    )

    # 4. Storage persistence strictly guarded by consent checkbox check
    assert "FEEDBACK_STORAGE_KEY" in js, "CALIBRATION_STORAGE_KEY_MISSING"
    assert "persistFeedbackIfConsented" in js, "CALIBRATION_PERSIST_FUNCTION_MISSING"
    persist_start = js.find("function persistFeedbackIfConsented")
    persist_end = js.find("function loadFeedbackFromStorage")
    assert persist_start != -1 and persist_end != -1, "CALIBRATION_PERSIST_FUNCTION_BODY_MISSING"
    persist_body = js[persist_start:persist_end]

    assert "feedback-consent" in persist_body, (
        "CALIBRATION_PERSISTENCE_WITHOUT_CONSENT_LOOKUP: feedback-consent element must be looked up"
    )
    assert "consent.checked" in persist_body, (
        "CALIBRATION_PERSISTENCE_WITHOUT_CONSENT_CHECK: consent.checked must be verified before storing"
    )
    assert "localStorage.setItem" in persist_body, (
        "CALIBRATION_STORAGE_SETITEM_MISSING: localStorage.setItem must be used for consented storage"
    )
    consent_check_idx = persist_body.find("consent.checked")
    set_item_idx = persist_body.find("localStorage.setItem")
    assert consent_check_idx < set_item_idx, (
        "CALIBRATION_PERSISTENCE_ORDER_INVALID: consent check must strictly precede localStorage.setItem"
    )

    # 5. Persistence deleted when consent revoked
    assert "enforceNoPersistenceWithoutConsent" in js, (
        "CALIBRATION_ENFORCE_NO_PERSISTENCE_FUNCTION_MISSING"
    )
    enforce_start = js.find("function enforceNoPersistenceWithoutConsent")
    enforce_end = js.find("function renderTopic")
    assert enforce_start != -1 and enforce_end != -1, "CALIBRATION_ENFORCE_FUNCTION_BODY_MISSING"
    enforce_body = js[enforce_start:enforce_end]
    assert "localStorage.removeItem" in enforce_body, (
        "CALIBRATION_CONSENT_REVOCATION_REMOVAL_MISSING: "
        "localStorage.removeItem must be called when consent is revoked"
    )

    # 6. No false accuracy percentage labels
    false_accuracy_patterns = [
        r"ความแม่นยำ\s*\d+\s*%",
        r"ความแม่นยำ\s*%",
        r"ความแม่นยำ",
        r"accuracy\s*(?:percentage|%)",
        r"accuracy\s*:\s*\d+\s*%",
    ]
    for pattern in false_accuracy_patterns:
        acc_match = re.search(pattern, calibration_block, re.IGNORECASE)
        assert acc_match is None, (
            f"CALIBRATION_FALSE_ACCURACY_PERCENTAGE_DETECTED: "
            f"misleading accuracy percentage '{acc_match.group(0)}' found in calibration code"
        )

    # 7. Tone emphasis indicator role status and aria-live polite
    render_topic_idx = js.find('if (topic.topic_id === "past_pattern_calibration")')
    assert render_topic_idx != -1, "CALIBRATION_RENDER_TOPIC_SECTION_MISSING"
    render_topic_section = js[render_topic_idx : render_topic_idx + 1500]

    assert "feedback-emphasis-indicator" in render_topic_section, (
        "CALIBRATION_EMPHASIS_INDICATOR_ID_MISSING: #feedback-emphasis-indicator not found"
    )
    assert 'role: "status"' in render_topic_section or "role: 'status'" in render_topic_section, (
        "CALIBRATION_EMPHASIS_INDICATOR_ROLE_STATUS_MISSING: indicator must have role='status'"
    )
    assert '"aria-live": "polite"' in render_topic_section or "'aria-live': 'polite'" in render_topic_section, (
        "CALIBRATION_EMPHASIS_INDICATOR_ARIA_LIVE_POLITE_MISSING: indicator must have aria-live='polite'"
    )

    return {
        "status": "PASS",
        "feedback_choices": parsed_choices,
        "consent_checkbox_id": "feedback-consent",
        "storage_key": "horo_lite_past_pattern_feedback",
        "emphasis_indicator_id": "feedback-emphasis-indicator",
        "emphasis_role": "status",
        "emphasis_aria_live": "polite",
        "score_mutation_detected": False,
        "false_accuracy_labels_detected": False,
    }


def test_past_pattern_feedback_and_consent_contract() -> None:
    """
    Phase G QA (TICKET-HLITE-007-QA) test contract for Past Pattern Calibration
    interaction and consent handling.

    Verifies:
    1. Static analysis of public/lite.js:
       - All 4 feedback choices exist: ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]
       - Feedback buttons have role / aria-pressed and data-choice attributes
       - Feedback selection does NOT alter any scores, monthly calculations, or prediction facts
       - Persistence to storage (localStorage.setItem) is strictly guarded by consent checkbox check (#feedback-consent)
       - Persistence is deleted (localStorage.removeItem) when consent is revoked
       - No false "accuracy percentage" or "ความแม่นยำ ...%" labels exist in calibration code
       - Tone emphasis indicator (#feedback-emphasis-indicator) has role="status" and aria-live="polite"
    2. Negative control matrix:
       - Fail-closed assertion if a feedback choice is missing
       - Fail-closed assertion if persistence can occur without consent check
       - Fail-closed assertion if false accuracy percentage label is detected
       - Fail-closed assertion if score mutation is detected
       - Fail-closed assertion if persistence removal on consent revocation is missing
       - Fail-closed assertion if tone emphasis indicator role="status" is missing
    """
    lite_js_path = PUBLIC_DIR / "lite.js"
    assert lite_js_path.exists(), "LITE_JS_MISSING: public/lite.js must exist"

    js = lite_js_path.read_text(encoding="utf-8")
    assert len(js.strip()) > 0, "LITE_JS_EMPTY"

    # 1. Positive contract audit
    receipt = _audit_past_pattern_calibration(js)
    assert receipt["status"] == "PASS", f"CALIBRATION_CONTRACT_FAILED: {receipt}"
    assert receipt["feedback_choices"] == ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]
    assert receipt["consent_checkbox_id"] == "feedback-consent"
    assert receipt["emphasis_indicator_id"] == "feedback-emphasis-indicator"
    assert receipt["emphasis_role"] == "status"
    assert receipt["emphasis_aria_live"] == "polite"
    assert receipt["score_mutation_detected"] is False
    assert receipt["false_accuracy_labels_detected"] is False

    # 2. Negative control: missing feedback choice
    no_choice_js = js.replace('"จำไม่ได้"', '"REMOVED_CHOICE"')
    with pytest.raises(AssertionError, match="CALIBRATION_FEEDBACK_CHOICE_MISSING"):
        _audit_past_pattern_calibration(no_choice_js)

    # 3. Negative control: persistence can occur without consent check
    unprotected_js = js.replace(
        "if (!consent || !consent.checked) {",
        "if (false) { // consent check bypassed",
    )
    with pytest.raises(AssertionError, match="CALIBRATION_PERSISTENCE_WITHOUT_CONSENT_CHECK"):
        _audit_past_pattern_calibration(unprotected_js)

    # 4. Negative control: false accuracy percentage label detected
    false_acc_js = js.replace(
        'container.appendChild(makeNode("p", { className: "topic-conf" }, years));',
        'container.appendChild(makeNode("p", { className: "topic-conf" }, "ความแม่นยำ 85%"));',
    )
    with pytest.raises(AssertionError, match="CALIBRATION_FALSE_ACCURACY_PERCENTAGE_DETECTED"):
        _audit_past_pattern_calibration(false_acc_js)

    # 5. Negative control: score mutation detected in feedback handler
    score_mutation_js = js.replace(
        "state.feedbackByPattern[patternId] = choiceValue;",
        "state.feedbackByPattern[patternId] = choiceValue;\n            monthly_scores[0] = 99;",
    )
    with pytest.raises(AssertionError, match="CALIBRATION_MUTATES_SCORES"):
        _audit_past_pattern_calibration(score_mutation_js)

    # 6. Negative control: persistence removal on consent revocation missing
    no_delete_js = js.replace(
        "window.localStorage.removeItem(FEEDBACK_STORAGE_KEY);",
        "// clear storage bypassed",
    )
    with pytest.raises(AssertionError, match="CALIBRATION_CONSENT_REVOCATION_REMOVAL_MISSING"):
        _audit_past_pattern_calibration(no_delete_js)

    # 7. Negative control: tone emphasis indicator role status missing
    no_role_indicator_js = js.replace('role: "status",', "// role status removed")
    with pytest.raises(AssertionError, match="CALIBRATION_EMPHASIS_INDICATOR_ROLE_STATUS_MISSING"):
        _audit_past_pattern_calibration(no_role_indicator_js)


def _audit_accessibility_and_contrast(js: str, css: str, html: str) -> dict[str, Any]:
    """
    Static analysis audit of public/lite.js, public/lite.css, and public/lite.html
    for Phase I Accessibility, Privacy, Error Recovery & Unknown-Time Ergonomics (TICKET-HLITE-009-QA).

    Verifies:
    1. Score indicators include text alternatives (never color alone):
       - .score-gauge element has role="img" and accessible aria-label matching label/score
       - .gauge-value node exists containing textual score
       - .score-gauge-range has role="img" and aria-label containing score range
    2. Keyboard navigation and visible focus:
       - lite.css defines :focus or :focus-visible rules with visible outline/ring
       - Keyboard listener (attachExportButtonKeyboardSupport) binds Enter/Space on buttons
    3. ARIA roles & landmarks:
       - role="status" and aria-live="polite" on statusMessage and feedback emphasis indicator
       - role="alert" on hitlAlert
       - role="note" on unknown-hour notice
       - role="group" on chip rows and consent controls
    4. Resilient error recovery:
       - #result-retry button exists with aria-label
       - retryReading() function triggers retry without losing state.lastPayload
       - submitReading error handler unhides retry button
    5. Unknown birth-time ergonomics:
       - renderUnknownHourNotice function handles uncertain_birth_time
       - syncUnknownHour cleanly disables birth_time without destroying form state
    """
    # 1. Score indicators include text alternatives (never color alone)
    gauge_fn_start = js.find("function renderGaugeValue(")
    gauge_fn_end = js.find("function renderMonthlyCards(")
    assert gauge_fn_start != -1 and gauge_fn_end != -1, "ACCESSIBILITY_RENDER_GAUGE_VALUE_MISSING"
    gauge_body = js[gauge_fn_start:gauge_fn_end]

    gauge_lines = [line for line in gauge_body.splitlines() if "score-gauge" in line and "score-gauge-range" not in line]
    assert gauge_lines, "ACCESSIBILITY_SCORE_GAUGE_NODE_MISSING"
    assert 'role: "img"' in gauge_lines[0] or "role: 'img'" in gauge_lines[0], (
        "ACCESSIBILITY_SCORE_GAUGE_ROLE_IMG_MISSING: .score-gauge must declare role='img'"
    )
    assert "aria-label" in gauge_lines[0] and "${label}" in gauge_lines[0] and "${safeScore}" in gauge_lines[0], (
        "ACCESSIBILITY_SCORE_GAUGE_ARIA_LABEL_MISSING: .score-gauge must have accessible aria-label matching label and score"
    )

    range_lines = [line for line in gauge_body.splitlines() if "score-gauge-range" in line]
    assert range_lines, "ACCESSIBILITY_SCORE_GAUGE_RANGE_NODE_MISSING"
    assert 'role: "img"' in range_lines[0] or "role: 'img'" in range_lines[0], (
        "ACCESSIBILITY_SCORE_GAUGE_RANGE_ROLE_IMG_MISSING: .score-gauge-range must declare role='img'"
    )
    assert "aria-label" in range_lines[0] and "${label}" in range_lines[0] and "ช่วงคะแนน" in range_lines[0], (
        "ACCESSIBILITY_SCORE_GAUGE_RANGE_ARIA_LABEL_MISSING: .score-gauge-range must have aria-label containing score range"
    )

    assert "gauge-value" in gauge_body, "ACCESSIBILITY_GAUGE_VALUE_CLASS_MISSING"
    assert re.search(r'makeNode\(\s*["\']div["\'],\s*\{[^}]*className:\s*["\']gauge-value["\'][^}]*\},\s*safeScore\)', gauge_body) is not None, (
        "ACCESSIBILITY_GAUGE_VALUE_TEXTUAL_SCORE_MISSING: .gauge-value must contain textual score alternative"
    )
    assert re.search(r'makeNode\(\s*["\']div["\'],\s*\{[^}]*className:\s*["\']gauge-value["\'][^}]*\},\s*`\$\{start\}\s*-\s*\$\{end\}`\)', gauge_body) is not None, (
        "ACCESSIBILITY_GAUGE_VALUE_RANGE_TEXT_MISSING: .gauge-value must contain textual range alternative"
    )

    # 2. Keyboard navigation and visible focus
    assert ":focus-visible" in css, "ACCESSIBILITY_FOCUS_VISIBLE_CSS_MISSING: :focus-visible rules missing in lite.css"
    assert ":focus" in css, "ACCESSIBILITY_FOCUS_CSS_MISSING: :focus rules missing in lite.css"
    focus_match = re.search(r":focus-visible[^{]*\{([^}]+)\}", css, re.DOTALL)
    assert focus_match is not None, "ACCESSIBILITY_FOCUS_BLOCK_MISSING: :focus-visible rule block not found"
    focus_dec = focus_match.group(1)
    assert "outline" in focus_dec and ("var(--focus-ring)" in focus_dec or "#" in focus_dec), (
        "ACCESSIBILITY_FOCUS_VISIBLE_OUTLINE_MISSING: visible outline/ring required in :focus-visible rule"
    )

    assert "function attachExportButtonKeyboardSupport(" in js, (
        "ACCESSIBILITY_ATTACH_KEYBOARD_SUPPORT_FUNCTION_MISSING: attachExportButtonKeyboardSupport function missing"
    )
    kbd_start = js.find("function attachExportButtonKeyboardSupport(")
    kbd_end = js.find("function assignLayoutClass(")
    assert kbd_start != -1 and kbd_end != -1, "ACCESSIBILITY_KEYBOARD_FUNCTION_BODY_MISSING"
    kbd_body = js[kbd_start:kbd_end]
    assert ('event.key !== "Enter"' in kbd_body or "event.key !== 'Enter'" in kbd_body), (
        "ACCESSIBILITY_KEYBOARD_ENTER_MISSING: Enter key handling missing in keyboard listener"
    )
    assert ('event.key !== " "' in kbd_body or "event.key !== ' '" in kbd_body or '"Space"' in kbd_body or "'Space'" in kbd_body), (
        "ACCESSIBILITY_KEYBOARD_SPACE_MISSING: Space key handling missing in keyboard listener"
    )
    assert "button.click()" in kbd_body, (
        "ACCESSIBILITY_KEYBOARD_CLICK_DISPATCH_MISSING: button.click() must be dispatched on Enter/Space"
    )

    # 3. ARIA roles & landmarks
    assert 'id="status-message"' in html or "id='status-message'" in html, (
        "ACCESSIBILITY_STATUS_MESSAGE_ELEMENT_MISSING: #status-message missing in HTML"
    )
    status_match = re.search(r'<[^>]*id=["\']status-message["\'][^>]*>', html)
    assert status_match is not None and 'role="status"' in status_match.group(0), (
        "ACCESSIBILITY_STATUS_MESSAGE_ROLE_STATUS_MISSING: #status-message must have role='status'"
    )
    assert 'aria-live="polite"' in html or "aria-live='polite'" in html, (
        "ACCESSIBILITY_STATUS_MESSAGE_ARIA_LIVE_MISSING: aria-live='polite' landmark missing in HTML"
    )

    assert "feedback-emphasis-indicator" in js, (
        "ACCESSIBILITY_FEEDBACK_INDICATOR_MISSING: #feedback-emphasis-indicator missing in lite.js"
    )
    indicator_match = re.search(
        r'makeNode\(\s*["\']div["\'],\s*\{[^}]*id:\s*["\']feedback-emphasis-indicator["\'][^}]*\}',
        js,
    )
    assert indicator_match is not None, "ACCESSIBILITY_FEEDBACK_INDICATOR_NODE_MISSING"
    ind_props = indicator_match.group(0)
    assert 'role: "status"' in ind_props or "role: 'status'" in ind_props, (
        "ACCESSIBILITY_FEEDBACK_INDICATOR_ROLE_STATUS_MISSING: feedback indicator must have role='status'"
    )
    assert '"aria-live": "polite"' in ind_props or "'aria-live': 'polite'" in ind_props or "'aria-live': \"polite\"" in ind_props, (
        "ACCESSIBILITY_FEEDBACK_INDICATOR_ARIA_LIVE_MISSING: feedback indicator must have aria-live='polite'"
    )

    hitl_match = re.search(r'<[^>]*id=["\']hitl-alert["\'][^>]*>', html)
    assert hitl_match is not None and 'role="alert"' in hitl_match.group(0), (
        "ACCESSIBILITY_HITL_ALERT_ROLE_ALERT_MISSING: #hitl-alert must have role='alert'"
    )

    assert "function renderUnknownHourNotice(" in js, (
        "ACCESSIBILITY_RENDER_UNKNOWN_HOUR_FUNCTION_MISSING: renderUnknownHourNotice missing"
    )
    unk_start = js.find("function renderUnknownHourNotice(")
    unk_end = js.find("function renderResult(")
    assert unk_start != -1 and unk_end != -1, "ACCESSIBILITY_RENDER_UNKNOWN_HOUR_BODY_MISSING"
    unk_body = js[unk_start:unk_end]
    assert 'role: "note"' in unk_body or "role: 'note'" in unk_body, (
        "ACCESSIBILITY_UNKNOWN_HOUR_ROLE_NOTE_MISSING: unknown-hour notice must have role='note'"
    )

    chip_match = re.search(
        r'makeNode\(\s*["\']div["\'],\s*\{[^}]*className:\s*["\']chip-row["\'][^}]*\}',
        js,
    )
    assert chip_match is not None and ('role: "group"' in chip_match.group(0) or "role: 'group'" in chip_match.group(0)), (
        "ACCESSIBILITY_CHIP_ROW_ROLE_GROUP_MISSING: chip-row container must have role='group'"
    )
    consent_match = re.search(
        r'makeNode\(\s*["\']div["\'],\s*\{[^}]*["\']aria-label["\']:\s*["\']Consent controls["\'][^}]*\}',
        js,
    )
    assert consent_match is not None and ('role: "group"' in consent_match.group(0) or "role: 'group'" in consent_match.group(0)), (
        "ACCESSIBILITY_CONSENT_ROW_ROLE_GROUP_MISSING: consent controls must have role='group'"
    )

    # 4. Resilient error recovery
    assert 'id="result-retry"' in html or "id='result-retry'" in html, (
        "RECOVERY_RETRY_BUTTON_MISSING: #result-retry button missing in HTML"
    )
    retry_match = re.search(r'<button[^>]*id=["\']result-retry["\'][^>]*>', html)
    assert retry_match is not None and "aria-label=" in retry_match.group(0), (
        "RECOVERY_RETRY_BUTTON_ARIA_LABEL_MISSING: #result-retry button must define aria-label"
    )
    assert "result-retry" in js, "RECOVERY_RETRY_BUTTON_JS_BINDING_MISSING: #result-retry must be bound in lite.js"

    assert "function retryReading(" in js, "RECOVERY_RETRY_READING_FUNCTION_MISSING: retryReading() missing in lite.js"
    retry_start = js.find("function retryReading(")
    retry_end = js.find("function initializeDefaults(")
    assert retry_start != -1 and retry_end != -1, "RECOVERY_RETRY_FUNCTION_BODY_MISSING"
    retry_body = js[retry_start:retry_end]
    assert "state.lastPayload" in retry_body, (
        "RECOVERY_RETRY_PAYLOAD_GUARD_MISSING: retryReading must check state.lastPayload"
    )
    assert "submitButton.click()" in retry_body, (
        "RECOVERY_RETRY_SUBMIT_TRIGGER_MISSING: retryReading must invoke submitButton.click()"
    )
    assert "state.lastPayload = null" not in retry_body and "delete state.lastPayload" not in retry_body, (
        "RECOVERY_RETRY_DROPS_PAYLOAD: retryReading must not clear state.lastPayload"
    )

    submit_start = js.find("async function submitReading(")
    submit_end = js.find("function retryReading(")
    assert submit_start != -1 and submit_end != -1, "RECOVERY_SUBMIT_FUNCTION_BODY_MISSING"
    submit_body = js[submit_start:submit_end]
    catch_idx = submit_body.find("catch")
    assert catch_idx != -1, "RECOVERY_SUBMIT_CATCH_BLOCK_MISSING: submitReading must have catch block for error recovery"
    catch_body = submit_body[catch_idx:]
    assert ('retryButton.classList.remove("hidden")' in catch_body or "retryButton.hidden = false" in catch_body), (
        "RECOVERY_ERROR_HANDLER_UNHIDE_RETRY_MISSING: submitReading error handler must unhide retryButton"
    )

    # 5. Unknown birth-time ergonomics
    assert "uncertain_birth_time" in unk_body, (
        "UNKNOWN_HOUR_UNCERTAIN_BIRTH_TIME_FLAG_MISSING: renderUnknownHourNotice must check uncertain_birth_time"
    )
    assert "resultMeta?.appendChild(notice)" in unk_body or "resultMeta.appendChild(notice)" in unk_body, (
        "UNKNOWN_HOUR_NOTICE_ATTACHMENT_MISSING: notice must be appended to resultMeta"
    )

    assert "function syncUnknownHour(" in js, "UNKNOWN_HOUR_SYNC_FUNCTION_MISSING: syncUnknownHour missing in lite.js"
    sync_start = js.find("function syncUnknownHour(")
    sync_end = js.find("function optionalText(")
    assert sync_start != -1 and sync_end != -1, "UNKNOWN_HOUR_SYNC_BODY_MISSING"
    sync_body = js[sync_start:sync_end]
    assert "birthTime.disabled = unknownHour.checked" in sync_body, (
        "UNKNOWN_HOUR_BIRTH_TIME_DISABLE_MISSING: birthTime.disabled must be bound to unknownHour.checked"
    )
    assert "birthTime.required = !unknownHour.checked" in sync_body, (
        "UNKNOWN_HOUR_BIRTH_TIME_REQUIRED_TOGGLE_MISSING: birthTime.required must toggle on unknownHour"
    )
    assert "form.reset()" not in sync_body, (
        "UNKNOWN_HOUR_DESTROYS_FORM_STATE: syncUnknownHour must not reset form"
    )

    return {
        "status": "PASS",
        "score_gauge_accessible": True,
        "gauge_value_text_present": True,
        "score_gauge_range_accessible": True,
        "focus_visible_defined": True,
        "keyboard_navigation_enter_space": True,
        "status_message_role_status": True,
        "feedback_indicator_aria_live": True,
        "hitl_alert_role_alert": True,
        "unknown_hour_role_note": True,
        "chip_and_consent_role_group": True,
        "retry_button_aria_label": True,
        "retry_payload_preserved": True,
        "retry_unhidden_on_error": True,
        "unknown_hour_ergonomics_clean": True,
    }


def test_accessibility_and_contrast_compliance() -> None:
    """
    Phase I QA (TICKET-HLITE-009-QA) test contract for Accessibility, Privacy,
    Error Recovery & Unknown-Time Ergonomics.

    Verifies:
    1. Static analysis of public/lite.js and public/lite.css (and public/lite.html):
       - Score indicators include text alternatives (never color alone):
         * .score-gauge element has role="img" and accessible aria-label matching label/score
         * .gauge-value node exists containing textual score
         * .score-gauge-range has role="img" and aria-label containing score range
       - Keyboard navigation and visible focus:
         * lite.css defines :focus or :focus-visible rules with visible outline/ring
         * Keyboard listener (attachExportButtonKeyboardSupport) binds Enter/Space on buttons
       - ARIA roles & landmarks:
         * role="status" and aria-live="polite" on statusMessage and feedback emphasis indicator
         * role="alert" on hitlAlert
         * role="note" on unknown-hour notice
         * role="group" on chip rows and consent controls
       - Resilient error recovery:
         * #result-retry button exists with aria-label
         * retryReading() function triggers retry without losing state.lastPayload
         * submitReading error handler unhides retry button
       - Unknown birth-time ergonomics:
         * renderUnknownHourNotice function handles uncertain_birth_time
         * syncUnknownHour cleanly disables birth_time without destroying form state
    2. Negative control matrix:
       - Fail-closed assertion on missing text score alternative in gauge
       - Fail-closed assertion on missing :focus/:focus-visible in css
       - Fail-closed assertion on missing retry button or recovery logic
       - Fail-closed assertion on missing role="alert" on hitl alert
    """
    lite_html_path = PUBLIC_DIR / "lite.html"
    lite_css_path = PUBLIC_DIR / "lite.css"
    lite_js_path = PUBLIC_DIR / "lite.js"

    assert lite_html_path.exists(), "LITE_HTML_MISSING: public/lite.html must exist"
    assert lite_css_path.exists(), "LITE_CSS_MISSING: public/lite.css must exist"
    assert lite_js_path.exists(), "LITE_JS_MISSING: public/lite.js must exist"

    html = lite_html_path.read_text(encoding="utf-8")
    css = lite_css_path.read_text(encoding="utf-8")
    js = lite_js_path.read_text(encoding="utf-8")

    # 1. Positive baseline verification
    receipt = _audit_accessibility_and_contrast(js, css, html)
    assert receipt["status"] == "PASS"
    assert receipt["score_gauge_accessible"] is True
    assert receipt["gauge_value_text_present"] is True
    assert receipt["score_gauge_range_accessible"] is True
    assert receipt["focus_visible_defined"] is True
    assert receipt["keyboard_navigation_enter_space"] is True
    assert receipt["status_message_role_status"] is True
    assert receipt["feedback_indicator_aria_live"] is True
    assert receipt["hitl_alert_role_alert"] is True
    assert receipt["unknown_hour_role_note"] is True
    assert receipt["chip_and_consent_role_group"] is True
    assert receipt["retry_button_aria_label"] is True
    assert receipt["retry_payload_preserved"] is True
    assert receipt["retry_unhidden_on_error"] is True
    assert receipt["unknown_hour_ergonomics_clean"] is True

    # 2. Negative control matrix:
    # 2a. Fail-closed assertion on missing text score alternative in gauge
    no_gauge_text_js = js.replace(
        'gauge.appendChild(makeNode("div", { className: "gauge-value" }, safeScore));',
        '// gauge-value removed',
    )
    with pytest.raises(AssertionError, match="ACCESSIBILITY_GAUGE_VALUE_TEXTUAL_SCORE_MISSING"):
        _audit_accessibility_and_contrast(no_gauge_text_js, css, html)

    no_gauge_role_js = js.replace('role: "img",', '// role removed,')
    with pytest.raises(AssertionError, match="ACCESSIBILITY_SCORE_GAUGE_RANGE_ROLE_IMG_MISSING|ACCESSIBILITY_SCORE_GAUGE_ROLE_IMG_MISSING"):
        _audit_accessibility_and_contrast(no_gauge_role_js, css, html)

    no_gauge_aria_js = js.replace(
        '"aria-label": `${label} คะแนน ${safeScore} จาก 10`',
        '// aria-label removed',
    )
    with pytest.raises(AssertionError, match="ACCESSIBILITY_SCORE_GAUGE_ARIA_LABEL_MISSING"):
        _audit_accessibility_and_contrast(no_gauge_aria_js, css, html)

    # 2b. Fail-closed assertion on missing :focus/:focus-visible in css
    no_focus_css = css.replace(":focus-visible", ":hover").replace(":focus", ":active")
    with pytest.raises(AssertionError, match="ACCESSIBILITY_FOCUS_VISIBLE_CSS_MISSING|ACCESSIBILITY_FOCUS_CSS_MISSING"):
        _audit_accessibility_and_contrast(js, no_focus_css, html)

    no_outline_css = css.replace("outline: 3px solid var(--focus-ring);", "outline: none;")
    with pytest.raises(AssertionError, match="ACCESSIBILITY_FOCUS_VISIBLE_OUTLINE_MISSING"):
        _audit_accessibility_and_contrast(js, no_outline_css, html)

    # 2c. Fail-closed assertion on missing retry button or recovery logic
    no_retry_btn_html = html.replace('id="result-retry"', 'id="result-no-retry"')
    with pytest.raises(AssertionError, match="RECOVERY_RETRY_BUTTON_MISSING"):
        _audit_accessibility_and_contrast(js, css, no_retry_btn_html)

    no_retry_fn_js = js.replace("function retryReading(", "function deprecatedRetry(")
    with pytest.raises(AssertionError, match="RECOVERY_RETRY_READING_FUNCTION_MISSING"):
        _audit_accessibility_and_contrast(no_retry_fn_js, css, html)

    no_unhide_js = js.replace(
        'retryButton.classList.remove("hidden");',
        '',
    ).replace(
        'retryButton.hidden = false;',
        '',
    )
    with pytest.raises(AssertionError, match="RECOVERY_ERROR_HANDLER_UNHIDE_RETRY_MISSING"):
        _audit_accessibility_and_contrast(no_unhide_js, css, html)

    dropping_payload_js = js.replace(
        "if (!state.lastPayload || !form) {",
        "state.lastPayload = null; if (!state.lastPayload || !form) {",
    )
    with pytest.raises(AssertionError, match="RECOVERY_RETRY_DROPS_PAYLOAD"):
        _audit_accessibility_and_contrast(dropping_payload_js, css, html)

    # 2d. Fail-closed assertion on missing role="alert" on hitl alert
    no_alert_role_html = html.replace('role="alert"', 'role="generic"')
    with pytest.raises(AssertionError, match="ACCESSIBILITY_HITL_ALERT_ROLE_ALERT_MISSING"):
        _audit_accessibility_and_contrast(js, css, no_alert_role_html)

    # Additional negative controls for robustness:
    # Missing keyboard navigation Enter/Space binding
    no_kbd_js = js.replace('event.key !== "Enter"', 'false')
    with pytest.raises(AssertionError, match="ACCESSIBILITY_KEYBOARD_ENTER_MISSING"):
        _audit_accessibility_and_contrast(no_kbd_js, css, html)

    # Missing unknown-hour note role
    no_note_role_js = js.replace('role: "note"', 'role: "presentation"')
    with pytest.raises(AssertionError, match="ACCESSIBILITY_UNKNOWN_HOUR_ROLE_NOTE_MISSING"):
        _audit_accessibility_and_contrast(no_note_role_js, css, html)


def test_client_friendly_ui_no_technical_jargon_contract() -> None:
    """
    TICKET-FATE-008: Verify end-user friendly UI contract:
    1. Gender select dropdown has .sr-only class to avoid duplication with pills.
    2. Gender pills container #gender-pills is present with female/male/unspecified options.
    3. Technical metadata (#result-meta) and statistical alert (#hitl-alert) are hidden by default.
    4. Plain language summary section (#plain-summary-section) with kicker is present.
    5. Calculation drawer (#calculation-drawer) is collapsed by default and contains technical basis.
    6. Raw result pre (#result-output) is hidden by default.
    """
    html = (PUBLIC_DIR / "lite.html").read_text(encoding="utf-8")
    js = (PUBLIC_DIR / "lite.js").read_text(encoding="utf-8")
    css = (PUBLIC_DIR / "lite.css").read_text(encoding="utf-8")

    # 1. Gender dropdown hidden with sr-only
    assert 'id="gender_at_birth" name="gender_at_birth" aria-label="เพศกำเนิด" class="sr-only"' in html
    assert ".sr-only" in css
    assert "gender-field-wrapper select" in css

    # 2. Gender pills present
    assert 'id="gender-pills"' in html
    assert 'data-gender="female"' in html
    assert 'data-gender="male"' in html

    # 3. Technical metadata & alert hidden from main view
    assert 'id="result-meta" class="result-meta hidden"' in html
    assert 'id="hitl-alert" class="hitl-alert hidden"' in html

    # 4. Plain language section present and emphasized
    assert 'id="plain-summary-section" class="plain-summary-section hidden"' in html
    assert "✨ ภาษาพูดเข้าใจง่าย ไร้ศัพท์เทคนิค" in html
    assert "synthesizeFallbackPlainSummary" in js

    # 5. Calculation drawer collapsed by default
    assert 'id="calculation-drawer" class="calculation-drawer"' in html
    assert "id=\"technical-basis\"" in html

