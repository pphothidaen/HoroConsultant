#!/usr/bin/env python3
"""
scripts/run_randomized_playwright_test.py
============================================
Executes Playwright browser UI automation on live HF Static Space:
  Target: https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html

Fills the BaZi form with randomized test questions across multiple life domains,
submits the form, waits for static/AI answer rendering, captures visual screenshots,
and saves the screenshots to artifacts directory.
"""

from __future__ import annotations

import sys
import os
import time
import json
import random
import asyncio
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

from playwright.async_api import async_playwright

PROD_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots"
ARTIFACT_DIR = Path("/Users/kimlenglim/.agy-account-1/.gemini/antigravity-cli/brain/54cf3650-3430-47cd-9081-c506d9a7fb8a/screenshots")

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
    print("  🚀 PLAYWRIGHT RANDOMIZED UI TEST FOR HF STATIC SPACE")
    print(f"  Target: {PROD_URL}")
    print("======================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 1000})
        page = await context.new_page()

        print("\n[STEP 1] Navigating to HF Static Space Dashboard...")
        resp = await page.goto(PROD_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        shot_init = SCREENSHOT_DIR / "hf_static_01_init.png"
        await page.screenshot(path=str(shot_init), full_page=True)
        shutil.copy(shot_init, ARTIFACT_DIR / shot_init.name)
        print(f"  • Initial Load: HTTP {resp.status}")

        test_results = []

        for idx, (category, query_text) in enumerate(RANDOM_QUERIES, 1):
            print(f"\n[STEP {idx+1}] Testing Category: {category}...")
            
            # Fill query field
            await page.fill("#query", query_text)
            
            # Click Calculate button
            await page.click("#btn-submit")
            
            # Wait for calculation results
            await page.wait_for_timeout(4000)
            
            # Check results rendering
            res_container_visible = await page.is_visible("#results-container") or await page.is_visible("#interpretation-card")
            reading_text = await page.inner_text("#reading-body") if await page.is_visible("#reading-body") else ""
            
            shot_file = SCREENSHOT_DIR / f"hf_static_q{idx:02d}_{category.replace(' ', '_').replace('/', '_')}.png"
            await page.screenshot(path=str(shot_file), full_page=True)
            shutil.copy(shot_file, ARTIFACT_DIR / shot_file.name)
            
            status = "PASSED" if res_container_visible and len(reading_text) > 20 else "FAILED"
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
