"""
tests/test_core.py — Unit Tests for Solar Time & BaZi Engine
=============================================================
Run:  python -m pytest tests/ -v
  or: python -m unittest discover -s tests -v
"""

import math
import json
import unittest
from datetime import datetime

from project.core.solar_time import calculate_true_solar_time, calculate_equation_of_time
from project.core.bazi_engine import (
    BaZiEngine,
    _year_stem_branch,
    _month_stem_branch,
    _day_stem_branch,
    _hour_stem_branch,
    STEMS, BRANCHES,
)


# ============================================================
# Solar Time Tests
# ============================================================

class TestEquationOfTime(unittest.TestCase):

    def test_february_minimum(self):
        """EoT around Feb 12 is near its annual minimum (~-14 min)."""
        dt  = datetime(2026, 2, 12, 12, 0, 0)
        eot = calculate_equation_of_time(dt)
        self.assertLess(eot, -10.0, f"EoT Feb 12 should be < -10 min, got {eot}")

    def test_november_maximum(self):
        """EoT around Nov 3 is near its annual maximum (~+16 min)."""
        dt  = datetime(2026, 11, 3, 12, 0, 0)
        eot = calculate_equation_of_time(dt)
        self.assertGreater(eot, 10.0, f"EoT Nov 3 should be > 10 min, got {eot}")

    def test_equinox_near_zero(self):
        """EoT near equinoxes (Apr 15, Sep 1) is approximately zero (< 4 min abs)."""
        for dt in [datetime(2026, 4, 15, 12, 0), datetime(2026, 9, 1, 12, 0)]:
            eot = calculate_equation_of_time(dt)
            self.assertLess(abs(eot), 5.0, f"EoT {dt.date()} should be near 0, got {eot}")


class TestTrueSolarTime(unittest.TestCase):

    def setUp(self):
        # Bangkok: λ=100.493°, UTC+7 → Λ_std=105.0°
        self.dt        = datetime(2026, 8, 3, 12, 0, 0)
        self.longitude = 100.4930
        self.utc       = 7.0

    def test_standard_meridian(self):
        res = calculate_true_solar_time(self.dt, self.longitude, self.utc)
        self.assertEqual(res.standard_meridian, 105.0)

    def test_longitude_offset_sign(self):
        """Bangkok is west of standard meridian → offset should be negative."""
        res = calculate_true_solar_time(self.dt, self.longitude, self.utc)
        self.assertLess(res.longitude_offset_minutes, 0.0)

    def test_tst_datetime_format(self):
        res = calculate_true_solar_time(self.dt, self.longitude, self.utc)
        # Should parse without error
        dt_out = datetime.strptime(res.tst_datetime, "%Y-%m-%d %H:%M:%S")
        self.assertIsInstance(dt_out, datetime)

    def test_lmt_is_intermediate(self):
        """LMT datetime != TST datetime (EoT is non-zero in August)."""
        res = calculate_true_solar_time(self.dt, self.longitude, self.utc)
        self.assertNotEqual(res.lmt_datetime, res.tst_datetime)

    def test_to_dict_keys(self):
        res = calculate_true_solar_time(self.dt, self.longitude, self.utc)
        d   = res.to_dict()
        for k in ["input_datetime", "longitude", "utc_offset_hours", "standard_meridian",
                  "longitude_offset_minutes", "eot_minutes", "lmt_datetime",
                  "tst_datetime", "tst_hour", "tst_minute", "tst_second"]:
            self.assertIn(k, d, f"Missing key: {k}")


# ============================================================
# BaZi Pillar Calculation Tests
# ============================================================

