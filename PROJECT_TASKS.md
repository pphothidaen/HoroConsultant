# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-10 — Rust-first Azure v1 implementation is active. Clean baseline at `e7c041c`: 200/200 Pytest PASS with one upstream deprecation warning. Historical Rust completion claims are being re-qualified against Linux packaging, parity, and ROI gates.*


---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# === RUST NATIVE CI/CD TOOLS ===

# 1. Native Rust tests (portable; install the pinned toolchain first)
rustup toolchain install 1.97.1
cd rust_core
cargo +1.97.1 fmt --check
cargo +1.97.1 clippy --all-targets --all-features -- -D warnings
cargo +1.97.1 test --all-targets --all-features
cd ..

# 2. Code reviewer and secret scan
python3 project/core/code_reviewer.py --review

# 3. Agent and governance checks
python3 scripts/sync_sdlc_agents.py --check
python3 scripts/sync_codex_agents.py --check

# 4. Pre-deployment secret scan
python3 project/core/code_reviewer.py --scan-secrets

# 5. Full Python suite (fresh baseline: 200 passed on 2026-08-10)
python3 -m pytest -v --ignore=project/kaggle_kernel

# 6. Linux AMD64 image build (push is performed only by release CI)
docker buildx build --platform linux/amd64 --load -t horoconsult:dev .
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────┬───────────────────────────┬────────────────────────┐
│          ✅ DONE          │         🔄 DOING         │        📋 TODO         │
├───────────────────────────┼───────────────────────────┼────────────────────────┤
│ • Rust/production audit   │ • Rust-first Azure v1     │ • HITL hardening       │
│ • Python baseline 200/200 │ • Linux AMD64 packaging  │ • Future LLM scope     │
│ • Existing Python API     │ • Parity + ROI gates      │                        │
│                           │ • Cold-start UX + release │                        │
└───────────────────────────┴───────────────────────────┴────────────────────────┘
```

---

- [x] **Historical/superseded report — Complete Zi Wei Dou Shu & Qi Men Dun Jia Rust Engine Migration & Python Cleanup ([`rust_core/src/ziwei.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/ziwei.rs), [`rust_core/src/qimen.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/qimen.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`project/core/zi_wei_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/zi_wei_engine.py), [`project/core/qi_men_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/qi_men_engine.py)); not current production evidence**
  - **Zi Wei Dou Shu Rust Native Binding**: Implemented `calculate_ming_shen_gong`, `calculate_zi_wei_star_branch`, and `calculate_14_main_stars` in Rust PyO3. Integrated into `fast_math.py` (`fast_ziwei_stars`) and `zi_wei_engine.py`.
  - **Qi Men Dun Jia Rust Native Binding**: Implemented `qimen_9palace_matrix` in Rust PyO3 for 4-plate 9-palace matrix placement (Earth Plate, 9 Stars, 8 Doors, 8 Spirits). Integrated into `fast_math.py` (`fast_qimen_matrix`) and `qi_men_engine.py`.
  - **Python Redundant Loop Cleanup**: Eliminated duplicate pure-Python matrix generation loops in favor of unified `fast_math.py` Rust PyO3 acceleration with NumPy zero-overhead fallback.
  - **Historical test result (superseded)**: Extended [`project/tests/test_rust_extensions.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_rust_extensions.py) — 174/174 Pytest tests PASSED 100% at that time; current release evidence is the 200-test baseline and active gates.

- [x] **Historical/superseded report — Phase 2 Rust Extensions: FAISS Dense Vector Search & Xuan Kong 9-Grid Matrix ([`rust_core/src/vector_search.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/vector_search.rs), [`rust_core/src/fengshui.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/fengshui.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`project/rag/vector_store.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/rag/vector_store.py), [`project/core/xuan_kong_engine.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/xuan_kong_engine.py)); not current production evidence**

  - **Historical benchmark (superseded)**: The FAISS Dense Vector Rust Native Binding was reported as sub-millisecond (< 1ms) retrieval; this is not current endpoint evidence and the active audit retains NumPy/FAISS pending the ROI gate.
  - **Feng Shui Flying Star 9-Grid Rust Matrix**: Implemented `resolve_mountain`, `fly_stars`, and `xuankong_9grid_matrix` in Rust PyO3 for 24-mountain directions and Period 9 Flying Stars chart math. Integrated into `xuan_kong_engine.py` and `fast_math.py`.
  - **Historical test result (superseded)**: Added [`project/tests/test_rust_extensions.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_rust_extensions.py) — 172/172 Pytest tests PASSED 100% at that time; current release evidence is the 200-test baseline and active gates.

- [x] **Kaggle GPU Fine-Tuning Iteration Pipeline Automation ([`scripts/kaggle_notebook_manager.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/kaggle_notebook_manager.py))**
  - Configured automated setup, notebook generation, and metadata verification for `qwen2.5:7b` fine-tuning on Nvidia Tesla T4 GPU.
  - Locked metadata accelerator configuration (`NvidiaTeslaT4`) preserved strictly.

