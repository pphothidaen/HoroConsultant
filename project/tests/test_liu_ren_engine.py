"""
Unit Tests for Da Liu Ren (大六壬) Core Calculation Engine
=========================================================
Deterministic verification of:
- Heaven/Earth plate rotation (天地盤) across 12 Earthly Branches
- Four Lessons (四課: 干上一課, 干上上二課, 支上三課, 支上上四課)
- Three Transmissions (三傳: 初傳, 中傳, 末傳)
- Twelve Heavenly Generals (十二天將: 貴人, 螣蛇, 朱雀, 六合, etc.)
- Daytime vs Nighttime Noble mappings (晝夜貴人)
- EngineChartResult protocol, metadata, dictionary indexing, and JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.liu_ren_engine import (
    BRANCHES,
    BRANCH_ELEMENTS,
    DAY_NOBLES,
    GENERAL_ELEMENTS,
    GENERAL_NATURES,
    HEAVENLY_GENERALS,
    MONTH_GENERALS,
    NIGHT_NOBLES,
    STEMS,
    STEM_PARASITIC_BRANCH,
    LiuRenEngine,
)


class TestLiuRenEngineMetadata:
    """Verify engine metadata, protocol conformity, and abstract engine inheritance."""

    def test_engine_identity_and_type(self):
        engine = LiuRenEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "Da Liu Ren Engine"
        assert engine.system_type == "san_shi"

    def test_stems_and_branches_completeness(self):
        assert len(STEMS) == 10
        assert len(BRANCHES) == 12
        assert len(HEAVENLY_GENERALS) == 12
        assert len(MONTH_GENERALS) == 12
        assert len(STEM_PARASITIC_BRANCH) == 10
        assert len(DAY_NOBLES) == 10
        assert len(NIGHT_NOBLES) == 10


class TestLiuRenHeavenPlateRotation:
    """Verify Heaven/Earth plate rotation (天地盤) mechanics."""

    def test_heaven_plate_all_12_branches_present(self):
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate(month_general_branch="亥", hour_branch="午")
        assert len(heaven_plate) == 12
        for branch in BRANCHES:
            assert branch in heaven_plate
            assert heaven_plate[branch] in BRANCHES

    def test_heaven_plate_exact_rotation_hai_over_wu(self):
        """Month general 亥 (idx 11) over Hour 午 (idx 6): Earth 午 gets Heaven 亥."""
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("亥", "午")
        expected = {
            "午": "亥", "未": "子", "申": "丑", "酉": "寅",
            "戌": "卯", "亥": "辰", "子": "巳", "丑": "午",
            "寅": "未", "卯": "申", "辰": "酉", "巳": "戌",
        }
        assert heaven_plate == expected

    def test_heaven_plate_identity_rotation(self):
        """When month general equals hour branch, Heaven plate matches Earth plate."""
        engine = LiuRenEngine()
        for branch in BRANCHES:
            heaven_plate = engine.calculate_heaven_plate(branch, branch)
            for b in BRANCHES:
                assert heaven_plate[b] == b

    def test_heaven_plate_all_month_generals(self):
        """Verify plate generation for all 12 canonical month generals."""
        engine = LiuRenEngine()
        for month_name, gen_branch in MONTH_GENERALS.items():
            plate = engine.calculate_heaven_plate(gen_branch, "子")
            assert plate["子"] == gen_branch
            assert len(plate) == 12

    def test_heaven_plate_fallback_unknown_branches(self):
        engine = LiuRenEngine()
        plate = engine.calculate_heaven_plate("INVALID_GEN", "INVALID_HOUR")
        assert len(plate) == 12


class TestLiuRenFourLessons:
    """Verify Four Lessons (四課) derivation."""

    def test_four_lessons_structure(self):
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("亥", "午")
        lessons = engine.calculate_four_lessons("甲", "子", heaven_plate)
        assert len(lessons) == 4
        lesson_names = [l["lesson_name"] for l in lessons]
        assert lesson_names == [
            "第一課 (干上)",
            "第二課 (干上上)",
            "第三課 (支上)",
            "第四課 (支上上)",
        ]

    def test_four_lessons_jia_zi_derivation(self):
        """
        Day: 甲子, Month General: 亥, Hour: 午.
        Parasitic branch of 甲 is 寅.
        From heaven_plate (亥 over 午):
          寅 -> 未
          未 -> 子
          子 -> 巳
          巳 -> 戌
        Lesson 1: bottom=甲, top=未 (heaven over 寅)
        Lesson 2: bottom=未, top=子 (heaven over 未)
        Lesson 3: bottom=子, top=巳 (heaven over 子)
        Lesson 4: bottom=巳, top=戌 (heaven over 巳)
        """
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("亥", "午")
        lessons = engine.calculate_four_lessons("甲", "子", heaven_plate)

        assert lessons[0] == {"lesson_name": "第一課 (干上)", "bottom": "甲", "top": "未"}
        assert lessons[1] == {"lesson_name": "第二課 (干上上)", "bottom": "未", "top": "子"}
        assert lessons[2] == {"lesson_name": "第三課 (支上)", "bottom": "子", "top": "巳"}
        assert lessons[3] == {"lesson_name": "第四課 (支上上)", "bottom": "巳", "top": "戌"}

    def test_four_lessons_all_10_stems_parasitic_mapping(self):
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("子", "子")
        for stem in STEMS:
            lessons = engine.calculate_four_lessons(stem, "午", heaven_plate)
            parasitic = STEM_PARASITIC_BRANCH[stem]
            assert lessons[0]["bottom"] == stem
            assert lessons[0]["top"] == parasitic
            assert lessons[2]["bottom"] == "午"


class TestLiuRenThreeTransmissions:
    """Verify Three Transmissions (三傳: 初傳, 中傳, 末傳)."""

    def test_three_transmissions_progression(self):
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("亥", "午")
        lessons = engine.calculate_four_lessons("甲", "子", heaven_plate)
        transmissions = engine.calculate_three_transmissions(lessons, heaven_plate)

        assert "初傳 (發端)" in transmissions
        assert "中傳 (移革)" in transmissions
        assert "末傳 (歸結)" in transmissions

        # 初傳 = Lesson 1 top ("未")
        assert transmissions["初傳 (發端)"] == "未"
        # 中傳 = Heaven over 未 ("子")
        assert transmissions["中傳 (移革)"] == "子"
        # 末傳 = Heaven over 子 ("巳")
        assert transmissions["末傳 (歸結)"] == "巳"

    def test_three_transmissions_all_valid_branches(self):
        engine = LiuRenEngine()
        for stem in STEMS:
            for branch in BRANCHES:
                heaven_plate = engine.calculate_heaven_plate("午", branch)
                lessons = engine.calculate_four_lessons(stem, branch, heaven_plate)
                transmissions = engine.calculate_three_transmissions(lessons, heaven_plate)
                assert transmissions["初傳 (發端)"] in BRANCHES
                assert transmissions["中傳 (移革)"] in BRANCHES
                assert transmissions["末傳 (歸結)"] in BRANCHES


class TestLiuRenHeavenlyGenerals:
    """Verify Twelve Heavenly Generals (十二天將) and Day/Night Nobles."""

    def test_day_and_night_nobles_mapping(self):
        for stem in STEMS:
            day_noble = DAY_NOBLES[stem]
            night_noble = NIGHT_NOBLES[stem]
            assert day_noble in BRANCHES
            assert night_noble in BRANCHES

        assert DAY_NOBLES["甲"] == "丑"
        assert NIGHT_NOBLES["甲"] == "未"
        assert DAY_NOBLES["丙"] == "亥"
        assert NIGHT_NOBLES["丙"] == "酉"
        assert DAY_NOBLES["辛"] == "午"
        assert NIGHT_NOBLES["辛"] == "寅"

    def test_twelve_generals_detail_completeness(self):
        engine = LiuRenEngine()
        heaven_plate = engine.calculate_heaven_plate("亥", "午")
        generals_plate = engine.calculate_generals_plate("亥", heaven_plate, is_day=True)
        details = engine.calculate_twelve_generals_detail(generals_plate, heaven_plate)

        assert len(details) == 12
        general_names = [d["general_name"] for d in details]
        for expected_gen in HEAVENLY_GENERALS:
            assert expected_gen in general_names

        for d in details:
            assert "general_name" in d
            assert "earth_branch" in d
            assert "heaven_branch" in d
            assert "element" in d
            assert "nature" in d
            assert "is_auspicious" in d
            assert d["element"] == GENERAL_ELEMENTS[d["general_name"]]
            assert d["nature"] == GENERAL_NATURES[d["general_name"]]


class TestLiuRenEngineChartCalculation:
    """Verify complete chart calculation and EngineChartResult contract invariants."""

    def test_calculate_chart_full_payload(self):
        engine = LiuRenEngine()
        result = engine.calculate_chart(
            day_stem="甲",
            day_branch="子",
            month_general="正月",
            hour_branch="午",
            is_daytime=True
        )

        assert isinstance(result, EngineChartResult)
        assert isinstance(result, dict)
        assert result.engine_name == "Da Liu Ren Engine"
        assert result.system_type == "san_shi"
        assert result["engine"] == "LiuRenEngine"
        assert result["day_stem_branch"] == "甲子"
        assert result["month_general"] == "正月 (亥)"
        assert result["hour_branch"] == "午"
        assert result["noble_branch"] == "丑"
        assert result["is_daytime"] is True
        assert len(result["four_lessons"]) == 4
        assert len(result["three_transmissions"]) == 3
        assert len(result["generals_detail"]) == 12

    def test_calculate_nighttime_chart(self):
        engine = LiuRenEngine()
        result = engine.calculate_chart(
            day_stem="甲",
            day_branch="子",
            month_general="正月",
            hour_branch="子",
            is_daytime=False
        )
        assert result["is_daytime"] is False
        assert result["noble_branch"] == "未"

    def test_calculate_generic_interface(self):
        engine = LiuRenEngine()
        res1 = engine.calculate("甲", "子", "正月", "午")
        res2 = engine.calculate_chart("甲", "子", "正月", "午")
        assert res1["day_stem_branch"] == res2["day_stem_branch"]
        assert res1["three_transmissions"] == res2["three_transmissions"]

    def test_json_serialization(self):
        engine = LiuRenEngine()
        result = engine.calculate_chart("丙", "寅", "五月", "申", is_daytime=True)
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "Da Liu Ren Engine"
        assert deserialized["system_type"] == "san_shi"
        assert "calculation_timestamp" in deserialized
        assert deserialized["day_stem_branch"] == "丙寅"
        assert len(deserialized["four_lessons"]) == 4
        assert len(deserialized["three_transmissions"]) == 3

    def test_to_dict_method(self):
        engine = LiuRenEngine()
        result = engine.calculate_chart("庚", "申", "九月", "辰")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "LiuRenEngine"
        assert "three_transmissions" in d
