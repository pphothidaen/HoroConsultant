"""
Horo Architecture v3.0 — Plan Composer Node (L7 User Delivery & Emission Layer)
Synthesizes arbitrated and audited claims into an objective user advisory report,
and enforces the mandatory Epistemic Disclaimer verbatim on all outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List

MANDATORY_EPISTEMIC_DISCLAIMER_TH = (
    "ผลการวิเคราะห์นี้เกิดขึ้นจากการประมวลผลตรรกะตามกฎของสำนักวิชาที่เลือก "
    "(Tradition-Rule Validity) และความสอดคล้องของแบบจำลอง (Interpretive Consistency) เท่านั้น "
    "ไม่ถือเป็นการรับรองผลสัมฤทธิ์ในอนาคตเชิงประจักษ์ "
    "(Predictive Validity is Explicitly Disclaimed)"
)

MANDATORY_EPISTEMIC_DISCLAIMER_EN = (
    "This analytical report is generated solely through rule-based deduction according to canonical metaphysics "
    "traditions (Tradition-Rule Validity) and model consistency (Interpretive Consistency). "
    "It does not constitute empirical guarantees of future life outcomes (Predictive Validity is Explicitly Disclaimed)."
)


class PlanComposer:
    """L7 Plan Composer synthesizing user reports and attaching mandatory epistemic disclaimers."""

    def compose_final_report(
        self,
        consensus_output: Dict[str, Any],
        audit_output: Dict[str, Any],
        language: str = "th",
    ) -> Dict[str, Any]:
        """Compose final structured response."""
        if not audit_output.get("can_proceed_to_composer", False):
            raise PermissionError(
                f"Cannot compose report: Audit failed with verdict '{audit_output.get('verdict')}'"
            )

        claims = consensus_output.get("claims", [])
        hard_vetoes = consensus_output.get("hard_vetoes", [])
        superseded_ids = {
            edge.get("target_claim_id")
            for edge in consensus_output.get("arbitrated_edges", [])
            if edge.get("edge_type") == "supersedes"
        }

        # Filter active effective claims
        effective_claims = [
            c for c in claims
            if c.get("claim_id") not in superseded_ids and not c.get("is_quarantined", False)
        ]

        disclaimer = (
            MANDATORY_EPISTEMIC_DISCLAIMER_TH if language == "th" else MANDATORY_EPISTEMIC_DISCLAIMER_EN
        )

        # Build sections
        discipline_insights: List[Dict[str, Any]] = []
        for c in effective_claims:
            discipline_insights.append({
                "domain": c.get("_domain", c.get("tradition_domain")),
                "statement": c.get("statement"),
                "applied_rule": c.get("epistemic_trace", {}).get("applied_rule_id"),
                "canon_source": c.get("epistemic_trace", {}).get("source_corpus"),
                "materiality": c.get("materiality_weight"),
            })

        exclusion_advisories: List[Dict[str, Any]] = []
        for v in hard_vetoes:
            exclusion_advisories.append({
                "veto_statement": v.get("statement"),
                "rule_id": v.get("epistemic_trace", {}).get("applied_rule_id"),
                "canon_source": v.get("epistemic_trace", {}).get("source_corpus"),
            })

        report_markdown = self._generate_markdown(
            user_intent=consensus_output.get("user_intent", "GENERAL"),
            insights=discipline_insights,
            exclusions=exclusion_advisories,
            audit_metrics=audit_output.get("metrics", {}),
            audit_verdict=audit_output.get("verdict", ""),
            disclaimer=disclaimer,
            warnings=audit_output.get("findings", {}).get("warnings", []),
        )

        return {
            "session_id": consensus_output.get("session_id"),
            "status": "COMPLETED",
            "report_markdown": report_markdown,
            "has_epistemic_disclaimer": disclaimer in report_markdown,
            "effective_claims_count": len(effective_claims),
            "excluded_vetoes_count": len(hard_vetoes),
            "audit_verdict": audit_output.get("verdict"),
            "lciw": audit_output.get("metrics", {}).get("lciw"),
            "rniw": audit_output.get("metrics", {}).get("rniw"),
        }

    def _generate_markdown(
        self,
        user_intent: str,
        insights: List[Dict[str, Any]],
        exclusions: List[Dict[str, Any]],
        audit_metrics: Dict[str, Any],
        audit_verdict: str,
        disclaimer: str,
        warnings: List[str],
    ) -> str:
        """Render final Markdown string."""
        md_lines = [
            f"# 📜 รายงานการประมวลผลเชิงภววิทยา HoroConsultant v3.0",
            f"> **Intent Focus**: `{user_intent}` | **Audit Status**: `{audit_verdict}` | **LCIw**: `{audit_metrics.get('lciw', 1.0)}` | **RNIw**: `{audit_metrics.get('rniw', 0.0)}`",
            "",
            "---",
            "",
            "## 1. บทสังเคราะห์ความสอดคล้องเชิงบูรณาการ (Consensus Synthesis)",
        ]

        for item in insights:
            md_lines.append(
                f"- **[{item['domain']}]** {item['statement']} *(อ้างอิง: 《{item['canon_source']}》, กฎ `{item['applied_rule']}`)*"
            )

        if exclusions:
            md_lines.extend([
                "",
                "## 2. ข้อห้ามและช่วงเวลาต้องห้ามเด็ดขาด (Hard Exclusion Gate)",
            ])
            for exc in exclusions:
                md_lines.append(
                    f"- ⚠️ **[VETO]** {exc['veto_statement']} *(อ้างอิง: 《{exc['canon_source']}》, กฎ `{exc['rule_id']}`)*"
                )

        if warnings:
            md_lines.extend([
                "",
                "## 3. หมายเหตุข้อจำกัดและความสอดคล้อง (Audit Advisories)",
            ])
            for w in warnings:
                md_lines.append(f"- ℹ️ {w}")

        md_lines.extend([
            "",
            "---",
            "",
            "### ⚖️ พันธสัญญาญาณวิทยาและการปฏิเสธการรับรอง (Epistemic Disclaimer)",
            f"> *{disclaimer}*",
            "",
            "<!-- HORO_V3_EMISSION_VERIFIED -->",
        ])

        return "\n".join(md_lines)
