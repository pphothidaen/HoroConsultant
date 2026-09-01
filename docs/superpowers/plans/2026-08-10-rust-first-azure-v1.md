# Rust-first Azure v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver and verify a cost-aware Rust-first HoroConsultant production runtime as private Linux AMD64 image `pansakorn/horoconsult:v1.0` on Azure Container Apps without breaking the existing API.

**Architecture:** Axum listens on public container port 8000, serves parity-qualified Rust calculations, and proxies an explicit route allowlist to a supervised Uvicorn worker on localhost:8001. Vercel/Hugging Face keep the static UI instantly available while Azure scales to zero and uses immutable blue/green revisions.

**Tech Stack:** Rust 1.97.1, Axum/Tokio, Python 3.12, FastAPI/Uvicorn, Docker Buildx, GitHub Actions, Docker Hub private registry, Azure Container Apps Consumption, Vercel, Playwright/Pytest.

> **Historical plan:** task-file references record the original plan context.
> `atomic_tasks.md` is the current operational task registry.

## Global Constraints

- Preserve all current public route methods, paths, statuses, request/response schemas, OpenAPI behavior, and SVG content.
- Public container port is `8000`; Python worker is private at `127.0.0.1:8001`.
- Build and publish only `linux/amd64`; push immutable `sha-<git-sha>` plus `v1.0` and `latest`, then deploy the resolved digest. Never overwrite `v1.0` after this release.
- Exact categorical/integer parity; float tolerance `1e-6`; equation-of-time tolerance `0.01` minute.
- Migration gate: endpoint p95 at least 20% faster and CPU/request at least 30% lower; otherwise PARK the candidate and retain Python.
- No dense-vector `.tolist()` copies, checked-in native libraries, recursive native loader, silent production fallback, secret output, fake UI success, or automatic retry of mutations.
- Azure defaults: `southeastasia`, Consumption, multiple revisions, min replicas 0, max replicas 1, 0.5 vCPU/1 GiB, Target port 8000.
- Python logging emitted by subprocess/CI paths uses ASCII `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]` tags.
- Use TDD for every behavior change: add the test, capture expected RED, implement, and capture GREEN.

---

### Task 1: Requirements, Kanban, and Baseline Evidence

**Files:**
- Create: `docs/superpowers/specs/2026-08-10-rust-first-azure-v1-design.md`
- Create: `docs/superpowers/plans/2026-08-10-rust-first-azure-v1.md`
- Modify: `plans/plan.md`
- Modify: `atomic_tasks.md`

**Interfaces:**
- Produces the binding design, task boundaries, acceptance matrix, and active Kanban card used by every later task.

- [x] Record the clean starting SHA and full baseline result `200 passed, 1 warning` from `python3 -m pytest -v --ignore=project/kaggle_kernel`.
- [x] Replace the obsolete Grafana master plan with goal, ROI matrix, FR/NFR, architecture, rollout, and test matrix for this release.
- [x] Correct the board summary, move completed Rust checkboxes out of TODO, add the production-readiness audit under DONE, and add the Rust-first Azure release under DOING with Root Cause and Prevention.
- [x] Commit the documentation foundation as `docs: plan rust-first Azure v1 release`.

### Task 2: Rust Toolchain, Packaging, and Honest Runtime Identity

**Files:**
- Modify: `rust_core/Cargo.toml`, `rust_core/src/lib.rs`, `rust_core/__init__.py`, `project/core/fast_math.py`
- Create/modify tests under: `rust_core/tests/`, `project/tests/test_rust_extensions.py`
- Delete: tracked `rust_core/*.so`

**Interfaces:**
- Produces deterministic imports and runtime identity used by Docker, CI, and the gateway.
- `runtime_backend() -> dict[str, object]` reports `rust_available`, `rust_version`, and active kernel names without secrets.

