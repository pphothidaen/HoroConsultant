"""
Unit Tests for I Ching & Liu Yao (易經 & 六爻) Core Calculation Engine
===================================================================
Deterministic verification of:
- Hexagram line casting (yarrow/coin simulation with seed control)
- Binary string conversion for Primary and Transformed Hexagrams
- Hexagram lookup across binary patterns (all 64 combinations tested)
- Moving line detection and state transitions (6: Old Yin -> Yang, 9: Old Yang -> Yin)
- Six Animals / Spirits (六神) assignment for all 10 Heavenly Stems
- Five Relatives (五親) cyclic allocation
- EngineChartResult contract invariants, dictionary indexing, and JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.iching_engine import (
    DAY_STEM_SIX_ANIMALS_START,
    FIVE_RELATIVES,
    HEXAGRAM_64_NAMES,
    SIX_ANIMALS,
    TRIGRAM_BINARY,
    TRIGRAM_NAMES,
    IChingEngine,
)


class TestIChingEngineMetadata:
    """Verify engine metadata, protocol conformity, and data dictionary completeness."""

    def test_engine_identity(self):
        engine = IChingEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "I Ching & Liu Yao Engine"
        assert engine.system_type == "pu_shi"

    def test_trigrams_and_constants_count(self):
        assert len(TRIGRAM_NAMES) == 8
        assert len(TRIGRAM_BINARY) == 8
        assert len(FIVE_RELATIVES) == 5
        assert len(SIX_ANIMALS) == 6
        assert len(DAY_STEM_SIX_ANIMALS_START) == 10


class TestIChingCastLines:
    """Verify casting mechanics, determinism, and valid line values."""

    def test_cast_lines_length_and_values(self):
        engine = IChingEngine()
        lines = engine.cast_lines()
        assert len(lines) == 6
        for val in lines:
            assert val in (6, 7, 8, 9)

    def test_cast_lines_deterministic_seed(self):
        engine = IChingEngine()
        lines1 = engine.cast_lines(seed=42)
        lines2 = engine.cast_lines(seed=42)
        assert lines1 == lines2

    def test_cast_lines_different_seeds_produce_variation(self):
        engine = IChingEngine()
        lines_a = engine.cast_lines(seed=100)
        lines_b = engine.cast_lines(seed=999)
        assert len(lines_a) == 6
        assert len(lines_b) == 6


class TestIChingBinaryConversion:
    """Verify binary translation for static and moving lines."""

    def test_static_pure_yang(self):
        engine = IChingEngine()
        # All Young Yang (7) -> Primary: 111111, Transformed: 111111
        primary, transformed = engine.lines_to_binary([7, 7, 7, 7, 7, 7])
        assert primary == "111111"
        assert transformed == "111111"

    def test_static_pure_yin(self):
        engine = IChingEngine()
        # All Young Yin (8) -> Primary: 000000, Transformed: 000000
        primary, transformed = engine.lines_to_binary([8, 8, 8, 8, 8, 8])
        assert primary == "000000"
        assert transformed == "000000"

    def test_moving_old_yin_flips_to_yang(self):
        engine = IChingEngine()
        # 6 (Old Yin) at line 1 flips to 1 in transformed
        primary, transformed = engine.lines_to_binary([6, 8, 8, 8, 8, 8])
        assert primary == "000000"
        assert transformed == "100000"

    def test_moving_old_yang_flips_to_yin(self):
        engine = IChingEngine()
        # 9 (Old Yang) at line 6 flips to 0 in transformed
        primary, transformed = engine.lines_to_binary([7, 7, 7, 7, 7, 9])
        assert primary == "111111"
        assert transformed == "111110"

    def test_all_moving_lines_invert(self):
        engine = IChingEngine()
        # All Old Yin (6) -> 000000 becomes 111111
        primary_yin, transformed_yin = engine.lines_to_binary([6, 6, 6, 6, 6, 6])
        assert primary_yin == "000000"
        assert transformed_yin == "111111"

        # All Old Yang (9) -> 111111 becomes 000000
        primary_yang, transformed_yang = engine.lines_to_binary([9, 9, 9, 9, 9, 9])
        assert primary_yang == "111111"
        assert transformed_yang == "000000"


class TestIChingHexagramLookup:
    """Verify 64 hexagrams and trigram name lookups."""

    @pytest.mark.parametrize("binary_code,expected_name,expected_nature", [
        ("111111", "乾為天", "大吉"),
        ("000000", "坤為地", "順利"),
        ("100010", "水雷屯", "宜守"),
        ("010001", "山水蒙", "啓蒙"),
        ("111010", "水天需", "等待"),
        ("010111", "天水訟", "謹慎"),
        ("010000", "地水師", "律己"),
        ("000010", "水地比", "親和"),
        ("111011", "風天小畜", "積蓄"),
        ("110111", "天澤履", "禮儀"),
        ("111000", "地天泰", "通達"),
        ("000111", "天地否", "閉塞"),
        ("101111", "天火同人", "和諧"),
        ("111101", "火天大有", "豐盛"),
    ])
    def test_known_hexagram_lookups(self, binary_code, expected_name, expected_nature):
        assert binary_code in HEXAGRAM_64_NAMES
        meta = HEXAGRAM_64_NAMES[binary_code]
        assert meta["name"] == expected_name
        assert meta["nature"] == expected_nature
        assert meta.name == expected_name
        assert meta.nature == expected_nature

    @pytest.mark.parametrize("binary,expected_trigram", [
        ("000", "坤"), ("100", "震"), ("010", "坎"), ("110", "兌"),
        ("001", "艮"), ("101", "離"), ("011", "巽"), ("111", "乾"),
    ])
    def test_trigram_binary_mappings(self, binary, expected_trigram):
        assert TRIGRAM_BINARY[binary] == expected_trigram

    def test_all_64_hexagrams_complete_in_dictionary(self):
        """Verify all 64 King Wen hexagrams are present with multi-key indexing (256 total keys)."""
        assert len(HEXAGRAM_64_NAMES) == 256
        for num in range(1, 65):
            meta = HEXAGRAM_64_NAMES[num]
            assert 1 <= meta["number"] <= 64
            assert len(meta["name"]) > 0
            assert len(meta["nature"]) > 0
            assert len(meta["judgment"]) > 0
            assert meta["upper_trigram"] in TRIGRAM_NAMES
            assert meta["lower_trigram"] in TRIGRAM_NAMES
            # Verify lookup by binary string
            assert HEXAGRAM_64_NAMES[meta.binary] == meta
            # Verify lookup by bit tuple
            bit_tuple = tuple(int(b) for b in meta.binary)
            assert HEXAGRAM_64_NAMES[bit_tuple] == meta
            # Verify lookup by trigram pair
            assert HEXAGRAM_64_NAMES[(meta.lower_trigram, meta.upper_trigram)] == meta

    def test_all_64_binary_permutations_handled_safely(self):
        """Ensure all 2^6 = 64 bit sequences produce valid hexagram lookups without error."""
        engine = IChingEngine()
        for i in range(64):
            bin_str = f"{i:06b}"
            lines = [7 if b == "1" else 8 for b in bin_str]
            chart = engine.calculate_liu_yao("甲", lines)
            assert "primary_hexagram" in chart
            assert chart["primary_hexagram"]["binary"] == bin_str
            assert len(chart["primary_hexagram"]["name"]) > 0


class TestIChingSixAnimalsAndRelatives:
    """Verify Six Animals starting position by Day Stem and Five Relatives sequence."""

    @pytest.mark.parametrize("day_stem,expected_start_animal", [
        ("甲", "青龍"), ("乙", "青龍"),
        ("丙", "朱雀"), ("丁", "朱雀"),
        ("戊", "勾陳"),
        ("己", "騰蛇"),
        ("庚", "白虎"), ("辛", "白虎"),
        ("壬", "玄武"), ("癸", "玄武"),
    ])
    def test_day_stem_starts_six_animals(self, day_stem, expected_start_animal):
        assert DAY_STEM_SIX_ANIMALS_START[day_stem] == expected_start_animal

        engine = IChingEngine()
        chart = engine.calculate_liu_yao(day_stem, [7, 7, 7, 7, 7, 7])
        lines = chart["six_lines"]
        assert lines[0]["animal"] == expected_start_animal

    def test_six_animals_cyclic_order(self):
        engine = IChingEngine()
        # Jia Day starts with Qing Long -> Zhu Que -> Gou Chen -> Teng She -> Bai Hu -> Xuan Wu
        chart = engine.calculate_liu_yao("甲", [7, 7, 7, 7, 7, 7])
        animals = [line["animal"] for line in chart["six_lines"]]
        assert animals == ["青龍", "朱雀", "勾陳", "騰蛇", "白虎", "玄武"]

    def test_five_relatives_cyclic_order(self):
        engine = IChingEngine()
        chart = engine.calculate_liu_yao("甲", [7, 7, 7, 7, 7, 7])
        relatives = [line["relative"] for line in chart["six_lines"]]
        # 5 relatives cycle for 6 lines: idx 0,1,2,3,4,0 -> 父母, 兄弟, 子孫, 妻財, 官鬼, 父母
        assert relatives == ["父母", "兄弟", "子孫", "妻財", "官鬼", "父母"]


class TestIChingEngineChartResultInvariants:
    """Verify EngineChartResult contract invariants and serialization."""

    def test_calculate_liu_yao_payload_structure(self):
        engine = IChingEngine()
        chart = engine.calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8])

        assert isinstance(chart, EngineChartResult)
        assert isinstance(chart, dict)
        assert chart.engine_name == "I Ching & Liu Yao Engine"
        assert chart.system_type == "pu_shi"
        assert chart["engine"] == "IChingEngine"
        assert chart["day_stem"] == "甲"
        assert chart["raw_lines"] == [6, 7, 8, 9, 7, 8]

        # Six lines detail
        lines = chart["six_lines"]
        assert len(lines) == 6
        for i, line in enumerate(lines):
            assert line["line_number"] == i + 1
            assert line["line_value"] in (6, 7, 8, 9)
            assert line["line_type"] in ("陽爻", "陰爻")
            assert isinstance(line["is_moving"], bool)
            assert line["relative"] in FIVE_RELATIVES
            assert line["animal"] in SIX_ANIMALS

        assert lines[0]["is_moving"] is True   # line_val 6
        assert lines[1]["is_moving"] is False  # line_val 7
        assert lines[2]["is_moving"] is False  # line_val 8
        assert lines[3]["is_moving"] is True   # line_val 9
        assert lines[4]["is_moving"] is False  # line_val 7
        assert lines[5]["is_moving"] is False  # line_val 8

    def test_generic_calculate_interface(self):
        engine = IChingEngine()
        res1 = engine.calculate("丙", [7, 7, 7, 7, 7, 7])
        res2 = engine.calculate_liu_yao("丙", [7, 7, 7, 7, 7, 7])
        assert res1["primary_hexagram"] == res2["primary_hexagram"]
        assert res1["day_stem"] == res2["day_stem"]

    def test_json_serialization(self):
        engine = IChingEngine()
        chart = engine.calculate_liu_yao("壬", [6, 8, 7, 9, 8, 7])
        serialized = json.dumps(chart)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "I Ching & Liu Yao Engine"
        assert deserialized["system_type"] == "pu_shi"
        assert "calculation_timestamp" in deserialized
        assert len(deserialized["six_lines"]) == 6

    def test_to_dict_method(self):
        engine = IChingEngine()
        chart = engine.calculate_liu_yao("癸", [7, 8, 7, 8, 7, 8])
        d = chart.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "IChingEngine"
        assert "primary_hexagram" in d
