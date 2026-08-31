"""
project/schemas/dataset_schema_v1.py — ShareGPT, Fine-Tuning & Evaluation Schemas v1.0
======================================================================================
Comprehensive Pydantic schemas and serialization utilities for:
1. ShareGPT JSONL format (multi-turn conversational training data with audit metadata)
2. Fine-Tuning Q&A Pairs (CoT reasoning, classical treatise citations, domain alignment)
3. 100-pt Metaphysics Validation Rubric entries & 6-Domain Benchmark Evaluation reports

Pure ASCII logging and RFC-compliant JSONL serialization.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# Enums for Dataset Domains & Roles
# ==============================================================================

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"
    OBSERVATION = "observation"


class BenchmarkDomain(str, Enum):
    CAREER = "career"
    FINANCE = "finance"
    LOVE = "love"
    HEALTH = "health"
    FAMILY = "family"
    TIMING = "timing"


class RubricEvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    FLAGGED = "FLAGGED_FOR_REVIEW"


# ==============================================================================
# 1. ShareGPT JSONL Dataset Schemas
# ==============================================================================

class ShareGPTMessage(BaseModel):
    """Single message turn in ShareGPT conversation format."""
    role: MessageRole = Field(..., description="Role of the speaker: system, user, assistant, function, tool")
    content: str = Field(..., min_length=1, description="Textual body content of the message")
    name: Optional[str] = Field(None, description="Optional name identifier for tool or persona")

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @classmethod
    def create(cls, role: Union[str, MessageRole], content: str, name: Optional[str] = None) -> "ShareGPTMessage":
        role_enum = MessageRole(role) if isinstance(role, str) else role
        return cls(role=role_enum, content=content, name=name)


class ShareGPTMetadata(BaseModel):
    """Provenance and Human-in-the-Loop audit metadata attached to ShareGPT entries."""
    item_id: str = Field(..., description="Unique dataset item identifier")
    source_domain: str = Field(..., description="Originating domain or school (e.g. 'BaZi Four Pillars', 'Qi Men Dun Jia')")
    source_id: Optional[str] = Field(None, description="Classical source code (e.g. 'CM-BZ-004')")
    source_title: Optional[str] = Field(None, description="Title of classical treatise or corpus document")
    category: str = Field("chinese_metaphysics", description="Super-category of knowledge")
    question: Optional[str] = Field(None, description="Extracted user question")
    required_human_review: bool = Field(False, description="Whether item required HITL review")
    conflict_detected: bool = Field(False, description="Whether multi-agent debate detected cross-branch conflict")
    conflicting_domains: List[str] = Field(default_factory=list, description="List of conflicting master branches")
    consensus_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Consensus score from 8-Master debate")
    hitl_routing: Optional[Dict[str, Any]] = Field(None, description="HITL routing snapshot")
    decision: Optional[str] = Field("approve", description="Review decision: 'approve', 'refine', 'reject'")
    reviewer: Optional[str] = Field("QA_Tester", description="Reviewer persona or agent ID")
    confidence_rating: Optional[int] = Field(5, ge=1, le=5, description="Expert confidence rating 1-5")
    tags: List[str] = Field(default_factory=list, description="Custom searchable metadata tags")
    notes: Optional[str] = Field(None, description="Reviewer or curator notes")
    reviewed_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    pipeline: Optional[str] = Field("hitl_router", description="Originating ingestion pipeline")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ShareGPTConversationEntry(BaseModel):
    """Root entry representing one multi-turn conversation line in ShareGPT JSONL."""
    messages: List[ShareGPTMessage] = Field(
        ...,
        min_length=2,
        description="Sequential list of conversation turns (minimum user + assistant)"
    )
    meta: Optional[ShareGPTMetadata] = Field(
        default=None,
        alias="_meta",
        description="Optional provenance and audit metadata (serialized as '_meta')"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def to_jsonl_dict(self) -> Dict[str, Any]:
        """Serialize into clean dictionary compatible with ShareGPT JSONL format."""
        data: Dict[str, Any] = {
            "messages": [msg.model_dump(exclude_none=True) for msg in self.messages]
        }
        if self.meta is not None:
            data["_meta"] = self.meta.model_dump(exclude_none=True)
        return data

    def to_jsonl_line(self) -> str:
        """Convert single entry to a one-line JSON string."""
        return json.dumps(self.to_jsonl_dict(), ensure_ascii=False)


class ShareGPTDataset(BaseModel):
    """Collection wrapper for ShareGPT JSONL datasets with batch I/O and validation."""
    entries: List[ShareGPTConversationEntry] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def append(self, entry: ShareGPTConversationEntry) -> None:
        self.entries.append(entry)

    def to_jsonl_string(self) -> str:
        """Serialize all entries into multi-line JSONL text."""
        return "\n".join(entry.to_jsonl_line() for entry in self.entries) + ("\n" if self.entries else "")

    def save_to_file(self, filepath: Union[str, Path]) -> int:
        """Save dataset to a JSONL file. Returns number of entries written."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_jsonl_string()
        path.write_text(content, encoding="utf-8")
        return len(self.entries)

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> "ShareGPTDataset":
        """Load and parse dataset from a JSONL file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"ShareGPT JSONL file not found: {filepath}")
        
        entries: List[ShareGPTConversationEntry] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                entry = ShareGPTConversationEntry.model_validate(raw)
                entries.append(entry)
        return cls(entries=entries)


# ==============================================================================
# 2. Fine-Tuning Q&A Pairs Schemas
# ==============================================================================

class FineTuningQAPair(BaseModel):
    """Structured high-quality Q&A pair for supervised fine-tuning (SFT)."""
    id: str = Field(..., description="Unique Q&A sample identifier (e.g. 'FT-CAREER-001')")
    domain: BenchmarkDomain = Field(..., description="Target question domain (career, finance, love, health, family, timing)")
    system_prompt: str = Field(
        ...,
        description="System instruction defining master persona, domain authority, and analysis guidelines"
    )
    user_query: str = Field(..., min_length=5, description="Realistic natural language user question")
    context_chart_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured chart calculation payload (e.g. BaZi pillars, Zi Wei palaces, Qi Men matrix)"
    )
    canonical_citations: List[str] = Field(
        default_factory=list,
        description="Classical canonical texts cited (e.g. ['滴天髓', '子平真詮', '協紀辨方書'])"
    )
    master_interpretations: Dict[str, str] = Field(
        default_factory=dict,
        description="Individual perspectives from relevant domain masters"
    )
    ground_truth_synthesis: str = Field(
        ...,
        min_length=20,
        description="Expert synthesized interpretation directly answering user query with evidence"
    )
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="Chain-of-Thought (CoT) analytical calculation steps"
    )
    actionable_recommendations: List[str] = Field(
        default_factory=list,
        description="Concrete, practical, and non-fatalistic remedies or action items"
    )
    favorable_elements: List[str] = Field(default_factory=list, description="Favorable Five Elements (用神/喜神)")
    unfavorable_elements: List[str] = Field(default_factory=list, description="Unfavorable Five Elements (忌神/仇神)")
    auspicious_directions: List[str] = Field(default_factory=list, description="Auspicious directions (e.g. ['South', 'East'])")
    language: Literal["th", "en", "zh"] = Field("th", description="Primary language of the Q&A pair")
    quality_score: float = Field(100.0, ge=0.0, le=100.0, description="Curator quality score")
    verified_by_master: bool = Field(True, description="Whether sample has passed expert validation")

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def to_sharegpt_entry(self) -> ShareGPTConversationEntry:
        """Convert Fine-Tuning Q&A pair into ShareGPT format for model training."""
        messages = [
            ShareGPTMessage.create("system", self.system_prompt),
            ShareGPTMessage.create("user", self.user_query),
            ShareGPTMessage.create("assistant", self.ground_truth_synthesis)
        ]
        meta = ShareGPTMetadata(
            item_id=self.id,
            source_domain=f"Domain Benchmark: {self.domain.value}",
            source_id=self.id,
            source_title=", ".join(self.canonical_citations) if self.canonical_citations else "Metaphysics Golden Corpus",
            category="domain_benchmark_finetune",
            question=self.user_query,
            required_human_review=False,
            conflict_detected=False,
            confidence_rating=5,
            tags=[self.domain.value, self.language] + self.canonical_citations,
            notes=f"Quality score: {self.quality_score}"
        )
        return ShareGPTConversationEntry(messages=messages, _meta=meta)


class FineTuningDataset(BaseModel):
    """Collection of structured fine-tuning Q&A pairs."""
    name: str = Field("HoroConsultant-Metaphysics-SFT-v1")
    version: str = Field("1.0.0")
    pairs: List[FineTuningQAPair] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    def __len__(self) -> int:
        return len(self.pairs)

    def to_sharegpt_dataset(self) -> ShareGPTDataset:
        """Convert entire collection of Q&A pairs into a ShareGPTDataset."""
        entries = [pair.to_sharegpt_entry() for pair in self.pairs]
        return ShareGPTDataset(entries=entries)


# ==============================================================================
# 3. 100-Point Metaphysics Validation Rubric Schemas
# ==============================================================================

class RubricScoreBreakdown(BaseModel):
    """
    Standard 100-Point Evaluation Rubric across 4 core pillars:
    - Direct Relevance: 30 pts (directly answers core user question)
    - Astrological Logic: 30 pts (element balance, stems/branches, star math)
    - Canonical Evidence: 20 pts (treatise citations from verified corpus)
    - Actionable Guidance: 20 pts (concrete, realistic, non-fatalistic remedies)
    Total = 100.0 points maximum.
    """
    direct_relevance: float = Field(
        ...,
        ge=0.0,
        le=30.0,
        description="Direct question answering relevance score (0 - 30 pts)"
    )
    astrological_logic: float = Field(
        ...,
        ge=0.0,
        le=30.0,
        description="Mathematical & theoretical logic consistency (0 - 30 pts)"
    )
    canonical_evidence: float = Field(
        ...,
        ge=0.0,
        le=20.0,
        description="Classical treatise citation quality (0 - 20 pts)"
    )
    actionable_guidance: float = Field(
        ...,
        ge=0.0,
        le=20.0,
        description="Actionable, practical guidance without fatalism (0 - 20 pts)"
    )

    model_config = ConfigDict(extra="allow")

    @property
    def total_score(self) -> float:
        """Calculates total score (sum of all 4 pillars)."""
        return round(
            self.direct_relevance + self.astrological_logic + self.canonical_evidence + self.actionable_guidance,
            2
        )

    def is_passing(self, threshold: float = 80.0) -> bool:
        """Check if score meets or exceeds passing threshold (default 80.0 pts)."""
        return self.total_score >= threshold


class ValidationRubricEntry(BaseModel):
    """Single benchmark evaluation test case outcome scored against the 100-pt rubric."""
    id: str = Field(..., description="Test case identifier (e.g. 'career_1.1')")
    expected_domain: BenchmarkDomain = Field(..., description="Ground-truth expected domain")
    classified_domain: BenchmarkDomain = Field(..., description="Domain assigned by QuestionFocusRouter")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Router confidence score")
    domain_match: bool = Field(..., description="Whether classified domain matches expected domain")
    domain_match_en: bool = Field(True, description="English localization match confirmation")
    rubric_scores: RubricScoreBreakdown = Field(..., description="Detailed 4-pillar score breakdown")
    total_score: float = Field(..., ge=0.0, le=100.0, description="Total score out of 100.0")
    status: RubricEvaluationStatus = Field(RubricEvaluationStatus.PASS, description="Pass/Fail/Flagged verdict")
    reviewer: str = Field("QA_Benchmark_Runner", description="Auditor identity")
    evaluation_notes: Optional[str] = Field(None, description="Observations or suggestions for improvement")

    model_config = ConfigDict(extra="allow")

    @field_validator("total_score", mode="before")
    @classmethod
    def compute_or_validate_total(cls, v: Any, info: Any) -> float:
        return float(v)


class DomainBenchmarkSummary(BaseModel):
    """Aggregated benchmark metrics for a single question domain."""
    domain: BenchmarkDomain
    total_questions: int = Field(..., ge=0)
    passed_questions: int = Field(..., ge=0)
    pass_rate_percentage: float = Field(..., ge=0.0, le=100.0)
    average_score: float = Field(..., ge=0.0, le=100.0)
    results: List[ValidationRubricEntry] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class BenchmarkEvaluationReport(BaseModel):
    """Top-level 6-Domain Question Alignment Benchmark Report."""
    benchmark_name: str = Field("6-Domain Question Alignment Benchmark")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_questions: int = Field(..., ge=0)
    passed_questions: int = Field(..., ge=0)
    pass_rate_percentage: float = Field(..., ge=0.0, le=100.0)
    overall_average_score: float = Field(..., ge=0.0, le=100.0)
    domain_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Average score per domain: career, finance, love, health, family, timing"
    )
    domain_results: Dict[str, List[ValidationRubricEntry]] = Field(
        default_factory=dict,
        description="Granular evaluation entries grouped by domain"
    )
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    def to_report_dict(self) -> Dict[str, Any]:
        """Serialize into dictionary suitable for JSON report export."""
        return self.model_dump(mode="json")
