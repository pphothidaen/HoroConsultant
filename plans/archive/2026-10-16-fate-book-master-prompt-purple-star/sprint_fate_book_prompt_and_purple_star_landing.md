# GRILL REPORT: Sprint Fate Book Master Prompt & Purple Star UI Overhaul

- **Task/Sprint ID:** `SPRINT-FATE-BOOK-PURPLE-STAR`
- **Date:** 2026-10-16
- **Status:** `APPROVED`
- **Gate Decision:** `APPROVED` (All 9 dimensions resolved; zero critical blockers; explicit user confirmation)
- **Authorized Next Phase:** Planning & Ticket Decomposition (`lead_ba` to register tickets in `ATOMIC_TICKET.md` and `plans/plan.md`)

---

## 1. Nine-Dimension Assessment Matrix

| ID | Dimension | Severity | Evidence State | Assessment Result |
| :--- | :--- | :--- | :--- | :--- |
| **D1** | Scope Boundary | `CRITICAL` | `[CONFIRMED]` | **IN:** 1) Purple Star Mapper-inspired landing page template for `public/lite.html` & `lite.css` (hero banner, pill form inputs, gender pill toggles, purple-astral palette); 2) Plain-language conversational consensus summary card below the form/results covering 6 key domains without esoteric jargon (ภาพรวมรายปี, การเงิน, ความรัก, สุขภาพ, ครอบครัว, จังหวะโอกาสและควรระวัง); 3) Fate Book Master Prompt Modal Popup in `lite.html` & `lite.js` with full preview and one-click clipboard copy button; 4) Inclusion of Zi Wei Dou Shu (12 Palaces, 14 Primary Stars, Si Hua, Ming/Shen Gong) alongside BaZi/Saju and Thai Suriyayart in the compiled master prompt and engine metadata; 5) Automated Playwright E2E and Node contract test updates. **OUT:** Paid LLM runtime API calls; modification of locked backend Python files. |
| **D2** | Requirement Delta | `HIGH` | `[CONFIRMED]` | Transforms `lite.html` UI from minimal utility form into modern Purple Star Mapper-style landing page. Adds accessible `<dialog>` Modal Popup for Master Prompt preview and copy. Adds Plain-Language Consensus Summary cards. |
| **D3** | Acceptance & Stop Conditions | `CRITICAL` | `[CONFIRMED]` | **Acceptance:** 1) `lite.html` renders Purple Star Mapper-inspired hero, rounded pill form, and gender selector; 2) Results display 6 plain-language conversational summaries without astrological jargon; 3) Clicking "ดู Master Prompt (Fate Book)" opens Modal Popup with full preview; 4) Clicking "คัดลอกลง Clipboard" copies prompt and shows feedback; 5) Prompt contains Zi Wei Dou Shu, BaZi, and Thai astrology sections; 6) 100% tests pass (Node contract + Playwright E2E); 7) Zero secret leaks. **Stop:** Broken responsive layout, clipboard copy crash, non-ASCII logs, or test failure halts execution fail-closed. |
| **D4** | Inputs & Dependencies | `HIGH` | `[AUTO]` | Inputs: `birth_date`, `birth_time`, `unknown_hour`, `birth_place`, `gender_at_birth`, `target_year`, `display_name`. Dependencies: `api/unified_reading_engine.js`, `public/lite.html`, `public/lite.js`, `public/lite.css`. |
| **D5** | Architecture & Ownership | `HIGH` | `[CONFIRMED]` | 6-Lane Architecture: `lead_ba` (planning & ticket registration), `developer` (`api/**`, `public/**`), `qa_tester` (`tests/**`), `code_reviewer` (safety audit), `devops` (PR, release, production deployment). Single-editor boundaries strictly maintained. |
| **D6** | Assumption Register | `CRITICAL` | `[CONFIRMED]` | 1) Modal uses accessible HTML5 `<dialog>` or accessible modal pattern (`role="dialog"`, `aria-modal="true"`, Esc key handler); 2) Plain-language summaries translate astrological consensus into conversational advice; 3) Zi Wei Dou Shu parameters are derived from birth date/time. |
| **D7** | Risk & Recovery | `HIGH` | `[CONFIRMED]` | Risk: Clipboard API permissions blocked in non-secure context or older browser. Mitigation: Provide `execCommand('copy')` fallback and easy "เลือกข้อความทั้งหมด (Select All)" button inside modal. |
| **D8** | Budget & Evidence Strategy | `HIGH` | `[AUTO]` | Pure client/edge execution; zero third-party API costs; bounded ASCII logs ([OK], [INFO], [WARNING], [ERROR]). |
| **D9** | Domain & HITL Check | `CRITICAL` | `[CONFIRMED]` | Chinese BaZi (Four Pillars), Zi Wei Dou Shu (12 Palaces & 14 Primary Stars), and Thai Suriyayart integrated into the Master Prompt structure. Multi-tradition consensus maintained. |

---

## 2. In-Scope vs Out-of-Scope Declarations

