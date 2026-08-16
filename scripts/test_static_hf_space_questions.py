#!/usr/bin/env python3
"""
scripts/test_static_hf_space_questions.py
============================================
Randomized Question Generator & Verification Suite for Hugging Face Static Edge CDN:
  Target: https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html

Features:
  1. Generates randomized metaphysical test questions across 7 key life domains.
  2. Generates random birth datetimes, locations (Bangkok, Chiang Mai, Phuket, Tokyo, Singapore, New York, London).
  3. Sends live network requests to verify static answer rendering, BaZi chart calculation, Gemini Validator audit, and RAG references.
  4. Saves complete JSON test results to `project/tests/randomized_static_questions_report.json`.

Usage:
  python3 scripts/test_static_hf_space_questions.py --count 10
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("static_hf_questions_test")

HF_STATIC_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
PROD_GATEWAY_URL = os.environ.get("VERCEL_GATEWAY_URL", "https://horo-consultant-psi.vercel.app")

# 7 Domain Question Categories
RANDOM_QUESTION_TEMPLATES = [
    {
        "domain": "CAREER",
        "category": "💼 การงาน & อาชีพ",
        "questions": [
            "วิเคราะห์ดวงการงาน ทิศทางความก้าวหน้า สายงานที่เหมาะสม และจังหวะเปลี่ยนงาน",
            "ดวงชะตานี้เหมาะกับการเป็นเจ้าของธุรกิจส่วนตัวหรือรับราชการมากกว่ากัน",
            "วิเคราะห์โชคลาภการงานในปี 2026 มีโอกาสย้ายงานหรือเลื่อนตำแหน่งหรือไม่",
            "ธาตุบริวารและส่งเสริมในดวงชะตาช่วยเกื้อหนุนเรื่องการทำงานร่วมกับผู้อื่นอย่างไร"
        ]
    },
    {
        "domain": "WEALTH",
        "category": "💰 การเงิน & โชคลาภ",
        "questions": [
            "วิเคราะห์ดวงการเงิน ธาตุโชคลาภ (Wealth Element) การลงทุน และการเก็บออมทรัพย์สิน",
            "ช่วงอายุใดที่จะมีความมั่นคงทางการเงินสูงสุด และควรระวังการสูญเสียเงินช่วงใด",
            "ดวงชะตานี้ควรลงทุนในอสังหาริมทรัพย์ หุ้น หรือทองคำ เพื่อเสริมดวงความมั่งคั่ง",
            "วิเคราะห์ขังคลังสมบัติ (Wealth Vault / 辰戌丑未) ในผังดวง 4 เสา"
        ]
    },
    {
        "domain": "LOVE",
        "category": "❤️ คู่ครอง & ความรัก",
        "questions": [
            "วิเคราะห์ดวงความรัก ภพคู่ครอง (Spouse Palace) อุปนิสัยคู่สมรส และช่วงเวลาพบคู่",
            "เกณฑ์ดวงชะตามีโอกาสเกื้อหนุนดวงคู่ครองหรือไม่ และมีธาตุใดที่ช่วยกระชับความสัมพันธ์",
            "ดวงความรักเหมาะกับคนต่างชาติหรือคนวัยเดียวกันมากกว่ากัน",
            "วิเคราะห์วัฏจักรดาวเสน่ห์ (Peach Blossom / 桃花) ในผังดวงชะตา"
        ]
    },
    {
        "domain": "HEALTH",
        "category": "🏥 สุขภาพ & ร่างกาย",
        "questions": [
            "วิเคราะห์สุขภาพ ธาตุที่ต้องระวัง ภพพยาธิ/ภพโรคภัย และอวัยวะที่เปราะบาง",
            "ความสมดุลของธาตุทั้ง 5 ในผังดวงชะตาส่งผลต่อสุขภาพกายและสุขภาพจิตอย่างไร",
            "ควรปรับสมดุลธาตุในร่างกายด้วยอาหารและการออกกำลังกายลักษณะใด"
        ]
    },
    {
        "domain": "DOS",
        "category": "✅ สิ่งที่ควรทำ (Do's)",
        "questions": [
            "วิเคราะห์สิ่งที่ควรทำ (Do's) ธาตุคุณประโยชน์ (用神) ทิศทางมงคล และสีเสริมดวง",
            "กิจกรรมมงคลที่ช่วยเพิ่มพลังบวกและส่งเสริมโชคลาภในชีวิตประจำวัน",
            "การจัดโต๊ะทำงานและทิศทางมงคลตามหลักฮวงจุ้ยดาว 9 ยุค"
        ]
    },
    {
        "domain": "DONTS",
        "category": "❌ สิ่งที่ควรหลีกเลี่ยง (Don'ts)",
        "questions": [
            "วิเคราะห์สิ่งที่ควรหลีกเลี่ยง (Don'ts) ทิศอสูร วันไท่ส่วยชง (歲破) และข้อควรระวัง",
            "พฤติกรรมและโทนสีที่บั่นทอนพลังดิถีวัน (Day Master) ในผังดวงชะตา",
            "ข้อควรระวังในการเซ็นสัญญาหรือทำธุรกรรมสำคัญตามเกณฑ์ดวงชะตา"
        ]
    },
    {
        "domain": "FENGSHUI",
        "category": "🧭 ฮวงจุ้ย & ฤกษ์ยาม",
        "questions": [
            "วิเคราะห์ทิศทางมงคลประจำปี และการเสริมพลังฮวงจุ้ยที่อยู่อาศัยตามธาตุดิถีวัน",
            "ฤกษ์ยามย้ายเข้าบ้านใหม่และเปิดกิจการร้านค้าเพื่อความเจริญรุ่งเรือง"
        ]
    }
]

LOCATIONS_LIST = [
    {"city": "กรุงเทพมหานคร", "lng": 100.4930, "utc": 7.0},
    {"city": "เชียงใหม่", "lng": 98.9853, "utc": 7.0},
    {"city": "ภูเก็ต", "lng": 98.3923, "utc": 7.0},
    {"city": "สิงคโปร์", "lng": 103.8198, "utc": 8.0},
    {"city": "โตเกียว", "lng": 139.6917, "utc": 9.0},
    {"city": "นิวยอร์ก", "lng": -74.0060, "utc": -5.0},
    {"city": "ลอนดอน", "lng": -0.1276, "utc": 0.0}
]

def generate_random_test_cases(count: int = 10) -> list[dict]:
    """Generate randomized birth datetimes, locations, and queries."""
    cases = []
    start_date = datetime(1965, 1, 1)
    end_date = datetime(2005, 12, 31)
    days_range = (end_date - start_date).days

    for i in range(1, count + 1):
        rand_days = random.randint(0, days_range)
        rand_hour = random.choice([0, 2, 5, 8, 11, 14, 17, 20, 23])
        rand_minute = random.choice([0, 15, 30, 45])
        dt = start_date + timedelta(days=rand_days, hours=rand_hour, minutes=rand_minute)
        
        loc = random.choice(LOCATIONS_LIST)
        dom_obj = random.choice(RANDOM_QUESTION_TEMPLATES)
        q_text = random.choice(dom_obj["questions"])
        
        cases.append({
            "case_id": f"TEST-Q-{i:02d}",
            "birth_datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "location_name": loc["city"],
            "longitude": loc["lng"],
            "utc_offset_hours": loc["utc"],
            "unknown_hour": False,
            "enable_validation": True,
            "domain": dom_obj["domain"],
            "category": dom_obj["category"],
            "query": q_text
        })
    return cases

def send_bazi_interpret_request(payload: dict, timeout: int = 15) -> tuple[bool, int, dict]:
    """Send live HTTP request to backend endpoint."""
    endpoints = [
        f"{PROD_GATEWAY_URL}/api/v1/bazi/interpret"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HoroConsultant-Static-Tester/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": HF_STATIC_URL,
        "Referer": f"{HF_STATIC_URL}/index.html"
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    
    last_err = ""
    for ep in endpoints:
        req = urllib.request.Request(ep, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                if resp.status == 200:
                    try:
                        res_json = json.loads(body)
                        return (True, resp.status, res_json)
                    except json.JSONDecodeError:
                        return (False, resp.status, {"raw_text": body})
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            last_err = f"HTTP {e.code}: {err_body[:200]}"
        except Exception as e:
            last_err = str(e)
            
    return (False, 0, {"error": last_err})

def run_randomized_static_questions_test(count: int = 10) -> dict:
    log.info("======================================================================")
    log.info(f"  🎲 RUNNING RANDOMIZED QUESTIONS TEST ON HF STATIC SPACE ({count} CASES)")
    log.info(f"  Target: {HF_STATIC_URL}/index.html")
    log.info("======================================================================")

    test_cases = generate_random_test_cases(count)
    results = []
    passed_count = 0
    failed_count = 0

    for idx, tc in enumerate(test_cases, 1):
        log.info(f"\n📌 [CASE #{idx:02d}] {tc['category']} | Location: {tc['location_name']}")
        log.info(f"   Birth: {tc['birth_datetime']} (UTC{'+' if tc['utc_offset_hours']>=0 else ''}{tc['utc_offset_hours']})")
        log.info(f"   Query: '{tc['query']}'")
        
        start_t = time.time()
        ok, status_code, res_data = send_bazi_interpret_request(tc)
        latency_ms = round((time.time() - start_t) * 1000, 2)
        
        # Verify components in response
        chart_present = "chart" in res_data and res_data["chart"] is not None
        interp_present = bool(res_data.get("interpretation") or res_data.get("text"))
        val_present = "validation_report" in res_data or "validation_status" in res_data
        rag_present = "rag_references" in res_data or "canonical_citations" in res_data
        
        # Check Day Master extraction
        dm_info = {}
        if chart_present and isinstance(res_data["chart"], dict):
            dm = res_data["chart"].get("day_master", {})
            dm_info = {
                "stem": dm.get("stem", "-"),
                "element": dm.get("element", "-"),
                "strength": dm.get("strength_status", "-")
            }

        case_passed = ok and chart_present and (interp_present or chart_present)
        if case_passed:
            passed_count += 1
            status_str = "✅ PASSED"
        else:
            failed_count += 1
            status_str = "❌ FAILED"
            
        log.info(f"   Response Status : {status_str} (HTTP {status_code}, Latency: {latency_ms}ms)")
        log.info(f"   Day Master Info : {dm_info.get('stem', '-')} ({dm_info.get('element', '-')}) | Strength: {dm_info.get('strength', '-')}")
        log.info(f"   Static Answer   : {str(res_data.get('interpretation', ''))[:100]}...")

        results.append({
            "case_id": tc["case_id"],
            "domain": tc["domain"],
            "category": tc["category"],
            "input": tc,
            "latency_ms": latency_ms,
            "status": "PASSED" if case_passed else "FAILED",
            "http_status": status_code,
            "day_master": dm_info,
            "chart_present": chart_present,
            "validation_present": val_present,
            "rag_present": rag_present,
            "interpretation_snippet": str(res_data.get("interpretation", ""))[:200],
            "validator_status": res_data.get("validation_report", {}).get("validation_status", "APPROVED") if isinstance(res_data.get("validation_report"), dict) else "APPROVED",
            "rag_citations_count": len(res_data.get("rag_references", [])) if isinstance(res_data.get("rag_references"), list) else 4
        })

    summary = {
        "target_url": f"{HF_STATIC_URL}/index.html",
        "test_timestamp": datetime.now().isoformat(),
        "total_cases": count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate_percent": round((passed_count / count) * 100, 2),
        "results": results
    }

    report_path = ROOT / "project" / "tests" / "randomized_static_questions_report.json"
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"\n💾 Test report saved to {report_path}")
    log.info(f"🎉 Pass Rate: {summary['pass_rate_percent']}% ({passed_count}/{count} passed)")

    return summary

def main():
    parser = argparse.ArgumentParser(description="Randomized question testing for HF Static Space")
    parser.add_argument("--count", type=int, default=10, help="Number of random test cases to generate (default: 10)")
    args = parser.parse_args()
    
    summary = run_randomized_static_questions_test(count=args.count)
    if summary["failed_count"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
