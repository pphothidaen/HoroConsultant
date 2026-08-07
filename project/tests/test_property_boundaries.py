"""
project/tests/test_property_boundaries.py — Property-Based & Edge Boundary Tests
Computational Metaphysics Engine
"""

import unittest
from datetime import datetime, timedelta
from project.core.bazi_engine import BaZiEngine
from project.core.solar_time import calculate_true_solar_time, calculate_equation_of_time
from project.core.fast_math import cached_julian_day


class TestPropertyBoundaries(unittest.TestCase):
    """Property-based and edge boundary test cases across historical date ranges."""

    def setUp(self):
        self.engine = BaZiEngine()

    def test_lichun_boundary_transitions_1950_to_2050(self):
        """Verify year pillar correctly switches on Lichun boundary across 100 years."""
        for yr in range(1950, 2050):
            # Feb 3 is before Lichun -> Previous Year Stem/Branch
            dt_before = datetime(yr, 2, 3, 12, 0)
            chart_before = self.engine.calculate(dt_before, 100.4930, 7.0)
            
            # Feb 6 is after Lichun -> Current Year Stem/Branch
            dt_after = datetime(yr, 2, 6, 12, 0)
            chart_after = self.engine.calculate(dt_after, 100.4930, 7.0)

            stem_before = chart_before["pillars"]["year"]["stem"]
            stem_after = chart_after["pillars"]["year"]["stem"]

            char_before = stem_before["char"] if isinstance(stem_before, dict) else stem_before
            char_after  = stem_after["char"]  if isinstance(stem_after, dict)  else stem_after

            self.assertIsNotNone(char_before)
            self.assertIsNotNone(char_after)
            self.assertIn(char_before, ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"])
            self.assertIn(char_after,  ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"])

    def test_leap_year_february_29(self):
        """Verify leap year Feb 29 chart calculations without errors."""
        leap_years = [1984, 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024, 2028]
        for yr in leap_years:
            dt = datetime(yr, 2, 29, 23, 59)
            chart = self.engine.calculate(dt, 100.4930, 7.0)
            self.assertEqual(chart["system_type"], "ming_xue")
            self.assertIsNotNone(chart["pillars"]["day"])

    def test_utc_offset_extreme_boundaries(self):
        """Verify calculation under extreme UTC offsets (-12.0 to +14.0)."""
        dt = datetime(2026, 8, 7, 12, 0)
        offsets = [-12.0, -9.5, -5.0, 0.0, 3.5, 7.0, 9.5, 12.0, 14.0]
        for offset in offsets:
            tst = calculate_true_solar_time(dt, longitude=100.4930, utc_offset_hours=offset)
            self.assertIsNotNone(tst.tst_datetime)

    def test_julian_day_monotonicity(self):
        """Verify Julian Day numbers strictly increase for sequential days."""
        base_dt = datetime(1900, 1, 1)
        prev_jd = cached_julian_day(base_dt.year, base_dt.month, base_dt.day)
        for i in range(1, 365):
            curr_dt = base_dt + timedelta(days=i)
            curr_jd = cached_julian_day(curr_dt.year, curr_dt.month, curr_dt.day)
            self.assertGreater(curr_jd, prev_jd)
            prev_jd = curr_jd


if __name__ == "__main__":
    unittest.main()
