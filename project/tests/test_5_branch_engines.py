"""
Unit & Integration Tests for 5-Branch Metaphysics Calculation Engines:
- Zi Wei Dou Shu Engine
- Qi Men Dun Jia Engine
- Da Liu Ren Engine
- I Ching & Liu Yao Engine
- Xuan Kong Flying Stars Engine
- Date Selection Engine
"""


from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine


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

    def test_zi_wei_literal_oracle_fields(self):
        chart = ZiWeiEngine().calculate_chart(1990, 5, 15, 14, "male")
        assert {
            key: chart[key]
            for key in (
                "birth_solar", "year_stem_branch", "hour_branch",
                "ming_gong_branch", "shen_gong_branch", "five_element_bureau",
                "zi_wei_star_branch", "tian_fu_star_branch",
            )
        } == {
            "birth_solar": "1990-05-15 14:00", "year_stem_branch": "庚午",
            "hour_branch": "未", "ming_gong_branch": "亥", "shen_gong_branch": "丑",
            "five_element_bureau": "土五局", "zi_wei_star_branch": "辰",
            "tian_fu_star_branch": "子",
        }
        assert chart["palaces"][10]["mutators"] == ["太陽化祿", "太陰化科"]


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

    def test_qi_men_literal_four_plate_oracle(self):
        chart = QiMenEngine().calculate_chart(2026, 8, 7, 14)
        assert (chart["solar_term"], chart["dun_type"], chart["ju_number"]) == ("立秋", "Yin", 5)
        assert [
            (p["palace_number"], p["earth_stem"], p["star"], p["door"], p["spirit"])
            for p in chart["palaces"]
        ] == [
            (1, "壬", "天蓬", "休門", "值符"), (2, "辛", "天芮", "死門", "玄武"),
            (3, "庚", "天衝", "傷門", "太陰"), (4, "己", "天輔", "杜門", "六合"),
            (5, "戊", "天禽", "生門", "值符"), (6, "乙", "天心", "開門", "九天"),
            (7, "丙", "天柱", "驚門", "九地"), (8, "丁", "天任", "生門", "騰蛇"),
            (9, "癸", "天英", "景門", "白虎"),
        ]


class TestLiuRenEngine:
    def test_liu_ren_chart_structure(self):
        engine = LiuRenEngine()
        chart = engine.calculate_chart("甲", "子", "正月", "午")
        assert chart["engine"] == "LiuRenEngine"
        assert len(chart["four_lessons"]) == 4
        assert len(chart["three_transmissions"]) == 3
        assert "heaven_plate" in chart

    def test_liu_ren_literal_transmissions(self):
        chart = LiuRenEngine().calculate_chart("甲", "子", "正月", "午")
        assert chart["three_transmissions"] == {
            "初傳 (發端)": "未", "中傳 (移革)": "子", "末傳 (歸結)": "巳"
        }
        assert chart["four_lessons"][0] == {
            "lesson_name": "第一課 (干上)", "bottom": "甲", "top": "未"
        }


class TestIChingEngine:
    def test_cast_lines_and_liu_yao(self):
        engine = IChingEngine()
        lines = engine.cast_lines(seed=123)
        assert len(lines) == 6
        chart = engine.calculate_liu_yao("甲", lines)
        assert chart["engine"] == "IChingEngine"
        assert "primary_hexagram" in chart
        assert len(chart["six_lines"]) == 6

    def test_iching_literal_moving_line_oracle(self):
        chart = IChingEngine().calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8])
        assert chart["primary_hexagram"]["binary"] == "010110"
        assert chart["primary_hexagram"]["name"] == "澤水困"
        assert chart["primary_hexagram"]["nature"] == "困頓"
        assert chart["transformed_hexagram"]["binary"] == "110010"
        assert chart["transformed_hexagram"]["name"] == "水澤節"
        assert [(line["animal"], line["is_moving"]) for line in chart["six_lines"]] == [
            ("青龍", True), ("朱雀", False), ("勾陳", False),
            ("騰蛇", True), ("白虎", False), ("玄武", False),
        ]


class TestXuanKongEngine:
    def test_xuan_kong_grid_structure(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(180.0, period=9)
        assert chart["engine"] == "XuanKongEngine"
        assert chart["period"] == 9
        assert len(chart["grid_palaces"]) == 9
        assert "facing_mountain" in chart

    def test_xuan_kong_24_mountain_yin_yang_drives_literal_flying_tracks(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(180.0, period=9)

        assert chart["facing_mountain"] == "午 (離卦 - 陰)"
        assert chart["sitting_mountain"] == "子 (坎卦 - 陰)"
        assert [
            (palace["palace_number"], palace["sitting_star"], palace["facing_star"])
            for palace in chart["grid_palaces"]
        ] == [
            (1, 4, 8), (2, 3, 7), (3, 2, 6),
            (4, 1, 5), (5, 9, 4), (6, 8, 3),
            (7, 7, 2), (8, 6, 1), (9, 5, 9),
        ]


class TestZeJiEngine:
    def test_ze_ji_suitability(self):
        engine = ZeJiEngine()
        result = engine.check_suitability("午", "申", "寅", "子")
        assert result["engine"] == "ZeJiEngine"
        assert "duty_officer" in result
        assert 1 <= result["rating_stars"] <= 5
        assert "activities_suitability" in result

    def test_ze_ji_literal_suitability_oracle(self):
        result = ZeJiEngine().check_suitability("午", "申", "寅", "子")
        assert result["duty_officer"] == "破日"
        assert result["overall_status"] == "凶 - 大事不宜 (歲破/月破/破日)"
        assert (result["is_year_breaker"], result["is_month_breaker"], result["is_user_clash"]) == (False, True, False)
        assert result["activities_suitability"] == {
            "結婚訂婚": "忌", "開市開業": "忌", "搬家入宅": "忌",
            "出行遠遊": "忌", "求醫治病": "宜",
        }
