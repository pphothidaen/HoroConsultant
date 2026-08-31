"""
Unit Tests for Qi Men Dun Jia (奇門遁甲) Core Calculation Engine
==============================================================
Deterministic verification of:
- Solar term lookup across all 24 solar terms (二十四節氣)
- Yang Dun (陽遁) and Yin Dun (陰遁) 18 Ju determination
- 4 Plates: Earth Plate Stems, 9 Stars (九星), 8 Doors (八門), 8 Spirits (八神)
- Leader Star & Leader Door (值符星 & 值使門)
- Tactical summary and directional recommendations
- EngineChartResult contract invariants, dictionary subscripting, and JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.qi_men_engine import (
    DOOR_AUSPICIOUSNESS,
    DOOR_ELEMENTS,
    EIGHT_DOORS,
    EIGHT_SPIRITS,
    LUO_SHU_TRIGRAMS,
    NINE_STARS,
    PALACE_NUMBERS,
    SOLAR_TERM_JU_MAP,
    SPIRIT_NATURES,
    STAR_ELEMENTS,
    QiMenEngine,
)


class TestQiMenEngineMetadata:
    """Verify engine metadata, protocol conformity, and data dictionary completeness."""

    def test_engine_identity(self):
        engine = QiMenEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "Qi Men Dun Jia Engine"
        assert engine.system_type == "san_shi"

    def test_palaces_and_entities_count(self):
        assert len(PALACE_NUMBERS) == 9
        assert len(LUO_SHU_TRIGRAMS) == 9
        assert len(NINE_STARS) == 9
        assert len(EIGHT_DOORS) == 8
        assert len(EIGHT_SPIRITS) == 8
        assert len(SOLAR_TERM_JU_MAP) == 24


class TestQiMenSolarTermsAndDunDetermination:
    """Verify solar term lookup and Yang/Yin Dun classification."""

    @pytest.mark.parametrize("month,day,expected_term", [
        (1, 1, "冬至"),
        (1, 6, "小寒"),
        (1, 20, "大寒"),
        (2, 4, "立春"),
        (2, 19, "雨水"),
        (3, 6, "驚蟄"),
        (3, 21, "春分"),
        (4, 5, "清明"),
        (4, 20, "谷雨"),
        (5, 6, "立夏"),
        (5, 21, "小滿"),
        (6, 6, "芒種"),
        (6, 21, "夏至"),
        (7, 7, "小暑"),
        (7, 23, "大暑"),
        (8, 7, "立秋"),
        (8, 23, "處暑"),
        (9, 7, "白露"),
        (9, 23, "秋分"),
        (10, 8, "寒露"),
        (10, 23, "霜降"),
        (11, 7, "立冬"),
        (11, 22, "小雪"),
        (12, 7, "大雪"),
        (12, 22, "冬至"),
        (12, 31, "冬至"),
    ])
    def test_determine_solar_term(self, month, day, expected_term):
        term = QiMenEngine.determine_solar_term(month, day)
        assert term == expected_term

    def test_all_24_solar_terms_mapped_to_yang_or_yin_dun(self):
        for term, (dun_type, ju_list) in SOLAR_TERM_JU_MAP.items():
            assert dun_type in ("Yang", "Yin")
            assert len(ju_list) == 3
            for ju in ju_list:
                assert 1 <= ju <= 9

    def test_yang_dun_solar_terms(self):
        yang_terms = [
            "冬至", "小寒", "大寒", "立春", "雨水", "驚蟄",
            "春分", "清明", "谷雨", "立夏", "小滿", "芒種",
        ]
        for term in yang_terms:
            dun_type, _ = SOLAR_TERM_JU_MAP[term]
            assert dun_type == "Yang", f"{term} should be Yang Dun"

    def test_yin_dun_solar_terms(self):
        yin_terms = [
            "夏至", "小暑", "大暑", "立秋", "處暑", "白露",
            "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
        ]
        for term in yin_terms:
            dun_type, _ = SOLAR_TERM_JU_MAP[term]
            assert dun_type == "Yin", f"{term} should be Yin Dun"


class TestQiMenPalacesAndPlates:
    """Verify 4-plate composition, 9 palaces, and celestial assignments."""

    def test_palaces_structure_and_completeness(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 8, 7, 14)
        assert len(chart["palaces"]) == 9

        palace_nums = [p["palace_number"] for p in chart["palaces"]]
        assert sorted(palace_nums) == [1, 2, 3, 4, 5, 6, 7, 8, 9]

        for p in chart["palaces"]:
            assert "palace_number" in p
            assert "trigram" in p
            assert "direction" in p
            assert "palace_element" in p
            assert "earth_stem" in p
            assert "star" in p
            assert "star_element" in p
            assert "door" in p
            assert "door_element" in p
            assert "door_auspiciousness" in p
            assert "spirit" in p
            assert "spirit_nature" in p

            assert p["star"] in NINE_STARS
            assert p["door"] in EIGHT_DOORS
            assert p["spirit"] in EIGHT_SPIRITS

    def test_leader_star_and_door_resolution(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 8, 7, 14)
        
        # Leader star & door must match the palace with Zhi Fu (值符)
        zhifu_palaces = [p for p in chart["palaces"] if p["spirit"] == "值符"]
        assert len(zhifu_palaces) >= 1
        
        leader_star = chart["leader_star"]
        leader_door = chart["leader_door"]
        assert leader_star in NINE_STARS
        assert leader_door in EIGHT_DOORS

        assert chart["tactical_summary"]["leader_star"] == leader_star
        assert chart["tactical_summary"]["leader_door"] == leader_door

    def test_tactical_summary_directions(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 8, 7, 14)
        summary = chart["tactical_summary"]
        assert "best_action_directions" in summary
        assert "avoid_directions" in summary
        assert len(summary["best_action_directions"]) > 0
        assert len(summary["avoid_directions"]) > 0


class TestQiMenYuanJuCalculations:
    """Verify Yuan selection (Upper/Middle/Lower Ju) and solar term override."""

    def test_custom_solar_term_override(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 8, 7, 14, solar_term="春分")
        assert chart["solar_term"] == "春分"
        assert chart["dun_type"] == "Yang"
        assert "陽遁" in chart["ju_name"]

    def test_yuan_progression_across_days(self):
        engine = QiMenEngine()
        # Day 1 -> Upper (idx 0), Day 6 -> Middle (idx 1), Day 11 -> Lower (idx 2)
        chart_day1 = engine.calculate_chart(2026, 3, 1, 12, solar_term="春分")
        chart_day6 = engine.calculate_chart(2026, 3, 6, 12, solar_term="春分")
        chart_day11 = engine.calculate_chart(2026, 3, 11, 12, solar_term="春分")

        _, ju_list = SOLAR_TERM_JU_MAP["春分"]
        assert chart_day1["ju_number"] == ju_list[0]
        assert chart_day6["ju_number"] == ju_list[1]
        assert chart_day11["ju_number"] == ju_list[2]

    def test_leap_year_calculation(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2024, 2, 29, 10)
        assert chart["solar_term"] == "雨水"
        assert chart["dun_type"] == "Yang"
        assert len(chart["palaces"]) == 9


class TestQiMenEngineChartResultInvariants:
    """Verify EngineChartResult contract invariants and serialization."""

    def test_calculate_chart_payload_structure(self):
        engine = QiMenEngine()
        result = engine.calculate_chart(2026, 5, 15, 8)
        
        assert isinstance(result, EngineChartResult)
        assert isinstance(result, dict)
        assert result.engine_name == "Qi Men Dun Jia Engine"
        assert result.system_type == "san_shi"
        assert result["engine"] == "QiMenEngine"
        assert "datetime" in result
        assert "solar_term" in result
        assert "dun_type" in result
        assert "ju_number" in result
        assert "ju_name" in result
        assert "palaces" in result
        assert "tactical_summary" in result

    def test_generic_calculate_interface(self):
        engine = QiMenEngine()
        res1 = engine.calculate(2026, 8, 7, 14)
        res2 = engine.calculate_chart(2026, 8, 7, 14)
        assert res1["solar_term"] == res2["solar_term"]
        assert res1["ju_number"] == res2["ju_number"]
        assert res1["leader_star"] == res2["leader_star"]

    def test_json_serialization(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 12, 25, 22)
        serialized = json.dumps(chart)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "Qi Men Dun Jia Engine"
        assert deserialized["system_type"] == "san_shi"
        assert deserialized["dun_type"] == "Yang"
        assert len(deserialized["palaces"]) == 9
        assert "calculation_timestamp" in deserialized

    def test_to_dict_method(self):
        engine = QiMenEngine()
        chart = engine.calculate_chart(2026, 6, 21, 12)
        d = chart.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "QiMenEngine"
        assert d["solar_term"] == "夏至"
