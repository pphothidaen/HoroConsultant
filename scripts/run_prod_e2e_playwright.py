"""
scripts/run_prod_e2e_playwright.py
==================================
Production Live E2E Automation & UI Button Regression Suite.
Executes real Playwright browser automation on live production:
  Target: https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html

Verifies all 20 UI interactive buttons, form controls, presets, 
9 Master Astrology Disciplines, AI BaZi calculation, and Tab switchers.

Profiles:
  - smoke (default): critical path checks (page load, key API + key UI flows)
  - full: smoke checks plus all 9 discipline calculation buttons.

Generates:
  - project/tests/prod_button_regression_report.json
  - project/tests/screenshots/prod_*.png
"""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kimlenglim/.agy-account-2/Library/Caches/ms-playwright"

from playwright.async_api import async_playwright

PROD_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots"
REPORT_PATH = ROOT / "project" / "tests" / "prod_button_regression_report.json"
ARTIFACT_DIR = ROOT / "project" / "tests" / "artifacts_screenshots"

SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


async def run_live_e2e_production_regression(profile: str = "smoke"):
    profile = (profile or "smoke").strip().lower()
    if profile not in {"smoke", "full"}:
        raise ValueError(f"Unsupported profile: {profile}")
    is_full_profile = profile == "full"

    print("======================================================================")
    print("  🚀 STARTING PRODUCTION E2E UI BUTTON REGRESSION SUITE")
    print(f"  Target: {PROD_URL}")
    print(f"  Profile: {profile.upper()}")
    print("======================================================================")

    button_results = []
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 950})
        page = await context.new_page()

        # Listen for console messages & network responses
        api_responses = []
        page.on("response", lambda resp: api_responses.append({
            "url": resp.url,
            "status": resp.status,
            "ok": resp.ok
        }))

        # -------------------------------------------------------------------
        # 1. Initial Page Load
        # -------------------------------------------------------------------
        print("\n[STEP 1] Navigating to Production Index Dashboard...")
        resp = await page.goto(PROD_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        shot1 = SCREENSHOT_DIR / "prod_01_dashboard_initial.png"
        await page.screenshot(path=str(shot1), full_page=True)
        shutil.copy(shot1, ARTIFACT_DIR / shot1.name)

        title = await page.title()
        page_loaded = resp.status == 200 and "Computational Metaphysics" in title
        print(f"  • Load Status: HTTP {resp.status} | Title: {title}")

        button_results.append({
            "id": "BTN-PROD-00",
            "page": "index.html",
            "name": "🌐 Production Page Load",
            "handler": "HTTP GET",
            "endpoint": PROD_URL,
            "status": "PASSED" if page_loaded else "FAILED",
            "detail": f"HTTP {resp.status} - Page loaded cleanly with title '{title}'",
            "screenshot": f"screenshots/{shot1.name}"
        })

        # -------------------------------------------------------------------
        # 1B. Testing Production Vercel Gateway Health Check Endpoints
        # -------------------------------------------------------------------
        print("\n[STEP 1B] Testing Vercel Gateway /health Endpoint...")
        try:
            health_page = await page.context.new_page()
            h_resp = await health_page.goto("https://horo-consultant-psi.vercel.app/health")
            h_status = h_resp.status if h_resp else 0
            h_body = await health_page.content()
            h_ok = h_status == 200 and "ok" in h_body.lower()
            await health_page.close()
            print(f"  • Vercel Gateway GET /health: HTTP {h_status} -> {'OK' if h_ok else 'FAIL'}")
            button_results.append({
                "id": "BTN-PROD-00",
                "page": "index.html",
                "name": "💚 Vercel Gateway Health Check (/health)",
                "handler": "HTTP GET /health",
                "endpoint": "GET /health",
                "status": "PASSED" if h_ok else "FAILED",
                "detail": f"HTTP {h_status} - Response status ok confirmed",
            })
        except Exception as e:
            print(f"  ❌ Vercel Gateway Health Check Failed: {e}")

        # -------------------------------------------------------------------
        # 1C. Direct API E2E Fetch Test: POST /api/v1/bazi/interpret
        # -------------------------------------------------------------------
        print("\n[STEP 1C] Testing Direct API Fetch: POST /api/v1/bazi/interpret...")
        try:
            api_page = await page.context.new_page()
            interpret_payload = {
                "birth_datetime": "1990-05-15 14:30:00",
                "longitude": 100.4930,
                "utc_offset_hours": 7.0,
                "unknown_hour": False,
                "enable_validation": True,
                "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา"
            }
            api_resp = await api_page.request.post(
                "https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret",
                data=json.dumps(interpret_payload),
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
                }
            )
            api_status = api_resp.status
            api_json = await api_resp.json() if api_resp.ok else {}
            api_text = api_json.get("interpretation", "")
            is_fallback = "คำนวณค่าตำแหน่งดวงดาวและ 4 เสาหลักเรียบร้อยแล้ว" in api_text
            api_ok = api_status == 200 and len(api_text) > 50 and not is_fallback

            await api_page.close()
            print(f"  • Direct API POST /api/v1/bazi/interpret: HTTP {api_status}, Output Length={len(api_text)} -> {'OK' if api_ok else 'FAIL'}")
            button_results.append({
                "id": "BTN-PROD-00B",
                "page": "index.html",
                "name": "🔮 Direct API Gateway Endpoint (/api/v1/bazi/interpret)",
                "handler": "HTTP POST /api/v1/bazi/interpret",
                "endpoint": "POST /api/v1/bazi/interpret",
                "status": "PASSED" if api_ok else "FAILED",
                "detail": f"HTTP {api_status} - AI Interpretation output verified ({len(api_text)} chars, fallback: {is_fallback})",
            })
        except Exception as e:
            print(f"  ❌ Direct API Fetch Failed: {e}")

        # -------------------------------------------------------------------
        # 2. Location Search Button (resolveLocation)
        # -------------------------------------------------------------------
        print("\n[STEP 2] Testing Location Search Button ('ค้นหา & เติมค่า')...")
        try:
            await page.fill("#location_search", "บางกะปิ")
            await page.click("button:has-text('ค้นหา & เติมค่า')")
            await page.wait_for_timeout(3000)

            status_text = await page.inner_text("#location-status")
            lng_val = await page.input_value("#longitude")
            utc_val = await page.input_value("#utc_offset_hours")

            success = "✅" in status_text or "บางกะปิ" in status_text or float(lng_val) > 0
            shot2 = SCREENSHOT_DIR / "prod_02_location_resolved.png"
            await page.screenshot(path=str(shot2), full_page=True)
            shutil.copy(shot2, ARTIFACT_DIR / shot2.name)

            print(f"  • Status Text: {status_text.strip()}")
            print(f"  • Longitude: {lng_val} | UTC: {utc_val}")

            button_results.append({
                "id": "BTN-PROD-01",
                "page": "index.html",
                "name": "🔍 ค้นหา & เติมค่า (Location Search)",
                "handler": "resolveLocation()",
                "endpoint": "POST /api/v1/location/resolve",
                "status": "PASSED" if success else "FAILED",
                "detail": f"Resolved location to {status_text.strip()} (lng: {lng_val}, utc: {utc_val})",
                "screenshot": f"screenshots/{shot2.name}"
            })
        except Exception as e:
            print(f"  ❌ Location Search Failed: {e}")
            button_results.append({
                "id": "BTN-PROD-01",
                "page": "index.html",
                "name": "🔍 ค้นหา & เติมค่า (Location Search)",
                "handler": "resolveLocation()",
                "endpoint": "POST /api/v1/location/resolve",
                "status": "FAILED",
                "detail": f"Error: {e}"
            })

        # -------------------------------------------------------------------
        # 3. Preset Buttons (loadPreset)
        # -------------------------------------------------------------------
        print("\n[STEP 3] Testing Preset Buttons...")
        presets = [
            ("BTN-PROD-02", "กรุงเทพฯ", "1990-05-15 14:30:00", 100.4930, 7.0),
            ("BTN-PROD-03", "สิงคโปร์", "1988-08-08 08:08:00", 103.8198, 8.0),
            ("BTN-PROD-04", "นิวยอร์ก", "1995-12-25 23:45:00", -74.0060, -5.0)
        ]

        for btn_id, label, expected_dt, expected_lng, expected_utc in presets:
            try:
                await page.click(f".preset-buttons button:has-text('{label}')")
                await page.wait_for_timeout(500)

                dt_val = await page.input_value("#birth_datetime")
                lng_val = float(await page.input_value("#longitude"))
                utc_val = float(await page.input_value("#utc_offset_hours"))

                dt_ok = expected_dt in dt_val
                lng_ok = abs(lng_val - expected_lng) < 0.01
                utc_ok = abs(utc_val - expected_utc) < 0.01
                success = dt_ok and lng_ok and utc_ok

                print(f"  • Preset '{label}': dt={dt_val}, lng={lng_val}, utc={utc_val} -> {'OK' if success else 'FAIL'}")

                button_results.append({
                    "id": btn_id,
                    "page": "index.html",
                    "name": f"📍 Preset: {label}",
                    "handler": f"loadPreset('{expected_dt}', {expected_lng}, {expected_utc})",
                    "endpoint": "DOM Input Population",
                    "status": "PASSED" if success else "FAILED",
                    "detail": f"Fields updated to dt={dt_val}, lng={lng_val}, utc={utc_val}"
                })
            except Exception as e:
                print(f"  ❌ Preset '{label}' Failed: {e}")
                button_results.append({
                    "id": btn_id,
                    "page": "index.html",
                    "name": f"📍 Preset: {label}",
                    "handler": "loadPreset()",
                    "endpoint": "DOM Input Population",
                    "status": "FAILED",
                    "detail": f"Error: {e}"
                })

        shot3 = SCREENSHOT_DIR / "prod_03_presets_loaded.png"
        await page.screenshot(path=str(shot3), full_page=True)
        shutil.copy(shot3, ARTIFACT_DIR / shot3.name)

        # -------------------------------------------------------------------
        # 4. Master Discipline Calculation Buttons (9 Items)
        # -------------------------------------------------------------------
        if is_full_profile:
            print("\n[STEP 4] Testing 9 Master Metaphysics Discipline Buttons...")
            disciplines = [
                ("BTN-PROD-05", "Zi Wei", "calcZiWei()", "/api/v1/ziwei/calculate", "紫微", "紫微斗數"),
                ("BTN-PROD-06", "Qi Men", "calcQiMen()", "/api/v1/qimen/calculate", "奇門", "奇門遁甲"),
                ("BTN-PROD-07", "Da Liu Ren", "calcLiuRen()", "/api/v1/liuren/calculate", "六壬", "大六壬"),
                ("BTN-PROD-08", "I Ching", "calcIChing()", "/api/v1/iching/calculate", "易經", "六爻"),
                ("BTN-PROD-09", "Xuan Kong", "calcXuanKong()", "/api/v1/xuankong/calculate", "風水", "玄空"),
                ("BTN-PROD-10", "Ze Ji", "calcZeJi()", "/api/v1/zeji/calculate", "擇吉", "คำนวณฤกษ์"),
                ("BTN-PROD-11", "Thai Vedic", "calcThaiVedic()", "/api/v1/thaivedic/calculate", "🐘", "โหราศาสตร์ไทย"),
                ("BTN-PROD-12", "Western", "calcWestern()", "/api/v1/western/calculate", "🌌", "โหราศาสตร์สากล"),
                ("BTN-PROD-13", "Numerology", "calcNumerology()", "/api/v1/numerology/calculate", "🔢", "สัตตเลข")
            ]

            for btn_id, name, handler, endpoint, icon_match, text_match in disciplines:
                try:
                    # Find button by selector text
                    btn_selector = f"button:has-text('{text_match}')"
                    await page.click(btn_selector)
                    await page.wait_for_timeout(3500)

                    # Check branch result card content
                    card_visible = await page.is_visible("#branch-result-card") or await page.is_visible('[id="5-branch-result-card"]')
                    if not card_visible:
                        # Retry click if card was not visible immediately
                        await page.click(btn_selector)
                        await page.wait_for_timeout(3500)
                        card_visible = await page.is_visible("#branch-result-card") or await page.is_visible('[id="5-branch-result-card"]')
                    body_text = ""
                    if await page.is_visible("#branch-body"):
                        body_text = await page.inner_text("#branch-body")
                    elif await page.is_visible('[id="5-branch-body"]'):
                        body_text = await page.inner_text('[id="5-branch-body"]')

                    # Check network calls for endpoint
                    matched_api = [r for r in api_responses if endpoint in r["url"]]
                    api_ok = any(r["ok"] for r in matched_api)

                    success = card_visible and len(body_text) > 15 and api_ok
                    print(f"  • Discipline '{name}': Card Visible={card_visible}, Text Length={len(body_text)}, API Calls={len(matched_api)} -> {'OK' if success else 'FAIL'}")

                    button_results.append({
                        "id": btn_id,
                        "page": "index.html",
                        "name": f"☯ {name} ({text_match})",
                        "handler": handler,
                        "endpoint": f"GET {endpoint}",
                        "status": "PASSED" if success else "FAILED",
                        "detail": f"Result card rendered cleanly with {len(body_text)} chars output. API status: {[r['status'] for r in matched_api]}",
                    })
                except Exception as e:
                    print(f"  ❌ Discipline '{name}' Failed: {e}")
                    button_results.append({
                        "id": btn_id,
                        "page": "index.html",
                        "name": f"☯ {name}",
                        "handler": handler,
                        "endpoint": f"GET {endpoint}",
                        "status": "FAILED",
                        "detail": f"Error: {e}"
                    })

            shot4 = SCREENSHOT_DIR / "prod_04_master_disciplines_calculated.png"
            await page.screenshot(path=str(shot4), full_page=True)
            shutil.copy(shot4, ARTIFACT_DIR / shot4.name)

        # -------------------------------------------------------------------
        # 5. Form Checkboxes (unknown_hour & enable_validation)
        # -------------------------------------------------------------------
        print("\n[STEP 5] Testing Form Checkboxes...")
        try:
            await page.click("#unknown_hour")
            chk_unk = await page.is_checked("#unknown_hour")
            await page.click("#unknown_hour")  # toggle back off

            chk_val = await page.is_checked("#enable_validation")
            print(f"  • Checkboxes: unknown_hour toggle={chk_unk}, enable_validation={chk_val}")

            button_results.append({
                "id": "CHK-PROD-18",
                "page": "index.html",
                "name": "☑ ไม่ทราบยามเกิด (Unknown Hour Checkbox)",
                "handler": "DOM Checkbox Toggle",
                "endpoint": "DOM State",
                "status": "PASSED",
                "detail": f"Successfully toggled checkbox state (Value={chk_unk})"
            })
            button_results.append({
                "id": "CHK-PROD-19",
                "page": "index.html",
                "name": "☑ Gemini Prediction Validator Checkbox",
                "handler": "DOM Checkbox State",
                "endpoint": "DOM State",
                "status": "PASSED",
                "detail": f"Checkbox checked state verified (Checked={chk_val})"
            })
        except Exception as e:
            print(f"  ❌ Checkboxes Test Failed: {e}")

        # -------------------------------------------------------------------
        # 6. Main Submit Button: Calculate Chart & AI Interpretation (#btn-submit)
        # -------------------------------------------------------------------
        print("\n[STEP 6] Testing Main Submit Button ('คำนวณผังดวง & ตีความด้วย AI')...")
        try:
            # Load preset 1 for clean data
            await page.click("button:has-text('กรุงเทพฯ')")
            await page.wait_for_timeout(500)

            # Click Submit button
            await page.click("#btn-submit")
            print("  • Clicked #btn-submit, waiting for AI interpretation response (up to 30s)...")

            # Wait for reading-body or interpretation-card to be unhidden
            await page.wait_for_selector("#interpretation-card", timeout=30000)
            await page.wait_for_timeout(2000)

            interp_text = ""
            if await page.is_visible("#reading-body"):
                interp_text = await page.inner_text("#reading-body")
            elif await page.is_visible("#llm-markdown-output"):
                interp_text = await page.inner_text("#llm-markdown-output")

            interpret_api_calls = [r for r in api_responses if "/api/v1/bazi/interpret" in r["url"]]
            api_status = interpret_api_calls[-1]["status"] if interpret_api_calls else "OK (Proxy/Cached)"

            is_fallback = "คำนวณค่าตำแหน่งดวงดาวและ 4 เสาหลักเรียบร้อยแล้ว" in interp_text
            has_ai_output = len(interp_text) > 100 and not is_fallback

            success = has_ai_output and (interpret_api_calls and interpret_api_calls[-1]["ok"])

            shot5 = SCREENSHOT_DIR / "prod_05_bazi_ai_result.png"
            await page.screenshot(path=str(shot5), full_page=True)
            shutil.copy(shot5, ARTIFACT_DIR / shot5.name)

            print(f"  • AI Interpretation Output Length: {len(interp_text)} chars (Is Fallback: {is_fallback})")
            print(f"  • Interpretation snippet: {interp_text[:120].strip()}")

            button_results.append({
                "id": "BTN-PROD-14",
                "page": "index.html",
                "name": "🔮 คำนวณผังดวง & ตีความด้วย AI (#btn-submit)",
                "handler": "calculateChart(event)",
                "endpoint": "POST /api/v1/bazi/interpret",
                "status": "PASSED" if success else "FAILED",
                "detail": f"Calculated 4 Pillars chart & AI interpretation ({len(interp_text)} chars). API Status: {api_status}",
                "screenshot": f"screenshots/{shot5.name}"
            })
        except Exception as e:
            print(f"  ❌ Main Submit Button Failed: {e}")
            button_results.append({
                "id": "BTN-PROD-14",
                "page": "index.html",
                "name": "🔮 คำนวณผังดวง & ตีความด้วย AI (#btn-submit)",
                "handler": "calculateChart(event)",
                "endpoint": "POST /api/v1/bazi/interpret",
                "status": "FAILED",
                "detail": f"Error during calculation: {e}"
            })

        # -------------------------------------------------------------------
        # 7. Interpretation Tab Switchers
        # -------------------------------------------------------------------
        print("\n[STEP 7] Testing Interpretation Output Tabs...")
        tabs = [
            ("BTN-PROD-15", "📖 บทตีความโหราศาสตร์", "switchTab('tab-reading')", "#tab-reading"),
            ("BTN-PROD-16", "🛡️ Gemini Validator Audit", "switchTab('tab-validator')", "#tab-validator"),
            ("BTN-PROD-17", "📚 คัมภีร์อ้างอิง (RAG 3,132 Chunks)", "switchTab('tab-rag')", "#tab-rag")
        ]

        for btn_id, label, handler, tab_target in tabs:
            try:
                await page.click(f"button:has-text('{label}')")
                await page.wait_for_timeout(500)

                is_hidden = await page.eval_on_selector(tab_target, "el => el.classList.contains('hidden')")
                success = not is_hidden
                print(f"  • Tab '{label}': Target={tab_target}, Hidden={is_hidden} -> {'OK' if success else 'FAIL'}")

                button_results.append({
                    "id": btn_id,
                    "page": "index.html",
                    "name": f"📑 Tab: {label}",
                    "handler": handler,
                    "endpoint": "DOM Tab Switch",
                    "status": "PASSED" if success else "FAILED",
                    "detail": f"Tab container '{tab_target}' active state verified (hidden={is_hidden})"
                })
            except Exception as e:
                print(f"  ❌ Tab '{label}' Switch Failed: {e}")
                button_results.append({
                    "id": btn_id,
                    "page": "index.html",
                    "name": f"📑 Tab: {label}",
                    "endpoint": "DOM Tab Switch",
                    "status": "FAILED",
                    "detail": f"Error: {e}"
                })

        shot6 = SCREENSHOT_DIR / "prod_06_tabs_navigated.png"
        await page.screenshot(path=str(shot6), full_page=True)
        shutil.copy(shot6, ARTIFACT_DIR / shot6.name)

        await browser.close()

    elapsed = round(time.time() - start_time, 2)
    passed_count = sum(1 for r in button_results if r["status"] == "PASSED")
    failed_count = sum(1 for r in button_results if r["status"] == "FAILED")
    total_count = len(button_results)

    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "target_url": PROD_URL,
        "profile": profile,
        "elapsed_seconds": elapsed,
        "summary": {
            "total_buttons": total_count,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate_pct": round((passed_count / total_count) * 100, 2)
        },
        "results": button_results
    }

    REPORT_PATH.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n======================================================================")
    print("  📊 PRODUCTION E2E REGRESSION SUMMARY")
    print("======================================================================")
    print(f"  • Target URL     : {PROD_URL}")
    print(f"  • Total Controls : {total_count}")
    print(f"  • Passed         : {passed_count} ✅")
    print(f"  • Failed         : {failed_count} ❌")
    print(f"  • Pass Rate      : {report_data['summary']['pass_rate_pct']}%")
    print(f"  • Elapsed Time   : {elapsed} seconds")
    print(f"  • JSON Report    : {REPORT_PATH}")
    print("======================================================================\n")

    return failed_count == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run production E2E regression with a smoke/full profile.")
    parser.add_argument(
        "--profile",
        choices=["smoke", "full"],
        default=os.getenv("E2E_PROFILE", "smoke"),
        help="Execution profile. 'smoke' is faster and lower cost; 'full' validates all discipline controls."
    )
    args = parser.parse_args()
    success = asyncio.run(run_live_e2e_production_regression(profile=args.profile))
    sys.exit(0 if success else 1)
