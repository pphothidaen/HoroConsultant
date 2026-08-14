"""
project/tests/test_question_focus_router.py
============================================
Tests for Question-Focused Answering Router.
Verifies domain classification, prompt building, and metadata enrichment.
"""

import pytest
from project.core.question_focus_router import QuestionFocusRouter, DOMAIN_KEYWORDS, DOMAIN_ANALYSIS_GUIDES


@pytest.fixture
def router():
    return QuestionFocusRouter()


@pytest.fixture
def sample_chart():
    return {
        "day_master": {"stem": "壬", "element": "Water", "polarity": "Yang"},
        "five_elements": {
            "scores": {"Wood": 18.0, "Fire": 12.0, "Earth": 24.5, "Metal": 9.0, "Water": 21.0},
            "percentages": {"Wood": 21.4, "Fire": 14.3, "Earth": 29.2, "Metal": 10.7, "Water": 25.0},
            "dominant_element": "Earth",
            "weakest_element": "Metal",
        },
        "pillars": {
            "year": {"stem": {"char": "庚"}, "branch": {"char": "午"}},
            "month": {"stem": {"char": "辛"}, "branch": {"char": "巳"}},
            "day": {"stem": {"char": "壬"}, "branch": {"char": "寅"}},
            "hour": {"stem": {"char": "丙"}, "branch": {"char": "午"}},
        },
    }


# --- Classification Tests ---

class TestQuestionClassification:
    def test_career_chinese_keywords(self, router):
        """Career domain detected from Chinese astrological terms."""
        category, confidence = router.classify_question("今年的官星如何？能升职吗？")
        assert category == "career"
        assert confidence > 0.0

    def test_career_thai_keywords(self, router):
        """Career domain detected from Thai keywords."""
        category, confidence = router.classify_question("ในปี 2026 ควรย้ายงานหรือเปิดธุรกิจดี")
        assert category == "career"
        assert confidence > 0.0

    def test_career_english_keywords(self, router):
        """Career domain detected from English keywords."""
        category, confidence = router.classify_question("Should I change my career or start a business?")
        assert category == "career"
        assert confidence > 0.0

    def test_finance_keywords(self, router):
        """Finance domain detected from wealth-related terms."""
        category, _ = router.classify_question("การเงินในปีนี้มีเกณฑ์โชคลาภหรือไม่")
        assert category == "finance"

    def test_finance_chinese(self, router):
        """Finance domain from Chinese terms."""
        category, _ = router.classify_question("偏財运如何？有劫財的风险吗？")
        assert category == "finance"

    def test_love_keywords(self, router):
        """Love domain detected from relationship terms."""
        category, _ = router.classify_question("ดวงความรักปีนี้จะเจอคู่ครองไหม")
        assert category == "love"

    def test_love_compatibility(self, router):
        """Love domain from compatibility question."""
        category, _ = router.classify_question("Is this person compatible with me for marriage?")
        assert category == "love"

    def test_health_keywords(self, router):
        """Health domain detected from health-related terms."""
        category, _ = router.classify_question("มีเกณฑ์เจ็บป่วยหนักไหมปีนี้")
        assert category == "health"

    def test_family_keywords(self, router):
        """Family domain detected from family terms."""
        category, _ = router.classify_question("ดวงบุตรจะมีลูกเมื่อไหร่")
        assert category == "family"

    def test_timing_keywords(self, router):
        """Timing domain detected from date selection terms."""
        category, _ = router.classify_question("วันไหนเป็นฤกษ์ดี เลือกวันดีให้หน่อย")
        assert category == "timing"

    def test_general_no_match(self, router):
        """General category returned when no domain matches."""
        category, confidence = router.classify_question("Tell me about my chart")
        assert category == "general"
        assert confidence == 0.0

    def test_empty_query(self, router):
        """Empty query returns general with zero confidence."""
        category, confidence = router.classify_question("")
        assert category == "general"
        assert confidence == 0.0

    def test_none_query(self, router):
        """None query returns general with zero confidence."""
        category, confidence = router.classify_question(None)
        assert category == "general"
        assert confidence == 0.0

    def test_chinese_keywords_higher_weight(self, router):
        """Chinese keywords should have higher weight than English."""
        # Question with both career and finance terms, but finance has Chinese terms
        cat_cn, conf_cn = router.classify_question("偏財和正財 career job")
        assert cat_cn == "finance"  # Chinese finance terms should dominate

    def test_confidence_score_range(self, router):
        """Confidence score should be between 0 and 1."""
        _, confidence = router.classify_question("ย้ายงานเปิดธุรกิจ career promotion")
        assert 0.0 <= confidence <= 1.0


# --- Analysis Guide Tests ---

