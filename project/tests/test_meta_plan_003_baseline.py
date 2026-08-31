"""
project/tests/test_meta_plan_003_baseline.py
=============================================
Sprint META-PLAN-003: Milestone M0 Baseline Test Suite.

Comprehensive contract integrity and baseline functionality tests for:
1. 16 Core Metaphysics Engines:
   - San Shi (三式): Tai Yi, Da Liu Ren, Qi Men Dun Jia
   - Ming Xue (命學): BaZi, Zi Wei Dou Shu, Qi Zheng Si Yu
   - Pu Shi (卜筮): I Ching, Liu Yao, Mei Hua Yi Shu
   - Xiang Xue (相學): Xuan Kong Flying Stars, San He Feng Shui, Mian Xiang
   - Ze Ji (擇吉): Imperial Date Selection
   - Expanded Astrology & Numerology: Thai & Vedic, Western & Uranian, Numerology (Satta-Lek & Chaldean)
2. Multi-Engine Router & Debate Synthesizer:
   - Question Focus Router (6-domain classification, prompt building, citation references)
   - Multi-Agent Peer Debate & Consensus Matrix Engine (10-branch consensus synthesis)
3. RAG Vector Store & Retrieval Engine:
   - Vector Store backend, FAISS integration/fallback, Keyword Indexing, Chunking, Hybrid RRF Search
4. Determinism & Integrity Baseline Guard.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult, ElementScores, PillarData
from project.core.bazi_engine import BaZiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.tai_yi_engine import TaiYiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.san_he_engine import SanHeEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.question_focus_router import QuestionFocusRouter, DOMAIN_KEYWORDS, DOMAIN_ANALYSIS_GUIDES, DOMAIN_CITATIONS
from project.core.multi_agent_debate import MetaphysicsDebateEngine, CANONICAL_TEXTS
from project.rag.vector_store import (
    VectorStore,
    get_vector_store,
    _chunk_text,
    _KeywordIndex,
)


# All 16 core engines mapped to their respective classes and expected system types
CORE_ENGINES = [
    (BaZiEngine, "BaZi Engine", "ming_xue"),
    (ZiWeiEngine, "Zi Wei Dou Shu Engine", "ming_xue"),
    (QiMenEngine, "Qi Men Dun Jia Engine", "san_shi"),
    (LiuRenEngine, "Da Liu Ren Engine", "san_shi"),
    (TaiYiEngine, "Tai Yi Shen Shu Engine", "san_shi"),
    (IChingEngine, "I Ching & Liu Yao Engine", "pu_shi"),
    (LiuYaoEngine, "Liu Yao Divination Engine", "pu_shi"),
    (MeiHuaEngine, "Mei Hua Yi Shu Engine", "divination"),
    (XuanKongEngine, "Xuan Kong Flying Stars Engine", "xiang_xue"),
    (SanHeEngine, "San He Feng Shui Engine", "feng_shui"),
    (ZeJiEngine, "Imperial Calendar Date Selection Engine", "ze_ji"),
    (MianXiangEngine, "Mian Xiang Physiognomy Engine", "mian_xiang"),
    (ThaiVedicEngine, "Thai & Vedic Suriyayart Engine", "thai_vedic"),
    (WesternUranianEngine, "Western & Uranian Astrology Engine", "western_astro"),
    (NumerologyEngine, "Numerology & Satta-Lek Engine", "numerology"),
    (QiZhengSiYuEngine, "Qi Zheng Si Yu Engine", "chinese_astrology"),
]


# ==============================================================================
# 1. Base Engine Contract Integrity Suite
# ==============================================================================

class TestBaseEngineContract:
    """Verifies that all 16 engines inherit from AbstractAstrologyEngine and uphold the contract."""

    @pytest.mark.parametrize("engine_cls,expected_name,expected_system", CORE_ENGINES)
    def test_engine_contract_inheritance(self, engine_cls, expected_name, expected_system):
        assert issubclass(engine_cls, AbstractAstrologyEngine), (
            f"{engine_cls.__name__} must inherit from AbstractAstrologyEngine"
        )
        instance = engine_cls()
        assert instance.engine_name == expected_name
        assert instance.system_type == expected_system
        assert hasattr(instance, "calculate")
        assert callable(instance.calculate)

    def test_engine_chart_result_payload_contract(self):
        """Verify EngineChartResult dict inheritance, JSON serializability, and attribute access."""
        sample_scores = ElementScores(wood=20.0, fire=30.0, earth=20.0, metal=15.0, water=15.0)
        res = EngineChartResult(
            engine_name="Test Engine",
            system_type="test_type",
            chart_data={"key_a": 123, "key_b": "value_b"},
            element_scores=sample_scores,
            metadata={"source": "test_suite"}
        )

        assert isinstance(res, dict)
        assert res["engine_name"] == "Test Engine"
        assert res["system_type"] == "test_type"
        assert res["key_a"] == 123
        assert res["key_b"] == "value_b"
        assert "calculation_timestamp" in res
        assert res["element_scores"]["wood"] == 20.0
        assert res["metadata"]["source"] == "test_suite"

        # Attribute access
        assert res.engine_name == "Test Engine"
        assert res.system_type == "test_type"
        assert res.element_scores["fire"] == 30.0

        # JSON Dump test
        json_str = json.dumps(res)
        parsed = json.loads(json_str)
        assert parsed["key_a"] == 123
        assert parsed["system_type"] == "test_type"

    def test_pillar_data_model(self):
        """Verify PillarData model attributes and conversion."""
        pillar = PillarData(stem="甲", branch="子", element="Wood", hidden_stems=["癸"])
        p_dict = pillar.to_dict()
        assert p_dict["stem"] == "甲"
        assert p_dict["branch"] == "子"
        assert p_dict["element"] == "Wood"
        assert p_dict["hidden_stems"] == ["癸"]


# ==============================================================================
# 2. San Shi (三式) Engines Suite
# ==============================================================================

class TestSanShiEngines:
    """Verifies baseline calculation functionality for Tai Yi, Da Liu Ren, and Qi Men Dun Jia."""

    def test_tai_yi_engine(self):
        engine = TaiYiEngine()
        result = engine.calculate(2026, 8, 15, 12)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "TaiYiEngine"
        assert "tai_yi_number" in result
        assert "accumulated_years" in result
        assert len(result["heaven_plate"]) == 9
        assert len(result["earth_plate"]) == 9
        assert 0 <= result["star_palace"] < 16
        assert result["strategic_assessment"] in ["吉", "凶", "平", "大吉", "大凶", "小吉", "小凶", "半吉"]
        assert result["cycle_info"]["cycle_length"] == 72

    def test_liu_ren_engine(self):
        engine = LiuRenEngine()
        result = engine.calculate("甲", "子", "正月", "午")
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "LiuRenEngine"
        assert len(result["four_lessons"]) == 4
        assert len(result["three_transmissions"]) == 3
        assert "heaven_plate" in result
        assert result["three_transmissions"]["初傳 (發端)"] == "未"
        assert result["three_transmissions"]["中傳 (移革)"] == "子"
        assert result["three_transmissions"]["末傳 (歸結)"] == "巳"

    def test_qi_men_engine(self):
        engine = QiMenEngine()
        result = engine.calculate(2026, 8, 7, 14)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "QiMenEngine"
        assert result["solar_term"] == "立秋"
        assert result["dun_type"] == "Yin"
        assert result["ju_number"] == 5
        assert len(result["palaces"]) == 9
        assert result.system_type == "san_shi"


# ==============================================================================
# 3. Ming Xue (命學) Engines Suite
# ==============================================================================

class TestMingXueEngines:
    """Verifies baseline calculation functionality for BaZi, Zi Wei Dou Shu, and Qi Zheng Si Yu."""

    def test_bazi_engine(self):
        engine = BaZiEngine()
        dt = datetime(1990, 5, 15, 14, 0)
        result = engine.calculate(dt, longitude=100.493, utc_offset_hours=7.0)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine_name"] == "BaZi Engine"
        assert result["system_type"] == "ming_xue"
        assert "pillars" in result
        assert "year" in result["pillars"]
        assert "month" in result["pillars"]
        assert "day" in result["pillars"]
        assert "hour" in result["pillars"]
        assert result["pillars"]["year"]["stem"]["char"] == "庚"
        assert result["pillars"]["year"]["branch"]["char"] == "午"
        assert "day_master" in result
        assert "five_elements" in result
        assert "dayun" in result

    def test_zi_wei_engine(self):
        engine = ZiWeiEngine()
        result = engine.calculate(1990, 5, 15, 14, "male")
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "ZiWeiEngine"
        assert len(result["palaces"]) == 12
        assert result["year_stem_branch"] == "庚午"
        assert result["ming_gong_branch"] == "亥"
        assert result["shen_gong_branch"] == "丑"
        assert result["five_element_bureau"] == "土五局"
        assert result["zi_wei_star_branch"] == "辰"
        assert result["tian_fu_star_branch"] == "子"

    def test_qi_zheng_engine(self):
        engine = QiZhengSiYuEngine()
        result = engine.calculate(1990, 5, 15, 14, longitude=100.493, latitude=13.7563)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine_name"] == "Qi Zheng Si Yu Engine"
        assert result["system_type"] == "chinese_astrology"
        assert "planets" in result
        assert "shadow_stars" in result
        assert "lunar_mansions" in result
        assert len(result["planets"]) >= 5


# ==============================================================================
# 4. Pu Shi (卜筮) Engines Suite
# ==============================================================================

class TestPuShiEngines:
    """Verifies baseline calculation functionality for I Ching, Liu Yao, and Mei Hua Yi Shu."""

    def test_iching_engine(self):
        engine = IChingEngine()
        lines = engine.cast_lines(seed=42)
        assert len(lines) == 6
        assert all(line in (6, 7, 8, 9) for line in lines)
        result = engine.calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8])
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "IChingEngine"
        assert result["primary_hexagram"]["binary"] == "010110"
        assert result["transformed_hexagram"]["binary"] == "110010"
        assert len(result["six_lines"]) == 6

    def test_liu_yao_engine(self):
        engine = LiuYaoEngine()
        lines = [7, 8, 9, 8, 7, 6]
        result = engine.calculate(lines, day_stem_idx=0, month_branch_idx=0)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine_name"] == "Liu Yao Divination Engine"
        assert result["system_type"] == "pu_shi"
        assert len(result["lines"]) == 6
        assert "shi_line" in result
        assert "ying_line" in result
        assert "palace" in result

    def test_mei_hua_engine(self):
        engine = MeiHuaEngine()
        # Time method
        res_time = engine.calculate_from_time(2026, 8, 31, 14)
        assert isinstance(res_time, (EngineChartResult, dict))
        assert "primary_hexagram" in res_time
        assert "body_function" in res_time
        assert "mutual_hexagram" in res_time
        assert "transformed_hexagram" in res_time

        # Numbers method
        res_num = engine.calculate_from_numbers(3, 5, 2)
        assert isinstance(res_num, (EngineChartResult, dict))
        assert res_num["primary_hexagram"]["upper_trigram"] == "離"
        assert res_num["primary_hexagram"]["lower_trigram"] == "巽"
        assert res_num["primary_hexagram"]["moving_line"] == 2

        # calculate entry point
        res_calc = engine.calculate(2026, 8, 31, 14)
        assert isinstance(res_calc, (EngineChartResult, dict))


# ==============================================================================
# 5. Xiang Xue (相學) & Ze Ji (擇吉) Engines Suite
# ==============================================================================

class TestXiangXueAndZeJiEngines:
    """Verifies baseline calculation functionality for Xuan Kong, San He, Mian Xiang, and Ze Ji."""

    def test_xuan_kong_engine(self):
        engine = XuanKongEngine()
        result = engine.calculate_chart(180.0, period=9)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "XuanKongEngine"
        assert result["period"] == 9
        assert len(result["grid_palaces"]) == 9
        assert result["facing_mountain"] == "午 (離卦 - 陰)"
        assert result["sitting_mountain"] == "子 (坎卦 - 陰)"

    def test_san_he_engine(self):
        engine = SanHeEngine()
        result = engine.calculate(sitting_degree=0.0, facing_degree=180.0, water_exit_degree=120.0)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine_name"] == "San He Feng Shui Engine"
        assert result["system_type"] == "feng_shui"
        assert result["sitting_mountain"] == "子"
        assert result["facing_mountain"] == "午"
        assert "water_method" in result
        assert "harmony_assessment" in result

    def test_mian_xiang_engine(self):
        engine = MianXiangEngine()
        features = {
            "face_shape": "round",
            "forehead": "wide",
            "eyebrows": "thick",
            "eyes": "large",
            "nose": "high",
            "mouth": "full",
            "ears": "large",
            "chin": "round",
            "moles": [{"location": "left cheek", "size": "small"}]
        }
        result = engine.calculate(features, birth_year=1990)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine_name"] == "Mian Xiang Physiognomy Engine"
        assert result["system_type"] == "mian_xiang"
        assert "Water (水形)" in result["face_element"]
        assert len(result["twelve_palaces"]) == 12
        assert len(result["five_officials"]) == 5
        assert "fortune_flow" in result

    def test_ze_ji_engine(self):
        engine = ZeJiEngine()
        result = engine.check_suitability("午", "申", "寅", "子")
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "ZeJiEngine"
        assert result["duty_officer"] == "破日"
        assert result["overall_status"] == "凶 - 大事不宜 (歲破/月破/破日)"
        assert result["is_month_breaker"] is True
        assert 1 <= result["rating_stars"] <= 5
        assert "activities_suitability" in result


# ==============================================================================
# 6. Expanded Astrology & Numerology Engines Suite
# ==============================================================================

class TestExpandedAstrologyAndNumerologyEngines:
    """Verifies baseline calculation functionality for Thai-Vedic, Western Uranian, and Numerology."""

    def test_thai_vedic_engine(self):
        engine = ThaiVedicEngine()
        result = engine.calculate_chart(1990, 5, 15, 14, day_of_week=2)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "ThaiVedicEngine"
        assert result["thai_lagna"] == "ราศีกันย์ (House 6)"
        assert result["kalakini_planet"] == "จันทร์ (2)"
        assert result["sri_planet"] == "พฤหัสบดี (5)"
        assert result["vedic_nakshatra"]["name"] == "อุตตรภัทรบท (Uttara Bhadrapada)"
        assert result["vimshottari_dasha"] == "มาฆะ (Ketu)"

    def test_western_uranian_engine(self):
        engine = WesternUranianEngine()
        result = engine.calculate_chart(1990, 5, 15, 14)
        assert isinstance(result, (EngineChartResult, dict))
        assert result["engine"] == "WesternUranianEngine"
        assert "planets_tropical" in result
        assert len(result["uranian_tnps"]) == 8
        assert "uranian_midpoint_formula" in result
        assert "planetary_aspects" in result

    def test_numerology_engine(self):
        engine = NumerologyEngine()
        # Satta-Lek matrix
        sl = engine.calculate_satta_lek(day_num=2, lunar_month=6, year_zodiac_num=7)
        assert isinstance(sl, (EngineChartResult, dict))
        assert sl["engine"] == "SattaLekEngine"
        assert len(sl["matrix_7_base"]) == 7

        # Chaldean scoring
        score = engine.score_text_or_number("ดอ6ZF8BYฮมพ")
        assert isinstance(score, (EngineChartResult, dict))
        assert score["engine"] == "ChaldeanNumerologyEngine"
        assert (score["total_score"], score["reduced_root_digit"]) == (57, 3)

        # Standard calculate
        calc_res = engine.calculate(day_num=2, lunar_month=6, year_zodiac_num=7)
        assert isinstance(calc_res, (EngineChartResult, dict))


# ==============================================================================
# 7. Question Focus Router Suite
# ==============================================================================

class TestQuestionFocusRouterBaseline:
    """Verifies 6-domain classification, prompt building, and citation retrieval."""

    @pytest.fixture
    def router(self):
        return QuestionFocusRouter()

    @pytest.fixture
    def sample_chart(self):
        return {
            "day_master": {"stem": "壬", "element": "Water"},
            "five_elements": {
                "scores": {"Wood": 18.0, "Fire": 12.0, "Earth": 24.5, "Metal": 9.0, "Water": 21.0},
                "percentages": {"Wood": 21.4, "Fire": 14.3, "Earth": 29.2, "Metal": 10.7, "Water": 25.0},
                "dominant_element": "Earth",
            },
            "year_stem_branch": "庚午",
        }

    def test_all_six_domain_classifications(self, router):
        domain_samples = {
            "career": ["Should I change career or start a business?", "ปี 2026 มีเกณฑ์เลื่อนตำแหน่งหรือย้ายงานไหม", "今年官星如何？"],
            "finance": ["Will I have good investment returns?", "การเงินและโชคลาภปีนี้เป็นอย่างไร", "偏財运势如何？"],
            "love": ["Is this person compatible with me for marriage?", "ดวงความรักและคู่ครองปีนี้เป็นอย่างไร", "夫妻宫桃花运怎么样？"],
            "health": ["Are there any health risks or surgeries this year?", "มีเกณฑ์เจ็บป่วยหรืออุบัติเหตุไหม", "疾厄宫健康运势？"],
            "family": ["Will we have a child this year?", "ดวงครอบครัวและบุตรบริวาร", "子女宫运势如何？"],
            "timing": ["What is the best auspicious date for opening?", "ฤกษ์ยามมงคลเปิดกิจการวันไหนดี", "擇吉日吉時？"],
        }
        for expected_domain, queries in domain_samples.items():
            for q in queries:
                domain, conf = router.classify_question(q)
                assert domain == expected_domain, f"Query '{q}' classified as '{domain}', expected '{expected_domain}'"
                assert conf > 0.0

    def test_general_and_empty_queries(self, router):
        domain, conf = router.classify_question("Tell me everything about life")
        assert domain == "general"
        assert conf == 0.0

        domain_empty, conf_empty = router.classify_question("")
        assert domain_empty == "general"
        assert conf_empty == 0.0

    def test_analysis_guides_and_citations_completeness(self, router):
        for domain in ["career", "finance", "love", "health", "family", "timing"]:
            guide = router.get_analysis_guide(domain)
            assert isinstance(guide, dict)
            assert len(guide) > 0

            citations = router.get_citation_references(domain)
            assert isinstance(citations, list)
            assert len(citations) >= 1

    def test_focused_prompt_generation_multilingual(self, router, sample_chart):
        query = "ปี 2026 ควรย้ายงานหรือเปิดธุรกิจดี"
        # Thai prompt
        prompt_th = router.build_focused_prompt("career", sample_chart, query, language="th")
        assert "CAREER" in prompt_th
        assert "ตอบเป็นภาษาไทย" in prompt_th
        assert query in prompt_th

        # English prompt
        prompt_en = router.build_focused_prompt("career", sample_chart, query, language="en")
        assert "CAREER" in prompt_en
        assert "Respond in English" in prompt_en

        # Chinese prompt
        prompt_zh = router.build_focused_prompt("career", sample_chart, query, language="zh")
        assert "CAREER" in prompt_zh
        assert "用中文回答" in prompt_zh


# ==============================================================================
# 8. Multi-Agent Peer Debate & Consensus Synthesizer Suite
# ==============================================================================

class TestMultiAgentDebateBaseline:
    """Verifies multi-agent debate facilitation, consensus matrix derivation, and classical citations."""

    def test_multi_agent_peer_debate_execution(self):
        engine = MetaphysicsDebateEngine()
        context = {
            "query": "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลปี 2026",
            "birth_datetime": "1990-05-15 14:30:00",
        }
        res = engine.run_peer_debate(context)
        assert isinstance(res, dict)
        assert "domain_perspectives" in res
        assert "consensus_matrix" in res
        assert "orchestrator_synthesis" in res

        perspectives = res["domain_perspectives"]
        assert len(perspectives) >= 8
        assert "san_shi_master" in perspectives
        assert "ming_xue_master" in perspectives
        assert "pu_shi_master" in perspectives
        assert "xiang_xue_master" in perspectives
        assert "ze_ji_master" in perspectives
        assert "thai_vedic_master" in perspectives
        assert "western_astro_master" in perspectives
        assert "numerology_master" in perspectives

        consensus = res["consensus_matrix"]
        assert 0.0 <= consensus["consensus_score"] <= 1.0
        assert "consonance_factors" in consensus
        assert "cautionary_factors" in consensus
        assert "favorable_elements" in consensus

    def test_canonical_texts_integrity(self):
        assert "san_shi" in CANONICAL_TEXTS
        assert "ming_xue" in CANONICAL_TEXTS
        assert "pu_shi" in CANONICAL_TEXTS
        assert "xiang_xue" in CANONICAL_TEXTS
        assert "ze_ji" in CANONICAL_TEXTS
        assert "thai_vedic" in CANONICAL_TEXTS
        assert "western_uranian" in CANONICAL_TEXTS
        assert "numerology" in CANONICAL_TEXTS
        assert len(CANONICAL_TEXTS["san_shi"]) >= 3


# ==============================================================================
# 9. Vector Store & RAG Search Retrieval Suite
# ==============================================================================

class TestVectorStoreAndRAGBaseline:
    """Verifies RAG Vector Store, hybrid search, keyword indexing, and chunking integrity."""

    def test_vector_store_singleton_and_instance(self):
        vs = get_vector_store()
        assert isinstance(vs, VectorStore)
        assert vs._mode in ("faiss", "keyword", "empty", "unloaded")
        assert isinstance(vs._chunks, list)
        assert len(vs._chunks) > 0

    def test_vector_store_search_structure(self):
        vs = get_vector_store()
        res = vs.search("甲木 丙火 summer season", top_k=3)
        assert isinstance(res, dict)
        assert "query" in res
        assert "results" in res
        assert "corpus_searched" in res
        assert "total_results" in res
        assert "index_mode" in res
        assert isinstance(res["results"], list)
        assert len(res["results"]) <= 3

        if len(res["results"]) > 0:
            top_hit = res["results"][0]
            assert "rank" in top_hit
            assert "source" in top_hit
            assert "passage" in top_hit
            assert "verified" in top_hit
            assert "page_ref" in top_hit

    def test_vector_store_hybrid_search(self):
        vs = get_vector_store()
        hits = vs.hybrid_search("滴天髓 命理", top_k=5)
        assert isinstance(hits, list)
        assert len(hits) <= 5
        for hit in hits:
            assert "rank" in hit
            assert "source" in hit
            assert "passage" in hit
            assert "hybrid_rrf_score" in hit
            assert isinstance(hit["hybrid_rrf_score"], float)

    def test_keyword_index_isolated(self):
        sample_chunks = [
            {"text": "甲木生於春月，餘寒猶存，喜丙火溫暖。", "source": "QiongTongBaoJian", "chunk": 1},
            {"text": "乙木生於夏月，火旺木焦，專取癸水為用。", "source": "DiTianSui", "chunk": 2},
            {"text": "丙火猛烈，欺霜傲雪，能鍛庚金，逢辛反怯。", "source": "DiTianSui", "chunk": 3},
        ]
        kw_idx = _KeywordIndex(sample_chunks)
        results = kw_idx.search("丙火 庚金", top_k=2, threshold=0.0)
        assert len(results) >= 1
        assert results[0]["source"] == "DiTianSui"
        assert "丙火" in results[0]["passage"]

    def test_chunk_text_functionality(self):
        raw_text = "段落一：天地玄黃，宇宙洪荒。\n\n段落二：日月盈昃，辰宿列張。\n\n段落三：寒來暑往，秋收冬藏。"
        chunks = _chunk_text(raw_text, source="QianZiWen", chunk_size=20)
        assert isinstance(chunks, list)
        assert len(chunks) >= 3
        for c in chunks:
            assert c["source"] == "QianZiWen"
            assert "text" in c
            assert "chunk" in c


# ==============================================================================
# 10. Baseline Integrity & Determinism Suite
# ==============================================================================

class TestBaselineIntegrityAndDeterminism:
    """Verifies baseline calculations are 100% deterministic and all 16 engines are functional."""

    def test_engine_calculation_determinism(self):
        engine = BaZiEngine()
        dt = datetime(1990, 5, 15, 14, 0)
        res1 = engine.calculate(dt, longitude=100.493, utc_offset_hours=7.0)
        res2 = engine.calculate(dt, longitude=100.493, utc_offset_hours=7.0)

        assert res1["pillars"]["year"]["stem"]["char"] == res2["pillars"]["year"]["stem"]["char"]
        assert res1["pillars"]["year"]["branch"]["char"] == res2["pillars"]["year"]["branch"]["char"]
        assert res1["day_master"]["stem"] == res2["day_master"]["stem"]
        assert res1["five_elements"]["dominant_element"] == res2["five_elements"]["dominant_element"]

    def test_all_16_engines_complete_manifest(self):
        assert len(CORE_ENGINES) == 16
        engine_classes = [item[0] for item in CORE_ENGINES]
        assert len(set(engine_classes)) == 16, "All 16 engine classes must be distinct"
