from __future__ import annotations

from html.parser import HTMLParser
from copy import deepcopy
from datetime import date
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
        element = {
            "tag": tag.lower(),
            "attrs": {name.lower(): value or "" for name, value in attrs},
            "text": "",
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
    assert _field(first_result, "engine_version") == "annual_timing_proxy.v1"
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
    parser = _parse_lite_html(html)

    stylesheet_hrefs = [
        element["attrs"].get("href", "")
        for element in parser.elements
        if element["tag"] == "link"
        and "stylesheet" in element["attrs"].get("rel", "").lower()
    ]
    script_srcs = [
        element["attrs"].get("src", "")
        for element in parser.elements
        if element["tag"] == "script"
    ]
    assert any(href.endswith("lite.css") for href in stylesheet_hrefs), (
        "LITE_HTML_STYLESHEET_REFERENCE_MISSING"
    )
    assert any(src.endswith("lite.js") for src in script_srcs), "LITE_HTML_SCRIPT_REFERENCE_MISSING"

    birth_date = _find_control(
        parser,
        field_name="birth_date",
        tokens=("birth_date", "birth-date", "birthdate"),
        types=("date",),
    )
    assert birth_date["attrs"].get("autocomplete") in {"bday", ""}, (
        "LITE_FORM_BIRTH_DATE_AUTOCOMPLETE_UNEXPECTED"
    )
    _find_control(
        parser,
        field_name="birth_time",
        tokens=("birth_time", "birth-time", "birthtime"),
        types=("time",),
    )
    _find_control(
        parser,
        field_name="unknown_birth_time",
        tokens=("unknown_hour", "unknown-time", "unknown_birth_time", "unknownbirthtime"),
        types=("checkbox",),
    )
    _find_control(
        parser,
        field_name="birthplace_geocoding",
        tokens=("birth_place", "birth-place", "birthplace", "location", "geocode", "place-search"),
        types=("search", "text"),
    )
    _find_control(
        parser,
        field_name="gender",
        tokens=("gender", "sex"),
        tags=("select", "input"),
    )
    _find_control(
        parser,
        field_name="target_year",
        tokens=("target_year", "target-year", "targetyear", "year"),
        types=("number", "text"),
    )

    optional_profile_controls = [
        element
        for element in parser.elements
        if element["tag"] in {"input", "textarea"}
        and any(
            token in _attr_blob(element)
            for token in (
                "display_name",
                "display-name",
                "displayname",
                "focus_question",
                "focus-question",
                "primary_focus_question",
            )
        )
    ]
    label_targets = _label_targets(parser)
    for control in optional_profile_controls:
        assert control["attrs"].get("id") and control["attrs"].get("name"), (
            "LITE_FORM_OPTIONAL_PROFILE_CONTROL_ID_NAME_MISSING"
        )
        assert _control_is_accessibly_labelled(control, parser, label_targets), (
            "LITE_FORM_OPTIONAL_PROFILE_CONTROL_ACCESSIBLE_LABEL_MISSING"
        )

    advanced_blocks = _details_blocks(parser)
    assert advanced_blocks, "LITE_FORM_ADVANCED_DETAILS_DISCLOSURE_MISSING"
    advanced_text = "\n".join(
        f"{block['text']} {' '.join(block['attrs'].values())}".lower()
        for block in advanced_blocks
        if "open" not in block["attrs"]
    )
    for token in ("latitude", "longitude", "timezone"):
        assert token in advanced_text, f"LITE_FORM_ADVANCED_{token.upper()}_NOT_COLLAPSED"
    assert "engine" in advanced_text or "advanced" in advanced_text or "การคำนวณ" in advanced_text, (
        "LITE_FORM_ADVANCED_ENGINE_CONTROLS_NOT_COLLAPSED"
    )

    button_texts = [
        element["text"].strip()
        for element in parser.elements
        if element["tag"] == "button"
    ]
    assert any("คำนวณผังดวง & ตีความด้วย AI" in text for text in button_texts), (
        "LITE_FORM_PRIMARY_ACTION_TEXT_MISSING"
    )

    assert "/api/v3/unified-reading" in js, "LITE_JS_UNIFIED_READING_API_CALL_MISSING"
    forbidden_local_logic = {
        "calcFourPillars",
        "calculate_annual_timing",
        "calculateAnnualTiming",
        "generate_past_pattern_candidates",
    }
    for function_name in forbidden_local_logic:
        assert function_name not in js, f"LITE_JS_LOCAL_ASTROLOGY_LOGIC_DUPLICATED: {function_name}"
    assert not re.search(r"for\s*\([^)]*month[^)]*<=\s*12[^)]*\).*score", js, re.I | re.S), (
        "LITE_JS_DIRECT_MONTHLY_SCORING_LOOP_DETECTED"
    )

    css_lower = css.lower()
    has_focus_style = ":focus" in css_lower or ":focus-visible" in css_lower
    has_high_contrast_style = bool(
        re.search(r"color\s*:\s*#[0-9a-f]{3,6}", css_lower)
        and re.search(r"background(?:-color)?\s*:\s*#[0-9a-f]{3,6}", css_lower)
        and re.search(r"border(?:-color)?\s*:\s*#[0-9a-f]{3,6}", css_lower)
    )
    assert has_focus_style or has_high_contrast_style, (
        "LITE_CSS_ACCESSIBLE_FOCUS_OR_HIGH_CONTRAST_STYLE_MISSING"
    )


def test_lite_routes_and_assets_respond_200(monkeypatch: pytest.MonkeyPatch) -> None:
    import re
    from fastapi.testclient import TestClient

    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SKIP_FAISS_WARMUP", "true")

    from project.main import app

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
            assert response.status_code == 200, f"{endpoint}_HTTP_STATUS_NOT_200"
            content_type = response.headers.get("content-type", "")
            assert re.search(re.escape(expected_mime), content_type, re.I), (
                f"{endpoint}_CONTENT_TYPE_MISSING: {content_type}"
            )


def test_export_formats_and_privacy_default() -> None:
    export_js = (PUBLIC_DIR / "export_engine.js").read_text(encoding="utf-8")

    for name in (
        "exportFullPng",
        "exportStoryPng",
        "copySocialSummary",
        "printResult",
    ):
        assert f"async function {name}" in export_js or f"{name}(" in export_js, (
            f"EXPORT_ENGINE_MISSING_FUNCTION_{name}"
        )

    assert "window.horoLiteExport" in export_js, "EXPORT_ENGINE_NAMESPACE_MISSING"
    assert "includeBirthDetails" in export_js, "EXPORT_ENGINE_INCLUDE_BIRTH_OPTION_MISSING"
    assert "DEFAULT_COPY_TEXT" in export_js, "EXPORT_ENGINE_PRIVACY_MASKING_TOKEN_MISSING"
    assert "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว" in export_js, (
        "EXPORT_ENGINE_PRIVACY_COPY_TEXT_NOT_ENFORCED"
    )