- [x] Add a Python integration test that fails when import order changes native availability or a source-tree `.so` is scanned.
- [x] Add Rust tests that fail under the current abort/test profile and for exported kernels lacking real behavior assertions.
- [x] Remove host binary discovery and expose one standard installed-package import path; retain explicit development fallback only behind `HORO_ALLOW_PYTHON_FALLBACK=1`.
- [x] Set test/runtime-safe panic behavior, split library features so pure core/server do not require PyO3, and remove committed native artifacts.
- [x] Build/install the wheel in a clean environment and run Python tests against the installed wheel before committing `build: make Rust packaging deterministic`.

### Task 3: BaZi and Solar-Time Parity

**Files:**
- Modify: `rust_core/src/bazi.rs`, `rust_core/src/solar.rs`
- Test: `rust_core/tests/test_bazi_parity.rs`, `project/tests/test_bazi_calculator.py`

**Interfaces:**
- `calculate_bazi(...)` and true-solar-time output must serialize to the existing Python response schema.

- [x] Add literal golden cases for Li Chun boundaries, leap day, timezone/longitude extremes, 23:00 day rollover, and known Bangkok/Singapore charts; capture RED against hard-coded or divergent Rust behavior.
- [x] Port the canonical Python calculations, including hidden stems, season weighting, equation of time, standard meridian, and pillar boundaries.
- [x] Add deterministic 10,000-case parity and 100,000-input invalid/fuzz runners with reproducible seeds.
- [x] Benchmark complete endpoint work rather than isolated FFI calls; enable Rust only if both ROI thresholds pass, otherwise record PARKED evidence.
- [x] Commit as `feat: make Rust BaZi and solar time parity-gated`.

### Task 4: Remaining Engine, SVG, and Metrics Parity

**Files:**
- Modify: Rust engine modules under `rust_core/src/` and their matching `project/core/*_engine.py` adapters
- Test: `rust_core/tests/test_engine_parity.rs`, `project/tests/test_5_branch_engines.py`, `project/tests/test_expanded_astrology_engines.py`, `project/tests/test_e2e_mcp_svg.py`

**Interfaces:**
- Rust handlers must return the exact existing ZiWei, QiMen, XuanKong, Thai/Vedic, I Ching, LiuRen, ZeJi, Numerology, SVG, and metrics structures.

- [ ] Add golden fixtures that expose the known XuanKong 12/24 mismatch, placeholder SVG data loss, and any method/schema mismatch; verify RED.
- [ ] Correct each pure calculation against the Python oracle, one engine per red-green cycle.
- [ ] Keep Swiss Ephemeris and Western/Uranian astronomical calculations in Python; do not replace native Swiss Ephemeris with analytical approximations.
- [ ] Run per-engine parity and full endpoint benchmarks; enable only qualifying Rust engines and record the others as PARKED.
- [ ] Commit as `feat: gate Rust astrology engines on parity and ROI`.

### Task 5: Axum Gateway and Supervised Python Worker

**Files:**
- Modify: `rust_core/src/bin/horo_server.rs`, `rust_core/src/server.rs`, `project/main.py`
- Create: gateway contract/integration tests under `rust_core/tests/` and `project/tests/`

**Interfaces:**
- Axum binds `0.0.0.0:8000`; Uvicorn binds `127.0.0.1:8001`.
- Proxy preserves request bytes, query, method, selected end-to-end headers, response status/content type/body, and correlation ID.

- [ ] Capture the Python OpenAPI document and representative responses as literal goldens, then add failing tests for current Axum method/path/schema differences.
- [ ] Implement process supervision, readiness wait, signal forwarding, and fail-fast child handling without a shell as PID 1.
- [ ] Implement exact Rust routes plus a closed proxy allowlist for dynamic/admin/HITL/native-library routes; reject unknown proxy targets.
- [ ] Add health/runtime identity, payload limits, timeouts, hop-by-hop header stripping, and CORS parity.
- [ ] Run all 42 route contract checks through the gateway and commit `feat: add contract-safe Rust production gateway`.

