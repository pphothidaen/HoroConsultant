"""
project/tests/test_web_regression.py
======================================
Web UX/UI & FastAPI Server Full Regression Test Suite.

Verifies:
  - Static Web Dashboard UI routes (HTML, CSS, JS)
  - API Endpoints (/calculate, /interpret, /validate, /eot, /health)
  - True Solar Time & Five Elements calculations
  - Gemini Prediction Validator Agent integration

Usage:
  python -m pytest project/tests/test_web_regression.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.main import app

client = TestClient(app)


class TestWebRegressionUI:
    """Regression tests for Web UI Dashboard assets and routes."""

    def test_ui_index_html_loads(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "<title>" in res.text
        assert "HORO CONSULTANT" in res.text
        assert "bazi-form" in res.text

    def test_ui_static_css_loads(self):
        res = client.get("/static/style.css")
        assert res.status_code == 200
        assert "--bg-dark" in res.text
        assert "glass-card" in res.text

    def test_ui_static_js_loads(self):
        res = client.get("/static/app.js")
        assert res.status_code == 200
        assert "calculateChart" in res.text
        assert "renderResults" in res.text


class TestAPIRegressionEndpoints:
    """Regression tests for FastAPI backend routes."""

    def test_health_check(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "Computational Metaphysics Engine" in data["service"]

    def test_equation_of_time(self):
        res = client.get("/api/v1/eot?date=2026-08-03")
        assert res.status_code == 200
        data = res.json()
        assert data["date"] == "2026-08-03"
        assert "eot_minutes" in data
        assert isinstance(data["eot_minutes"], float)

    def test_bazi_calculate(self):
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "unknown_hour": False,
        }
        res = client.post("/api/v1/bazi/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "pillars" in data
        assert "day_master" in data
        assert "five_elements" in data
        assert data["day_master"]["stem"] == "庚"

    def test_bazi_interpret_basic(self):
        from unittest.mock import patch
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "query": "วิเคราะห์การงาน",
            "enable_validation": False,
        }
        mock_ai = {
            "text": "ดวงชะตานี้มี Day Master เป็น 庚金",
            "model_used": "qwen2.5:7b",
            "route": "ollama_primary",
            "latency_ms": 120,
        }
        with patch("project.main.router.generate", return_value=mock_ai):
            res = client.post("/api/v1/bazi/interpret", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert "chart" in data
            assert "interpretation" in data
            assert data["route"] == "ollama_primary"

    def test_bazi_validate_endpoint(self):
        chart = {
            "day_master": {"stem": "庚", "element": "Metal", "polarity": "Yang"},
            "five_elements": {"percentages": {"Metal": 20, "Fire": 30}},
        }
        payload = {
            "bazi_chart": chart,
            "initial_interpretation": "เจ้าชะตามี Day Master เป็น庚金",
            "query": "ตรวจสอบตรรกะธาตุ",
        }
        res = client.post("/api/v1/bazi/validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "validation_status" in data
        assert "peer_perspective" in data

    def test_location_resolve_endpoint(self):
        from unittest.mock import patch, MagicMock
        payload = {"location": "บางกะปิ, กรุงเทพ"}
        
        mock_location = MagicMock()
        mock_location.latitude = 13.7667
        mock_location.longitude = 100.6500
        mock_location.address = "Bang Kapi, Bangkok, Thailand"

        with patch("geopy.geocoders.Nominatim.geocode", return_value=mock_location):
            with patch("timezonefinder.TimezoneFinder.timezone_at", return_value="Asia/Bangkok"):
                res = client.post("/api/v1/location/resolve", json=payload)
                assert res.status_code == 200
                data = res.json()
                assert "latitude" in data
                assert "longitude" in data
                assert "timezone" in data
                assert "utc_offset_hours" in data
                assert data["timezone"] == "Asia/Bangkok"
