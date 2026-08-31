"""
project/tests/test_meta_plan_003_m2_dataset.py
==============================================
Sprint META-PLAN-003: Milestone M2 QA Verification Test Suite.

Comprehensive verification for:
1. ShareGPT JSONL Dataset Schemas & RFC Compliance:
   - Message roles (system, user, assistant, function, tool, observation)
   - ShareGPT metadata, provenance, HITL routing, and audit schemas
   - Entry serialization (to_jsonl_dict, to_jsonl_line, to_jsonl_string, batch save/load)
2. Fine-Tuning Q&A Pair Formulation & SFT Pipeline:
   - CoT reasoning, classical treatise citations, domain alignment
   - Conversion to canonical ShareGPT training entries
3. 100-Point Metaphysics Validation Rubric Calculation:
   - 4 Core Pillars: Direct Relevance (30 pts), Astrological Logic (30 pts),
     Canonical Evidence (20 pts), Actionable Guidance (20 pts)
   - Score boundaries, passing threshold evaluation (>= 80.0 pts)
4. Golden Corpus Integrity across all 16 Disciplines & 6 Domains:
   - Verification of `project/data/domain_benchmark_dataset_v3.json`
   - Zero empty responses, canonical citation presence across all 16 disciplines
   - 6-Domain coverage (career, finance, love, health, family, timing)
5. MLX & HuggingFace Harvester Normalization Logic:
   - Normalization of Alpaca, ShareGPT, ChatML, and term-definition formats
   - Deduplication and deterministic dataset formatting

Pure ASCII logging and 100% deterministic test assertions.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project.schemas.dataset_schema_v1 import (
    BenchmarkDomain,
    BenchmarkEvaluationReport,
    DomainBenchmarkSummary,
    FineTuningDataset,
    FineTuningQAPair,
    MessageRole,
    RubricEvaluationStatus,
    RubricScoreBreakdown,
    ShareGPTConversationEntry,
    ShareGPTDataset,
    ShareGPTMessage,
    ShareGPTMetadata,
    ValidationRubricEntry,
)
from scripts.extract_dataset_mlx import (
    SYSTEM_PROMPT as MLX_SYSTEM_PROMPT,
    _chart_to_instruction,
    _chart_to_response,
    build_sharegpt_entry,
)
from scripts.harvest_hf_liked_datasets import (
    SYSTEM_PROMPT as HARVEST_SYSTEM_PROMPT,
    normalize_row_to_chatml,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_m2_dataset")


# ==============================================================================
# 1. ShareGPT JSONL Dataset Schema Tests
# ==============================================================================

class TestShareGPTSchemaContracts:
    """Verifies Pydantic validation, serialization, and deserialization for ShareGPT format."""

    def test_message_role_enum_and_creation(self):
        """Verify MessageRole enum values and ShareGPTMessage factory creation."""
        roles = [MessageRole.SYSTEM, MessageRole.USER, MessageRole.ASSISTANT, MessageRole.FUNCTION, MessageRole.TOOL, MessageRole.OBSERVATION]
        assert len(roles) == 6

        msg_sys = ShareGPTMessage.create("system", "You are a master consultant.")
        assert msg_sys.role == MessageRole.SYSTEM
        assert msg_sys.content == "You are a master consultant."
        assert msg_sys.name is None

        msg_user = ShareGPTMessage.create(MessageRole.USER, "What is my Day Master?", name="Seeker")
        assert msg_user.role == MessageRole.USER
        assert msg_user.content == "What is my Day Master?"
        assert msg_user.name == "Seeker"

    def test_message_validation_rejects_empty_content(self):
        """Verify ShareGPTMessage rejects empty or whitespace-only content."""
        with pytest.raises(ValidationError):
            ShareGPTMessage(role=MessageRole.USER, content="")

    def test_metadata_schema_fields_and_defaults(self):
        """Verify ShareGPTMetadata captures complete provenance and HITL review details."""
        meta = ShareGPTMetadata(
            item_id="TEST-META-001",
            source_domain="BaZi Four Pillars",
            source_id="CM-BZ-001",
            source_title="Di Tian Sui",
            category="chinese_metaphysics",
            question="What is the strength of Jia Wood in Spring?",
            required_human_review=False,
            conflict_detected=False,
            consensus_score=0.95,
            decision="approve",
            reviewer="QA_Tester",
            confidence_rating=5,
            tags=["bazi", "jia_wood", "spring"],
        )
        assert meta.item_id == "TEST-META-001"
        assert meta.source_domain == "BaZi Four Pillars"
        assert meta.consensus_score == 0.95
        assert meta.confidence_rating == 5
        assert "bazi" in meta.tags

    def test_conversation_entry_serialization(self):
        """Verify ShareGPTConversationEntry serialized dictionary and JSONL line output."""
        messages = [
            ShareGPTMessage.create("system", "Metaphysics consultant assistant."),
            ShareGPTMessage.create("user", "Explain Gui Water in Winter."),
            ShareGPTMessage.create("assistant", "Gui Water in Winter is at its peak strength (Wang 旺)."),
        ]
        meta = ShareGPTMetadata(
            item_id="CONV-001",
            source_domain="BaZi",
            category="chinese_metaphysics",
        )
        entry = ShareGPTConversationEntry(messages=messages, _meta=meta)

        # Dictionary format
        data_dict = entry.to_jsonl_dict()
        assert "messages" in data_dict
        assert len(data_dict["messages"]) == 3
        assert data_dict["messages"][0]["role"] == "system"
        assert data_dict["messages"][1]["role"] == "user"
        assert data_dict["messages"][2]["role"] == "assistant"
        assert "_meta" in data_dict
        assert data_dict["_meta"]["item_id"] == "CONV-001"

        # JSONL single line serialization
        line = entry.to_jsonl_line()
        assert isinstance(line, str)
        assert "\n" not in line
        parsed = json.loads(line)
        assert parsed["_meta"]["source_domain"] == "BaZi"

    def test_sharegpt_dataset_batch_save_and_load(self):
        """Verify ShareGPTDataset batch appending, JSONL file saving, and file loading."""
        dataset = ShareGPTDataset()
        for i in range(5):
            entry = ShareGPTConversationEntry(
                messages=[
                    ShareGPTMessage.create("system", "Test System Prompt"),
                    ShareGPTMessage.create("user", f"Test query number {i+1}"),
                    ShareGPTMessage.create("assistant", f"Deterministic response for {i+1}"),
                ],
                _meta=ShareGPTMetadata(item_id=f"ITEM-{i+1}", source_domain="TestDomain"),
            )
            dataset.append(entry)

        assert len(dataset) == 5

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            written_count = dataset.save_to_file(tmp_path)
            assert written_count == 5
            assert tmp_path.exists()

            # Load back from file
            loaded_dataset = ShareGPTDataset.load_from_file(tmp_path)
            assert len(loaded_dataset) == 5
            assert loaded_dataset.entries[0].messages[1].content == "Test query number 1"
            assert loaded_dataset.entries[4].messages[2].content == "Deterministic response for 5"
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


# ==============================================================================
# 2. Fine-Tuning Q&A Pairs & SFT Dataset Schemas
# ==============================================================================

class TestFineTuningQAPairContracts:
    """Verifies FineTuningQAPair structure and conversion to ShareGPT entries."""

    @pytest.fixture
    def sample_qa_pair(self) -> FineTuningQAPair:
        return FineTuningQAPair(
            id="FT-CAREER-001",
            domain=BenchmarkDomain.CAREER,
            system_prompt="You are an expert BaZi and Chinese Metaphysics consultant.",
            user_query="How does Yang Wood (Jia) perform in You Rooster Autumn month?",
            context_chart_data={
                "day_master": {"stem": "甲", "element": "Wood"},
                "month_pillar": {"stem": "癸", "branch": "酉"},
            },
            canonical_citations=["滴天髓 (Di Tian Sui)", "子平真詮 (Zi Ping Zhen Quan)"],
            master_interpretations={
                "bazi_master": "Jia Wood in Autumn needs Gui Water Seal to transform Qi Sha Metal.",
                "ziwei_master": "Tian Fu in Career Palace signifies solid institutional executive power.",
            },
            ground_truth_synthesis=(
                "Day Master Jia Wood in You month is weak in season, but Gui Water provides the "
                "essential Officer-Transforms-Into-Seal (官印相生) bridge, granting strong organizational leadership."
            ),
            reasoning_steps=[
                "1. Identify Day Master Jia Wood in resting Autumn season.",
                "2. Assess Month Stem Gui Water serving as Direct Seal (Zheng Yin).",
                "3. Conclude officer pressure is transmuted into executive authority.",
            ],
            actionable_recommendations=[
                "Target executive director or organizational management roles in Q2-Q3.",
                "Avoid uncalculated speculative startup ventures without institutional backing.",
            ],
            favorable_elements=["Water", "Wood"],
            unfavorable_elements=["Excessive Metal", "Dry Earth"],
            auspicious_directions=["North", "East"],
            language="en",
            quality_score=98.5,
            verified_by_master=True,
        )

    def test_qa_pair_attributes_and_validation(self, sample_qa_pair: FineTuningQAPair):
        assert sample_qa_pair.id == "FT-CAREER-001"
        assert sample_qa_pair.domain == BenchmarkDomain.CAREER
        assert len(sample_qa_pair.canonical_citations) == 2
        assert len(sample_qa_pair.reasoning_steps) == 3
        assert len(sample_qa_pair.actionable_recommendations) == 2
        assert sample_qa_pair.quality_score == 98.5
        assert sample_qa_pair.verified_by_master is True

    def test_qa_pair_to_sharegpt_entry_conversion(self, sample_qa_pair: FineTuningQAPair):
        entry = sample_qa_pair.to_sharegpt_entry()
        assert isinstance(entry, ShareGPTConversationEntry)
        assert len(entry.messages) == 3
        assert entry.messages[0].role == MessageRole.SYSTEM
        assert entry.messages[0].content == sample_qa_pair.system_prompt
        assert entry.messages[1].role == MessageRole.USER
        assert entry.messages[1].content == sample_qa_pair.user_query
        assert entry.messages[2].role == MessageRole.ASSISTANT
        assert entry.messages[2].content == sample_qa_pair.ground_truth_synthesis

        assert entry.meta is not None
        assert entry.meta.item_id == "FT-CAREER-001"
        assert "Di Tian Sui" in entry.meta.source_title

    def test_fine_tuning_dataset_collection(self, sample_qa_pair: FineTuningQAPair):
        ft_dataset = FineTuningDataset(
            name="HoroConsultant-Metaphysics-SFT-v1",
            version="1.0.0",
            pairs=[sample_qa_pair],
        )
        assert len(ft_dataset) == 1
        sharegpt_ds = ft_dataset.to_sharegpt_dataset()
        assert len(sharegpt_ds) == 1
        assert sharegpt_ds.entries[0].messages[1].content == sample_qa_pair.user_query


# ==============================================================================
# 3. 100-Point Metaphysics Validation Rubric Schemas
# ==============================================================================

class TestValidationRubricContracts:
    """Verifies the standard 100-point rubric calculation and evaluation summaries."""

    def test_rubric_score_breakdown_calculation(self):
        """Verify 4 core pillars sum to total score and boundary constraints."""
        rubric = RubricScoreBreakdown(
            direct_relevance=28.5,     # max 30
            astrological_logic=29.0,   # max 30
            canonical_evidence=19.0,   # max 20
            actionable_guidance=18.5,  # max 20
        )
        assert rubric.total_score == 95.0
        assert rubric.is_passing(threshold=80.0) is True

    def test_rubric_failing_score(self):
        """Verify failing verdict when score is below passing threshold."""
        rubric_fail = RubricScoreBreakdown(
            direct_relevance=20.0,
            astrological_logic=20.0,
            canonical_evidence=10.0,
            actionable_guidance=15.0,
        )
        assert rubric_fail.total_score == 65.0
        assert rubric_fail.is_passing(threshold=80.0) is False

    def test_rubric_score_pillar_boundary_validation(self):
        """Verify ValidationError when pillar score exceeds its maximum limit."""
        with pytest.raises(ValidationError):
            # direct_relevance max is 30.0
            RubricScoreBreakdown(
                direct_relevance=35.0,
                astrological_logic=25.0,
                canonical_evidence=15.0,
                actionable_guidance=15.0,
            )

        with pytest.raises(ValidationError):
            # canonical_evidence max is 20.0
            RubricScoreBreakdown(
                direct_relevance=25.0,
                astrological_logic=25.0,
                canonical_evidence=25.0,
                actionable_guidance=15.0,
            )

    def test_validation_rubric_entry_and_domain_summary(self):
        """Verify ValidationRubricEntry and DomainBenchmarkSummary aggregation."""
        rubric = RubricScoreBreakdown(
            direct_relevance=30.0,
            astrological_logic=30.0,
            canonical_evidence=20.0,
            actionable_guidance=20.0,
        )
        entry = ValidationRubricEntry(
            id="career_1.1",
            expected_domain=BenchmarkDomain.CAREER,
            classified_domain=BenchmarkDomain.CAREER,
            confidence=0.98,
            domain_match=True,
            domain_match_en=True,
            rubric_scores=rubric,
            total_score=100.0,
            status=RubricEvaluationStatus.PASS,
            reviewer="QA_Benchmark_Runner",
        )
        assert entry.total_score == 100.0
        assert entry.domain_match is True

        summary = DomainBenchmarkSummary(
            domain=BenchmarkDomain.CAREER,
            total_questions=1,
            passed_questions=1,
            pass_rate_percentage=100.0,
            average_score=100.0,
            results=[entry],
        )
        assert summary.pass_rate_percentage == 100.0
        assert summary.passed_questions == 1

    def test_benchmark_evaluation_report_export(self):
        """Verify top-level 6-Domain BenchmarkEvaluationReport dictionary serialization."""
        report = BenchmarkEvaluationReport(
            benchmark_name="6-Domain Question Alignment Benchmark",
            total_questions=6,
            passed_questions=6,
            pass_rate_percentage=100.0,
            overall_average_score=96.5,
            domain_scores={
                "career": 98.0,
                "finance": 95.0,
                "love": 97.0,
                "health": 96.0,
                "family": 96.5,
                "timing": 96.5,
            },
            provenance_metadata={"git_commit": "20260831-sprint-meta-003", "environment": "test"},
        )
        report_dict = report.to_report_dict()
        assert report_dict["pass_rate_percentage"] == 100.0
        assert report_dict["overall_average_score"] == 96.5
        assert len(report_dict["domain_scores"]) == 6


# ==============================================================================
# 4. Golden Corpus Integrity across all 16 Disciplines & 6 Domains
# ==============================================================================

class TestDomainBenchmarkGoldenCorpusV3:
    """
    Validates `project/data/domain_benchmark_dataset_v3.json`:
    - Contains benchmark cases for all 16 classical metaphysics disciplines.
    - Covers all 6 consulting domains (career, finance, love, health, family, timing).
    - Every case contains canonical treatise citations with original text.
    - Zero empty question prompts or synthesis guidance fields.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def benchmark_data(cls) -> Dict[str, Any]:
        benchmark_file = ROOT_DIR / "project/data/domain_benchmark_dataset_v3.json"
        assert benchmark_file.exists(), f"Benchmark file missing: {benchmark_file}"
        with open(benchmark_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def test_benchmark_dataset_metadata(self, benchmark_data: Dict[str, Any]):
        """Verify benchmark version, taxonomy, and total cases."""
        assert benchmark_data["version"] == "3.0.0"
        assert benchmark_data["disciplines_count"] == 16
        assert benchmark_data["total_benchmark_cases"] >= 48
        assert len(benchmark_data["domain_taxonomy"]) == 6

        expected_domains = {"career", "finance", "love", "health", "family", "timing"}
        assert set(benchmark_data["domain_taxonomy"].keys()) == expected_domains

    def test_all_16_disciplines_present_in_benchmark(self, benchmark_data: Dict[str, Any]):
        """Verify benchmark cases cover all 16 metaphysics disciplines."""
        cases = benchmark_data["benchmark_cases"]
        disciplines_found = {c["discipline"].lower() for c in cases}

        expected_16_disciplines = {
            "bazi",
            "ziwei",
            "qimen",
            "liuren",
            "taiyi",
            "iching",
            "liuyao",
            "meihua",
            "xuankong",
            "sanhe",
            "zeji",
            "mianxiang",
            "thaivedic",
            "western",
            "numerology",
            "qizheng",
        }

        missing = expected_16_disciplines - disciplines_found
        assert len(missing) == 0, f"Missing disciplines in benchmark dataset: {missing}"

    def test_canonical_citations_presence_across_all_cases(self, benchmark_data: Dict[str, Any]):
        """Verify every benchmark case contains verified classical treatise citations."""
        cases = benchmark_data["benchmark_cases"]
        for idx, case in enumerate(cases):
            case_id = case.get("id", f"case_{idx}")
            citations = case.get("canonical_citations", [])
            assert isinstance(citations, list), f"Case {case_id} citations must be a list"
            assert len(citations) >= 1, f"Case {case_id} ({case.get('discipline')}) must have at least 1 classical citation"

            for cit in citations:
                assert "treatise" in cit and len(cit["treatise"].strip()) > 0, f"Case {case_id} citation missing treatise title"
                assert "original_text" in cit and len(cit["original_text"].strip()) > 0, f"Case {case_id} citation missing original text"

    def test_zero_empty_questions_and_responses(self, benchmark_data: Dict[str, Any]):
        """Verify zero empty question strings and synthesis responses across all cases."""
        cases = benchmark_data["benchmark_cases"]
        for idx, case in enumerate(cases):
            case_id = case.get("id", f"case_{idx}")
            question_dict = case.get("question", {})
            assert "question_th" in question_dict and len(question_dict["question_th"].strip()) > 10, f"Case {case_id} question_th empty"
            assert "question_en" in question_dict and len(question_dict["question_en"].strip()) > 10, f"Case {case_id} question_en empty"

            logic_dict = case.get("expected_astrological_logic", {})
            assert "synthesis" in logic_dict and len(logic_dict["synthesis"].strip()) > 10, f"Case {case_id} synthesis empty"
            assert "step_by_step_reasoning" in logic_dict and len(logic_dict["step_by_step_reasoning"]) > 0, f"Case {case_id} reasoning empty"

            guidance_dict = case.get("actionable_guidance", {})
            assert "strategic_actions" in guidance_dict and len(guidance_dict["strategic_actions"]) > 0, f"Case {case_id} strategic actions empty"

    def test_convert_benchmark_cases_to_sharegpt_format(self, benchmark_data: Dict[str, Any]):
        """Verify benchmark cases can be converted to valid ShareGPTConversationEntry objects."""
        cases = benchmark_data["benchmark_cases"]
        converted_entries: List[ShareGPTConversationEntry] = []

        for case in cases:
            messages = [
                ShareGPTMessage.create("system", f"You are a master consultant in {case['discipline_name_en']}."),
                ShareGPTMessage.create("user", case["question"]["question_en"]),
                ShareGPTMessage.create("assistant", case["expected_astrological_logic"]["synthesis"]),
            ]
            citations_list = [c["treatise"] for c in case.get("canonical_citations", [])]
            meta = ShareGPTMetadata(
                item_id=case["id"],
                source_domain=case["discipline_name_en"],
                source_title=", ".join(citations_list),
                category="metaphysics_benchmark_v3",
                question=case["question"]["question_en"],
                confidence_rating=5,
                tags=[case["discipline"], case["domain"]] + citations_list,
            )
            entry = ShareGPTConversationEntry(messages=messages, _meta=meta)
            converted_entries.append(entry)

        assert len(converted_entries) == len(cases)
        for entry in converted_entries:
            line = entry.to_jsonl_line()
            assert len(line) > 50
            parsed = json.loads(line)
            assert len(parsed["messages"]) == 3
            assert parsed["_meta"]["confidence_rating"] == 5


# ==============================================================================
# 5. MLX Fine-Tune & HuggingFace Harvester Normalizer Tests
# ==============================================================================

class TestDatasetExportersAndNormalizers:
    """Verifies MLX template extraction and HuggingFace harvester normalization."""

    def test_mlx_chart_to_instruction_and_response(self):
        """Verify MLX instruction and response generation from BaZi chart data."""
        mock_chart = {
            "solar_time_info": {
                "input_datetime": "1990-05-15 14:30:00",
                "longitude": 100.4930,
                "utc_offset_hours": 7.0,
            },
            "day_master": {
                "stem": "庚",
                "element": "Metal",
                "polarity": "Yang",
            },
            "five_elements": {
                "percentages": {"Wood": 20.0, "Fire": 30.0, "Earth": 20.0, "Metal": 15.0, "Water": 15.0},
                "dominant_element": "Fire",
                "weakest_element": "Metal",
            },
            "pillars": {
                "year": {"stem": {"char": "庚", "element": "Metal"}, "branch": {"char": "午", "element": "Fire"}},
                "month": {"stem": {"char": "辛", "element": "Metal"}, "branch": {"char": "巳", "element": "Fire"}},
                "day": {"stem": {"char": "庚", "element": "Metal"}, "branch": {"char": "辰", "element": "Earth"}},
                "hour": {"stem": {"char": "癸", "element": "Water"}, "branch": {"char": "未", "element": "Earth"}},
            },
        }

        instruction = _chart_to_instruction(mock_chart)
        assert "1990-05-15 14:30:00" in instruction
        assert "Day Master is 庚" in instruction

        response_str = _chart_to_response(mock_chart)
        resp_data = json.loads(response_str)
        assert "day_master_assessment" in resp_data
        assert "five_elements_breakdown" in resp_data
        assert "favourable_elements" in resp_data

        sharegpt_entry = build_sharegpt_entry(mock_chart)
        assert "conversations" in sharegpt_entry
        assert len(sharegpt_entry["conversations"]) == 3
        assert sharegpt_entry["conversations"][0]["role"] == "system"
        assert sharegpt_entry["conversations"][1]["role"] == "human"
        assert sharegpt_entry["conversations"][2]["role"] == "assistant"

    def test_harvester_normalize_alpaca_format(self):
        """Verify normalize_row_to_chatml converts Alpaca format (instruction, input, output)."""
        alpaca_row = {
            "instruction": "Explain the significance of the Wood Element in Spring.",
            "input": "Day Master is Jia Wood born in Yin Tiger month.",
            "output": "Wood is dominant and thriving during Spring season.",
        }
        res = normalize_row_to_chatml(alpaca_row)
        assert res is not None
        assert "messages" in res
        assert len(res["messages"]) == 3
        assert res["messages"][0]["role"] == "system"
        assert res["messages"][1]["role"] == "user"
        assert "Explain the significance" in res["messages"][1]["content"]
        assert "Context:" in res["messages"][1]["content"]
        assert res["messages"][2]["role"] == "assistant"
        assert "Wood is dominant" in res["messages"][2]["content"]

    def test_harvester_normalize_sharegpt_format(self):
        """Verify normalize_row_to_chatml converts ShareGPT conversations format."""
        sharegpt_row = {
            "conversations": [
                {"from": "human", "value": "How to interpret Seven Killings (Qi Sha)?"},
                {"from": "gpt", "value": "Seven Killings represents power, pressure, and authority."},
            ]
        }
        res = normalize_row_to_chatml(sharegpt_row)
        assert res is not None
        assert len(res["messages"]) == 3  # System prompt prepended
        assert res["messages"][0]["role"] == "system"
        assert res["messages"][1]["role"] == "user"
        assert res["messages"][2]["role"] == "assistant"

    def test_harvester_normalize_term_definition_format(self):
        """Verify normalize_row_to_chatml converts term/definition format."""
        term_row = {
            "term": "Ten Gods (十神)",
            "definition": "Ten Gods describe the relational dynamics between the Day Master and other stems/branches.",
        }
        res = normalize_row_to_chatml(term_row)
        assert res is not None
        assert len(res["messages"]) == 3
        assert "Explain the BaZi metaphysical concept of: Ten Gods (十神)" in res["messages"][1]["content"]

    def test_harvester_rejects_empty_row(self):
        """Verify normalize_row_to_chatml returns None for empty or invalid rows."""
        assert normalize_row_to_chatml({}) is None
        assert normalize_row_to_chatml({"dummy_key": "dummy_value"}) is None
