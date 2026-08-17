# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last Updated: 2026-08-17 — `TICKET-META-001` DOING: roadmap implementation and release verification in progress.*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# === RUST NATIVE CI/CD TOOLS ===

# 1. Native Rust Integration Test Suite (2 integration tests: vector search)
export PATH="/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH"
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup -L /opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib -l Python3.14"
cd rust_core
cargo test
# Optional runtime suite: 12 checks; start horo_server first to exercise its health check.
cargo run --bin regression_runner
cd ..

# 2. Rust Code Reviewer & Safety Auditor Binary (Pre-Deployment Audit)
python3 project/core/code_reviewer.py --review
# OR Direct Rust Binary:
./rust_core/target/release/code_reviewer

# 3. Rust Agent & Governance Spec Sync Check Binary
python3 scripts/sync_sdlc_agents.py --check
# OR Direct Rust Binary:
./rust_core/target/release/sync_sdlc_agents

# 4. Codex Agent Compatibility Sync Check
python3 scripts/sync_codex_agents.py --check

# 5. Rust Atomic Prometheus Observability Collector Test
python3 -c "import rust_core; print(rust_core.generate_prometheus_metrics_rust(120.0))"

# 6. Rust SVG Chart Rendering Engine Test (BaZi, ZiWei, Zodiac, QiMen, XuanKong)
python3 -c "from project.core.svg_generator import generate_bazi_svg; print(generate_bazi_svg({'day_master': {'stem': '庚'}}))"

# 7. Rust Astrological Consistency Audit (PyO3 Accelerated)
python3 scripts/audit_astrological_consistency.py

# 8. Pre-Deployment Safety Audit & Secret Scan (Rust Rayon Parallel — 642 files, 0 leaks)
python3 project/core/code_reviewer.py --scan-secrets

# 9. Full Python Pytest Suite (All test cases PASS)
pytest -v project/tests/
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│   ✅ DONE: Phase 17 — Client-Side Deterministic BaZi & True Solar Time Engine  │
├───────────────────────────────────────────────────────────────────────────────┤
│ • 0ms Pre-rendering & Zero-Latency Fast-Path Chart Render in Pure JavaScript  │
│ • Client True Solar Time (Equation of Time + Longitude Correction) in app.js  │
│ • 24 Solar Terms (JieQi) boundary check, 10 Stems, 12 Branches, 5 Elements   │
│ • Full Dual-Path sync across project/static/app.js and public/app.js          │
│ • Kaggle Fine-Tuning Pipeline v132 Execution Completed (Loss: 0.6974)         │
│ • 570/570 Pytest Tests Passed (100%), 31/31 UI Button Regressions Passed     │
│ • Deployed to HF Spaces (pphothidaen/horoconsultant-core-backend) & Verified │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 16 — 3-Tier Notebook AST, Python Syntax & MLOps Safety Gate  │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Tier 1: Local Pre-Commit Hook (`.githooks/pre-commit`) blocking syntax bugs  │
│ • Tier 2: Pytest Suite (`tests/test_notebook_syntax.py`) AST & Conflict locks  │
│ • Tier 3: Pre-Deployment Audit (`CodeReviewer.audit_notebooks()`) integrated   │
│ • Fixed unterminated newline literals in notebook string writing loops        │
│ • Created `scripts/sync_notebook_cells.py` safe cell generator & validator    │
│ • Full Pytest Pass: 602/602 (100%), Pre-Deployment Audit: READY_FOR_PROD      │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 15 — Kaggle Fine-Tuning Pipeline NumPy 2.x & BNB Hotfix      │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Fixed `ValueError: numpy.dtype size changed` by upgrading datasets>=2.21.0  │
│ • Removed legacy pyarrow_hotfix and unlocked BNB_CUDA_VERSION auto-detect     │
│ • Fixed top-level import json and dataset_cmd_path safety guard check         │
│ • Synced horoconsultant-finetune-pipeline.ipynb & project/kaggle_kernel/      │
│ • Passed 598/598 tests (100%), 33/33 Button Regressions, READY_FOR_PROD       │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Production Gateway 404/502 Hotfix & Post-Deploy Verification       │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Resolved 404/502 across `/calendar/month`, `/simulation`, `/prompt-pills`  │
│ • Unified `fetchApi()` Routing across All Submodules with Local JS Fallbacks  │
│ • Updated Vercel Gateway `api/index.js` with full standalone engine handlers  │
│ • Passed 598/598 tests (100%), 33/33 Button Regressions, Published to HF Space │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 14 — Metaphysics AI Live Consultant Chat Assistant (100%)    │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Floating Glassmorphic Slide-Out Drawer & Co-Pilot Split-Screen View         │
│ • Auto-Context Injection (Day Master 丁火, 5-Elements, DaYun, RAG Grounding)   │
│ • Hybrid Backend: SSE Stream `/api/v2/chat/stream` + JSON `/api/v2/chat/consult` │
│ • 5-Category Dynamic Prompt Pills & Privacy-First Client Session Management   │
│ • Full Pytest Pass: 598/598 (100%), Button Regression: 33/33 (100%), 0 Drift   │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 13 — Imperial White & Red Theme Overhaul (FengShuiX-Style)   │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Complete UI Theme Alignment with White & Red FengShuiX Metaphysics Style    │
│ • Full Elimination of Dark Remnants in Admin Studio & HITL Review Studio      │
│ • High-Contrast 5-Elements Metaphysics Palette & Dual-Path Asset Sync (100%)  │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 12 — Life Path Multi-Scenario Simulation & What-If (100%)    │
├───────────────────────────────────────────────────────────────────────────────┤
│ • 3-5 Year Multi-Path Life Decision Simulation Model (Career/Startup/Move)     │
│ • 4-Dimension Trajectory Scoring (Wealth, Career, Stability, Opportunity)     │
│ • Interactive Scenario Comparison Table & Optimal Path Recommendation UI      │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 11 — LuoPan 24-Mountain & Dream Symbol Decoder (100%)        │
├───────────────────────────────────────────────────────────────────────────────┤
│ • 24-Mountain LuoPan Compass & Period 9 Flying Star 9-Palace Energy Heatmap   │
│ • AI Metaphysics Dream Interpreter with 64 Hexagrams & Sattaleka Numbers      │
│ • Interactive SVG LuoPan Compass Dial, Sector Matrix & Dream Search UI        │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 📋 PLANNED SPRINT: Metaphysics Learning Roadmap & Question-Forecast Alignment
**Grill Gate Status**: DOING — scope approved for execution; child tickets are queued in `TODO`.
**Sprint Tracking Lead**: `orchestrator` / `business_analyst`
**Source Documents**:
- [`plans/metaphysics_learning_roadmap.md`](plans/metaphysics_learning_roadmap.md)
- [`plans/plan.md`](plans/plan.md)
- [`plans/question_forecast_alignment_spec.md`](plans/question_forecast_alignment_spec.md)
- [`plans/todo_tasks_plan.md`](plans/todo_tasks_plan.md)

**Plan Coverage Matrix**:

| Plan | Covered scope | Kanban disposition |
|---|---|---|
| `metaphysics_learning_roadmap.md` | Five branches, source ingestion, deterministic engines, fine-tuning, MCP, and UI visualizer | `TICKET-META-001` scope; implementation child tickets required |
| `plan.md` | Phases 1–16, MLOps/provider/Grafana work, governance, multi-cloud, quality gates, and future model architecture | Existing phase tickets remain historical evidence; active/future gaps require child tickets |
| `question_forecast_alignment_spec.md` | Six benchmark domains, 100-point rubric, validator threshold, prompt/debate routing | `TICKET-META-001` acceptance criteria |
| `todo_tasks_plan.md` | Six implementation workstreams and five-phase SDLC execution flow | `TICKET-META-001` instructions and child-ticket handoff |

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-META-001` | `orchestrator` / `business_analyst` | Consolidate and execute the five-branch metaphysics roadmap, six-domain question/forecast alignment benchmark, and six TODO workstreams | DOING | None |
| `TICKET-META-002` | `domain_master` / `developer` | Implement and test the five-branch deterministic metaphysics calculation modules | TODO | `TICKET-META-001` |
| `TICKET-META-003` | `developer` | Execute OCR/RAG ingestion, dataset generation, fine-tuning, model fusion, MCP, and visualizer integration | TODO | `TICKET-META-001` |
| `TICKET-META-004` | `developer` / `qa_tester` | Implement six-domain question/forecast alignment, focused prompting, debate routing, and validator benchmarks | TODO | `TICKET-META-001` |
| `TICKET-META-005` | `devops` / `developer` | Reconcile active/future `plan.md` platform work: providers, observability, CI/CD, governance, and release architecture | TODO | `TICKET-META-001` |
| `TICKET-META-006` | `qa_tester` / `code_reviewer` / `business_analyst` | Run full QA, security, synchronization, release evidence, and final Kanban documentation handoff | DOING | `TICKET-META-002`..`005` |

### 🎫 TICKET-META-001 | `orchestrator` / `business_analyst` | [STATUS: DOING]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: Future implementation, QA, release, and production handoff tickets derived from this scope.

#### Detailed Instructions
1. **Scope and architecture** — implement the five roadmap branches and their calculation/knowledge surfaces: Three Cosmic Styles (Tai Yi, Da Liu Ren, Qi Men), Destiny Analysis (BaZi improvements, Zi Wei, Qi Zheng Si Yu), Divination (I Ching, Liu Yao, Mei Hua), Physiognomy/Feng Shui (Xuan Kong, San He, Mian Xiang), and Date Selection (Ze Ji).
2. **Knowledge pipeline** — run the OCR/Obsidian ingestion flow, maintain the RAG vector store and exported ShareGPT JSONL dataset, and preserve traceable classical-source metadata.
3. **Deterministic engines** — implement or extend the pure-Python calculation modules under `project/core/`, including deterministic unit tests for solar terms, chart placement, interactions, and fallback behavior.
4. **Model and delivery pipeline** — execute the dataset/fine-tuning, adapter-to-GGUF/Ollama fusion, MCP tool integration, and Glassmorphism dashboard visualization work described by the roadmap and `plans/todo_tasks_plan.md`.
5. **Question/forecast alignment** — implement the six benchmark domains in `plans/question_forecast_alignment_spec.md`; pass the user’s `user_query` and extracted focus into `project/core/prompt_manager.py` and `project/core/multi_agent_debate.py`; validate direct relevance, astrological consistency, canonical evidence, and actionable guidance using the 100-point rubric and `Confidence Score > 0.85` validator threshold.
6. **TODO workstreams** — complete the six deliverables in `plans/todo_tasks_plan.md`: model fusion, external provider routing, Swiss Ephemeris, batch vault ingestion, CI/CD automation, and consultant UI enhancements.
7. **SDLC handoff** — follow the repository workflow from planning through implementation, QA, release verification, and final Kanban evidence. Create child tickets for developer, QA, DevOps, domain, and review work before execution begins.
8. **Complete `plans/plan.md` coverage** — treat its historical completed phases as required traceability/evidence, and its active or future sections as execution scope:
   - Phase 1–3: all-16-discipline E2E/snapshot visualizer baseline, seven extended SVG visualizers, and the multimodal 16-discipline consensus matrix.
   - Phase 4–6: external multi-provider gateway, multilingual/i18n interpretation, production delivery/PWA/offline support, and consultation report export.
   - Phase 7–10: DaYun/LiuNian timeline and transit clock, voice TTS/STT, synastry compatibility matrix, and interactive Ze Ji calendar/date selector.
   - Phase 11–14: LuoPan/dream decoder, multi-scenario life simulation, Imperial White/Crimson UI, and live multi-turn consultant chat with grounded RAG.
   - Phase 15–16: Kaggle NumPy/BNB pipeline compatibility and the three-tier notebook AST/pre-commit/deployment safety gate.
   - Continuous MLOps, hybrid LLM provider expansion, and Grafana latency/observability tuning.
   - Skill-context governance, agent synchronization, Grafana Cloud integration, multi-cloud architecture, quality-control standards, future LLM model expansion/circuit breaking, and the ten-policy operating consensus matrix.
9. **Status reconciliation** — link each `plan.md` phase to its existing Kanban ticket and verification evidence; do not re-open phases already marked `DONE`. Any active or future item without a current ticket must receive a child ticket before implementation.

#### Acceptance Criteria
- [ ] All roadmap modules and their source/algorithm boundaries are mapped to implementation files and child tickets.
- [ ] OCR/RAG ingestion produces traceable Markdown, vector-store, and JSONL outputs without losing source metadata.
- [ ] Calculation engines have deterministic tests covering the implemented branches and pass the project’s required pytest gate.
- [ ] The six-domain benchmark contains executable cases for direct relevance, logic consistency, canonical evidence, and actionable guidance.
- [ ] Prompt/debate routing preserves the user’s requested focus, and validator evidence meets `Confidence Score > 0.85`.
- [ ] The six TODO workstreams have implementation, test, and release evidence recorded in the child tickets.
- [ ] Every section of `plans/plan.md` is dispositioned as `DONE` with evidence, `DOING`, or `TODO` with a child ticket; no plan section is left untracked.
- [ ] CI/CD, secret scan, agent synchronization, pre-deployment review, and required E2E/UI regression gates pass before release.
- [ ] `PROJECT_TASKS.md`, the four source plans, and the final delivery evidence are synchronized with the actual implementation state.

#### Definition of Done
This ticket is `DOING` while child tickets are being executed. It moves to `DONE` only when every child ticket is complete, all acceptance evidence is recorded, the relevant test/release gates pass, and the final Kanban/documentation synchronization is verified.

### 🎫 TICKET-META-002 | `domain_master` / `developer` | [STATUS: TODO]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-004`, `TICKET-META-006`

#### Detailed Instructions
Implement or extend the five roadmap branches: Tai Yi, Da Liu Ren, Qi Men, BaZi/Zi Wei/Qi Zheng, I Ching/Liu Yao/Mei Hua, Xuan Kong/San He/Mian Xiang, and Ze Ji. Map each module to canonical source material, preserve pure-Python deterministic behavior, and add deterministic tests for chart placement, solar terms, interactions, and fallback paths.

#### Acceptance Criteria
- [ ] Every roadmap module has an implementation path, owner, canonical source mapping, and child evidence.
- [ ] Deterministic tests cover every implemented branch and pass.
- [ ] Existing BaZi and Swiss Ephemeris behavior remains backward compatible.

### 🎫 TICKET-META-003 | `developer` | [STATUS: TODO]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Execute the knowledge and delivery pipeline from the roadmap and TODO plan: OCR into Obsidian Markdown, RAG/vector and ShareGPT JSONL export, additional batch ingestion, Kaggle fine-tuning, GGUF/Ollama fusion, MCP calculation tools, and the Glassmorphism five-branch visualizer. Include the external provider and Swiss Ephemeris deliverables where they are part of the current implementation path.

#### Acceptance Criteria
- [ ] Ingestion outputs retain source metadata and are reproducible.
- [ ] Dataset, fusion, provider, Swiss Ephemeris, MCP, and visualizer tests pass for implemented scope.
- [ ] Root and target artifacts remain synchronized where the plans require parity.

### 🎫 TICKET-META-004 | `developer` / `qa_tester` | [STATUS: TODO]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`, `TICKET-META-002`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Implement the six benchmark domains from `question_forecast_alignment_spec.md`. Ensure `user_query` and extracted focus reach `prompt_manager.py` and `multi_agent_debate.py`; preserve direct relevance, astrological consistency, canonical citations, actionable guidance, the 100-point rubric, and validator confidence above `0.85`.

#### Acceptance Criteria
- [ ] All six benchmark questions have executable regression cases.
- [ ] Responses remain focused on the user’s question and include required evidence and actions.
- [ ] Validator results meet the configured confidence threshold without template-only fallback.

