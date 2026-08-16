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


class TestBaZiRustParityOracleFixtures:
    """Literal Python-oracle fixtures consumed by the Rust parity gate."""

    def test_bangkok_full_calculation_golden(self, calculator):
        result = calculator.calculate(
            datetime(1990, 5, 15, 14, 30, 0),
            longitude=100.493,
            utc_offset_hours=7.0,
        )
        assert result["solar_time_info"] == {
            "input_datetime": "1990-05-15 14:30:00",
            "longitude": 100.493,
            "utc_offset_hours": 7.0,
            "standard_meridian": 105.0,
            "longitude_offset_minutes": -18.028,
            "eot_minutes": 3.9239,
            "lmt_datetime": "1990-05-15 14:11:58",
            "tst_datetime": "1990-05-15 14:15:53",
            "tst_hour": 14,
            "tst_minute": 15,
            "tst_second": 53,
        }
        assert [
            result["pillars"][name]["stem"]["char"]
            + result["pillars"][name]["branch"]["char"]
            for name in ("year", "month", "day", "hour")
        ] == ["庚午", "辛巳", "庚辰", "癸未"]
        assert result["five_elements"] == {
            "scores": {
                "Wood": 6.6,
                "Fire": 36.0,
                "Earth": 32.4,
                "Metal": 22.05,
                "Water": 6.9,
            },
            "percentages": {
                "Wood": 6.35,
                "Fire": 34.63,
                "Earth": 31.17,
                "Metal": 21.21,
                "Water": 6.64,
            },
            "dominant_element": "Fire",
            "weakest_element": "Wood",
            "total_raw": 103.95,
        }

    def test_li_chun_uses_corrected_solar_date(self, calculator):
        before = calculator.calculate(datetime(2026, 2, 4, 0, 0), 105.0, 7.0)
        after = calculator.calculate(datetime(2026, 2, 4, 12, 0), 105.0, 7.0)
        assert before["solar_time_info"]["tst_datetime"] == "2026-02-03 23:46:23"
        assert before["pillars"]["year"]["stem"]["char"] == "乙"
        assert before["pillars"]["month"]["branch"]["char"] == "丑"
        assert after["solar_time_info"]["tst_datetime"] == "2026-02-04 11:46:19"
        assert after["pillars"]["year"]["stem"]["char"] == "丙"
        assert after["pillars"]["month"]["branch"]["char"] == "寅"

    def test_true_solar_midnight_rollover_changes_day_and_hour(self, calculator):
        result = calculator.calculate(
            datetime(2026, 2, 3, 23, 58, 30),
            longitude=120.0,
            utc_offset_hours=7.0,
        )
        assert result["solar_time_info"]["longitude_offset_minutes"] == 60.0
        assert result["solar_time_info"]["eot_minutes"] == -13.614
        assert result["solar_time_info"]["tst_datetime"] == "2026-02-04 00:44:53"
        assert result["pillars"]["day"]["stem"]["char"] == "己"
        assert result["pillars"]["hour"]["stem"]["char"] == "甲"
        assert result["pillars"]["hour"]["branch"]["char"] == "子"

    def test_leap_day_and_timezone_extreme_golden(self, calculator):
        result = calculator.calculate(
            datetime(2000, 2, 29, 23, 30),
            longitude=180.0,
            utc_offset_hours=14.0,
        )
        assert result["solar_time_info"]["standard_meridian"] == 210.0
        assert result["solar_time_info"]["longitude_offset_minutes"] == -120.0
        assert result["solar_time_info"]["eot_minutes"] == -12.7579
        assert result["solar_time_info"]["tst_datetime"] == "2000-02-29 21:17:14"
        assert [
            result["pillars"][name]["stem"]["char"]
            + result["pillars"][name]["branch"]["char"]
            for name in ("year", "month", "day", "hour")
        ] == ["庚辰", "戊寅", "丁巳", "辛亥"]


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
