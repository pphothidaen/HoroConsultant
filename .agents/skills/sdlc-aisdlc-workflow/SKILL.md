---
name: sdlc-aisdlc-workflow
description: "Run 5-phase AI SDLC: planning, implementation, QA, release, and post-deploy verification."
---

# 🔄 AI SDLC & SDLC Workflow Skill Guide

This skill provides step-by-step instructions for executing the AI Software Development Life Cycle (AI SDLC) on **HoroConsultant**.

---

## 🎯 The 5-Phase AI SDLC Lifecycle

```
[User Request / Goal]
       │
       ▼
[Gate 0: Requirement-Grill Gate (`requirement-grill-gate` skill)]
       │  ├─ Interactive 9-dimension interview & context auto-scan
       │  ├─ Prepend GRILL REPORT to `/plans/plan.md` (✅ APPROVED / ⚠️ WAIVED / 🚫 BLOCKED)
       │  └─ Generate specialized sub-agent tickets in `PROJECT_TASKS.md`
       │
       ▼
Phase 1: Planning & Blueprinting (Master Orchestrator)
       │  ├─ Check Kaggle status (`python3 scripts/kaggle_notebook_manager.py --status`)
       │  ├─ Finalize technical architecture blueprint in `/plans/plan.md`
       │  └─ Dispatch assigned tickets to sub-agents (`orchestrator`, `developer`, `qa_tester`, `devops`)
       │
       ▼
Phase 2: Code Implementation & Inline Docs (Senior Developer)
       │  ├─ Write Python 3.12 / Rust PyO3 / FastAPI code
       │  └─ Enforce Pure ASCII logging guard ([OK], [ERROR])
       │
       ▼
Phase 3: Quality Assurance & Testing (QA Tester)
       │  ├─ Run Pytest suite (`python3 -m pytest -v`)
       │  └─ Execute UI Button & Playwright E2E tests (`python3 scripts/run_button_regression.py`)
       │      ├─ [FAIL] -> Return bug report snippet to Developer
       │      └─ [PASS] -> Report 100% test pass rate
       ▼
Phase 4: Environment & Release Verification (DevOps & Release)
       │  ├─ Audit Doppler secrets & `.env` variables
       │  ├─ Verify Docker compose & Hugging Face payload (`python3 scripts/publish_space_hf.py --dry-run`)
       │  └─ Scan secret leaks (`python3 project/core/code_reviewer.py --scan-secrets`)
       ▼
Phase 5: Code Review, Deployment & Post-Deploy E2E (Master Orchestrator & Code Reviewer)
       │  ├─ Execute pre-deployment audit (`python3 project/core/code_reviewer.py --review`)
       │  ├─ Push to production (`git push origin main`) & publish HF Space
       │  └─ Verify post-deployment E2E functionality (`python3 scripts/run_button_regression.py`)
       ▼
[User Delivery Complete]
```

---

## 📌 Phase Instructions for Agents

### Phase 1: Requirement Grill, Planning & Blueprinting (Orchestrator)
1. **Mandatory Requirement-Grill Gate (`requirement-grill-gate` skill)**:
   - Execute the 9-dimension grill interview pass before planning.
   - Scan codebase for low-risk auto-answers and ask user one-by-one for critical/high items.
   - Prepend the signed-off **GRILL REPORT** at the top of `/plans/plan.md` with status badge (`✅ APPROVED` / `⚠️ WAIVED` / `🚫 BLOCKED`).
   - If `🚫 BLOCKED`, halt and do not proceed to Phase 2.
2. **Deconstruct Sub-Agent Tickets in `PROJECT_TASKS.md`**:
   - Create a dedicated sprint/session block in `PROJECT_TASKS.md` with one ticket per assigned sub-agent (`orchestrator`, `developer`, `qa_tester`, `devops`, `domain_master`).
   - Detail step-by-step instructions, dependencies, and testable acceptance criteria for each ticket.
3. **Kaggle Pre-Development Sync Mandate**:
   ```bash
   python3 scripts/kaggle_notebook_manager.py --status
   ```
   If kernel output is updated, pull latest artifacts via `--pull`.
4. **Handoff & Tracking**:
   - Transition `TICKET-001` (Plan) to `DONE` and move `TICKET-002` (Developer) from `TODO` to `DOING`.

### Phase 2: Feature Implementation (Developer)
1. Write/modify code in `project/`, `rust_core/`, or `scripts/`.
2. Follow Pure ASCII logging standard: use `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` (no emojis inside subprocess logs).
3. Respect locked dependencies (`transformers==4.44.2`, `peft==0.12.0`, `accelerate>=0.34.0,<1.0.0`).

### Phase 3: QA, Testing & Auto-Remediation Loop (QA Tester & Orchestrator)
1. Run pytest unit & integration regression suite across all calculation modules, notebooks, RAG, MCP, and 4 core components:
   ```bash
   python3 -m pytest -v --ignore=project/kaggle_kernel
   ```
2. Run UI button & endpoint contract regression suite across **Main Dashboard**, **Admin Panel**, **HITL Review Studio**, and **OpenAPI Interactive Documentation** (`/docs`, `/redoc`, `/openapi.json`):
   ```bash
   python3 scripts/run_button_regression.py
   ```
3. Run Playwright E2E browser automation & visual screenshot capture suite across all 4 core components:
   ```bash
   python3 scripts/run_e2e_screenshots.py
   ```
4. **Auto-Remediation Loop & HITL Protocol**:
   - If any test or quality gate fails: `qa_tester` extracts concise failure snippets and passes them to `orchestrator`.
   - `orchestrator` automatically distributes the fix ticket to `developer` for remediation.
   - The loop repeats: `developer` fixes -> `qa_tester` verifies.
   - **HITL Threshold**: If the issue remains unresolved after **3 consecutive retry attempts**, the orchestrator MUST pause the workflow, generate an Incident Summary, and escalate to **Human-In-The-Loop (HITL)** for guidance.

### Phase 4: DevOps & Release (DevOps)
1. Validate environment files (`.env`, `.env.production`).
2. Run secret scan:
   ```bash
   python3 project/core/code_reviewer.py --scan-secrets
   ```
3. Verify Hugging Face Spaces deployment payload:
   ```bash
   python3 scripts/publish_space_hf.py --dry-run
   ```

### Phase 5: Final Review & Post-Deploy E2E Verification (Orchestrator & Code Reviewer)
1. Run full code review audit:
   ```bash
   python3 project/core/code_reviewer.py --review
   ```
   Ensure status is `READY_FOR_PROD`.
2. Push to GitHub main: `git push origin main`.
3. Publish to Hugging Face Spaces: `python3 scripts/publish_space_hf.py`.
4. Execute Post-Deployment E2E verification across all 4 Core Components (Main Dashboard, Admin Panel, HITL Studio, OpenAPI Docs):
   ```bash
   python3 scripts/run_button_regression.py
   python3 scripts/run_e2e_screenshots.py
   ```
