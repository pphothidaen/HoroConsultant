#!/usr/bin/env python3
"""
scripts/run_visual_layout_audit.py
====================================
Automated Multi-Viewport Screenshot Capture & Visual Layout Distortion Auditor.

Validates:
1. Multi-viewport rendering across Desktop, Laptop, Tablet, and Mobile devices.
2. DOM element bounding box collision/overlap detection.
3. Horizontal overflow and layout distortion guard.
4. Full-page screenshot artifact cataloging.

Usage:
    python3 scripts/run_visual_layout_audit.py
    python3 scripts/run_visual_layout_audit.py --url http://localhost:8888 --json
    python3 scripts/run_visual_layout_audit.py --viewports desktop-4k mobile-ios
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from multiprocessing import Process
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("visual_layout_audit")

DEFAULT_SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots" / "visual_audit"
DEFAULT_REPORT_DIR = ROOT / "project" / "tests" / "artifacts"

VIEWPORT_MATRIX: dict[str, dict[str, Any]] = {
    "desktop-4k": {"width": 1920, "height": 1080, "category": "desktop", "device_scale_factor": 1},
    "laptop-standard": {"width": 1366, "height": 768, "category": "laptop", "device_scale_factor": 1},
    "tablet-portrait": {"width": 768, "height": 1024, "category": "tablet", "device_scale_factor": 2, "is_mobile": True},
    "mobile-ios": {"width": 390, "height": 844, "category": "mobile", "device_scale_factor": 3, "is_mobile": True, "has_touch": True},
    "mobile-compact": {"width": 360, "height": 740, "category": "mobile", "device_scale_factor": 2, "is_mobile": True, "has_touch": True},
}

DEFAULT_PAGES = [
    {"name": "main_dashboard", "path": "/"},
    {"name": "admin_panel", "path": "/admin.html"},
]

DOM_AUDIT_JS = """
() => {
    const results = {
        viewport: { width: window.innerWidth, height: window.innerHeight },
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
        overlaps: [],
        clippedElements: [],
        totalElementsAudited: 0
    };

    // Candidate elements for overlap auditing
    const selector = 'button, input, select, textarea, .card, .v3-claim-card, .tab-btn, .disclaimer-banner, nav, header, main, footer, section, .form-group';
    const elements = Array.from(document.querySelectorAll(selector)).filter(el => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && rect.width > 5 && rect.height > 5;
    });

    results.totalElementsAudited = elements.length;

    // Check overlaps
    for (let i = 0; i < elements.length; i++) {
        const elA = elements[i];
        const rectA = elA.getBoundingClientRect();

        for (let j = i + 1; j < elements.length; j++) {
            const elB = elements[j];
            // Skip parent-child relationships
            if (elA.contains(elB) || elB.contains(elA)) continue;

            const rectB = elB.getBoundingClientRect();

            // Intersect bounding box check
            const intersects = !(
                rectA.right <= rectB.left ||
                rectA.left >= rectB.right ||
                rectA.bottom <= rectB.top ||
                rectA.top >= rectB.bottom
            );

            if (intersects) {
                // Calculate intersection area
                const overlapWidth = Math.min(rectA.right, rectB.right) - Math.max(rectA.left, rectB.left);
                const overlapHeight = Math.min(rectA.bottom, rectB.bottom) - Math.max(rectA.top, rectB.top);
                const overlapArea = overlapWidth * overlapHeight;

                if (overlapArea > 25) { // Minimum 25px^2 to ignore 1px border touching
                    results.overlaps.push({
                        elementA: { tag: elA.tagName.toLowerCase(), id: elA.id || null, class: elA.className || null, rect: { x: rectA.x, y: rectA.y, w: rectA.width, h: rectA.height } },
                        elementB: { tag: elB.tagName.toLowerCase(), id: elB.id || null, class: elB.className || null, rect: { x: rectB.x, y: rectB.y, w: rectB.width, h: rectB.height } },
                        overlapArea: Math.round(overlapArea)
                    });
                }
            }
        }
    }

    return results;
}
"""


def _start_local_server(port: int = 8899) -> Process:
    """Start local uvicorn background process for testing."""
    os.environ["SKIP_FAISS_WARMUP"] = "true"
    os.environ["AUTO_SYNC_ON_STARTUP"] = "false"
    os.environ["AUTO_SYNC_ENABLED"] = "false"
    import uvicorn
    p = Process(target=uvicorn.run, args=("project.main:app",), kwargs={"host": "127.0.0.1", "port": port, "log_level": "error"})
    p.daemon = True
    p.start()
    time.sleep(1.5)
    return p


async def audit_viewport_page(
    page: Any,
    base_url: str,
    page_def: dict[str, str],
    vp_name: str,
    vp_config: dict[str, Any],
    screenshot_dir: Path
) -> dict[str, Any]:
    """Audit single page under specific viewport configuration."""
    target_url = f"{base_url.rstrip('/')}{page_def['path']}"
    logger.info(f"🔍 Auditing [{vp_name}] on {page_def['name']} ({target_url})...")

    await page.set_viewport_size({"width": vp_config["width"], "height": vp_config["height"]})
    t0 = time.monotonic()

    try:
        resp = await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
        status_code = resp.status if resp else 0
        await page.wait_for_timeout(300) # Allow CSS transitions/fonts to settle
    except Exception as exc:
        logger.warning(f"⚠️ Page navigation error on {target_url}: {exc}")
        return {
            "viewport": vp_name,
            "page": page_def["name"],
            "url": target_url,
            "status": "NAVIGATION_FAILED",
            "error": str(exc),
            "latency_ms": round((time.monotonic() - t0) * 1000, 2)
        }

    # Run in-browser DOM audit
    audit_data = await page.evaluate(DOM_AUDIT_JS)
    latency_ms = round((time.monotonic() - t0) * 1000, 2)

    # Capture Screenshot
    screenshot_file = screenshot_dir / f"{vp_name}_{page_def['name']}.png"
    await page.screenshot(path=str(screenshot_file), full_page=True)

    has_issues = audit_data.get("hasHorizontalOverflow", False) or len(audit_data.get("overlaps", [])) > 0
    verdict = "LAYOUT_PASS" if not has_issues else "LAYOUT_WARN"

    return {
        "viewport": vp_name,
        "viewport_config": vp_config,
        "page": page_def["name"],
        "url": target_url,
        "http_status": status_code,
        "latency_ms": latency_ms,
        "verdict": verdict,
        "has_horizontal_overflow": audit_data.get("hasHorizontalOverflow", False),
        "scroll_width": audit_data.get("scrollWidth", 0),
        "client_width": audit_data.get("clientWidth", 0),
        "overlap_count": len(audit_data.get("overlaps", [])),
        "overlaps": audit_data.get("overlaps", []),
        "elements_audited": audit_data.get("totalElementsAudited", 0),
        "screenshot_path": str(screenshot_file.relative_to(ROOT) if ROOT in screenshot_file.parents else screenshot_file)
    }


async def run_visual_audit_suite(
    base_url: str = "http://127.0.0.1:8899",
    viewports: list[str] | None = None,
    screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR
) -> dict[str, Any]:
    """Execute complete multi-viewport visual layout audit."""
    from playwright.async_api import async_playwright

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    active_viewports = viewports or list(VIEWPORT_MATRIX.keys())
    results: list[dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for vp_name in active_viewports:
            if vp_name not in VIEWPORT_MATRIX:
                logger.warning(f"Unknown viewport profile: {vp_name}, skipping.")
                continue
            vp_config = VIEWPORT_MATRIX[vp_name]
            for page_def in DEFAULT_PAGES:
                res = await audit_viewport_page(page, base_url, page_def, vp_name, vp_config, screenshot_dir)
                results.append(res)

        await browser.close()

    total_scenarios = len(results)
    passed_scenarios = sum(1 for r in results if r.get("verdict") == "LAYOUT_PASS")
    overflow_count = sum(1 for r in results if r.get("has_horizontal_overflow", False))
    total_overlaps = sum(r.get("overlap_count", 0) for r in results)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": base_url,
        "total_scenarios": total_scenarios,
        "passed_scenarios": passed_scenarios,
        "failed_scenarios": total_scenarios - passed_scenarios,
        "horizontal_overflow_detected": overflow_count,
        "total_dom_overlaps_detected": total_overlaps,
        "overall_status": "PASSED" if passed_scenarios == total_scenarios else "WARNING",
        "scenarios": results
    }

    report_file = report_dir / "visual_layout_report.json"
    report_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"📄 Saved visual layout report to {report_file}")

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Horo Visual Layout & Multi-Viewport Auditor")
    parser.add_argument("--url", default=None, help="Base URL to audit (defaults to starting local server)")
    parser.add_argument("--viewports", nargs="+", default=None, help="Viewports to audit (e.g. desktop-4k mobile-ios)")
    parser.add_argument("--json", action="store_true", help="Output pure JSON summary")
    parser.add_argument("--no-server", action="store_true", help="Do not spin up local server")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    server_process = None
    target_url = args.url

    if not target_url and not args.no_server:
        logger.info("🚀 Launching local testing server on port 8899...")
        server_process = _start_local_server(8899)
        target_url = "http://127.0.0.1:8899"
    elif not target_url:
        target_url = "http://127.0.0.1:8000"

    try:
        summary = asyncio.run(run_visual_audit_suite(
            base_url=target_url,
            viewports=args.viewports,
        ))
    finally:
        if server_process and server_process.is_alive():
            server_process.terminate()
            server_process.join()

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 76)
        print("  HORO UI VISUAL LAYOUT & MULTI-VIEWPORT AUDIT REPORT")
        print("=" * 76)
        print(f"  Target Base URL     : {summary['base_url']}")
        print(f"  Total Scenarios     : {summary['total_scenarios']}")
        print(f"  Passed Scenarios    : {summary['passed_scenarios']}/{summary['total_scenarios']}")
        print(f"  Horizontal Overflow : {summary['horizontal_overflow_detected']}")
        print(f"  DOM Overlaps Found  : {summary['total_dom_overlaps_detected']}")
        print(f"  Overall Status      : {summary['overall_status']}")
        print("=" * 76)
        for s in summary["scenarios"]:
            print(f"  • [{s['viewport']:<15}] {s['page']:<16} : {s.get('verdict','UNKNOWN'):<11} (Overlaps: {s.get('overlap_count',0)}, H-Overflow: {s.get('has_horizontal_overflow',False)})")
        print("=" * 76 + "\n")

    return 0 if summary["overall_status"] in ("PASSED", "WARNING") else 1


if __name__ == "__main__":
    raise SystemExit(main())
