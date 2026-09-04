# Horo Lite Unified Consensus Reading Implementation Plan

> **Task ID**: `TICKET-HORO-LITE-PLAN-001`  
> **Role**: `business_analyst`  
> **Target Release**: `v1.5.0-lite-preview`  
> **Status**: `READY_FOR_OWNER_REVIEW` (Planning Complete — Implementation Strictly Paused)  
> **Authority**: Owner prompt command dated `2026-09-04`  

---

## 1. Executive Summary & Architectural Overview

The **Horo Lite Unified Consensus Reading** initiative introduces a modern, accessible consumer experience hosted at `/lite` (`public/lite.html`), presenting astrological wisdom through 12 user-centric life topics rather than fragmented traditional terminology. The existing Advanced Dashboard at `/index.html` is permanently preserved. Both interfaces share the identical underlying calculation engines (`project/core/`), Horo v3.0 Consensus Engine arbitration, and unified API contracts (`/api/v3/unified-reading`) without code duplication.

### Key Architectural Pillars
1. **Single-Action Intuitive Form**: Clean birth date, time (or "unknown time"), location resolution (auto coordinates/timezone), and target year, with raw coordinates and advanced settings gracefully tucked into a disclosure drawer.
2. **Deterministic-First Foundation**: Verified Thai Suriyayart natal/transit ephemeris + BaZi 60-JiaZi monthly cycles. Scores (Career, Finance, Love 1–10) are computed deterministically before passing to LLM copy translation.
3. **Ethically Bounded Past Pattern Calibration**: Deterministic candidate cycles (3–5 life milestones) for verifiable themes (education, career shift, relocation, financial pressure), offering user feedback ("ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้") used solely to personalize future explanation emphasis without altering calculations or claiming false "accuracy percentages".
4. **12 Topic-Based Modules**:
   - 1. Personal overview & strengths
   - 2. Past Pattern Calibration
   - 3. Annual overview
   - 4. Career & business
   - 5. Finance
   - 6. Love & relationships
   - 7. Health & wellbeing
   - 8. Family & surrounding people
   - 9. Opportunities & caution periods
   - 10. Twelve-month roadmap (Career, Finance, Love 1–10)
   - 11. Three top priorities & three top cautions
   - 12. Export and sharing actions
5. **Multi-Format Export**: Full Long-Form Mobile PNG, Condensed 1080×1920 9:16 Story PNG, Copyable Social Text, and Print/PDF with privacy toggles (birth data hidden by default in social exports).
6. **Mandatory HITL Gate Policy**: Low consensus (`consensus_score < 0.75`), tradition conflicts, `force_human_review=true`, and uncertain birth times automatically trigger `/hitl` review queueing.

---

## 2. Resource Ownership & Lane Allocation Matrix

To prevent concurrent write collisions, the repository enforces strict single-editor path boundaries:

| Lane Identifier | Assigned Specialist | Exclusive Writable Paths | Bound Modular Skills |
| :--- | :--- | :--- | :--- |
| **Management** | `lead_ba` | `ATOMIC_TICKET.md`, `plans/plan.md`, `plans/intake/**`, `docs/superpowers/plans/**` | `bsa-doc-skill-management`, `agile-governance`, `requirement-grill-gate` |
| **Computation Core** | `developer_core` | `project/core/annual_timing_engine.py`, `project/core/past_pattern_calibrator.py`, `project/core/unified_reading_engine.py`, `project/core/bazi.py` | `sdlc-aisdlc-workflow`, `metaphysical-domain-engine` |
| **API Gateway** | `developer_api` | `project/routers/unified_reading_router.py`, `project/routers/v3_engine_router.py`, `api/index.js` | `sdlc-aisdlc-workflow`, `ai-inference-verifier` |
| **Frontend & UX** | `ux_ui_designer` | `public/lite.html`, `public/lite.js`, `public/lite.css`, `public/export_engine.js`, `public/export_modal.css` | `web-color-design`, `ui-visual-auditor` |
| **Visual QA** | `ui_visual_tester` | `plans/test_provenance/visual_audits/**` | `ui-visual-auditor` |
| **QA Verification** | `qa_tester` | `tests/test_horo_lite_unified_reading.py`, `plans/test_provenance/sprint_horo_v3_infographic_migration.json` | `qa-e2e-testing`, `hf-static-release-verification` |
| **Security Audit** | `code_reviewer` | Read-only security audit log (`plans/evidence/security_review.json`) | `hf-static-release-verification` |
| **Master Control** | `orchestrator` | Lane dispatch, DAG execution, lock verification, final sign-off | `orchestrator-delegation`, `multi-account-agent-orchestration` |