### 🎫 TICKET-META-005 | `devops` / `developer` | [STATUS: TODO]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`, `TICKET-META-003`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Reconcile every active or future section of `plan.md` with implementation or a child ticket. Cover hybrid provider failover, Grafana/observability, CI/CD, multi-cloud deployment, skill and agent synchronization, release safeguards, caching/rate limits/security, and future model circuit-breaking architecture. Do not reopen historical `DONE` phases without contrary evidence.

#### Acceptance Criteria
- [ ] Each active/future plan section has an owner, ticket, dependency, and measurable gate.
- [ ] Provider, observability, CI/CD, security, and agent-sync checks pass for the implemented scope.
- [ ] Rollback and release evidence is recorded before production claims.

### 🎫 TICKET-META-006 | `qa_tester` / `code_reviewer` / `business_analyst` | [STATUS: DOING]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-002`..`005`
**Blocks**: None

#### Detailed Instructions
Run the required unit, integration, UI/E2E, security, agent synchronization, pre-deployment, and documentation audits. Reconcile all four source plans against actual implementation evidence, update ticket statuses, and record the final handoff without marking incomplete work as done.

#### Current Verification Evidence
- [x] Full local QA: `609 passed, 4 skipped` with elevated network/localhost permissions.
- [x] Button and endpoint contract regression: `31/31 PASSED`.
- [x] Local Playwright E2E report: `17/17 PASSED`; console still records local `sw.js` 404 and proxy 502 events requiring live/release disposition.
- [x] Secret scan: `0` leaks across `1,485` files.
- [x] Hugging Face static payload dry-run: `21` files, `3.75 MB`, authenticated payload audit passed.
- [ ] Rust/Python full-review wrapper completion: wrapper hangs while re-running its internal suite; independent full QA evidence is available.
- [ ] Live production Playwright E2E: pending explicit authorization for external birth-data test egress.

#### Acceptance Criteria
- [ ] Required pytest, UI regression, E2E, secret scan, and code-review gates pass.
- [ ] Agent definitions are synchronized with zero drift.
- [ ] All child tickets have evidence-backed `DONE`, `BLOCKED`, or remaining `TODO` status.
- [ ] Parent ticket is moved to `DONE` only after the complete audit passes.

## 🚀 ACTIVE SPRINT: Phase 14 — Metaphysics AI Live Consultant Chat Assistant & Multi-Turn Interactive Consultation Engine
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-CHAT-001` | `orchestrator` | Architecture Blueprint & Specification | DONE | None |
| `TICKET-CHAT-002` | `developer` | Backend Chat Engine & Streaming Router (`chat_assistant_engine.py`, `chat.py`, `main.py`) | DONE | `TICKET-CHAT-001` |
| `TICKET-CHAT-003` | `developer` | Frontend Floating Drawer, Co-Pilot Split-Screen & Modal UI (`index.html`, `style.css`, `app.js`, `i18n.js`) | DONE | `TICKET-CHAT-002` |
| `TICKET-CHAT-004` | `qa_tester` | Unit & Regression Test Suite (`test_chat_assistant.py`) | DONE | `TICKET-CHAT-002`..`003` |
| `TICKET-CHAT-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-CHAT-004` |
| `TICKET-CHAT-006` | `code_reviewer` | Pre-Deploy Safety Audit & Documentation Sync | DONE | `TICKET-CHAT-005` |

---

### 🎫 TICKET-CHAT-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-CHAT-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report via `/grill-me`.
2. Establish SSE streaming format, RAG citation metadata schema, 5-category dynamic prompt pills hierarchy, and hybrid drawer/co-pilot layout specs.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-CHAT-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CHAT-001`  
**Blocks**: `TICKET-CHAT-003`..`004`  
#### Detailed Instructions
1. In `project/core/chat_assistant_engine.py`:
   - Implement `ChatAssistantEngine` with auto-context injection (Day Master stem/strength, 4-Pillars, 5-Elements %, Favorable/Unfavorable elements, Symbolic Stars, Current Da Yun decade, 2026 Liu Nian transit).
   - Ingest 3,132 RAG classical knowledge chunks for grounded citations.
   - Generate dynamic 5-category follow-up prompt pills (Career, Romance, Feng Shui, Da Yun Timing, 5 Elements Remedies).
2. In `project/routers/chat.py`:
   - `POST /api/v2/chat/stream` (SSE Server-Sent Events delta token streaming, citations, chips, done event).
   - `POST /api/v2/chat/consult` (Synchronous JSON response for audit/export).
   - `POST /api/v2/chat/anonymized-feedback` (Opt-in QA collection for HITL pipeline).
3. In `project/main.py`:
   - Register and mount `chat_router`.
#### Acceptance Criteria
- [x] SSE streaming endpoint returns valid chunk deltas.
- [x] Synchronous consultation endpoint returns full context + citations + chips.

---

### 🎫 TICKET-CHAT-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CHAT-002`  
**Blocks**: `TICKET-CHAT-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add Floating Chat Drawer launcher icon, slide-out drawer markup (`#floating-chat-drawer`), Co-Pilot split-screen mode toggle, full-screen modal expander, dynamic prompt pills bar, and privacy-consent dialog.
2. In `project/static/style.css` and `public/style.css`:
   - Style drawer, chat bubbles (AI vs User), grounded citation cards, dynamic pills, and typing stream animation in Imperial White & Crimson Red palette.
3. In `project/static/app.js` and `public/app.js`:
   - Implement SSE streaming client reader (`EventSource` / `fetch` reader), auto-scroll, message history, auto-context collector, dynamic pill ranking, export JSON/Markdown, and clear chat functions.
4. In `project/static/i18n.js` and `public/i18n.js`:
   - Add English, Thai, and Chinese translations for all Chat Assistant UI elements.
#### Acceptance Criteria
- [x] Floating Drawer opens seamlessly and transforms to Co-Pilot mode.
- [x] Real-time token streaming works with smooth typing animation.
- [x] Both `project/static/` and `public/` synced (0 diff).

---

### 🎫 TICKET-CHAT-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CHAT-002`..`003`  
**Blocks**: `TICKET-CHAT-005`  
#### Detailed Instructions
1. Create unit and integration test suite in `project/tests/test_chat_assistant.py`.
2. Test SSE streaming endpoint, JSON endpoint, auto-context synthesis, RAG citations, and prompt pills.
3. Run button regression: `python3 scripts/run_button_regression.py`.
4. Run full pytest suite: `python3 -m pytest -v --ignore=project/kaggle_kernel`.
#### Acceptance Criteria
- [x] All tests in `test_chat_assistant.py` pass 100% (11/11).
- [x] 100% pytest pass rate (598/598 tests passed).

---

### 🎫 TICKET-CHAT-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-CHAT-004`  
**Blocks**: `TICKET-CHAT-006`  
#### Detailed Instructions
1. Verify dual-path synchronization between `project/static/` and `public/`.
2. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
3. Verify HF Space publishing payload dry run: `python3 scripts/publish_space_hf.py --dry-run`.
#### Acceptance Criteria
- [x] Zero secret leaks detected across 1,321 files.
- [x] Files perfectly synchronized.

---

### 🎫 TICKET-CHAT-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CHAT-005`  
**Blocks**: None (Delivery Gateway)  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Ensure status is `READY_FOR_PROD`.
3. Synchronize agent definitions and update live docs.
#### Acceptance Criteria
- [x] `code_reviewer.py --review` returns `READY_FOR_PROD`.
- [x] Agent sync checks pass 100%.

---

### 🏛️ ARCHIVED SPRINTS

#### 🎫 Phase 14 — Metaphysics AI Live Consultant Chat Assistant [STATUS: DONE]
- `TICKET-CHAT-001` (Orchestrator Blueprint) — DONE
- `TICKET-CHAT-002` (Backend Chat Engine & SSE Stream Router) — DONE
- `TICKET-CHAT-003` (Frontend Floating Drawer & Co-Pilot UI) — DONE
- `TICKET-CHAT-004` (Pytest & Button Regression Verification) — DONE
- `TICKET-CHAT-005` (DevOps & Dual-Path Sync) — DONE
- `TICKET-CHAT-006` (Safety Audit & Doc Sync) — DONE

#### 🎫 Phase 13 — Imperial White & Crimson Red Theme Overhaul (FengShuiX-Inspired Aesthetic) [STATUS: DONE]
- `TICKET-THEME-001` (Orchestrator Blueprint) — DONE
- `TICKET-THEME-002` (Style.css & Main UI Theme Polish) — DONE
- `TICKET-THEME-003` (Admin & HITL Studio Migration) — DONE
- `TICKET-THEME-004` (Button Regression & Pytest Verification) — DONE
- `TICKET-THEME-005` (Production Delivery & Static Parity) — DONE
- `TICKET-THEME-006` (Safety Audit & Doc Sync) — DONE
#### Acceptance Criteria
- [ ] Status `READY_FOR_PROD` verified.
- [ ] Live docs updated.

---

## 🚀 COMPLETED SPRINT: Phase 12 — Metaphysics Life Path Multi-Scenario Simulation & What-If Analyzer
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-SIM-001` | `orchestrator` | Architecture Blueprint & Specification | DONE | None |
| `TICKET-SIM-002` | `developer` | Backend Multi-Scenario Simulation Engine & Router (`simulation_engine.py`, `simulation.py`, `main.py`) | DONE | `TICKET-SIM-001` |
| `TICKET-SIM-003` | `developer` | Frontend Scenario Comparison UI (`index.html`, `style.css`, `app.js`, `i18n.js`) | DONE | `TICKET-SIM-001` |
| `TICKET-SIM-004` | `qa_tester` | Unit & Regression Test Suite (`test_simulation_engine.py`) | DONE | `TICKET-SIM-002`..`003` |
| `TICKET-SIM-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-SIM-004` |
| `TICKET-SIM-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-SIM-005` |

---

### 🎫 TICKET-SIM-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-SIM-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate 4-dimension trajectory scoring math across 2026-2030 transit pillars and scenario element alignment.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-SIM-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SIM-001`  
**Blocks**: `TICKET-SIM-004`  
#### Detailed Instructions
1. Create `project/core/simulation_engine.py`:
   - Implement `simulate_scenarios(birth_datetime, scenarios, horizon_years)`.
   - Implement `get_preset_scenarios()`.
2. Create `project/routers/simulation.py` and register in `project/main.py`.
#### Acceptance Criteria
- [x] Returns multi-scenario comparison data and optimal path recommendation.

---

### 🎫 TICKET-SIM-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SIM-001`  
**Blocks**: `TICKET-SIM-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add `#scenario-simulation-card` with scenario selector checkboxes, custom input, and comparison view.
2. In `style.css` and `public/style.css`: Add styles for scenario comparison cards and optimal path badge.
3. In `app.js` and `public/app.js`: Implement `runScenarioSimulation()` and `renderSimulationComparison()`.
4. In `i18n.js` and `public/i18n.js`: Add translations across TH, EN, ZH.
#### Acceptance Criteria
- [x] Comparison table and scenario cards render smoothly.

---

### 🎫 TICKET-SIM-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SIM-002`..`003`  
**Blocks**: `TICKET-SIM-005`  
#### Detailed Instructions
1. Create `project/tests/test_simulation_engine.py`.
2. Run full pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (74/74 passed).

---

### 🎫 TICKET-SIM-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-SIM-004`  
**Blocks**: `TICKET-SIM-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-SIM-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SIM-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 11 — LuoPan 24-Mountain Energy Heatmap & Dream Symbolism Decoder
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-SYNTH-001` | `orchestrator` | Architecture Blueprint & Specification | DONE | None |
| `TICKET-SYNTH-002` | `developer` | Backend LuoPan 24-Mountain, Heatmap & Dream Decoder Engine (`luopan_dream_engine.py`, `luopan_dream.py`, `main.py`) | DONE | `TICKET-SYNTH-001` |
| `TICKET-SYNTH-003` | `developer` | Frontend LuoPan Compass, 9-Grid Heatmap & Dream Decoder UI (`index.html`, `style.css`, `app.js`, `i18n.js`) | DONE | `TICKET-SYNTH-001` |
| `TICKET-SYNTH-004` | `qa_tester` | Unit & Regression Test Suite (`test_luopan_dream_engine.py`) | DONE | `TICKET-SYNTH-002`..`003` |
| `TICKET-SYNTH-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-SYNTH-004` |
| `TICKET-SYNTH-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-SYNTH-005` |

---

### 🎫 TICKET-SYNTH-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-SYNTH-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Define 24-Mountain degree ranges, Period 9 flying stars base chart, and dream symbol mappings to 64 Hexagrams & Sattaleka numbers.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-SYNTH-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNTH-001`  
**Blocks**: `TICKET-SYNTH-004`  
#### Detailed Instructions
1. Create `project/core/luopan_dream_engine.py`:
   - Implement `calculate_luopan(facing_degree: float, period: int = 9)`.
   - Implement `interpret_dream(dream_text: str, user_day_master: Optional[str] = None)`.
2. Create `project/routers/luopan_dream.py` and register in `main.py`.
#### Acceptance Criteria
- [x] Returns valid 24-mountain sector energy analysis and dream symbol decoding.

---

### 🎫 TICKET-SYNTH-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNTH-001`  
**Blocks**: `TICKET-SYNTH-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add `#luopan-compass-card` with angle slider and 9-Grid Floorplan Energy Heatmap.
   - Add `#dream-interpreter-card` with input box and dream result display.
2. In `style.css` and `public/style.css`: Add styles for 9-grid heatmap and dream tags.
3. In `app.js` and `public/app.js`: Implement `calcLuoPan(deg)` and `analyzeDream(text)`.
4. In `i18n.js` and `public/i18n.js`: Add translations across TH, EN, ZH.
#### Acceptance Criteria
- [x] UI components render and interact smoothly.

---

### 🎫 TICKET-SYNTH-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNTH-002`..`003`  
**Blocks**: `TICKET-SYNTH-005`  
#### Detailed Instructions
1. Create `project/tests/test_luopan_dream_engine.py`.
2. Run full pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-SYNTH-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-SYNTH-004`  
**Blocks**: `TICKET-SYNTH-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-SYNTH-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNTH-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 10 — Astrological Calendar & Auspicious Date Selector
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-CALENDAR-001` | `orchestrator` | Architecture Blueprint & Calendar Engine Spec | DONE | None |
| `TICKET-CALENDAR-002` | `developer` | Backend Calendar Calculation Engine & Router (`calendar_engine.py`, `calendar.py`, `main.py`) | DONE | `TICKET-CALENDAR-001` |
| `TICKET-CALENDAR-003` | `developer` | Frontend Interactive Calendar & Date Selector UI (`index.html`, `style.css`, `app.js`, `i18n.js`) | DONE | `TICKET-CALENDAR-001` |
| `TICKET-CALENDAR-004` | `qa_tester` | Unit & Regression Test Suite (`test_calendar_engine.py`) | DONE | `TICKET-CALENDAR-002`..`003` |
| `TICKET-CALENDAR-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-CALENDAR-004` |
| `TICKET-CALENDAR-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-CALENDAR-005` |

---

### 🎫 TICKET-CALENDAR-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-CALENDAR-002`..`003`  
#### Detailed Instructions
1. Formulate 12 Duty Officers, 28 Mansions, and 24 Solar Terms calendar algorithms.
2. Formulate Auspicious and Inauspicious rating systems for date selection.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-CALENDAR-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CALENDAR-001`  
**Blocks**: `TICKET-CALENDAR-004`  
#### Detailed Instructions
1. Create `project/core/calendar_engine.py`:
   - Implement `generate_monthly_calendar(year, month)`.
   - Implement `find_best_dates(intent, start_date, days_ahead, user_day_master)`.
2. Create `project/routers/calendar.py` and mount in `project/main.py`.
#### Acceptance Criteria
- [x] Valid calendar data generation and date selection recommendations.

---

### 🎫 TICKET-CALENDAR-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CALENDAR-001`  
**Blocks**: `TICKET-CALENDAR-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add `#calendar-view-card` with month switcher, activity filter pills, and date grid.
2. In `style.css` and `public/style.css`: Add calendar grid and auspicious badges styles.
3. In `app.js` and `public/app.js`: Implement `loadMonthCalendar(year, month)` and `filterCalendarIntent(intent)`.
4. In `i18n.js` and `public/i18n.js`: Add translations.
#### Acceptance Criteria
- [x] Interactive calendar displays and filters dates seamlessly.

