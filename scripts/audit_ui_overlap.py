"""Read-only multi-viewport overlap audit for the canonical Vercel UI.

The Hugging Face Docker service is recorded as the separate backend target and
is never opened as a UI page. The command is offline by default; ``--live`` is
required before Playwright or the network is used.
"""

from __future__ import annotations

import argparse
import asyncio
from urllib.parse import urlsplit

CANONICAL_VERCEL_UI_URL = "https://horo-consultant-psi.vercel.app"
CANONICAL_HF_DOCKER_BACKEND_URL = (
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
DEFAULT_TIMEOUT_SECONDS = 15

VIEWPORTS = [
    {"name": "desktop-4k", "width": 1920, "height": 1080},
    {"name": "laptop-standard", "width": 1366, "height": 768},
    {"name": "tablet-portrait", "width": 768, "height": 1024},
    {"name": "mobile-ios", "width": 390, "height": 844},
    {"name": "mobile-compact", "width": 360, "height": 740},
]

OVERLAP_SCRIPT = """() => {
    const overlaps = [];
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
    const visible = [];
    for (const selector of majorSelectors) {
        const element = document.querySelector(selector);
        if (!element) continue;
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        if (
            style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            !element.classList.contains('hidden') &&
            rect.width > 0 &&
            rect.height > 0
        ) {
            visible.push({selector, element, rect});
        }
    }
    for (let first = 0; first < visible.length; first += 1) {
        for (let second = first + 1; second < visible.length; second += 1) {
            const a = visible[first];
            const b = visible[second];
            if (a.element.contains(b.element) || b.element.contains(a.element)) continue;
            const x = Math.max(
                0,
                Math.min(a.rect.right, b.rect.right) - Math.max(a.rect.left, b.rect.left)
            );
            const y = Math.max(
                0,
                Math.min(a.rect.bottom, b.rect.bottom) - Math.max(a.rect.top, b.rect.top)
            );
            if (x > 5 && y > 5) {
                overlaps.push({
                    type: 'MAJOR_OVERLAP',
                    elementA: a.selector,
                    elementB: b.selector,
                    intersectionArea: x * y
                });
            }
        }
    }

    const cards = Array.from(
        document.querySelectorAll('.results-section > .result-card:not(.hidden)')
    );
    for (let first = 0; first < cards.length; first += 1) {
        for (let second = first + 1; second < cards.length; second += 1) {
            const rectA = cards[first].getBoundingClientRect();
            const rectB = cards[second].getBoundingClientRect();
            const x = Math.max(
                0,
                Math.min(rectA.right, rectB.right) - Math.max(rectA.left, rectB.left)
            );
            const y = Math.max(
                0,
                Math.min(rectA.bottom, rectB.bottom) - Math.max(rectA.top, rectB.top)
            );
            if (x > 5 && y > 5) {
                overlaps.push({
                    type: 'CARD_SIBLING_OVERLAP',
                    elementA: cards[first].id || 'unnamed-card',
                    elementB: cards[second].id || 'unnamed-card',
                    intersectionArea: x * y
                });
            }
        }
    }

    const viewportWidth = window.innerWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    return {
        overlaps,
        hasHorizontalScroll: scrollWidth > viewportWidth + 1,
        viewportWidth,
        scrollWidth,
        activeCardCount: cards.length
    };
}"""


def _require_canonical_https_url(value: str, expected: str, label: str) -> str:
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        candidate != expected
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{label} must be the canonical HTTPS target")
    return candidate


async def audit_viewport_overlaps(
    page, viewport: dict, target_url: str, timeout_ms: int
) -> bool:
    """Audit one viewport without printing browser content or input values."""
    await page.set_viewport_size(
        {"width": viewport["width"], "height": viewport["height"]}
    )
    await page.goto(target_url, wait_until="load", timeout=timeout_ms)
    await page.wait_for_timeout(500)

    populated = False
    try:
        await page.click(".preset-buttons button", timeout=timeout_ms)
        await page.click("#btn-submit", timeout=timeout_ms)
        await page.wait_for_selector(
            "#interpretation-card:not(.hidden)", timeout=timeout_ms
        )
        populated = True
    except Exception:  # noqa: BLE001 - preserve audit after optional UI failure
        print(f"[WARNING] {viewport['name']}: result population unavailable")

    try:
        await page.click('button[onclick="calcZiWei()"]', timeout=timeout_ms)
        await page.wait_for_timeout(300)
    except Exception:  # noqa: BLE001 - preserve audit after optional UI failure
        print(f"[WARNING] {viewport['name']}: branch-card population unavailable")

    report = await page.evaluate(OVERLAP_SCRIPT)
    overlap_count = len(report["overlaps"])
    has_overflow = bool(report["hasHorizontalScroll"])
    passed = overlap_count == 0 and not has_overflow
    tag = "[OK]" if passed else "[ERROR]"
    print(
        f"{tag} {viewport['name']}: overlaps={overlap_count} "
        f"horizontal_overflow={str(has_overflow).lower()} "
        f"active_cards={report['activeCardCount']} populated={str(populated).lower()}"
    )
    return passed


async def run_live_audit(
    *,
    ui_url: str,
    backend_url: str,
    timeout_seconds: int,
) -> bool:
    """Run the canonical five-viewport live audit."""
    ui_url = _require_canonical_https_url(ui_url, CANONICAL_VERCEL_UI_URL, "UI URL")
    backend_url = _require_canonical_https_url(
        backend_url,
        CANONICAL_HF_DOCKER_BACKEND_URL,
        "Backend URL",
    )
    if not 1 <= timeout_seconds <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[ERROR] Playwright is not installed")
        return False

    print("[INFO] Vercel UI overlap audit")
    print(f"[INFO] UI target: {ui_url}")
    print(f"[INFO] Backend target: {backend_url}")
    timeout_ms = timeout_seconds * 1000
    results: list[bool] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        for viewport in VIEWPORTS:
            results.append(
                await audit_viewport_overlaps(page, viewport, ui_url, timeout_ms)
            )
        await browser.close()

    passed = all(results)
    print(
        "[OK] All viewport audits passed"
        if passed
        else "[ERROR] Viewport issues detected"
    )
    return passed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only five-viewport overlap audit for the Vercel UI"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        "--prod",
        dest="live",
        action="store_true",
        help="Enable live browser requests",
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="Validate the offline plan"
    )
    parser.add_argument("--ui-url", default=CANONICAL_VERCEL_UI_URL)
    parser.add_argument("--backend-url", default=CANONICAL_HF_DOCKER_BACKEND_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ui_url = _require_canonical_https_url(
            args.ui_url, CANONICAL_VERCEL_UI_URL, "UI URL"
        )
        backend_url = _require_canonical_https_url(
            args.backend_url,
            CANONICAL_HF_DOCKER_BACKEND_URL,
            "Backend URL",
        )
        if not 1 <= args.timeout <= 60:
            raise ValueError("timeout must be between 1 and 60 seconds")
    except ValueError as exc:
        print(f"[ERROR] Invalid diagnostic configuration: {exc}")
        return 2

    if not args.live:
        print("[INFO] Offline dry run; no browser or network access")
        print(f"[INFO] UI target: {ui_url}")
        print(f"[INFO] Backend target: {backend_url}")
        print(f"[OK] Planned viewports: {len(VIEWPORTS)}")
        return 0

    return (
        0
        if asyncio.run(
            run_live_audit(
                ui_url=ui_url,
                backend_url=backend_url,
                timeout_seconds=args.timeout,
            )
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