---

## 3. Dependency Graph (DAG)

```text
Phase A: TICKET-HLITE-001 (Schema & Compatibility Contracts)
   |
   +--> Phase B: TICKET-HLITE-002 (Deterministic Annual Timing & Past Pattern Engine)
   |       |
   |       +--> Phase C: TICKET-HLITE-003 (Horo v3.0 Consensus & HITL Integration)
   |       |       |
   |       |       +--> Phase D: TICKET-HLITE-004 (Unified Reading API Router & Copy Transformer)
   |       |               |
   |       +---------------+--> Phase E: TICKET-HLITE-005 (Horo Lite Form & Single-Action Flow)
   |                               |
   |                               +--> Phase F: TICKET-HLITE-006 (12 Topic-Based Result UI)
   |                               |       |
   |                               |       +--> Phase G: TICKET-HLITE-007 (Past Pattern Interaction & Consent)
   |                               |       |
   |                               +-------+--> Phase H: TICKET-HLITE-008 (Multi-Format Mobile Exporter Suite)
   |                                               |
   |                                               +--> Phase I: TICKET-HLITE-009 (Accessibility, Privacy & Error Recovery)
   |                                               |
   \-----------------------------------------------+--> Phase J: TICKET-HLITE-010 (Contract & End-to-End Regression Suite)
                                                           |
                                                           +--> Phase K: TICKET-HLITE-011 (Multi-Viewport Visual Layout Audit)
                                                           |
                                                           +--> Phase L: TICKET-HLITE-012 (Security Review & Release Verification)
```

---

## 4. Detailed TDD Implementation Steps by Phase

### Phase A — Versioned Unified Reading Schema & Compatibility Contracts
- [ ] **Step A.1 (Failing Test)**: Create `tests/test_horo_lite_unified_reading.py::test_unified_reading_schema_contract` validating the Pydantic schema for `UnifiedReadingRequest` and `UnifiedReadingResponse` (including 12 topics, monthly scores 1–10, consensus metadata, past patterns, and HITL flags).  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_unified_reading_schema_contract -v` (Must FAIL: schema not yet defined).
- [ ] **Step A.2 (Implementation)**: Define `UnifiedReadingRequest`, `TopicModule`, `MonthlyScoreItem`, `PastPatternCandidate`, and `UnifiedReadingResponse` in `project/core/unified_reading_engine.py`. Ensure backward compatibility with existing `/api/v1/bazi/interpret` and `/api/v3/calculate`.  
  *Owner*: `developer_core`
- [ ] **Step A.3 (Passing Test)**: Re-run `test_unified_reading_schema_contract` to verify schema validation, default parameters, and strict field constraints.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_unified_reading_schema_contract -v` (Must PASS).
- [ ] **Step A.4 (Review)**: Review that no existing legacy schemas in `project/models/` or `project/schemas/` were mutated.

### Phase B — Verified Deterministic Annual-Timing & Past Pattern Calibration Model
- [ ] **Step B.1 (Failing Test)**: Add tests `test_deterministic_annual_timing_12_months` and `test_past_pattern_candidate_generation` in `tests/test_horo_lite_unified_reading.py`. Validate that Career, Finance, and Love scores (1–10) are deterministically computed for 12 months with traceable reasons, and that 3–5 non-sensitive past pattern candidates are generated within historical age/year ranges.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k "test_deterministic_annual_timing_12_months or test_past_pattern_candidate_generation" -v` (Must FAIL).
- [ ] **Step B.2 (Implementation)**:  
  - In `project/core/annual_timing_engine.py`, implement Thai Suriyayart transit house calculations (Jupiter, Saturn, Rahu ephemeris) combined with BaZi 60-JiaZi Liu Yue cycles. Handle `unknown_hour=True` by calculating valid factors only, emitting score ranges and `confidence: LOW/ESTIMATED`.  
  - In `project/core/past_pattern_calibrator.py`, implement deterministic past cycle detection identifying historical major transits (Da Yun transitions, Jupiter return, Saturn square) mapped to verifiable life themes (education, career shift, relocation, financial pressure). Forbid sensitive themes.  
  *Owner*: `developer_core`
- [ ] **Step B.3 (Passing Test)**: Verify deterministic repeatability across test fixture profiles (e.g. 1990-05-15 14:30 Bangkok).  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k "test_deterministic_annual_timing_12_months or test_past_pattern_candidate_generation" -v` (Must PASS).
- [ ] **Step B.4 (Review)**: Verify that calculation runtime is <50ms and that zero random or generative values exist in the core models.

