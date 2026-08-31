"""
Unit Tests for Xuan Kong Flying Stars (玄空風水) Core Calculation Engine
=====================================================================
Deterministic verification of:
- 24 Mountains (二十四山) angular resolution across all compass headings
- Degree angle boundaries & normalization (0°, 45°, 90°, 180°, 270°, 359°, etc.)
- Flying Stars Algorithm forward (順飛) and backward (逆飛) Luo Shu tracks
- Period 9 Base Chart (九運運盤) structure and star distribution
- Sitting Star (山星) and Facing Star (向星) placement across the 9-palace grid
- EngineChartResult contract invariants, dictionary indexing, and JSON serialization
"""

import json
import pytest

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.xuan_kong_engine import (
    LUO_SHU_PALACES,
    MOUNTAINS_24,
    PERIOD_9_BASE_CHART,
    STAR_NAMES,
    XuanKongEngine,
)


class TestXuanKongEngineMetadata:
    """Verify engine metadata, protocol conformity, and data completeness."""

    def test_engine_identity(self):
        engine = XuanKongEngine()
        assert isinstance(engine, AbstractAstrologyEngine)
        assert engine.engine_name == "Xuan Kong Flying Stars Engine"
        assert engine.system_type == "xiang_xue"

    def test_constants_completeness(self):
        assert len(MOUNTAINS_24) == 24
        assert len(LUO_SHU_PALACES) == 9
        assert len(PERIOD_9_BASE_CHART) == 9
        assert len(STAR_NAMES) == 9


class TestXuanKong24MountainsResolution:
    """Verify 24 Mountain resolution for required angles and boundary cases."""

    @pytest.mark.parametrize("degree,expected_mountain,expected_trigram,expected_yy", [
        (0.0, "子", "坎", "陰"),
        (45.0, "艮", "艮", "陽"),
        (90.0, "卯", "震", "陰"),
        (180.0, "午", "離", "陰"),
        (270.0, "酉", "兌", "陰"),
        (359.0, "子", "坎", "陰"),
    ])
    def test_required_canonical_degrees(self, degree, expected_mountain, expected_trigram, expected_yy):
        engine = XuanKongEngine()
        name, trigram, yy = engine.resolve_mountain(degree)
        assert name == expected_mountain
        assert trigram == expected_trigram
        assert yy == expected_yy

    @pytest.mark.parametrize("name,center_deg,trigram,yy", [
        ("壬", 345.0, "坎", "陽"),
        ("子", 0.0, "坎", "陰"),
        ("癸", 15.0, "坎", "陰"),
        ("丑", 30.0, "艮", "陰"),
        ("艮", 45.0, "艮", "陽"),
        ("寅", 60.0, "艮", "陽"),
        ("甲", 75.0, "震", "陽"),
        ("卯", 90.0, "震", "陰"),
        ("乙", 105.0, "震", "陰"),
        ("辰", 120.0, "巽", "陰"),
        ("巽", 135.0, "巽", "陽"),
        ("巳", 150.0, "巽", "陽"),
        ("丙", 165.0, "離", "陽"),
        ("午", 180.0, "離", "陰"),
        ("丁", 195.0, "離", "陰"),
        ("未", 210.0, "坤", "陰"),
        ("坤", 225.0, "坤", "陽"),
        ("申", 240.0, "坤", "陽"),
        ("庚", 255.0, "兌", "陽"),
        ("酉", 270.0, "兌", "陰"),
        ("辛", 285.0, "兌", "陰"),
        ("戌", 300.0, "乾", "陰"),
        ("乾", 315.0, "乾", "陽"),
        ("亥", 330.0, "乾", "陽"),
    ])
    def test_all_24_mountains_center_degrees(self, name, center_deg, trigram, yy):
        engine = XuanKongEngine()
        m_name, m_trigram, m_yy = engine.resolve_mountain(center_deg)
        assert m_name == name
        assert m_trigram == trigram
        assert m_yy == yy

    def test_degree_normalization_and_wrapping(self):
        engine = XuanKongEngine()
        # 360° wraps to 0° (子)
        assert engine.resolve_mountain(360.0)[0] == "子"
        # 720° wraps to 0° (子)
        assert engine.resolve_mountain(720.0)[0] == "子"
        # -90° wraps to 270° (酉)
        assert engine.resolve_mountain(-90.0)[0] == "酉"
        # -180° wraps to 180° (午)
        assert engine.resolve_mountain(-180.0)[0] == "午"

    def test_boundary_transitions(self):
        engine = XuanKongEngine()
        # 352.5 is start of 子
        assert engine.resolve_mountain(352.5)[0] == "子"
        # 352.4 is end of 壬
        assert engine.resolve_mountain(352.4)[0] == "壬"
        # 7.5 is start of 癸
        assert engine.resolve_mountain(7.5)[0] == "癸"
        # 7.4 is end of 子
        assert engine.resolve_mountain(7.4)[0] == "子"


