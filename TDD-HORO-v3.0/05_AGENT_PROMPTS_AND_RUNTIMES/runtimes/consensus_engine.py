"""
Horo Architecture v3.0 — Consensus Engine (L5 Orchestration & Arbitration Layer)
Constructs the Tri-Graph state, executes Dynamic Arbitration according to user intent,
evaluates Tier H2 Hard Exclusion vetoes, and resolves cross-domain contradictions.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

INTENT_HIERARCHIES: Dict[str, List[str]] = {
    "STRATEGIC_TIMING_ACTION": [
        "san_shi_qi_men",
        "ze_ji_xue",
        "ming_xue_bazi",
        "ming_xue_ziwei",
        "san_shi_da_liu_ren",
    ],
    "NATAL_CHARACTER_PATH": [
        "ming_xue_bazi",
        "ming_xue_ziwei",
        "ming_xue_qi_zheng",
        "xiang_xue_mian_xiang",
    ],
    "SPATIAL_LOCATION_OFFICE": [
        "xiang_xue_feng_shui",
        "san_shi_qi_men",
        "ming_xue_bazi",
    ],
    "TACTICAL_DIVINATION_EVENT": [
        "bu_shi_liu_yao",
        "san_shi_da_liu_ren",
        "san_shi_qi_men",
    ],
    "HEALTH_VITALITY": [
        "ming_xue_bazi",
        "ming_xue_ziwei",
        "xiang_xue_mian_xiang",
    ],
    "RELATIONSHIP_SYNASTRY": [
        "ming_xue_bazi",
        "ming_xue_ziwei",
        "bu_shi_liu_yao",
    ],
}


class ConsensusEngine:
    """L5 Multi-Agent Consensus and Dynamic Arbitration Engine."""

    def __init__(self, user_intent: str = "STRATEGIC_TIMING_ACTION") -> None:
        self.user_intent = user_intent
        self.priority_order = INTENT_HIERARCHIES.get(
            user_intent,
            ["ming_xue_bazi", "ming_xue_ziwei", "san_shi_qi_men"],
        )

    def arbitrate_claims(
        self, claim_emissions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize and arbitrate claims from multiple L3/L4 agent emissions."""
        all_claims: List[Dict[str, Any]] = []
        events_emitted: List[str] = []
        hard_vetoes: List[Dict[str, Any]] = []
        arbitrated_edges: List[Dict[str, Any]] = []
        hitl_escalations: List[Dict[str, Any]] = []

        # 1. Collect all valid claims
        for emission in claim_emissions:
            domain = emission.get("tradition_domain", "")
            for claim in emission.get("claims", []):
                enriched = dict(claim)
                enriched["_domain"] = domain
                enriched["_node_id"] = emission.get("node_id", "")
                all_claims.append(enriched)

        # 2. Check for Tier H2 Hard Exclusions (Vetoes)
        for claim in all_claims:
            if claim.get("claim_type") == "hard_exclusion":
                hard_vetoes.append(claim)
                events_emitted.append("FSM_H2_EXCLUSION")

        # 3. Detect and resolve declared conflicts / cross-domain contradictions
        for i in range(len(all_claims)):
            for j in range(i + 1, len(all_claims)):
                c1, c2 = all_claims[i], all_claims[j]
                d1, d2 = c1["_domain"], c2["_domain"]
                if d1 == d2:
                    continue

                # Check if potential conflict is declared or exists
                conflicts = c1.get("potential_conflicts", []) + c2.get("potential_conflicts", [])
                is_conflicting = any(
                    conf.get("target_domain") in (d1, d2) for conf in conflicts
                )

                if is_conflicting:
                    edge = self._resolve_conflict(c1, c2, events_emitted, hitl_escalations)
                    arbitrated_edges.append(edge)

        events_emitted.append("CONSENSUS_GRAPH_BUILT")

        return {
            "session_id": str(uuid.uuid4()),
            "user_intent": self.user_intent,
            "total_claims": len(all_claims),
            "claims": all_claims,
            "hard_vetoes": hard_vetoes,
            "arbitrated_edges": arbitrated_edges,
            "hitl_escalations": hitl_escalations,
            "events_emitted": list(set(events_emitted)),
            "requires_hitl": len(hitl_escalations) > 0,
        }

    def _resolve_conflict(
        self,
        c1: Dict[str, Any],
        c2: Dict[str, Any],
        events_emitted: List[str],
        hitl_escalations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply dynamic arbitration rules between two conflicting claims."""
        events_emitted.append("FSM_H3_ARBITRATION")
        d1, d2 = c1["_domain"], c2["_domain"]

        rank1 = self.priority_order.index(d1) if d1 in self.priority_order else 99
        rank2 = self.priority_order.index(d2) if d2 in self.priority_order else 99

        if rank1 < rank2:  # Domain 1 wins by priority dominance (ARB-01)
            winner, loser = c1, c2
            subtype = "direct_supersedes"
        elif rank2 < rank1:  # Domain 2 wins by priority dominance (ARB-01)
            winner, loser = c2, c1
            subtype = "direct_supersedes"
        else:  # Equal rank tiebreaker (ARB-02)
            s1 = self._composite_score(c1)
            s2 = self._composite_score(c2)
            if abs(s1 - s2) >= 0.20:
                winner = c1 if s1 > s2 else c2
                loser = c2 if s1 > s2 else c1
                subtype = "effective_supersedes"
            else:
                # Severity check for HITL escalation
                hitl_escalations.append({
                    "claim_a_id": c1.get("claim_id"),
                    "claim_b_id": c2.get("claim_id"),
                    "domain_a": d1,
                    "domain_b": d2,
                    "reason": "Equal intent rank with composite score delta < 0.20",
                })
                events_emitted.append("FSM_H3_HITL_ESCALATION")
                return {
                    "edge_type": "contradicts",
                    "status": "active_escalated_to_hitl",
                    "claim_a": c1.get("claim_id"),
                    "claim_b": c2.get("claim_id"),
                }

        return {
            "edge_type": "supersedes",
            "subtype": subtype,
            "source_claim_id": winner.get("claim_id"),
            "target_claim_id": loser.get("claim_id"),
            "winning_domain": winner.get("_domain"),
            "arbitration_rule": "ARB-01-PRIORITY-DOMINANCE" if rank1 != rank2 else "ARB-02-EQUAL-RANK-TIEBREAKER",
        }

    @staticmethod
    def _composite_score(claim: Dict[str, Any]) -> float:
        """Compute composite confidence score S for tiebreaking."""
        m = claim.get("materiality_weight", 0.5)
        cv = claim.get("confidence_vector", {})
        ci = cv.get("calculation_integrity", 0.8)
        ss = cv.get("source_support", 0.8)
        rm = cv.get("rule_match_strength", 0.8)
        return m * (0.4 * ci + 0.3 * ss + 0.3 * rm)
