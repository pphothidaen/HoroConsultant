"""
Unit & Integration Tests for 5-Branch Metaphysics Calculation Engines:
- Zi Wei Dou Shu Engine
- Qi Men Dun Jia Engine
- Da Liu Ren Engine
- I Ching & Liu Yao Engine
- Xuan Kong Flying Stars Engine
- Date Selection Engine
"""

import pytest
from datetime import datetime

from project.core.zi_wei_engine import ZiWeiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.iching_engine import IChingEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine


class TestZiWeiEngine:
    def test_zi_wei_chart_structure(self):
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14, "male")
        assert chart["engine"] == "ZiWeiEngine"
        assert len(chart["palaces"]) == 12
        assert "five_element_bureau" in chart
        assert "zi_wei_star_branch" in chart
        assert "si_hua" in chart

    def test_zi_wei_ming_gong_present(self):
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1995, 8, 20, 10, "female")
        ming_palaces = [p for p in chart["palaces"] if p["is_ming_gong"]]
        assert len(ming_palaces) == 1
        assert ming_palaces[0]["palace_name"] == "命宮"


class TestQiMenEngine:
    def test_qi_men_chart_structure(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 8, 7, 14)
        assert chart["engine"] == "QiMenEngine"
        assert chart["dun_type"] in ["Yang", "Yin"]
        assert 1 <= chart["ju_number"] <= 9
        assert len(chart["palaces"]) == 9

    def test_solar_term_lookup(self):
        engine = QiMenEngine()
        term = engine.determine_solar_term(1, 15)
        assert term in ["小寒", "大寒"]


class TestLiuRenEngine:
    def test_liu_ren_chart_structure(self):
        engine = LiuRenEngine()
        chart = engine.calculate_chart("甲", "子", "正月", "午")
        assert chart["engine"] == "LiuRenEngine"
        assert len(chart["four_lessons"]) == 4
        assert len(chart["three_transmissions"]) == 3
        assert "heaven_plate" in chart


class TestIChingEngine:
    def test_cast_lines_and_liu_yao(self):
        engine = IChingEngine()
        lines = engine.cast_lines(seed=123)
        assert len(lines) == 6
        chart = engine.calculate_liu_yao("甲", lines)
        assert chart["engine"] == "IChingEngine"
        assert "primary_hexagram" in chart
        assert len(chart["six_lines"]) == 6


class TestXuanKongEngine:
    def test_xuan_kong_grid_structure(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(180.0, period=9)
        assert chart["engine"] == "XuanKongEngine"
        assert chart["period"] == 9
        assert len(chart["grid_palaces"]) == 9
        assert "facing_mountain" in chart


class TestZeJiEngine:
    def test_ze_ji_suitability(self):
        engine = ZeJiEngine()
        result = engine.check_suitability("午", "申", "寅", "子")
        assert result["engine"] == "ZeJiEngine"
        assert "duty_officer" in result
        assert 1 <= result["rating_stars"] <= 5
        assert "activities_suitability" in result
