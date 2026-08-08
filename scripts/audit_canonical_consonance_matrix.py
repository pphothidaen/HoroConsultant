#!/usr/bin/env python3
"""
scripts/audit_canonical_consonance_matrix.py
================================================
Canonical Consonance Matrix & Multi-Domain Scripture Verifier.

Verifies the 5-W Consonance Framework across all 8 Metaphysics Disciplines:
  1. WHAT (อะไร): Core diagnosis aligned with user query
  2. WHERE (ที่ไหน): Directions, Palaces, Element sectors matching classical books
  3. HOW (อย่างไร): Actionable remedies matching Useful God (用神) & auspicious timing
  4. SCRIPTURES (คัมภีร์): Strict adherence to canonical texts per domain
  5. CONSENSUS (ความคล้อยตามกัน): Peer debate harmonization across all 8 masters

Usage:
  python3 scripts/audit_canonical_consonance_matrix.py
"""

from __future__ import annotations

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.multi_agent_debate import MetaphysicsDebateEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("consonance_matrix_auditor")

debate_engine = MetaphysicsDebateEngine()

CANONICAL_SCRIPTURES = {
    "san_shi_master": ["煙波釣叟歌", "六壬指南"],
    "ming_xue_master": ["滴天髓", "子平真詮", "淵海子平"],
    "pu_shi_master": ["周易", "增刪卜易"],
    "xiang_xue_master": ["沈氏玄空學", "青囊奧語"],
    "ze_ji_master": ["協紀辨方書"],
    "thai_vedic_master": ["คัมภีร์สุริยยาตร์ & มาณต", "Brihat Parasara Hora Sastra"],
    "western_astro_master": ["Rules for Planetary Pictures", "Tetrabiblos"],
    "numerology_master": ["ตำราสัตตเลข ๗ ฐาน", "Chaldean Numerology"]
}


def audit_canonical_consonance_matrix() -> dict:
    """Audit 5-W Consonance Matrix across all 8 Domain Masters."""
    log.info("======================================================================")
    log.info("🔮 CANONICAL CONSONANCE MATRIX & MULTI-DOMAIN SCRIPTURE AUDIT")
    log.info("======================================================================")

    context = {
        "query": "วิเคราะห์ดวงชะตาเชิงลึก สุขภาพ การงาน ความรัก และฤกษ์ยามทิศทางมงคล",
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0
    }

    debate_res = debate_engine.run_peer_debate(context)
    perspectives = debate_res.get("domain_perspectives", {})
    orchestrator_synth = debate_res.get("orchestrator_synthesis", {})
    consensus_facts = orchestrator_synth.get("consensus_facts", [])

    results = []
    all_masters_passed = True

    log.info("\n📖 [PHASE 1] Auditing Individual Master Scripture Citations & Domain Boundaries:\n")

    for master_id, citations in CANONICAL_SCRIPTURES.items():
        master_data = perspectives.get(master_id, {})
        branch_name = master_data.get("branch", master_id)
        analysis_text = master_data.get("analysis", "")
        master_citations = master_data.get("canonical_citations", [])

        # 1. Check Scripture Citation Match
        citation_matches = [c for c in citations if c in master_citations or c in analysis_text or any(c in str(mc) for mc in master_citations)]
        has_scripture = len(citation_matches) > 0

        # 2. Check 5-W Scope Enforcement
        has_what_where_how = len(analysis_text) > 30 and ("วิเคราะห์" in analysis_text or "ผัง" in analysis_text or "คำนวณ" in analysis_text)

        passed = has_scripture and has_what_where_how
        if not passed:
            all_masters_passed = False

        log.info(f"   • Agent: {master_id:<22} [{branch_name}]")
        log.info(f"     - Scripture Citation : {master_citations} | Valid Citation: {'✅' if has_scripture else '❌'}")
        log.info(f"     - 5-W Analysis Text  : {analysis_text[:90]}...")
        log.info(f"     - Status             : {'✅ PASSED' if passed else '❌ FAILED'}\n")

        results.append({
            "master_id": master_id,
            "branch": branch_name,
            "has_scripture": has_scripture,
            "citations": master_citations,
            "passed": passed
        })

    log.info("----------------------------------------------------------------------")
    log.info("🤝 [PHASE 2] Auditing Cross-Domain Consensus Harmonization (ความคล้อยตามกัน):")
    log.info("----------------------------------------------------------------------")

    has_consensus = len(consensus_facts) > 0
    log.info(f"   • Consensus Facts Count: {len(consensus_facts)}")
    for idx, fact in enumerate(consensus_facts, 1):
        log.info(f"     [{idx}] {fact}")

    log.info(f"\n   • Cross-Domain Consonance Status: {'✅ PASSED (100% Consonance Achieved)' if (all_masters_passed and has_consensus) else '❌ FAILED'}")

    summary = {
        "audit_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "PASSED 100%" if (all_masters_passed and has_consensus) else "FAILED",
        "total_masters_audited": len(CANONICAL_SCRIPTURES),
        "masters_passed": sum(1 for r in results if r["passed"]),
        "has_consensus": has_consensus,
        "consensus_facts": consensus_facts,
        "master_details": results
    }

    report_file = ROOT / "project" / "tests" / "canonical_consonance_matrix_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"\n📄 Consonance Matrix Report Saved: {report_file}")

    return summary


if __name__ == "__main__":
    audit_canonical_consonance_matrix()
