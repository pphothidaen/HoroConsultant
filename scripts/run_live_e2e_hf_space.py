"""Read-only Playwright E2E diagnostics for the Vercel production UI.

The Hugging Face target is a separate Docker backend and is never treated as a
browser page. The legacy filename remains only for compatibility. The command
is offline by default; ``--live`` is required to launch a browser or write the
existing screenshot and JSON report artifacts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots" / "live_e2e"
REPORT_PATH = ROOT / "project" / "tests" / "live_e2e_report.json"

CANONICAL_VERCEL_UI_URL = "https://horo-consultant-psi.vercel.app"
CANONICAL_HF_DOCKER_BACKEND_URL = (
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
DEFAULT_TIMEOUT_SECONDS = 20

QUERY_CASES = [
    (
        "Children and offspring",
        "How are children and offspring represented in this BaZi chart?",
        "02_children_query_result.png",
    ),
    (
        "Business investment",
        "Is opening a restaurant in 2026 supported by this chart?",
        "03_business_2026_query_result.png",
    ),
    (
        "Love and relationships",
        "Analyze love, partnership, and relationship timing this year.",
        "04_love_query_result.png",
    ),
    (
        "Wealth and finance",
        "Analyze finance, income, and wealth opportunities this year.",
        "05_wealth_query_result.png",
    ),
    (
        "Health and wellness",
        "Analyze general health and wellness tendencies in this chart.",
        "06_health_query_result.png",
    ),
]

DISCIPLINE_BUTTONS = [
    ("ZiWei", 'button[onclick="calcZiWei()"]'),
    ("QiMen", 'button[onclick="calcQiMen()"]'),
    ("LiuRen", 'button[onclick="calcLiuRen()"]'),
    ("IChing", 'button[onclick="calcIChing()"]'),
    ("XuanKong", 'button[onclick="calcXuanKong()"]'),
    ("ZeJi", 'button[onclick="calcZeJi()"]'),
]


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


def _result(case: str, passed: bool, started: float, details: str) -> dict:
    return {
        "case": case,
        "passed": passed,
        "latency_ms": round((time.monotonic() - started) * 1000),
        "details": details,
    }


async def run_live_e2e(
    *,
    ui_url: str,
    backend_url: str,
    timeout_seconds: int,
) -> bool:
    """Run read-only UI checks and write the established E2E artifacts."""
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

    print("[INFO] Vercel UI live E2E diagnostics")
    print(f"[INFO] UI target: {ui_url}")
    print(f"[INFO] Backend target: {backend_url}")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timeout_ms = timeout_seconds * 1000
    results: list[dict] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await context.new_page()

        browser_error_counts = {"console": 0, "page": 0}

        def record_console(message) -> None:
            if message.type == "error":
                browser_error_counts["console"] += 1

        def record_page_error(_error) -> None:
            browser_error_counts["page"] += 1

        page.on("console", record_console)
        page.on("pageerror", record_page_error)

        started = time.monotonic()
        response = await page.goto(
            f"{ui_url}/", wait_until="networkidle", timeout=timeout_ms
        )
        status = response.status if response is not None else 0
        loaded = status == 200
        await page.screenshot(path=str(SCREENSHOT_DIR / "01_main_dashboard_loaded.png"))
        results.append(
            _result("1. Vercel UI dashboard load", loaded, started, f"HTTP {status}")
        )
        print(f"{'[OK]' if loaded else '[ERROR]'} Dashboard HTTP {status}")

        await page.fill("#birth_datetime", "1990-05-15 14:30:00")
        for index, (name, query, screenshot_name) in enumerate(QUERY_CASES, start=2):
            started = time.monotonic()
            passed = False
            response_length = 0
            try:
                reading = page.locator("#reading-body")
                previous_interpretation = (
                    await reading.inner_text() if await reading.count() else ""
                )
                await page.fill("#query", query)
                await page.click("#btn-submit")
                await page.wait_for_function(
                    """previous => {
                        const card = document.querySelector('#interpretation-card');
                        const reading = document.querySelector('#reading-body');
                        if (!card || !reading || card.classList.contains('hidden')) return false;
                        const current = (reading.textContent || '').trim();
                        return current.length > 50 && current !== previous;
                    }""",
                    arg=previous_interpretation.strip(),
                    timeout=timeout_ms,
                )
                interpretation = await page.inner_text("#reading-body")
                response_length = len(interpretation.strip())
                passed = response_length > 50
                await page.screenshot(path=str(SCREENSHOT_DIR / screenshot_name))
            except Exception:  # noqa: BLE001 - isolate one browser scenario
                passed = False
            results.append(
                _result(
                    f"{index}. Synthetic query - {name}",
                    passed,
                    started,
                    f"response_present={response_length > 50}",
                )
            )
            print(f"{'[OK]' if passed else '[ERROR]'} Synthetic query case {index}")

        started = time.monotonic()
        location_passed = False
        try:
            await page.fill("#location_search", "Bangkok")
            await page.click('button[onclick="resolveLocation()"]')
            await page.wait_for_function(
                "document.getElementById('longitude').value !== ''",
                timeout=timeout_ms,
            )
            longitude = float(await page.input_value("#longitude"))
            location_passed = 90.0 < longitude < 110.0
            await page.screenshot(path=str(SCREENSHOT_DIR / "07_location_resolved.png"))
        except Exception:  # noqa: BLE001 - isolate one browser scenario
            location_passed = False
        results.append(
            _result(
                "7. Synthetic location resolution",
                location_passed,
                started,
                f"resolved={location_passed}",
            )
        )
        print(f"{'[OK]' if location_passed else '[ERROR]'} Location resolution")

        started = time.monotonic()
        discipline_passed = 0
        for _name, selector in DISCIPLINE_BUTTONS:
            try:
                await page.click(selector, timeout=timeout_ms)
                discipline_passed += 1
            except Exception:  # noqa: BLE001, S112 - count optional button failures
                continue
        await page.screenshot(
            path=str(SCREENSHOT_DIR / "08_metaphysics_disciplines.png")
        )
        disciplines_ok = discipline_passed >= 5
        results.append(
            _result(
                "8. Metaphysics discipline buttons",
                disciplines_ok,
                started,
                f"passed={discipline_passed}/6",
            )
        )
        print(f"{'[OK]' if disciplines_ok else '[ERROR]'} Discipline buttons")

        for case_number, page_name, path in (
            (9, "Admin panel", "admin.html"),
            (10, "HITL review studio", "hitl.html"),
        ):
            started = time.monotonic()
            response = await page.goto(
                f"{ui_url}/{path}", wait_until="domcontentloaded", timeout=timeout_ms
            )
            status = response.status if response is not None else 0
            passed = status == 200
            results.append(
                _result(
                    f"{case_number}. {page_name} availability",
                    passed,
                    started,
                    f"HTTP {status}; content_not_recorded=true",
                )
            )
            print(f"{'[OK]' if passed else '[ERROR]'} {page_name} HTTP {status}")

        await browser.close()

    all_passed = all(item["passed"] for item in results)
    report = {
        "success": all_passed,
        "ui_url": ui_url,
        "backend_url": backend_url,
        "browser_error_counts": browser_error_counts,
        "results": results,
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    passed_count = sum(1 for item in results if item["passed"])
    print(f"[INFO] Results: {passed_count}/{len(results)} passed")
    print(
        "[INFO] Artifacts: project/tests/screenshots/live_e2e and live_e2e_report.json"
    )
    print(
        "[OK] E2E diagnostics passed"
        if all_passed
        else "[ERROR] E2E diagnostics failed"
    )
    return all_passed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Playwright diagnostics for the Vercel UI"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live", action="store_true", help="Enable live browser requests"
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
        print("[INFO] Offline dry run; no browser, network, or artifact write")
        print(f"[INFO] UI target: {ui_url}")
        print(f"[INFO] Backend target: {backend_url}")
        print(f"[OK] Planned E2E cases: {len(QUERY_CASES) + 5}")
        return 0

    return (
        0
        if asyncio.run(
            run_live_e2e(
                ui_url=ui_url,
                backend_url=backend_url,
                timeout_seconds=args.timeout,
            )
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
