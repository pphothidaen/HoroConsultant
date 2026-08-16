"""
project/tests/test_synastry_engine.py
=====================================
Unit and integration tests for Multi-Profile Synastry & Partner Compatibility Matrix:
  1. Test Day Master Affinity (Stem Combination, Generation, Overcoming).
  2. Test Spouse Palace Affinity (Branch Combination, Clash, Harm).
  3. Test full synastry calculation and 4-tier score generation.
  4. Test FastAPI endpoint POST /api/v1/synastry/analyze.
  5. Test Frontend HTML/JS/i18n bindings in static and public paths.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from project.core.synastry_engine import SynastryEngine, synastry_engine
from project.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


class TestSynastryEngineCalculations:
    """Test core algorithmic rules for Day Master and Spouse Palace compatibility."""

    def test_day_master_combinations(self):
        # Jia (甲) + Ji (己) = Earth Combination
        res = SynastryEngine.analyze_day_master_affinity("甲", "己")
        assert res["type"] == "STEM_COMBINATION"
        assert res["score"] == 30
        assert res["element"] == "Earth"

    def test_day_master_generating(self):
        # Jia (甲: Wood) + Bing (丙: Fire) = Generating
        res = SynastryEngine.analyze_day_master_affinity("甲", "丙")
        assert res["type"] == "ELEMENT_GENERATING"
        assert res["score"] == 26

    def test_spouse_palace_combinations_and_clashes(self):
        # Zi (子) + Chou (丑) = Branch Combination
        res_comb = SynastryEngine.analyze_spouse_palace_affinity("子", "丑")
        assert res_comb["type"] == "BRANCH_COMBINATION"
        assert res_comb["score"] == 30
        assert res_comb["favorable"] is True

        # Zi (子) + Wu (午) = Branch Clash
        res_clash = SynastryEngine.analyze_spouse_palace_affinity("子", "午")
        assert res_clash["type"] == "BRANCH_CLASH"
        assert res_clash["score"] == 8
        assert res_clash["favorable"] is False

    def test_calculate_synastry_composite(self):
        chart_a = {
            "day_master": {"stem": "甲"},
            "pillars": {
                "day": {"stem": {"char": "甲"}, "branch": {"char": "子"}}
            }
        }
        chart_b = {
            "day_master": {"stem": "己"},
            "pillars": {
                "day": {"stem": {"char": "己"}, "branch": {"char": "丑"}}
            }
        }
        res = SynastryEngine.calculate_synastry(chart_a, chart_b)
        assert res["composite_score"] >= 85
        assert res["grade"] in ("A+", "A")
        assert "romantic_harmony" in res["dimensions"]
        assert "business_synergy" in res["dimensions"]
        assert len(res["advice"]) > 0


class TestSynastryAPIEndpoint:
    """Test API endpoint contract for /api/v1/synastry/analyze."""

    def test_synastry_api_success(self):
        payload = {
            "person_a": {
                "name": "Somchai",
                "birth_datetime": "1990-05-15 14:30:00",
                "longitude": 100.493,
                "utc_offset_hours": 7.0,
                "gender": "male"
            },
            "person_b": {
                "name": "Somsri",
                "birth_datetime": "1992-08-20 10:15:00",
                "longitude": 100.493,
                "utc_offset_hours": 7.0,
                "gender": "female"
            },
            "relation_type": "romantic",
            "language": "th"
        }
        resp = client.post("/api/v1/synastry/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "composite_score" in data
        assert "grade" in data
        assert "dimensions" in data
        assert data["person_a"]["name"] == "Somchai"
        assert data["person_b"]["name"] == "Somsri"


class TestSynastryUIIntegration:
    """Verify HTML markup, CSS, and JS integration parity."""

    def test_index_html_has_synastry_elements(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="toggle-synastry-mode"' in html, f"Missing toggle in {subpath}"
            assert 'id="partner-b-section"' in html, f"Missing partner-b-section in {subpath}"
            assert 'id="synastry-result-card"' in html, f"Missing synastry-result-card in {subpath}"

    def test_app_js_has_synastry_functions(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "toggleSynastryMode" in js
            assert "calcSynastry" in js
            assert "renderSynastryResult" in js

    def test_i18n_has_synastry_keys(self):
        for subpath in ["project/static/i18n.js", "public/i18n.js"]:
            content = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "synastry_mode_title" in content
            assert "partner_b_title" in content
            assert "synastry_result_title" in content
