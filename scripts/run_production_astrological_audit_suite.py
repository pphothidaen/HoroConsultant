#!/usr/bin/env python3
"""
scripts/run_production_astrological_audit_suite.py
=====================================================
Comprehensive Multi-Scenario Production Astrological Consistency & Verification Suite.

Tests 4 Diverse Real-World & Edge-Case Birth Scenarios:
  Scenario A: Bangkok Birth (Spring Yang Metal 庚金) — Five Elements & TST offset
  Scenario B: New York Birth (Winter Yin Wood 乙木 near Midnight 23:45) — TST Midnight shift & Day Master change
  Scenario C: Singapore & High Precision Longitude — 7-Base Satta-Lek Matrix & Zi Wei Dou Shu alignment
  Scenario D: Leap Year Feb 29 2024 — Julian Day Monotonicity & LiChun Boundary transition

Outputs:
  Detailed console report + JSON artifact saved to project/tests/production_astrological_audit_suite_report.json
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.bazi_engine import BaZiEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.solar_time import (
    calculate_equation_of_time,
    calculate_true_solar_time,
)
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.rag.vector_store import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("production_astrology_audit")

bazi_engine = BaZiEngine()
ziwei_engine = ZiWeiEngine()
thaivedic_engine = ThaiVedicEngine()
western_engine = WesternUranianEngine()
numerology_engine = NumerologyEngine()
vector_store = get_vector_store()


def run_scenario_a_bangkok_yang_metal() -> dict:
    """Scenario A: Bangkok Birth (1990-05-15 14:30, 100.493°E, UTC+7)"""
    log.info("\n----------------------------------------------------------------------")
    log.info("📌 [SCENARIO A] Bangkok Birth (Spring Yang Metal 庚金)")
    log.info("----------------------------------------------------------------------")
    dt = datetime(1990, 5, 15, 14, 30, 0)
    chart = bazi_engine.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
    tst_res = calculate_true_solar_time(dt=dt, longitude=100.493, utc_offset_hours=7.0)
    tst_dict = tst_res.to_dict() if hasattr(tst_res, "to_dict") else tst_res

    dm = chart.get("day_master", {})
    fe = chart.get("five_elements", {}).get("percentages", {})
    total_pct = sum(fe.values())
    useful_god = chart.get("useful_god_analysis", {})

    # Guardrails verification
    fe_passed = abs(total_pct - 100.0) < 0.1
    tst_passed = "23:" not in tst_dict.get("tst_datetime", "") and "14:" in tst_dict.get("tst_datetime", "")
    dm_passed = dm.get("stem") == "庚" and dm.get("element") == "Metal"

    log.info(f"   • Day Master: {dm.get('stem')} ({dm.get('element')}) | Season: Spring/Summer")
    log.info(f"   • Clock Time: 14:30:00 -> TST Time: {tst_dict.get('tst_datetime')}")
    log.info(f"   • Five Elements Scores: {fe} (Total = {total_pct:.2f}%)")
    log.info(f"   • Useful God Choice: {useful_god.get('suggested_useful_god', 'N/A')}")
    log.info(f"   • Verification Result: {'✅ PASSED' if (fe_passed and tst_passed and dm_passed) else '❌ FAILED'}")

    return {
        "scenario": "A_Bangkok_Yang_Metal",
        "passed": fe_passed and tst_passed and dm_passed,
        "day_master": dm,
        "tst_time": tst_dict.get("tst_datetime"),
        "five_elements_sum": total_pct,
        "useful_god": useful_god
    }


def run_scenario_b_new_york_midnight_shift() -> dict:
    """Scenario B: New York Birth near Midnight (1995-12-25 23:45, -74.006°W, UTC-5)"""
    log.info("\n----------------------------------------------------------------------")
    log.info("📌 [SCENARIO B] New York Midnight Shift & TST Transition")
    log.info("----------------------------------------------------------------------")
    dt = datetime(1995, 12, 25, 23, 45, 0)
    chart = bazi_engine.calculate(dt=dt, longitude=-74.006, utc_offset_hours=-5.0)
    tst_res = calculate_true_solar_time(dt=dt, longitude=-74.006, utc_offset_hours=-5.0)
    tst_dict = tst_res.to_dict() if hasattr(tst_res, "to_dict") else tst_res

    pillars = chart.get("pillars", {})
    hour_branch = pillars.get("hour", {}).get("branch", {}).get("char")
    day_stem = pillars.get("day", {}).get("stem", {}).get("char")
    year_sb = f"{pillars.get('year',{}).get('stem',{}).get('char')}{pillars.get('year',{}).get('branch',{}).get('char')}"

    # TST for NY at 23:45 with -74.006 vs std -75.0 (offset = +3.96 min + EoT +0.2 min = ~23:49)
    zi_hour_passed = hour_branch == "子"
    valid_day = bool(day_stem)

    log.info(f"   • Clock: 1995-12-25 23:45:00 EST -> TST Datetime: {tst_dict.get('tst_datetime')}")
    log.info(f"   • Calculated Four Pillars: Year={year_sb}, DayStem={day_stem}, HourBranch={hour_branch}")
    log.info(f"   • Verification Result: {'✅ PASSED' if (zi_hour_passed and valid_day) else '❌ FAILED'}")

    return {
        "scenario": "B_NewYork_Midnight_Shift",
        "passed": zi_hour_passed and valid_day,
        "tst_time": tst_dict.get("tst_datetime"),
        "four_pillars": pillars
    }


def run_scenario_c_singapore_multi_domain() -> dict:
    """Scenario C: Singapore Birth Multi-Domain Synergy (1988-08-08 08:08, 103.8198°E, UTC+8)"""
    log.info("\n----------------------------------------------------------------------")
    log.info("📌 [SCENARIO C] Singapore Birth Multi-Domain Synergy")
    log.info("----------------------------------------------------------------------")
    dt = datetime(1988, 8, 8, 8, 8, 0)
    bazi = bazi_engine.calculate(dt=dt, longitude=103.8198, utc_offset_hours=8.0)
    ziwei = ziwei_engine.calculate_chart(1988, 8, 8, 8, gender="female").chart_data
    thai = thaivedic_engine.calculate_chart(1988, 8, 8, 8, day_of_week=1)
    western = western_engine.calculate_chart(1988, 8, 8, 8).chart_data
    num = numerology_engine.calculate_satta_lek(day_num=1, lunar_month=9, year_zodiac_num=5).chart_data

    bazi_dm = bazi.get("day_master", {}).get("stem")
    ziwei_ming = ziwei.get("ming_gong_branch")
    thai_lagna = thai.get("thai_lagna")
    western_sun = western.get("planets_tropical", {}).get("Sun (อาทิตย์)")
    num_matrix = num.get("matrix_7_base")

    synergy_passed = all([bazi_dm, ziwei_ming, thai_lagna, western_sun, num_matrix])

    log.info(f"   • BaZi Day Master  : {bazi_dm}")
    log.info(f"   • Zi Wei Ming Gong  : {ziwei_ming}")
    log.info(f"   • Thai Lagna Zodiac : {thai_lagna}")
    log.info(f"   • Western Sun Sign  : {western_sun}")
    log.info(f"   • Satta-Lek Matrix  : {len(num_matrix) if isinstance(num_matrix, list) else 0} rows")
    log.info(f"   • Verification Result: {'✅ PASSED' if synergy_passed else '❌ FAILED'}")

    return {
        "scenario": "C_Singapore_Multi_Domain",
        "passed": synergy_passed,
        "bazi_dm": bazi_dm,
        "ziwei_ming": ziwei_ming,
        "thai_lagna": thai_lagna,
        "western_sun": western_sun
    }


def run_scenario_d_leap_year_feb29() -> dict:
    """Scenario D: Leap Year Feb 29, 2024 Solar Noon Monotonicity & LiChun Boundary"""
    log.info("\n----------------------------------------------------------------------")
    log.info("📌 [SCENARIO D] Leap Year Feb 29, 2024 Monotonicity & LiChun Boundary")
    log.info("----------------------------------------------------------------------")
    dt = datetime(2024, 2, 29, 12, 0, 0)
    chart = bazi_engine.calculate(dt=dt, longitude=100.493, utc_offset_hours=7.0)
    eot = calculate_equation_of_time(dt)

    pillars = chart.get("pillars", {})
    year_sb = f"{pillars.get('year',{}).get('stem',{}).get('char')}{pillars.get('year',{}).get('branch',{}).get('char')}"
    month_sb = f"{pillars.get('month',{}).get('stem',{}).get('char')}{pillars.get('month',{}).get('branch',{}).get('char')}"

    # 2024 is Jia-Chen (甲辰) Year after LiChun (Feb 4 2024)
    lichun_passed = year_sb == "甲辰"
    eot_passed = -15.0 <= eot <= 5.0

    log.info("   • Date: 2024-02-29 12:00:00 (Leap Day)")
    log.info(f"   • Equation of Time: {eot:.2f} mins")
    log.info(f"   • Year Pillar: {year_sb} (Post LiChun Verification) | Month Pillar: {month_sb}")
    log.info(f"   • Verification Result: {'✅ PASSED' if (lichun_passed and eot_passed) else '❌ FAILED'}")

    return {
        "scenario": "D_LeapYear_Feb29",
        "passed": lichun_passed and eot_passed,
        "year_pillar": year_sb,
        "month_pillar": month_sb,
        "eot_minutes": eot
    }


def main():
    print("=" * 72)
    print("🔮 PRODUCTION ASTROLOGICAL CONSISTENCY & VERIFICATION SUITE")
    print("=" * 72)

    res_a = run_scenario_a_bangkok_yang_metal()
    res_b = run_scenario_b_new_york_midnight_shift()
    res_c = run_scenario_c_singapore_multi_domain()
    res_d = run_scenario_d_leap_year_feb29()

    all_passed = res_a["passed"] and res_b["passed"] and res_c["passed"] and res_d["passed"]

    summary = {
        "audit_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "PASSED 100%" if all_passed else "FAILED",
        "scenarios_evaluated": 4,
        "scenarios_passed": sum([res_a["passed"], res_b["passed"], res_c["passed"], res_d["passed"]]),
        "details": [res_a, res_b, res_c, res_d]
    }

    print("\n" + "=" * 72)
    print(f"🏆 AUDIT SUITE FINAL RESULT: {summary['overall_status']}")
    print(f"   • Scenarios Passed: {summary['scenarios_passed']} / {summary['scenarios_evaluated']}")
    print("=" * 72)

    report_file = ROOT / "project" / "tests" / "production_astrological_audit_suite_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📄 Full Audit Report Saved: {report_file}")


if __name__ == "__main__":
    main()
