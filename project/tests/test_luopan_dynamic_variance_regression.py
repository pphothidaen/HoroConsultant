"""
project/tests/test_luopan_dynamic_variance_regression.py
========================================================
Comprehensive Regression Test Suite for Dynamic LuoPan 24-Mountain &
Period 9 Xuan Kong Flying Star 9-Palace Compass Engine.

Tests:
1. 24-Mountain boundary calculations across all 360 degrees.
2. Dynamic 9-palace flying star sector transitions across all 8 primary directions.
3. Facing Star (向星) and Mountain Sitting Star (山星) score and role verification.
4. Afflicted sectors (5 Yellow & 2 Black) position rotation and cure validation.
5. Typo regression check (ensuring SW is correctly spelled as ทิศตะวันตกเฉียงใต้).
6. FastAPI /api/v1/luopan/calculate contract and response variance.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from project.main import app
from project.core.luopan_dream_engine import LuoPanDreamEngine, calculate_dynamic_period9_sectors

client = TestClient(app)

CARDINAL_TEST_ORIENTATIONS = [
    (0.0, "N", "S", "1 ขาว (向星", "9 ม่วง (山星"),
    (45.0, "NE", "SW", "7 แดง (向星", "1 ขาว (山星"),
    (90.0, "E", "W", "8 ขาว (向星", "4 เขียว (山星"),
    (135.0, "SE", "NW", "9 ม่วง (向星", "6 ขาว (山星"),
    (180.0, "S", "N", "9 ม่วง (向星", "9 ม่วง (山星"),
    (225.0, "SW", "NE", "1 ขาว (向星", "7 แดง (山星"),
    (270.0, "W", "E", "4 เขียว (向星", "8 ขาว (山星"),
    (315.0, "NW", "SE", "6 ขาว (向星", "9 ม่วง (山星"),
]


class TestLuoPan24MountainBoundaries:
    """Validate full 360-degree 24-mountain coverage without overlap or gaps."""

    def test_24_unique_mountains_discovered(self):
        facing_mountains = set()
        for deg in range(0, 360, 5):
            res = LuoPanDreamEngine.calculate_mountain(float(deg))
            facing_mountains.add(res["facing_mountain"])
        assert len(facing_mountains) == 24, f"Expected 24 unique mountains, got {len(facing_mountains)}"

    def test_opposite_sitting_mountain_is_always_180_deg_offset(self):
        for deg in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 15.0, 105.0]:
            facing = LuoPanDreamEngine.calculate_mountain(deg)
            sitting = LuoPanDreamEngine.calculate_mountain((deg + 180.0) % 360.0)
            assert facing["sitting_mountain"] == sitting["facing_mountain"]


class TestLuoPanDynamic9PalaceSectors:
    """Validate that 9-palace flying star sectors shift dynamically per facing degree."""

    @pytest.mark.parametrize("facing_deg, facing_key, sitting_key, facing_star_prefix, sitting_star_prefix", CARDINAL_TEST_ORIENTATIONS)
    def test_facing_and_sitting_palaces_receive_correct_stars_and_scores(
        self, facing_deg, facing_key, sitting_key, facing_star_prefix, sitting_star_prefix
    ):
        res = LuoPanDreamEngine.calculate_luopan_heatmap(facing_deg, period=9)
        sectors = res["sectors"]

        # Facing palace assertions
        assert facing_key in sectors
        assert facing_star_prefix in sectors[facing_key]["star"]
        assert sectors[facing_key]["heat_score"] >= 95, "Facing palace should receive high prosperity score"

        # Sitting palace assertions
        assert sitting_key in sectors
        assert sitting_star_prefix in sectors[sitting_key]["star"]
        assert sectors[sitting_key]["heat_score"] >= 90, "Sitting palace should receive mountain support score"

    def test_sector_variance_between_opposite_directions(self):
        """North-facing and South-facing buildings must have distinct sector distributions."""
        north_res = LuoPanDreamEngine.calculate_luopan_heatmap(0.0, period=9)["sectors"]
        south_res = LuoPanDreamEngine.calculate_luopan_heatmap(180.0, period=9)["sectors"]

        # Sector N should be Facing in North building, but Sitting in South building
        assert "向星" in north_res["N"]["star"]
        assert "山星" in south_res["N"]["star"]

        # Calamity 5 Yellow should be in East for North building, but Northwest for South building
        assert "5 เหลือง" in north_res["E"]["star"]
        assert "5 เหลือง" in south_res["NW"]["star"]

    def test_southwest_typo_regression_guard(self):
        """Ensure SW sector is spelled ทิศตะวันตกเฉียงใต้ and never mistaken for Southeast."""
        for deg in [0.0, 90.0, 180.0, 270.0, 225.0]:
            sectors = calculate_dynamic_period9_sectors(deg, period=9)
            sw_name = sectors["SW"]["sector"]
            assert "ทิศตะวันตกเฉียงใต้" in sw_name
            assert "Southwest" in sw_name
            assert "ทิศต.อ.เฉียงใต้" not in sw_name


class TestLuoPanAPIEndpointContract:
    """Validate FastAPI router for /api/v1/luopan/calculate."""

    def test_calculate_luopan_post_endpoint(self):
        payload = {"facing_degree": 90.0, "period": 9}
        resp = client.post("/api/v1/luopan/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["period"] == 9
        assert data["facing_degree"] == 90.0
        assert "mountain" in data
        assert data["mountain"]["facing_mountain"] == "卯 (Mao)"
        assert "sectors" in data
        assert len(data["sectors"]) == 9
        assert "向星 - ประตูหน้ามหาเศรษฐี" in data["sectors"]["E"]["star"]

    def test_calculate_luopan_zero_degree_north(self):
        payload = {"facing_degree": 0.0, "period": 9}
        resp = client.post("/api/v1/luopan/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["facing_degree"] == 0.0
        assert data["mountain"]["facing_mountain"] == "子 (Zi)"
        assert "向星 - ประตูหน้าปัญญารับทรัพย์" in data["sectors"]["N"]["star"]