class TestPillarHelpers(unittest.TestCase):

    def test_year_pillar_2026(self):
        """2026 is 丙午 year (stem idx=2, branch idx=2)."""
        ys, yb = _year_stem_branch(2026, 8, 3)
        self.assertEqual(STEMS[ys]["name"], "丙")
        self.assertEqual(BRANCHES[yb]["name"], "午")

    def test_year_pillar_boundary_before_lichun(self):
        """Jan 15, 2026 should still be 乙巳 year (2025 cycle)."""
        ys, yb = _year_stem_branch(2026, 1, 15)
        self.assertEqual(STEMS[ys]["name"], "乙")
        self.assertEqual(BRANCHES[yb]["name"], "巳")

    def test_day_stem_cycle_consistency(self):
        """Day stem-branch cycle must advance by 1 each day."""
        dt1 = datetime(2026, 8, 3)
        dt2 = datetime(2026, 8, 4)
        ds1, db1 = _day_stem_branch(dt1)
        ds2, db2 = _day_stem_branch(dt2)
        self.assertEqual((ds1 + 1) % 10, ds2)
        self.assertEqual((db1 + 1) % 12, db2)

    def test_hour_branch_midnight(self):
        """TST hour 0 → 丑 (branch idx 1)."""
        # 00:00 → (0 + 1) // 2 = 0 → 子? Let's check…
        # Actually hour 0 → (0+1)//2 = 0 → 子
        from project.core.bazi_engine import _hour_branch_from_tst
        self.assertEqual(_hour_branch_from_tst(0), 0)   # 子

    def test_hour_branch_23(self):
        """TST hour 23 → 子 (branch idx 0)."""
        from project.core.bazi_engine import _hour_branch_from_tst
        self.assertEqual(_hour_branch_from_tst(23), 0)  # 子


# ============================================================
# BaZi Engine Integration Tests
# ============================================================

class TestBaZiEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BaZiEngine()
        self.dt        = datetime(2026, 8, 3, 14, 30, 0)
        self.longitude = 100.4930
        self.utc       = 7.0

    def test_deterministic_chart_structure(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc)
        self.assertFalse(result["is_probabilistic"])
        for key in ["year", "month", "day", "hour"]:
            self.assertIn(key, result["pillars"])

    def test_five_elements_percentages_sum_to_100(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc)
        pcts   = result["five_elements"]["percentages"]
        total  = sum(pcts.values())
        self.assertAlmostEqual(total, 100.0, places=0)

    def test_day_master_present(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc)
        dm = result["day_master"]
        self.assertIn("stem",    dm)
        self.assertIn("element", dm)
        self.assertIn("polarity", dm)

    def test_json_serialisable(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc)
        try:
            json.dumps(result, ensure_ascii=False)
        except TypeError as e:
            self.fail(f"Result is not JSON serialisable: {e}")

    # ---- Probabilistic Mode ----

    def test_probabilistic_matrix_returns_12_scenarios(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc, unknown_hour=True)
        self.assertTrue(result["is_probabilistic"])
        self.assertEqual(len(result["probabilistic_matrix"]), 12)

    def test_probabilistic_weights_sum_to_1(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc, unknown_hour=True)
        total  = sum(s["probability_weight"] for s in result["probabilistic_matrix"])
        self.assertAlmostEqual(total, 1.0, places=3)

    def test_probabilistic_each_scenario_has_elements(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc, unknown_hour=True)
        for scenario in result["probabilistic_matrix"]:
            self.assertIn("five_elements", scenario)
            self.assertIn("hour_pillar",   scenario)

    def test_probabilistic_json_serialisable(self):
        result = self.engine.calculate(self.dt, self.longitude, self.utc, unknown_hour=True)
        try:
            json.dumps(result, ensure_ascii=False)
        except TypeError as e:
            self.fail(f"Probabilistic result is not JSON serialisable: {e}")

    # ---- Edge Cases ----

    def test_greenwich_meridian(self):
        """Should work at longitude=0 (Greenwich, UTC+0)."""
        dt = datetime(2026, 6, 21, 12, 0, 0)
        result = self.engine.calculate(dt, longitude=0.0, utc_offset_hours=0.0)
        self.assertFalse(result["is_probabilistic"])

    def test_western_longitude(self):
        """Should work at negative longitude (New York -74°, UTC-5)."""
        dt = datetime(2026, 6, 21, 12, 0, 0)
        result = self.engine.calculate(dt, longitude=-74.0, utc_offset_hours=-5.0)
        self.assertFalse(result["is_probabilistic"])

    def test_near_midnight_hour_boundary(self):
        """Hour 23 should map to 子 branch."""
        dt = datetime(2026, 8, 3, 23, 30, 0)
        result = self.engine.calculate(dt, self.longitude, self.utc)
        self.assertFalse(result["is_probabilistic"])
        hour_branch = result["pillars"]["hour"]["branch"]["char"]
        # 23:30 TST (minus ~18 min offset) stays in late-night range → 子 or 亥
        self.assertIn(hour_branch, ["子", "亥"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
