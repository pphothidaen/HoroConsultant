"""
Unit Tests for Zi Wei Dou Shu (紫微斗數) Core Calculation Engine
==============================================================
Deterministic verification of:
- Year Stem-Branch & Hour Branch calculation
- Ming Gong (命宮) and Shen Gong (身宮) placement
- Five Element Bureau (五行局: 水二局, 木三局, 金四局, 土五局, 火六局)
- 14 Major Stars & Assistant Stars (六吉星, 六煞星, 祿存, 天馬)
- Si Hua Mutators (四化: 化祿, 化權, 化科, 化忌) for all 10 Heavenly Stems
- Decade Luck Periods (大限) clockwise/counter-clockwise directionality
- 12 Palaces invariant validation & JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.zi_wei_engine import (
    BRANCHES,
    FIVE_ELEMENT_BUREAUS,
    LUCUN_BRANCH_MAP,
    PALACE_NAMES,
    SI_HUA_MATRIX,
    STEMS,
    TIAN_MA_MAP,
    ZiWeiEngine,
)


class TestZiWeiEngineMetadata:
    """Verify engine metadata, protocol conformity, and data dictionary completeness."""

    def test_engine_identity(self):
        engine = ZiWeiEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "Zi Wei Dou Shu Engine"
        assert engine.system_type == "ming_xue"

    def test_palaces_and_constants_count(self):
        assert len(PALACE_NAMES) == 12
        assert len(FIVE_ELEMENT_BUREAUS) == 5
        assert len(SI_HUA_MATRIX) == 10
        assert len(LUCUN_BRANCH_MAP) == 10
        assert len(TIAN_MA_MAP) == 12


class TestZiWeiStemBranchCalculations:
    """Verify Year Stem-Branch and Hour Branch derivation."""

    @pytest.mark.parametrize("year,expected_stem,expected_branch", [
        (1984, "甲", "子"),
        (1990, "庚", "午"),
        (1995, "乙", "亥"),
        (2000, "庚", "辰"),
        (2024, "甲", "辰"),
        (2026, "丙", "午"),
    ])
    def test_year_stem_branch(self, year, expected_stem, expected_branch):
        stem, branch = ZiWeiEngine._get_year_stem_branch(year)
        assert stem == expected_stem
        assert branch == expected_branch

    @pytest.mark.parametrize("hour,expected_branch", [
        (0, "子"), (1, "丑"), (2, "丑"), (3, "寅"),
        (4, "寅"), (5, "卯"), (6, "卯"), (7, "辰"),
        (8, "辰"), (9, "巳"), (10, "巳"), (11, "午"),
        (12, "午"), (13, "未"), (14, "未"), (15, "申"),
        (16, "申"), (17, "酉"), (18, "酉"), (19, "戌"),
        (20, "戌"), (21, "亥"), (22, "亥"), (23, "子"),
    ])
    def test_hour_branch_mapping(self, hour, expected_branch):
        branch = ZiWeiEngine._get_hour_branch(hour)
        assert branch == expected_branch


class TestZiWeiMingShenGong:
    """Verify Ming Gong and Shen Gong location calculations."""

    def test_ming_shen_gong_month_1_zi_hour(self):
        # Month 1, Hour 子 (idx 0) -> Ming = Yin (idx 2), Shen = Yin (idx 2)
        ming_b, shen_b, ming_idx, shen_idx = ZiWeiEngine.calculate_ming_shen_gong(1, "子")
        assert ming_b == "寅"
        assert shen_b == "寅"
        assert ming_idx == 2
        assert shen_idx == 2

    def test_ming_shen_gong_month_5_wei_hour(self):
        # Month 5, Hour 未 (idx 7)
        # Ming = (2 + (5-1) - 7) % 12 = -1 % 12 = 11 (亥)
        # Shen = (2 + (5-1) + 7) % 12 = 13 % 12 = 1 (丑)
        ming_b, shen_b, ming_idx, shen_idx = ZiWeiEngine.calculate_ming_shen_gong(5, "未")
        assert ming_b == "亥"
        assert shen_b == "丑"
        assert ming_idx == 11
        assert shen_idx == 1

    def test_ming_shen_gong_all_months(self):
        for month in range(1, 13):
            for branch in BRANCHES:
                ming_b, shen_b, ming_idx, shen_idx = ZiWeiEngine.calculate_ming_shen_gong(month, branch)
                assert ming_b in BRANCHES
                assert shen_b in BRANCHES
                assert 0 <= ming_idx <= 11
                assert 0 <= shen_idx <= 11


class TestZiWeiFiveElementBureau:
    """Verify Five Element Bureau (五行局) calculations."""

    @pytest.mark.parametrize("year_stem,ming_branch,expected_bureau", [
        ("戊", "寅", "水二局"),
        ("甲", "辰", "木三局"),
        ("庚", "辰", "金四局"),
        ("甲", "午", "土五局"),
        ("甲", "寅", "火六局"),
    ])
    def test_five_element_bureau_derivation(self, year_stem, ming_branch, expected_bureau):
        bureau = ZiWeiEngine.calculate_five_element_bureau(year_stem, ming_branch)
        assert bureau == expected_bureau

    def test_all_five_bureaus_exist_in_mapping(self):
        bureaus = set()
        for stem in STEMS:
            for branch in BRANCHES:
                b = ZiWeiEngine.calculate_five_element_bureau(stem, branch)
                bureaus.add(b)
        assert bureaus == {"水二局", "木三局", "金四局", "土五局", "火六局"}


class TestZiWeiStarPlacement:
    """Verify Zi Wei star position and Assistant stars."""

    @pytest.mark.parametrize("bureau_num,lunar_day,expected_branch", [
        (2, 1, "丑"),
        (2, 2, "寅"),
        (3, 1, "辰"),
        (4, 1, "亥"),
        (5, 15, "辰"),
    ])
    def test_zi_wei_star_branch(self, bureau_num, lunar_day, expected_branch):
        branch = ZiWeiEngine.calculate_zi_wei_star_branch(bureau_num, lunar_day)
        assert branch == expected_branch

    def test_assistant_stars_structure(self):
        engine = ZiWeiEngine()
        assistants = engine.calculate_assistant_stars(
            year_stem="庚",
            year_branch="午",
            lunar_month=5,
            hour_branch="未"
        )
        assert len(assistants) == 12
        for branch in BRANCHES:
            assert isinstance(assistants[branch], list)

        # Lucun of 庚 is 申, Qing Yang is 酉, Tuo Luo is 未
        assert "祿存" in assistants["申"]
        assert "擎羊" in assistants["酉"]
        assert "陀羅" in assistants["未"]
        # Tian Ma of 午 is 申
        assert "天馬" in assistants["申"]


class TestZiWeiSiHua:
    """Verify Si Hua (四化: 化祿, 化權, 化科, 化忌) for all 10 Heavenly Stems."""

    @pytest.mark.parametrize("stem,expected_lu,expected_quan,expected_ke,expected_ji", [
        ("甲", "廉貞", "破軍", "武曲", "太陽"),
        ("乙", "天機", "天梁", "紫微", "太陰"),
        ("丙", "天同", "天機", "文昌", "廉貞"),
        ("丁", "太陰", "天同", "天機", "巨門"),
        ("戊", "貪狼", "太陰", "右弼", "天機"),
        ("己", "武曲", "貪狼", "天梁", "文曲"),
        ("庚", "太陽", "武曲", "太陰", "天同"),
        ("辛", "巨門", "太陽", "文曲", "文昌"),
        ("壬", "天梁", "紫微", "左輔", "武曲"),
        ("癸", "破軍", "巨門", "太陰", "貪狼"),
    ])
    def test_si_hua_all_stems(self, stem, expected_lu, expected_quan, expected_ke, expected_ji):
        si_hua = SI_HUA_MATRIX[stem]
        assert si_hua["化祿"] == expected_lu
        assert si_hua["化權"] == expected_quan
        assert si_hua["化科"] == expected_ke
        assert si_hua["化忌"] == expected_ji


class TestZiWeiDecadeLuck:
    """Verify Decade Luck direction (順行 / 逆行)."""

    def test_decade_luck_yang_male(self):
        # 1990 is 庚午 (庚 is Yang stem, Male -> Forward)
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14, gender="male")
        assert chart["is_forward_decade"] is True

    def test_decade_luck_yang_female(self):
        # 1990 is 庚午 (庚 is Yang stem, Female -> Backward)
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14, gender="female")
        assert chart["is_forward_decade"] is False

    def test_decade_luck_yin_female(self):
        # 1995 is 乙亥 (乙 is Yin stem, Female -> Forward)
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1995, 8, 20, 10, gender="female")
        assert chart["is_forward_decade"] is True

    def test_decade_luck_yin_male(self):
        # 1995 is 乙亥 (乙 is Yin stem, Male -> Backward)
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1995, 8, 20, 10, gender="male")
        assert chart["is_forward_decade"] is False


class TestZiWeiEngineChartResultInvariants:
    """Verify EngineChartResult contract invariants, 12 palaces, and serialization."""

    def test_calculate_chart_12_palaces_invariants(self):
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(1990, 5, 15, 14, gender="male")

        assert isinstance(chart, EngineChartResult)
        assert isinstance(chart, dict)
        assert chart.engine_name == "Zi Wei Dou Shu Engine"
        assert chart.system_type == "ming_xue"

        palaces = chart["palaces"]
        assert len(palaces) == 12

        ming_palaces = [p for p in palaces if p["is_ming_gong"]]
        assert len(ming_palaces) == 1
        assert ming_palaces[0]["palace_name"] == "命宮"

        shen_palaces = [p for p in palaces if p["is_shen_gong"]]
        assert len(shen_palaces) == 1

        palace_names = [p["palace_name"] for p in palaces]
        for expected_name in PALACE_NAMES:
            assert expected_name in palace_names

        for p in palaces:
            assert "palace_name" in p
            assert "earth_branch" in p
            assert "stars" in p
            assert "primary_stars" in p
            assert "assistant_stars" in p
            assert "mutators" in p
            assert "decade_luck" in p
            assert "is_ming_gong" in p
            assert "is_shen_gong" in p

    def test_generic_calculate_interface(self):
        engine = ZiWeiEngine()
        res1 = engine.calculate(1990, 5, 15, 14, gender="male")
        res2 = engine.calculate_chart(1990, 5, 15, 14, gender="male")
        assert res1["year_stem_branch"] == res2["year_stem_branch"]
        assert res1["five_element_bureau"] == res2["five_element_bureau"]
        assert res1["zi_wei_star_branch"] == res2["zi_wei_star_branch"]

    def test_json_serialization(self):
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(2000, 1, 1, 0, gender="female")
        serialized = json.dumps(chart)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "Zi Wei Dou Shu Engine"
        assert deserialized["system_type"] == "ming_xue"
        assert len(deserialized["palaces"]) == 12
        assert "calculation_timestamp" in deserialized

    def test_to_dict_method(self):
        engine = ZiWeiEngine()
        chart = engine.calculate_chart(2024, 6, 15, 18, gender="male")
        d = chart.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "ZiWeiEngine"
        assert len(d["palaces"]) == 12
