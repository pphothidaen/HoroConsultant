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
Phase 1: Planning & Blueprinting (Master Orchestrator)
       │  ├─ Check Kaggle status (`python3 scripts/kaggle_notebook_manager.py --status`)
       │  └─ Write spec & task breakdown to `/plans/plan.md`
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

### Phase 1: Planning & Blueprinting (Orchestrator)
1. **Kaggle Pre-Development Sync Mandate**: Before starting any code edits, run:
   ```bash
   python3 scripts/kaggle_notebook_manager.py --status
   ```
   If kernel output is updated, pull latest artifacts via `--pull`.
2. Run a mandatory requirement grilling pass in `/plans/plan.md`:
   - Scope boundaries (what is in/out of scope).
   - Requirement deltas since last commit / last request.
   - Acceptance criteria (measurable outcomes + QA checkpoints).
   - Constraint checks (security, data, quota, model latency, compliance).
   - Pending assumptions that need owner confirmation.
3. Document requirements and sub-task specifications in `/plans/plan.md` only after the grill questions are answered or explicitly accepted as waived.
3. Delegate sub-tasks to `developer`, `qa_tester`, and `devops`.

### Phase 2: Feature Implementation (Developer)
1. Write/modify code in `project/`, `rust_core/`, or `scripts/`.
2. Follow Pure ASCII logging standard: use `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` (no emojis inside subprocess logs).
3. Respect locked dependencies (`transformers==4.44.2`, `peft==0.12.0`, `accelerate==0.33.0`).

### Phase 3: QA & Testing (QA Tester)
1. Run pytest unit & integration regression suite across all calculation modules, RAG, MCP, and 4 core components:
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
4. Extract concise log snippets if any test fails (do not dump raw context).

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
