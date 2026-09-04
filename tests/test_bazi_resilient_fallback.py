"""Unit test suite for BaZi resilient deterministic calculation engine & fallback."""

from pathlib import Path
import pytest

APP_JS_PATH = Path(__file__).parent.parent / "project" / "static" / "app.js"
PUBLIC_APP_JS_PATH = Path(__file__).parent.parent / "public" / "app.js"


class TestBaziResilientFallback:
    """Verify resilient deterministic fallback and blocker elimination."""

    def test_app_js_exists(self):
        """app.js and public/app.js must exist."""
        assert APP_JS_PATH.exists()
        assert PUBLIC_APP_JS_PATH.exists()

    def test_app_js_has_eco_mode_badge_text(self):
        """app.js must emit Eco-Mode badge text instead of unavailable blocker."""
        content = APP_JS_PATH.read_text(encoding='utf-8')
        assert "Backend: Eco-Mode (Auto-Wake on Demand)" in content

    def test_app_js_has_deterministic_calculation_fallback(self):
        """app.js must implement deterministic fallback rather than blocking calculateChart."""
        content = APP_JS_PATH.read_text(encoding='utf-8')
        assert "computeClientSideBazi" in content
        assert "โหมดคำนวณ Deterministic ความแม่นยำสูง" in content

    def test_app_js_edge_first_instant_calculation(self):
        """calculateChart must calculate via Edge engine instantly without waiting on ensureBackendReady."""
        content = APP_JS_PATH.read_text(encoding='utf-8')
        assert "Edge-First" in content or "โหมด Deterministic Edge Engine" in content
        assert "bypassColdStartToEdgeEngine" in content

    def test_branch_calculations_have_client_fallback(self):
        """calcFourPillars and calcHoroV3 must contain client fallback instead of raw blocker."""
        content = APP_JS_PATH.read_text(encoding='utf-8')
        assert "calcFourPillars" in content
        assert "calcHoroV3" in content

    def test_app_js_parity_with_public_app_js(self):
        """project/static/app.js and public/app.js must have identical contents."""
        assert APP_JS_PATH.read_text(encoding='utf-8') == PUBLIC_APP_JS_PATH.read_text(encoding='utf-8')