---

### 🎫 TICKET-CALENDAR-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CALENDAR-002`..`003`  
**Blocks**: `TICKET-CALENDAR-005`  
#### Detailed Instructions
1. Create `project/tests/test_calendar_engine.py`.
2. Run pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-CALENDAR-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-CALENDAR-004`  
**Blocks**: `TICKET-CALENDAR-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-CALENDAR-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-CALENDAR-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 9 — Multi-Profile Synastry & Partner Compatibility Matrix
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-SYNASTRY-001` | `orchestrator` | Architecture Blueprint & Synastry Specification | DONE | None |
| `TICKET-SYNASTRY-002` | `developer` | Backend Synastry Calculation Engine & Router (`synastry_engine.py`, `synastry.py`, `main.py`) | DONE | `TICKET-SYNASTRY-001` |
| `TICKET-SYNASTRY-003` | `developer` | Frontend Dual-Profile Input & Synastry Result Card (`index.html`, `style.css`, `app.js`, `i18n.js`) | DONE | `TICKET-SYNASTRY-001` |
| `TICKET-SYNASTRY-004` | `qa_tester` | Unit & Regression Test Suite (`test_synastry_engine.py`) | DONE | `TICKET-SYNASTRY-002`..`003` |
| `TICKET-SYNASTRY-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-SYNASTRY-004` |
| `TICKET-SYNASTRY-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-SYNASTRY-005` |

---

### 🎫 TICKET-SYNASTRY-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-SYNASTRY-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate Synastry scoring weights:
   - Day Master Stem Affinity (30 pts): Combination = 30, Generating = 25, Same Element = 20, Overcoming = 10.
   - Day Branch (Spouse Palace) Harmony (30 pts): 6-Combination = 30, 3-Harmony = 25, Neutral = 15, Clash = 5, Harm/Punishment = 5.
   - Five Elements Balance Complementarity (20 pts): Complementary deficit fill = 20, Balanced = 15, Competing = 8.
   - Year/Month Pillars Resonance (20 pts): Year Stem/Branch compatibility.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-SYNASTRY-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNASTRY-001`  
**Blocks**: `TICKET-SYNASTRY-004`  
#### Detailed Instructions
1. Create `project/core/synastry_engine.py`:
   - Implement `calculate_synastry(chart_a, chart_b)`.
   - Provide breakdown for Romance, Business, Communication, Stability.
2. Create `project/routers/synastry.py` and register in `main.py`.
#### Acceptance Criteria
- [x] Returns valid synastry calculation with score and aspect breakdowns.

---

### 🎫 TICKET-SYNASTRY-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNASTRY-001`  
**Blocks**: `TICKET-SYNASTRY-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add Synastry Mode toggle checkbox `#toggle-synastry-mode`.
   - Add Partner B profile form inputs `#partner-b-form-section`.
   - Add `#synastry-result-card` to display composite score and pillar interactions.
2. In `style.css` and `public/style.css`: Add styles for synastry score gauge and comparison table.
3. In `app.js` and `public/app.js`: Implement `toggleSynastryMode()` and `calcSynastry()`.
#### Acceptance Criteria
- [x] Synastry UI toggles smoothly and displays dual-profile comparison.

---

### 🎫 TICKET-SYNASTRY-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNASTRY-002`..`003`  
**Blocks**: `TICKET-SYNASTRY-005`  
#### Detailed Instructions
1. Create `project/tests/test_synastry_engine.py`.
2. Run full pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-SYNASTRY-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-SYNASTRY-004`  
**Blocks**: `TICKET-SYNASTRY-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-SYNASTRY-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-SYNASTRY-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 8 — Metaphysics AI Voice & Speech Synthesis (TTS / STT)
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-VOICE-001` | `orchestrator` | Architecture Blueprint & Voice Engine Specification | DONE | None |
| `TICKET-VOICE-002` | `developer` | Client-Side TTS/STT Engine in `voice_engine.js` & `app.js` | DONE | `TICKET-VOICE-001` |
| `TICKET-VOICE-003` | `developer` | Audio Player Bar & Microphone UI Components (`index.html`, `style.css`, `i18n.js`) | DONE | `TICKET-VOICE-001` |
| `TICKET-VOICE-004` | `qa_tester` | Unit & Regression Test Suite (`test_voice_speech_engine.py`) | DONE | `TICKET-VOICE-002`..`003` |
| `TICKET-VOICE-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-VOICE-004` |
| `TICKET-VOICE-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-VOICE-005` |

---

### 🎫 TICKET-VOICE-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-VOICE-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate Web Speech Synthesis & Recognition architecture:
   - TTS Engine: Match language codes (`th-TH`, `en-US`, `zh-CN`) to available browser voices.
   - STT Engine: Bind SpeechRecognition event listeners (`onresult`, `onerror`, `onend`) to `#query` textarea.
   - Audio Controls: Play, Pause, Resume, Stop, 0.75x - 1.5x speed rate.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-VOICE-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-VOICE-001`  
**Blocks**: `TICKET-VOICE-004`  
#### Detailed Instructions
1. Create `project/static/voice_engine.js` and `public/voice_engine.js`:
   - Implement `speakText(text, lang, rate)`, `pauseSpeech()`, `resumeSpeech()`, `stopSpeech()`.
   - Implement `startVoiceRecognition(targetInputId, lang, onStatusChange)`.
   - Provide fallback when speech synthesis or recognition is unsupported.
#### Acceptance Criteria
- [x] Speech functions work smoothly and export cleanly to `window.HoroVoice`.

---

### 🎫 TICKET-VOICE-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-VOICE-001`  
**Blocks**: `TICKET-VOICE-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add microphone dictation button `#btn-voice-input` next to question `#query`.
   - Add `#audio-player-bar` with play/pause, stop, speed buttons, and animated waveform bars.
   - Add `🔊 ฟังบทพยากรณ์เสียง AI` buttons to AI interpretation output cards.
2. In `style.css` and `public/style.css`: Add styles for audio bar, pulsating mic button, and waveform animation.
3. In `i18n.js` and `public/i18n.js`: Add voice translations in TH, EN, ZH.
#### Acceptance Criteria
- [x] Voice mic button and audio player bar render with glassmorphic styling.

---

### 🎫 TICKET-VOICE-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-VOICE-002`..`003`  
**Blocks**: `TICKET-VOICE-005`  
#### Detailed Instructions
1. Create `project/tests/test_voice_speech_engine.py`.
2. Run full pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-VOICE-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-VOICE-004`  
**Blocks**: `TICKET-VOICE-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-VOICE-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-VOICE-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 7 — Interactive DaYun/LiuNian Timeline Scrubber & Live Sky Transit Clock
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-TRANSIT-001` | `orchestrator` | Architecture Blueprint & Timeline Transit Specification | DONE | None |
| `TICKET-TRANSIT-002` | `developer` | Stem-Branch Interaction Engine in `transit_engine.py` | DONE | `TICKET-TRANSIT-001` |
| `TICKET-TRANSIT-003` | `developer` | Live Sky Clock & Interactive Timeline Scrubber UI (`index.html`, `style.css`, `app.js`) | DONE | `TICKET-TRANSIT-001` |
| `TICKET-TRANSIT-004` | `qa_tester` | Unit & Regression Test Suite (`test_dayun_transit_timeline.py`) | DONE | `TICKET-TRANSIT-002`..`003` |
| `TICKET-TRANSIT-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-TRANSIT-004` |
| `TICKET-TRANSIT-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-TRANSIT-005` |

---

### 🎫 TICKET-TRANSIT-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-TRANSIT-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate Stem-Branch interaction taxonomy:
   - 6 Heavenly Stem Combinations (天干五合): 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火.
   - 6 Earthly Branch Clashes (地支六沖): 子午沖, 丑未沖, 寅申沖, 卯酉沖, 辰戌沖, 巳亥沖.
   - 6 Earthly Branch Combinations (地支六合): 子丑合, 寅亥合, 卯戌合, 辰酉合, 巳申合, 午未合.
   - 3 Earthly Branch Harmonies (地支三合局): 申子辰合水, 亥卯未合木, 寅午戌合火, 巳酉丑合金.
   - 6 Earthly Branch Harms (地支六害): 子未害, 丑午害, 寅巳害, 卯辰害, 申亥害, 酉戌害.
3. Formulate Live Sky Clock mathematical formula.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-TRANSIT-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-TRANSIT-001`  
**Blocks**: `TICKET-TRANSIT-004`  
#### Detailed Instructions
1. Create `project/core/transit_engine.py`:
   - Compute Stem Combinations, Branch Clashes, Combinations, Harmonies, Harms, and Punishments.
   - Provide `analyze_transit_interactions(natal_chart, transit_year, transit_age)` method.
   - Provide `get_live_sky_pillars(now_datetime, longitude, utc_offset)` method.
#### Acceptance Criteria
- [x] Correctly identifies clashes and harmonies against Day Master and Natal Pillars.

---

### 🎫 TICKET-TRANSIT-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-TRANSIT-001`  
**Blocks**: `TICKET-TRANSIT-004`  
#### Detailed Instructions
1. In `project/static/index.html` and `public/index.html`:
   - Add `#transit-clock-widget` to navbar / top area showing live ticking sky pillars.
   - Add `#dayun-timeline-card` in results section with interactive slider (Age 1 - 100), active Da Yun badge, active Liu Nian badge, and dynamic interaction alert tags.
2. In `style.css` and `public/style.css`: Add styles for timeline slider, live clock, and aspect badges.
3. In `app.js` and `public/app.js`: Implement `startLiveSkyClock()`, `initDaYunTimeline()`, and `onTimelineScrub(age)`.
#### Acceptance Criteria
- [x] Live clock ticks smoothly every minute.
- [x] Timeline slider instantly updates active pillars and interaction alerts.

---

### 🎫 TICKET-TRANSIT-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-TRANSIT-002`..`003`  
**Blocks**: `TICKET-TRANSIT-005`  
#### Detailed Instructions
1. Create `project/tests/test_dayun_transit_timeline.py`.
2. Run full pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-TRANSIT-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-TRANSIT-004`  
**Blocks**: `TICKET-TRANSIT-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization checks.
2. Verify production deployment hygiene.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-TRANSIT-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-TRANSIT-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 6 — Production Delivery, PWA Offline Support & Consultation Report Exporter
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-DELIVERY-001` | `orchestrator` | Architecture Blueprint & Delivery Specification | DONE | None |
| `TICKET-DELIVERY-002` | `developer` | PWA Manifest & Offline Service Worker (`manifest.json`, `sw.js`) | DONE | `TICKET-DELIVERY-001` |
| `TICKET-DELIVERY-003` | `developer` | Printable & Exportable Consultation Report Generator (`app.js`, `style.css`) | DONE | `TICKET-DELIVERY-001` |
| `TICKET-DELIVERY-004` | `qa_tester` | Unit & Integration Regression Suite (`test_pwa_and_report_export.py`) | DONE | `TICKET-DELIVERY-002`..`003` |
| `TICKET-DELIVERY-005` | `devops` | Production Delivery Release & HF Spaces Sync | DONE | `TICKET-DELIVERY-004` |
| `TICKET-DELIVERY-006` | `code_reviewer` | Final Code Review & Live Documentation Sync | DONE | `TICKET-DELIVERY-005` |

---

### 🎫 TICKET-DELIVERY-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-DELIVERY-002`..`003`  
#### Detailed Instructions
1. Review delivery requirements in `plans/plan.md` and finalize Phase 6 Grill Report.
2. Formulate PWA caching architecture: Cache static HTML, CSS, JavaScript, fonts, and SVG graphics for 100% offline calculations.
3. Formulate Printable Consultation Report template format.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-DELIVERY-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-DELIVERY-001`  
**Blocks**: `TICKET-DELIVERY-004`  
#### Detailed Instructions
1. Create `project/static/manifest.json` and `public/manifest.json`:
   - Specify `name`, `short_name`, `theme_color`, `background_color`, `display: standalone`, and icons.
2. Create `project/static/sw.js` and `public/sw.js`:
   - Implement Service Worker caching static assets (`/`, `/index.html`, `/admin.html`, `/style.css`, `/app.js`, `/i18n.js`).
   - Implement cache-first network-fallback strategy.
3. Register Service Worker in `index.html` and `admin.html`.
#### Acceptance Criteria
- [x] `manifest.json` and `sw.js` pass syntax validation and register in browser.

---

### 🎫 TICKET-DELIVERY-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-DELIVERY-001`  
**Blocks**: `TICKET-DELIVERY-004`  
#### Detailed Instructions
1. In `style.css` and `public/style.css`: Add comprehensive `@media print` styles.
2. In `app.js` and `public/app.js`: Add `exportConsultationReport()` assembling client name, birth chart, active discipline SVGs, and AI interpretation summary.
3. Add `📄 ส่งออกรายงาน (Export Report)` button to results action bar.
#### Acceptance Criteria
- [x] Clean formatted consultation report exports without dark background waste.

---

### 🎫 TICKET-DELIVERY-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-DELIVERY-002`..`003`  
**Blocks**: `TICKET-DELIVERY-005`  
#### Detailed Instructions
1. Create `project/tests/test_pwa_and_report_export.py`.
2. Run pytest suite and UI button regression suite.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites.

---

### 🎫 TICKET-DELIVERY-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-DELIVERY-004`  
**Blocks**: `TICKET-DELIVERY-006`  
#### Detailed Instructions
1. Run secret leak scan and agent synchronization.
2. Verify production deployment readiness.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync.

---

### 🎫 TICKET-DELIVERY-006 | `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-DELIVERY-005`  
**Blocks**: None  
#### Detailed Instructions
1. Verify `READY_FOR_PROD` status.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Delivery complete and documented.

---

## 🚀 COMPLETED SPRINT: Phase 5 — Multi-Language Internationalization (i18n) & Localized Interpretation
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-I18N-001` | `orchestrator` | Architecture Blueprint, Schema & Translation Dictionary Specification | DONE | None |
| `TICKET-I18N-002` | `developer` | Client-Side i18n Engine & UI Navbar Switcher Integration (`i18n.js`, `app.js`, `index.html`, `admin.html`) | DONE | `TICKET-I18N-001` |
| `TICKET-I18N-003` | `developer` | Localized SVG Vector Symbolic Chart Generators in `svg_generator.py` | DONE | `TICKET-I18N-001` |
| `TICKET-I18N-004` | `developer` | Backend Multi-Lingual Prompt Directives in `question_focus_router.py` & API Routers | DONE | `TICKET-I18N-001` |
| `TICKET-I18N-005` | `qa_tester` | Unit & Integration Regression Suite (`test_i18n.py`, Pytest 536/536, 33/33 Button Regression) | DONE | `TICKET-I18N-002`..`004` |
| `TICKET-I18N-006` | `devops` | CI/CD Production Release to HF Spaces & Live Playwright Verification | DONE | `TICKET-I18N-005` |
| `TICKET-I18N-007` | `code_reviewer` | Pre-Deployment Safety Audit & Live Documentation Sync | DONE | `TICKET-I18N-006` |

---

### 🎫 TICKET-I18N-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-I18N-002`..`004`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate 3-language taxonomy (Thai `th`, English `en`, Simplified/Traditional Chinese `zh`):
   - Common UI terms, headings, form labels, buttons, tooltips, validation messages.
   - 16 Metaphysics Discipline names, pillars, palaces, ten gods, trigrams, hexagrams, branches, stems, and life themes.
   - SVG vector chart dictionary mapping.