### Phase C — Horo v3.0 Consensus Arbitration & Mandatory HITL Integration
- [ ] **Step C.1 (Failing Test)**: Add test `test_horo_v3_consensus_arbitration_and_hitl_triggers` verifying that monthly claims from multiple traditions are arbitrated into consensus scores, and that `consensus_score < 0.75`, tradition conflicts, `force_human_review=True`, or uncertain birth time automatically set `hitl_routing.status = "QUEUED_FOR_HUMAN_REVIEW"`.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_horo_v3_consensus_arbitration_and_hitl_triggers -v` (Must FAIL).
- [ ] **Step C.2 (Implementation)**: Integrate `project/core/annual_timing_engine.py` with `project/debate/consensus_matrix.py` to calculate multi-tradition cross-validation. Connect triggers to the HITL queue database (`project/hitl_router.py`).  
  *Owner*: `developer_core`
- [ ] **Step C.3 (Passing Test)**: Run `test_horo_v3_consensus_arbitration_and_hitl_triggers` to verify that low-consensus scenarios fail closed into the review queue.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_horo_v3_consensus_arbitration_and_hitl_triggers -v` (Must PASS).
- [ ] **Step C.4 (Review)**: Confirm passing live probe `GET /hitl/scope-audit?source_domain=metaphysical-domain-engine` remains valid (`pass_gate_check=true`).

### Phase D — Unified Orchestration API & LLM Copy Transformer
- [ ] **Step D.1 (Failing Test)**: Add `test_unified_reading_api_endpoint` in `tests/test_horo_lite_unified_reading.py` testing `POST /api/v3/unified-reading`. Validate response payload structure, latency SLA (<300ms deterministic, <2.5s with LLM copy translation), and guardrails against hallucinated scores.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_unified_reading_api_endpoint -v` (Must FAIL).
- [ ] **Step D.2 (Implementation)**: In `project/routers/unified_reading_router.py`, implement `POST /api/v3/unified-reading`. Orchestrate deterministic calculations, consensus arbitration, HITL checks, and optional LLM prompt translation (using Gemini API or Ollama local). Ensure prompt strictly forbids altering scores, dates, or facts. Register route in `project/main.py`.  
  *Owner*: `developer_api`
- [ ] **Step D.3 (Passing Test)**: Execute `test_unified_reading_api_endpoint` against local test client.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_unified_reading_api_endpoint -v` (Must PASS).
- [ ] **Step D.4 (Review)**: Verify OpenAPI documentation updates at `/docs` and verify zero breaking changes to existing endpoints.

### Phase E — Horo Lite Form & Single-Action Flow (`public/lite.html`)
- [ ] **Step E.1 (Failing Test)**: Create Playwright/HTML parser contract test `test_lite_form_dom_contract` verifying presence of simplified inputs (birth date, time picker with unknown toggle, birthplace search with geocoding, gender selector, target year) and hidden raw coordinates disclosure.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_lite_form_dom_contract -v` (Must FAIL).
- [ ] **Step E.2 (Implementation)**: Build `public/lite.html`, `public/lite.css`, and `public/lite.js`. Provide a single high-contrast action button ("คำนวณผังดวง & ตีความด้วย AI"), smooth geocoding lookup for Thai provinces, and seamless client state management.  
  *Owner*: `ux_ui_designer`
- [ ] **Step E.3 (Passing Test)**: Run `test_lite_form_dom_contract` to confirm DOM structure, accessibility labels, and attribute bindings.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_lite_form_dom_contract -v` (Must PASS).
- [ ] **Step E.4 (Review)**: Validate that `public/lite.js` makes API calls to `/api/v3/unified-reading` and does NOT replicate astrological calculations locally.

### Phase F — Topic-Based Three-Part Result UI
- [ ] **Step F.1 (Failing Test)**: Add test `test_topic_based_result_rendering` asserting all 12 topic sections render with correct CSS classes, score gauges, accessible icons, and technical drawer disclosure ("ดูที่มาและรายละเอียดการคำนวณ").  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_topic_based_result_rendering -v` (Must FAIL).
- [ ] **Step F.2 (Implementation)**: In `public/lite.js` and `public/lite.css`, build the dynamic renderer for the 12 topic modules:
  - Part 1 (Annual Overview): 10 Key Modules with visual icons.
  - Part 2 (12-Month Roadmap): 12 distinct cards with visual score gauges (1–10) and text descriptions.
  - Part 3 (Final Directives): 3 Top Focus, 3 Top Cautions, and Life Guidance.
  - Technical calculation drawer with link to Advanced Dashboard (`/index.html`).  
  *Owner*: `ux_ui_designer`
- [ ] **Step F.3 (Passing Test)**: Re-run `test_topic_based_result_rendering` to verify DOM population.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_topic_based_result_rendering -v` (Must PASS).
- [ ] **Step F.4 (Review)**: Test with `unknown_hour=True` to ensure score ranges and reduced-confidence badges display clearly.