### Task 6: Cold-start UI and Vercel Gateway

**Files:**
- Modify: `project/static/app.js`, `project/static/index.html`, `project/static/style.css`, `vercel.json`
- Test: `project/tests/test_web_regression.py`, `project/tests/test_prod_regression.py`, Playwright scripts/tests

**Interfaces:**
- `wakeBackend()` probes readiness with 1/2/4/8/10-second delays up to 60 seconds.
- `ensureBackendReady()` gates a user action but never retries its mutation request.

- [ ] Add failing browser/unit contract tests for cold startup, preserved inputs, `aria-live`, one mutation request, retry UI, and removal of fake success.
- [ ] Implement the wake state machine and separate API-waking from AI-processing status.
- [ ] Route static requests to Hugging Face and API/health requests to the Azure origin through Vercel; keep previews protected and production public.
- [ ] Make Playwright output portable and fail caught steps instead of reporting them as successful.
- [ ] Commit `feat: add safe cold-start experience`.

### Task 7: Linux Image, CI, and Azure Infrastructure

**Files:**
- Modify: `Dockerfile`, `.github/workflows/ci.yml`, release/deployment workflows
- Create: `infra/azure/` declarative resources and cost-guard workflow/script
- Remove/retire: automatic Fly and unrelated Kaggle-on-main deployment paths

**Interfaces:**
- Image tags: `baseline-<sha>`, `rc-<sha>`, immutable `sha-<sha>`, one-time alias `v1.0`, and convenience alias `latest`; Azure is pinned to their verified digest.
- Registry secrets: GitHub read/write push token and Azure read-only pull token; no value output.

- [ ] Add tests that fail against the current Dockerfile/CI because Rust is absent, Python is 3.11, the wheel is not installed, and pytest is not explicitly installed.
- [ ] Build a multi-stage Python 3.12/Rust 1.97.1 non-root image with Axum health check, OCI Git labels, and only runtime assets.
- [ ] Make CI install and test the wheel, run fmt/clippy/Rust/Python/contract/security gates, inspect AMD64 image metadata, generate SBOM, and push only after gates pass.
- [ ] Add Azure Consumption/multiple-revision resources, private registry reference, probes, labels, Target port 8000, min 0/max 1, and OIDC deployment.
- [ ] Add a conservative monthly usage guard that disables external ingress at 70% of free allowance or any billed cost, and re-enables after reset plus health smoke.
- [ ] Replace unsafe secret-sync output with key-name/status-only behavior; commit `ci: add private AMD64 Azure release pipeline`.

### Task 8: Release Verification, Documentation, and Production Cutover

**Files:**
- Modify: verification/release scripts, `README.md`, `HOWTO.md`, `atomic_tasks.md`, `plans/plan.md`, `.agents/LESSONS_LEARNED.md`

**Interfaces:**
- Verification accepts an expected Git SHA, image digest, Azure revision, and public base URL and exits non-zero on any mismatch.

- [ ] Build/push `baseline-<sha>` and deploy blue without moving public traffic; prove health and rollback.
- [ ] Push the feature branch, open the PR, run required checks, merge through the approved PR flow, and build green from the resulting main SHA.
- [ ] Deploy green by digest with zero traffic, verify contract/parity/performance/E2E on its revision-label URL, then promote that digest to `v1.0` and `latest` and verify both aliases resolve to it.
- [ ] Switch Azure traffic and Vercel production routing, verify public SHA/runtime and all UI contracts, and observe a 30-minute soak; exercise rollback before final promotion if any threshold fires.
- [ ] Revoke the exposed Docker credential and ensure production uses newly scoped push/pull tokens without printing them.
- [ ] Update every operational document with exact final commands/counts/digest/revision, move the Kanban card to DONE with Root Cause and Prevention, and commit `docs: record Azure v1 production evidence`.
