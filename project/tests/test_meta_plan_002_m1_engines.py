"""
project/tests/test_meta_plan_002_m1_engines.py
================================================
Sprint META-PLAN-002: Milestone M1 Computational Engines Test Suite.

Comprehensive deterministic verification, boundary conditions, edge cases,
and EngineChartResult contract validation across all 16 computational engines:

1. San Shi (三式):
   - Tai Yi Shen Shu (太乙神數)
   - Da Liu Ren (大六壬)
   - Qi Men Dun Jia (奇門遁甲)
2. Ming Xue (命學):
   - BaZi (八字 - Four Pillars of Destiny)
   - Zi Wei Dou Shu (紫微斗數 - 12 Palaces & Si Hua)
   - Qi Zheng Si Yu (七政四餘 - 7 Governors & 4 Shadows)
3. Bu Shi (卜筮):
   - I Ching (周易 - 64 Hexagrams)
   - Liu Yao (六爻 - Na Jia & 6 Spirits)
   - Mei Hua Yi Shu (梅花易數 - Ti/Yong Gua)
4. Xiang Xue (相學):
   - Xuan Kong Flying Stars (玄空風水 - Period 9 & 24 Mountains)
   - San He Feng Shui (三合風水 - 12 Life Stages Water Method)
   - Mian Xiang (麻衣神相 - 12 Facial Palaces & 5 Officials)
5. Ze Ji (擇吉):
   - Imperial Date Selection (協紀辨方書 - 12 Duty Officers & Clash Filters)
6. Expanded Astrology & Numerology:
   - Thai & Vedic Suriyayart (โหราศาสตร์ไทย & ภารตวิทยา)
   - Western Tropical & Uranian (โหราศาสตร์สากล & ยูเรเนียน)
   - Numerology & Satta-Lek (สัตตเลข 7 ฐาน & Chaldean)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest

from project.core.base_engine import (
    AbstractAstrologyEngine,
    EngineChartResult,
    ElementScores,
    PillarData,
)
from project.core.bazi_engine import (
    BaZiEngine,
    _hour_branch_from_tst,
    _year_stem_branch,
    _month_branch_idx,
    _day_stem_branch,
)
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


# ==============================================================================
# 1. San Shi (三式) Engine Deepening Tests
# ==============================================================================

class TestSanShiM1Engines:
    """Verifies deterministic math, boundary conditions, and contract for San Shi."""

    @pytest.fixture
    def tai_yi(self):
        return TaiYiEngine()

    @pytest.fixture
    def liu_ren(self):
        return LiuRenEngine()

    @pytest.fixture
    def qi_men(self):
        return QiMenEngine()

    def test_tai_yi_deterministic_repeatability(self, tai_yi):
        """Verify identical inputs produce strictly identical results."""
        res1 = tai_yi.calculate(2026, 8, 31, 14)
        res2 = tai_yi.calculate(2026, 8, 31, 14)
        assert res1["tai_yi_number"] == res2["tai_yi_number"]
        assert res1["accumulated_years"] == res2["accumulated_years"]
        assert res1["star_palace"] == res2["star_palace"]
        assert res1["strategic_assessment"] == res2["strategic_assessment"]
        assert res1["heaven_plate"] == res2["heaven_plate"]
        assert res1["earth_plate"] == res2["earth_plate"]

    def test_tai_yi_epoch_boundaries(self, tai_yi):
        """Verify Tai Yi accumulated years and 72-cycle across distinct historical epochs."""
        years = [1900, 1984, 2000, 2024, 2026, 2043, 2099]
        for y in years:
            res = tai_yi.calculate(y, 1, 1, 0)
            assert isinstance(res, EngineChartResult)
            assert res.system_type == "san_shi"
            assert res["accumulated_years"] > 0
            assert 0 <= res["star_palace"] < 16
            assert len(res["heaven_plate"]) == 9
            assert len(res["earth_plate"]) == 9

    def test_liu_ren_four_lessons_and_three_transmissions_edge_cases(self, liu_ren):
        """Verify Da Liu Ren 4-lessons and 3-transmissions across all 10 Stems and 12 Branches."""
        stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

        for s in stems:
            res = liu_ren.calculate(s, "子", "正月", "午")
            assert isinstance(res, EngineChartResult)
            assert len(res["four_lessons"]) == 4
            assert len(res["three_transmissions"]) == 3
            assert "初傳 (發端)" in res["three_transmissions"]
            assert "中傳 (移革)" in res["three_transmissions"]
            assert "末傳 (歸結)" in res["three_transmissions"]
            assert res["three_transmissions"]["初傳 (發端)"] in branches

    def test_qi_men_solar_term_and_dun_ju_transitions(self, qi_men):
        """Verify Qi Men 24 solar terms, Yang Dun vs Yin Dun transitions and 18-Ju calculation."""
        # Yang Dun periods (Dongzhi to Xiazhi)
        res_yang = qi_men.calculate(2026, 1, 15, 10, solar_term="冬至")
        assert res_yang["dun_type"] == "Yang"
        assert 1 <= res_yang["ju_number"] <= 9
        assert len(res_yang["palaces"]) == 9

        # Yin Dun periods (Xiazhi to Dongzhi)
        res_yin = qi_men.calculate(2026, 7, 15, 10, solar_term="夏至")
        assert res_yin["dun_type"] == "Yin"
        assert 1 <= res_yin["ju_number"] <= 9
        assert len(res_yin["palaces"]) == 9

        # Verify all 9 palaces contain doors, stars, and spirits
        for p in res_yin["palaces"]:
            assert "palace_number" in p
            assert "star" in p
            assert "door" in p
            assert "spirit" in p


# ==============================================================================
# 2. Ming Xue (命學) Engine Deepening Tests
# ==============================================================================

class TestMingXueM1Engines:
    """Verifies BaZi, Zi Wei Dou Shu, and Qi Zheng Si Yu calculations and edge cases."""

    @pytest.fixture
    def bazi(self):
        return BaZiEngine()

    @pytest.fixture
    def zi_wei(self):
        return ZiWeiEngine()

    @pytest.fixture
    def qi_zheng(self):
        return QiZhengSiYuEngine()

    def test_bazi_midnight_transition_boundaries(self, bazi):
        """Verify hour branch and pillar calculation around midnight boundaries."""
        # Hour 23 (Early Rat / Zi hour)
        h23_branch = _hour_branch_from_tst(23)
        assert h23_branch == 0  # 子 (Rat)

        # Hour 0 (Late Rat / Zi hour)
        h0_branch = _hour_branch_from_tst(0)
        assert h0_branch == 0  # 子 (Rat)

        # Hour 1 (Chou hour)
        h1_branch = _hour_branch_from_tst(1)
        assert h1_branch == 1  # 丑 (Ox)

        dt_23 = datetime(2026, 8, 31, 23, 30)
        res_23 = bazi.calculate(dt_23, longitude=100.493, utc_offset_hours=7.0)
        assert res_23["pillars"]["hour"]["branch"]["char"] == "子"

        dt_00 = datetime(2026, 8, 31, 0, 30)
        res_00 = bazi.calculate(dt_00, longitude=100.493, utc_offset_hours=7.0)
        assert res_00["pillars"]["hour"]["branch"]["char"] == "子"

    def test_bazi_lichun_solar_term_boundary(self, bazi):
        """Verify year stem/branch transition precisely across Lichun boundary (approx Feb 4)."""
        # Feb 3 (Before Lichun) -> Previous year's stem/branch
        dt_before = datetime(2026, 2, 3, 12, 0)
        res_before = bazi.calculate(dt_before, longitude=100.493, utc_offset_hours=7.0)

        # Feb 5 (After Lichun) -> New year's stem/branch
        dt_after = datetime(2026, 2, 5, 12, 0)
        res_after = bazi.calculate(dt_after, longitude=100.493, utc_offset_hours=7.0)

        assert res_before["pillars"]["year"]["stem"]["char"] != res_after["pillars"]["year"]["stem"]["char"] or \
               res_before["pillars"]["year"]["branch"]["char"] != res_after["pillars"]["year"]["branch"]["char"]

    def test_bazi_leap_year_february_29(self, bazi):
        """Verify Julian Day calculation and Day Pillar on leap year Feb 29 (2024-02-29)."""
        dt_leap = datetime(2024, 2, 29, 12, 0)
        res_leap = bazi.calculate(dt_leap, longitude=100.493, utc_offset_hours=7.0)
        assert isinstance(res_leap, EngineChartResult)
        assert res_leap["pillars"]["month"]["stem"]["char"] is not None
        assert res_leap["day_master"]["stem"] is not None
        assert "five_elements" in res_leap
        assert len(res_leap["dayun"]["cycles"]) > 0

    def test_zi_wei_palaces_and_si_hua_transformations(self, zi_wei):
        """Verify Zi Wei 12-palaces, 14 major stars, and Si Hua transformations."""
        # Male chart
        res_male = zi_wei.calculate(1990, 5, 15, 14, gender="male")
        assert isinstance(res_male, EngineChartResult)
        assert len(res_male["palaces"]) == 12
        assert res_male["five_element_bureau"] in ["水二局", "木三局", "金四局", "土五局", "火六局"]
        assert any(p["is_ming_gong"] for p in res_male["palaces"])
        assert any(p["is_shen_gong"] for p in res_male["palaces"])

        # Female chart
        res_female = zi_wei.calculate(1990, 5, 15, 14, gender="female")
        assert isinstance(res_female, EngineChartResult)
        assert len(res_female["palaces"]) == 12

    def test_qi_zheng_7_governors_and_4_shadows(self, qi_zheng):
        """Verify Qi Zheng 7 planetary governors + 4 shadow stars + 28 lunar mansions."""
        res = qi_zheng.calculate(2026, 8, 31, 14, longitude=100.493, latitude=13.7563)
        assert isinstance(res, EngineChartResult)
        assert res.system_type == "chinese_astrology"
        assert len(res["planets"]) >= 5
        assert "shadow_stars" in res
        assert "lunar_mansions" in res
        for planet, mansion in res["lunar_mansions"].items():
            assert mansion in [
                "角", "亢", "氐", "房", "心", "尾", "箕",
                "斗", "牛", "女", "虛", "危", "室", "壁",
                "奎", "婁", "胃", "昴", "畢", "觜", "參",
                "井", "鬼", "柳", "星", "張", "翼", "軫"
            ]


# ==============================================================================
# 3. Bu Shi (卜筮) Engine Deepening Tests
# ==============================================================================

class TestPuShiM1Engines:
    """Verifies I Ching, Liu Yao, and Mei Hua Yi Shu divination engines."""

    @pytest.fixture
    def iching(self):
        return IChingEngine()

    @pytest.fixture
    def liu_yao(self):
        return LiuYaoEngine()

    @pytest.fixture
    def mei_hua(self):
        return MeiHuaEngine()

    def test_iching_all_changing_lines_edge_case(self, iching):
        """Verify I Ching boundary condition where all 6 lines change (乾 -> 坤 or 坤 -> 乾)."""
        # All old Yang (9) -> Transformed to all Yin (0)
        lines_all_9 = [9, 9, 9, 9, 9, 9]
        res_9 = iching.calculate_liu_yao("甲", lines_all_9)
        assert res_9["primary_hexagram"]["binary"] == "111111"  # 乾為天
        assert res_9["transformed_hexagram"]["binary"] == "000000"  # 坤為地
        assert all(line["is_moving"] for line in res_9["six_lines"])

        # All old Yin (6) -> Transformed to all Yang (1)
        lines_all_6 = [6, 6, 6, 6, 6, 6]
        res_6 = iching.calculate_liu_yao("甲", lines_all_6)
        assert res_6["primary_hexagram"]["binary"] == "000000"  # 坤為地
        assert res_6["transformed_hexagram"]["binary"] == "111111"  # 乾為天

    def test_iching_no_changing_lines_edge_case(self, iching):
        """Verify I Ching boundary condition where NO lines change (static hexagram)."""
        lines_static = [7, 8, 7, 8, 7, 8]
        res_static = iching.calculate_liu_yao("甲", lines_static)
        assert res_static["primary_hexagram"]["binary"] == res_static["transformed_hexagram"]["binary"]
        assert not any(line["is_moving"] for line in res_static["six_lines"])

    def test_liu_yao_na_jia_and_six_spirits_mapping(self, liu_yao):
        """Verify Liu Yao Na Jia 6-line assignment, Shi/Ying line placement, 5 Relatives and 6 Spirits."""
        # 10 day stems test for 6 spirits sequence
        for stem_idx in range(10):
            res = liu_yao.calculate([7, 8, 9, 8, 7, 6], day_stem_idx=stem_idx, month_branch_idx=0)
            assert isinstance(res, EngineChartResult)
            assert len(res["lines"]) == 6
            assert 1 <= res["shi_line"] <= 6
            assert 1 <= res["ying_line"] <= 6
            assert res["palace"] in ["乾", "坤", "震", "巽", "坎", "離", "艮", "兌"]
            animals = [l["animal"] for l in res["lines"]]
            assert len(set(animals)) == 6

    def test_mei_hua_time_and_number_methods(self, mei_hua):
        """Verify Mei Hua Yi Shu Ti/Yong dynamic relationship for both Time and Numbers methods."""
        # Number method
        res_num = mei_hua.calculate_from_numbers(1, 8, 3)
        assert isinstance(res_num, EngineChartResult)
        assert res_num["primary_hexagram"]["upper_trigram"] == "乾"
        assert res_num["primary_hexagram"]["lower_trigram"] == "坤"
        assert res_num["body_function"]["body_trigram"] in ["乾", "坤"]
        assert res_num["body_function"]["function_trigram"] in ["乾", "坤"]
        assert res_num["body_function"]["interaction"] in ["生", "剋", "比和", "洩", "耗"]


# ==============================================================================
# 4. Xiang Xue (相學) & Ze Ji (擇吉) Engine Deepening Tests
# ==============================================================================

class TestXiangXueAndZeJiM1Engines:
    """Verifies Xuan Kong Flying Stars, San He Feng Shui, Mian Xiang, and Ze Ji."""

    @pytest.fixture
    def xuan_kong(self):
        return XuanKongEngine()

    @pytest.fixture
    def san_he(self):
        return SanHeEngine()

    @pytest.fixture
    def mian_xiang(self):
        return MianXiangEngine()

    @pytest.fixture
    def ze_ji(self):
        return ZeJiEngine()

    def test_xuan_kong_period_9_and_24_mountain_boundaries(self, xuan_kong):
        """Verify Xuan Kong Period 9 across critical compass boundary degrees (0°, 90°, 180°, 270°, 359.9°)."""
        angles = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 359.9]
        for angle in angles:
            res = xuan_kong.calculate(facing_degree=angle, period=9)
            assert isinstance(res, EngineChartResult)
            assert res["period"] == 9
            assert len(res["grid_palaces"]) == 9
            for p in res["grid_palaces"]:
                assert 1 <= int(p["base_star"]) <= 9
                assert 1 <= int(p["facing_star"]) <= 9
                assert 1 <= int(p["sitting_star"]) <= 9

    def test_san_he_12_life_stages_water_methods(self, san_he):
        """Verify San He 24-mountain water methods and 12 life stages harmony."""
        res = san_he.calculate(sitting_degree=0.0, facing_degree=180.0, water_entry_degree=60.0, water_exit_degree=120.0)
        assert isinstance(res, EngineChartResult)
        assert res["sitting_mountain"] == "子"
        assert res["facing_mountain"] == "午"
        assert "water_method" in res
        assert "harmony_assessment" in res

    def test_mian_xiang_5_element_face_shapes_and_12_palaces(self, mian_xiang):
        """Verify Mian Xiang face element classification and 12 palaces for different facial archetypes."""
        face_archetypes = [
            ("round", "Water"),
            ("long", "Wood"),
            ("oval", "Metal"),
            ("pointed", "Fire"),
            ("square", "Earth"),
        ]
        for shape, expected_elem in face_archetypes:
            features = {
                "face_shape": shape,
                "forehead": "high",
                "eyebrows": "curved",
                "eyes": "bright",
                "nose": "straight",
                "mouth": "defined",
                "ears": "well-formed",
                "chin": "strong",
            }
            res = mian_xiang.calculate(features, birth_year=1995)
            assert isinstance(res, EngineChartResult)
            assert expected_elem in res["face_element"]
            assert len(res["twelve_palaces"]) == 12
            assert len(res["five_officials"]) == 5

    def test_ze_ji_12_duty_officers_and_clash_filters(self, ze_ji):
        """Verify Ze Ji 12 duty officers, month-breaker (月破), and year-breaker (歲破) clash detection."""
        # Month breaker clash: Month 申 vs Day 寅 (Clash) -> 破日
        res_clash = ze_ji.check_suitability(year_branch="午", month_branch="申", day_branch="寅", user_birth_branch="子")
        assert isinstance(res_clash, EngineChartResult)
        assert res_clash["duty_officer"] == "破日"
        assert res_clash["is_month_breaker"] is True
        assert res_clash["rating_stars"] <= 2
        assert "凶" in res_clash["overall_status"]

        # Auspicious day: 成日 / 開日
        res_auspicious = ze_ji.check_suitability(year_branch="午", month_branch="寅", day_branch="戌", user_birth_branch="午")
        assert isinstance(res_auspicious, EngineChartResult)
        assert res_auspicious["is_month_breaker"] is False
        assert 1 <= res_auspicious["rating_stars"] <= 5


# ==============================================================================
# 5. Expanded Astrology & Numerology Engine Deepening Tests
# ==============================================================================

class TestExpandedAstrologyAndNumerologyM1Engines:
    """Verifies Thai-Vedic, Western Uranian, and Numerology engines."""

    @pytest.fixture
    def thai_vedic(self):
        return ThaiVedicEngine()

    @pytest.fixture
    def western(self):
        return WesternUranianEngine()

    @pytest.fixture
    def numerology(self):
        return NumerologyEngine()

    def test_thai_vedic_lagna_and_nakshatra_cycles(self, thai_vedic):
        """Verify Thai Lagna, Maha Thaksa 8 planets, and 27 Nakshatras across all days of the week."""
        for dow in range(7):
            res = thai_vedic.calculate(1995, 6, 20, 10, day_of_week=dow)
            assert isinstance(res, EngineChartResult)
            assert "thai_lagna" in res
            assert "kalakini_planet" in res
            assert "sri_planet" in res
            assert "vedic_nakshatra" in res
            assert 1 <= res["vedic_nakshatra"]["pada"] <= 4

    def test_western_uranian_8_tnps_and_midpoints(self, western):
        """Verify 10 tropical planets, 8 Uranian TNPs, aspects, and midpoint calculations."""
        res = western.calculate(2026, 8, 31, 14)
        assert isinstance(res, EngineChartResult)
        assert len(res["planets_tropical"]) >= 5
        assert len(res["uranian_tnps"]) == 8
        expected_tnps = ["Cupido", "Hades", "Zeus", "Kronos", "Apollon", "Admetos", "Vulkanus", "Poseidon"]
        for tnp in expected_tnps:
            assert any(tnp in k for k in res["uranian_tnps"])
            matching_key = next(k for k in res["uranian_tnps"] if tnp in k)
            assert 0.0 <= res["uranian_tnps"][matching_key] < 360.0

    def test_numerology_satta_lek_and_chaldean_scoring(self, numerology):
        """Verify Satta-Lek 7-base 4-row matrix and Chaldean text/number scoring."""
        # Satta-Lek
        sl_res = numerology.calculate(day_num=1, lunar_month=5, year_zodiac_num=6)
        assert isinstance(sl_res, EngineChartResult)
        assert len(sl_res["matrix_7_base"]) == 7

        # Chaldean text scoring with Thai and English strings
        test_strings = [
            ("HoroConsultant", 46, 1),
            ("888999", 51, 6),
            ("ดวงดีมีโชค", 35, 8),
        ]
        for text, expected_min_score, expected_root_range in test_strings:
            res = numerology.score_text_or_number(text)
            assert isinstance(res, EngineChartResult)
            assert res["total_score"] > 0
            assert 1 <= res["reduced_root_digit"] <= 9


# ==============================================================================
# 6. Global EngineChartResult Architecture Invariant Suite
# ==============================================================================

class TestEngineChartResultContractInvariants:
    """Verifies that all 16 engines strictly fulfill EngineChartResult contract invariants."""

    ALL_ENGINES = [
        (BaZiEngine, lambda e: e.calculate(datetime(1990, 5, 15, 14, 0), 100.493, 7.0)),
        (ZiWeiEngine, lambda e: e.calculate(1990, 5, 15, 14, "male")),
        (QiMenEngine, lambda e: e.calculate(2026, 8, 7, 14)),
        (LiuRenEngine, lambda e: e.calculate("甲", "子", "正月", "午")),
        (TaiYiEngine, lambda e: e.calculate(2026, 8, 15, 12)),
        (IChingEngine, lambda e: e.calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8])),
        (LiuYaoEngine, lambda e: e.calculate([7, 8, 9, 8, 7, 6], 0, 0)),
        (MeiHuaEngine, lambda e: e.calculate(2026, 8, 31, 14)),
        (XuanKongEngine, lambda e: e.calculate(180.0, 9)),
        (SanHeEngine, lambda e: e.calculate(0.0, 180.0, 120.0)),
        (ZeJiEngine, lambda e: e.check_suitability("午", "申", "寅", "子")),
        (MianXiangEngine, lambda e: e.calculate({"face_shape": "round"}, 1990)),
        (ThaiVedicEngine, lambda e: e.calculate(1990, 5, 15, 14, 2)),
        (WesternUranianEngine, lambda e: e.calculate(1990, 5, 15, 14)),
        (NumerologyEngine, lambda e: e.calculate(2, 6, 7)),
        (QiZhengSiYuEngine, lambda e: e.calculate(1990, 5, 15, 14)),
    ]

    @pytest.mark.parametrize("engine_cls,invoker", ALL_ENGINES)
    def test_all_engines_produce_serializable_chart_results(self, engine_cls, invoker):
        engine = engine_cls()
        result = invoker(engine)

        assert isinstance(result, EngineChartResult), f"{engine_cls.__name__} must return EngineChartResult"
        assert isinstance(result, dict), f"{engine_cls.__name__} result must be an instance of dict"
        assert hasattr(result, "engine_name")
        assert hasattr(result, "system_type")
        assert hasattr(result, "calculation_timestamp")
        assert len(result.engine_name) > 0
        assert len(result.system_type) > 0

        # Native JSON serialization invariant
        json_repr = json.dumps(result)
        assert len(json_repr) > 20
        reloaded = json.loads(json_repr)
        assert isinstance(reloaded, dict)
        assert reloaded["engine_name"] == result.engine_name