3. Formulate backend prompt directive templates for target languages.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets allocated in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-I18N-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-I18N-001`  
**Blocks**: `TICKET-I18N-005`  
#### Detailed Instructions
1. Create `public/i18n.js` and `project/static/i18n.js` with comprehensive translations for TH, EN, ZH:
   - Provide `initI18n()`, `setLanguage(lang)`, `getLanguage()`, and `t(key, defaultVal)` helper functions.
   - Support `data-i18n="key"` attribute auto-translation and dynamic string formatting.
2. In `index.html` & `admin.html` (both `public/` and `project/static/`):
   - Add glassmorphic language toggle selector (`TH` | `EN` | `ZH`) to the top navbar.
   - Bind `changeLanguage` event listener and apply translation matrix on load and change.
3. In `app.js`: Ensure dynamic calculations, result cards, and alert messages use `t()` translation helper.
#### Acceptance Criteria
- [x] Language toggle instantly switches UI text without page reload.
- [x] Selected language is persisted in `localStorage.getItem('horo_lang')`.
- [x] 0 `[object Object]` leaks across all 16 disciplines in all languages.

---

### 🎫 TICKET-I18N-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-I18N-001`  
**Blocks**: `TICKET-I18N-005`  
#### Detailed Instructions
1. Update `project/core/svg_generator.py`:
   - Add `lang: str = "th"` parameter to all SVG generator functions (`generate_bazi_svg`, `generate_ziwei_svg`, `generate_qimen_svg`, `generate_liuren_svg`, `generate_iching_svg`, `generate_xuankong_svg`, `generate_zeji_svg`, `generate_thai_vedic_svg`, `generate_uranian_svg`, `generate_tai_yi_svg`, `generate_liu_yao_svg`, `generate_meihua_svg`, `generate_sanhe_svg`, `generate_qizheng_svg`, `generate_mianxiang_svg`, `generate_numerology_svg`, `generate_multimodal_matrix_svg`).
   - Provide localized text dictionaries for chart titles, subtitles, coordinates, legend labels, and palace titles.
   - Maintain 100% backward compatibility when `lang` is omitted.
#### Acceptance Criteria
- [x] All SVG generators accept `lang` parameter and render localized text cleanly.
- [x] Responsive `viewBox="0 0 800 600"` and glassmorphic styling preserved.

---

### 🎫 TICKET-I18N-004 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-I18N-001`  
**Blocks**: `TICKET-I18N-005`  
#### Detailed Instructions
1. In `project/schemas/` & `project/routers/v2.py` & `project/routers/debate.py`:
   - Add `language: Optional[str] = "th"` to request models (`InterpretationRequest`, `FocusedInterpretationRequest`, `UnifiedCalculateRequest`).
2. In `project/core/question_focus_router.py`:
   - Update `generate_domain_directive_prompt(domain, request, language="th")` with target language instructions:
     - `th`: "จงตอบเป็นภาษาไทยที่ไพเราะ สละสลวย ชัดเจน ลึกซึ้งตามหลักวิชา"
     - `en`: "Please provide the comprehensive analysis in fluent, professional, and clear English, citing classical metaphysical principles."
     - `zh`: "請使用繁體/簡體中文進行專業、深入且詳盡的命理分析，嚴格遵循古籍經典法度。"
#### Acceptance Criteria
- [x] Backend routing passes language parameter to LLM system prompt directives.
- [x] Zero breaking changes to existing endpoints when `language` is omitted.

---

### 🎫 TICKET-I18N-005 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-I18N-002`..`004`  
**Blocks**: `TICKET-I18N-006`  
#### Detailed Instructions
1. Create `project/tests/test_i18n.py` verifying all 3 languages.
2. Run pytest suite: `python3 -m pytest -v --ignore=project/kaggle_kernel`.
3. Run UI button regression suite: `python3 scripts/run_button_regression.py`.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (536/536 tests passed).
- [x] 33/33 UI & API button regression passed.

---

### 🎫 TICKET-I18N-006 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-I18N-005`  
**Blocks**: `TICKET-I18N-007`  
#### Detailed Instructions
1. Run secret scan: 0 secrets leaked across modified files.
2. Run agent sync checks: `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check`.
3. Verify live deployment hygiene and readiness.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync, release hygiene verified.

---

### 🎫 TICKET-I18N-007 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-I18N-006`  
**Blocks**: None  
#### Detailed Instructions
1. Run pre-deployment review and safety audit.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Status `READY_FOR_PROD` verified.

---

---

### 🎫 TICKET-LLM-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-LLM-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate 6-tier failover routing protocol:
   - Tier 1: Cloudflare Workers AI (`@cf/meta/llama-3.1-8b-instruct`, `@cf/qwen/qwen2.5-7b-instruct`)
   - Tier 2: Google Gemini (Gemini 2.5/1.5 Flash via `GEMINI_API_KEY` / `GOOGLE_API_KEY`)
   - Tier 3: OpenAI / CODEX_PRO proxy (`OPENAI_API_KEY`, `CODEX_PRO_BASE_URL`)
   - Tier 4: Anthropic Claude proxy (`ANTHROPIC_API_KEY` / `CLAUDE_API_KEY`)
   - Tier 5: Local Ollama Workhorse (`OLLAMA_BASE_URL`, default `http://127.0.0.1:11434`)
   - Tier 6: Canonical Deterministic Synthesizer (always safe fallback)
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets allocated in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-LLM-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-LLM-001`  
**Blocks**: `TICKET-LLM-004`  
#### Detailed Instructions
1. Create `project/core/llm_gateway.py` with `LLMGateway` class:
   - Methods: `async generate_text(prompt, system_instruction, preferred_provider=None)`, `get_providers_status()`, `test_provider(provider_key)`.
   - Dynamic circuit breaker (trip after 3 consecutive failures, cooldown 60s).
   - Real-time latency tracking and error counters.
2. Integrate `LLMGateway` into `project/core/model_activation.py` and `project/core/orchestrator_router.py`.
#### Acceptance Criteria
- [x] Multi-tier failover executes gracefully without raising uncaught exceptions.

---

### 🎫 TICKET-LLM-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-LLM-001`  
**Blocks**: `TICKET-LLM-004`  
#### Detailed Instructions
1. In `project/routers/v2.py`: Add `GET /api/v2/llm/providers/status` and `POST /api/v2/llm/route-test`.
2. In `project/static/admin.html` and `public/admin.html`: Add Live LLM Gateway Status card with health indicators and manual provider test button.
#### Acceptance Criteria
- [x] Admin panel displays provider health and test trigger works.

---

### 🎫 TICKET-LLM-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-LLM-002`..`003`  
**Blocks**: `TICKET-LLM-005`  
#### Detailed Instructions
1. Create `project/tests/test_llm_multirouter.py` with mock failure scenarios testing Tier 1 ➔ Tier 2 ➔ Tier 3 ➔ Tier 4 ➔ Tier 5 ➔ Deterministic Fallback.
2. Run pytest suite, UI button regression suite (32/32), and Playwright E2E screenshots.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (522/522 pytest tests passed).

---

### 🎫 TICKET-LLM-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-LLM-004`  
**Blocks**: `TICKET-LLM-006`  
#### Detailed Instructions
1. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
2. Commit, push, and deploy to Hugging Face Spaces.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync, live deployment verified.

---

### 🎫 TICKET-LLM-006 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-LLM-005`  
**Blocks**: None  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Status `READY_FOR_PROD` verified.

---

### 🎫 TICKET-MULTIMODAL-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-MULTIMODAL-002`..`003`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate 16-discipline consensus aggregation algorithm:
   - 4 Metaphysics Super-Families:
     1. Astrological: BaZi (四柱), Zi Wei (紫微), Qi Zheng (七政), Thai Vedic (โหราศาสตร์ไทย)
     2. Divination / San Shi: Qi Men (奇門), Da Liu Ren (六壬), Tai Yi (太乙), I Ching (易經), Liu Yao (六爻), Mei Hua (梅花)
     3. Geomancy: Xuan Kong (玄空), San He (三合), Ze Ji (擇吉)
     4. Numerology & Physiognomy: Satta-Lek (สัตตเลข), Mian Xiang (麻衣神相), Western Uranian (ยูเรเนียน)
   - 6 Core Life Themes: Career (ธุรกิจการงาน), Finance (การเงินโชคลาภ), Love (ความรักคู่ครอง), Health (สุขภาพพลานามัย), Family/Home (ครอบครัวและที่อยู่อาศัย), Timing (กาลเวลาและจังหวะชีวิต).
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets allocated in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-MULTIMODAL-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-MULTIMODAL-001`  
**Blocks**: `TICKET-MULTIMODAL-004`  
#### Detailed Instructions
1. In `project/core/svg_generator.py`: Implement `generate_multimodal_matrix_svg(data, title)` with 16-spoke radial radar mandala, gold glowing center, and elemental harmony distribution indicators.
#### Acceptance Criteria
- [x] `generate_multimodal_matrix_svg` produces clean, valid SVG with responsive `viewBox="0 0 800 600"`.

---

### 🎫 TICKET-MULTIMODAL-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-MULTIMODAL-001`  
**Blocks**: `TICKET-MULTIMODAL-004`  
#### Detailed Instructions
1. In `project/static/index.html` & `public/index.html`: Add Unified Multimodal Matrix section with 6 life theme buttons (`#btn-multimodal-matrix`, `#multimodal-matrix-card`).
2. In `project/static/app.js` & `public/app.js`: Implement `calcMultimodalMatrix(domain)` and `switchFocusDomain(domain)` with client SVG generator, consensus score meter, and cross-discipline synthesis table.
#### Acceptance Criteria
- [x] Users can toggle between 6 life domains and see real-time updated consensus metrics and SVG charts.
- [x] Zero `[object Object]` leaks.

---

### 🎫 TICKET-MULTIMODAL-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-MULTIMODAL-002`..`003`  
**Blocks**: `TICKET-MULTIMODAL-005`  
#### Detailed Instructions
1. Write unit and integration tests in `project/tests/test_multimodal_matrix.py`.
2. Run pytest suite, UI button regression suite (32/32), and Playwright E2E screenshots.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (517+ pytest tests passed).

---

### 🎫 TICKET-MULTIMODAL-005 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-MULTIMODAL-004`  
**Blocks**: `TICKET-MULTIMODAL-006`  
#### Detailed Instructions
1. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
2. Commit, push, and deploy to Hugging Face Spaces.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync, live deployment verified.

---

### 🎫 TICKET-MULTIMODAL-006 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-MULTIMODAL-005`  
**Blocks**: None  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Status `READY_FOR_PROD` verified.

---

### 🎫 TICKET-PHASE2-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-PHASE2-002`..`004`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Establish canonical schemas for all 7 extended disciplines:
   - Tai Yi: accumulated years, 16 paths, 8 palaces, 12 heavenly generals.
   - Liu Yao: Na Jia earthly branches, 6 relatives, 6 celestial animals, moving line.
   - Mei Hua: upper/lower trigram, body/use, mutual/resulting hexagrams.
   - San He: 24 mountains, sitting/facing, 12 life stage water methods.
   - Qi Zheng: 7 governors, 4 extras, 28 mansions, 12 zodiac houses.
   - Mian Xiang: 12 facial palaces, 100 age positions, 3 courts, 5 features.
   - Satta-Lek: 7 bases, 4 rows, 21 planetary strengths, Chaldean root & 7 houses.
3. Define glassmorphic SVG tokens (dark gradient, gold borders, cyan/purple highlights, 800x600 responsive viewBox).
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets allocated in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-PHASE2-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-PHASE2-001`  
**Blocks**: `TICKET-PHASE2-005`  
#### Detailed Instructions
1. In `project/core/svg_generator.py`: Implement `generate_tai_yi_svg(data)` with 16-path circular palace wheel and `generate_liu_yao_svg(data)` with 6-line Na Jia plate.
2. In `project/static/app.js` and `public/app.js`: Implement `calcTaiYi()` and `calcLiuYao()` with interactive form controls (year, question, hexagram, lines), canonical tables, and SVG rendering.
#### Acceptance Criteria
- [x] Tai Yi and Liu Yao render interactive tables and glassmorphic SVG charts without `[object Object]`.
- [x] All custom input controls respond to user interaction.

---

### 🎫 TICKET-PHASE2-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-PHASE2-001`  
**Blocks**: `TICKET-PHASE2-005`  
#### Detailed Instructions
1. In `project/core/svg_generator.py`: Implement `generate_meihua_svg(data)` with plum blossom hexagram flow and `generate_sanhe_svg(data)` with 24-mountain compass & 12 water methods.
2. In `project/static/app.js` and `public/app.js`: Implement `calcMeiHua()` and `calcSanHe()` with interactive form controls (datetime, sitting degree, water exit degree), canonical tables, and SVG rendering.
#### Acceptance Criteria
- [x] Mei Hua and San He render interactive tables and glassmorphic SVG charts without `[object Object]`.

---

### 🎫 TICKET-PHASE2-004 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-PHASE2-001`  
**Blocks**: `TICKET-PHASE2-005`  
#### Detailed Instructions
1. In `project/core/svg_generator.py`: Implement `generate_qizheng_svg(data)`, `generate_mianxiang_svg(data)`, and `generate_numerology_svg(data)`.
2. In `project/static/app.js` and `public/app.js`: Implement `calcQiZheng()`, `calcMianXiang()`, and `calcNumerology()` with interactive form controls, canonical tables, and SVG rendering.
#### Acceptance Criteria
- [x] Qi Zheng, Mian Xiang, and Satta-Lek render interactive tables and glassmorphic SVG charts without `[object Object]`.

---

### 🎫 TICKET-PHASE2-005 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-PHASE2-002`..`004`  
**Blocks**: `TICKET-PHASE2-006`  
#### Detailed Instructions
1. Run pytest suite: `python3 -m pytest -v --ignore=project/kaggle_kernel`.
2. Run UI button regression suite: `python3 scripts/run_button_regression.py`.
3. Run Playwright E2E screenshots suite: `python3 scripts/run_e2e_screenshots.py`.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (515/515 pytest tests passed).
- [x] 31/31 UI buttons passed, zero object rendering leaks.

---

### 🎫 TICKET-PHASE2-006 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-PHASE2-005`  
**Blocks**: `TICKET-PHASE2-007`  
#### Detailed Instructions
1. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
2. Run agent sync checks: `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check`.
3. Commit and push to `origin/main`, deploy to Hugging Face Spaces.
#### Acceptance Criteria
- [x] 0 secret leaks, 100% agent sync, live deployment verified.

---

### 🎫 TICKET-PHASE2-007 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-PHASE2-006`  
**Blocks**: None  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Update live documentation in `PROJECT_TASKS.md` and report to user.
#### Acceptance Criteria
- [x] Status `READY_FOR_PROD` verified.

