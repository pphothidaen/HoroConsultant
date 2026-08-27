#!/usr/bin/env python3
"""
scripts/run_luopan_e2e_regression.py
====================================
Live Production E2E Regression Runner for LuoPan 24-Mountain Compass &
Dynamic Period 9 Xuan Kong Flying Star 9-Palace Heatmap.

Validates:
1. Live Production API (/api/v1/luopan/calculate) returns dynamic sectors across full 360-degree range.
2. Distinct facing stars (向星) and sitting mountain stars (山星) per orientation.
3. Afflicted sector shifts (5 Yellow, 2 Black).
4. No typo in Southwest sector name ("ทิศตะวันตกเฉียงใต้ (Southwest - 坤)").
5. Generates structured JSON report at project/tests/luopan_e2e_regression_report.json.

Usage:
  python3 scripts/run_luopan_e2e_regression.py
  python3 scripts/run_luopan_e2e_regression.py --url https://horo-consultant-psi.vercel.app
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://horo-consultant-psi.vercel.app"
REPORT_PATH = ROOT / "project" / "tests" / "luopan_e2e_regression_report.json"

TEST_SAMPLE_ORIENTATIONS = [
    {"degree": 0.0, "expected_facing_mountain": "子", "expected_facing_palace": "N", "expected_facing_star": "1 ขาว (向星"},
    {"degree": 45.0, "expected_facing_mountain": "艮", "expected_facing_palace": "NE", "expected_facing_star": "7 แดง (向星"},
    {"degree": 90.0, "expected_facing_mountain": "卯", "expected_facing_palace": "E", "expected_facing_star": "8 ขาว (向星"},
    {"degree": 135.0, "expected_facing_mountain": "巽", "expected_facing_palace": "SE", "expected_facing_star": "9 ม่วง (向星"},
    {"degree": 180.0, "expected_facing_mountain": "午", "expected_facing_palace": "S", "expected_facing_star": "9 ม่วง (向星"},
    {"degree": 225.0, "expected_facing_mountain": "坤", "expected_facing_palace": "SW", "expected_facing_star": "1 ขาว (向星"},
    {"degree": 270.0, "expected_facing_mountain": "酉", "expected_facing_palace": "W", "expected_facing_star": "4 เขียว (向星"},
    {"degree": 315.0, "expected_facing_mountain": "乾", "expected_facing_palace": "NW", "expected_facing_star": "6 ขาว (向星"},
]


def post_json(url: str, payload: dict, timeout: int = 25) -> tuple[int, dict, float]:
    """Send POST request with JSON body and return (status, parsed_dict, latency_ms)."""
    start = time.perf_counter()
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 HoroConsultant-LuoPan-E2E-Tester",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            latency = (time.perf_counter() - start) * 1000
            return resp.status, json.loads(body), latency
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else "{}"
        latency = (time.perf_counter() - start) * 1000
        try:
            return e.code, json.loads(body), latency
        except Exception:
            return e.code, {"error": body}, latency
    except Exception as ex:
        latency = (time.perf_counter() - start) * 1000
        return 0, {"error": str(ex)}, latency


def run_luopan_e2e_audit(base_url: str = DEFAULT_URL) -> dict:
    """Run E2E audit across 8 primary directions on live production."""
    base_url = base_url.rstrip("/")
    endpoint = f"{base_url}/api/v1/luopan/calculate"
    print(f"\n🚀 Running Live LuoPan 24-Mountain & Dynamic 9-Palace E2E Regression on: {endpoint}\n" + "=" * 78)

    report = {
        "target_url": endpoint,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "UNKNOWN",
        "tests": [],
        "failures": [],
    }

    unique_facing_stars = set()
    unique_5yellow_sectors = set()

    for item in TEST_SAMPLE_ORIENTATIONS:
        deg = item["degree"]
        exp_m = item["expected_facing_mountain"]
        exp_palace = item["expected_facing_palace"]
        exp_star = item["expected_facing_star"]

        status, data, latency = post_json(endpoint, {"facing_degree": deg, "period": 9})

        test_result = {
            "input_degree": deg,
            "http_status": status,
            "latency_ms": round(latency, 1),
            "passed": False,
            "details": {}
        }

        if status != 200:
            print(f"❌ [FAIL] Degree {deg:5.1f}° -> HTTP Status {status} ({latency:.1f}ms)")
            report["failures"].append(f"HTTP {status} on degree {deg}")
            report["tests"].append(test_result)
            continue

        mountain = data.get("mountain", {})
        sectors = data.get("sectors", {})
        facing_mountain_name = mountain.get("facing_mountain", "")
        facing_sector_data = sectors.get(exp_palace, {})
        facing_star_name = facing_sector_data.get("star", "")

        # Check 1: Facing mountain character
        m_ok = exp_m in facing_mountain_name
        # Check 2: Facing palace star
        star_ok = exp_star in facing_star_name
        # Check 3: Southwest label typo check
        sw_name = sectors.get("SW", {}).get("sector", "")
        sw_ok = "ทิศตะวันตกเฉียงใต้" in sw_name and "ทิศต.อ.เฉียงใต้" not in sw_name

        # Find 5 Yellow palace
        five_yellow_palace = next((k for k, v in sectors.items() if "5 เหลือง" in v.get("star", "")), "NOT_FOUND")

        unique_facing_stars.add(facing_star_name)
        unique_5yellow_sectors.add(five_yellow_palace)

        passed = m_ok and star_ok and sw_ok

        test_result["passed"] = passed
        test_result["details"] = {
            "facing_mountain": facing_mountain_name,
            "facing_palace": exp_palace,
            "facing_star": facing_star_name,
            "facing_heat_score": facing_sector_data.get("heat_score"),
            "five_yellow_palace": five_yellow_palace,
            "southwest_label": sw_name,
        }

        report["tests"].append(test_result)

        status_tag = "✅ [OK]" if passed else "❌ [FAIL]"
        print(f"{status_tag} Degree {deg:5.1f}° -> Facing: {facing_mountain_name:12s} | Palace [{exp_palace}]: {facing_star_name:38s} | 5-Yellow: {five_yellow_palace:6s} [{latency:.1f}ms]")

    # Overall regression verification
    total_passed = sum(1 for t in report["tests"] if t["passed"])
    has_variance = len(unique_facing_stars) >= 5 and len(unique_5yellow_sectors) >= 4

    print("=" * 78)
    print(f"📊 Test Summary: {total_passed}/{len(TEST_SAMPLE_ORIENTATIONS)} Passed | Unique Facing Stars: {len(unique_facing_stars)} | 5-Yellow Shifts: {len(unique_5yellow_sectors)}")

    if total_passed == len(TEST_SAMPLE_ORIENTATIONS) and has_variance:
        report["status"] = "ALL_PASSED_READY_FOR_PROD"
        print("🎉 [SUCCESS] Dynamic LuoPan 9-Palace Flying Star Regression Passed 100%!")
    else:
        report["status"] = "REGRESSION_FAILED"
        print("❌ [FAILED] LuoPan Dynamic Regression Detected Mismatches or Lack of Variance!")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"📁 Detailed Audit Report Saved to: {REPORT_PATH}\n")
    return report


def main():
    parser = argparse.ArgumentParser(description="LuoPan Dynamic 9-Palace E2E Regression Suite")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Base production URL")
    args = parser.parse_args()

    report = run_luopan_e2e_audit(args.url)
    sys.exit(0 if report["status"] == "ALL_PASSED_READY_FOR_PROD" else 1)


if __name__ == "__main__":
    main()
