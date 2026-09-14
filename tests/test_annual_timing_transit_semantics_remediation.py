"""RED baseline for honest annual-timing transit proxy semantics.

The annual timing engine currently derives planetary-house values from modulo
and request-seed arithmetic.  Those values may be useful as deterministic
product heuristics, but the consumer payload must not present them as a
verified astronomical transit-house calculation.
"""

from __future__ import annotations

from datetime import date, time

from project.core.unified_reading_engine import UnifiedReadingRequest
from project.core.annual_timing_engine import calculate_annual_timing


def _request(*, unknown_hour: bool = False) -> UnifiedReadingRequest:
    return UnifiedReadingRequest(
        target_year=2026,
        birth_date=date(1990, 6, 15),
        birth_time=time(14, 30),
        birth_place="Bangkok",
        latitude=13.7563,
        longitude=100.5018,
        timezone="Asia/Bangkok",
        gender_at_birth="male",
        unknown_hour=unknown_hour,
    )


def test_annual_timing_exposes_only_honest_transit_proxy_semantics() -> None:
    """Planetary houses must be labeled as uncertain proxies, not verified transits."""
    result = calculate_annual_timing(_request())

    for month in result["monthly_scores"]:
        basis = month["score_basis"]
        assert "thai_suriyayart_transit" not in basis, (
            f"Month {month['month']} exposes proxy arithmetic as a transit calculation"
        )

        proxy = basis.get("thai_suriyayart_proxy")
        assert isinstance(proxy, dict), f"Month {month['month']} is missing proxy semantics"
        precision = str(proxy.get("precision", "")).lower()
        assert "proxy" in precision, f"Month {month['month']} does not label the result as a proxy"
        assert "deterministic transit-house calculation" not in precision
        assert proxy.get("verified") is False, (
            f"Month {month['month']} must explicitly reject verified astronomical status"
        )
        uncertainty = proxy.get("uncertainty")
        uncertainty_text = str(uncertainty).lower()
        assert "proxy" in uncertainty_text and "not" in uncertainty_text and "verified" in uncertainty_text, (
            f"Month {month['month']} uncertainty must say the proxy is not verified"
        )


def test_annual_timing_reasons_disclose_non_astronomical_proxy_status() -> None:
    """Consumer-facing reasons must not imply that proxy houses are astronomical facts."""
    result = calculate_annual_timing(_request())

    for month in result["monthly_scores"]:
        reasons = " ".join(str(reason) for reason in month["reasons"]).lower()
        assert "proxy" in reasons, f"Month {month['month']} reason omits proxy disclosure"
        assert any(
            phrase in reasons
            for phrase in ("not a verified astronomical transit", "not verified astronomical", "not an astronomical transit")
        ), f"Month {month['month']} reason implies verified astronomy: {reasons}"


def test_annual_timing_semantics_preserve_month_scores_and_unknown_ranges() -> None:
    """Semantic relabeling must preserve existing month, target-year, score, and range identities."""
    result = calculate_annual_timing(_request())
    assert result["target_year"] == 2026
    expected_scores = [
        (7, 7, 7), (9, 8, 6), (5, 5, 6), (5, 6, 8), (4, 5, 2), (6, 6, 6),
        (8, 9, 8), (7, 9, 6), (4, 5, 6), (8, 7, 7), (5, 7, 5), (4, 4, 4),
    ]
    assert [month["month"] for month in result["monthly_scores"]] == list(range(1, 13))
    assert [
        (month["career_score"], month["finance_score"], month["love_score"])
        for month in result["monthly_scores"]
    ] == expected_scores

    unknown_result = calculate_annual_timing(_request(unknown_hour=True))
    assert unknown_result["target_year"] == 2026
    expected_ranges = [
        ([5, 9], [5, 9], [5, 9]), ([7, 9], [6, 8], [5, 7]), ([5, 9], [4, 8], [4, 8]),
        ([3, 5], [5, 7], [6, 8]), ([3, 7], [3, 7], [1, 5]), ([3, 5], [4, 6], [5, 7]),
        ([6, 10], [7, 10], [6, 10]), ([6, 8], [7, 9], [5, 7]), ([4, 8], [5, 9], [4, 8]),
        ([5, 7], [5, 7], [6, 8]), ([4, 8], [5, 9], [3, 7]), ([3, 5], [4, 6], [3, 5]),
    ]
    assert [month["month"] for month in unknown_result["monthly_scores"]] == list(range(1, 13))
    assert [
        (month["career_score_range"], month["finance_score_range"], month["love_score_range"])
        for month in unknown_result["monthly_scores"]
    ] == expected_ranges
