# GRILL REPORT — Sprint: Lite Focus Question Smart Routing & Dedicated Hero Card

**Status**: `APPROVED`
**Owner Confirmed Date**: 2026-10-16T17:00:29+07:00
**Lead BSA**: `business_analyst` (`lead_ba`)
**Selected Architectural Decision**: Single Dropdown Selector + Conditional Dedicated Hero Card (<5ms Latency, Zero LLM API Cost)
**Grill Gate Verdict**: `GRILL GATE: APPROVED`

---

## 1. Executive Summary

Following owner review and 9-Dimension Grill assessment, the focus topic input mechanism is streamlined into an unambiguous, 100% deterministic single dropdown selector replacing freeform text entry. Users can explicitly select a core life topic to prioritize, completely eliminating classification ambiguity, misspellings, or token costs while guaranteeing instantaneous Edge response times (<5ms).

When a focus topic is selected, the reading engine synthesizes a dedicated `focus_analysis` payload, and the UI dynamically renders a dedicated `#focus-question-hero-card` at the very top of `#result-panel`. The hero card highlights:
1. Category title and score
2. 🌟 เดือนจังหวะโอกาสทองสูงสุด (Peak Golden Month) with proactive guidance
3. ⚠️ เดือนที่ควรเฝ้าระวัง (Caution Month) with defensive guidance
4. 💡 กลยุทธ์คำแนะนำเชิงรุก/รับ

When the default unselected option is chosen (`""`), the hero card remains completely hidden, preserving the clean, tranquil consultation flow.

---

## 2. Dropdown UI Specification (`primary_focus_topic`)

In `public/lite.html`, replace the text input field `#primary_focus_question` with a structured `<select>` element:

- **Label**: `🎯 ประเด็นที่ต้องการเน้นเป็นพิเศษ`
- **Element ID**: `id="primary_focus_topic"`
- **Element Name**: `name="primary_focus_topic"`
- **Options**:
  1. `value=""`: `-- ไม่ระบุ (ดูภาพรวมทั่วไป) --` *(Default)*
  2. `value="career_business"`: `💼 การงานและธุรกิจ (Career & Business)`
  3. `value="finance_wealth"`: `💰 การเงินและโชคลาภ (Finance & Wealth)`
  4. `value="love_relationship"`: `💞 ความรักและความสัมพันธ์ (Love & Relationships)`
  5. `value="health_vitality"`: `🩺 สุขภาพและพลังชีวิต (Health & Vitality)`
  6. `value="family_environment"`: `👨‍👩‍👧 ครอบครัวและคนรอบตัว (Family & Environment)`

---

## 3. Dedicated Hero Card UI Specification (`#focus-question-hero-card`)

- **Element ID**: `<div id="focus-question-hero-card" class="focus-hero-card hidden">`
- **Placement**: Mounted at the very top of `#result-panel` (before `#plain-summary-container`).
- **Conditional Visibility**:
  - **Selected topic (`value !== ""` )**: Revealed on result arrival (`classList.remove("hidden")`, `hidden = false`).
  - **Unselected default (`value === ""` or omitted)**: Completely hidden (`classList.add("hidden")`, `hidden = true`).
- **Hero Card Structure & Content**:
  1. **Header Badge**: `🎯 บทวิเคราะห์เจาะลึกประเด็นโฟกัสพิเศษ (Special Focused Analysis)`
  2. **Topic Title & Favorability Score**:
     - Prominent topic header with emoji and Thai title (e.g. `💼 การงานและธุรกิจ`)
     - Score badge / meter (e.g. `คะแนนความราบรื่น: 8.5/10 — จังหวะเกื้อหนุนสูง`)
  3. **🌟 เดือนจังหวะโอกาสทองสูงสุด (Peak Golden Month)**:
     - Identifies the highest-scoring month for this topic from the 12-month roadmap.
     - Actionable proactive guidance (คำแนะนำเชิงรุก: จังหวะเร่งสร้างผลงาน / ขยายโอกาส / เจรจาสำคัญ)
  4. **⚠️ เดือนที่ควรเฝ้าระวัง (Caution Month)**:
     - Identifies the most challenging month or period requiring caution.
     - Prudent defensive guidance (คำแนะนำเชิงรับ: ควรชะลอการตัดสินใจเสี่ยง / สำรองทรัพยากร / ตรวจสอบความถูกต้อง)
  5. **💡 กลยุทธ์คำแนะนำเชิงรุก/รับ (Strategic Guidance)**:
     - Synthesized plain-language executive summary combining proactive and defensive actions for the year ahead.

---

## 4. 9-Dimension Grill Assessment

| ID | Dimension | Severity | Assessment Status | Evidence / Details |
|---|---|---|---|---|
| **D1** | Scope Boundary | CRITICAL | `[CONFIRMED]` | **In-Scope**: Dropdown selector in `public/lite.html`, CSS styling in `public/lite.css`, controller wiring in `public/lite.js`, focus analysis synthesis in `api/unified_reading_engine.js`, Node contract & Pytest regression tests, test provenance manifest. **Out-of-Scope**: External LLM billing, breaking changes to base unified reading API. |
| **D2** | Requirement Delta | HIGH | `[CONFIRMED]` | Dropdown replaces free-text input; eliminates NLP guesswork; deterministic mapping directly selects topic calculations with zero latency degradation (<5ms). |
| **D3** | Acceptance & Stop Conditions | CRITICAL | `[CONFIRMED]` | 1. Dropdown renders 5 core topics + default unselected option.<br>2. When unselected, `#focus-question-hero-card` remains hidden.<br>3. When selected, `#focus-question-hero-card` renders at top of `#result-panel` with score, Peak Golden Month, Caution Month, and proactive/defensive strategy.<br>4. Node contract tests and Pytest pass 100%.<br>5. Latency <5ms; pure ASCII logs. |
| **D4** | Inputs & Constraints | HIGH | `[CONFIRMED]` | Input: `primary_focus_topic` enum string. Synchronous execution on Edge runtime. Zero external dependencies. |
| **D5** | Architecture & Ownership | HIGH | `[CONFIRMED]` | Single-editor ownership: `lead_ba` (specs/plans/intake), `developer` (engine and UI), `qa_tester` (tests/provenance), `code_reviewer` (review/evidence/notes), `devops` (git/release). |
| **D6** | Assumption Register | CRITICAL | `[CONFIRMED]` | Scores and monthly peak/caution identification derive deterministically from the 12-month roadmap topic arrays. |
| **D7** | Risk & Recovery | HIGH | `[CONFIRMED]` | Zero risk of broken input parsing; backward compatible fallback to default overview reading. Atomic rollback ready. |
| **D8** | Budget & Evidence Strategy | HIGH | `[CONFIRMED]` | Zero runtime cost. Validated through automated test suite, Rayon secret scan, and test provenance manifest. |
| **D9** | Metaphysics Domain Audit | HIGH | `[CONFIRMED]` | Topic significators correctly align with classical Thai Suriyayart, Chinese BaZi, and Zi Wei Dou Shu palace correlations. |

---

## 5. Terminal Gate Decision

**Verdict**: `GRILL GATE: APPROVED`
**Next Step**: Authorize developer implementation on `TICKET-FOCUS-002` across `api/unified_reading_engine.js`, `public/lite.html`, `public/lite.css`, and `public/lite.js`.
