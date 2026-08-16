"""
scripts/audit_all_astrology_disciplines.py
===========================================
Deep E2E Snapshot Auditor for All Metaphysical & Astrological Disciplines.
Automates browser interaction for all disciplines, captures high-res snapshots,
and verifies canonical doctrine completeness (Toolbars, Matrices, SVG Diagrams, In-Depth Cards).
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

SCREENSHOT_DIR = Path("project/tests/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

DISCIPLINES = [
    {
        "id": "DISC-01",
        "name": "四柱 BaZi (Four Pillars)",
        "selector": "button:has-text('四柱 Four Pillars')",
        "doctrine": "Classical BaZi (滴天髓 / 淵海子平)",
        "expected_elements": ["Year", "Month", "Day", "Hour", "True Solar Time", "Pillars"],
        "svg_expected": True
    },
    {
        "id": "DISC-02",
        "name": "紫微斗數 (Zi Wei Dou Shu)",
        "selector": "button:has-text('紫微斗數')",
        "doctrine": "Zi Wei Dou Shu (紫微斗數全書)",
        "expected_elements": ["命宮", "身宮", "五行局", "紫微星位", "四化", "ผัง 12 ภพ"],
        "svg_expected": True
    },
    {
        "id": "DISC-03",
        "name": "奇門遁甲 (Qi Men Dun Jia)",
        "selector": "button:has-text('奇門遁甲')",
        "doctrine": "Qi Men Dun Jia (煙波釣叟歌 / 御定奇門寶鑑)",
        "expected_elements": ["節氣", "陰陽遁", "局", "宮位", "九星", "八門", "八神"],
        "svg_expected": True
    },
    {
        "id": "DISC-04",
        "name": "大六壬 (Da Liu Ren)",
        "selector": "button:has-text('大六壬')",
        "doctrine": "Da Liu Ren (六壬大全 / 六壬指南)",
        "expected_elements": ["日干支", "月將", "占時", "三傳", "四課"],
        "svg_expected": True
    },
    {
        "id": "DISC-05",
        "name": "易經六爻 (I Ching & Liu Yao)",
        "selector": "button:has-text('易經六爻')",
        "doctrine": "I Ching & Wen Wang Ba Gua (周易 / 卜筮正宗 / 增刪卜易)",
        "expected_elements": ["本卦", "變卦", "爻", "六神"],
        "svg_expected": True
    },
    {
        "id": "DISC-06",
        "name": "玄空風水 (Xuan Kong Flying Stars)",
        "selector": "button:has-text('玄空風水')",
        "doctrine": "Xuan Kong Flying Stars (沈氏玄空學 / 青囊經)",
        "expected_elements": ["九運", "向首", "坐山", "山", "向", "運星"],
        "svg_expected": True
    },
    {
        "id": "DISC-07",
        "name": "擇吉คำนวณฤกษ์ (Ze Ji Auspicious Timing)",
        "selector": "button:has-text('擇吉คำนวณฤกษ์')",
        "doctrine": "Ze Ji Date Selection (協紀辨方書 / 玉匣記)",
        "expected_elements": ["建除十二神", "ระดับความมงคล", "ความเหมาะสมประจำกิจกรรม"],
        "svg_expected": True
    },
    {
        "id": "DISC-08",
        "name": "โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish)",
        "selector": "button:has-text('โหราศาสตร์ไทย')",
        "doctrine": "Thai Suriyayart & Parashara Jyotish (คัมภีร์สุริยยาตร์ / มหาทักษา / พฤหัสชาดก)",
        "expected_elements": ["ลัคนาสุริยยาตร์", "ดาวศรี", "ดาวกาลกิณี", "มหาทักษา", "นักษัตร 27 ดารา", "วิมโชตตรีทศา"],
        "svg_expected": True
    },
    {
        "id": "DISC-09",
        "name": "โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian)",
        "selector": "button:has-text('โหราศาสตร์สากล')",
        "doctrine": "Western Tropical & Hamburg Uranian (Tetrabiblos / Alfred Witte Rulebook)",
        "expected_elements": ["Tropical Planets", "Uranian TNPs", "จุดอิทธิพลสะท้อนศูนย์ลิขิต"],
        "svg_expected": True
    },
    {
        "id": "DISC-10",
        "name": "สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean",
        "selector": "button:has-text('สัตตเลข 7 ฐาน')",
        "doctrine": "Thai Satta-Lek 7-Base (คัมภีร์สัตตเลข 7 ฐาน 4 แถว) & Chaldean Gematria",
        "expected_elements": ["ผัง 7 ฐาน 4 แถว", "อัตตา", "มัชฌิมา", "ฐาน ๔", "Chaldean", "ถอดราก"],
        "svg_expected": True
    }
]


async def run_audit(target_url: str):
    print("======================================================================")
    print("  🔮 COMPREHENSIVE ASTROLOGY DISCIPLINE E2E SNAPSHOT AUDITOR")
    print(f"  Target URL: {target_url}")
    print(f"  Total Disciplines Audited: {len(DISCIPLINES)}")
    print("======================================================================")

    audit_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 950})

        print("\n[INIT] Loading Dashboard...")
        await page.goto(target_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        for d in DISCIPLINES:
            d_id = d["id"]
            d_name = d["name"]
            sel = d["selector"]
            print(f"\n[{d_id}] Auditing: {d_name}...")
            
            try:
                btn = page.locator(sel)
                if not await btn.count():
                    raise ValueError(f"Button selector not found: {sel}")
                
                await btn.click()
                await page.wait_for_timeout(2000)

                # Locate result card
                card_locator = page.locator("#branch-result-card")
                is_visible = await card_locator.is_visible()
                body_text = await card_locator.inner_text() if is_visible else ""

                # Check SVG diagram inside card
                has_svg = await card_locator.locator("svg").count() > 0 or await page.locator("#svg-chart-card svg").count() > 0

                # Capture clean screenshot
                shot_filename = f"discipline_{d_id.lower().replace('-','_')}.png"
                shot_path = SCREENSHOT_DIR / shot_filename
                
                if is_visible:
                    await card_locator.scroll_into_view_if_needed()
                    await page.wait_for_timeout(400)
                    await card_locator.screenshot(path=str(shot_path))
                else:
                    await page.screenshot(path=str(shot_path), full_page=True)

                # Check expected doctrinal elements
                element_checks = []
                for exp in d["expected_elements"]:
                    found = exp.lower() in body_text.lower()
                    element_checks.append({"item": exp, "found": found})

                all_elements_present = all(c["found"] for c in element_checks)
                svg_status_ok = has_svg if d["svg_expected"] else True
                passed = is_visible and all_elements_present and svg_status_ok

                found_cnt = sum(1 for c in element_checks if c['found'])
                total_cnt = len(element_checks)

                print(f"  • Result Card Visible      : {'✅ YES' if is_visible else '❌ NO'}")
                print(f"  • SVG Vector Rendered      : {'✅ YES' if has_svg else '❌ MISSING'}")
                print(f"  • Doctrinal Elements Match : {found_cnt}/{total_cnt} {'✅' if all_elements_present else '⚠️'}")
                print(f"  • Snapshot Captured        : {shot_filename}")
                print(f"  • Status                   : {'✅ PASSED (100% COMPLETE)' if passed else '⚠️ NEEDS ATTENTION'}")

                audit_results.append({
                    "id": d_id,
                    "name": d_name,
                    "doctrine": d["doctrine"],
                    "passed": passed,
                    "is_visible": is_visible,
                    "has_svg": has_svg,
                    "svg_expected": d["svg_expected"],
                    "element_checks": element_checks,
                    "elements_matched": f"{found_cnt}/{total_cnt}",
                    "snapshot": shot_filename
                })

            except Exception as e:
                print(f"  ❌ Error auditing {d_name}: {e}")
                audit_results.append({
                    "id": d_id,
                    "name": d_name,
                    "doctrine": d["doctrine"],
                    "passed": False,
                    "error": str(e)
                })

        await browser.close()

    # Save detailed JSON report
    report_file = Path("project/tests/discipline_audit_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)

    total = len(audit_results)
    passed_cnt = sum(1 for r in audit_results if r.get("passed"))
    
    print("\n======================================================================")
    print("  📊 ASTROLOGY DISCIPLINE AUDIT SUMMARY")
    print("======================================================================")
    print(f"  • Total Disciplines Audited : {total}")
    print(f"  • Fully Complete & Passed   : {passed_cnt}/{total} ✅ ({passed_cnt/total*100:.1f}%)")
    print(f"  • Report JSON Path          : {report_file}")
    print(f"  • Screenshots Directory     : {SCREENSHOT_DIR.resolve()}")
    print("======================================================================")
    return passed_cnt == total


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else f"file://{Path('project/static/index.html').resolve()}"
    success = asyncio.run(run_audit(url))
    sys.exit(0 if success else 1)
