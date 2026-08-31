"""
project/tests/test_question_alignment_benchmark.py
===================================================
Sprint META-PLAN-002: Milestone M2 Benchmark Validation Test Suite.

Verifies:
1. 6-Domain Question NLP Classification accuracy (Thai, English, Chinese):
   - Career & Business Strategy (career)
   - Finance, Wealth & Investment (finance)
   - Love, Marriage & Partnership (love)
   - Health, Longevity & Accident Hazards (health)
   - Family, Offspring & Inheritance (family)
   - Auspicious Date Selection & Cosmic Cycles (timing)
2. Domain-focused prompt synthesis with multi-engine directives and citations.
3. Execution of `scripts/run_question_alignment_benchmark.py` asserting all 6 domains score >= 90/100.
4. Rubric scoring assertions and report provenance.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from project.core.bazi_engine import BaZiEngine
from project.core.question_focus_router import (
    QuestionFocusRouter,
    DOMAIN_KEYWORDS,
    DOMAIN_ANALYSIS_GUIDES,
    DOMAIN_CITATIONS,
)
from scripts.run_question_alignment_benchmark import (
    load_benchmark_dataset,
    evaluate_benchmark_question,
    run_question_alignment_benchmark,
)


class TestQuestionAlignment6DomainClassification:
    """Verifies precision of NLP intent routing across all 6 consulting domains."""

    @pytest.fixture
    def router(self):
        return QuestionFocusRouter()

    @pytest.fixture
    def sample_chart(self):
        engine = BaZiEngine()
        from datetime import datetime
        dt = datetime(1990, 5, 15, 14, 30)
        return engine.calculate(dt, 100.493, 7.0)

    @pytest.mark.parametrize("query,expected_domain", [
        # Domain 1: Career
        ("ในปี 2026 ควรย้ายงานหรือเปิดธุรกิจของตัวเองดี", "career"),
        ("มีโอกาสเลื่อนตำแหน่งหรือขึ้นเงินเดือนในปีนี้ไหม", "career"),
        ("In 2026, is it better to change jobs or start a startup?", "career"),
        ("Are there promotion opportunities in my current company?", "career"),
        ("今年官星與事業運勢如何？", "career"),

        # Domain 2: Finance
        ("การเงินในปีนี้มีเกณฑ์โชคลาภลอยหรือได้ทรัพย์ใหญ่ไหม", "finance"),
        ("มีจุดรั่วไหลของเงินหรือหนี้สินที่ต้องระวังไหม", "finance"),
        ("Is there windfall wealth or major investment return this year?", "finance"),
        ("Where are the financial leakage points in my chart?", "finance"),
        ("偏財運與正財收入如何？", "finance"),

        # Domain 3: Love
        ("ดวงสมพงษ์กับคู่ครองหรือหุ้นส่วนคนนี้หรือไม่", "love"),
        ("ความรักปีนี้จะมีเกณฑ์แต่งงานหรือขัดแย้งไหม", "love"),
        ("Is this new partner compatible with my natal chart?", "love"),
        ("Will there be marriage or relationship conflict this year?", "love"),
        ("夫妻宮桃花運與婚姻合不合？", "love"),

        # Domain 4: Health
        ("ดวงชะตามีเกณฑ์เจ็บป่วยหนัก เลือดตกยางออก หรือผ่าตัดไหม", "health"),
        ("สุขภาพในปีนี้มีอวัยวะส่วนไหนที่ต้องระวังเป็นพิเศษ", "health"),
        ("Is there risk of serious illness, surgery, or accidents this year?", "health"),
        ("Which organ systems have Five Elements deficiency?", "health"),
        ("疾厄宮與身體健康狀況如何？", "health"),

        # Domain 5: Family
        ("ดวงชะตามีเกณฑ์มีบุตรง่ายหรือยาก บุตรจะส่งเสริมพ่อแม่ไหม", "family"),
        ("ความสัมพันธ์ในครอบครัวและพี่น้องปีนี้ราบรื่นไหม", "family"),
        ("Does the chart indicate ease of having children and offspring?", "family"),
        ("Will children support parents and bring family harmony?", "family"),
        ("子女宮運勢與父母家庭和諧？", "family"),

        # Domain 6: Timing
        ("ช่วงเวลาหรือวันไหนในเดือนหน้าเหมาะแก่การเซ็นสัญญาเปิดบริษัท", "timing"),
        ("ฤกษ์ยามมงคลเปิดร้านใหม่หรือขึ้นบ้านใหม่วันไหนดีที่สุด", "timing"),
        ("Which dates next month are most auspicious for signing contracts?", "timing"),
        ("What is the best auspicious date selection for opening?", "timing"),
        ("擇吉日吉時與大運流年？", "timing"),
    ])
    def test_multi_lingual_6_domain_classification(self, router, query, expected_domain):
        domain, conf = router.classify_question(query)
        assert domain == expected_domain, f"Query '{query}' classified as '{domain}', expected '{expected_domain}'"
        assert conf > 0.0

    def test_domain_analysis_guides_coverage(self, router):
        """Verify each of the 6 domains has comprehensive multi-engine analysis guides."""
        domains = ["career", "finance", "love", "health", "family", "timing"]
        for d in domains:
            guide = router.get_analysis_guide(d)
            assert isinstance(guide, dict)
            assert "guidance" in guide
            assert len(guide) >= 3, f"Domain {d} must have at least 3 engine focus instructions"

    def test_domain_classical_citations_coverage(self, router):
        """Verify each of the 6 domains provides canonical classical treatise citations."""
        domains = ["career", "finance", "love", "health", "family", "timing"]
        for d in domains:
            citations = router.get_citation_references(d)
            assert isinstance(citations, list)
            assert len(citations) >= 2, f"Domain {d} must cite at least 2 classical treatises"

    def test_focused_prompt_structure_integrity(self, router, sample_chart):
        """Verify that generated prompts include required critical directives and sections."""
        query = "ปี 2026 ควรย้ายงานหรือเปิดธุรกิจของตัวเองดี"
        prompt = router.build_focused_prompt("career", sample_chart, query, language="th")
        assert "## FOCUSED ASTROLOGICAL CONSULTATION" in prompt
        assert "CRITICAL DIRECTIVE" in prompt
        assert "FORBIDDEN" in prompt
        assert "Citation Requirements:" in prompt
        assert "BAZI Analysis Focus:" in prompt
        assert "ZIWEI Analysis Focus:" in prompt


class TestBenchmarkRunnerSuite:
    """Verifies that running the benchmark runner produces >= 90/100 across all 6 domains."""

    def test_benchmark_dataset_integrity(self):
        dataset = load_benchmark_dataset()
        assert "version" in dataset
        assert "categories" in dataset
        assert len(dataset["categories"]) == 6

        domain_keys = [c["domain"] for c in dataset["categories"]]
        assert set(domain_keys) == {"career", "finance", "love", "health", "family", "timing"}

        for cat in dataset["categories"]:
            assert len(cat["questions"]) >= 1
            for q in cat["questions"]:
                assert "id" in q
                assert "question_th" in q
                assert "question_en" in q
                assert "expected_criteria" in q
                criteria = q["expected_criteria"]
                assert "direct_relevance" in criteria
                assert "astrological_logic" in criteria
                assert "canonical_citations" in criteria

    def test_benchmark_runner_execution_and_thresholds(self, tmp_path):
        report_file = tmp_path / "test_m2_benchmark_report.json"
        report_data = run_question_alignment_benchmark(report_path=report_file)

        assert report_data["total_questions"] >= 6
        assert report_data["passed_questions"] == report_data["total_questions"]
        assert report_data["pass_rate_percentage"] == 100.0
        assert report_data["overall_average_score"] >= 90.0

        # Assert every single domain achieved >= 90/100
        for domain, score in report_data["domain_scores"].items():
            assert score >= 90.0, f"Domain '{domain}' scored {score}/100 (< 90.0 threshold)"

        # Verify saved JSON report
        assert report_file.exists()
        with open(report_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["overall_average_score"] == report_data["overall_average_score"]