class TestAnalysisGuide:
    def test_career_guide_has_bazi(self, router):
        guide = router.get_analysis_guide("career")
        assert "bazi" in guide
        assert "官星" in guide["bazi"]

    def test_career_guide_has_guidance(self, router):
        guide = router.get_analysis_guide("career")
        assert "guidance" in guide

    def test_finance_guide_has_uranian(self, router):
        guide = router.get_analysis_guide("finance")
        assert "uranian" in guide

    def test_love_guide_has_iching(self, router):
        guide = router.get_analysis_guide("love")
        assert "iching" in guide

    def test_health_guide_has_organ_mapping(self, router):
        guide = router.get_analysis_guide("health")
        assert "liver" in guide["bazi"].lower() or "Wood" in guide["bazi"]

    def test_timing_guide_has_zeji(self, router):
        guide = router.get_analysis_guide("timing")
        assert "zeji" in guide

    def test_general_guide_fallback(self, router):
        guide = router.get_analysis_guide("unknown_domain")
        assert "guidance" in guide


# --- Citation Tests ---

class TestCitations:
    def test_career_citations(self, router):
        citations = router.get_citation_references("career")
        assert len(citations) >= 2
        assert any("滴天髓" in c for c in citations)

    def test_love_citations(self, router):
        citations = router.get_citation_references("love")
        assert len(citations) >= 2

    def test_unknown_domain_default_citations(self, router):
        citations = router.get_citation_references("nonexistent")
        assert len(citations) >= 2


# --- Prompt Building Tests ---

class TestPromptBuilding:
    def test_prompt_contains_user_question(self, router, sample_chart):
        query = "ควรย้ายงานไหม"
        prompt = router.build_focused_prompt("career", sample_chart, query)
        assert query in prompt

    def test_prompt_contains_day_master(self, router, sample_chart):
        prompt = router.build_focused_prompt("career", sample_chart, "test", language="en")
        assert "壬" in prompt
        assert "Water" in prompt

    def test_prompt_contains_domain_label(self, router, sample_chart):
        prompt = router.build_focused_prompt("finance", sample_chart, "test")
        assert "FINANCE" in prompt

    def test_prompt_contains_forbidden_section(self, router, sample_chart):
        prompt = router.build_focused_prompt("career", sample_chart, "test")
        assert "FORBIDDEN" in prompt
        assert "generic" in prompt.lower()

    def test_prompt_thai_language(self, router, sample_chart):
        prompt = router.build_focused_prompt("career", sample_chart, "test", language="th")
        assert "ภาษาไทย" in prompt

    def test_prompt_english_language(self, router, sample_chart):
        prompt = router.build_focused_prompt("career", sample_chart, "test", language="en")
        assert "English" in prompt

    def test_prompt_contains_citations(self, router, sample_chart):
        prompt = router.build_focused_prompt("career", sample_chart, "test")
        assert "滴天髓" in prompt


# --- Metadata Enrichment Tests ---

class TestMetadataEnrichment:
    def test_metadata_structure(self, router):
        meta = router.enrich_response_metadata("career", 0.85, "response text")
        assert "question_focus" in meta
        assert meta["question_focus"]["category"] == "career"
        assert meta["question_focus"]["confidence"] == 0.85

    def test_metadata_engines_consulted(self, router):
        meta = router.enrich_response_metadata("career", 0.9, "test")
        engines = meta["question_focus"]["engines_consulted"]
        assert "bazi" in engines
        assert "guidance" not in engines  # guidance is not an engine

    def test_metadata_citation_coverage_hit(self, router):
        meta = router.enrich_response_metadata("career", 0.9, "滴天髓 analysis shows...")
        assert "1/" in meta["question_focus"]["citation_coverage"]

    def test_metadata_citation_coverage_miss(self, router):
        meta = router.enrich_response_metadata("career", 0.9, "no citations here")
        assert meta["question_focus"]["citation_coverage"].startswith("0/")


# --- Domain Coverage Tests ---

class TestDomainCoverage:
    def test_all_six_domains_have_keywords(self):
        expected_domains = {"career", "finance", "love", "health", "family", "timing"}
        assert expected_domains == set(DOMAIN_KEYWORDS.keys())

    def test_all_six_domains_have_guides(self):
        expected_domains = {"career", "finance", "love", "health", "family", "timing"}
        assert expected_domains == set(DOMAIN_ANALYSIS_GUIDES.keys())

    def test_each_guide_has_guidance_key(self):
        for domain, guide in DOMAIN_ANALYSIS_GUIDES.items():
            assert "guidance" in guide, f"Domain '{domain}' missing 'guidance' key"

    def test_each_domain_has_at_least_5_keywords(self):
        for domain, keywords in DOMAIN_KEYWORDS.items():
            assert len(keywords) >= 5, f"Domain '{domain}' has only {len(keywords)} keywords"