### Phase G — Past Pattern Calibration Interaction & Consent Handling
- [ ] **Step G.1 (Failing Test)**: Add test `test_past_pattern_feedback_and_consent_contract` verifying that selecting feedback choices ("ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้") does not alter original calculations, does not display false "accuracy percentages", and requires explicit consent before any persistence.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_past_pattern_feedback_and_consent_contract -v` (Must FAIL).
- [ ] **Step G.2 (Implementation)**: In `public/lite.js`, implement interactive calibration chips. Wire feedback to dynamically adjust tone emphasis in explanation cards without changing score metrics. Implement explicit privacy consent checkbox before saving any calibration preference.  
  *Owner*: `ux_ui_designer`
- [ ] **Step G.3 (Passing Test)**: Run `test_past_pattern_feedback_and_consent_contract` to confirm consent gate and immutable calculation state.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_past_pattern_feedback_and_consent_contract -v` (Must PASS).
- [ ] **Step G.4 (Review)**: Verify that no sensitive trauma categories are generated or accepted.

### Phase H — Mobile Infographic & Multi-Format Social Exporter Suite
- [ ] **Step H.1 (Failing Test)**: Add test `test_export_formats_and_privacy_default` verifying that Full Long-Form PNG, 1080×1920 Story PNG, Copyable Text, and Print/PDF export functions exist and default to hiding birth details.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_export_formats_and_privacy_default -v` (Must FAIL).
- [ ] **Step H.2 (Implementation)**: In `public/export_engine.js` and `public/export_modal.css`, implement pure client-side HTML5 Canvas rasterizer:
  - 1-Click "Save Full Mobile Infographic" (long vertical PNG).
  - 1-Click "Save 9:16 Story" (exact 1080×1920 PNG).
  - 1-Click "Copy Social Summary" (clean formatted Thai text).
  - Secondary Print/PDF view with print CSS rules.
  - Privacy toggle: "แสดงวันเวลาเกิดในรูปภาพ" (default: OFF).  
  *Owner*: `ux_ui_designer`
- [ ] **Step H.3 (Passing Test)**: Run `test_export_formats_and_privacy_default` to confirm canvas dimension calculations and privacy scrubbing.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_export_formats_and_privacy_default -v` (Must PASS).
- [ ] **Step H.4 (Review)**: Verify error handling displays a non-destructive retry notification without clearing the user's active reading.

### Phase I — Accessibility, Privacy, Error Recovery & Unknown-Time Ergonomics
- [ ] **Step I.1 (Failing Test)**: Add test `test_accessibility_and_contrast_compliance` checking WCAG AA compliance, focus rings, keyboard tab order, ARIA attributes, and score gauge text alternatives.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_accessibility_and_contrast_compliance -v` (Must FAIL).
- [ ] **Step I.2 (Implementation)**: Add keyboard navigation listeners, ARIA-expanded states, focus indicators, and accessible text alternatives to all gauges and badges in `public/lite.css` and `public/lite.js`.  
  *Owner*: `ux_ui_designer`
- [ ] **Step I.3 (Passing Test)**: Run `test_accessibility_and_contrast_compliance` to ensure 100% compliance.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -k test_accessibility_and_contrast_compliance -v` (Must PASS).
- [ ] **Step I.4 (Review)**: Verify that color alone is never used to communicate positive or cautious ratings.

