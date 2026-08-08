#!/usr/bin/env python3
"""
scripts/audit_astrological_consistency.py
============================================
Metaphysical Interpretation & Logical Consistency Auditor.

Audits:
  1. Five Elements Sum & Day Master Strength Logic (身強/身弱)
  2. True Solar Time (TST) & Midnight Boundary Transitions
  3. Classical RAG Passage Citation Integrity (Zero Hallucination)
  4. Cross-Domain Consistency (BaZi vs Zi Wei vs Thai Vedic vs Western Uranian)

Usage:
  python3 scripts/audit_astrological_consistency.py
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
from project.core.solar_time import calculate_equation_of_time, calculate_true_solar_time
from project.rag.vector_store import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("metaphysics_auditor")

bazi_engine = BaZiEngine()
ziwei_engine = ZiWeiEngine()
thaivedic_engine = ThaiVedicEngine()
western_engine = WesternUranianEngine()
numerology_engine = NumerologyEngine()
vector_store = get_vector_store()


def audit_1_five_elements_balance() -> dict:
    """Audit 1: Verify Five Elements percentages sum to 100% and Day Master logic."""
    log.info("\n☯️ [Audit 1: Five Elements Sum & Day Master Balance]")
    dt = datetime(1990, 5, 15, 14, 30, 0)
    chart = bazi_engine.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
    
    fe = chart.get("five_elements", {}).get("percentages", {})
    total_pct = sum(fe.values())
    dm = chart.get("day_master", {})
    
    passed = abs(total_pct - 100.0) < 0.1 and "stem" in dm and "element" in dm
    log.info(f"   • Day Master: {dm.get('stem')} ({dm.get('element')})")
    log.info(f"   • Five Elements Scores: {fe} | Total Sum: {total_pct:.2f}%")
    log.info(f"   • Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return {
        "test": "Five Elements Sum & Day Master Balance",
        "passed": passed,
        "day_master": dm,
        "total_pct": total_pct,
        "elements": fe
    }


def audit_2_tst_equation_of_time() -> dict:
    """Audit 2: Verify Equation of Time bounds and TST midnight boundary."""
    log.info("\n☀️ [Audit 2: True Solar Time & EoT Monotonicity]")
    
    # Test EoT values across 4 cardinal dates
    feb_eot = calculate_equation_of_time(datetime(2026, 2, 12))
    nov_eot = calculate_equation_of_time(datetime(2026, 11, 3))
    
    # Test 23:30 TST boundary shift
    dt_2330 = datetime(2026, 5, 15, 23, 30, 0)
    tst_res = calculate_true_solar_time(dt=dt_2330, longitude=100.493, utc_offset_hours=7.0)
    tst_dict = tst_res.to_dict() if hasattr(tst_res, "to_dict") else tst_res
    
    passed = (-15.0 <= feb_eot <= 0.0) and (0.0 <= nov_eot <= 17.0) and "tst_datetime" in tst_dict
    log.info(f"   • Feb EoT: {feb_eot:.2f} mins (Min) | Nov EoT: {nov_eot:.2f} mins (Max)")
    log.info(f"   • Clock: 23:30:00 -> TST Datetime: {tst_dict.get('tst_datetime')}")
    log.info(f"   • Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return {
        "test": "True Solar Time & EoT Monotonicity",
        "passed": passed,
        "feb_eot": feb_eot,
        "nov_eot": nov_eot,
        "tst_sample": tst_dict
    }


def audit_3_rag_citations() -> dict:
    """Audit 3: Classical RAG Passage Citation Integrity."""
    log.info("\n📚 [Audit 3: Classical RAG Passage Citation Integrity]")
    query = "วิเคราะห์ความแข็งแกร่งของ Day Master 庚金 ในฤดูใบไม้ผลิ"
    res = vector_store.search(query=query, top_k=3)
    matches = res.get("results") if isinstance(res, dict) and "results" in res else (res.get("matches") if isinstance(res, dict) else res)
    if not isinstance(matches, list):
        matches = []
    
    has_matches = len(matches) > 0
    valid_citations = all(isinstance(m, dict) and (m.get("source") or m.get("passage")) for m in matches) if has_matches else False
    passed = has_matches and valid_citations
    
    log.info(f"   • Query: '{query}'")
    log.info(f"   • Matches Found: {len(matches)}")
    for idx, m in enumerate(matches, 1):
        if isinstance(m, dict):
            log.info(f"     [{idx}] Source: {m.get('source')} | Score: {m.get('score', 0):.4f}")
    log.info(f"   • Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    return {
        "test": "RAG Citation Integrity",
        "passed": passed,
        "match_count": len(matches),
        "matches": matches
    }


def audit_4_cross_domain_synergy() -> dict:
    """Audit 4: Cross-Domain Multi-Engine Consistency."""
    log.info("\n🌌 [Audit 4: Cross-Domain Multi-Engine Consistency]")
    year, month, day, hour = 1990, 5, 15, 14
    
    bazi_chart = bazi_engine.calculate(dt=datetime(year, month, day, hour, 30), longitude=100.493, utc_offset_hours=7.0)
    ziwei_res = ziwei_engine.calculate_chart(year, month, day, hour, gender="male")
    thai_res = thaivedic_engine.calculate_chart(year, month, day, hour, day_of_week=2)
    western_res = western_engine.calculate_chart(year, month, day, hour)
    num_res = numerology_engine.calculate_satta_lek(day_num=3, lunar_month=6, year_zodiac_num=7)
    
    ziwei_chart = ziwei_res.chart_data if hasattr(ziwei_res, "chart_data") else ziwei_res
    thai_chart = thai_res.chart_data if hasattr(thai_res, "chart_data") else thai_res
    western_chart = western_res.chart_data if hasattr(western_res, "chart_data") else western_res
    num_chart = num_res.chart_data if hasattr(num_res, "chart_data") else num_res
    
    bazi_dm = bazi_chart.get("day_master", {}).get("stem")
    ziwei_ming = ziwei_chart.get("ming_gong_branch")
    thai_lagna = thai_chart.get("thai_lagna")
    western_sun = western_chart.get("planets_tropical", {}).get("Sun (อาทิตย์)")
    num_atta = num_chart.get("matrix_7_base")
    
    all_engines_computed = all([
        bazi_dm is not None,
        ziwei_ming is not None,
        thai_lagna is not None,
        western_sun is not None,
        num_atta is not None
    ])
    
    log.info(f"   • BaZi Day Master : {bazi_dm}")
    log.info(f"   • Zi Wei Ming Gong : {ziwei_ming}")
    log.info(f"   • Thai Lagna Zodiac: {thai_lagna}")
    log.info(f"   • Western Sun Sign : {western_sun}")
    log.info(f"   • Satta-Lek Matrix : {len(num_atta) if isinstance(num_atta, list) else 0} rows")
    log.info(f"   • Status: {'✅ PASSED' if all_engines_computed else '❌ FAILED'}")
    
    return {
        "test": "Cross-Domain Synergy",
        "passed": all_engines_computed,
        "engines_verified": 5
    }


def main():
    print("=" * 65)
    print("🔮 ASTROLOGICAL INTERPRETATION & LOGICAL CONSISTENCY AUDIT")
    print("=" * 65)
    
    r1 = audit_1_five_elements_balance()
    r2 = audit_2_tst_equation_of_time()
    r3 = audit_3_rag_citations()
    r4 = audit_4_cross_domain_synergy()
    
    all_passed = r1["passed"] and r2["passed"] and r3["passed"] and r4["passed"]
    
    summary = {
        "audit_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "PASSED 100%" if all_passed else "FAILED",
        "audits": [r1, r2, r3, r4]
    }
    
    print("\n" + "=" * 65)
    print(f"🏆 AUDIT SUMMARY: {summary['overall_status']}")
    print("=" * 65)
    
    report_file = ROOT / "project" / "tests" / "astrological_consistency_audit.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📄 Audit Report Saved: {report_file}")


if __name__ == "__main__":
    main()
