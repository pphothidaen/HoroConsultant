"""
test_bazi_url_validation.py — Regression & randomized validation tests
=======================================================================

1. Regression: exact case from bazi.fengshuix.com URL (1985-08-26 23:03 Ratchaburi)
2. Randomized stress tests across boundary hours, extreme longitudes, leap years
3. Cross-checks against known golden cases in test_bazi_calculator.py
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# ── ensure project root on path ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine  # noqa: E402

# ── deterministic RNG for reproducible randomized tests ─────────────────────────
_RNG = random.Random(0xBA21_2026)

# ── known golden: the exact URL case ────────────────────────────────────────────
URL_CASE_INPUT = {
    "dt": datetime(1985, 8, 26, 23, 3, 0),
    "longitude": 99.91,       # Ratchaburi approx
    "utc_offset_hours": 7.0,
    # Expected four pillars from bazi.fengshuix.com:
    "expected_stems": ["乙", "甲", "丁", "辛"],
    "expected_branches": ["丑", "申", "酉", "亥"],
    "expected_day_master_stem": "丁",
    "expected_day_master_element": "Fire",
}


# ── helper: assert pillars match expected ──────────────────────────────────────
def _check_pillars(result: dict, expected_stems: list[str], expected_branches: list[str]) -> None:
    """Raise AssertionError with detailed diff if pillars mismatch."""
    labels = ["year", "month", "day", "hour"]
    actual_stems = []
    actual_branches = []
    for label in labels:
        p = result["pillars"][label]
        s = p["stem"]["char"]
        b = p["branch"]["char"]
        actual_stems.append(s)
        actual_branches.append(b)
        # per-pillar detail so failures read clearly
        exp_s = expected_stems[labels.index(label)]
        exp_b = expected_branches[labels.index(label)]
        assert s == exp_s, f"{label} stem mismatch: got {s} ({p['stem']['pinyin']}), expected {exp_s}"
        assert b == exp_b, f"{label} branch mismatch: got {b} ({p['branch']['animal']}), expected {exp_b}"
    assert actual_stems == expected_stems, f"stem sequence mismatch: got {actual_stems}"
    assert actual_branches == expected_branches, f"branch sequence mismatch: got {actual_branches}"


# ==============================================================================
# 1. REGRESSION: exact case from bazi.fengshuix.com URL
# ==============================================================================
class TestBaziUrlRegression:
    """Verify the engine reproduces the four pillars shown on bazi.fengshuix.com."""

    @pytest.fixture(scope="class")
    def engine(self) -> BaZiEngine:
        return BaZiEngine()

    def test_url_case_pillars_match(self, engine: BaZiEngine) -> None:
        """Four pillars must match the reference website exactly."""
        inp = URL_CASE_INPUT
        result = engine.calculate(
            dt=inp["dt"],
            longitude=inp["longitude"],
            utc_offset_hours=inp["utc_offset_hours"],
        )
        _check_pillars(result, inp["expected_stems"], inp["expected_branches"])
        assert result["day_master"]["stem"] == inp["expected_day_master_stem"], (
            f"day master stem mismatch: got {result['day_master']['stem']}, "
            f"expected {inp['expected_day_master_stem']}"
        )
        assert result["day_master"]["element"] == inp["expected_day_master_element"], (
            f"day master element mismatch: got {result['day_master']['element']}, "
            f"expected {inp['expected_day_master_element']}"
        )

    def test_url_case_true_solar_time_reasonable(self, engine: BaZiEngine) -> None:
        """TST correction is within plausible range for Ratchaburi."""
        result = engine.calculate(
            dt=URL_CASE_INPUT["dt"],
            longitude=URL_CASE_INPUT["longitude"],
            utc_offset_hours=URL_CASE_INPUT["utc_offset_hours"],
        )
        tst = result["solar_time_info"]
        # Correction should be negative (east of standard meridian 105°, local ~99.91°)
        assert tst["longitude_offset_minutes"] < 0, "Ratchaburi is east of 105°E meridian"
        # EoT on Aug 26 should be roughly -2 to -6 minutes
        assert -10.0 < tst["eot_minutes"] < 0.0, f"EoT {tst['eot_minutes']:.2f} out of plausible Aug range"
        # TST should be earlier than input (correction subtracts)
        assert tst["tst_hour"] <= 23, "TST hour should be ≤ input hour after correction"
        # tst_datetime should be on the same calendar date or one day earlier (rollover)
        assert tst["tst_datetime"].startswith("1985-08-26") or tst["tst_datetime"].startswith("1985-08-25")

    def test_url_case_five_elements_has_all_five(self, engine: BaZiEngine) -> None:
        """Five Elements percentages must cover Wood/Fire/Earth/Metal/Water."""
        result = engine.calculate(
            dt=URL_CASE_INPUT["dt"],
            longitude=URL_CASE_INPUT["longitude"],
            utc_offset_hours=URL_CASE_INPUT["utc_offset_hours"],
        )
        pct = result["five_elements"]["percentages"]
        assert set(pct.keys()) == {"Wood", "Fire", "Earth", "Metal", "Water"}
        total = sum(pct.values())
        assert abs(total - 100.0) < 0.5, f"percentages sum to {total}, not 100"


# ==============================================================================
# 2. RANDOMIZED STRESS TESTS — boundary hours, extreme longitudes, leap years
# ==============================================================================
class TestBaziRandomizedStress:
    """Randomized inputs exercising edge cases the engine must handle."""

    @pytest.fixture(scope="class")
    def engine(self) -> BaZiEngine:
        return BaZiEngine()

    # ── 2a. Hour-boundary stress: every double-hour transition across a year ──
    def test_hour_boundary_transitions_consistent(self, engine: BaZiEngine) -> None:
        """
        For a fixed date+location, step through all 24 clock hours and verify:
        - Hour pillar changes exactly at double-hour boundaries (e.g. 23→01 子)
        - No two consecutive hours produce the same hour pillar unless
          TST rollover keeps them in the same double-hour.
        """
        base_dt = datetime(2024, 6, 15, 0, 0, 0)
        longitude = 100.5
        utc = 7.0
        prev_hour_pillar = None
        transition_count = 0
        for clock_hour in range(24):
            dt = datetime(2024, 6, 15, clock_hour, 0, 0)
            result = engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=utc)
            hp = result["pillars"]["hour"]
            pillar_key = hp["stem"]["char"] + hp["branch"]["char"]
            if prev_hour_pillar is not None and pillar_key != prev_hour_pillar:
                transition_count += 1
            prev_hour_pillar = pillar_key
        # Across 24 clock hours there should be exactly 12 hour-branch transitions
        # (one per double-hour). Allow a tolerance for TST date rollover effects.
        assert 10 <= transition_count <= 14, (
            f"expected ~12 hour-branch transitions across 24 clock hours, got {transition_count}"
        )

    # ── 2b. Extreme longitudes ─────────────────────────────────────────────────
    @pytest.mark.parametrize("longitude", [
        -180.0,   # farthest west
        -90.0,
        0.0,      # prime meridian
        90.0,
        150.0,
        180.0,    # farthest east
    ])
    def test_extreme_longitudes_produce_valid_charts(self, engine: BaZiEngine, longitude: float) -> None:
        """No crash / no error for longitudes spanning the full -180..180 range."""
        dt = datetime(2000, 1, 1, 12, 0, 0)
        result = engine.calculate(dt=dt, longitude=longitude, utc_offset_hours=UTC_FOR_LONGITUDE(longitude))
        # Only assert structural validity; pillar values depend on longitude, not hardcoded.
        assert result is not None
        assert "pillars" in result
        for label in ("year", "month", "day", "hour"):
            assert label in result["pillars"]
            p = result["pillars"][label]
            assert len(p["stem"]["char"]) == 1
            assert len(p["branch"]["char"]) == 1
            assert p["stem"]["element"] in {"Wood", "Fire", "Earth", "Metal", "Water"}
            assert p["branch"]["animal"] in {
                "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
            }
        assert result["five_elements"] is not None
        assert result["day_master"]["stem"] in {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}

    # ── 2c. Random decades of dates ────────────────────────────────────────────
    def test_random_dates_across_20th_century_all_valid(self, engine: BaZiEngine) -> None:
        """Random dates 1901–1999 must all produce valid four pillars."""
        # March forward from a seed date to avoid invalid calendar construction
        base = datetime(1901, 1, 1)
        for _ in range(200):
            offset_days = _RNG.randint(0, 36_500)  # covers ~100 years
            dt = base + timedelta(days=offset_days)
            # also advance clock time by a random offset within that day
            dt = dt.replace(
                hour=_RNG.randint(0, 23),
                minute=_RNG.randint(0, 59),
                second=0,
            )
            lon = round(_RNG.uniform(-170.0, 170.0), 3)
            utc = round(_RNG.choice([-12.0, -5.0, 0.0, 5.5, 7.0, 8.0, 9.5, 12.0]), 1)
            result = engine.calculate(dt=dt, longitude=lon, utc_offset_hours=utc)
            assert result is not None
            assert "pillars" in result
            for label in ("year", "month", "day", "hour"):
                assert label in result["pillars"]
                assert "stem" in result["pillars"][label]
                assert "branch" in result["pillars"][label]
                assert len(result["pillars"][label]["stem"]["char"]) == 1
                assert len(result["pillars"][label]["branch"]["char"]) == 1

    # ── 2d. Midnight rollover edge cases ──────────────────────────────────────
    @pytest.mark.parametrize("dt_str", [
        "2026-02-03 23:58:30",   # TST rolls to next day (known golden case)
        "2000-02-29 23:30:00",   # leap day near midnight
        "1999-12-31 23:59:59",   # year boundary midnight
        "2023-03-01 00:00:00",   # just after midnight (TST may roll back)
    ])
    def test_midnight_rollover_produces_consistent_day_and_hour(
        self, engine: BaZiEngine, dt_str: str
    ) -> None:
        """TST-induced date rollover must not crash and must yield valid day/hour."""
        dt = datetime.fromisoformat(dt_str)
        lon = 105.0
        utc = 7.0
        result = engine.calculate(dt=dt, longitude=lon, utc_offset_hours=utc)
        assert result["pillars"]["day"]["stem"]["char"] in {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
        assert result["pillars"]["hour"]["branch"]["char"] in {
            "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"
        }


# ==============================================================================
# 3. CROSS-CHECK AGAINST EXISTING GOLDEN CASES
# ==============================================================================
class TestBaziCrossCheckWithGoldens:
    """Ensure new randomized tests are consistent with the literal oracle goldens."""

    @pytest.fixture(scope="class")
    def engine(self) -> BaZiEngine:
        return BaZiEngine()

    def test_bangkok_1990_cross_check(self, engine: BaZiEngine) -> None:
        """Must match the golden Bangkok 1990-05-15 14:30 case from test_bazi_calculator.py."""
        result = engine.calculate(
            dt=datetime(1990, 5, 15, 14, 30, 0),
            longitude=100.493,
            utc_offset_hours=7.0,
        )
        assert result["pillars"]["year"]["stem"]["char"] + result["pillars"]["year"]["branch"]["char"] == "庚午"
        assert result["pillars"]["month"]["stem"]["char"] + result["pillars"]["month"]["branch"]["char"] == "辛巳"
        assert result["pillars"]["day"]["stem"]["char"] + result["pillars"]["day"]["branch"]["char"] == "庚辰"
        assert result["pillars"]["hour"]["stem"]["char"] + result["pillars"]["hour"]["branch"]["char"] == "癸未"

    def test_singapore_cross_check(self, engine: BaZiEngine) -> None:
        """Must produce four valid pillars for Singapore (103.82°E, UTC+8).

        No golden oracle exists for this combination in-tree, so we assert
        structural validity (one-char stems/branches, all five elements present)
        rather than hard-coding pillar values that depend on TST corrections.
        """
        result = engine.calculate(
            dt=datetime(2000, 1, 1, 8, 0, 0),
            longitude=103.82,
            utc_offset_hours=8.0,
        )
        assert result is not None
        assert "pillars" in result
        # Every pillar must have a single-char stem + single-char branch
        for label in ("year", "month", "day", "hour"):
            p = result["pillars"][label]
            assert len(p["stem"]["char"]) == 1, f"{label} stem not single char"
            assert len(p["branch"]["char"]) == 1, f"{label} branch not single char"
            assert p["stem"]["element"] in {"Wood", "Fire", "Earth", "Metal", "Water"}
            assert p["branch"]["animal"] in {
                "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
            }
        # Five Elements must sum to ~100%
        pct = result["five_elements"]["percentages"]
        assert set(pct.keys()) == {"Wood", "Fire", "Earth", "Metal", "Water"}
        assert abs(sum(pct.values()) - 100.0) < 0.5

    def test_unknown_hour_probabilistic_matrix_has_12_scenarios(self, engine: BaZiEngine) -> None:
        """Unknown-hour mode must enumerate all 12 double-hour branches."""
        result = engine.calculate(
            dt=datetime(1990, 11, 7, 0, 5, 0),
            longitude=100.493,
            utc_offset_hours=7.0,
            unknown_hour=True,
        )
        assert result["is_probabilistic"] is True
        assert len(result["probabilistic_matrix"]) == 12
        scenario_branches = {s["hour_branch"] for s in result["probabilistic_matrix"]}
        assert scenario_branches == {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}


# ── small helper for test_extreme_longitudes ───────────────────────────────────
def UTC_FOR_LONGITUDE(lon: float) -> float:
    """Rough UTC offset for extreme-longitude test parametrize: floor(lon/15)."""
    return round(lon / 15.0)  # type: ignore[return-value]