- [x] **Historical/superseded report — Phase 3 Rust Extensions: Rust Metaphysical Engine Coverage & CI/CD ABI3 Audit ([`rust_core/src/thai_vedic.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/thai_vedic.rs), [`rust_core/src/uranian.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/uranian.rs), [`rust_core/src/iching.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/iching.rs), [`rust_core/src/liuren.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/liuren.rs), [`rust_core/src/zeji.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/zeji.rs), [`rust_core/src/numerology.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/numerology.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py), [`.github/workflows/ci.yml`](file:///Users/kimlenglim/Project/HoroConsultant/.github/workflows/ci.yml)); not current production evidence**
  - **Historical claim (superseded)**: The six Rust modules were previously described as providing 100% Rust high-performance math-core coverage across ten branches; current release enablement is per-engine and requires parity plus ROI evidence.
  - **Fast Math Bridge Integration**: Added Python PyO3 bindings in `project/core/fast_math.py` (`fast_thai_lagna`, `fast_thaksa_map`, `fast_uranian_midpoint`, `fast_uranian_sensitive_point`, `fast_liuren_heaven_plate`, `fast_zeji_duty_officer`, `fast_satta_lek_matrix`).
  - **CI/CD Build Staging**: Updated `.github/workflows/ci.yml` with `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` and Maturin wheel building step in GitHub Actions.
  - **Historical test result (superseded)**: Extended `project/tests/test_rust_extensions.py` — the 177/177 suite was reported at a 100% pass rate at that time; current release evidence must come from the active Python/Rust/contract gates.


- [x] **Local OpenAI Codex CLI (`CODEX_CHATGPT`) AI Provider & Dynamic Provider Router ([`project/core/ai_provider_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/ai_provider_router.py), [`project/core/codex_client.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/codex_client.py), [`project/tests/test_ai_provider_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/tests/test_ai_provider_router.py))**
  - **Local ChatGPT Pro Subcription Integration**: Executes non-interactive `codex exec -s read-only --json` using local session (`codex login`). Completely eliminates API key requirements (`OPENAI_API_KEY`, `CODEX_PRO`) and API billing.
  - **Provider Architecture**: Implemented `AIProviderRouter` with `PRIMARY = CODEX_CHATGPT` and `FALLBACK = GEMINI`.
  - **Health Check & Error Taxonomy**: Implemented `get_provider_health()` reporting `installed`, `authenticated`, and `available` status. Distinguishes error taxonomy (`command_not_found`, `not_authenticated`, `rate_limit_exceeded`, `timeout`, `malformed_response`, `execution_error`).
  - **Verified Test Suite**: Added `project/tests/test_ai_provider_router.py` (9/9 PASS covering Requirements A–F). Verified full 165/165 Pytest suite passing 100%. Real local smoke test returned `CODEX_CHATGPT_OK`.

- [x] **Production CI/CD Build Staging & Multi-Cloud Health Status Verification ([`api/index.js`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.js), [`scripts/publish_space_hf.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/publish_space_hf.py), [`project/static/app.js`](file:///Users/kimlenglim/Project/HoroConsultant/project/static/app.js))**

  - [x] **Auto-Inject Git Commit Version Staging**: Inject exact Git commit version string (`v1.0.0.<commit_hash>`) into static `index.html` during `publish_space_hf.py` build staging.
  - [x] **Vercel Serverless Handler Resolution**: Simplify `api/index.js` using Vercel `res.status().json()` methods to eliminate stream hanging and resolve `FUNCTION_INVOCATION_FAILED`.
  - [x] **Amber Status Indicator Wording**: Update `#f59e0b` amber badge text to accurately state `Health: Standby (Local Engine Fallback)` when backend health check is in fallback state.
  - [x] **End-to-End Live Health Status Verification**: Implemented [`scripts/run_live_health_verification.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_live_health_verification.py) — verifies HTTP 200 across HF Spaces, Fly.io, and Vercel with detailed latency reporting.

- [x] **Post-Deployment Synthetic Health Monitoring Cron** ([`scripts/synthetic_health_monitor.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/synthetic_health_monitor.py))
  - Implemented scheduled 5-minute health ping checks against `/health` and `/api/v1/health` for all cloud deployments.
  - Supports `--once` (single-shot) and `--interval <seconds>` (continuous loop) modes.
  - Formats OTLP metric payloads and pushes to Grafana Cloud when credentials are set.
  - Run: `python3 scripts/synthetic_health_monitor.py --once` or `python3 scripts/synthetic_health_monitor.py --interval 300`

- [x] **Extend Grafana Exporter for Gateway Telemetry** ([`scripts/grafana_cloud_exporter.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/grafana_cloud_exporter.py))
  - Added `fetch_gateway_telemetry()` function that probes Vercel, HF Spaces, and Fly.io health endpoints.
  - Collects `gateway_response_latency_ms`, `gateway_http_status_code`, and `gateway_http_requests_total` (bucketed by 2xx/4xx/5xx/error).
  - Added `--push-gateway-telemetry` CLI flag to push OTLP payload to Grafana Cloud.
  - Run: `python3 scripts/grafana_cloud_exporter.py --dry-run --push-gateway-telemetry`
  - Verified: 9 OTLP data points generated across 3 gateways × 3 metrics (exit code 0 ✅)

---

### ✅ DONE (historical completed work; current release remains gated)

- [x] **Rust migration ROI and production-readiness audit (`e7c041c`)**
  - **Evidence**: Clean worktree baseline completed 200/200 Pytest tests; production Dockerfiles did not build/install `rust_core`; tracked native binaries were macOS ARM64; direct Rust import was order-dependent; several engine outputs and benchmarks did not match their Python reference.
  - **Decision**: Replace blanket "100% Rust" claims with per-engine parity and ROI qualification. Keep Swiss Ephemeris, FAISS/NumPy, RAG/LLM, geolocation, admin, and HITL in the private Python worker.
  - **Root Cause**: CI built Rust separately from Python/runtime tests, while deployment images omitted Rust and silent fallbacks masked the inactive native path.
  - **Prevention**: Release CI must install the Linux wheel/image, attest the active runtime backend, compare API goldens, and fail when a required Rust handler is unavailable.

- [x] **Historical/superseded report — Decoupled DDD Multi-Cloud Architecture & Rust High-Performance Core Engine Strategy ([`rust_core/`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/), [`vercel.json`](file:///Users/kimlenglim/Project/HoroConsultant/vercel.json), [`Dockerfile.hf`](file:///Users/kimlenglim/Project/HoroConsultant/Dockerfile.hf)); not current production evidence**
  - **Historical design targets (superseded)**: The Fly.io Rust Axum gateway was specified at < 8 MB RAM, < 20 ms cold start, and 50,000+ requests/sec in Singapore; no current release evidence establishes these targets.
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
  - **Historical performance report (superseded)**: Parallelized 10-Domain Engines execution was reported at < 2.0 s latency; this is not current release evidence.
- [x] **Unified Admin Panel & HITL Studio Security Integration (`project/static/admin.html`)**
  - Integrated HITL Review Studio directly into Admin Panel navigation sidebar (`showPage('hitl')`).
- [x] **Production Secret Environment Variables Injection & Verification**
  - Verified `HF_TOKEN`, `GEMINI_API_KEY`, and `OPENAI_API_KEY` in environment config & fallback chain.
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
  - **Post-Deploy Regression**: Created [`scripts/run_vercel_prod_curl_regression.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_vercel_prod_curl_regression.py) — tests live Vercel URL with exact HuggingFace browser headers: GET `/health`, OPTIONS preflight, POST `/api/v1/bazi/interpret`.

- [x] **Historical/superseded report — Phase 6.1: Standalone Pure Rust Axum API Gateway & Core Metaphysical Engines (Option C) ([`rust_core/src/bin/horo_server.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/horo_server.rs)); not current production evidence**
  - **Historical performance report (superseded)**: The Rust server binary was reported as a full Axum gateway with < 10 MB RAM and < 1 ms latency; these are not current release measurements.
  - **Historical routing claim (superseded)**: The listed calculation routes were previously described as pure Rust; current routing is enabled only after parity and ROI gates, with the Python worker retained where required.
  - **Python RAG Async Proxy**: `/api/v1/proxy/*path` targeting Python RAG/LLM Service (`PYTHON_RAG_HOST`).

- [x] **Historical/superseded report — Phase 6.2: Native Rust Regression Runner Integration (Option 1) ([`rust_core/src/bin/regression_runner.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/regression_runner.rs)); not current production evidence**
  - **Historical report (superseded)**: A 12-check parallel Rust CLI Runner (`regression_runner`) was reported to complete in **0.078 s** on 2026-08-09; this is not the current release gate.
  - **Historical execution claim (superseded)**: The listed audits were previously described as running in pure Rust; current runtime identity and per-engine parity must be verified in the installed Linux image.
  - **Historical test claim (superseded)**: The Rust binaries were previously reported at a 100% test pass rate; current release evidence must come from the active Python/Rust/contract gates.

- [x] **Historical/superseded report — Swiss Ephemeris Native Pure Rust Bridge ([`rust_core/src/swisseph.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/swisseph.rs)); not current production evidence**
  - **Historical implementation claim (superseded)**: The analytical planetary ephemeris functions were previously described as a high-precision pure-Rust engine; the current audit retains native Python/C Swiss Ephemeris because the Rust approximation does not meet the accuracy contract.

- [x] **BaZi Interpretation Router Singleton Regression Fix ([`project/routers/debate.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/routers/debate.py))**
  - The interpretation endpoint now shares the application `HybridRouter` singleton instead of constructing an independent router, so its configured routing and test dependency are consistent.
  - Verified by the previously failing `test_bazi_interpret_basic` and the full **195/195** Pytest suite.

- [x] **Backward-Compatible Codex Subagent Configuration ([`scripts/sync_codex_agents.py`](scripts/sync_codex_agents.py), [`.codex/agents/`](.codex/agents/), [`AGENTS.md`](AGENTS.md))**
  - Reuses the 16 existing `.agents/agents/*/agent.json` role definitions as the source and generates native Codex TOML files without changing Antigravity files or legacy provider allocations.
  - Adds `--check` drift detection, TOML parsing tests, and safe historical model guidance: Codex roles inherit the active Codex model.
  - Verification: both synchronization checks pass; Codex migration plus legacy agent configuration tests pass **6/6**. The remaining pre-existing live-Codex fallback test requires its configured 45-second CLI timeout and exceeds this harness's foreground-command limit.

### 🔄 DOING (กำลังดำเนินการ)

- [ ] **Cost-aware Rust-first Azure v1 production runtime (`feat/rust-first-azure-v1`)**
  - **Scope**: Linux AMD64 private image `pansakorn/horoconsult` tagged with immutable SHA, `v1.0`, and `latest`; Axum public port 8000; supervised Python worker on localhost:8001; Azure Container Apps blue/green; Vercel/HF static UI. Azure is pinned to the verified digest.
  - **ROI Gate**: Enable an engine in Rust only after exact schema parity, numeric tolerance, endpoint p95 improvement of at least 20%, and CPU/request reduction of at least 30%; otherwise mark it PARKED and retain Python.
  - **Compatibility & fallback**: Preserve all current public API contracts. Roll back by immutable Azure revision/image digest rather than shipping duplicate silent fallback algorithms.
  - **Dead-code cleanup**: Remove tracked native binaries, recursive native loading, `.tolist()` dense-vector bridge, retired Fly deployment automation, and fake UI success behavior.
  - **Verification**: Python/Rust/contract/fuzz/UI/security/Linux-image gates, private registry pull, Azure green-label E2E, production soak, and rollback exercise.
  - **Root Cause**: The previous migration optimized code artifacts without proving that production loaded them or that their results and resource use were better.
  - **Prevention**: One immutable SHA/digest must pass installed-runtime identity, parity, performance, and live release verification before traffic promotion.

---

### 📋 TODO (งานระยะถัดไป / Phased Roadmap)

- [ ] **Harden HITL Button Regression Contracts**
  - Select a deterministic valid item from `/hitl/queue`, then assert successful draft → review → undo lifecycle responses (rather than treating `404` from a synthetic ID as a pass).
  - Keep invalid-ID behaviour as a separate negative-path test.

- [ ] **Make Playwright E2E Results Portable and Trustworthy**
  - Replace the hard-coded external artifact directory with a configurable local output path.
  - Record every caught browser-step exception as a failed result so the 17-step report cannot overstate success.

- [ ] **Define the Future LLM Model Expansion Scope**
  - The master plan lists this roadmap item but has no approved provider/model, acceptance criteria, budget, or deployment target.

---

### ⏸ PARKED (ไม่ผ่าน ROI/accuracy gate ในการตรวจล่าสุด)

- [ ] **Rust dense-vector bridge**
  - Keep NumPy/FAISS active because the current PyO3 `.tolist()` bridge measured more than 1,000x slower than NumPy BLAS. Revisit only with a zero-copy buffer and at least 20% p95 improvement.
- [ ] **Pure-Rust Swiss Ephemeris replacement**
  - Keep the native Python/C Swiss Ephemeris path because the Rust approximation covers fewer bodies and does not meet the existing accuracy contract.
- [ ] **Blanket migration of RAG/LLM, admin, HITL, geolocation, and deployment orchestration**
  - Keep these in Python unless a production profile shows a qualifying CPU hotspot and a payback period within six months.