### In-Scope (Authorized)
1. **Purple Star Mapper-Inspired Landing Page UI (`public/lite.html`, `public/lite.css`)**:
   - Modern purple-astral background, hero banner with clear value proposition.
   - Rounded pill inputs (`border-radius: 9999px`) for date, time, and city.
   - Interactive pill toggle for gender (ชาย / หญิง) matching Purple Star Mapper UX.
   - Responsive layout optimized for mobile and desktop viewports.
2. **Plain-Language Conversational Consensus Summary (สรุปภาษาพูดเข้าใจง่าย ไม่มีศัพท์เทคนิค)**:
   - Dedicated card/section below the form synthesizing all traditions into 6 core life themes:
     1. ภาพรวมดวงชะตารายปี (Annual Trajectory)
     2. การเงินและโชคลาภ (Money & Wealth)
     3. ความรักและความสัมพันธ์ (Love & Marriage)
     4. สุขภาพและสุขภาวะ (Health & Vitality)
     5. ครอบครัวและบุคคลรอบตัว (Family & Social Connections)
     6. จังหวะโอกาสและช่วงที่ต้องระวัง (Timing Opportunities & Cautions)
   - Written in friendly, actionable conversational Thai without esoteric terms (เช่น ตัดคำว่า ชง, ฮะ, ย้งซิ้ง, ดิถี, ต้าอวิ้น ออกในส่วนนี้ แล้วอธิบายเป็นแนวทางชีวิตตรงไปตรงมา).
3. **Fate Book Master Prompt Modal Popup (`public/lite.js`, `public/lite.html`)**:
   - Dedicated action button: *"📋 ดูและคัดลอก Master Prompt (Fate Book)"*
   - Clicking opens an accessible Modal Dialog displaying the complete scholarly prompt.
   - Formatted in Thai with pre-filled dynamic variables (ชื่อ, วันเกิด, เวลาเกิด, เวลาสุริยคติจริง, ตาราง 4 เสา BaZi, ภพชะตาและดาวหลัก Zi Wei Dou Shu, ลัคนาไทย).
   - "คัดลอกลง Clipboard" button with instant visual confirmation (Toast / Copied state).
4. **Engine Support for Plain-Language Synthesis & Master Prompt (`api/unified_reading_engine.js`)**:
   - Output `plain_summary` object with the 6 conversational domains.
   - Output `fate_book_prompt` string containing the compiled master prompt ready for copy.
5. **QA Verification & Provenance**:
   - Node contract tests asserting `plain_summary` and `fate_book_prompt` in API response.
   - Playwright E2E tests verifying Purple Star UI layout, Modal Popup open/close, and clipboard copy behavior.

### Out-of-Scope (Excluded)
- Direct mutation of locked Python core calculation files (JS edge engine provides verified parity).
- Direct integration with paid LLM APIs (users copy the Master Prompt into their own ChatGPT/Claude/Gemini).
- Modifying locked Kaggle GPU/TPU accelerator settings.

---

## 3. Measurable Acceptance Criteria

1. **AC-01 (Landing Page Aesthetic):** `lite.html` renders with purple-astral styling, hero banner, rounded pill inputs, and gender selector.
2. **AC-02 (Conversational Summary):** Unified reading outputs 6 plain-language summary cards without esoteric astrological jargon.
3. **AC-03 (Master Prompt Modal):** Clicking "ดูและคัดลอก Master Prompt" opens an accessible Modal Popup showing full formatted prompt.
4. **AC-04 (Zi Wei Dou Shu Inclusion):** Master Prompt explicitly contains Zi Wei Dou Shu 12 Palaces, 14 Primary Stars, and Si Hua alongside BaZi and Thai astrology.
5. **AC-05 (Clipboard Copy):** Clicking copy button inside modal copies prompt text and displays visual confirmation.
6. **AC-06 (Keyboard Accessibility):** Modal opens on Enter/Space, closes on Escape key or backdrop click, visible focus outline maintained.
7. **AC-07 (Quality Gates):** 100% pass across Node contract tests, Playwright E2E suite, Rayon secret scan (0 leaks), and ecosystem sync (exit code 0).

---

## 4. Single-Editor Lane Assignments

- **Lane 1 (`lead_ba`):** Decompose sprint tickets in `ATOMIC_TICKET.md` and roadmap in `plans/plan.md`.
- **Lane 2 (`developer`):** Implement `plain_summary` and `fate_book_prompt` in `api/unified_reading_engine.js`, overhaul landing page UI in `public/lite.html` & `public/lite.css`, and implement Modal Popup in `public/lite.js`.
- **Lane 3 (`qa_tester`):** Update `tests/api_unified_reading_edge.test.mjs` and Playwright E2E suite (`scripts/run_prod_lite_e2e.py`) to verify Purple Star UI, conversational summary, and Master Prompt modal.
- **Lane 4 (`code_reviewer`):** Pre-deployment security review (Rayon secret scan, AST check, ecosystem sync check).
- **Lane 5 (`devops`):** PR creation, CI monitoring, squash merge to `main`, production deployment to Vercel, and live verification.
