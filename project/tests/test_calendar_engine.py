"""
project/tests/test_calendar_engine.py
=====================================
Unit and integration tests for Astrological Calendar & Date Selection Engine:
  1. Test 60 Jia-Zi daily pillar derivation.
  2. Test 12 Day Duty Officers and 28 Mansions calculations.
  3. Test Monthly Calendar generation and intent-based date finder.
  4. Test FastAPI endpoints GET /api/v1/calendar/month & POST /api/v1/calendar/query-dates.
  5. Test HTML markup and JS function parity across static and public folders.
"""

from datetime import date
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from project.core.calendar_engine import (
    CalendarEngine, calendar_engine, DUTY_OFFICERS, LUNAR_MANSIONS
)
from project.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


class TestCalendarEngineAlgorithms:
    """Test core deterministic algorithms for calendar and date selection."""

    def test_day_pillar_generation(self):
        dt = date(2026, 8, 16)
        stem, branch = CalendarEngine.get_day_pillar(dt)
        assert stem in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        assert branch in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    def test_duty_officer_calculation(self):
        for m in range(1, 13):
            for b in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
                off = CalendarEngine.calculate_duty_officer(m, b)
                assert off in DUTY_OFFICERS

    def test_lunar_mansion_calculation(self):
        dt = date(2026, 8, 16)
        mansion = CalendarEngine.calculate_lunar_mansion(dt)
        assert mansion in LUNAR_MANSIONS

    def test_generate_monthly_calendar(self):
        data = CalendarEngine.generate_monthly_calendar(2026, 8, user_day_master="甲", user_zodiac="子")
        assert data["year"] == 2026
        assert data["month"] == 8
        assert data["total_days"] == 31
        assert len(data["days"]) == 31
        first_day = data["days"][0]
        assert "officer" in first_day
        assert "score" in first_day
        assert "suitable" in first_day

    def test_find_best_dates(self):
        best = CalendarEngine.find_best_dates(
            intent="business_opening",
            start_date="2026-08-01",
            days_ahead=30,
            user_day_master="甲",
            user_zodiac="子"
        )
        assert len(best) > 0
        assert all(b["officer"] in ["開", "成", "滿", "建"] for b in best)
        assert best[0]["score"] >= best[-1]["score"]


class TestCalendarAPIEndpoints:
    """Test API endpoint contract for calendar features."""

    def test_get_monthly_calendar_endpoint(self):
        resp = client.get("/api/v1/calendar/month?year=2026&month=8")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2026
        assert data["month"] == 8
        assert len(data["days"]) == 31

    def test_query_dates_endpoint(self):
        payload = {
            "intent": "marriage_ceremony",
            "start_date": "2026-08-01",
            "days_ahead": 30,
            "user_day_master": "甲",
            "user_zodiac": "子"
        }
        resp = client.post("/api/v1/calendar/query-dates", json=payload)
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        assert len(results) > 0


class TestCalendarUIIntegration:
    """Verify HTML markup, CSS, and JS integration."""

    def test_index_html_has_calendar_elements(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="calendar-view-card"' in html
            assert 'id="calendar-grid-container"' in html
            assert 'id="calendar-current-month-badge"' in html

    def test_app_js_has_calendar_functions(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "loadMonthCalendar" in js
            assert "changeCalendarMonth" in js
            assert "filterCalendarIntent" in js
            assert "renderCalendarGrid" in js

    def test_i18n_has_calendar_keys(self):
        for subpath in ["project/static/i18n.js", "public/i18n.js"]:
            content = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "calendar_title" in content
            assert "intent_all" in content
            assert "intent_business" in content