---
├───────────────────────────────────────────────────────────────────────────────┤
│ • 100% Field & Math Parity with Bazi.Fengshuix.com reference case (ป๋อง กพล)   │
│ • True Solar Time gamma fractional equation of time precision (0.01 min match)│
│ • Four Pillars 辛亥/丁酉/甲申/乙丑, Ming Gua Kua 6 乾 (Qian), Favorable elements│
│ • 10 Profiles & 5 Structures percentage algorithm exact match                 │
│ • Da Yun 12-cycle navigation + 12x13 Annual Cells grid + General Stars matrix │
│ • Complete responsive standalone HTML generator (project/core/bazi_display.py)│
│ • Full Pytest suite (508/508 PASS 100%), 0 agent sync drift                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 RECENT COMPLETED SPRINT: BaZi Fengshuix.com Complete Replication & HTML Display Component
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-001` | `developer` | Align `bazi_engine.py` algorithms with Fengshuix mathematical model (Ten God IR/DR, favorable elements, 10 profiles weights) | DONE | None |
| `TICKET-002` | `developer` | Build Top Navbar & True Solar Time alert banner matching Fengshuix design | DONE | `TICKET-001` |
| `TICKET-003` | `developer` | Build 4 Pillars responsive grid with left vertical banner & color-coded elements | DONE | `TICKET-002` |
| `TICKET-004` | `developer` | Implement 5 Structures SVG Radar Spider Chart + 10 Profiles bar chart | DONE | `TICKET-003` |
| `TICKET-005` | `developer` | Implement Symbolic & General Stars matrix by pillar | DONE | `TICKET-004` |
| `TICKET-006` | `developer` | Implement 12 Da Yun Cycles navigation bar + 12x13 Annual Cells grid | DONE | `TICKET-005` |
| `TICKET-007` | `developer` | Integrate `generate_bazi_html()` in `bazi_display.py` with standalone wrapper | DONE | `TICKET-006` |
| `TICKET-008` | `qa_tester` | Reference fixture regression test suite in `project/tests/test_bazi_replication.py` | DONE | `TICKET-007` |
| `TICKET-009` | `qa_tester` | Full project regression verification across all 508 tests (100% PASS) | DONE | `TICKET-008` |
| `TICKET-010` | `code_reviewer` | Pre-deployment security & contract safety audit | DONE | `TICKET-009` |
| `TICKET-011` | `developer` | Fix fractional year gamma equation of time in `solar_time.py` | DONE | `TICKET-001` |
| `TICKET-012` | `developer` | Add root test entry point `tests/test_bazi_engine.py` | DONE | `TICKET-008` |
| `TICKET-013` | `developer` | Add Cold-Start API readiness state machine & sync public static assets | DONE | `TICKET-009` |

---
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer (100% PASS)          │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Interactive Form: วันเกิด 1-7, เดือน 1-12, ปีนักษัตร 1-12, ข้อความวิเคราะห์   │
│ • ผัง 7 ฐาน 4 แถว (ฐานวัน, ฐานเดือน, ฐานปี, ฐานกำลังดาวผลรวม 21 พระเคราะห์)    │
│ • Chaldean Letter Decomposition Grid, ผลรวมชะตา, รากเลข 1-9 & คำพยากรณ์ 7 ภพ  │
│ • SVG Vector Generator คมชัดระดับ Glassmorphism, Pytest 427/427 PASS          │
│ • Full Playwright E2E 22/22 PASS & UI Overlap Check: 0 Overlaps, 0 Overflow   │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Continuous MLOps, Hybrid LLM Provider & Grafana Tuning (100% PASS) │
├───────────────────────────────────────────────────────────────────────────────┤
│ • MLOps threshold-driven auto-finetune trigger (HITL approved count >= 50)    │
│ • Tier 3 Reasoning Proxy (9router / DeepSeek-R1 / Qwen2.5-32B) in AI router   │
│ • Synthetic health monitor latency SLA check (< 5000ms) with degradation alert│
│ • Full Pytest suite (427/427 PASS 100%), UI Button Regression (31/31 PASS)   │
│ • Rust Pre-Deployment Code Review & Safety Audit: READY_FOR_PROD (0 leaks)    │
│ • Synchronized skills & agents across .antigravity, .agents, and .codex (100%)│
└───────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 RECENT COMPLETED SPRINT: All 16 Metaphysics Disciplines E2E Snapshot & Visualizer Upgrade (Phase 1: Core 9 Disciplines + Satta-Lek)
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-VISUAL-001` | `orchestrator` | Common Foundation, Canonical Schema & SVG Glassmorphic Token System | DONE | None |
| `TICKET-VISUAL-002` | `developer` | Zi Wei Dou Shu & BaZi 4-Pillars Interactive Visualizers & SVG Charts | DONE | `TICKET-VISUAL-001` |
| `TICKET-VISUAL-003` | `developer` | Qi Men Dun Jia & Da Liu Ren 4-Plates / 3-Transmissions Visualizers & SVG Charts | DONE | `TICKET-VISUAL-001` |
| `TICKET-VISUAL-004` | `developer` | I Ching / Liu Yao 6-Lines & Xuan Kong 9-Grid Flying Stars Visualizers & SVG Charts | DONE | `TICKET-VISUAL-001` |
| `TICKET-VISUAL-005` | `developer` | Thai Vedic / Jyotish, Western / Uranian & Ze Ji Visualizers & SVG Charts | DONE | `TICKET-VISUAL-001` |
| `TICKET-VISUAL-006` | `qa_tester` | E2E Snapshot Regression Suite & Canonical Doctrinal Verification Gate | DONE | `TICKET-VISUAL-002`..`005` |
| `TICKET-VISUAL-007` | `devops` | Production CI/CD Release, Version Audit & Live Playwright E2E Verification | DONE | `TICKET-VISUAL-006` |

---

## 🚀 RECENT COMPLETED SPRINT: สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer Web Application
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-NUMEROLOGY-001` | `orchestrator` | Architecture Blueprint, 7-Base Schema & Chaldean Gematria Matrix Plan | DONE | None |
| `TICKET-NUMEROLOGY-002` | `developer` | Implement Interactive Visualizer, SVG Generator & Custom Input Controls | DONE | `TICKET-NUMEROLOGY-001` |
| `TICKET-NUMEROLOGY-003` | `qa_tester` | Unit Test Suite & Visual Overlap Automation Verification | DONE | `TICKET-NUMEROLOGY-002` |
| `TICKET-NUMEROLOGY-004` | `devops` | Production CI/CD Release, Version Audit & Live Playwright E2E Verification | DONE | `TICKET-NUMEROLOGY-003` |

---

## 🚀 RECENT COMPLETED SPRINT: Continuous MLOps, Hybrid LLM Provider & Grafana Tuning
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-ROADMAP-001` | `orchestrator` | Architecture Blueprint & Task Breakdown | DONE | None |
| `TICKET-ROADMAP-002` | `developer` | Implement MLOps Auto-Trigger, AI Tier 3 Proxy & Synth Latency SLA | DONE | `TICKET-ROADMAP-001` |
| `TICKET-ROADMAP-003` | `qa_tester` | Unit & Regression Suite Execution | DONE | `TICKET-ROADMAP-002` |
| `TICKET-ROADMAP-004` | `devops` | Environment, Secret Scan & Agent Sync Check | DONE | `TICKET-ROADMAP-003` |
| `TICKET-ROADMAP-005` | `code_reviewer` | Pre-Deployment Safety Audit & Post-Deploy Verification | DONE | `TICKET-ROADMAP-004` |

---

### 🎫 TICKET-ROADMAP-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-ROADMAP-002`  
#### Detailed Instructions
1. Review requirements in `plans/plan.md` and complete Gate 0 Grill Report.
2. Formulate execution blueprint for MLOps threshold trigger, Tier 3 LLM reasoning proxy, and Grafana latency alerting.
#### Acceptance Criteria
- [x] GRILL REPORT generated in `/plans/plan.md`.
- [x] Sub-agent tickets allocated in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-ROADMAP-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-ROADMAP-001`  
**Blocks**: `TICKET-ROADMAP-003`  
#### Detailed Instructions
1. Update `project/hitl_router.py`: Implement `check_and_trigger_auto_finetune()` when approved count crosses `HITL_AUTO_FINETUNE_THRESHOLD` (default 50).
2. Update `project/core/ai_provider_router.py`: Implement Tier 3 Reasoning Proxy (`invoke_reasoning_proxy`) for `deepseek-r1` / `qwen2.5-32b` via 9router / custom base URL.
3. Update `scripts/synthetic_health_monitor.py`: Implement `--max-latency-ms` (default 5000ms) with warning degradation and metric reporting.
4. Implement corresponding unit tests in `project/tests/`.
#### Acceptance Criteria
- [x] MLOps threshold auto-trigger logic implemented with unit test.
- [x] Tier 3 Reasoning Proxy integrated into fallback chain.
- [x] Synthetic health monitor latency SLA check integrated.

---

### 🎫 TICKET-ROADMAP-003 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-ROADMAP-002`  
**Blocks**: `TICKET-ROADMAP-004`  
#### Detailed Instructions
1. Run pytest suite: `python3 -m pytest -v --ignore=project/kaggle_kernel`.
2. Run UI button regression suite: `python3 scripts/run_button_regression.py`.
3. Verify test coverage and error handling for all new components.
#### Acceptance Criteria
- [x] 100% test pass rate across all suites (419/419 pytest tests passed).
- [x] UI button regression 100% passed (31/31 passed).

---

### 🎫 TICKET-ROADMAP-004 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-ROADMAP-003`  
**Blocks**: `TICKET-ROADMAP-005`  
#### Detailed Instructions
1. Run secret scan: `python3 project/core/code_reviewer.py --scan-secrets`.
2. Run agent sync checks: `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check`.
#### Acceptance Criteria
- [x] 0 secret leaks detected across 3,447 files.
- [x] Agent definitions 100% synchronized across .antigravity, .agents, and .codex.

---

### 🎫 TICKET-ROADMAP-005 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-ROADMAP-004`  
**Blocks**: None  
#### Detailed Instructions
1. Run pre-deployment review: `python3 project/core/code_reviewer.py --review`.
2. Verify live docs and final delivery.
#### Acceptance Criteria
- [x] Status `READY_FOR_PROD` verified.
- [x] Documentation updated.

---

## 📜 RECENT COMPLETED SPRINT: Requirement-Grill Gate & Sub-Agent Task Flow
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-GRILL-001` | `orchestrator` | Standalone `requirement-grill-gate` Skill & Spec Blueprint | DONE | None |
| `TICKET-GRILL-002` | `developer` | System Rule 08 & SDLC Workflow Integration | DONE | `TICKET-GRILL-001` |
| `TICKET-GRILL-003` | `qa_tester` | Agent Synchronization & Context Budget Verification | DONE | `TICKET-GRILL-002` |
| `TICKET-GRILL-004` | `devops` | Global Agent Registrations & Codex Compatibility Sync | DONE | `TICKET-GRILL-003` |
| `TICKET-GRILL-005` | `code_reviewer` | Live Documentation & Task Board Audit | DONE | `TICKET-GRILL-004` |

---

### 🎫 TICKET-GRILL-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: None  
**Blocks**: `TICKET-GRILL-002`  
#### Detailed Instructions
1. Design standalone skill `.agents/skills/requirement-grill-gate/SKILL.md` with 9 dimensions.
2. Formulate interview protocol with auto-scan for LOW risk items and interactive `ask_question` for CRITICAL/HIGH items.
3. Define GRILL REPORT template for `/plans/plan.md` with status badges (`✅ APPROVED`, `⚠️ WAIVED`, `🚫 BLOCKED`).
#### Acceptance Criteria
- [x] SKILL.md created with complete 9-dimension interview guide.
- [x] Gate blocking semantics clearly defined.

---

### 🎫 TICKET-GRILL-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-GRILL-001`  
**Blocks**: `TICKET-GRILL-003`  
#### Detailed Instructions
1. Create system rule `.agents/rules/08-grill-gate-enforcement.md`.
2. Update `.agents/skills/sdlc-aisdlc-workflow/SKILL.md` to wire Gate 0 as prerequisite.
3. Update `.agents/workflows/aisdlc.md` lifecycle diagram.
4. Add `requirement-grill-gate` tool to `orchestrator.json` and `orchestrator.md`.
#### Acceptance Criteria
- [x] Rule 08 created and documented.
- [x] SDLC workflow and orchestrator agent definitions updated.

---

### 🎫 TICKET-GRILL-003 | `qa_tester` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-GRILL-002`  
**Blocks**: `TICKET-GRILL-004`  
#### Detailed Instructions
1. Run `python3 scripts/sync_sdlc_agents.py --check --use-python`.
2. Run `python3 scripts/sync_codex_agents.py --check`.
3. Verify SKILL.md frontmatter description stays within context budget (< 100 characters).
#### Acceptance Criteria
- [x] 100% sync check passed across all agent specifications.
- [x] Zero context budget errors.

---

### 🎫 TICKET-GRILL-004 | `devops` | [STATUS: DONE]
**Priority**: HIGH  
**Depends On**: `TICKET-GRILL-003`  
**Blocks**: `TICKET-GRILL-005`  
#### Detailed Instructions
1. Run sync scripts (`sync_sdlc_agents.py --sync` and `sync_codex_agents.py --sync`).
2. Verify manifests in `.antigravity/` and `.codex/`.
#### Acceptance Criteria
- [x] Synced 17 agents and 9 skills across `.antigravity`, `.agents`, and `.codex`.

---

### 🎫 TICKET-GRILL-005 | `code_reviewer` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL  
**Depends On**: `TICKET-GRILL-004`  
**Blocks**: None  
#### Detailed Instructions
1. Update `PROJECT_TASKS.md` and `.agents/AGENTS.md`.
2. Verify end-to-end task flow tracking mechanism from Grill Gate to completion.
#### Acceptance Criteria
- [x] Live documentation updated and synchronized.
- [x] Sub-agent task board fully verifiable.

---

- [x] **Future Roadmap: 16-Domain Metaphysics Expansion, API v2, QFA Benchmark, Rate Limiting & UI Upgrades ([`project/routers/v2.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/routers/v2.py), [`project/core/tai_yi_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/tai_yi_engine.py), [`project/core/liu_yao_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/liu_yao_engine.py), [`project/core/mei_hua_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/mei_hua_engine.py), [`project/core/san_he_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/san_he_engine.py), [`project/core/qi_zheng_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/qi_zheng_engine.py), [`project/core/mian_xiang_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/mian_xiang_engine.py), [`project/core/question_focus_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/question_focus_router.py), [`project/core/rate_limiter.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/rate_limiter.py))**
  - **6 New Metaphysics Engines**: Implemented Tai Yi Shen Shu (太乙神數), Liu Yao (六爻), Mei Hua Yi Shu (梅花易數), San He Feng Shui (三合風水), Qi Zheng Si Yu (七政四餘), and Mian Xiang (麻衣神相) with PyO3 Rust math modules and pure Python fallbacks.
  - **Question-Focused Answering Router (QFA)**: Implemented 6-Domain Question Benchmark classification (Career, Finance, Love, Health, Family, Timing) with multi-engine directive prompt generation and citation enforcement.
  - **API v2 Unified Router**: Added `/api/v2/health`, `/api/v2/calculate/unified`, `/api/v2/interpret/focused`, and `/api/v2/mian_xiang/analyze`.
  - **In-Memory Rate Limiter**: Added token-bucket rate limiter with IP tracking, burst protection, and monthly budget guards.
  - **UI & Regression Hardening**: Added 6 interactive discipline buttons in `index.html` + `app.js`. Extended button regression suite to 31/31 passing tests (100%).
  - **Verified Test Suite**: Full test suite expanded to **353/353 PASSING** tests (100% pass rate).

- [x] **Hermes Agent Full Cloud-Ready Stack & Antigravity Hook Architecture ([`.agents/hooks.json`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/hooks.json), [`.agents/hooks/pre_tool_check.py`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/hooks/pre_tool_check.py), [`.agents/hooks/post_tool_audit.py`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/hooks/post_tool_audit.py), [`.agents/config/gemini_parity.yaml`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/config/gemini_parity.yaml), [`.github/workflows/azure_deploy.yml`](file:///Users/kimlenglim/Project/HoroConsultant/.github/workflows/azure_deploy.yml), [`.github/workflows/ci.yml`](file:///Users/kimlenglim/Project/HoroConsultant/.github/workflows/ci.yml))**

  - **Antigravity Hooks Manifest**: Implemented `.agents/hooks.json` specifying `PreToolUse` command interceptor and `PostToolUse` audit logger conforming to the Antigravity camelCase protojson protocol.
  - **CI Headless Auto-Approval Mode**: Configured `pre_tool_check.py` to recognize `CI=true` and non-interactive environments, returning instantaneous JSON decisions (`allow`/`deny`) without blocking stdin.
  - **Doppler 2-Tier Priority Secrets Sync**: Wired Doppler CLI secret injection into `.github/workflows/azure_deploy.yml` and `.github/workflows/ai_cicd.yml` with fallback to GitHub Repository Secrets per Rule 06.
  - **SDLC & Codex CI Agent Sync Audit**: Integrated `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check` into `.github/workflows/ci.yml` pipeline.
  - **Gemini 3.6/3.7 Parity Engine**: Configured task-specific temperature calibration, self-critique loops, and sliding-window context compression for Gemini 3.6 Medium/Flash and Gemini 3.7 Flash across orchestration, coding, QA, devops, and domain synthesis.

- [x] **Complete Zi Wei Dou Shu & Qi Men Dun Jia Rust Engine Migration & Python Cleanup ([`rust_core/src/ziwei.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/ziwei.rs), [`rust_core/src/qimen.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/qimen.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`project/core/zi_wei_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/zi_wei_engine.py), [`project/core/qi_men_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/qi_men_engine.py))**
  - **Zi Wei Dou Shu Rust Native Binding**: Implemented `calculate_ming_shen_gong`, `calculate_zi_wei_star_branch`, and `calculate_14_main_stars` in Rust PyO3. Integrated into `fast_math.py` (`fast_ziwei_stars`) and `zi_wei_engine.py`.
  - **Qi Men Dun Jia Rust Native Binding**: Implemented `qimen_9palace_matrix` in Rust PyO3 for 4-plate 9-palace matrix placement (Earth Plate, 9 Stars, 8 Doors, 8 Spirits). Integrated into `fast_math.py` (`fast_qimen_matrix`) and `qi_men_engine.py`.
  - **Python Redundant Loop Cleanup**: Eliminated duplicate pure-Python matrix generation loops in favor of unified `fast_math.py` Rust PyO3 acceleration with NumPy zero-overhead fallback.
  - **Verified Test Suite**: Extended [`project/tests/test_rust_extensions.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_rust_extensions.py) — 174/174 Pytest tests PASSED 100%.

- [x] **Phase 2 Rust Extensions: FAISS Dense Vector Search & Xuan Kong 9-Grid Matrix ([`rust_core/src/vector_search.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/vector_search.rs), [`rust_core/src/fengshui.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/fengshui.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`project/rag/vector_store.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/rag/vector_store.py), [`project/core/xuan_kong_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/xuan_kong_engine.py))**

  - **FAISS Dense Vector Rust Native Binding**: Implemented `dense_vector_search` in Rust PyO3 with Rayon parallelization over 768-dim embeddings for sub-millisecond retrieval (< 1ms). Integrated into `vector_store.py` and `fast_math.py`.
  - **Feng Shui Flying Star 9-Grid Rust Matrix**: Implemented `resolve_mountain`, `fly_stars`, and `xuankong_9grid_matrix` in Rust PyO3 for 24-mountain directions and Period 9 Flying Stars chart math. Integrated into `xuan_kong_engine.py` and `fast_math.py`.
  - **Verified Test Suite**: Added [`project/tests/test_rust_extensions.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_rust_extensions.py) — 172/172 Pytest tests PASSED 100%.

- [x] **Kaggle GPU Fine-Tuning Iteration Pipeline Automation ([`scripts/kaggle_notebook_manager.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/kaggle_notebook_manager.py))**
  - Configured automated setup, notebook generation, and metadata verification for `qwen2.5:7b` fine-tuning on Nvidia Tesla T4 GPU.
  - Locked metadata accelerator configuration (`NvidiaTeslaT4`) preserved strictly.

