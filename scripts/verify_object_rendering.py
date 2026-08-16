"""
scripts/verify_object_rendering.py
===================================
Automated Verification Suite for String & Object Rendering across all 16 Metaphysics Disciplines.
Strictly verifies that no '[object Object]', '[object Undefined]', 'NaN', or raw unformatted data leaks into the DOM.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

LOCAL_URL = f"file://{Path('project/static/index.html').resolve()}"
REPORT_FILE = Path("project/tests/object_rendering_verification_report.json")

DISCIPLINE_SELECTORS = [
    {"id": "01_bazi", "name": "BaZi Four Pillars", "selector": "button:has-text('四柱 Four Pillars')", "is_main": True},
    {"id": "02_ziwei", "name": "Zi Wei Dou Shu", "selector": "button:has-text('紫微斗數')", "is_main": False},
    {"id": "03_qimen", "name": "Qi Men Dun Jia", "selector": "button:has-text('奇門遁甲')", "is_main": False},
    {"id": "04_liuren", "name": "Da Liu Ren", "selector": "button:has-text('大六壬')", "is_main": False},
    {"id": "05_iching", "name": "I Ching Liu Yao", "selector": "button:has-text('易經六爻')", "is_main": False},
    {"id": "06_xuankong", "name": "Xuan Kong Flying Stars", "selector": "button:has-text('玄空風水')", "is_main": False},
    {"id": "07_zeji", "name": "Ze Ji Auspicious", "selector": "button:has-text('擇吉คำนวณฤกษ์')", "is_main": False},
    {"id": "08_thaivedic", "name": "Thai & Jyotish", "selector": "button:has-text('โหราศาสตร์ไทย')", "is_main": False},
    {"id": "09_western", "name": "Western & Uranian", "selector": "button:has-text('โหราศาสตร์สากล')", "is_main": False},
    {"id": "10_numerology", "name": "Satta-Lek & Chaldean", "selector": "button:has-text('สัตตเลข 7 ฐาน')", "is_main": False},
    {"id": "11_taiyi", "name": "Tai Yi Shen Shu", "selector": "button:has-text('太乙神數')", "is_main": False},
    {"id": "12_liuyao", "name": "Liu Yao Divination", "selector": "button:has-text('六爻預測')", "is_main": False},
    {"id": "13_meihua", "name": "Mei Hua Plum Blossom", "selector": "button:has-text('梅花易數')", "is_main": False},
    {"id": "14_sanhe", "name": "San He Feng Shui", "selector": "button:has-text('三合風水')", "is_main": False},
    {"id": "15_qizheng", "name": "Qi Zheng Si Yu", "selector": "button:has-text('七政四餘')", "is_main": False},
    {"id": "16_mianxiang", "name": "Mian Xiang Physiognomy", "selector": "button:has-text('麻衣神相')", "is_main": False},
]

VIEWPORTS = [
    {"name": "Desktop (1440x900)", "width": 1440, "height": 900},
    {"name": "Mobile (375x812)", "width": 375, "height": 812},
]


async def audit_discipline_rendering(page, disc):
    name = disc["name"]
    sel = disc["selector"]
    
    # Trigger calculation
    try:
        if disc["is_main"]:
            await page.click("#btn-submit")
        else:
            btn = await page.wait_for_selector(sel, timeout=3000)
            if btn:
                await btn.click()
        await page.wait_for_timeout(800)
    except Exception as e:
        return {
            "discipline": name,
            "passed": False,
            "error": f"Failed to click selector {sel}: {e}",
            "findings": []
        }

    # Evaluate rendered DOM content
    evaluation = await page.evaluate('''() => {
        const bodyText = document.body.innerText || '';
        const bodyHtml = document.body.innerHTML || '';
        
        const findings = [];
        
        if (bodyText.includes('[object Object]')) {
            findings.push('Found [object Object] in visible text');
        }
        if (bodyHtml.includes('[object Object]')) {
            findings.push('Found [object Object] in innerHTML markup');
        }
        if (bodyText.includes('[object Undefined]')) {
            findings.push('Found [object Undefined] in visible text');
        }
        if (bodyText.includes('NaN%') || bodyText.includes(': NaN')) {
            findings.push('Found NaN value in visible text');
        }
        if (bodyText.includes('undefined°') || bodyText.includes('undefined undefined')) {
            findings.push('Found undefined text fragment in visible text');
        }
        
        // Check 4 pillars specific fields
        const pillarsBox = document.querySelector('#pillars-grid');
        let pillarsValid = true;
        if (pillarsBox) {
            const pText = pillarsBox.innerText;
            if (pText.includes('[object Object]') || pText.includes('undefined')) {
                pillarsValid = false;
                findings.push('Pillars grid contains unformatted object/undefined');
            }
        }
        
        // Check Five elements balance percentages
        const elemBox = document.querySelector('#elements-bars');
        let fiveElementsValid = true;
        if (elemBox) {
            const eText = elemBox.innerText;
            if (eText.includes('NaN') || eText.includes('[object Object]')) {
                fiveElementsValid = false;
                findings.push('Five elements bar contains NaN or unformatted object');
            }
        }
        
        return {
            findings,
            passed: findings.length === 0,
            hasPillars: !!pillarsBox,
            hasFiveElements: !!elemBox
        };
    }''')

    return {
        "discipline": name,
        "passed": evaluation["passed"],
        "findings": evaluation["findings"],
        "hasPillars": evaluation["hasPillars"],
        "hasFiveElements": evaluation["hasFiveElements"]
    }


async def run_full_verification():
    print("======================================================================")
    print("  🔍 OBJECT RENDERING & [object Object] ELIMINATION VERIFIER")
    print(f"  Target: {LOCAL_URL}")
    print("======================================================================")

    all_results = []
    total_passed = 0
    total_audited = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for vp in VIEWPORTS:
            print(f"\n--- Testing Viewport: {vp['name']} ---")
            context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = await context.new_page()
            await page.goto(LOCAL_URL, wait_until="load")
            await page.wait_for_timeout(1000)

            # Test Bangkok preset first
            try:
                await page.click(".preset-buttons button:has-text('กรุงเทพฯ')")
                await page.wait_for_timeout(500)
            except Exception:
                pass

            for disc in DISCIPLINE_SELECTORS:
                total_audited += 1
                res = await audit_discipline_rendering(page, disc)
                res["viewport"] = vp["name"]
                all_results.append(res)
                
                if res["passed"]:
                    total_passed += 1
                    print(f"  [OK] {disc['name']:<30} : PASSED (0 object/undefined leaks)")
                else:
                    print(f"  [ERROR] {disc['name']:<30} : FAILED -> {', '.join(res['findings'])}")

            await context.close()
        await browser.close()

    pass_rate = (total_passed / total_audited * 100.0) if total_audited > 0 else 0.0

    report_data = {
        "title": "Object Rendering & [object Object] Verification Report",
        "total_audited": total_audited,
        "total_passed": total_passed,
        "pass_rate_percent": pass_rate,
        "all_passed": total_passed == total_audited,
        "results": all_results
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print("\n======================================================================")
    print(f"  📊 VERIFICATION SUMMARY: {total_passed}/{total_audited} PASSED ({pass_rate:.1f}%)")
    print(f"  Report saved to: {REPORT_FILE}")
    print("======================================================================")

    return total_passed == total_audited


if __name__ == "__main__":
    success = asyncio.run(run_full_verification())
    sys.exit(0 if success else 1)
