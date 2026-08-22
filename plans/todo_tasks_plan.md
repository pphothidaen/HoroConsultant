# Implementation Plan: Fulfill TODO Tasks in PROJECT_TASKS.md

**Goal**: Execute the remaining tasks in the `📋 TODO` section of `PROJECT_TASKS.md` following the AI SDLC Workflow (`.agents/workflows/aisdlc.md`).

> **Current disposition (2026-08-21):** Tasks 1–6 have implementation and focused-test evidence under `TICKET-META-003`/`004`. CI/CD release verification remains explicitly blocked under `TICKET-META-005`/`006`; see [`PROJECT_TASKS.md`](../PROJECT_TASKS.md) for owner, gate, and recovery action. This plan is retained for traceability, not as an unstarted backlog.

---

## Task Breakdown & Roadmap

### Task 1: Model Fusion & GGUF Ollama Export Pipeline
- **Objective**: Create `scripts/post_train_fuse.py` and Modelfile tooling to support model fusion and GGUF/Ollama model export when adapter weights are available or mock fallback is specified.
- **Deliverables**:
  - `scripts/post_train_fuse.py` with robust CLI options, checks for MLX / PyTorch adapters, and convert/create pipeline.
  - `project/models/Modelfile` for Ollama configuration.
  - Test suite covering fusion script execution and Modelfile validation.

### Task 2: External AI Provider Integration (Cloud / Gemini / OpenAI Fallback)
- **Objective**: Extend `project/api_router.py` to support external AI providers (Cloudflare AI, Gemini, Vertex AI, and OpenAI fallback) alongside Ollama.
- **Deliverables**:
  - Update `project/api_router.py` with configurable providers (`OpenAI`, `Gemini`, `Cloudflare AI`, `Vertex AI`).
  - Add tests in `project/tests/test_api_router_external.py`.

### Task 3: Swiss Ephemeris Integration (`pyswisseph` / `swisseph`)
- **Objective**: Integrate Swiss Ephemeris calculation fallback/enhancement into planetary & TST / solar time modules (`project/core/solar_time.py` or new `project/core/swiss_ephemeris.py`).
- **Deliverables**:
  - `project/core/swiss_ephemeris.py` module with graceful fallback to pure python NOAA algorithms when C library is unavailable.
  - Integration with BaZi calculation for precise planetary/solar positions.
  - Unit tests in `project/tests/test_swiss_ephemeris.py`.

### Task 4: Additional Source Ingestion (Vault Expansion & Batch Ingest Enhancements)
- **Objective**: Enhance `project/rag/ingest_vault.py` with multi-source batch ingestion capabilities, enhanced metadata tracking, and CLI batch mode.
- **Deliverables**:
  - Updates to `project/rag/ingest_vault.py`.
  - Tests for new ingestion options in `project/tests/test_ingest_vault.py`.

### Task 5: CI/CD Automation (GitHub Actions Pipeline Audit & Workflow Update)
- **Objective**: Ensure `.github/workflows/ci.yml` exists, runs `pytest`, linting (`ruff`), and security checks on push/PR.
- **Deliverables**:
  - `.github/workflows/ci.yml`.

### Task 6: Consultant Web UI Enhancements (Frontend Glassmorphism)
- **Objective**: Enhance `project/static/` web interface with interactive 4-Pillar visual display, element dynamic balance graphs, and consultant chat interaction UI.
- **Deliverables**:
  - UI updates in `project/static/index.html`, `project/static/app.js`, `project/static/style.css`.
  - Verified with Web Regression test suite.

---

## Execution Phases & SDLC Compliance

1. **Phase 1: Planning** -> Plan documented in `plans/todo_tasks_plan.md`.
2. **Phase 2: Feature Implementation** -> Develop core modules & scripts.
3. **Phase 3: QA & Testing** -> Run unit tests and pytest regression.
4. **Phase 4: DevOps & Release Verification** -> Audit configs, dependencies, Docker build compatibility.
5. **Phase 5: Task Board Update & Delivery Summary** -> Update `PROJECT_TASKS.md` status to DONE and report results.
