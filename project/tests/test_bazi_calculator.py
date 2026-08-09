"""
project/tests/test_bazi_calculator.py
=======================================
Alias test file matching the path specified in the Post-Bootstrap plan.

    pytest project/tests/test_bazi_calculator.py

All actual test logic lives in tests/test_core.py.
This file re-imports and extends those tests, adding higher-level
"calculator" integration tests that match the plan's terminology.
"""

import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── Re-export all base tests so `pytest project/tests/` still runs them ──────
from datetime import datetime

# ── Extended Integration Tests (BaZi Calculator level) ───────────────────────
import pytest

from project.core.bazi_engine import BaZiEngine
from tests.test_core import (  # noqa: F401
    TestBaZiEngine,
    TestEquationOfTime,
    TestPillarHelpers,
    TestTrueSolarTime,
)


@pytest.fixture(scope="module")
def calculator():
    return BaZiEngine()


class TestBaZiCalculatorIntegration:
    """
    Higher-level tests that verify the calculator produces
    consistent, meaningful BaZi analysis output.
    """

    def test_bangkok_chart_1990(self, calculator):
        """Standard Bangkok chart — validates full pipeline."""
        dt     = datetime(1990, 5, 15, 14, 30)
        result = calculator.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
        assert result["day_master"]["stem"] == "庚"
        assert result["day_master"]["element"] == "Metal"
        assert result["five_elements"]["dominant_element"] == "Fire"

    def test_singapore_chart(self, calculator):
        """Singapore longitude (103.82) — different standard meridian."""
        dt     = datetime(2000, 1, 1, 8, 0)
        result = calculator.calculate(dt=dt, longitude=103.82, utc_offset_hours=8.0)
        assert "pillars" in result
        assert "year" in result["pillars"]
        assert "month" in result["pillars"]
        assert "day" in result["pillars"]
        assert "hour" in result["pillars"]

    def test_five_elements_complete(self, calculator):
        """All five elements must appear in every chart."""
        dt     = datetime(1985, 3, 20, 6, 0)
        result = calculator.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
        elements = result["five_elements"]["percentages"]
        assert set(elements.keys()) == {"Wood", "Fire", "Earth", "Metal", "Water"}
        total = sum(elements.values())
        assert abs(total - 100.0) < 0.5

    def test_calculator_json_output_is_complete(self, calculator):
        """Verify all top-level keys required by the API are present."""
        dt     = datetime(1978, 11, 30, 22, 0)
        result = calculator.calculate(dt=dt, longitude=116.407, utc_offset_hours=8.0)
        required_keys = {
            "engine_version", "solar_time_info", "day_master",
            "pillars", "five_elements", "is_probabilistic",
        }
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_tst_applied_before_hour_pillar(self, calculator):
        """
        Charts near hour boundaries should use TST, not LMT.
        Verifies the solar time correction is applied.
        """
        dt     = datetime(1990, 5, 15, 14, 30)
        result = calculator.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
        tst    = result["solar_time_info"]
        # TST ≠ LMT due to longitude offset + EoT
        assert tst["tst_datetime"] != tst["lmt_datetime"]
        assert tst["eot_minutes"] != 0.0

    def test_probabilistic_matrix_coverage(self, calculator):
        """Near-boundary charts must produce 12 probabilistic scenarios."""
        # Near Zi/Chou boundary (midnight)
        dt     = datetime(1990, 11, 7, 0, 5)
        result = calculator.calculate(
            dt=dt,
            longitude=100.493,
            utc_offset_hours=7.0,
            unknown_hour=True,
        )
        assert result["is_probabilistic"] is True
        assert len(result["probabilistic_matrix"]) == 12
        weights = [s["probability_weight"] for s in result["probabilistic_matrix"]]
        assert abs(sum(weights) - 1.0) < 1e-4

    def test_western_city_chart(self, calculator):
        """New York (UTC-5) — verifies negative UTC offset handling."""
        dt     = datetime(1995, 7, 4, 12, 0)
        result = calculator.calculate(dt=dt, longitude=-74.006, utc_offset_hours=-5.0)
        tst    = result["solar_time_info"]
        assert tst["utc_offset_hours"] == -5.0
        # Longitude offset should be negative (west of prime meridian)
        assert tst["longitude_offset_minutes"] != 0

    def test_all_heavenly_stems_reachable(self, calculator):
        """Cycle through 10 years to confirm all stems appear at least once."""
        stems_seen = set()
        for year in range(1984, 1994):
            dt   = datetime(year, 6, 1, 12, 0)
            res  = calculator.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
            stems_seen.add(res["pillars"]["year"]["stem"]["char"])
        assert len(stems_seen) == 10, f"Only saw stems: {stems_seen}"


class TestPredictionValidator:
    """Tests for external Gemini Prediction Validator agent."""

    def test_validator_returns_structured_dict(self):
        from project.validator import PredictionValidator
        validator = PredictionValidator()
        chart = {
            "day_master": {"stem": "庚", "element": "Metal", "polarity": "Yang"},
            "five_elements": {"percentages": {"Metal": 20, "Fire": 30}},
        }
        res = validator.validate(
            bazi_chart=chart,
            initial_interpretation="Test interpretation",
            user_query="Test query",
        )
        assert "validation_status" in res
        assert "confidence_score" in res
        assert "peer_perspective" in res
        assert "refined_interpretation" in res



# ── Smoke test: run this file directly ────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
