# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last Updated: 2026-08-16 19:40:00 +07 — BaZi.Fengshuix.com Complete Replication & Standalone Display Component Sprint (100% Match): True Solar Time with equation of time gamma precision, Four Pillars 100% math/stem/branch parity, Ming Gua, 5 Structures Radar spider chart, 10 Profiles percentage chart, 12 Da Yun Cycles, 12x13 Annual Matrix, 508/508 Pytest PASS (100%), 0 agent sync drift.*

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

# 9. Full Python Pytest Suite (All 508 test cases PASS)
python3 -m pytest -v --ignore=project/kaggle_kernel
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│   🚀 IN PROGRESS: Phase 4 — External LLM Multi-Routing & Cloud Gateway        │
├───────────────────────────────────────────────────────────────────────────────┤
│ • 5-Tier Resilient Failover (Cloudflare AI ➔ Gemini ➔ OpenAI ➔ Claude ➔ Ollama)│
│ • Deterministic Fallback Guard (Zero uncaught exceptions / Zero leakage)      │
│ • Dynamic Circuit Breaker, Exponential Backoff & Latency Health Monitoring    │
│ • Endpoints /api/v2/llm/providers/status & /api/v2/llm/route-test             │
│ • Admin Panel Live Provider Status Widget (project/static/admin.html)         │
├───────────────────────────────────────────────────────────────────────────────┤
│   ✅ DONE: Phase 3 — Unified Multimodal Matrix & 16-Discipline Consensus (100%)│
├───────────────────────────────────────────────────────────────────────────────┤
│ • 6 Core Life Themes Focus Controller, 16-Discipline Radar Mandala SVG Chart  │
│ • Pytest 517/517 PASS, 32/32 UI Buttons PASS, Live HF Space v1.0.0.3c08386    │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 ACTIVE SPRINT: Phase 4 — External LLM Multi-Routing & Multi-Provider Cloud Gateway
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md`)  
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)  

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-LLM-001` | `orchestrator` | Architecture Blueprint & Multi-Provider Gateway Spec | DONE | None |
| `TICKET-LLM-002` | `developer` | Multi-Tier LLM Gateway & Circuit Breaker Engine in `project/core/llm_gateway.py` | DONE | `TICKET-LLM-001` |
| `TICKET-LLM-003` | `developer` | FastAPI Routers & Admin Panel Provider Status Widget Integration | DONE | `TICKET-LLM-001` |
| `TICKET-LLM-004` | `qa_tester` | Unit & Mock Failure Regression Test Suite (`test_llm_multirouter.py`) | DONE | `TICKET-LLM-002`..`003` |
| `TICKET-LLM-005` | `devops` | CI/CD Production Release to HF Spaces & Live Verification | DONE | `TICKET-LLM-004` |
| `TICKET-LLM-006` | `code_reviewer` | Pre-Deployment Safety Audit & Live Documentation Sync | DONE | `TICKET-LLM-005` |

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
