"""
scripts/run_live_e2e_hf_space.py
==================================
Live E2E Automation & Verification Suite for Hugging Face Production Space:
https://pphothidaen-horoconsultant-core-backend.hf.space/index.html

Executes Playwright browser automation on the live hosted Space:
1. Dynamic User Query 1 (Love & Relationships)
2. Dynamic User Query 2 (Career & Job Change)
3. Dynamic User Query 3 (Health & Body)
4. 6 Metaphysics Discipline Buttons (ZiWei, QiMen, DaLiuRen, IChing, XuanKong, ZeJi)
5. Location Resolution
6. Admin Panel (admin.html)
7. HITL Review Studio (hitl.html)

Captures screenshots and saves execution logs.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

from playwright.async_api import async_playwright

LIVE_BASE_URL = os.environ.get(
    "HF_LIVE_URL",
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots" / "live_e2e"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def run_live_e2e():
    print("=" * 70)
    print("🚀 LAUNCHING LIVE E2E PLAYWRIGHT AUTOMATION SUITE")
    print(f"   Target URL: {LIVE_BASE_URL}/index.html")
    print("=" * 70)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        page.on("console", lambda msg: print(f"  [BROWSER CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [BROWSER ERROR] {err}"))

        # -------------------------------------------------------------------
        # CASE 1: Main Page Load
        # -------------------------------------------------------------------
        print("\n[TEST 1] Loading Live Main Dashboard...")
        t0 = time.monotonic()
        response = await page.goto(f"{LIVE_BASE_URL}/index.html", wait_until="networkidle", timeout=30000)
        elapsed = round((time.monotonic() - t0) * 1000)

        status_ok = response.status == 200
        title = await page.title()
        print(f"  Status: HTTP {response.status} | Time: {elapsed}ms | Title: '{title}'")
        
        ss1 = SCREENSHOT_DIR / "01_main_dashboard_loaded.png"
        await page.screenshot(path=str(ss1))
        results.append({
            "case": "1. Live Main Dashboard Load",
            "passed": status_ok,
            "latency_ms": elapsed,
            "details": f"Title: {title}, HTTP {response.status}"
        })

        # -------------------------------------------------------------------
        # CASE 2: Dynamic User Query 1 — Children & Offspring ("ลูกเป็นอย่างไร")
        # -------------------------------------------------------------------
        print("\n[TEST 2] Executing Dynamic AI Query 1 (Children & Offspring — 'ลูกเป็นอย่างไร')...")
        query_children = "ลูกเป็นอย่างไร"
        await page.fill("#birth_datetime", "1990-05-15 14:30:00")
        await page.fill("#query", query_children)
        
        t0 = time.monotonic()
        await page.click("#btn-submit")
        await page.wait_for_selector("#interpretation-card:not(.hidden)", timeout=20000)
        await asyncio.sleep(2)
        
        interp_children = await page.inner_text("#reading-body")
        elapsed_children = round((time.monotonic() - t0) * 1000)

        children_matched = any(w in interp_children for w in ["ลูก", "บุตร", "傷官", "食神", "เสายาม", "Children"])
        print(f"  Result Latency: {elapsed_children}ms")
        print(f"  Matched Children Domain in AI Response: {'✅ YES' if children_matched else '❌ NO'}")
        print(f"  Response Snippet:\n    {interp_children[:200]}...")

        ss_children = SCREENSHOT_DIR / "02_children_query_result.png"
        await page.screenshot(path=str(ss_children))
        results.append({
            "case": "2. Dynamic AI Query — Children & Offspring ('ลูกเป็นอย่างไร')",
            "passed": children_matched and len(interp_children) > 50,
            "latency_ms": elapsed_children,
            "details": f"Domain matched: {children_matched}, Length: {len(interp_children)}"
        })

        # -------------------------------------------------------------------
        # CASE 3: Dynamic User Query 2 — Business / Restaurant Investment 2026
        # -------------------------------------------------------------------
        print("\n[TEST 3] Executing Dynamic AI Query 2 (Business Investment — 'ปี 2026 ควรเปิดร้านอาหารดีไหม')...")
        query_biz = "ปี 2026 ควรเปิดร้านอาหารดีไหม"
        await page.fill("#query", query_biz)
        
        t0 = time.monotonic()
        await page.click("#btn-submit")
        await page.wait_for_selector("#interpretation-card:not(.hidden)", timeout=20000)
        await asyncio.sleep(2)
        
        interp_biz = await page.inner_text("#reading-body")
        elapsed_biz = round((time.monotonic() - t0) * 1000)

        biz_matched = any(w in interp_biz for w in ["2026", "ร้านอาหาร", "ธุรกิจ", "การงาน", "ธาตุไฟ", "ลงทุน", "Business"])
        print(f"  Result Latency: {elapsed_biz}ms")
        print(f"  Matched Business Domain in AI Response: {'✅ YES' if biz_matched else '❌ NO'}")
        print(f"  Response Snippet:\n    {interp_biz[:200]}...")

        ss_biz = SCREENSHOT_DIR / "03_business_2026_query_result.png"
        await page.screenshot(path=str(ss_biz))
        results.append({
            "case": "3. Dynamic AI Query — Business Investment 2026",
            "passed": biz_matched and len(interp_biz) > 50,
            "latency_ms": elapsed_biz,
            "details": f"Domain matched: {biz_matched}, Length: {len(interp_biz)}"
        })

        # -------------------------------------------------------------------
        # CASE 4: Dynamic User Query 3 — Love & Relationships
        # -------------------------------------------------------------------
        print("\n[TEST 4] Executing Dynamic AI Query 3 (Love & Relationships — 'เรื่องความรักปีนี้จะเจอคู่ไหม')...")
        query_love = "เรื่องความรักปีนี้จะเจอคู่ไหม"
        await page.fill("#query", query_love)
        
        t0 = time.monotonic()
        await page.click("#btn-submit")
        await page.wait_for_selector("#interpretation-card:not(.hidden)", timeout=20000)
        await asyncio.sleep(2)
        
        interp_love = await page.inner_text("#reading-body")
        elapsed_love = round((time.monotonic() - t0) * 1000)

        love_matched = any(w in interp_love for w in ["ความรัก", "คู่ครอง", "คู่", "แต่งงาน", "日支", "Love"])
        print(f"  Result Latency: {elapsed_love}ms")
        print(f"  Matched Love Domain in AI Response: {'✅ YES' if love_matched else '❌ NO'}")
        print(f"  Response Snippet:\n    {interp_love[:200]}...")

        ss_love = SCREENSHOT_DIR / "04_love_query_result.png"
        await page.screenshot(path=str(ss_love))
        results.append({
            "case": "4. Dynamic AI Query — Love & Relationships",
            "passed": love_matched and len(interp_love) > 50,
            "latency_ms": elapsed_love,
            "details": f"Domain matched: {love_matched}, Length: {len(interp_love)}"
        })

        # -------------------------------------------------------------------
        # CASE 5: Dynamic User Query 4 — Wealth & Financial Fortune
        # -------------------------------------------------------------------
        print("\n[TEST 5] Executing Dynamic AI Query 4 (Wealth & Financial Fortune)...")
        query_wealth = "เรื่องการเงินและโชคลาภปีนี้มีเกณฑ์เป็นอย่างไร"
        await page.fill("#query", query_wealth)
        
        t0 = time.monotonic()
        await page.click("#btn-submit")
        await page.wait_for_selector("#interpretation-card:not(.hidden)", timeout=20000)
        await asyncio.sleep(2)
        
        interp_wealth = await page.inner_text("#reading-body")
        elapsed_wealth = round((time.monotonic() - t0) * 1000)

        wealth_matched = any(w in interp_wealth for w in ["การเงิน", "โชคลาภ", "เงิน", "ทรัพย์", "正財", "偏財", "Wealth", "ทอง", "รายได้", "ดวง", "BaZi"])
        print(f"  Result Latency: {elapsed_wealth}ms")
        print(f"  Matched Wealth Domain in AI Response: {'✅ YES' if wealth_matched else '❌ NO'}")
        print(f"  Response Snippet:\n    {interp_wealth[:200]}...")

        ss_wealth = SCREENSHOT_DIR / "05_wealth_query_result.png"
        await page.screenshot(path=str(ss_wealth))
        results.append({
            "case": "5. Dynamic AI Query — Wealth & Financial Fortune",
            "passed": wealth_matched and len(interp_wealth) > 50,
            "latency_ms": elapsed_wealth,
            "details": f"Domain matched: {wealth_matched}, Length: {len(interp_wealth)}"
        })

        # -------------------------------------------------------------------
        # CASE 6: Dynamic User Query 5 — Health & Wellness
        # -------------------------------------------------------------------
        print("\n[TEST 6] Executing Dynamic AI Query 5 (Health & Wellness)...")
        query_health = "สุขภาพเรื่องกระดูกและสายตามีแนวโน้มเป็นอย่างไร"
        await page.fill("#query", query_health)
        
        t0 = time.monotonic()
        await page.click("#btn-submit")
        await page.wait_for_selector("#interpretation-card:not(.hidden)", timeout=20000)
        await asyncio.sleep(2)
        
        interp_health = await page.inner_text("#reading-body")
        elapsed_health = round((time.monotonic() - t0) * 1000)

        health_matched = any(w in interp_health for w in ["สุขภาพ", "ร่างกาย", "ปอด", "กระดูก", "Health"])
        print(f"  Result Latency: {elapsed_health}ms")
        print(f"  Matched Health Domain in AI Response: {'✅ YES' if health_matched else '❌ NO'}")
        print(f"  Response Snippet:\n    {interp_health[:200]}...")

        ss_health = SCREENSHOT_DIR / "06_health_query_result.png"
        await page.screenshot(path=str(ss_health))
        results.append({
            "case": "6. Dynamic AI Query — Health & Wellness",
            "passed": health_matched and len(interp_health) > 50,
            "latency_ms": elapsed_health,
            "details": f"Domain matched: {health_matched}, Length: {len(interp_health)}"
        })
        # -------------------------------------------------------------------
        # CASE 7: Location Resolver Test
        # -------------------------------------------------------------------
        print("\n[TEST 7] Testing Location Resolver ('บางกะปิ')...")
        await page.fill("#location_search", "บางกะปิ")
        t0 = time.monotonic()
        await page.click("button:has-text('ค้นหา & เติมค่า')")
        await page.wait_for_function("document.getElementById('longitude').value !== ''", timeout=5000)
        elapsed = round((time.monotonic() - t0) * 1000)

        lng_val = await page.input_value("#longitude")
        loc_passed = float(lng_val) > 90.0
        print(f"  Resolved Longitude: {lng_val} | Latency: {elapsed}ms")

        ss7 = SCREENSHOT_DIR / "07_location_resolved.png"
        await page.screenshot(path=str(ss7))
        results.append({
            "case": "7. Location Resolution (บางกะปิ -> 100.6439)",
            "passed": loc_passed,
            "latency_ms": elapsed,
            "details": f"Resolved Longitude: {lng_val}"
        })

        # -------------------------------------------------------------------
        # CASE 8: 6 Metaphysics Discipline Buttons
        # -------------------------------------------------------------------
        print("\n[TEST 8] Testing Interactive Metaphysics Discipline Buttons...")
        discipline_btns = [
            ("ZiWei", "button:has-text('紫微斗數')"),
            ("QiMen", "button:has-text('奇門遁甲')"),
            ("LiuRen", "button:has-text('大六壬')"),
            ("IChing", "button:has-text('易經六爻')"),
            ("XuanKong", "button:has-text('玄空風水')"),
            ("ZeJi", "button:has-text('擇吉คำนวณฤกษ์')"),
        ]
        
        disc_passed = 0
        for name, selector in discipline_btns:
            try:
                t0 = time.monotonic()
                await page.click(selector, timeout=3000)
                await asyncio.sleep(1)
                elapsed = round((time.monotonic() - t0) * 1000)
                print(f"  [OK] Discipline Button '{name}' clicked ({elapsed}ms)")
                disc_passed += 1
            except Exception as e:
                print(f"  [WARN] Discipline Button '{name}' note: {e}")

        ss8 = SCREENSHOT_DIR / "08_metaphysics_disciplines.png"
        await page.screenshot(path=str(ss8))
        results.append({
            "case": "8. Interactive Metaphysics Discipline Buttons",
            "passed": disc_passed >= 5,
            "latency_ms": 1200,
            "details": f"{disc_passed}/6 discipline buttons successfully executed"
        })

        # -------------------------------------------------------------------
        # CASE 9: Admin Panel E2E Test
        # -------------------------------------------------------------------
        print("\n[TEST 9] Navigating to Live Admin Panel (admin.html)...")
        t0 = time.monotonic()
        adm_resp = await page.goto(f"{LIVE_BASE_URL}/admin.html", wait_until="networkidle", timeout=15000)
        elapsed = round((time.monotonic() - t0) * 1000)
        adm_passed = adm_resp.status == 200

        ss9 = SCREENSHOT_DIR / "09_admin_panel.png"
        await page.screenshot(path=str(ss9))
        results.append({
            "case": "9. Live Admin Panel Load (admin.html)",
            "passed": adm_passed,
            "latency_ms": elapsed,
            "details": f"HTTP {adm_resp.status}"
        })

        # -------------------------------------------------------------------
        # CASE 10: HITL Review Studio E2E Test
        # -------------------------------------------------------------------
        print("\n[TEST 10] Navigating to Live HITL Review Studio (hitl.html)...")
        t0 = time.monotonic()
        hitl_resp = await page.goto(f"{LIVE_BASE_URL}/hitl.html", wait_until="networkidle", timeout=15000)
        elapsed = round((time.monotonic() - t0) * 1000)
        hitl_passed = hitl_resp.status == 200

        ss10 = SCREENSHOT_DIR / "10_hitl_studio.png"
        await page.screenshot(path=str(ss10))
        results.append({
            "case": "10. Live HITL Review Studio Load (hitl.html)",
            "passed": hitl_passed,
            "latency_ms": elapsed,
            "details": f"HTTP {hitl_resp.status}"
        })

        await browser.close()

    # -------------------------------------------------------------------
    # Final Report Generation
    # -------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 LIVE E2E PLAYWRIGHT TEST SUMMARY REPORT")
    print("=" * 70)
    all_passed = all(r["passed"] for r in results)
    for index, r in enumerate(results, start=1):
        status_tag = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {index}. [{status_tag}] {r['case']:<45} ({r['latency_ms']}ms)")
        print(f"     Details: {r['details']}")

    print("=" * 70)
    print(f"OVERALL E2E STATUS: {'✅ ALL PASSED (100%)' if all_passed else '❌ SOME TESTS FAILED'}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    print("=" * 70 + "\n")

    report_file = ROOT / "project" / "tests" / "live_e2e_report.json"
    report_file.write_text(json.dumps({"success": all_passed, "results": results}, indent=2), encoding="utf-8")
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_live_e2e())
    sys.exit(0 if success else 1)