class TestXuanKongFlyStars:
    """Verify forward and backward flying star tracks."""

    def test_fly_stars_forward_from_center_9(self):
        engine = XuanKongEngine()
        # Forward flight: sequence 5->6->7->8->9->1->2->3->4
        tracks = engine.fly_stars(center_star=9, is_forward=True)
        assert tracks == {
            5: 9, 6: 1, 7: 2, 8: 3, 9: 4, 1: 5, 2: 6, 3: 7, 4: 8
        }
        # Invariant: all 9 stars present exactly once
        assert set(tracks.values()) == set(range(1, 10))

    def test_fly_stars_backward_from_center_9(self):
        engine = XuanKongEngine()
        # Backward flight: sequence 5->6->7->8->9->1->2->3->4
        tracks = engine.fly_stars(center_star=9, is_forward=False)
        assert tracks == {
            5: 9, 6: 8, 7: 7, 8: 6, 9: 5, 1: 4, 2: 3, 3: 2, 4: 1
        }
        assert set(tracks.values()) == set(range(1, 10))

    def test_fly_stars_all_center_stars_permutations(self):
        engine = XuanKongEngine()
        for center in range(1, 10):
            for is_fwd in (True, False):
                tracks = engine.fly_stars(center, is_fwd)
                assert len(tracks) == 9
                assert tracks[5] == center
                assert set(tracks.values()) == set(range(1, 10))


class TestXuanKongPeriod9Grid:
    """Verify Period 9 base chart and 9-palace grid layout."""

    def test_period_9_base_chart_center_is_9(self):
        assert PERIOD_9_BASE_CHART[5] == 9

    def test_chart_calculation_facing_south_wu(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(facing_degree=180.0, period=9)

        assert chart["facing_mountain"] == "午 (離卦 - 陰)"
        assert chart["sitting_mountain"] == "子 (坎卦 - 陰)"
        assert chart["period"] == 9

        palaces = chart["grid_palaces"]
        assert len(palaces) == 9

        palace_numbers = [p["palace_number"] for p in palaces]
        assert palace_numbers == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_chart_calculation_facing_north_zi(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(facing_degree=0.0, period=9)

        assert chart["facing_mountain"] == "子 (坎卦 - 陰)"
        assert chart["sitting_mountain"] == "午 (離卦 - 陰)"
        assert len(chart["grid_palaces"]) == 9

    def test_chart_calculation_facing_northeast_gen(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(facing_degree=45.0, period=9)

        assert chart["facing_mountain"] == "艮 (艮卦 - 陽)"
        assert chart["sitting_mountain"] == "坤 (坤卦 - 陽)"
        assert len(chart["grid_palaces"]) == 9


class TestXuanKongEngineChartResultInvariants:
    """Verify EngineChartResult contract invariants and serialization."""

    def test_calculate_chart_payload_structure(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(135.0, period=9)

        assert isinstance(chart, EngineChartResult)
        assert isinstance(chart, dict)
        assert chart.engine_name == "Xuan Kong Flying Stars Engine"
        assert chart.system_type == "xiang_xue"
        assert chart["engine"] == "XuanKongEngine"
        assert chart["period"] == 9
        assert chart["facing_degree"] == 135.0
        assert "facing_mountain" in chart
        assert "sitting_mountain" in chart

        palaces = chart["grid_palaces"]
        assert len(palaces) == 9
        for p in palaces:
            assert "palace_number" in p
            assert "palace_name" in p
            assert "direction" in p
            assert "base_star" in p
            assert "sitting_star" in p
            assert "facing_star" in p
            assert "facing_star_name" in p
            assert 1 <= p["base_star"] <= 9
            assert 1 <= p["sitting_star"] <= 9
            assert 1 <= p["facing_star"] <= 9
            assert p["facing_star_name"] == STAR_NAMES[p["facing_star"]]

    def test_generic_calculate_interface(self):
        engine = XuanKongEngine()
        res1 = engine.calculate(270.0, period=9)
        res2 = engine.calculate_chart(270.0, period=9)
        assert res1["facing_mountain"] == res2["facing_mountain"]
        assert res1["sitting_mountain"] == res2["sitting_mountain"]

    def test_json_serialization(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(90.0, period=9)
        serialized = json.dumps(chart)
        deserialized = json.loads(serialized)

        assert deserialized["engine_name"] == "Xuan Kong Flying Stars Engine"
        assert deserialized["system_type"] == "xiang_xue"
        assert len(deserialized["grid_palaces"]) == 9
        assert "calculation_timestamp" in deserialized

    def test_to_dict_method(self):
        engine = XuanKongEngine()
        chart = engine.calculate_chart(315.0, period=9)
        d = chart.to_dict()
        assert isinstance(d, dict)
        assert d["engine"] == "XuanKongEngine"
        assert len(d["grid_palaces"]) == 9
