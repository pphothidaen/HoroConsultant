#!/usr/bin/env python3
"""Deterministic multi-viewport screenshot and visual layout auditor.

The default scenario preserves the historical dashboard/admin audit. The
``v3-consensus`` scenario selects and populates the Horo v3.0 tab with a local
fixture, so it never depends on a production calculation response.
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

V3_CONSENSUS_FIXTURE: dict[str, Any] = {
    "audit_verdict": "AUDIT_PASS",
    "lciw": 0.9125,
    "rniw": 0.0875,
    "epistemic_disclaimer": (
        "ผลการวิเคราะห์นี้เกิดขึ้นจากการประมวลผลตรรกะตามกฎของสำนักวิชา"
        "และความสอดคล้องของแบบจำลองเท่านั้น ไม่ถือเป็นการรับรองผลสัมฤทธิ์"
        "ในอนาคตเชิงประจักษ์"
    ),
}

SCENARIO_DEFINITIONS: dict[str, dict[str, Any]] = {
    "default": {
        "description": "Historical dashboard and admin page audit",
        "pages": DEFAULT_PAGES,
        "scope_selector": "body",
    },
    "v3-consensus": {
        "description": "Selected Horo v3.0 Consensus Engine tab with deterministic populated fixture",
        "pages": [{"name": "horo_v3_consensus", "path": "/", "setup": "v3-consensus"}],
        "scope_selector": "#interpretation-card",
        "color_scheme": "dark",
        "theme": "dark",
    },
}

# Accepts {scopeSelector}. Audits root/body overflow, visible descendants for
# bounds/clipping, direct siblings for collisions, and rendered text for WCAG AA.
DOM_AUDIT_JS = r"""
(options = {}) => {
    const tolerance = 1;
    const scopeSelector = options.scopeSelector || 'body';
    const scope = document.querySelector(scopeSelector) || document.body;
    const root = document.documentElement;
    const body = document.body;

    const roundedRect = rect => ({
        x: Math.round(rect.x * 100) / 100,
        y: Math.round(rect.y * 100) / 100,
        width: Math.round(rect.width * 100) / 100,
        height: Math.round(rect.height * 100) / 100,
        right: Math.round(rect.right * 100) / 100,
        bottom: Math.round(rect.bottom * 100) / 100
    });
    const describe = el => {
        if (!el) return null;
        let value = el.tagName.toLowerCase();
        if (el.id) value += `#${el.id}`;
        const classes = typeof el.className === 'string'
            ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 3)
            : [];
        if (classes.length) value += `.${classes.join('.')}`;
        return value;
    };
    const isVisible = el => {
        if (!(el instanceof Element)) return false;
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return !['none', 'contents'].includes(style.display)
            && style.visibility !== 'hidden'
            && Number.parseFloat(style.opacity || '1') > 0
            && rect.width > 0.5 && rect.height > 0.5
            && !el.closest('[aria-hidden="true"]');
    };

    const scopedElements = [scope, ...scope.querySelectorAll('*')].filter(isVisible);
    const outOfBounds = [];
    const clippedElements = [];
    const clippingRoots = [];
    for (const el of scopedElements) {
        const rect = el.getBoundingClientRect();
        if (rect.left < -tolerance || rect.right > root.clientWidth + tolerance) {
            outOfBounds.push({
                element: describe(el), rect: roundedRect(rect), rootClientWidth: root.clientWidth,
                leftOverflowPx: Math.max(0, Math.round(-rect.left * 100) / 100),
                rightOverflowPx: Math.max(0, Math.round((rect.right - root.clientWidth) * 100) / 100)
            });
        }
        let ancestor = el.parentElement;
        while (ancestor && ancestor !== root) {
            const style = getComputedStyle(ancestor);
            const clipsX = ['hidden', 'clip'].includes(style.overflowX);
            const clipsY = ['hidden', 'clip'].includes(style.overflowY);
            if (clipsX || clipsY) {
                const parentRect = ancestor.getBoundingClientRect();
                const clippedX = clipsX && (rect.left < parentRect.left - tolerance || rect.right > parentRect.right + tolerance);
                const clippedY = clipsY && (rect.top < parentRect.top - tolerance || rect.bottom > parentRect.bottom + tolerance);
                if (clippedX || clippedY) {
                    const axes = [clippedX ? 'x' : null, clippedY ? 'y' : null].filter(Boolean);
                    // Keep the highest clipped descendant per ancestor/axis. Its
                    // nested children share the same root cause and add noise.
                    const coveredByRoot = clippingRoots.some(item =>
                        item.ancestor === ancestor
                        && item.axes.join(',') === axes.join(',')
                        && item.element.contains(el)
                    );
                    if (!coveredByRoot) {
                        clippingRoots.push({element: el, ancestor, axes});
                        clippedElements.push({
                            element: describe(el), ancestor: describe(ancestor), axes,
                            elementRect: roundedRect(rect), ancestorRect: roundedRect(parentRect),
                            ancestorOverflow: {x: style.overflowX, y: style.overflowY}
                        });
                    }
                    break;
                }
            }
            ancestor = ancestor.parentElement;
        }
    }

    const collisionSelector = [
        'button', 'input', 'select', 'textarea', '[role="button"]', '.tab-buttons',
        '.tab-btn', '.card', '.v3-claim-card', '.v3-audit-summary-container',
        '.v3-epistemic-disclaimer', '.v3-veto-banner', 'nav', 'header', 'main',
        'footer', 'section'
    ].join(',');
    const candidates = [scope, ...scope.querySelectorAll(collisionSelector)].filter(isVisible);
    const overlaps = [];
    for (let i = 0; i < candidates.length; i++) {
        const elA = candidates[i];
        const rectA = elA.getBoundingClientRect();
        for (let j = i + 1; j < candidates.length; j++) {
            const elB = candidates[j];
            if (elA.parentElement !== elB.parentElement) continue;
            const styleA = getComputedStyle(elA);
            const styleB = getComputedStyle(elB);
            if (['absolute', 'fixed'].includes(styleA.position) || ['absolute', 'fixed'].includes(styleB.position)) continue;
            const rectB = elB.getBoundingClientRect();
            const width = Math.min(rectA.right, rectB.right) - Math.max(rectA.left, rectB.left);
            const height = Math.min(rectA.bottom, rectB.bottom) - Math.max(rectA.top, rectB.top);
            const area = width * height;
            if (width > tolerance && height > tolerance && area > 25) {
                overlaps.push({
                    parent: describe(elA.parentElement),
                    elementA: {element: describe(elA), rect: roundedRect(rectA)},
                    elementB: {element: describe(elB), rect: roundedRect(rectB)},
                    overlapArea: Math.round(area)
                });
            }
        }
    }

    const parseColor = value => {
        const match = String(value).match(/rgba?\(\s*([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)/i);
        if (!match) return null;
        return {r: +match[1], g: +match[2], b: +match[3], a: match[4] === undefined ? 1 : +match[4]};
    };
    const composite = (front, back) => {
        const alpha = front.a + back.a * (1 - front.a);
        if (alpha <= 0) return {r: 255, g: 255, b: 255, a: 1};
        return {
            r: (front.r * front.a + back.r * back.a * (1 - front.a)) / alpha,
            g: (front.g * front.a + back.g * back.a * (1 - front.a)) / alpha,
            b: (front.b * front.a + back.b * back.a * (1 - front.a)) / alpha,
            a: alpha
        };
    };
    const colorString = color => `rgb(${Math.round(color.r)}, ${Math.round(color.g)}, ${Math.round(color.b)})`;
    const luminance = color => {
        const channel = value => {
            const normalized = value / 255;
            return normalized <= 0.04045 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
        };
        return 0.2126 * channel(color.r) + 0.7152 * channel(color.g) + 0.0722 * channel(color.b);
    };
    const contrastRatio = (a, b) => {
        const l1 = luminance(a);
        const l2 = luminance(b);
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    };
    const effectiveBackground = el => {
        let current = el;
        let result = {r: 255, g: 255, b: 255, a: 0};
        while (current && current instanceof Element) {
            const style = getComputedStyle(current);
            if (style.backgroundImage && style.backgroundImage !== 'none') {
                return {
                    determinate: false, reason: 'gradient_or_background_image',
                    element: describe(current), backgroundImage: style.backgroundImage.slice(0, 160)
                };
            }
            const layer = parseColor(style.backgroundColor);
            if (layer && layer.a > 0) {
                result = composite(result, layer);
                if (result.a >= 0.999) break;
            }
            current = current.parentElement;
        }
        if (result.a < 0.999) result = composite(result, {r: 255, g: 255, b: 255, a: 1});
        return {determinate: true, color: result};
    };

    const textElements = [];
    const seen = new Set();
    for (const el of scopedElements) {
        if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG'].includes(el.tagName)) continue;
        const nodes = [...el.childNodes].filter(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
        if (!nodes.length || seen.has(el)) continue;
        const rendered = nodes.some(node => {
            const range = document.createRange();
            range.selectNodeContents(node);
            const rect = range.getBoundingClientRect();
            return rect.width > 0.5 && rect.height > 0.5;
        });
        if (rendered) {
            seen.add(el);
            textElements.push({el, text: nodes.map(node => node.textContent.trim()).join(' ')});
        }
    }

    const contrastFailures = [];
    const contrastIndeterminate = [];
    let contrastAudited = 0;
    for (const item of textElements) {
        const style = getComputedStyle(item.el);
        const foreground = parseColor(style.color);
        if (!foreground || foreground.a <= 0) continue;
        const background = effectiveBackground(item.el);
        if (!background.determinate) {
            contrastIndeterminate.push({
                element: describe(item.el), textSample: item.text.slice(0, 100),
                foreground: style.color, reason: background.reason,
                backgroundElement: background.element, backgroundImage: background.backgroundImage
            });
            continue;
        }
        const effectiveForeground = foreground.a < 1 ? composite(foreground, background.color) : foreground;
        const ratio = contrastRatio(effectiveForeground, background.color);
        const fontSize = Number.parseFloat(style.fontSize || '16');
        const weight = Number.parseInt(style.fontWeight, 10) || 400;
        const largeText = fontSize >= 24 || (fontSize >= 18.66 && weight >= 700);
        const requiredRatio = largeText ? 3 : 4.5;
        contrastAudited += 1;
        if (ratio + 0.005 < requiredRatio) {
            contrastFailures.push({
                element: describe(item.el), textSample: item.text.slice(0, 100),
                foreground: colorString(effectiveForeground), background: colorString(background.color),
                ratio: Math.round(ratio * 100) / 100, requiredRatio,
                fontSizePx: fontSize, fontWeight: weight, largeText
            });
        }
    }

    return {
        scopeSelector,
        viewport: {width: window.innerWidth, height: window.innerHeight},
        documentMetrics: {
            scrollWidth: root.scrollWidth, clientWidth: root.clientWidth,
            hasHorizontalOverflow: root.scrollWidth > root.clientWidth + tolerance
        },
        bodyMetrics: {
            scrollWidth: body ? body.scrollWidth : 0, clientWidth: body ? body.clientWidth : 0,
            hasHorizontalOverflow: body ? body.scrollWidth > body.clientWidth + tolerance : false
        },
        overlaps, outOfBounds, clippedElements,
        contrast: {
            auditedTextElements: contrastAudited,
            failures: contrastFailures,
            indeterminate: contrastIndeterminate
        },
        totalElementsAudited: scopedElements.length
    };
}
"""


def _start_local_server(port: int = 8899) -> Process:
    """Start a local uvicorn process using test-safe environment flags."""
    os.environ["SKIP_FAISS_WARMUP"] = "true"
    os.environ["AUTO_SYNC_ON_STARTUP"] = "false"
    os.environ["AUTO_SYNC_ENABLED"] = "false"
    import uvicorn

    process = Process(
        target=uvicorn.run,
        args=("project.main:app",),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": "error"},
    )
    process.daemon = True
    process.start()
    time.sleep(1.5)
    return process


async def _prepare_v3_consensus_scenario(page: Any) -> dict[str, Any]:
    """Select and populate the v3 tab without calling the calculate API."""
    blocked_requests: list[str] = []

    async def block_v3_calculation(route: Any) -> None:
        blocked_requests.append(route.request.url)
        await route.abort()

    await page.route("**/api/v3/calculate", block_v3_calculation)
    await page.wait_for_function("typeof window.renderHoroV3Results === 'function'", timeout=10000)
    await page.add_style_tag(content="*, *::before, *::after { animation: none !important; transition: none !important; }")
    await page.evaluate(
        """
        fixture => {
            document.documentElement.style.scrollBehavior = 'auto';
            document.documentElement.dataset.theme = 'dark';
            document.body.classList.add('dark-mode');
            const card = document.getElementById('interpretation-card');
            if (!card) throw new Error('interpretation-card not found');
            card.classList.remove('hidden');
            const body = card.querySelector('.accordion-card-body');
            if (body) body.classList.remove('acc-collapsed');
            const header = card.querySelector('.accordion-card-header');
            if (header) header.setAttribute('aria-expanded', 'true');
            window.lastHoroV3Data = fixture;
        }
        """,
        V3_CONSENSUS_FIXTURE,
    )
    tab_button = page.locator("button.tab-btn[onclick*='tab-v3-engine']")
    # DOM activation is intentional: it can select a tab that is itself clipped,
    # leaving the geometry defect visible for the subsequent audit.
    await tab_button.evaluate("button => button.click()")
    await page.wait_for_function(
        """
        () => {
            const tab = document.getElementById('tab-v3-engine');
            const button = document.querySelector("button.tab-btn[onclick*='tab-v3-engine']");
            return Boolean(tab && !tab.classList.contains('hidden') && button && button.classList.contains('active'));
        }
        """,
        timeout=5000,
    )
    await page.locator("#v3-engine-results .v3-claim-card").first.wait_for(state="visible", timeout=5000)
    await page.evaluate("document.getElementById('interpretation-card').scrollIntoView({block: 'start'})")
    await page.wait_for_timeout(200)
    state = await page.evaluate(
        """
        () => ({
            fixtureInjected: window.lastHoroV3Data?.lciw === 0.9125,
            selectedTab: document.querySelector('.tab-btn.active')?.textContent.trim() || null,
            v3TabVisible: !document.getElementById('tab-v3-engine')?.classList.contains('hidden'),
            claimCardCount: document.querySelectorAll('#v3-engine-results .v3-claim-card').length,
            auditMetricStyles: [...document.querySelectorAll('.v3-audit-summary-container strong')].map(el => ({
                text: el.textContent.trim(),
                color: getComputedStyle(el).color,
                parentBackground: getComputedStyle(el.parentElement).backgroundColor
            }))
        })
        """
    )
    state["calculateApiRequestsBlocked"] = len(blocked_requests)
    return state


async def audit_viewport_page(
    page: Any,
    base_url: str,
    page_def: dict[str, str],
    vp_name: str,
    vp_config: dict[str, Any],
    screenshot_dir: Path,
    scenario_name: str = "default",
    scope_selector: str = "body",
) -> dict[str, Any]:
    """Audit one page at one viewport and capture deterministic evidence."""
    target_url = f"{base_url.rstrip('/')}{page_def['path']}"
    logger.info("Auditing [%s] scenario=%s page=%s url=%s", vp_name, scenario_name, page_def["name"], target_url)
    started_at = time.monotonic()
    try:
        response = await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
        status_code = response.status if response else 0
        await page.wait_for_timeout(300)
    except Exception as exc:
        logger.warning("Page navigation error on %s: %s", target_url, exc)
        return {
            "viewport": vp_name, "page": page_def["name"], "scenario": scenario_name,
            "url": target_url, "status": "NAVIGATION_FAILED", "error": str(exc),
            "latency_ms": round((time.monotonic() - started_at) * 1000, 2),
        }

    scenario_state: dict[str, Any] = {}
    try:
        if page_def.get("setup") == "v3-consensus":
            scenario_state = await _prepare_v3_consensus_scenario(page)
    except Exception as exc:
        logger.warning("Scenario setup error on %s: %s", target_url, exc)
        scenario_state = {"setupError": str(exc)}

    audit_data = await page.evaluate(DOM_AUDIT_JS, {"scopeSelector": scope_selector})
    latency_ms = round((time.monotonic() - started_at) * 1000, 2)
    screenshot_file = screenshot_dir / f"{vp_name}_{page_def['name']}.png"
    await page.screenshot(path=str(screenshot_file), full_page=True, animations="disabled")

    document_metrics = audit_data.get("documentMetrics", {})
    body_metrics = audit_data.get("bodyMetrics", {})
    overlaps = audit_data.get("overlaps", [])
    out_of_bounds = audit_data.get("outOfBounds", [])
    clipped = audit_data.get("clippedElements", [])
    contrast = audit_data.get("contrast", {})
    has_issues = any((
        status_code >= 400,
        bool(scenario_state.get("setupError")),
        document_metrics.get("hasHorizontalOverflow", False),
        body_metrics.get("hasHorizontalOverflow", False),
        bool(overlaps), bool(out_of_bounds), bool(clipped), bool(contrast.get("failures", [])),
    ))
    return {
        "viewport": vp_name, "viewport_config": vp_config, "page": page_def["name"],
        "scenario": scenario_name, "scenario_state": scenario_state, "audit_scope": scope_selector,
        "url": target_url, "http_status": status_code, "latency_ms": latency_ms,
        "verdict": "LAYOUT_WARN" if has_issues else "LAYOUT_PASS",
        "has_horizontal_overflow": document_metrics.get("hasHorizontalOverflow", False),
        "document_metrics": document_metrics, "body_metrics": body_metrics,
        "scroll_width": document_metrics.get("scrollWidth", 0),
        "client_width": document_metrics.get("clientWidth", 0),
        "overlap_count": len(overlaps), "overlaps": overlaps,
        "out_of_bounds_count": len(out_of_bounds), "out_of_bounds": out_of_bounds,
        "clipped_element_count": len(clipped), "clipped_elements": clipped,
        "contrast_failure_count": len(contrast.get("failures", [])),
        "contrast_failures": contrast.get("failures", []),
        "contrast_indeterminate_count": len(contrast.get("indeterminate", [])),
        "contrast_indeterminate": contrast.get("indeterminate", []),
        "contrast_text_elements_audited": contrast.get("auditedTextElements", 0),
        "elements_audited": audit_data.get("totalElementsAudited", 0),
        "screenshot_path": str(screenshot_file.relative_to(ROOT) if ROOT in screenshot_file.parents else screenshot_file),
    }


async def run_visual_audit_suite(
    base_url: str = "http://127.0.0.1:8899",
    viewports: list[str] | None = None,
    screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    scenario: str = "default",
) -> dict[str, Any]:
    """Execute a scenario across the canonical viewport matrix."""
    from playwright.async_api import async_playwright

    if scenario not in SCENARIO_DEFINITIONS:
        raise ValueError(f"Unknown scenario: {scenario}")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    active_viewports = viewports or list(VIEWPORT_MATRIX.keys())
    scenario_def = SCENARIO_DEFINITIONS[scenario]
    results: list[dict[str, Any]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        for vp_name in active_viewports:
            if vp_name not in VIEWPORT_MATRIX:
                logger.warning("Unknown viewport profile: %s; skipping", vp_name)
                continue
            vp_config = VIEWPORT_MATRIX[vp_name]
            context = await browser.new_context(
                viewport={"width": vp_config["width"], "height": vp_config["height"]},
                device_scale_factor=vp_config.get("device_scale_factor", 1),
                is_mobile=vp_config.get("is_mobile", False),
                has_touch=vp_config.get("has_touch", False), reduced_motion="reduce",
                color_scheme=scenario_def.get("color_scheme", "light"),
            )
            page = await context.new_page()
            for page_def in scenario_def["pages"]:
                results.append(await audit_viewport_page(
                    page, base_url, page_def, vp_name, vp_config, screenshot_dir,
                    scenario_name=scenario, scope_selector=scenario_def["scope_selector"],
                ))
            await context.close()
        await browser.close()

    total_scenarios = len(results)
    passed_scenarios = sum(1 for result in results if result.get("verdict") == "LAYOUT_PASS")
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": base_url, "scenario": scenario,
        "scenario_description": scenario_def["description"],
        "canonical_viewports_expected": len(VIEWPORT_MATRIX),
        "viewports_audited": [name for name in active_viewports if name in VIEWPORT_MATRIX],
        "total_scenarios": total_scenarios, "passed_scenarios": passed_scenarios,
        "failed_scenarios": total_scenarios - passed_scenarios,
        "horizontal_overflow_detected": sum(1 for result in results if result.get("has_horizontal_overflow", False)),
        "total_dom_overlaps_detected": sum(result.get("overlap_count", 0) for result in results),
        "total_out_of_bounds_detected": sum(result.get("out_of_bounds_count", 0) for result in results),
        "total_clipped_elements_detected": sum(result.get("clipped_element_count", 0) for result in results),
        "total_contrast_failures_detected": sum(result.get("contrast_failure_count", 0) for result in results),
        "total_contrast_indeterminate": sum(result.get("contrast_indeterminate_count", 0) for result in results),
        "overall_status": "PASSED" if passed_scenarios == total_scenarios and total_scenarios > 0 else "WARNING",
        "scenarios": results,
    }
    report_file = report_dir / "visual_layout_report.json"
    report_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved visual layout report to %s", report_file)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Horo Visual Layout and Multi-Viewport Auditor")
    parser.add_argument("--url", default=None, help="Base URL to audit (defaults to starting local server)")
    parser.add_argument("--viewports", nargs="+", default=None, help="Viewport profiles to audit")
    parser.add_argument("--scenario", choices=sorted(SCENARIO_DEFINITIONS), default="default", help="Deterministic audit scenario")
    parser.add_argument("--json", action="store_true", help="Output a JSON summary")
    parser.add_argument("--no-server", action="store_true", help="Do not start the local server")
    return parser


def summary_exit_code(summary: dict[str, Any]) -> int:
    """Fail automation whenever any audited scenario is not fully green."""
    return 0 if summary.get("overall_status") == "PASSED" else 1


def main() -> int:
    args = build_parser().parse_args()
    server_process = None
    target_url = args.url
    if not target_url and not args.no_server:
        logger.info("Launching local test server on port 8899")
        server_process = _start_local_server(8899)
        target_url = "http://127.0.0.1:8899"
    elif not target_url:
        target_url = "http://127.0.0.1:8000"
    try:
        summary = asyncio.run(run_visual_audit_suite(
            base_url=target_url, viewports=args.viewports, scenario=args.scenario,
        ))
    finally:
        if server_process and server_process.is_alive():
            server_process.terminate()
            server_process.join()

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 76)
        print("  HORO UI VISUAL LAYOUT AND MULTI-VIEWPORT AUDIT REPORT")
        print("=" * 76)
        print(f"  Target Base URL       : {summary['base_url']}")
        print(f"  Scenario              : {summary['scenario']}")
        print(f"  Passed Scenarios      : {summary['passed_scenarios']}/{summary['total_scenarios']}")
        print(f"  Horizontal Overflow   : {summary['horizontal_overflow_detected']}")
        print(f"  Sibling Overlaps      : {summary['total_dom_overlaps_detected']}")
        print(f"  Out of Bounds         : {summary['total_out_of_bounds_detected']}")
        print(f"  Clipped Elements      : {summary['total_clipped_elements_detected']}")
        print(f"  WCAG Contrast Failures: {summary['total_contrast_failures_detected']}")
        print(f"  Contrast Manual Review: {summary['total_contrast_indeterminate']}")
        print(f"  Overall Status        : {summary['overall_status']}")
        print("=" * 76)
        for item in summary["scenarios"]:
            print(
                f"  [{item['viewport']:<15}] {item['page']:<22}: {item.get('verdict', 'UNKNOWN'):<11} "
                f"(overlap={item.get('overlap_count', 0)}, out={item.get('out_of_bounds_count', 0)}, "
                f"clip={item.get('clipped_element_count', 0)}, contrast={item.get('contrast_failure_count', 0)})"
            )
        print("=" * 76 + "\n")
    return summary_exit_code(summary)


if __name__ == "__main__":
    raise SystemExit(main())
