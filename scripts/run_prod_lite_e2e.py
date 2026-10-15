"""Production E2E Playwright Suite for Horo Lite (TICKET-HLITE-014).

Executes live production browser automation against:
  https://horo-consultant-psi.vercel.app/lite.html

Scenarios:
  A. Success Scenario (พร้อมคำทำนาย):
     - Route interception for /api/v3/unified-reading returning realistic 12-topic UnifiedReadingResponse
     - Complete form filling (birth date, time, place, gender, target year)
     - Loading state verification
     - Exact 12 topic cards sequence matching CANONICAL_TOPIC_IDS
     - Thai prediction copy (คำทำนาย) verification
     - Score gauges text alternatives (role="img", aria-label, gauge-value)
     - Past pattern calibration chips and tone note update
     - Export actions verification (Full PNG, Story 9:16 PNG, Copy summary, Print)
     - Screenshot: project/tests/screenshots/prod_lite_e2e_success.png
  B. Failed Scenario (Fail-Closed & Resilient Recovery):
     - Route interception returning HTTP 503 (backend unavailable / sleeping)
     - Error state display in #status-message with is-error class
     - Accessible #result-retry button appearance
     - Retry click retaining payload and re-triggering submission
     - Screenshot: project/tests/screenshots/prod_lite_e2e_failed.png
  C. JSON report: project/tests/prod_lite_e2e_report.json

Enforces pure ASCII output: [OK], [ERROR], [WARNING], [INFO].
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.unified_reading_engine import CANONICAL_TOPIC_IDS

DEFAULT_PROD_URL = "https://horo-consultant-psi.vercel.app/lite.html"
TARGET_URL = os.getenv("HORO_LITE_URL", DEFAULT_PROD_URL)
SCREENSHOT_DIR = ROOT / "project" / "tests" / "screenshots"
REPORT_PATH = ROOT / "project" / "tests" / "prod_lite_e2e_report.json"

SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def build_mock_unified_reading_payload(target_year: int = 2026) -> dict[str, Any]:
    """Build a comprehensive, schema-compliant UnifiedReadingResponse with Thai prediction text."""
    topic_configs = [
        (
            "personal_overview_strengths",
            "ภาพรวมและจุดแข็งส่วนบุคคล (Personal Overview & Strengths)",
            "ภาพรวมดวงชะตาปี 2026 มีพลังดาวเกื้อหนุนโดดเด่น ธาตุไฟเสริมพลังความคิดสร้างสรรค์และภาวะผู้นำ จุดแข็งคือการตัดสินใจที่เฉียบคมและการปรับตัวเข้ากับสถานการณ์ใหม่ได้อย่างรวดเร็ว",
            "ใช้จุดแข็งด้านการสื่อสารและการวางแผนเชิงกลยุทธ์เพื่อสร้างผลงานในช่วงครึ่งปีแรก โดยเฉพาะโครงการที่ต้องใช้ความคิดริเริ่ม",
            "HIGH",
            ["suriyayart_ascendant", "bazi_day_master", "annual_transit_jupiter"],
        ),
        (
            "past_pattern_calibration",
            "การสอบเทียบรูปแบบอดีต (Past Pattern Calibration)",
            "พบรูปแบบการเปลี่ยนแปลงสำคัญในช่วงอายุ 28-30 ปี (2018-2020) สอดคล้องกับจังหวะดาวเสาร์ย้ายและรอบวัยจรใหญ่ที่มีการเปลี่ยนผ่านบทบาทหน้าที่การงาน",
            "ตรวจสอบเหตุการณ์ในอดีตเพื่อเทียบเคียงความแม่นยำของแบบจำลองและปรับน้ำเสียงคำทำนายให้สอดคล้องกับประสบการณ์จริงของคุณ",
            "HIGH",
            ["past_cycle_saturn_return", "decade_luck_pillar_shift"],
        ),
        (
            "annual_overview",
            "ภาพรวมรายปี 2026 (Annual Overview)",
            "ปี 2026 เป็นปีแห่งการขยายตัวและการลงหลักปักฐาน จังหวะชีวิตโดยรวมเฉลี่ย 8.2/10 ช่วงเวลาที่ดีที่สุดอยู่ในไตรมาสที่สองซึ่งพลังงานดาวศุภเคราะห์ทำมุมส่งเสริมเต็มที่",
            "ควรกำหนดเป้าหมายใหญ่ให้ชัดเจนตั้งแต่ต้นปี และเตรียมแผนสำรองสำหรับไตรมาสสี่เพื่อรองรับความผันผวนระยะสั้น",
            "HIGH",
            ["tai_sui_harmony", "solar_year_ruler", "annual_timing_v3"],
        ),
        (
            "career_business",
            "การงานและธุรกิจ (Career & Business)",
            "ทิศทางการงานมีความก้าวหน้าสูง ได้รับโอกาสในการรับผิดชอบโครงการสำคัญหรือเลื่อนตำแหน่ง ผู้ใหญ่และผู้ร่วมงานให้การสนับสนุนอย่างดียิ่ง",
            "เดือนที่ 5 และ 6 เป็นจังหวะทองในการเจรจาต่อรอง ขยายธุรกิจ หรือเปิดตัวผลิตภัณฑ์ใหม่ ควรเร่งลงมือสร้างความสำเร็จในช่วงนี้",
            "HIGH",
            ["career_palace_auspicious", "officer_star_prominent"],
        ),
        (
            "finance",
            "การเงินและโชคลาภ (Finance)",
            "กระแสการเงินหมุนเวียนคล่องตัว รายได้หลักมั่นคงและมีเกณฑ์ได้รับผลตอบแทนพิเศษจากการลงทุนระยะยาว แต่ควรระวังรายจ่ายจรเกี่ยวกับที่อยู่อาศัย",
            "ควรเน้นการออมและการลงทุนที่มีความเสี่ยงปานกลาง หลีกเลี่ยงการเก็งกำไรที่มีความผันผวนสูงในเดือน 9",
            "MEDIUM",
            ["wealth_star_strength", "treasury_combination"],
        ),
        (
            "love_relationships",
            "ความรักและความสัมพันธ์ (Love & Relationships)",
            "ความสัมพันธ์มีความเข้าอกเข้าใจกันมากขึ้น คนโสดมีโอกาสพบคนถูกใจจากแวดวงการงานหรือกิจกรรมทางสังคม คนมีคู่ความสัมพันธ์ราบรื่นและมั่นคง",
            "ให้เวลาและรับฟังคู่ครองอย่างลึกซึ้ง เดือนที่ 8 เหมาะแก่การเดินทางร่วมกันเพื่อกระชับความสัมพันธ์",
            "HIGH",
            ["peach_blossom_balance", "spouse_palace_peace"],
        ),
        (
            "health_wellbeing",
            "สุขภาพและสุขภาวะ (Health & Wellbeing)",
            "สุขภาพร่างกายโดยรวมแข็งแรง ควรระวังความตึงเครียดสะสมจากภาระงานหนักและอาการเมื่อยล้ากล้ามเนื้อออฟฟิศซินโดรม",
            "จัดสรรเวลาพักผ่อนให้เพียงพอ ออกกำลังกายสม่ำเสมอ และตรวจสุขภาพประจำปีช่วงกลางปี",
            "MEDIUM",
            ["vitality_indicator", "stress_cycle_transit"],
        ),
        (
            "family_surrounding_people",
            "ครอบครัวและคนรอบข้าง (Family & Surrounding People)",
            "บรรยากาศในครอบครัวอบอุ่น มีเกณฑ์ได้ร่วมงานมงคลหรือเฉลิมฉลองความสำเร็จของคนใกล้ชิด ผู้ใหญ่ในครอบครัวให้พรและความช่วยเหลือ",
            "สร้างเวลาคุณภาพร่วมกับสมาชิกในครอบครัว และหลีกเลี่ยงการนำความตึงเครียดจากเรื่องงานกลับเข้าบ้าน",
            "HIGH",
            ["family_palace_harmony", "benefactor_star"],
        ),
        (
            "opportunities_caution_periods",
            "ช่วงโอกาสและช่วงควรระวัง (Opportunities & Caution Periods)",
            "ช่วงจังหวะเกื้อหนุนสูงสุดคือเดือนพฤษภาคมและมิถุนายน (เดือน 5-6) ช่วงที่ควรเพิ่มความรอบคอบคือเดือนกันยายน (เดือน 9) เนื่องจากมีดาวหักเหทำมุมเล็ง",
            "เร่งผลักดันงานสำคัญในช่วงโอกาส และชะลอการตัดสินใจเรื่องเอกสารสัญญาสำคัญในช่วงระวัง",
            "HIGH",
            ["planetary_aspects_peak", "void_transit_window"],
        ),
        (
            "twelve_month_roadmap",
            "แผนผังรายเดือน 12 เดือน (Twelve Month Roadmap)",
            "การกระจายคะแนน 12 เดือนครอบคลุมมิติงาน เงิน และความรัก ชี้ให้เห็นแนวโน้มเชิงบวกต่อเนื่องตลอดทั้งปี 2026 โดยมีจุดพีคช่วงกลางปี",
            "ใช้คะแนนรายเดือนเป็นเข็มทิศในการจัดสรรพลังงาน วางแผนการเงินล่วงหน้า และบริหารความสัมพันธ์อย่างสมดุล",
            "HIGH",
            ["consensus_monthly_distribution", "solar_lunar_matrix"],
        ),
        (
            "top_priorities_cautions",
            "ลำดับความสำคัญและข้อควรระวัง (Top Priorities & Cautions)",
            "โฟกัสสูงสุดอยู่ที่การพัฒนาทักษะวิชาชีพและการสร้างพันธมิตรธุรกิจ ข้อควรระวังสำคัญคือการรักษาวินัยการใช้จ่ายและไม่ลงทุนเกินตัวช่วงปลายปี",
            "ยึดมั่นในความซื่อสัตย์และความรอบคอบ จะช่วยให้ผ่านพ้นช่วงทดสอบและคว้าโอกาสสำคัญได้อย่างเต็มศักยภาพ",
            "HIGH",
            ["priority_ranking_algorithm", "risk_mitigation_vector"],
        ),
        (
            "export_sharing_actions",
            "การส่งออกและแบ่งปัน (Export & Sharing Actions)",
            "รายงานสรุปดวงชะตาฉบับ Lite พร้อมส่งออกเป็นภาพแนวตั้งความละเอียดสูง รูปแบบ Story 9:16 หรือข้อความสรุปสำหรับแชร์",
            "สามารถเลือกเปิดหรือปิดการแสดงข้อมูลวันเกิดเพื่อรักษาความเป็นส่วนตัวตามมาตรฐาน PDPA",
            "HIGH",
            ["export_engine_v1", "social_card_manifest"],
        ),
    ]

    topics = [
        {
            "topic_id": t[0],
            "order": idx,
            "title": t[1],
            "summary": t[2],
            "guidance": t[3],
            "confidence": t[4],
            "evidence_refs": t[5],
        }
        for idx, t in enumerate(topic_configs, start=1)
    ]

    monthly_scores = []
    career_profile = [7, 8, 8, 9, 9, 8, 7, 8, 6, 7, 8, 9]
    finance_profile = [7, 7, 8, 8, 9, 8, 7, 7, 6, 7, 8, 8]
    love_profile = [8, 8, 7, 8, 8, 9, 8, 9, 7, 8, 8, 8]

    for m in range(1, 13):
        monthly_scores.append({
            "month": m,
            "career_score": career_profile[m - 1],
            "finance_score": finance_profile[m - 1],
            "love_score": love_profile[m - 1],
            "confidence": "HIGH",
            "score_basis": {
                "annual_transit": "favorable_jupiter_trine",
                "element_balance": "fire_wood_generation",
            },
            "reasons": [
                f"สถิติเดือนที่ {m} ได้รับแรงเกื้อหนุนจากรอบดาวประจำปี",
                "ทิศทางพลังงานธาตุส่งเสริมความมั่นคงและการตัดสินใจ",
            ],
        })

    past_patterns = [
        {
            "pattern_id": "pattern-2018-career",
            "year_range": [2018, 2020],
            "age_range": [28, 30],
            "theme": "career_shift",
            "deterministic_basis": [
                "saturn_transit_tenth_house",
                "jupiter_opposition_cycle",
            ],
            "sensitive_category": False,
            "allowed_feedback": ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
            "user_feedback": None,
        },
        {
            "pattern_id": "pattern-2021-relocation",
            "year_range": [2021, 2023],
            "age_range": [31, 33],
            "theme": "relocation",
            "deterministic_basis": [
                "travel_star_movement",
                "fourth_house_transit",
            ],
            "sensitive_category": False,
            "allowed_feedback": ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
            "user_feedback": None,
        },
    ]

    return {
        "schema_version": "horo_lite_unified_reading.v1",
        "request_id": f"unified-reading-e2e-prod-{target_year}",
        "target_year": target_year,
        "topics": topics,
        "monthly_scores": monthly_scores,
        "past_patterns": past_patterns,
        "consensus_metadata": {
            "consensus_score": 0.94,
            "arbitration_status": "CONSENSUS_REACHED",
            "engine_version": "v3.1.0",
        },
        "hitl_flags": {
            "required_human_review": False,
            "uncertain_birth_time": False,
            "tradition_conflict": False,
            "force_human_review": False,
            "low_consensus": False,
        },
        "hitl_routing": {
            "status": "NOT_REQUIRED",
        },
        "llm_metadata": {
            "facts_mutable_by_llm": False,
            "model": "gemini-2.5-flash",
            "inference_verified": True,
        },
    }


async def run_success_scenario(page: Page, url: str) -> dict[str, Any]:
    """Execute Scenario A: Success Scenario พร้อมคำทำนาย."""
    print("\n------------------------------------------------------------")
    print("[INFO] Starting Scenario A: Success Scenario (พร้อมคำทำนาย)")
    print(f"[INFO] Target URL: {url}")
    print("------------------------------------------------------------")

    scenario_result: dict[str, Any] = {
        "scenario": "success_scenario",
        "name": "Success Scenario (พร้อมคำทำนาย)",
        "status": "FAILED",
        "checks": [],
    }

    mock_data = build_mock_unified_reading_payload(target_year=2026)
    intercepted_requests: list[dict[str, Any]] = []

    async def route_handler(route):
        req = route.request
        try:
            body = json.loads(req.post_data) if req.post_data else {}
        except Exception:
            body = {}
        intercepted_requests.append({
            "url": req.url,
            "method": req.method,
            "body": body,
        })
        # Add brief latency to verify loading message deterministically
        await asyncio.sleep(0.5)
        await route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_data, ensure_ascii=False),
        )

    await page.route("**/api/v3/unified-reading*", route_handler)

    # 1. Navigation
    print("[INFO] Navigating to target page...")
    resp = await page.goto(url, wait_until="networkidle", timeout=30000)
    page_status = resp.status if resp else 0
    page_title = await page.title()
    assert page_status == 200, f"Expected HTTP 200, got {page_status}"
    assert "Horo Lite" in page_title or "HoroConsultant" in page_title, f"Unexpected title: {page_title}"
    print(f"[OK] Page loaded successfully: HTTP {page_status} | Title: {page_title}")
    scenario_result["checks"].append({
        "check": "page_load",
        "status": "PASSED",
        "detail": f"HTTP {page_status} | Title: {page_title}",
    })

    # 2. Fill Form
    print("[INFO] Filling form inputs: 1990-05-15 08:30, กรุงเทพมหานคร, gender ไม่ระบุ, target year 2026...")
    await page.fill("#birth_date", "1990-05-15")
    await page.fill("#birth_time", "08:30")
    await page.fill("#birth_place", "กรุงเทพมหานคร")
    await page.select_option("#gender_at_birth", value="")
    await page.fill("#target_year", "2026")

    bdate_val = await page.input_value("#birth_date")
    btime_val = await page.input_value("#birth_time")
    bplace_val = await page.input_value("#birth_place")
    tyear_val = await page.input_value("#target_year")
    assert bdate_val == "1990-05-15", f"birth_date mismatch: {bdate_val}"
    assert btime_val == "08:30", f"birth_time mismatch: {btime_val}"
    assert bplace_val == "กรุงเทพมหานคร", f"birth_place mismatch: {bplace_val}"
    assert tyear_val == "2026", f"target_year mismatch: {tyear_val}"
    print("[OK] Form values populated and verified successfully")
    scenario_result["checks"].append({
        "check": "form_fill",
        "status": "PASSED",
        "detail": "birth_date=1990-05-15, birth_time=08:30, birth_place=กรุงเทพมหานคร, target_year=2026",
    })

    # 3. Submit and verify loading state
    print("[INFO] Submitting reading request...")
    submit_button = page.locator("#submit-reading")
    assert await submit_button.is_visible(), "Submit button #submit-reading not visible"
    await submit_button.click()

    loading_message = await page.locator("#status-message").text_content()
    print(f"[OK] Loading message captured: {loading_message}")
    assert "กำลังส่งข้อมูล" in (loading_message or ""), f"Loading message did not contain expected text: {loading_message}"
    scenario_result["checks"].append({
        "check": "loading_state_message",
        "status": "PASSED",
        "detail": loading_message,
    })

    # 4. Wait for results & verify exact 12 topic cards in CANONICAL_TOPIC_IDS sequence
    print("[INFO] Waiting for 12 topic cards in #topics-container...")
    await page.wait_for_selector("#topics-container > article", timeout=15000)
    topic_cards = await page.locator("#topics-container > article").all()
    assert len(topic_cards) == 12, f"Expected exactly 12 topic cards, found {len(topic_cards)}"
    print(f"[OK] Exactly 12 direct topic cards found in #topics-container")

    card_labels: list[str] = []
    for idx, expected_id in enumerate(CANONICAL_TOPIC_IDS):
        card = topic_cards[idx]
        aria_label = await card.get_attribute("aria-labelledby")
        expected_label = f"topic-{expected_id}"
        assert aria_label == expected_label, (
            f"Topic card sequence mismatch at index {idx}: expected {expected_label}, got {aria_label}"
        )
        card_labels.append(aria_label or "")

        # 5. Verify prediction copy (คำทำนาย) rendered inside topic card
        copy_el = card.locator("p.topic-copy")
        copy_text = (await copy_el.text_content() or "").strip()
        assert len(copy_text) >= 10, f"Topic {expected_id} missing prediction copy: {copy_text}"

    print(f"[OK] All 12 cards match exact CANONICAL_TOPIC_IDS sequence with Thai prediction copy")
    scenario_result["checks"].append({
        "check": "canonical_topic_cards_sequence",
        "status": "PASSED",
        "detail": card_labels,
    })
    scenario_result["checks"].append({
        "check": "prediction_copy_rendered",
        "status": "PASSED",
        "detail": "Thai prediction copy verified across all 12 topic cards",
    })

    # 6. Verify score gauges text alternatives (role="img", aria-label, gauge value)
    print("[INFO] Verifying score gauges text alternatives...")
    score_gauges = await page.locator(".score-gauge[role='img']").all()
    assert len(score_gauges) >= 36, f"Expected at least 36 score gauges (12x3), found {len(score_gauges)}"
    for g_idx, gauge in enumerate(score_gauges[:6]):
        role_attr = await gauge.get_attribute("role")
        aria_label = await gauge.get_attribute("aria-label")
        gauge_val = (await gauge.locator(".gauge-value").text_content() or "").strip()
        assert role_attr == "img", f"Gauge {g_idx} missing role='img'"
        assert aria_label and "คะแนน" in aria_label, f"Gauge {g_idx} missing valid aria-label: {aria_label}"
        assert gauge_val and gauge_val.isdigit(), f"Gauge {g_idx} missing numeric gauge-value: {gauge_val}"

    print(f"[OK] Score gauges verified: role='img', aria-label, gauge-value ({len(score_gauges)} total gauges)")
    scenario_result["checks"].append({
        "check": "score_gauges_accessibility",
        "status": "PASSED",
        "detail": f"{len(score_gauges)} score gauges verified with role='img', aria-label, gauge-value",
    })

    # 7. Verify past pattern calibration chips & tone note update
    print("[INFO] Verifying past pattern calibration chips and interactive tone note update...")
    pattern_card = page.locator("article[aria-labelledby='topic-past_pattern_calibration']")
    chips = await pattern_card.locator(".chip").all()
    chip_texts = [await c.text_content() for c in chips]
    expected_chips = {"ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"}
    assert expected_chips.issubset(set(chip_texts)), f"Missing expected feedback chips: {chip_texts}"

    # Click chip "ตรง"
    chip_match = pattern_card.locator("button.chip[data-choice='ตรง']").first
    await chip_match.click()
    await chip_match.dispatch_event("Click")

    pressed_state = await chip_match.get_attribute("aria-pressed")
    emphasis_badge = pattern_card.locator(".pattern-item .pattern-feedback-emphasis")
    emphasis_text = (await emphasis_badge.text_content() or "").strip()
    indicator_text = (await page.locator("#feedback-emphasis-indicator").text_content() or "").strip()

    assert pressed_state == "true", f"Chip aria-pressed not true: {pressed_state}"
    assert "ตรง" in emphasis_text and "น้ำเสียง" in emphasis_text, f"Unexpected emphasis text: {emphasis_text}"
    assert "💡 การปรับน้ำเสียงคำอธิบาย" in indicator_text, f"Unexpected indicator text: {indicator_text}"
    print(f"[OK] Past pattern calibration chips verified: pressed={pressed_state}, badge='{emphasis_text}'")
    scenario_result["checks"].append({
        "check": "past_pattern_calibration_chips",
        "status": "PASSED",
        "detail": f"Chips: {chip_texts} | Selected: ตรง | Badge: {emphasis_text} | Indicator: {indicator_text}",
    })

    # 8. Verify export actions exist
    print("[INFO] Verifying export action buttons...")
    export_card = page.locator("article[aria-labelledby='topic-export_sharing_actions']")
    btn_full = export_card.locator("#export-full")
    btn_story = export_card.locator("#export-story")
    btn_copy = export_card.locator("#copy-summary")
    btn_print = export_card.locator("#print-summary")

    assert await btn_full.is_visible(), "Export Full PNG button #export-full missing"
    assert await btn_story.is_visible(), "Export Story 9:16 button #export-story missing"
    assert await btn_copy.is_visible(), "Copy summary button #copy-summary missing"
    assert await btn_print.is_visible(), "Print summary button #print-summary missing"

    full_txt = await btn_full.text_content()
    story_txt = await btn_story.text_content()
    copy_txt = await btn_copy.text_content()
    print(f"[OK] Export buttons verified: Full ('{full_txt}'), Story ('{story_txt}'), Copy ('{copy_txt}')")
    scenario_result["checks"].append({
        "check": "export_actions_available",
        "status": "PASSED",
        "detail": ["#export-full", "#export-story", "#copy-summary", "#print-summary"],
    })

    # 9. Screenshot
    shot_path = SCREENSHOT_DIR / "prod_lite_e2e_success.png"
    await page.screenshot(path=str(shot_path), full_page=True)
    assert shot_path.exists() and shot_path.stat().st_size > 0, "Screenshot not created"
    print(f"[OK] Success screenshot captured: {shot_path.relative_to(ROOT)} ({shot_path.stat().st_size} bytes)")
    scenario_result["checks"].append({
        "check": "success_screenshot",
        "status": "PASSED",
        "detail": str(shot_path.relative_to(ROOT)),
    })

    # Clean up route
    await page.unroute("**/api/v3/unified-reading*")

    scenario_result["status"] = "PASSED"
    print("[OK] Scenario A (Success Scenario) PASSED 100%")
    return scenario_result


async def run_failed_scenario(page: Page, url: str) -> dict[str, Any]:
    """Execute Scenario B: Failed Scenario (Fail-Closed & Resilient Recovery)."""
    print("\n------------------------------------------------------------")
    print("[INFO] Starting Scenario B: Failed Scenario (Fail-Closed & Recovery)")
    print(f"[INFO] Target URL: {url}")
    print("------------------------------------------------------------")

    scenario_result: dict[str, Any] = {
        "scenario": "failed_scenario",
        "name": "Failed Scenario (Fail-Closed & Resilient Recovery)",
        "status": "FAILED",
        "checks": [],
    }

    call_count = 0
    intercepted_payloads: list[dict[str, Any]] = []

    async def fail_then_recover_route(route):
        nonlocal call_count
        call_count += 1
        req = route.request
        try:
            body = json.loads(req.post_data) if req.post_data else {}
        except Exception:
            body = {}
        intercepted_payloads.append(body)

        if call_count == 1:
            # First attempt: fail closed with 503
            await route.fulfill(
                status=503,
                content_type="application/json",
                body=json.dumps({"detail": "Service Unavailable - Backend waking up / cold start"}),
            )
        else:
            # Second attempt (retry): succeed
            mock_data = build_mock_unified_reading_payload(target_year=2026)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(mock_data, ensure_ascii=False),
            )

    await page.route("**/api/v3/unified-reading*", fail_then_recover_route)

    # 1. Navigation
    print("[INFO] Navigating to target page...")
    resp = await page.goto(url, wait_until="networkidle", timeout=30000)
    page_status = resp.status if resp else 0
    assert page_status == 200, f"Expected HTTP 200, got {page_status}"
    print(f"[OK] Page loaded: HTTP {page_status}")
    scenario_result["checks"].append({
        "check": "page_load",
        "status": "PASSED",
        "detail": f"HTTP {page_status}",
    })

    # 2. Fill Form
    print("[INFO] Populating form for failure scenario...")
    await page.fill("#birth_date", "1990-05-15")
    await page.fill("#birth_time", "08:30")
    await page.fill("#birth_place", "กรุงเทพมหานคร")
    await page.fill("#target_year", "2026")

    # 3. Submit and verify 503 fail-closed error handling
    print("[INFO] Submitting form (expecting 503 failure)...")
    await page.click("#submit-reading")

    await page.wait_for_selector("#status-message.is-error", timeout=10000)
    status_el = page.locator("#status-message")
    status_text = (await status_el.text_content() or "").strip()
    status_classes = await status_el.get_attribute("class") or ""

    assert "is-error" in status_classes, f"#status-message missing is-error class: {status_classes}"
    assert "Service Unavailable" in status_text, f"#status-message missing failure detail: {status_text}"
    print(f"[OK] Fail-closed state verified: #status-message.is-error with text: '{status_text}'")
    scenario_result["checks"].append({
        "check": "fail_closed_error_message",
        "status": "PASSED",
        "detail": f"class='{status_classes}' | text='{status_text}'",
    })

    # 4. Verify retry button is accessible and visible
    retry_button = page.locator("#result-retry")
    assert await retry_button.is_visible(), "Retry button #result-retry is not visible"
    retry_classes = await retry_button.get_attribute("class") or ""
    assert "hidden" not in retry_classes, f"Retry button should not be hidden: {retry_classes}"
    print("[OK] #result-retry button is visible, accessible, and not hidden")
    scenario_result["checks"].append({
        "check": "retry_button_accessible",
        "status": "PASSED",
        "detail": f"visible=True | class='{retry_classes}'",
    })

    # 5. Capture failed screenshot
    shot_path = SCREENSHOT_DIR / "prod_lite_e2e_failed.png"
    await page.screenshot(path=str(shot_path), full_page=True)
    assert shot_path.exists() and shot_path.stat().st_size > 0, "Failed screenshot not created"
    print(f"[OK] Failed state screenshot captured: {shot_path.relative_to(ROOT)} ({shot_path.stat().st_size} bytes)")
    scenario_result["checks"].append({
        "check": "failed_screenshot",
        "status": "PASSED",
        "detail": str(shot_path.relative_to(ROOT)),
    })

    # 6. Verify clicking retry retains payload and re-triggers submission
    print("[INFO] Clicking #result-retry button to test payload retention and resubmission...")
    await retry_button.click()

    # Wait for recovery success
    await page.wait_for_selector("#topics-container > article", timeout=15000)
    recovered_cards = await page.locator("#topics-container > article").count()
    assert recovered_cards == 12, f"Expected 12 cards after retry recovery, got {recovered_cards}"

    assert call_count >= 2, f"Expected at least 2 API calls (initial + retry), got {call_count}"
    assert len(intercepted_payloads) >= 2, "Expected at least 2 intercepted payloads"
    payload_1 = intercepted_payloads[0]
    payload_2 = intercepted_payloads[1]

    # Verify identical core payload fields
    for field in ("birth_date", "birth_time", "birth_place", "target_year"):
        assert payload_1.get(field) == payload_2.get(field), (
            f"Payload field '{field}' modified during retry: {payload_1.get(field)} vs {payload_2.get(field)}"
        )

    print(f"[OK] Resubmission verified: identical payload retained and recovered to 12 topic cards")
    scenario_result["checks"].append({
        "check": "retry_payload_retention_and_recovery",
        "status": "PASSED",
        "detail": f"call_count={call_count} | payload_identical=True | recovered_cards={recovered_cards}",
    })

    # Clean up route
    await page.unroute("**/api/v3/unified-reading*")

    scenario_result["status"] = "PASSED"
    print("[OK] Scenario B (Failed Scenario) PASSED 100%")
    return scenario_result


async def run_prod_lite_e2e_suite(target_url: str = TARGET_URL, headless: bool = True) -> int:
    """Run full production E2E suite covering both success and failed scenarios."""
    print("======================================================================")
    print("  HORO CONSULTANT - PRODUCTION LITE E2E AUTOMATION SUITE")
    print(f"  Target: {target_url}")
    print(f"  Headless: {headless}")
    print("======================================================================")

    start_time = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="th-TH",
        )

        try:
            # Scenario A: Success Scenario
            page_a = await context.new_page()
            res_a = await run_success_scenario(page_a, target_url)
            results.append(res_a)
            await page_a.close()

            # Scenario B: Failed Scenario
            page_b = await context.new_page()
            res_b = await run_failed_scenario(page_b, target_url)
            results.append(res_b)
            await page_b.close()

        finally:
            await context.close()
            await browser.close()

    end_time = datetime.now(timezone.utc)
    duration_s = (end_time - start_time).total_seconds()

    all_passed = all(r.get("status") == "PASSED" for r in results)
    final_status = "ALL_PASSED_READY_FOR_PROD" if all_passed else "FAILED"

    report = {
        "timestamp": end_time.isoformat(),
        "ticket_id": "TICKET-HLITE-014",
        "target_url": target_url,
        "duration_seconds": round(duration_s, 2),
        "status": final_status,
        "scenarios": results,
        "screenshots": [
            str((SCREENSHOT_DIR / "prod_lite_e2e_success.png").relative_to(ROOT)),
            str((SCREENSHOT_DIR / "prod_lite_e2e_failed.png").relative_to(ROOT)),
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print("\n======================================================================")
    print(f"[OK] Execution report written to: {REPORT_PATH.relative_to(ROOT)}")
    print(f"[OK] Overall Suite Status: {final_status} (Duration: {duration_s:.2f}s)")
    print("======================================================================")

    return 0 if all_passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Production E2E Playwright Suite for Horo Lite")
    parser.add_argument("--url", default=TARGET_URL, help=f"Target URL (default: {TARGET_URL})")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()

    exit_code = asyncio.run(run_prod_lite_e2e_suite(target_url=args.url, headless=not args.headed))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