- [x] **Phase 3 Rust Extensions: 100% Rust Metaphysical Engine Coverage & CI/CD ABI3 Audit ([`rust_core/src/thai_vedic.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/thai_vedic.rs), [`rust_core/src/uranian.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/uranian.rs), [`rust_core/src/iching.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/iching.rs), [`rust_core/src/liuren.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/liuren.rs), [`rust_core/src/zeji.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/zeji.rs), [`rust_core/src/numerology.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/numerology.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`.github/workflows/ci.yml`](file:///Users/kimlenglim/Project/HoroConsultant/.github/workflows/ci.yml))**
  - **Full 10-Branch Rust Coverage**: Implemented 6 new Rust modules (`thai_vedic.rs`, `uranian.rs`, `iching.rs`, `liuren.rs`, `zeji.rs`, `numerology.rs`) achieving 100% Rust high-performance math core coverage across all 10 metaphysical calculation branches.
  - **Fast Math Bridge Integration**: Added Python PyO3 bindings in `project/core/fast_math.py` (`fast_thai_lagna`, `fast_thaksa_map`, `fast_uranian_midpoint`, `fast_uranian_sensitive_point`, `fast_liuren_heaven_plate`, `fast_zeji_duty_officer`, `fast_satta_lek_matrix`).
  - **CI/CD Build Staging**: Updated `.github/workflows/ci.yml` with `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` and Maturin wheel building step in GitHub Actions.
  - **177/177 Pytest Suite PASSED**: Extended `project/tests/test_rust_extensions.py` — verified 100% test pass rate across unit, integration, and Rust PyO3 extension tests.


- [x] **Local OpenAI Codex CLI (`CODEX_CHATGPT`) AI Provider & Dynamic Provider Router ([`project/core/ai_provider_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/ai_provider_router.py), [`project/core/codex_client.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/codex_client.py), [`project/tests/test_ai_provider_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_ai_provider_router.py))**
  - **Local ChatGPT Pro Subcription Integration**: Executes non-interactive `codex exec -s read-only --json` using local session (`codex login`). Completely eliminates API key requirements (`OPENAI_API_KEY`, `CODEX_PRO`) and API billing.
  - **Provider Architecture**: Implemented `AIProviderRouter` with `PRIMARY = CODEX_CHATGPT` and `FALLBACK = GEMINI`.
  - **Health Check & Error Taxonomy**: Implemented `get_provider_health()` reporting `installed`, `authenticated`, and `available` status. Distinguishes error taxonomy (`command_not_found`, `not_authenticated`, `rate_limit_exceeded`, `timeout`, `malformed_response`, `execution_error`).
  - **Verified Test Suite**: Added `project/tests/test_ai_provider_router.py` (9/9 PASS covering Requirements A–F). Verified full 165/165 Pytest suite passing 100%. Real local smoke test returned `CODEX_CHATGPT_OK`.

- [x] **Production CI/CD Build Staging & Multi-Cloud Health Status Verification ([`api/index.js`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.js), [`scripts/publish_space_hf.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/publish_space_hf.py), [`project/static/app.js`](file:///Users/kimlenglim/Project/HoroConsultant/project/static/app.js))**

  - [x] **Auto-Inject Git Commit Version Staging**: Inject exact Git commit version string (`v1.0.0.<commit_hash>`) into static `index.html` during `publish_space_hf.py` build staging.
  - [x] **Vercel Serverless Handler Resolution**: Simplify `api/index.js` using Vercel `res.status().json()` methods to eliminate stream hanging and resolve `FUNCTION_INVOCATION_FAILED`.
  - [x] **Amber Status Indicator Wording**: Update `#f59e0b` amber badge text to accurately state `Health: Standby (Local Engine Fallback)` when backend health check is in fallback state.
  - [x] **End-to-End Live Health Status Verification**: Implemented [`scripts/run_live_health_verification.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_live_health_verification.py) — verifies meaningful HTML/JSON payloads across HF Static UI, Vercel, Azure, and a deterministic API proxy request.

- [x] **Post-Deployment Synthetic Health Monitoring Cron** ([`scripts/synthetic_health_monitor.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/synthetic_health_monitor.py))
  - Implemented scheduled 15-minute GitHub Actions health checks against HF Static UI, Vercel, and Azure, with strict payload validation.
  - Supports `--once` (single-shot) and `--interval <seconds>` (continuous loop) modes.
  - Formats OTLP metric payloads and pushes to Grafana Cloud when credentials are set.
  - Run: `python3 scripts/synthetic_health_monitor.py --once --require-azure` or `python3 scripts/synthetic_health_monitor.py --daemon --interval 900`

- [x] **Extend Grafana Exporter for Gateway Telemetry** ([`scripts/grafana_cloud_exporter.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/grafana_cloud_exporter.py))
  - Added `fetch_gateway_telemetry()` function that probes Vercel, HF Spaces, and Fly.io health endpoints.
  - Collects `gateway_response_latency_ms`, `gateway_http_status_code`, and `gateway_http_requests_total` (bucketed by 2xx/4xx/5xx/error).
  - Added `--push-gateway-telemetry` CLI flag to push OTLP payload to Grafana Cloud.
  - Run: `python3 scripts/grafana_cloud_exporter.py --dry-run --push-gateway-telemetry`
  - Verified: 9 OTLP data points generated across 3 gateways × 3 metrics (exit code 0 ✅)

- [x] **Google Gemini API Dynamic Key & Model Rotation Engine + Telegram Outage Alerting ([`project/api_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/api_router.py), [`api/index.js`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.js), [`project/validator.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/validator.py), [`project/mlops/notifications/webhook_notifier.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/mlops/notifications/webhook_notifier.py))**
  - **Dynamic Model Hierarchy & Rotation**: Implemented seamless rotation across priority tiers (`gemini-3.5-flash-lite ➔ gemini-flash-latest ➔ gemini-3.6-flash`).
  - **Smart Model Fallback Candidates**: Added automatic translation and fallback candidate mapping to valid live Google AI Studio endpoints (`gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-flash`, `gemini-1.5-pro`) upon receiving HTTP 404 / 400.
  - **Multi-Key Failover & Clean Migration**: Automatically filters out placeholder/dummy keys and safely rotates across all valid Google AI Studio keys (`GOOGLE_AI_STUDIO_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY2`). Removed legacy deprecated keys cleanly without backward compatibility overhead.
  - **Instant Telegram Outage Alert**: Added `WebhookNotifier.notify_gemini_outage()` with a 300-second cooldown in `api_router.py` to immediately notify Telegram when all Gemini keys/models fail or hit rate-limits/403 blocks.
  - **Verified Test Suite**: Unit tests in [`project/tests/test_api_router_external.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_api_router_external.py) and [`project/tests/test_telegram_gemini_alert.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_telegram_gemini_alert.py) PASSED 100%.

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

- [x] **🆕 Production AI Inference Chain Fix — 5-Tier Fallback Architecture ([`api/index.js`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.js), [`project/api_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/api_router.py))** *(2026-08-15)*
  - **Verified Fallback Chain (Priority Hierarchy)**:
    1. **HF Inference API** `pphothidaen/qwen2.5-7b-bazi-instruct-4bit` (Fine-tuned BaZi Model) — PRIMARY (4.0s timeout + failover)
    2. **Google Gemini API** (Live candidate rotation: `gemini-2.5-flash`, `2.0-flash`, `2.0-flash-lite`, `1.5-flash`, 2 key rotation) — SECONDARY
    3. **Cloudflare Workers AI** (Multi-model candidate: `@cf/meta/llama-3.1-8b-instruct`, `@cf/meta/llama-3.2-3b-instruct`, `@cf/qwen/qwen1.5-7b-chat-awq`) — TERTIARY
    4. **OpenAI Chat Completions API** (`gpt-4o-mini`, `gpt-4o`, custom `OPENAI_BASE_URL` support) — QUATERNARY
    5. **Domain Template Fallback** (5 topic-specific Thai BaZi templates) — LAST RESORT
  - **Telegram Outage Alerting**: Non-blocking asynchronous alerts dispatched upon Tier 5 fallback or 403/429 provider errors (with 300s cooldown guard).
  - **`api/index.js` Architecture**: Proxy validation (ผ่านเฉพาะ response ที่มี `interpretation`/`pillars`/`chart` fields), fix backend URL default (`core-api` → `core-backend`), add `X-Deploy-SHA` + `X-AI-Source` + `X-AI-Model` headers
  - **`project/api_router.py` Cloud Mode**: Cloud priority reorder: **Cloudflare AI → Gemini → Vertex AI → OpenAI**, add `_call_cloudflare_ai()` REST API caller, add `cloudflare_ai` dispatch case, add `CLOUDFLARE_ACCOUNT_ID/AI_TOKEN/AI_MODEL` config vars
  - **Deployed**: `git push origin main` → commit `41d59f9` → Vercel auto-deploy triggered
  - **Pending**: ต้องตั้ง API key อย่างน้อย 1 ตัวใน Vercel Env Vars (`CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_AI_TOKEN` หรือ `HF_TOKEN` หรือ `GOOGLE_AI_STUDIO_API_KEY` หรือ `OPENAI_API_KEY`)

- [x] **Fine-Tune Pipeline Provider Cleanup (Remove Together AI Dependency) ([`project/admin_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/admin_router.py), [`project/static/admin.html`](file:///Users/kimlenglim/Project/HoroConsultant/project/static/admin.html), [`public/admin.html`](file:///Users/kimlenglim/Project/HoroConsultant/public/admin.html), [`project/rag/external_finetune.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/rag/external_finetune.py), [`project/tests/test_api_router_external.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_api_router_external.py))**
  - **Admin path now supports only `ollama`, `openai`, and `gemini`** for fine-tune triggering.
  - **Removed Together AI branch** (`together`, `TOGETHER_API_KEY`) from external finetune launcher and provider selection.
  - **Health/Route test alignment**: updated `project/tests/test_api_router_external.py` to verify OpenAI + Gemini provider chain presence, not Together.
  - **Production runtime cleanup**: removed `TOGETHER_API_KEY` from local `.env` to avoid accidental Together fallback.

- [x] **Decoupled DDD Multi-Cloud Architecture & Rust High-Performance Core Engine Strategy ([`rust_core/`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/), [`vercel.json`](file:///Users/kimlenglim/Project/HoroConsultant/vercel.json), [`Dockerfile.hf`](file:///Users/kimlenglim/Project/HoroConsultant/Dockerfile.hf))**
  - **Sub-Domain 1 (Fly.io Ultra-Fast Gateway)**: Rust Axum Micro-Gateway specification for < 8 MB RAM footprint, < 20ms cold start, and 50,000+ req/sec throughput in Singapore (`sin`) region.
  - **Sub-Domain 2 (Hugging Face Spaces Core Engine)**: 16 GB RAM continuous backend holding 3,132 RAG text chunks, Swiss Ephemeris astronomical math, and PyO3 Rust extensions (`rust_core/src/bazi.rs`, `rust_core/src/tfidf.rs`).
  - **Sub-Domain 3 (Render Async Background Worker)**: Async background worker for Grafana incident telemetry (`scripts/grafana_cloud_exporter.py`) and multi-agent batch audits.
  - **Sub-Domain 4 (Vercel Edge Global CDN Network)**: Native Vercel Edge CDN CORS preflight middleware and global proxy routing.

- [x] **Grafana Cloud All-in-One Production Monitoring & Telemetry Ingestion Engine ([`project/core/observability.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/observability.py), [`scripts/inject_prod_dummy_data.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/inject_prod_dummy_data.py), [`scripts/inject_grafana_incident_data.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/inject_grafana_incident_data.py), [`scripts/grafana_cloud_exporter.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/grafana_cloud_exporter.py), [`project/grafana/`](file:///Users/kimlenglim/Project/HoroConsultant/project/grafana/))**
  - **Official Production Dashboards**:
    - 🔮 [Public Live Shareable Dashboard](https://vividlamp2135.grafana.net/public-dashboards/cab04a7907b74c2b9889a8ad811bbcdb)
    - 🌐 [Authenticated Main Observability Dashboard](https://vividlamp2135.grafana.net/d/horoconsultant-observability/horoconsultant-observability-dashboard?from=now-1h&to=now&timezone=browser&var-DS_PROMETHEUS=grafanacloud-usage&refresh=5s)
    - 🚨 [Alert Groups Insights Dashboard](https://vividlamp2135.grafana.net/d/e18b8570-27bc-4ab2-bb1c-baeea1363061/alert-groups-insights?from=now-7d&to=now&timezone=browser&var-datasource=grafanacloud-usage)
    - 🌩️ [Incident Insights Dashboard](https://vividlamp2135.grafana.net/d/39ac5605-b947-4c43-87dc-60575f57f219/incident-insights?from=now-90d&to=now&timezone=utc)
  - **Telemetry Dummy Data Ingestion Tool (`scripts/inject_prod_dummy_data.py`)**: Enhanced high-density OTLP metric injector to push Prometheus metrics (`process_uptime_seconds`, `http_requests_total`, `http_request_duration_seconds_bucket`, `rag_search_total`, `rag_search_duration_seconds_sum`, `llm_inference_total`, `alert_groups_total`, `alert_groups_response_time_seconds_sum`, `alert_groups_resolution_time_seconds_sum`, `user_was_notified_of_alert_groups_total`) across multiple time stages with target selection (`--target prom`, `--target incident`, `--target all`) and `--verify-queries` PromQL verification.
  - **Grafana Incident Datasource Script (`scripts/inject_grafana_incident_data.py`)**: Created dedicated ingestion script for seeding rich dummy incident records (Status, Severity, Labels, MTTR, Assignments) into Grafana Cloud Incident REST API.
  - **Grafana Dashboard PromQL Repair**: De-garbled and repaired all 14 panel PromQL expressions in [`project/grafana/alert_groups_dashboard.json`](file:///Users/kimlenglim/Project/HoroConsultant/project/grafana/alert_groups_dashboard.json), ensuring exact match with OTLP telemetry metrics.
  - **Prometheus Metrics Engine**: Implemented `ObservabilityManager` for tracking HTTP request latencies, Request Per Minute (RPM), HTTP status code counters (2xx/4xx/5xx), RAG FAISS retrieval latency, and LLM inference stats.
  - **Grafana Cloud Exporter CLI (`scripts/grafana_cloud_exporter.py`)**: Developed automated exporter tool supporting `--export-dashboard`, `--dry-run`, `--check-connection`, and `--push-metrics` to push OTLP payloads directly to `vividlamp2135.grafana.net`.
  - **Prometheus Exposition Endpoint (`/metrics`)**: Added standard `/metrics` endpoint supporting both native `prometheus_client` and pure Python exposition text fallback format.
  - **Synthetic Uptime Monitoring Alias (`/api/health`)**: Exposed `/api/health` alias for Grafana Synthetic Monitoring pinging to prevent cloud container sleep modes.
  - **Verified Test Suite**: Comprehensive unit test suites ([`project/tests/test_inject_prod_dummy_data.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_inject_prod_dummy_data.py), [`project/tests/test_inject_grafana_incident_data.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_inject_grafana_incident_data.py), [`project/tests/test_grafana_cloud_exporter.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_grafana_cloud_exporter.py)) — 30/30 tests PASSED 100%.

- [x] **Dynamic Git Commit & Release Version Footer System ([`project/core/config.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/config.py), [`project/main.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/main.py), [`project/static/index.html`](file:///Users/kimlenglim/Project/HoroConsultant/project/static/index.html), [`project/static/app.js`](file:///Users/kimlenglim/Project/HoroConsultant/project/static/app.js))**
  - Added dynamic Git short commit hash extraction (`get_git_commit_hash`) with environment detection (`GIT_COMMIT_HASH`, `VERCEL_GIT_COMMIT_SHA`, `HF_COMMIT_SHA`, `COMMIT_REF`) and `git rev-parse --short HEAD` resolution.
  - Exposed release version with commit hash (`v1.0.0.cb9b314`) in FastAPI app metadata, `/health` response, initial HTML template, and client JS auto-refresh.

- [x] **Production Dual-Mode AI Inference Routing & Failover Engine ([`project/api_router.py`](file:///project/api_router.py), [`project/routers/debate.py`](file:///project/routers/debate.py))**
  - Configured Primary Route targeting Ollama / GGUF model (`qwen2.5:7b`) inside Hugging Face Docker Container (`http://localhost:11434` with 3.0s fast timeout).
  - Configured Fallback Route targeting Gemini 2.0 Flash Cloud Engine (`gemini-2.0-flash`) via Google AI Studio API for zero-downtime, fast natural-language interpretation.

- [x] **Cloud Production Environment Detection & Localhost Bypass Guard ([`project/api_router.py`](file:///project/api_router.py), [`project/rag/vector_store.py`](file:///project/rag/vector_store.py))**
  - Added smart detection for cloud production environments (`SPACE_ID`, `VERCEL`, `FLY_APP_NAME`, `ENVIRONMENT=production`).
  - Automatically bypasses unreachable localhost calls on pure cloud hosts while preserving local container inference.

- [x] **Full 5-Phase AI SDLC Deployment Pipeline & E2E Visual Suite ([`scripts/run_e2e_screenshots.py`](file:///scripts/run_e2e_screenshots.py))**

  - Resolved static asset routing (`/static/app.js` and `/static/style.css`) and converted route handlers to async Playwright handlers.
  - Achieved **100.0% Pass Rate** across 17 E2E visual features (Main Dashboard, Geocoding Resolver, Presets, 4-Pillars Grid, Tab Switching, 8 Master Disciplines Visualizers, Admin Auth, HITL Studio, OpenAPI Swagger UI, ReDoc).
  - Screenshots output saved to `project/tests/screenshots/` and report generated in `project/tests/e2e_results_report.json`.

- [x] **UI Button & Endpoint Contract Regression Suite ([`scripts/run_button_regression.py`](file:///scripts/run_button_regression.py))**
  - Verified 25/25 endpoint and button contract execution cards with 100% success rate (`project/tests/button_regression_report.json`).

- [x] **Pre-Deployment Safety Audit & Secret Leak Scan ([`project/core/code_reviewer.py`](file:///project/core/code_reviewer.py))**
  - Audited 1,060 files: **0 secret leaks found**, **0 CUDA issues**, test suite **138 passed**. Overall status: **`READY_FOR_PROD`**.

- [x] **Hugging Face Spaces Live Deployment ([`scripts/publish_space_hf.py`](file:///scripts/publish_space_hf.py))**
  - Dry-run payload audit passed (3.31 MB). Live demo published to target Space: [`pphothidaen/horoconsultant-core-backend`](https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend).

- [x] **Cross-Platform SDLC Agent Governance Sync ([`scripts/sync_sdlc_agents.py`](file:///scripts/sync_sdlc_agents.py))**
  - Synchronized all 16 Antigravity agent definitions (`.antigravity/agents/`), agent skills (`.agents/skills/`), and registry manifests. Verified via `--check` mode (`100% Synchronized`).

- [x] **Available Agents & Default Agent Configuration Fix ([`agent.md`](file:///Users/kimlenglim/Project/HoroConsultant/agent.md), [`.antigravity/agents/`](file:///Users/kimlenglim/Project/HoroConsultant/.antigravity/agents/), [`.agents/agents/`](file:///Users/kimlenglim/Project/HoroConsultant/.agents/agents/))**
  - Resolved `Available Agents` configuration discrepancy across project agent definitions.
  - Corrected machine key `name` field in `.antigravity/agents/*.agent` files (mapping exact identifiers e.g. `default`, `orchestrator`, `business_analyst`, `developer`, `qa_tester`, `devops`, `code_reviewer`, and domain masters).
  - Synchronized both underscore (`*_master.agent`) and hyphenated (`*-master.agent`) definition formats for full Antigravity CLI loader compatibility.
  - Standardized `.agents/agents/` directories with lowercase `agent.md` and valid YAML frontmatter across all 15 agents.
  - Verified via test suite `project/tests/test_agent_configurations.py` (full suite 138/138 PASS).

- [x] **Production Live Playwright E2E UI Button Regression ([`scripts/run_prod_e2e_playwright.py`](file:///scripts/run_prod_e2e_playwright.py))**
  - Target URL: `https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html`
  - Automated testing across 20 UI controls: Location Search, 3 Presets, 9 Metaphysics Master Disciplines, Form Checkboxes, AI BaZi interpretation submit button (`#btn-submit`), and 3 Interpretation Tabs.
  - Achieved **100.0% Pass Rate** (20/20 passed, 0 failed). Verified output in `project/tests/prod_button_regression_report.json` & screen captures in `project/tests/screenshots/prod_*.png`.

- [x] **Fly.io Docker Build .dockerignore Fix ([`.dockerignore`](file:///.dockerignore))**
  - Added `!**/.env.example` to `.dockerignore` to allow Docker to copy `.env.example` into build context.
  - Resolved `failed to calculate checksum of ref: "/.env.example": not found` error during `fly deploy`.
- [x] **Strict Admin Allowed Emails Restriction ([`project/admin_router.py`](file:///project/admin_router.py))**
  - Enforced whitelist strictly for `pansakorn@gmail.com` and `kimlenglim.work@gmail.com`.
  - Added client-side fallback auth in [`project/static/admin.html`](file:///project/static/admin.html).
- [x] **Koyeb Removal & Architecture Streamlining ([`vercel.json`](file:///vercel.json))**
  - Removed Koyeb references and route rewrites due to platform shutdown.
  - Streamlined Multi-Cloud Architecture across Fly.io, Vercel, Hugging Face, and Kaggle.
- [x] **Business System Analyst Agent & Skill Governance ([`.agents/agents/business_analyst/agent.md`](file:///.agents/agents/business_analyst/agent.md))**
  - Created `business_analyst` agent role for requirement analysis, documentation watchdog, and agent skill governance.
  - Created `bsa-doc-skill-management` skill ([`.agents/skills/bsa-doc-skill-management/SKILL.md`](file:///.agents/skills/bsa-doc-skill-management/SKILL.md)).
  - Updated Orchestrator collaboration flow and system rules in [`.agents/AGENTS.md`](file:///.agents/AGENTS.md).
- [x] **Multi-Model Quota Strategy & Model Allocation Matrix ([`.agents/AGENTS.md`](file:///.agents/AGENTS.md))**
  - Updated Gemini-First Production Baseline + Claude/GPT Quota Failover rules.
  - Configured high-efficiency tiering for `orchestrator`, `developer`, `qa_tester`, and `devops`.
- [x] **HuggingFace Spaces Docker Configuration ([`Dockerfile.hf`](file:///Dockerfile.hf))**
  - Created zero-cost production container setup targeting Port 7860 & User 1000 for HuggingFace Spaces.
- [x] **HuggingFace Space Automated Publisher & Dry-Run Verification ([`scripts/publish_space_hf.py`](file:///scripts/publish_space_hf.py))**
  - Built automated Deployment script to push Core Backend codebase to HuggingFace Space with 1 command.
  - Performed payload audit and token authentication check (Verified user: `pphothidaen`, 7 files, 0.17MB payload).
- [x] **Multi-Agent Async Debate & Synthesis Engine ([`project/core/multi_agent_debate.py`](file:///project/core/multi_agent_debate.py))**
  - Parallelized 10-Domain Engines execution via `asyncio.gather` for < 2.0s latency.
- [x] **Unified Admin Panel & HITL Studio Security Integration (`project/static/admin.html`)**
  - Integrated HITL Review Studio directly into Admin Panel navigation sidebar (`showPage('hitl')`).
- [x] **Production Secret Environment Variables Injection & Verification**
  - Verified `HF_TOKEN`, `GOOGLE_AI_STUDIO_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY2`, and `OPENAI_API_KEY` in environment config & fallback chain.
- [x] **Post-Finetune DB Vector Purge Execution & Pipeline ([`scripts/post_train_fuse.py`](file:///scripts/post_train_fuse.py))**
  - Configured model fusion, GGUF conversion, and vector store cleanup post-training pipeline.
- [x] **Vercel Edge API Gateway Proxy Setup ([`vercel.json`](file:///vercel.json))**
  - Configured `/api/hf/:path*` route forwarding to Hugging Face Spaces Core Backend (`pphothidaen-horoconsultant-core-backend.hf.space`).
- [x] **Unit, Integration & Pre-Deployment Audit Baseline**
  - Verified 111/111 tests passing cleanly in 2.85s.
  - Verified `project/core/code_reviewer.py` status `READY_FOR_PROD` with zero secret leaks.

- [x] **Vercel Gateway Handler Stabilization & Production Verification ([`api/main.py`](file:///Users/kimlenglim/Project/HoroConsultant/api/main.py), [`api/index.py`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.py), [`vercel.json`](file:///Users/kimlenglim/Project/HoroConsultant/vercel.json))**
  - Confirmed full Vercel serverless adapter (`api/main.py`) handling: GET health checks, POST `/api/v1/bazi/interpret`, OPTIONS CORS preflight (HTTP 204), and multi-route gateway forwarding.
  - CORS preflight headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`) verified via `ThreadingHTTPServer` live integration test.
  - Verified `vercel.json` rewrites: `/api/hf/:path*` proxy, `/health` → `/api/main`, `/api/v1/:path*` → `/api/main`, `/api/:path*` → `/api/main`.
  - Full production test coverage via `test_prod_regression.py` (7/7 tests PASSED) including CORS preflight, gateway config, and live endpoint contracts.

- [x] **CodeReviewer `.venv` Directory Exclusion Fix ([`project/core/code_reviewer.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/code_reviewer.py))**
  - Fixed false-positive `BLOCKED` status caused by scanning `.venv` third-party packages (pip, numpy test files) with Kaggle token regex pattern `kg_[A-Za-z0-9_-]{20,}`.
  - Root cause: exclusion list checked for `"venv"` but directory is named `.venv` (with dot prefix), so path parts never matched.
  - Extended skip list to include `.venv`, `wandb`, `node_modules`, `.vercel` in addition to existing `.git`, `.pytest_cache`, `.ruff_cache`, `__pycache__`.
  - Result: audit now correctly scans 1,077 project files (vs 4,156 with false positives), 0 secret leaks found, status restored to `READY_FOR_PROD`.
  - Test suite verified: **169/169 tests PASS** (upgraded from 142/142 with additional tests for observability, prod regression, and universal bridge).

- [x] **Vercel Lambda FUNCTION_INVOCATION_FAILED + CORS Error Fix ([`api/main.py`](file:///Users/kimlenglim/Project/HoroConsultant/api/main.py), [`runtime.txt`](file:///Users/kimlenglim/Project/HoroConsultant/runtime.txt), [`scripts/run_vercel_prod_curl_regression.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_vercel_prod_curl_regression.py))**
  - **Root Cause**: `api/main.py` contained `from project.main import app` at module level, pulling the entire FastAPI stack (FAISS, RAG, apscheduler, swisseph, all astrology engines) into the Vercel Lambda at cold-start → `FUNCTION_INVOCATION_FAILED (HTTP 500)`. Vercel's bare 500 omits `Access-Control-Allow-Origin` → browser misreports as CORS error.
  - **Fixes Applied**:
    - Removed `from project.main import app as fastapi_app` entirely from `api/main.py`.
    - Replaced CORS import with lazy `_get_cors_headers()` function with inline pure-Python fallback (zero heavy dependencies at module level).
    - Added `_safe_dispatch()` global exception wrapper guaranteeing CORS headers on ALL responses including uncaught errors.
    - Expanded OPTIONS preflight `Access-Control-Allow-Headers` to cover Chrome `sec-ch-ua*` headers.
    - Fixed `five_elements` parsing: engine returns nested `{percentages:{...}, scores:{...}}` dict, not flat floats.
    - Created `runtime.txt` specifying `python3.11` to pin Vercel Python runtime.
  - **Post-Deploy Regression**: Created [`scripts/run_vercel_prod_curl_regression.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_vercel_prod_curl_regression.py) — tests live Vercel URL with exact HuggingFace browser headers: GET `/health`, OPTIONS preflight, POST `/api/v1/bazi/interpret`, plus observability headers (`X-Deploy-SHA`, `X-AI-Source`, `X-AI-Model`).

- [x] **Phase 6.1: Standalone Pure Rust Axum API Gateway & Core Metaphysical Engines (Option C) ([`rust_core/src/bin/horo_server.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/horo_server.rs))**
  - **Rust Server Binary**: Full Axum gateway implementation (< 10MB RAM, < 1ms latency).
  - **Pure Rust Math Routing**: `/health`, `/metrics`, `/api/v1/bazi/calculate`, `/api/v1/ziwei/calculate`, `/api/v1/qimen/calculate`, `/api/v1/xuankong/calculate`, `/api/v1/thai_vedic/calculate`, `/api/v1/uranian/calculate`, `/api/v1/iching/calculate`, `/api/v1/liuren/calculate`, `/api/v1/zeji/calculate`, `/api/v1/numerology/calculate`.
  - **Python RAG Async Proxy**: `/api/v1/proxy/*path` targeting Python RAG/LLM Service (`PYTHON_RAG_HOST`).

- [x] **Phase 6.2: Native Rust Regression Runner Integration (Option 1) ([`rust_core/src/bin/regression_runner.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/regression_runner.rs))**
  - **Target Achieved**: Added a 12-check parallel Rust CLI Runner (`regression_runner`) that complements the full Pytest suite. The 2026-08-09 local audit completed all 12 checks in **0.078s** with the Axum health endpoint running.
  - **Execution Protocol**: Verifies BaZi, ZiWei, QiMen, XuanKong, Thai Vedic, Uranian, SwissEph, ZeJi, Secret Scanner, and Consonance audits in pure Rust.
  - **Migration Dead-Code Cleanup Mandate**: Cleaned up warnings and verified 100% test pass rate across Rust binaries.

- [x] **Swiss Ephemeris Native Pure Rust Bridge ([`rust_core/src/swisseph.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/swisseph.rs))**
  - High-precision analytical planetary ephemeris calculation engine in pure Rust (`calculate_sun_position_rust`, `calculate_moon_position_rust`, `compute_ephemeris_sun_moon`).

- [x] **BaZi Interpretation Router Singleton Regression Fix ([`project/routers/debate.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/routers/debate.py))**
  - The interpretation endpoint now shares the application `HybridRouter` singleton instead of constructing an independent router, so its configured routing and test dependency are consistent.
  - Verified by the previously failing `test_bazi_interpret_basic` and the full **195/195** Pytest suite.

- [x] **Backward-Compatible Codex Subagent Configuration ([`scripts/sync_codex_agents.py`](scripts/sync_codex_agents.py), [`.codex/agents/`](.codex/agents/), [`AGENTS.md`](AGENTS.md))**
  - Reuses the 16 existing `.agents/agents/*/agent.json` role definitions as the source and generates native Codex TOML files without changing Antigravity files or legacy provider allocations.
  - Adds `--check` drift detection, TOML parsing tests, and safe historical model guidance: Codex roles inherit the active Codex model.
  - Verification: both synchronization checks pass; Codex migration plus legacy agent configuration tests pass **6/6**. The remaining pre-existing live-Codex fallback test requires its configured 45-second CLI timeout and exceeds this harness's foreground-command limit.

## 🚨 RECENT RESOLVED UI ISSUES — Layout & Rendering (ภาพที่ 1 + ภาพที่ 2)

**Report Source**: User screenshot review on 2026-08-16 (ภาพที่ 1: `composer_2026-08-16_07-41-24-093_ab83ac.png`, ภาพที่ 2: `composer_2026-08-16_09-32-55-284_bfc687.png`)
**Report Context**: Hugging Face Spaces production dashboard — `https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html`

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-UI-001` | `qa_tester` / `developer` | Fix `[object Object]` rendering — data format issue in Four Pillars / Five Elements & 16 disciplines display (ภาพที่ 1) | **DONE** | None |
| `TICKET-UI-002` | `developer` / `qa_tester` | Fix layout overlap & mobile overflow at purple card area — rightmost result card & mobile viewport (ภาพที่ 2) | **DONE** | `TICKET-UI-001` |

---

### 🎫 TICKET-UI-001 | `qa_tester` / `developer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: None
**Blocks**: `TICKET-UI-002`

**Reported in**: ภาพที่ 1 (`composer_2026-08-16_07-41-24-093_ab83ac.png`)
**Root Cause Domain**: Frontend — `public/app.js` & `project/static/app.js` data rendering path

#### สังเกตและผลการแก้ไข
- ตรวจสอบและแก้ไขทุก render path ใน `app.js` (รวมถึง `calcMeiHua`, `calcQiZheng`, `calcMianXiang`, `calcTaiYi`, `calcLiuYao`, `calcSanHe`)
- เพิ่มการ unwrap property ป้องกัน object/undefined coercion
- สร้าง Playwright Automated Test Script: `scripts/verify_object_rendering.py`
- สร้าง Pytest Suite: `project/tests/test_object_rendering.py`
- ผลทดสอบ: **32/32 PASSED 100%** (0 `[object Object]`, 0 `[object Undefined]`, 0 `NaN`)

#### Acceptance Criteria
- [x] ไม่มี `[object Object]` ปรากฏบนหน้าจอในทุก discipline ที่ทดสอบ (16 ศาสตร์) — ยืนยัน 32/32 tests ผ่าน
- [x] Five Elements แสดงค่าเปอร์เซ็นต์จริง (ไม่แสดง 0.0% ทั้งหมด) เมื่อข้อมูลครบถ้วน
- [x] พิกัดแสดงตรงกับที่ input (ไม่ผิดเป็นตำแหน่งอื่น)
- [x] ปีแสดงตรงกับปีเกิดที่ input (ไม่แสดงปีปัจจุบันผิด)
- [x] ทดสอบกับ input หลายชุดแล้วแสดงผลถูกต้องทุกชุด (บันทึกใน `project/tests/object_rendering_verification_report.json`)
- [x] ยืนยันผ่าน Pytest และ Playwright E2E Suite

**Ticket Status**: DONE — แก้ไข render path และผ่านการ verify 100%

---

### 🎫 TICKET-UI-002 | `developer` / `qa_tester` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-UI-001`
**Blocks**: None

**Reported in**: ภาพที่ 2 (`composer_2026-08-16_09-32-55-284_bfc687.png`)
**Root Cause Domain**: Frontend — CSS layout / responsive boundaries (`public/style.css` & `project/static/style.css`)

#### ผลการแก้ไขและการทดสอบ
- ปรับ `.main-container` ให้ใช้ `grid-template-columns: minmax(0, 420px) minmax(0, 1fr)` พร้อม `min-width: 0; max-width: 100%`
- ปรับ `.glass-card` ให้รองรับ responsive padding `1rem` บน Mobile และ Tablet
- ปรับ `datetime-local` picker และ footer status badges ไม่ให้เกินขนาด viewport
- ทดสอบผ่าน `scripts/audit_ui_overlap.py` ข้าม 5 Viewports:
  - Desktop Large (1512×733): ✅ 0 Overlaps, Clean Width
  - Desktop Standard (1440×900): ✅ 0 Overlaps, Clean Width
  - Laptop Compact (1366×768): ✅ 0 Overlaps, Clean Width
  - Tablet (768×1024): ✅ 0 Overlaps, Clean Width
  - Mobile (375×812): ✅ 0 Overlaps, Clean Width (375px scrollWidth, 0 overflow)

#### Acceptance Criteria
- [x] ไม่มี element ใดทับซ้อนกันใน purple card area หรือ panel อื่นๆ
- [x] ปุ่ม/ข้อความท้ายการ์ดแสดงในพื้นที่ที่ถูกต้อง ไม่ชนองค์ประกอบข้างเคียง
- [x] ทดสอบกับ 5 viewports แล้วไม่มี overlap: 1512×733, 1440×900, 1366×768, 768×1024, 375×812
- [x] Content ยาว/สั้น ไม่ทำให้ layout แตกหรือ overlap
- [x] Mobile Viewport (375px) มี clean width (0 overflow-x)

#### Test Viewports Matrix
| Viewport | Status | Overlaps | Overflow |
|---|---|---|---|
| 1512×733 | ✅ PASSED | 0 | Clean Width |
| 1440×900 | ✅ PASSED | 0 | Clean Width |
| 1366×768 | ✅ PASSED | 0 | Clean Width |
| 768×1024 | ✅ PASSED | 0 | Clean Width |
| 375×812  | ✅ PASSED | 0 | Clean Width |

**Ticket Status**: DONE — ผ่านการทดสอบ 0 Overlap & 0 Overflow ครบทุกขนาดหน้าจอ

---

### 🔄 DOING (กำลังดำเนินการ)

### ✅ Current Operational Status Sync (Production Inference Handoff)

- [x] **Production Finalization Handoff (Verified & Live)** — **READY & VERIFIED**
  - **Current status:** POST `/api/v1/bazi/interpret` responds with live LLM model `@cf/meta/llama-3.1-8b-instruct` via `ai_agent_llm`.
  - **Live gate:** `source`/`model` confirmed live on production responses (`source=ai_agent_llm`, `model=@cf/meta/llama-3.1-8b-instruct`).
  - **Go-live criteria:** Verified `3/3 PASSED` from `run_vercel_prod_curl_regression.py` with `X-Deploy-SHA`, `X-AI-Source`, `X-AI-Model`.
- **Latest verification check (2026-08-16 00:39:23):** `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `3/3 PASSED` (GET /health 200, OPTIONS 204, POST 200; `source=ai_agent_llm`, `model=@cf/meta/llama-3.1-8b-instruct`; latency=5732ms)

- [x] **Production Verification Audits Completed (for handoff evidence)**
  - `00:39:23` `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `3/3 PASSED` (`source=ai_agent_llm`, `model=@cf/meta/llama-3.1-8b-instruct`)
  - `21:28` `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `3/3 PASSED` (`X-Deploy-SHA`, `X-AI-Source`, `X-AI-Model` present)
  - `21:45` `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `3/3 PASSED` (`X-Deploy-SHA`, `X-AI-Source`, `X-AI-Model` present; model=gemini-3.7-flash)

- [x] **Production Regression Suite Hardening Completed** (`scripts/run_vercel_prod_curl_regression.py`)
  - Added default `--timeout 45` และ `--retries 1` ให้สคริปต์ Python fallback
  - ปรับให้มี retry เมื่อตรวจพบ timeout เพื่อกัน false-negative จากคูลดาวน์/เครือข่ายชั่วคราว
  - ยืนยัน: `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python --timeout 45 --retries 1` → `3/3 PASSED`

- [x] **Vercel Gateway Timeout & Error Boundary Hardening (`api/index.js`)**
  - เพิ่ม `BACKEND_TIMEOUT_MS`, `AI_PROVIDER_TIMEOUT_MS`, `AI_ROUTE_BUDGET_MS` พร้อม `fetchWithTimeout()` เพื่อลด request hang
  - เพิ่มเงื่อนไข budget/cutoff ระหว่าง provider chain (Cloudflare, HF, Gemini, OpenAI) เพื่อ fallback อย่างเร็ว
  - รองรับการหยุด gracefully เมื่อ `proxyRequest` ล้มเหลว และยังคงคืน response ที่มี CORS-header

### 🔁 Production Inference Next Action Queue (เมื่อได้ key / redeploy แล้ว)

- [x] 1) ตั้ง API key อย่างน้อย 1 ตัวบน Vercel ตามลำดับ:
   - [x] Route 1: `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_AI_TOKEN` (Live: `@cf/meta/llama-3.1-8b-instruct`)
   - [x] *(Optional Fallback Key 2)* Route 2: `GOOGLE_AI_STUDIO_API_KEY` / `GOOGLE_AI_STUDIO_API_KEY2` (Optional Multi-Key Fallback)
   - [x] *(Optional Fallback Key 3)* Route 3: `OPENAI_API_KEY` / `OPENAI_API_KEY2` (Optional Multi-Key Fallback)
   - [x] *(Optional Fallback Key 4)* Route 4: `HF_TOKEN` / `HUGGINGFACE_TOKEN` / `HUGGINGFACE_API_KEY` (Optional Multi-Key Fallback)
- [x] 2) Redeploy แล้วรัน handoff evidence chain:
   - `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` (3/3 PASSED)
   - `python3 scripts/run_button_regression.py` (32/32 PASSED)
   - `python3 -m pytest -v --ignore=project/kaggle_kernel` (408/408 PASSED)
- [x] 3) Handoff verification pass: ตรวจพบ live model `@cf/meta/llama-3.1-8b-instruct` (`source=ai_agent_llm`)
- [x] 4) เปลี่ยน `Production Finalization Handoff` เป็น `[x]` และอัปเดต `Last Updated` + docs ที่เกี่ยวข้อง
- [x] 5) บันทึก evidence สรุปผลการตรวจสอบ live verification chain

---

### 📋 TODO (งานระยะถัดไป / Phased Roadmap)

- [x] **🔑 ตั้ง API keys สำหรับ Inference (ไม่ใช้ Together AI)** *(Priority: CRITICAL — Live & Operational)*
  - ติดตั้ง Cloudflare Workers AI credentials (`CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_AI_TOKEN`) ใน Vercel Environment Variables สำเร็จ และเชื่อมต่อ live inference model `@cf/meta/llama-3.1-8b-instruct`
  - Optional Rotation: สามารถเพิ่ม Gemini / OpenAI / HF Tokens สำรองเพิ่มเติมได้ตามต้องการ (Optional Fallbacks)


- [x] **Release Rollback & Recovery Runbook ([`docs/RELEASE_ROLLBACK_RUNBOOK.md`](file:///Users/kimlenglim/Project/HoroConsultant/docs/RELEASE_ROLLBACK_RUNBOOK.md))** *(Priority: MEDIUM)*
  - Define rollback/no-rollback criteria (health probe failures, route error rates, and cross-provider inference chain breakage).
  - Set owners and contact chain for Vercel, Hugging Face, and Azure fallback paths.
  - Owner mapping template:
    - **Primary owner (infra/runtime):** DevOps
    - **Primary owner (LLM routing):** Backend Developer
    - **Primary owner (incident comms):** Admin/On-call
    - **Escalation:** `orchestrator` → `business_analyst` → project lead
  - Prepare a dry-run drill checklist with evidence capture (`deployment id`, `X-Deploy-SHA`, sample inference latency, `X-AI-Source` continuity).
  - เตรียม runbook การ rollback/no-rollback policy, owner mapping, และ command playbook สำหรับกรณี production inference validation ไม่ผ่านต่อเนื่อง.
  - คำสั่ง handoff ด่วนสำหรับ production incident:
    - ตรวจความเสถียรเบื้องต้น:
      - `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python`
      - `curl -s https://horo-consultant-psi.vercel.app/health | python3 -m json.tool`
      - `curl -i -X POST https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret -H "Content-Type: application/json" -d '{"birth_datetime":"1990-05-15 14:30:00","query":"การงานและโชคลาภ","day_master":{"stem":"庚","element":"Metal"}}' | python3 -m json.tool`
    - ถ้าขึ้น `HTTP 0`/DNS fail ให้หยุดการ deploy ต่อเนื่องและ escalate infra (DNS/network/proxy) ก่อน
    - ถ้าพบ `X-AI-Source=fallback_template` หลังตั้ง key แล้ว ให้ถือว่า chain ไม่พร้อมใช้งาน -> รอ/รีดีพลอย + validate key env
    - ถ้า deploy hash ไม่ตรง:
      - รัน `npx vercel ls` และใช้ `npx vercel rollback` กลับไป deployment ที่มี `X-Deploy-SHA` ล่าสุดที่ยืนยันได้
    - เกณฑ์หยุดงานด่วน (auto-stop):
      - 2 รอบติดของ `python3 scripts/run_vercel_prod_curl_regression.py --url ... --use-python` ได้ผลต่ำกว่า 3/3
      - ค่าเฉลี่ย latency POST เกิน 12,000ms จาก 3 sample
      - `source`/`model` ไม่สม่ำเสมอข้าม 3 request ติดต่อกัน
    - รันเช็ก log:
      - `curl -s https://horo-consultant-psi.vercel.app/health | jq '.version, .inference_chain, .chain_trace'`
      - `for _ in 1 2 3; do curl -i -X POST https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret -H "Content-Type: application/json" -d '{"birth_datetime":"1990-05-15 14:30:00","query":"การงานและโชคลาภ","day_master":{"stem":"庚","element":"Metal"}}' | sed -n '1,14p'; done`
    - เก็บหลักฐานปิดงาน: deployment id, X-Deploy-SHA ชุดล่าสุด, 3 sample inference latency, source model ก่อนส่งต่อ handoff.
