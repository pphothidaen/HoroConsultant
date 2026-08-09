"""
Unit & Integration Tests for Expanded Astrology & Metaphysics Domain Engines:
- Thai & Vedic Astrology Engine (Suriyayart, Maha Thaksa, Nakshatras)
- Western & Uranian Astrology Engine (Tropical Aspects, TNPs, Midpoints)
- Numerology & Satta-Lek Engine (7-Base 4-Row Matrix, Chaldean Scoring)
- Multi-Agent Peer Debate & Master Orchestrator Integration
"""


from project.core.multi_agent_debate import MetaphysicsDebateEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine


class TestThaiVedicEngine:
    def test_thai_vedic_chart_structure(self):
        engine = ThaiVedicEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14, day_of_week=2)
        assert chart["engine"] == "ThaiVedicEngine"
        assert "thai_lagna" in chart
        assert "maha_thaksa" in chart
        assert "vedic_nakshatra" in chart
        assert chart["vedic_nakshatra"]["number"] >= 1


class TestWesternUranianEngine:
    def test_western_uranian_chart_structure(self):
        engine = WesternUranianEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14)
        assert chart["engine"] == "WesternUranianEngine"
        assert "planets_tropical" in chart
        assert "uranian_tnps" in chart
        assert len(chart["uranian_tnps"]) == 8
        assert "uranian_midpoint_formula" in chart


class TestNumerologyEngine:
    def test_satta_lek_matrix_structure(self):
        engine = NumerologyEngine()
        sl = engine.calculate_satta_lek(day_num=2, lunar_month=6, year_zodiac_num=7)
        assert sl["engine"] == "SattaLekEngine"
        assert len(sl["matrix_7_base"]) == 7

    def test_chaldean_scoring(self):
        engine = NumerologyEngine()
        res = engine.score_text_or_number("0812345678")
        assert res["engine"] == "ChaldeanNumerologyEngine"
        assert 1 <= res["reduced_root_digit"] <= 9


class TestExpandedMultiAgentDebate:
    def test_all_8_domain_masters_present(self):
        engine = MetaphysicsDebateEngine()
        res = engine.run_peer_debate({"query": "วิเคราะห์ดวงชะตาประยุกต์ 8 สายวิชา"})
        perspectives = res["domain_perspectives"]
        assert len(perspectives) == 8
        assert "thai_vedic_master" in perspectives
        assert "western_astro_master" in perspectives
        assert "numerology_master" in perspectives
