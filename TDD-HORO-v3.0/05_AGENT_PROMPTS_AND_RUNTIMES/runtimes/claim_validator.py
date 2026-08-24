"""
Horo Architecture v3.0 — Claim Validator (L3/L4 Gateway Guard)
Validates Structured Atomic Claims emitted by L3/L4 LLM Nodes against Claim Emission Schema,
enforces Domain Firewalls, and checks Epistemic Provenance.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# Authoritative Tradition Domain Firewalls and Forbidden Terms
DOMAIN_FIREWALLS: Dict[str, Dict[str, Any]] = {
    "ming_xue_bazi": {
        "canonical_corpora": ["渊海子平", "滴天髓", "子平真诠", "三命通会", "穷通宝鉴"],
        "forbidden_terms": ["四化", "化禄", "化权", "化科", "化忌", "十二宫", "八门", "九星", "值符", "太乙", "三传"],
    },
    "ming_xue_ziwei": {
        "canonical_corpora": ["紫微斗数全书", "斗数骨髓赋", "太微赋", "十八飞星策天紫微斗数全集"],
        "forbidden_terms": ["日主", "用神", "喜神", "十神", "正官格", "八门", "九星", "值符"],
    },
    "xiang_xue_feng_shui": {
        "canonical_corpora": ["沈氏玄空学", "青囊奥语", "地理五诀", "天元五歌"],
        "forbidden_terms": ["日主", "用神", "四化", "紫微星", "天府星", "十神"],
    },
    "bu_shi_liu_yao": {
        "canonical_corpora": ["周易", "卜筮正宗", "增删卜易", "易隐"],
        "forbidden_terms": ["四化", "紫微", "八门", "值符", "九星", "奇门"],
    },
    "san_shi_qi_men": {
        "canonical_corpora": ["烟波钓叟歌", "奇门遁甲大全", "御定奇门宝鉴", "奇门遁甲统宗"],
        "forbidden_terms": ["日主", "命宫", "四化", "化忌", "十神", "大运"],
    },
    "san_shi_da_liu_ren": {
        "canonical_corpora": ["六壬大全", "六壬指南", "御定六壬直指", "六壬断案"],
        "forbidden_terms": ["四化", "紫微", "八门", "值符", "九星"],
    },
    "san_shi_tai_yi": {
        "canonical_corpora": ["太乙金镜式经", "太乙统宗宝鉴", "太乙秘籍"],
        "forbidden_terms": ["日主", "命宫", "四化", "十神"],
    },
    "ming_xue_qi_zheng": {
        "canonical_corpora": ["果老星宗", "星学大成", "张果星宗", "郑氏星案"],
        "forbidden_terms": ["八门", "值符", "九星", "三传", "四课"],
    },
    "xiang_xue_mian_xiang": {
        "canonical_corpora": ["麻衣神相", "柳庄相法", "神相全编", "太清神鉴"],
        "forbidden_terms": ["四化", "八门", "值符", "九星", "三奇"],
    },
    "ze_ji_xue": {
        "canonical_corpora": ["协纪辨方书", "御定万年历", "选择宗镜", "象吉通书"],
        "forbidden_terms": ["四化", "化禄", "化忌", "命宫", "身宫"],
    },
}

REQUIRED_CONFIDENCE_DIMENSIONS = [
    "calculation_integrity",
    "rule_match_strength",
    "source_support",
    "interpretation_stability",
    "cross_agent_agreement",
]


class ClaimValidator:
    """Validator for Structured Atomic Claims emitted by L3/L4 agent nodes."""

    @classmethod
    def validate_emission_payload(cls, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate entire claim emission payload. Returns (is_valid, list_of_violations)."""
        violations: List[str] = []

        if not isinstance(payload, dict):
            return False, ["Payload must be a JSON object"]

        node_id = payload.get("node_id")
        if not node_id or not isinstance(node_id, str) or not node_id.startswith("@Horo_"):
            violations.append(f"Invalid or missing node_id: '{node_id}'")

        domain = payload.get("tradition_domain")
        if domain not in DOMAIN_FIREWALLS:
            violations.append(f"Unknown tradition_domain: '{domain}'")

        claims = payload.get("claims")
        if not isinstance(claims, list) or len(claims) == 0:
            violations.append("Emission must contain at least one claim in 'claims' array")
            return False, violations

        firewall = DOMAIN_FIREWALLS.get(domain, {})
        canonical_corpora = firewall.get("canonical_corpora", [])
        forbidden_terms = firewall.get("forbidden_terms", [])

        for idx, claim in enumerate(claims):
            c_prefix = f"Claim[{idx}]"
            claim_id = claim.get("claim_id")
            if not claim_id:
                violations.append(f"{c_prefix} missing 'claim_id'")

            materiality = claim.get("materiality_weight")
            if materiality is None or not (0.0 <= materiality <= 1.0):
                violations.append(f"{c_prefix} materiality_weight must be a float in [0.0, 1.0]")

            statement = claim.get("statement", "")
            if not statement or len(statement) < 10:
                violations.append(f"{c_prefix} statement missing or too short (< 10 chars)")

            # Check Domain Firewall - forbidden terms in statement
            for term in forbidden_terms:
                if term in statement:
                    violations.append(
                        f"{c_prefix} Domain Firewall Breach: Statement contains forbidden term '{term}' for domain '{domain}'"
                    )

            # Epistemic Trace validation
            trace = claim.get("epistemic_trace")
            if not trace or not isinstance(trace, dict):
                violations.append(f"{c_prefix} missing or invalid 'epistemic_trace'")
            else:
                corpus = trace.get("source_corpus")
                if not corpus:
                    violations.append(f"{c_prefix}.epistemic_trace missing 'source_corpus'")
                elif corpus not in canonical_corpora:
                    violations.append(
                        f"{c_prefix}.epistemic_trace: 'source_corpus' '{corpus}' is not in canonical corpora for '{domain}'"
                    )

                if not trace.get("applied_rule_id"):
                    violations.append(f"{c_prefix}.epistemic_trace missing 'applied_rule_id'")
                if not trace.get("derived_from_calc_hash"):
                    violations.append(f"{c_prefix}.epistemic_trace missing 'derived_from_calc_hash'")

            # Confidence Vector validation
            cv = claim.get("confidence_vector")
            if not cv or not isinstance(cv, dict):
                violations.append(f"{c_prefix} missing or invalid 'confidence_vector'")
            else:
                for dim in REQUIRED_CONFIDENCE_DIMENSIONS:
                    val = cv.get(dim)
                    if val is None or not (0.0 <= val <= 1.0):
                        violations.append(f"{c_prefix}.confidence_vector dimension '{dim}' must be in [0.0, 1.0]")

        is_valid = len(violations) == 0
        return is_valid, violations
