"""
Horo Architecture v3.0 — Audit Node (L6 Adversarial Verification & Quality Gate)
Calculates Weighted Logical Consistency Index (LCIw), Weighted Residual Noise Index (RNIw),
executes Inversion Thinking, and looks up deterministic verdicts in the Audit Truth Table.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class AuditNode:
    """L6 Adversarial Audit Node evaluating epistemic integrity and logical consistency."""

    LCIW_PASS_THRESHOLD: float = 0.85
    LCIW_WARN_THRESHOLD: float = 0.70
    RNIW_PASS_THRESHOLD: float = 0.15
    RNIW_WARN_THRESHOLD: float = 0.20

    def evaluate_consensus_state(self, consensus_output: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full adversarial audit on the consensus state. Returns audit report."""
        claims = consensus_output.get("claims", [])
        arbitrated_edges = consensus_output.get("arbitrated_edges", [])
        hitl_escalations = consensus_output.get("hitl_escalations", [])

        # 1. Compute RNIw (Weighted Residual Noise Index)
        rniw, ungrounded_claims = self._compute_rniw(claims)

        # 2. Compute LCIw (Weighted Logical Consistency Index)
        lciw = self._compute_lciw(claims, arbitrated_edges, hitl_escalations)

        # 3. Inversion Thinking & Echo Chamber Detection
        echo_chamber_detected, echo_warnings = self._check_echo_chamber(claims)
        false_provenance_detected = any(
            c.get("is_false_provenance", False) for c in claims
        )
        unresolved_h2_detected = len(consensus_output.get("hard_vetoes", [])) > 0 and any(
            edge.get("status") == "active_unresolved" for edge in arbitrated_edges
        )

        # 4. Truth Table Verdict Lookup
        verdict, action_code, notes = self._determine_verdict(
            lciw=lciw,
            rniw=rniw,
            false_provenance=false_provenance_detected,
            echo_chamber=echo_chamber_detected,
            unresolved_h2=unresolved_h2_detected,
        )

        return {
            "verdict": verdict,
            "action_code": action_code,
            "metrics": {
                "lciw": round(lciw, 4),
                "rniw": round(rniw, 4),
                "lciw_passed": lciw >= self.LCIW_PASS_THRESHOLD,
                "rniw_passed": rniw <= self.RNIW_PASS_THRESHOLD,
            },
            "findings": {
                "ungrounded_claims_count": len(ungrounded_claims),
                "echo_chamber_detected": echo_chamber_detected,
                "false_provenance_detected": false_provenance_detected,
                "unresolved_h2_detected": unresolved_h2_detected,
                "warnings": echo_warnings,
                "notes": notes,
            },
            "can_proceed_to_composer": verdict in ("AUDIT_PASS", "AUDIT_PASS_WITH_WARNINGS"),
        }

    def _compute_rniw(self, claims: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Compute fraction of materiality-weighted ungrounded claims."""
        if not claims:
            return 0.0, []

        total_materiality = 0.0
        ungrounded_mass = 0.0
        ungrounded_list = []

        for c in claims:
            m = c.get("materiality_weight", 0.5)
            total_materiality += m
            cv = c.get("confidence_vector", {})
            ss = cv.get("source_support", 1.0)
            is_quarantined = c.get("is_quarantined", False)

            if ss == 0.0 or is_quarantined:
                ungrounded_mass += m
                ungrounded_list.append(c)

        if total_materiality == 0.0:
            return 0.0, []

        return (ungrounded_mass / total_materiality), ungrounded_list

    def _compute_lciw(
        self,
        claims: List[Dict[str, Any]],
        arbitrated_edges: List[Dict[str, Any]],
        hitl_escalations: List[Dict[str, Any]],
    ) -> float:
        """Compute Weighted Logical Consistency Index (1.0 = zero unresolved conflicts)."""
        active_conflicts = [
            e for e in arbitrated_edges if e.get("edge_type") == "contradicts" and e.get("status") != "resolved_by_priority"
        ] + hitl_escalations

        if not active_conflicts:
            return 1.0

        # Sum unresolved conflict penalties
        penalty_mass = sum(c.get("severity", 0.8) * 0.5 for c in active_conflicts)
        total_mass = max(len(claims) * 0.5, 1.0)
        lciw = max(0.0, 1.0 - (penalty_mass / total_mass))
        return lciw

    def _check_echo_chamber(self, claims: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Inversion check: high agent agreement with low canonical grounding."""
        echo_detected = False
        warnings = []

        for c in claims:
            cv = c.get("confidence_vector", {})
            caa = cv.get("cross_agent_agreement", 0.0)
            ss = cv.get("source_support", 1.0)
            if caa > 0.90 and ss < 0.50:
                echo_detected = True
                warnings.append(
                    f"Claim '{c.get('claim_id')}' shows cross_agent_agreement={caa} but low source_support={ss} (Echo Chamber pattern)"
                )

        return echo_detected, warnings

    def _determine_verdict(
        self,
        lciw: float,
        rniw: float,
        false_provenance: bool,
        echo_chamber: bool,
        unresolved_h2: bool,
    ) -> Tuple[str, str, str]:
        """Lookup deterministic verdict according to audit policy truth table."""
        if false_provenance:
            return "AUDIT_FAIL_ESCALATE", "QUARANTINE_AND_ESCALATE_HITL", "False provenance detected in claim emission."

        if unresolved_h2:
            return "AUDIT_FAIL_RECOMPUTE", "ENFORCE_HARD_EXCLUSION_VETO", "Unresolved Tier H2 hard exclusion detected."

        if lciw < self.LCIW_WARN_THRESHOLD:
            return "AUDIT_FAIL_ESCALATE", "ESCALATE_TO_HITL", f"LCIw {lciw:.2f} is below minimum threshold 0.70."

        if rniw > self.RNIW_WARN_THRESHOLD:
            return "AUDIT_FAIL_RECOMPUTE", "TRIGGER_H1_RECOMPUTE", f"RNIw {rniw:.2f} exceeds noise threshold 0.20."

        if (lciw < self.LCIW_PASS_THRESHOLD) or (rniw > self.RNIW_PASS_THRESHOLD) or echo_chamber:
            return (
                "AUDIT_PASS_WITH_WARNINGS",
                "COMPOSER_RELEASE_WITH_DISCLAIMER",
                "Minor logical divergence or echo chamber warning detected. Releasing with explicit disclaimer.",
            )

        return "AUDIT_PASS", "COMPOSER_RELEASE", "All quality thresholds met. Verified for final composition."
