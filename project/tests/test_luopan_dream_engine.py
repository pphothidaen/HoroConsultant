"""
project/tests/test_luopan_dream_engine.py
=========================================
Unit and integration tests for LuoPan 24-Mountain Compass, Period 9 Heatmap & Dream Decoder:
  1. Test 24-Mountain degree to mountain name & element calculation.
  2. Test Period 9 9-Palace sector heatmap calculation.
  3. Test Dream semantic symbol decoding and Sattaleka lucky number generation.
  4. Test FastAPI endpoints POST /api/v1/luopan/calculate & POST /api/v1/dream/interpret.
  5. Test HTML/CSS/JS/i18n bindings in static and public paths.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from project.core.luopan_dream_engine import (
    LuoPanDreamEngine, luopan_dream_engine, MOUNTAINS_24, PERIOD_9_SECTORS
)
from project.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


class TestLuoPanAlgorithms:
    """Test 24-Mountain compass and Period 9 Flying Star mathematics."""

    def test_24_mountain_cardinal_directions(self):
        # 0 deg = North Zi
        m_north = LuoPanDreamEngine.calculate_mountain(0.0)
        assert "Zi" in m_north["facing_mountain"]
        assert m_north["facing_direction"] == "N"
        assert m_north["facing_element"] == "Water"

        # 90 deg = East Mao
        m_east = LuoPanDreamEngine.calculate_mountain(90.0)
        assert "Mao" in m_east["facing_mountain"]
        assert m_east["facing_direction"] == "E"

        # 180 deg = South Wu
        m_south = LuoPanDreamEngine.calculate_mountain(180.0)
        assert "Wu" in m_south["facing_mountain"]
        assert m_south["facing_direction"] == "S"

    def test_luopan_heatmap_period_9(self):
        res_south = LuoPanDreamEngine.calculate_luopan_heatmap(180.0, period=9)
        assert res_south["period"] == 9
        assert "sectors" in res_south
        assert "S" in res_south["sectors"]
        assert "NW" in res_south["sectors"]
        assert res_south["sectors"]["S"]["heat_score"] >= 90  # Facing Palace South 9 Purple
        assert res_south["sectors"]["NW"]["heat_score"] <= 30  # Calamity 5 Yellow

        # When facing North (0 deg), sectors dynamically adjust
        res_north = LuoPanDreamEngine.calculate_luopan_heatmap(0.0, period=9)
        assert res_north["sectors"]["N"]["heat_score"] >= 90  # Facing Palace North 1 White
        assert res_north["sectors"]["E"]["heat_score"] <= 30  # Calamity 5 Yellow
        assert res_north["sectors"]["N"]["star"] != res_south["sectors"]["N"]["star"]


class TestDreamDecoderAlgorithms:
    """Test dream semantic symbol recognition, I Ching hexagram, and Sattaleka numbers."""

    def test_interpret_water_and_dragon_dream(self):
        res = LuoPanDreamEngine.interpret_dream("เมื่อคืนฝันเห็นพญานาคสีทองเล่นน้ำในแม่น้ำใหญ่")
        assert len(res["symbols_detected"]) > 0
        assert len(res["lucky_numbers"]) > 0
        assert "hexagram_alignment" in res
        assert "omen" in res

    def test_interpret_generic_dream(self):
        res = LuoPanDreamEngine.interpret_dream("ฝันแปลกๆ จำรายละเอียดไม่ค่อยได้")
        assert len(res["lucky_numbers"]) > 0
        assert "hexagram_alignment" in res


class TestLuoPanDreamAPIEndpoints:
    """Test API endpoint contract for LuoPan and Dream Decoder."""

    def test_luopan_api_endpoint(self):
        resp = client.post("/api/v1/luopan/calculate", json={"facing_degree": 180.0, "period": 9})
        assert resp.status_code == 200
        data = resp.json()
        assert "mountain" in data
        assert "sectors" in data

    def test_dream_api_endpoint(self):
        resp = client.post("/api/v1/dream/interpret", json={"dream_text": "ฝันเห็นพระพุทธรูปทองคำเปล่งแสงสว่าง"})
        assert resp.status_code == 200
        data = resp.json()
        assert "lucky_numbers" in data
        assert "hexagram_alignment" in data


class TestLuoPanDreamUIIntegration:
    """Verify HTML markup and JS function parity."""

    def test_index_html_has_luopan_and_dream_elements(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="luopan-heatmap-card"' in html
            assert 'id="luopan-sector-grid"' in html
            assert 'id="dream-interpreter-card"' in html
            assert 'id="dream-result-box"' in html

    def test_app_js_has_luopan_and_dream_functions(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "calcLuoPan" in js
            assert "renderLuoPanHeatmap" in js
            assert "submitDreamInterpretation" in js
            assert "renderDreamResult" in js

    def test_i18n_has_luopan_and_dream_keys(self):
        for subpath in ["project/static/i18n.js", "public/i18n.js"]:
            content = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "luopan_title" in content
            assert "dream_title" in content
            assert "btn_interpret_dream" in content
