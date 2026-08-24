"""Adapt deterministic engine results to the Horo v3.0 claim contract.

The core engines calculate chart state; this module supplies the stable
provenance envelope consumed by the v3 interpretation nodes.  It does not
perform additional metaphysical calculations or generate predictions.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4


def _as_dict(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise TypeError("engine result must be a dictionary")
    return dict(result)


def _calc_hash(result: dict[str, Any]) -> str:
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim_id(node_id: str, rule_id: str, calc_hash: str) -> str:
    return hashlib.sha256(f"{node_id}:{rule_id}:{calc_hash}".encode("utf-8")).hexdigest()


def _value(result: dict[str, Any], *keys: str, default: Any = "unknown") -> Any:
    current: Any = result
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _emit(
    result: dict[str, Any],
    *,
    node_id: str,
    tradition_domain: str,
    source_corpus: str,
    locator: str,
    interpretation_id: str,
    rule_id: str,
    statement: str,
    claim_type: str,
    session_id: str | None,
    materiality_weight: float = 0.9,
) -> dict[str, Any]:
    calc_hash = _calc_hash(result)
    claim = {
        "claim_id": _claim_id(node_id, rule_id, calc_hash),
        "materiality_weight": materiality_weight,
        "epistemic_trace": {
            "source_corpus": source_corpus,
            "locator": locator,
            "interpretation_id": interpretation_id,
            "applied_rule_id": rule_id,
            "derived_from_calc_hash": calc_hash,
            "rule_version": "3.0.0",
        },
        "statement": statement,
        "confidence_vector": {
            "calculation_integrity": 1.0,
            "rule_match_strength": 1.0,
            "source_support": 0.9,
            "interpretation_stability": 0.85,
            "cross_agent_agreement": 0.0,
        },
        "potential_conflicts": [],
        "claim_type": claim_type,
        "tags": [tradition_domain, "deterministic_engine"],
    }
    emission = {
        "node_id": node_id,
        "tradition_domain": tradition_domain,
        "session_id": session_id or str(uuid4()),
        "emitted_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_state_hash": calc_hash,
        "claims": [claim],
    }
    return emission


def adapt_bazi_to_claims(bazi_result: dict, session_id: str | None = None) -> dict:
    """Adapt a BaZi engine result into a v3.0 natal-structure emission."""
    result = _as_dict(bazi_result)
    dm = _value(result, "day_master", "stem")
    element = _value(result, "day_master", "element")
    strength = _value(result, "day_master_strength")
    return _emit(
        result,
        node_id="@Horo_BaZi_Node",
        tradition_domain="ming_xue_bazi",
        source_corpus="滴天髓",
        locator="论身强",
        interpretation_id="INTERP-BAZI-0001",
        rule_id="BAZI-STRENGTH-001",
        statement=f"Day Master {dm} ({element}) is assessed as {strength} from the deterministic pillar calculation, per rule BAZI-STRENGTH-001.",
        claim_type="natal_structure",
        session_id=session_id,
    )


def adapt_ziwei_to_claims(ziwei_result: dict, session_id: str | None = None) -> dict:
    """Adapt a Zi Wei engine result into a v3.0 natal-structure emission."""
    result = _as_dict(ziwei_result)
    branch = _value(result, "ming_gong_branch")
    star_branch = _value(result, "zi_wei_star_branch")
    return _emit(
        result,
        node_id="@Horo_ZiWei_Node",
        tradition_domain="ming_xue_ziwei",
        source_corpus="紫微斗数全书",
        locator="第三章·紫微星系",
        interpretation_id="INTERP-ZIWEI-0001",
        rule_id="ZIWEI-PALACE-001",
        statement=f"Life Palace (命宫) is mapped to branch {branch}, with ZiWei star branch {star_branch}, per rule ZIWEI-PALACE-001.",
        claim_type="natal_structure",
        session_id=session_id,
    )


def adapt_qimen_to_claims(qimen_result: dict, session_id: str | None = None) -> dict:
    """Adapt a Qi Men engine result into a v3.0 tactical-vector emission."""
    result = _as_dict(qimen_result)
    term = _value(result, "solar_term")
    dun = _value(result, "dun_type")
    ju = _value(result, "ju_number")
    return _emit(
        result,
        node_id="@Horo_QiMen_Node",
        tradition_domain="san_shi_qi_men",
        source_corpus="烟波钓叟歌",
        locator="全篇·三奇得使章",
        interpretation_id="INTERP-QIMEN-0001",
        rule_id="QIMEN-FORMATION-001",
        statement=f"The tactical chart uses {dun} Dun, Ju {ju}, under solar term {term}, per rule QIMEN-FORMATION-001.",
        claim_type="tactical_vector",
        session_id=session_id,
    )


def adapt_zeji_to_claims(zeji_result: dict, session_id: str | None = None) -> dict:
    """Adapt a Ze Ji engine result into a v3.0 date-selection emission."""
    result = _as_dict(zeji_result)
    officer = _value(result, "duty_officer")
    rating = _value(result, "rating_stars")
    return _emit(
        result,
        node_id="@Horo_ZeJi_Node",
        tradition_domain="ze_ji_xue",
        source_corpus="协纪辨方书",
        locator="卷七·岁破章",
        interpretation_id="INTERP-ZEJI-0001",
        rule_id="ZEJI-VETO-001",
        statement=f"The selected date has duty officer {officer} and suitability rating {rating} of 5, per rule ZEJI-VETO-001.",
        claim_type="event_mutation",
        session_id=session_id,
        materiality_weight=1.0,
    )


__all__ = [
    "adapt_bazi_to_claims",
    "adapt_ziwei_to_claims",
    "adapt_qimen_to_claims",
    "adapt_zeji_to_claims",
]
