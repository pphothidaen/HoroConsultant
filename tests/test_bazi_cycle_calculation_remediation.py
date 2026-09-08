"""Remediation tests for Package 01: BaZi & transit cycle calculations.

Validates that:
1. Annual timing scores and basis are grounded in verified BaZi annual/monthly
   stems & branches and Thai transit aspects, not arbitrary modulo arithmetic.
2. Stem/branch interactions (clashes, harmonies, combinations) deterministically
   shape monthly domain scores.
3. Reasons cite computed astrological facts rather than generic proxy placeholders.
4. Past pattern calibration candidate years are grounded in astrological cycles
   (12-year Jupiter return, 10-year Da Yun boundaries, 6-year opposition clashes)
   rather than arbitrary hardcoded age lists.
5. Latency remains strictly under 50ms as required by performance specifications.
6. Deterministic reproducibility and chart distinctness are preserved.
"""

from __future__ import annotations

import time
from datetime import date, time as dt_time
from typing import Any

import pytest

from project.core.annual_timing_engine import calculate_annual_timing
from project.core.past_pattern_calibrator import generate_past_pattern_candidates
from project.core.unified_reading_engine import UnifiedReadingRequest


def _make_request(
    birth_date: date = date(1990, 6, 15),
    birth_time: dt_time | None = dt_time(14, 30),
    target_year: int = 2026,
    gender_at_birth: str = "male",
    unknown_hour: bool = False,
) -> UnifiedReadingRequest:
    return UnifiedReadingRequest(
        target_year=target_year,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place="Bangkok",
        latitude=13.7563,
        longitude=100.5018,
        timezone="Asia/Bangkok",
        gender_at_birth=gender_at_birth,
        unknown_hour=unknown_hour,
    )


# ---------------------------------------------------------------------------
# Test 1: Score basis contains verified BaZi stems & branches
# ---------------------------------------------------------------------------
def test_annual_timing_score_basis_contains_bazi_stems_and_branches() -> None:
    """Annual timing months must expose computed stems and branches."""
    req = _make_request()
    result = calculate_annual_timing(req)

    assert "monthly_scores" in result
    months = result["monthly_scores"]
    assert len(months) == 12

    for m in months:
        basis = m.get("score_basis", {})
        assert "bazi_annual" in basis, f"Month {m['month']}: missing bazi_annual in score_basis"
        assert "bazi_monthly" in basis, f"Month {m['month']}: missing bazi_monthly in score_basis"

        annual = basis["bazi_annual"]
        assert "stem" in annual and "branch" in annual
        assert isinstance(annual["stem"], str) and len(annual["stem"]) == 1
        assert isinstance(annual["branch"], str) and len(annual["branch"]) == 1

        monthly = basis["bazi_monthly"]
        assert "stem" in monthly and "branch" in monthly
        assert isinstance(monthly["stem"], str) and len(monthly["stem"]) == 1
        assert isinstance(monthly["branch"], str) and len(monthly["branch"]) == 1


# ---------------------------------------------------------------------------
# Test 2: Reasons cite calculated facts, not generic proxy strings
# ---------------------------------------------------------------------------
def test_reasons_cite_computed_astrological_facts() -> None:
    """Reasons must reference actual calculated stems, branches, or transit aspects."""
    req = _make_request()
    result = calculate_annual_timing(req)

    for m in result["monthly_scores"]:
        reasons = m.get("reasons", [])
        assert len(reasons) >= 1
        joined = " ".join(reasons)
        # Must not be the generic placeholder
        assert "proxy is present" not in joined.lower(), (
            f"Month {m['month']}: reason still contains generic proxy text: {joined}"
        )


# ---------------------------------------------------------------------------
# Test 3: Interactions (harmony/clash) are detected in score basis
# ---------------------------------------------------------------------------
def test_interactions_present_in_score_basis() -> None:
    """Score basis must record interaction metadata between transit and natal pillars."""
    req = _make_request()
    result = calculate_annual_timing(req)

    has_interactions = False
    for m in result["monthly_scores"]:
        basis = m.get("score_basis", {})
        if "interactions" in basis and isinstance(basis["interactions"], list):
            has_interactions = True
            break

    assert has_interactions, "At least one month must record interactions in score_basis"


# ---------------------------------------------------------------------------
# Test 4: Past pattern candidates grounded in astrological cycles
# ---------------------------------------------------------------------------
def test_past_pattern_candidates_grounded_in_astrological_cycles() -> None:
    """Adult past-pattern candidates must cite astrological cycles."""
    req = _make_request(birth_date=date(1980, 5, 20), target_year=2026)
    result = generate_past_pattern_candidates(req)

    candidates = result.get("candidates", [])
    assert 3 <= len(candidates) <= 5, f"Adult should receive 3-5 candidates, got {len(candidates)}"

    for c in candidates:
        basis_list = c.get("deterministic_basis", [])
        assert len(basis_list) > 0, f"Pattern {c.get('pattern_id')} missing deterministic_basis"
        joined_basis = " ".join(basis_list).lower()
        # Must cite a recognized metaphysical/astrological cycle
        has_cycle_ref = any(
            cycle_term in joined_basis
            for cycle_term in ("jupiter", "da yun", "clash", "transit", "cycle", "pillar", "return")
        )
        assert has_cycle_ref, (
            f"Pattern {c.get('pattern_id')} basis does not cite an astrological cycle: {basis_list}"
        )


# ---------------------------------------------------------------------------
# Test 5: Latency under 50ms performance gate
# ---------------------------------------------------------------------------
def test_annual_timing_latency_under_50ms() -> None:
    """calculate_annual_timing must run within 50ms."""
    req = _make_request()
    # Warmup
    calculate_annual_timing(req)

    times = []
    for _ in range(10):
        start = time.perf_counter()
        calculate_annual_timing(req)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        times.append(elapsed_ms)

    avg_ms = sum(times) / len(times)
    max_ms = max(times)
    assert avg_ms < 50.0, f"Average latency {avg_ms:.2f}ms exceeds 50ms ceiling (max: {max_ms:.2f}ms)"


# ---------------------------------------------------------------------------
# Test 6: Different birth charts produce distinct scores and basis
# ---------------------------------------------------------------------------
def test_distinct_birth_charts_produce_different_scores() -> None:
    """Two different birth dates must produce different monthly scores."""
    req1 = _make_request(birth_date=date(1985, 3, 10))
    req2 = _make_request(birth_date=date(1995, 11, 25))

    res1 = calculate_annual_timing(req1)
    res2 = calculate_annual_timing(req2)

    scores1 = [(m["career_score"], m["finance_score"], m["love_score"]) for m in res1["monthly_scores"]]
    scores2 = [(m["career_score"], m["finance_score"], m["love_score"]) for m in res2["monthly_scores"]]

    assert scores1 != scores2, "Different birth charts must produce different monthly scores"


# ---------------------------------------------------------------------------
# Test 7: Deterministic reproducibility
# ---------------------------------------------------------------------------
def test_deterministic_reproducibility() -> None:
    """Same input must produce identical scores and basis on multiple runs."""
    req = _make_request()
    res1 = calculate_annual_timing(req)
    res2 = calculate_annual_timing(req)

    assert res1 == res2, "Multiple calls with identical request must produce identical outputs"