### Phase J — Contract, Unit, Inference-Origin & Regression Test Baseline
- [ ] **Step J.1 (Failing Test)**: Add comprehensive test suite in `tests/test_horo_lite_unified_reading.py` covering end-to-end integration, real model inference validation (via `ai-inference-verifier`), and fallback behavior.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -v` (Must FAIL on missing components).
- [ ] **Step J.2 (Implementation)**: Ensure all edge cases (leap months, midnight birth, timezone boundary, high latitude) pass cleanly.  
  *Owner*: `qa_tester`
- [ ] **Step J.3 (Passing Test)**: Execute complete test suite and record evidence in `plans/test_provenance/sprint_horo_v3_infographic_migration.json`.  
  *Command*: `pytest tests/test_horo_lite_unified_reading.py -v` (Must PASS: 100%).
- [ ] **Step J.4 (Review)**: Verify zero regressions across existing test suites (`test_visual_endpoints.py`, `test_browser_notifications_and_processing_modal.py`, `test_bazi_resilient_fallback.py`).

### Phase K — Multi-Viewport Visual Layout Audit (360px, 375px, 390px, 768px, 1440px)
- [ ] **Step K.1 (Test Setup)**: Configure automated headless viewport capture script `scripts/audit_lite_viewports.py` across 5 canonical viewports (360×780, 375×667, 390×844, 768×1024, 1440×900).  
  *Owner*: `ui_visual_tester`
- [ ] **Step K.2 (Execution & Evidence)**: Execute viewport audit to capture screenshots and verify zero DOM clipping, zero text overlap, and zero horizontal scrollbar overflow.  
  *Command*: `python3 scripts/audit_lite_viewports.py --url http://localhost:8000/lite --output plans/test_provenance/visual_audits/`  
- [ ] **Step K.3 (Review & Sign-Off)**: Review screenshot artifacts and record visual audit receipt.

### Phase L — Security Review, Documentation Synchronization & Release Readiness
- [ ] **Step L.1 (Security Scan)**: Run Rayon parallel secret scanner and pre-tool audit.  
  *Command*: `python3 scripts/scan_secrets.py --all` (Must return 0 leaks).  
  *Owner*: `code_reviewer`
- [ ] **Step L.2 (Ecosystem Synchronization)**: Run AI agent ecosystem check.  
  *Command*: `python3 scripts/sync_ai_agent_ecosystem.py --check` (Must PASS with 0 drift).  
  *Owner*: `lead_ba`
- [ ] **Step L.3 (Release Notes)**: Draft release notes entry in `ReleaseNotes.md` reflecting `v1.5.0-lite-preview`.  
  *Owner*: `lead_ba`
- [ ] **Step L.4 (Final Sign-Off)**: Present completed verification matrix to Orchestrator and Owner for release approval.

---

## 5. Self-Review Against Confirmed Requirements

| Requirement | Addressed in Section | Validation Mechanism |
| :--- | :--- | :--- |
| Horo Lite at `/lite`, Advanced at `/index.html` | Section 1, Phase E | URL routing contract test (`test_lite_form_dom_contract`) |
| Shared core engines & zero code duplication | Section 1, Phase A, B | Schema & API contract test (`test_unified_reading_schema_contract`) |
| Single-action intuitive form + Advanced disclosure | Section 1, Phase E | DOM contract test (`test_lite_form_dom_contract`) |
| 12 Topic-based result presentation | Section 1, Phase F | Module rendering test (`test_topic_based_result_rendering`) |
| Ethically bounded Past Pattern Calibration | Section 1, Phase B, G | Calibration contract test (`test_past_pattern_feedback_and_consent_contract`) |
| No sensitive trauma claims | Section 1, Phase B | Negative assertion tests in `test_past_pattern_candidate_generation` |
| No false accuracy percentages | Section 1, Phase G | Feedback chip contract assertion |
| 12 Monthly roadmap cards (Career, Finance, Love 1–10) | Section 1, Phase B, F | Deterministic score test (`test_deterministic_annual_timing_12_months`) |
| Full Long-form PNG & 1080×1920 Story PNG export | Section 1, Phase H | Export canvas test (`test_export_formats_and_privacy_default`) |
| Privacy default: birth details hidden in social export | Section 1, Phase H | Privacy scrubber assertion test |
| D9 CRITICAL + Passing HITL scope audit | Section 1, Phase C | Verified passing `GET /hitl/scope-audit` live probe |
| Mandatory HITL routing (consensus < 0.75, conflicts) | Section 1, Phase C | Fail-closed HITL trigger test |
| Multi-viewport audit (360px, 375px, 390px) | Section 4, Phase K | Headless screenshot audit script |
| Zero source edits / zero deployments during planning | Entire Document | Read-only boundary strictly enforced |

---

## 6. Stop Condition & Gate Statement

- **Current Status**: `PLANNING_COMPLETE` — All 4 canonical planning documents are ratifying the expanded scope.
- **Hold Status**: Source code modification, commits, pushes, and deployments remain **STRICTLY PAUSED** awaiting explicit owner authorization.
