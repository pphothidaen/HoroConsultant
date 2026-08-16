"""
scripts/audit_ui_overlap.py
===========================
Automated UI Layout & Section Overlap Auditor using Playwright.
Evaluates DOM bounding boxes across Desktop, Tablet, and Mobile viewports
to detect any element collision, negative margin clipping, or visual overlaps.
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

PROD_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
VIEWPORTS = [
    {"name": "Desktop (1440x900)", "width": 1440, "height": 900},
    {"name": "Tablet (768x1024)", "width": 768, "height": 1024},
    {"name": "Mobile (375x812)", "width": 375, "height": 812},
]


async def audit_viewport_overlaps(page, vp):
    print(f"\n--- Checking Viewport: {vp['name']} ---")
    await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
    await page.goto(PROD_URL, wait_until="networkidle")
    await page.wait_for_timeout(1500)

    # Click preset & calculate to populate all sections
    try:
        await page.click(".preset-buttons button:has-text('กรุงเทพฯ')")
        await page.click("#btn-submit")
        await page.wait_for_timeout(4000)
    except Exception as e:
        print(f"  Note during form submit: {e}")

    # Also calculate a branch to populate #branch-result-card
    try:
        await page.click("button:has-text('紫微斗數')")
        await page.wait_for_timeout(1000)
    except Exception as e:
        pass

    # Execute JS overlap detection in browser
    overlap_report = await page.evaluate('''() => {
        const results = [];
        
        // 1. Check top-level major sections
        const majorSelectors = [
            '.app-header',
            '.main-container',
            '.form-section',
            '.results-section',
            '.app-footer',
            '#branch-result-card',
            '#svg-chart-card',
            '#pillars-card',
            '#elements-card',
            '#interpretation-card'
        ];

        const elements = [];
        for (const sel of majorSelectors) {
            const el = document.querySelector(sel);
            if (el) {
                const style = window.getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden' && !el.classList.contains('hidden')) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        elements.push({ sel, el, rect });
                    }
                }
            }
        }

        // Pairwise collision check
        for (let i = 0; i < elements.length; i++) {
            for (let j = i + 1; j < elements.length; j++) {
                const a = elements[i];
                const b = elements[j];

                // Skip if one contains the other
                if (a.el.contains(b.el) || b.el.contains(a.el)) continue;

                // Check bounding box intersection
                const xOverlap = Math.max(0, Math.min(a.rect.right, b.rect.right) - Math.max(a.rect.left, b.rect.left));
                const yOverlap = Math.max(0, Math.min(a.rect.bottom, b.rect.bottom) - Math.max(a.rect.top, b.rect.top));

                if (xOverlap > 5 && yOverlap > 5) {
                    results.push({
                        type: 'MAJOR_OVERLAP',
                        elemA: a.sel,
                        elemB: b.sel,
                        rectA: { left: a.rect.left, top: a.rect.top, right: a.rect.right, bottom: a.rect.bottom },
                        rectB: { left: b.rect.left, top: b.rect.top, right: b.rect.right, bottom: b.rect.bottom },
                        intersectionArea: xOverlap * yOverlap
                    });
                }
            }
        }

        // 2. Check inner card siblings inside results-section
        const resultCards = Array.from(document.querySelectorAll('.results-section > .result-card:not(.hidden)'));
        for (let i = 0; i < resultCards.length; i++) {
            for (let j = i + 1; j < resultCards.length; j++) {
                const a = resultCards[i];
                const b = resultCards[j];
                const rA = a.getBoundingClientRect();
                const rB = b.getBoundingClientRect();
                const xO = Math.max(0, Math.min(rA.right, rB.right) - Math.max(rA.left, rB.left));
                const yO = Math.max(0, Math.min(rA.bottom, rB.bottom) - Math.max(rA.top, rB.top));
                if (xO > 5 && yO > 5) {
                    results.push({
                        type: 'CARD_SIBLING_OVERLAP',
                        elemA: a.id || a.className,
                        elemB: b.id || b.className,
                        intersectionArea: xO * yO
                    });
                }
            }
        }

        // 3. Check overflow-x issues (content extending past viewport)
        const docWidth = document.documentElement.offsetWidth;
        const scrollWidth = document.documentElement.scrollWidth;
        const hasHorizontalScroll = scrollWidth > docWidth + 2;

        return {
            overlaps: results,
            hasHorizontalScroll,
            docWidth,
            scrollWidth,
            activeCardCount: resultCards.length
        };
    }''')

    overlaps = overlap_report["overlaps"]
    print(f"  • Active Visible Result Cards: {overlap_report['activeCardCount']}")
    print(f"  • Horizontal Overflow: {'⚠️ YES (' + str(overlap_report['scrollWidth']) + 'px > ' + str(overlap_report['docWidth']) + 'px)' if overlap_report['hasHorizontalScroll'] else '✅ NO (Clean Width)'}")
    if overlaps:
        print(f"  ❌ Detected {len(overlaps)} Element Overlaps:")
        for ol in overlaps:
            print(f"     - [{ol['type']}] {ol['elemA']} overlaps with {ol['elemB']} (Area: {ol['intersectionArea']:.1f}px²)")
    else:
        print(f"  ✅ 0 Overlaps Detected — Layout is clean!")

    return len(overlaps) == 0 and not overlap_report["hasHorizontalScroll"]


async def main():
    print("======================================================================")
    print("  🎨 UI SECTION & LAYOUT OVERLAP AUDITOR")
    print(f"  Target: {PROD_URL}")
    print("======================================================================")

    all_passed = True
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for vp in VIEWPORTS:
            ok = await audit_viewport_overlaps(page, vp)
            if not ok:
                all_passed = False

        await browser.close()

    print("\n======================================================================")
    if all_passed:
        print("  🎉 AUDIT COMPLETE: ALL VIEWPORTS PASSED WITH ZERO OVERLAPS")
    else:
        print("  ⚠️ AUDIT COMPLETE: ISSUES DETECTED")
    print("======================================================================")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
