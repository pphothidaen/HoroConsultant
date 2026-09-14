"""Versioned schema contracts for Horo Lite unified readings."""

from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


SCHEMA_VERSION = "horo_lite_unified_reading.v1"

CANONICAL_TOPIC_IDS: tuple[str, ...] = (
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
)

ALLOWED_PAST_PATTERN_THEMES: frozenset[str] = frozenset(
    {
        "education",
        "career_shift",
        "relocation",
        "financial_pressure",
        "work_role_change",
    }
)

ALLOWED_FEEDBACK_CHOICES: tuple[str, ...] = (
    "ตรง",
    "ตรงบางส่วน",
    "ไม่ตรง",
    "จำไม่ได้",
)


class UnifiedReadingRequest(BaseModel):
    """Input contract for Horo Lite unified annual reading generation."""

    birth_date: date
    birth_time: time | None = None
    unknown_hour: bool = False
    birth_place: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timezone: str
    gender_at_birth: str | None = None
    target_year: int = Field(..., ge=1900, le=2200)
    locale: str = "th-TH"
    display_name: str | None = None
    primary_focus_question: str | None = None
    force_human_review: bool = False

    @model_validator(mode="after")
    def validate_birth_target_year_relationship(self) -> "UnifiedReadingRequest":
        """Reject nonsensical birth_date / target_year combinations.

        - birth_date in the future relative to target_year is invalid.
        - target_year before birth_year is invalid.
        These produce the young-person contract: children too young for
        past-pattern analysis receive an empty past_patterns list instead
        of an HTTP 500.
        """
        if self.birth_date.year > self.target_year:
            raise ValueError(
                f"birth_date year ({self.birth_date.year}) must not be after "
                f"target_year ({self.target_year})"
            )
        return self


class TopicModule(BaseModel):
    """Canonical topic block within a unified reading response."""

    topic_id: str
    order: int = Field(..., ge=1, le=12)
    title: str
    summary: str
    guidance: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    evidence_refs: list[str] = Field(..., min_length=1)


class MonthlyScoreItem(BaseModel):
    """Per-month user-facing scores with deterministic evidence basis.

    When ``unknown_hour`` is True, the ``*_score_range`` fields carry the
    uncertainty bounds and the single ``*_score`` fields contain the range
    midpoint for backward compatibility.
    """

    month: int = Field(..., ge=1, le=12)
    career_score: int = Field(..., ge=1, le=10)
    finance_score: int = Field(..., ge=1, le=10)
    love_score: int = Field(..., ge=1, le=10)
    career_score_range: list[int] | None = None
    finance_score_range: list[int] | None = None
    love_score_range: list[int] | None = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    score_basis: dict[str, Any] = Field(..., min_length=1)
    reasons: list[str] = Field(..., min_length=1)


class PastPatternCandidate(BaseModel):
    """Non-sensitive past event candidate for user calibration feedback."""

    pattern_id: str
    year_range: list[int] = Field(..., min_length=2, max_length=2)
    age_range: list[int] = Field(..., min_length=2, max_length=2)
    theme: str
    deterministic_basis: list[str] = Field(..., min_length=1)
    sensitive_category: bool = False
    allowed_feedback: list[str]
    user_feedback: str | None = None

    @model_validator(mode="after")
    def reject_sensitive_patterns(self) -> "PastPatternCandidate":
        if self.sensitive_category:
            raise ValueError("Sensitive past patterns are not allowed")
        if self.theme not in ALLOWED_PAST_PATTERN_THEMES:
            raise ValueError("Past pattern theme is outside the non-sensitive allowlist")
        if self.allowed_feedback != list(ALLOWED_FEEDBACK_CHOICES):
            raise ValueError("Past pattern feedback choices must match the contract")
        if self.user_feedback is not None and self.user_feedback not in ALLOWED_FEEDBACK_CHOICES:
            raise ValueError("Past pattern feedback value is not allowed")
        return self


class UnifiedReadingResponse(BaseModel):
    """Versioned unified reading response with compatibility guardrails."""

    schema_version: Literal["horo_lite_unified_reading.v1"] = SCHEMA_VERSION
    request_id: str
    target_year: int = Field(..., ge=1900, le=2200)
    topics: list[TopicModule] = Field(..., min_length=12, max_length=12)
    monthly_scores: list[MonthlyScoreItem] = Field(..., min_length=12, max_length=12)
    past_patterns: list[PastPatternCandidate] = Field(..., min_length=0, max_length=5)
    insufficient_history_reason: str | None = None
    consensus_metadata: dict[str, Any]
    hitl_flags: dict[str, Any]
    hitl_routing: dict[str, Any]
    llm_metadata: dict[str, Any]

    @field_validator("llm_metadata")
    @classmethod
    def preserve_llm_fact_immutability(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value.get("facts_mutable_by_llm") is not False:
            raise ValueError("LLM metadata must explicitly keep deterministic facts immutable")
        return value

    @model_validator(mode="after")
    def validate_response_contract(self) -> "UnifiedReadingResponse":
        topic_ids = tuple(topic.topic_id for topic in self.topics)
        if topic_ids != CANONICAL_TOPIC_IDS:
            raise ValueError("Topics must match the canonical order")

        topic_orders = [topic.order for topic in self.topics]
        if topic_orders != list(range(1, 13)):
            raise ValueError("Topic order must be exactly 1 through 12")

        months = [score.month for score in self.monthly_scores]
        if sorted(months) != list(range(1, 13)):
            raise ValueError("Monthly scores must contain exactly months 1 through 12")

        consensus_score = self.consensus_metadata.get("consensus_score")
        if not isinstance(consensus_score, int | float):
            raise ValueError("consensus_score must be numeric")
        if not 0 <= float(consensus_score) <= 1:
            raise ValueError("consensus_score must be between 0 and 1")

        conflict_detected = bool(
            self.hitl_flags.get("tradition_conflict")
            or self.hitl_flags.get("conflict_detected")
            or self.consensus_metadata.get("tradition_conflicts")
        )
        force_review = bool(self.hitl_flags.get("force_human_review"))
        uncertain_time = bool(self.hitl_flags.get("uncertain_birth_time"))
        low_consensus = bool(self.hitl_flags.get("low_consensus")) or float(consensus_score) < 0.75
        requires_review = conflict_detected or force_review or uncertain_time or low_consensus

        if requires_review and self.hitl_flags.get("required_human_review") is not True:
            raise ValueError("HITL review must be required when fail-closed flags are present")

        routing_status = self.hitl_routing.get("status")
        if requires_review and routing_status == "NOT_REQUIRED":
            raise ValueError("HITL routing cannot be NOT_REQUIRED when review is required")
        if not requires_review and routing_status != "NOT_REQUIRED":
            raise ValueError("HITL routing status must be NOT_REQUIRED when review is not required")

        return self
