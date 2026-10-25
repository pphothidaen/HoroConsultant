#!/usr/bin/env python3
"""
scripts/run_randomized_playwright_test.py
============================================
Executes Playwright browser UI automation on the public Vercel application:
  Target: HORO_PUBLIC_URL (defaults to the public Vercel origin)

Fills the BaZi form with randomized test questions across multiple life domains,
submits the form, waits for static/AI answer rendering, captures visual screenshots,
and saves the screenshots to artifacts directory.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.async_api import async_playwright

PUBLIC_ORIGIN = os.getenv("HORO_PUBLIC_URL", "https://horo-consultant-psi.vercel.app").rstrip("/")
PROD_URL = f"{PUBLIC_ORIGIN}/"
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots"
ARTIFACT_DIR = ROOT / "project" / "tests" / "artifacts_screenshots"

SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_QUERIES = [
    ("💼 การงาน", "วิเคราะห์ทิศทางความก้าวหน้าในการงาน และช่วงเวลาที่เหมาะสมในการเปลี่ยนสายงาน"),
    ("💰 การเงิน", "วิเคราะห์ธาตุโชคลาภ (Wealth Element) และการลงทุนในทรัพย์สินเพื่อความมั่นคง"),
    ("❤️ ความรัก", "วิเคราะห์ดวงความรัก ภพคู่ครอง (Spouse Palace) และลักษณะอุปนิสัยคู่สมรส"),
    ("🏥 สุขภาพ", "วิเคราะห์ความสมดุลของธาตุทั้ง 5 และการดูแลสุขภาพกายและจิตใจ"),
    ("✅ Do's", "วิเคราะห์สิ่งที่ควรทำ (Do's) ธาตุคุณประโยชน์ (用神) และทิศทางมงคลเสริมดวง"),
    ("❌ Don'ts", "วิเคราะห์สิ่งที่ควรหลีกเลี่ยง (Don'ts) ทิศอสูร และข้อควรระวังสำคัญ")
]

async def run_randomized_playwright_ui_test():
    print("======================================================================")
    print("  🚀 PLAYWRIGHT RANDOMIZED UI TEST FOR PUBLIC VERCEL")
    print(f"  Target: {PROD_URL}")
    print("======================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 1000})
        page = await context.new_page()

        print("\n[STEP 1] Navigating to public Vercel dashboard...")
        resp = await page.goto(PROD_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        shot_init = SCREENSHOT_DIR / "prod_01_init.png"
        await page.screenshot(path=str(shot_init), full_page=True)
        shutil.copy(shot_init, ARTIFACT_DIR / shot_init.name)
        print(f"  • Initial Load: HTTP {resp.status if resp else 0}")

        test_results = []
        api_responses = []
        page.on("response", lambda response: api_responses.append({
            "url": response.url,
            "ok": response.ok,
            "status": response.status,
        }))

        for idx, (category, query_text) in enumerate(RANDOM_QUERIES, 1):
            print(f"\n[STEP {idx+1}] Testing Category: {category}...")
            request_start = len(api_responses)
            
            # Fill query field
            await page.fill("#query", query_text)
            
            # Click Calculate button
            await page.click("#btn-submit")
            
            # Wait for calculation results
            await page.wait_for_timeout(4000)
            
            # Check results rendering
            res_container_visible = await page.is_visible("#results-container") or await page.is_visible("#interpretation-card")
            reading_text = await page.inner_text("#reading-body") if await page.is_visible("#reading-body") else ""
            
            shot_file = SCREENSHOT_DIR / f"prod_q{idx:02d}_{category.replace(' ', '_').replace('/', '_')}.png"
            await page.screenshot(path=str(shot_file), full_page=True)
            shutil.copy(shot_file, ARTIFACT_DIR / shot_file.name)
            
            api_ok = any(
                response["ok"] and "/api/v1/bazi/interpret" in response["url"]
                for response in api_responses[request_start:]
            )
            status = "PASSED" if res_container_visible and len(reading_text) > 20 and api_ok else "FAILED"
            print(f"  • Category: {category}")
            print(f"  • Render Status: {'✅ PASSED' if status == 'PASSED' else '❌ FAILED'}")
            print(f"  • Answer Snippet: {reading_text[:80].strip()}...")
            print(f"  • Screenshot: screenshots/{shot_file.name}")
            
            test_results.append({
                "step": idx,
                "category": category,
                "query": query_text,
                "status": status,
                "answer_snippet": reading_text[:150].strip(),
                "screenshot_path": f"screenshots/{shot_file.name}"
            })

        await browser.close()
        print("\n======================================================================")
        print("  🎉 PLAYWRIGHT RANDOMIZED UI TEST COMPLETE")
        print("======================================================================")
        return test_results

def main():
    results = asyncio.run(run_randomized_playwright_ui_test())
    all_passed = all(r["status"] == "PASSED" for r in results)
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
