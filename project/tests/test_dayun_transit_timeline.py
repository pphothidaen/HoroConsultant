"""
project/tests/test_dayun_transit_timeline.py
============================================
Regression and unit tests for Interactive DaYun Timeline Scrubber & Live Sky Clock:
  1. Test TransitEngine annual pillar calculation (60 Jia-Zi cycles).
  2. Test Stem-Branch combinations, clashes, harmonies, and harms.
  3. Test analyze_natal_transit_aspects overall score and categorization.
  4. Test get_live_sky_pillars format and components.
  5. Test HTML and CSS integration parity between static and public.
"""

from datetime import datetime
from pathlib import Path
import pytest
from project.core.transit_engine import TransitEngine, transit_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def sample_natal_chart():
    return {
        "day_master": {"stem": "甲", "element": "Wood", "polarity": "Yang"},
        "pillars": {
            "year": {"stem": {"char": "庚"}, "branch": {"char": "午"}},
            "month": {"stem": {"char": "辛"}, "branch": {"char": "巳"}},
            "day": {"stem": {"char": "甲"}, "branch": {"char": "子"}},
            "hour": {"stem": {"char": "辛"}, "branch": {"char": "未"}},
        }
    }


class TestTransitEngine:
    """Test mathematical engine for 60 Jia-Zi cycles and transit aspects."""

    def test_annual_pillar_cycles(self):
        p1984 = TransitEngine.get_annual_pillar(1984)
        assert p1984["pillar_str"] == "甲子"
        assert p1984["stem"] == "甲"
        assert p1984["branch"] == "子"

        p2024 = TransitEngine.get_annual_pillar(2024)
        assert p2024["pillar_str"] == "甲辰"

        p2026 = TransitEngine.get_annual_pillar(2026)
        assert p2026["pillar_str"] == "丙午"
        assert p2026["stem_element"] == "Fire"
        assert p2026["branch_element"] == "Fire"

    def test_natal_transit_aspect_detection(self, sample_natal_chart):
        # 2026 is Bing Wu (丙午)
        # Natal Day is Jia Zi (甲子) -> Zi clashes with Wu (子午相沖)
        # Natal Year has Geng Wu (庚午)
        res = TransitEngine.analyze_natal_transit_aspects(
            natal_chart=sample_natal_chart,
            transit_year=2026,
            transit_age=36
        )
        assert res["transit_year"] == 2026
        assert res["transit_age"] == 36
        assert "aspects" in res
        assert len(res["aspects"]) > 0

        # Check for Zi-Wu clash in aspects
        clash_found = any(a.get("type") == "CLASH" and "子午" in a.get("name", "") for a in res["aspects"])
        assert clash_found, "Must detect Zi-Wu clash with Natal Day Branch"

    def test_stem_combination_detection(self, sample_natal_chart):
        # 2019 is Ji Hai (己亥)
        # Natal Day Master is Jia (甲) -> Jia-Ji Earth combination (甲己合土)
        res = TransitEngine.analyze_natal_transit_aspects(
            natal_chart=sample_natal_chart,
            transit_year=2019,
            transit_age=29
        )
        comb_found = any(a.get("type") == "COMBINATION" and a.get("element") == "Earth" for a in res["aspects"])
        assert comb_found, "Must detect Jia-Ji Earth combination"

    def test_live_sky_pillars_generation(self):
        dt = datetime(2026, 8, 16, 14, 30, 0)
        sky = TransitEngine.get_live_sky_pillars(dt=dt, longitude=100.493, utc_offset_hours=7.0)

        assert "pillars_str" in sky
        assert "year_pillar" in sky
        assert "month_pillar" in sky
        assert "day_pillar" in sky
        assert "hour_pillar" in sky
        assert "2026-08-16" in sky["timestamp"]


class TestTimelineUIIntegration:
    """Verify DOM element parity and styles for Live Clock and Timeline Scrubber."""

    def test_index_html_has_sky_clock_and_scrubber(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="sky-clock-widget"' in html, f"Missing sky-clock-widget in {subpath}"
            assert 'id="sky-clock-pillars"' in html, f"Missing sky-clock-pillars in {subpath}"
            assert 'id="timeline-scrubber-card"' in html, f"Missing timeline-scrubber-card in {subpath}"
            assert 'id="timeline-age-slider"' in html, f"Missing timeline-age-slider in {subpath}"
            assert 'id="timeline-aspects-container"' in html, f"Missing timeline-aspects-container in {subpath}"

    def test_style_css_has_timeline_classes(self):
        for subpath in ["project/static/style.css", "public/style.css"]:
            css = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert ".sky-clock-widget" in css, f"Missing .sky-clock-widget in {subpath}"
            assert ".timeline-slider" in css, f"Missing .timeline-slider in {subpath}"
            assert ".aspect-card" in css, f"Missing .aspect-card in {subpath}"

    def test_app_js_has_timeline_functions(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "startLiveSkyClock" in js, f"Missing startLiveSkyClock in {subpath}"
            assert "initDaYunTimeline" in js, f"Missing initDaYunTimeline in {subpath}"
            assert "onTimelineSliderChange" in js, f"Missing onTimelineSliderChange in {subpath}"
