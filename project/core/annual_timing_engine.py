"""Deterministic annual timing proxies for Horo Lite unified readings."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from project.core.bazi_engine import (
    BRANCHES,
    STEMS,
    _day_stem_branch,
    _month_stem_branch,
    _year_stem_branch,
)
from project.core.transit_engine import (
    BRANCH_CLASHES,
    BRANCH_COMBINATIONS,
    STEM_COMBINATIONS,
)
from project.debate.consensus_matrix import (
    DEFAULT_TRADITIONS_CONSIDERED,
    arbitrate_monthly_consensus,
)


_DOMAINS: tuple[str, ...] = ("career", "finance", "love")
_CYCLE_LABELS: tuple[str, ...] = (
    "Wood",
    "Fire",
    "Earth",
    "Metal",
    "Water",
)
_TRADITIONS_CONSIDERED: tuple[str, ...] = DEFAULT_TRADITIONS_CONSIDERED


def _clamp_score(value: int) -> int:
    return max(1, min(10, value))


def _birth_time_minutes(request: Any) -> int:
    birth_time = getattr(request, "birth_time", None)
    if birth_time is None:
        return 12 * 60
    return birth_time.hour * 60 + birth_time.minute


def _birth_date(request: Any) -> date:
    value = getattr(request, "birth_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _request_seed(request: Any) -> int:
    birth = _birth_date(request)
    longitude_bucket = int(round((float(getattr(request, "longitude", 0.0)) + 180.0) * 10))
    latitude_bucket = int(round((float(getattr(request, "latitude", 0.0)) + 90.0) * 10))
    unknown_hour = bool(getattr(request, "unknown_hour", False))
    # When birth hour is unknown, ignore any supplied birth_time to ensure
    # scores are time-invariant.  Use the noon default (720 minutes // 30 = 24).
    if unknown_hour:
        time_bucket = 12 * 60 // 30  # noon
    else:
        time_bucket = _birth_time_minutes(request) // 30
    gender_seed = sum(ord(ch) for ch in str(getattr(request, "gender_at_birth", "") or ""))
    return (
        birth.year * 37
        + birth.month * 41
        + birth.day * 43
        + int(getattr(request, "target_year")) * 47
        + longitude_bucket
        + latitude_bucket
        + time_bucket * 11
        + gender_seed
    )


def _cycle_index(year: int, month: int, offset: int) -> int:
    return ((year - 1984) * 12 + month - 1 + offset) % 60


def _score_range(score: int, month: int) -> list[int]:
    spread = 1 + (month % 2)
    return [_clamp_score(score - spread), _clamp_score(score + spread)]


def _stable_text_checksum(value: Any) -> int:
    return sum(ord(ch) for ch in str(value or ""))


def _build_consensus_metadata(
    request: Any,
    months: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    fixture_claims = getattr(request, "tradition_monthly_claims", None)
    if not isinstance(fixture_claims, list):
        fixture_claims = None

    return arbitrate_monthly_consensus(
        months,
        tradition_monthly_claims=fixture_claims,
        consensus_fixture_id=getattr(request, "consensus_fixture_id", None),
        seed=seed,
        traditions_considered=_TRADITIONS_CONSIDERED,
    )


def _build_hitl_payload(
    request: Any,
    metadata: dict[str, Any],
    unknown_hour: bool,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    consensus_score = float(metadata["consensus_score"])
    tradition_conflict = bool(metadata["tradition_conflicts"])
    force_human_review = bool(getattr(request, "force_human_review", False))
    uncertain_birth_time = unknown_hour
    low_consensus = consensus_score < 0.75
    required_human_review = (
        low_consensus
        or tradition_conflict
        or force_human_review
        or uncertain_birth_time
    )

    flags = {
        "required_human_review": required_human_review,
        "low_consensus": low_consensus,
        "tradition_conflict": tradition_conflict,
        "conflict_detected": tradition_conflict,
        "force_human_review": force_human_review,
        "uncertain_birth_time": uncertain_birth_time,
    }
    routing = {
        "status": "QUEUED_FOR_HUMAN_REVIEW" if required_human_review else "NOT_REQUIRED",
        "reason": (
            "hitl_triggered"
            if required_human_review
            else "automated_synthesis_sufficient"
        ),
        "trigger_reasons": [
            k for k, v in flags.items() if v and k != "required_human_review"
        ],
        "required_human_review": required_human_review,
        "conflict_detected": tradition_conflict,
        "conflicting_domains": metadata.get("conflicting_domains", []),
        "consensus_score": consensus_score,
        "routing_key": (
            f"horo_v3_consensus_{getattr(request, 'target_year')}_"
            f"{seed}_{_stable_text_checksum(getattr(request, 'consensus_fixture_id', ''))}"
        ),
    }
    return flags, routing


def calculate_annual_timing(request: Any) -> dict[str, Any]:
    """Return deterministic 12-month annual timing scores grounded in BaZi and Thai proxies.

    Combines target-year/month sexagenary cycle positions (Liu Nian/Liu Yue),
    natal Day Master interactions (combinations, clashes, harmonies), and Thai
    Suriyayart-style house proxies. The house values are deterministic proxies,
    not verified astronomical transit calculations.
    """

    target_year = int(getattr(request, "target_year"))
    unknown_hour = bool(getattr(request, "unknown_hour", False)) or getattr(request, "birth_time", None) is None
    seed = _request_seed(request)
    birth = _birth_date(request)

    # 1. Natal chart pillars
    dt_birth = datetime(birth.year, birth.month, birth.day, 12, 0)
    n_ys, n_yb = _year_stem_branch(birth.year, birth.month, birth.day)
    n_ds, n_db = _day_stem_branch(dt_birth)
    natal_dm = STEMS[n_ds]["name"]
    natal_dm_elem = STEMS[n_ds]["element"]
    natal_yb_char = BRANCHES[n_yb]["name"]
    natal_db_char = BRANCHES[n_db]["name"]

    # 2. Transit annual pillar
    t_ys, t_yb = _year_stem_branch(target_year, 6, 15)
    annual_stem = STEMS[t_ys]["name"]
    annual_branch = BRANCHES[t_yb]["name"]
    annual_element = STEMS[t_ys]["element"]
    annual_cycle = (target_year - 1984) % 60

    months: list[dict[str, Any]] = []
    for month in range(1, 13):
        # Transit monthly pillar
        t_ms, t_mb = _month_stem_branch(t_ys, month, 15)
        month_stem = STEMS[t_ms]["name"]
        month_branch = BRANCHES[t_mb]["name"]
        month_element = STEMS[t_ms]["element"]
        monthly_cycle = _cycle_index(target_year, month, seed % 12)

        # Interaction detection
        interactions: list[str] = []
        clash_y = frozenset([month_branch, natal_yb_char]) in BRANCH_CLASHES
        clash_d = frozenset([month_branch, natal_db_char]) in BRANCH_CLASHES
        if clash_y:
            interactions.append(f"Branch clash: month {month_branch} clashes with natal year branch {natal_yb_char}")
        if clash_d and not clash_y:
            interactions.append(f"Branch clash: month {month_branch} clashes with natal day branch {natal_db_char}")

        combo_y = frozenset([month_branch, natal_yb_char]) in BRANCH_COMBINATIONS
        combo_d = frozenset([month_branch, natal_db_char]) in BRANCH_COMBINATIONS
        if combo_y:
            interactions.append(f"Branch harmony: month {month_branch} combines with natal year branch {natal_yb_char}")
        if combo_d and not combo_y:
            interactions.append(f"Branch harmony: month {month_branch} combines with natal day branch {natal_db_char}")

        stem_combo = frozenset([month_stem, natal_dm]) in STEM_COMBINATIONS
        if stem_combo:
            interactions.append(f"Stem combination: month {month_stem} combines with Day Master {natal_dm}")

        # Thai transit house positions
        jupiter_house = (target_year - birth.year + month + (seed % 3)) % 12 + 1
        saturn_house = ((target_year - birth.year) * 2 + month) % 12 + 1
        rahu_house = (12 - ((target_year - birth.year + month) % 12)) or 12

        # Grounded domain scores (base 6 neutral positive)
        career_val = 6
        finance_val = 6
        love_val = 6

        if combo_y or combo_d:
            career_val += 1
            finance_val += 1
            love_val += 1
        if clash_y or clash_d:
            career_val -= 1
            finance_val -= 1
            love_val -= 2
        if stem_combo:
            finance_val += 1
            love_val += 1

        if jupiter_house in (1, 5, 9, 10, 11):
            career_val += 1
            finance_val += 1
        elif jupiter_house in (6, 8, 12):
            career_val -= 1

        if jupiter_house in (2, 11):
            finance_val += 1
        if jupiter_house == 7:
            love_val += 1

        if saturn_house in (6, 8, 12):
            career_val -= 1
        if rahu_house in (2, 8):
            finance_val -= 1
        if rahu_house == 7:
            love_val -= 1

        # Month offset variance for dynamic texture
        c_score = _clamp_score(career_val + ((month + t_ms) % 3) - 1)
        f_score = _clamp_score(finance_val + ((month + t_mb) % 3) - 1)
        l_score = _clamp_score(love_val + ((month + n_ds) % 3) - 1)

        reasons = [
            f"BaZi month pillar {month_stem}{month_branch} ({month_element}) interacts with natal Day Master {natal_dm} ({natal_dm_elem}).",
            (
                "Thai Suriyayart house values are deterministic proxy signals, "
                "not a verified astronomical transit."
            ),
        ]
        if interactions:
            reasons.append(interactions[0])
        else:
            reasons.append(f"Proxy Jupiter house {jupiter_house} provides steady structural support.")

        item: dict[str, Any] = {
            "month": month,
            "confidence": "ESTIMATED" if unknown_hour else "HIGH",
            "score_basis": {
                "bazi_annual": {
                    "stem": annual_stem,
                    "branch": annual_branch,
                    "element": annual_element,
                },
                "bazi_monthly": {
                    "stem": month_stem,
                    "branch": month_branch,
                    "element": month_element,
                },
                "bazi_liu_yue_proxy": {
                    "annual_cycle_index": annual_cycle,
                    "monthly_cycle_index": monthly_cycle,
                    "cycle_element": month_element,
                },
                "thai_suriyayart_proxy": {
                    "jupiter_house": jupiter_house,
                    "saturn_house": saturn_house,
                    "rahu_house": rahu_house,
                    "precision": "deterministic proxy house estimate",
                    "verified": False,
                    "uncertainty": "Proxy estimate only; not a verified astronomical transit.",
                },
                "interactions": interactions,
            },
            "reasons": reasons,
        }

        domain_scores = {"career": c_score, "finance": f_score, "love": l_score}
        for domain, score in domain_scores.items():
            if unknown_hour:
                item[f"{domain}_score_range"] = _score_range(score, month)
            else:
                item[f"{domain}_score"] = score

        months.append(item)

    consensus_metadata = _build_consensus_metadata(request, months, seed)
    hitl_flags, hitl_routing = _build_hitl_payload(
        request,
        consensus_metadata,
        unknown_hour,
        seed,
    )

    return {
        "target_year": target_year,
        "overall_confidence": "ESTIMATED" if unknown_hour else "HIGH",
        "monthly_scores": months,
        "engine_version": "annual_timing_bazi_transit.v2",
        "consensus_metadata": consensus_metadata,
        "hitl_flags": hitl_flags,
        "hitl_routing": hitl_routing,
    }
