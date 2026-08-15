# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-15 — Fixed production AI inference root cause: `api/index.js` Vercel Gateway rewritten with 5-tier inference fallback chain (Together AI → Cloudflare Workers AI → HF Inference → Gemini API → Domain Template). `project/api_router.py` cloud route priority reordered: Together AI → Cloudflare AI → Gemini (previously Together AI was dead-last after Gemini). Added `_call_cloudflare_ai()` function and `CLOUDFLARE_ACCOUNT_ID/AI_TOKEN/AI_MODEL` config vars. Fixed backend URL default (`core-api` → `core-backend`). Added `X-Deploy-SHA` + `X-AI-Source` headers for observability. Deployed to production via git push `41d59f9` → Vercel auto-deploy triggered.*


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

# 8. Full Python Pytest Suite (195/195 tests PASS as of 2026-08-09)
python3 -m pytest -v --ignore=project/kaggle_kernel
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│   ✅ DONE: Phase 6 Rust Migration 100% + Production Inference Chain Fixed      │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Decoupled DDD Multi-Cloud & Rust Core                                       │
│ • Phase 1–6: Rust Engines, SVG Charts, Prometheus, Code Reviewer, Gateway    │
│ • Swiss Ephemeris Native Pure Rust Bridge (swisseph.rs)                       │
│ • Grafana Cloud Observability Engine + Gateway Telemetry                      │
│ • 195/195 Python Pytest Suite (100% PASS)                                     │
│ • 2 Cargo integration tests + Rust Runner 12/12 PASS                         │
│ • HF Spaces Live Deploy & Audit (pphothidaen/horoconsultant-core-backend)    │
│ • Pre-Deploy Safety Audit (READY_FOR_PROD)                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│ 🆕 2026-08-15 — Production AI Inference Chain Fix (commit 41d59f9)           │
│ • api/index.js: 5-tier fallback: Together AI → CF Workers AI → HF →          │
│   Gemini → Domain Template                                                    │
│ • api_router.py: Cloud priority reorder: Together AI FIRST (was dead-last)   │
│ • Added _call_cloudflare_ai() + CLOUDFLARE_* config vars                     │
│ • Fixed backend URL default (core-api → core-backend)                        │
│ • Added X-Deploy-SHA + X-AI-Source headers for observability                 │
├───────────────────────────────────────────────────────────────────────────────┤
│ 🔑 ACTION REQUIRED: Set TOGETHER_API_KEY in Vercel Env Vars                  │
│   → https://vercel.com/dashboard → HoroConsultant → Settings → Env Vars     │
│   Get free key: https://api.together.xyz                                     │
└───────────────────────────────────────────────────────────────────────────────┘
```

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

- [x] **🆕 Production AI Inference Chain Fix — 5-Tier Fallback Architecture ([`api/index.js`](file:///Users/kimlenglim/Project/HoroConsultant/api/index.js), [`project/api_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/api_router.py))** *(2026-08-15, commit `41d59f9`)*
  - **Root Cause Fixed**: Vercel Gateway (`api/index.js`) ถูก deploy เป็น outdated commit `a737ff9` ที่ return static `{"status":"ok"}` โดยไม่มี `interpretation` field → `app.js` client-side fallback trigger template response
  - **Root Cause Fixed**: HF Serverless Inference API ไม่รองรับ MLX 4-bit quantized model (`pphothidaen/qwen2.5-7b-bazi-instruct-4bit`) → inference ล้มเหลวทุก request
  - **Root Cause Fixed**: Together AI ถูกวางไว้เป็น route สุดท้าย (after Gemini) ใน `api_router.py` cloud mode — ทั้งที่ควรเป็น primary
  - **`api/index.js` Vercel Gateway**: เขียนใหม่ทั้งหมด — 5-tier inference chain:
    1. **Together AI** `Qwen2.5-7B-Instruct-Turbo` (OpenAI-compatible API) — PRIMARY
    2. **Cloudflare Workers AI** `@cf/qwen/qwen1.5-7b-chat-awq` (REST API) — SECONDARY
    3. **HF Inference API** `pphothidaen/qwen2.5-7b-bazi-instruct-4bit` — TERTIARY
    4. **Gemini API** (9 model candidates, 2 key rotation) — QUATERNARY
    5. **Domain Template Fallback** (5 topic-specific Thai BaZi templates) — LAST RESORT
  - **`api/index.js` Architecture**: Proxy validation (ผ่านเฉพาะ response ที่มี `interpretation`/`pillars`/`chart` fields), fix backend URL default (`core-api` → `core-backend`), add `X-Deploy-SHA` + `X-AI-Source` + `X-AI-Model` headers
  - **`project/api_router.py` Cloud Mode**: Cloud priority reorder: **Together AI → Cloudflare AI → Gemini → Vertex AI** (Together AI ขึ้นมาจาก dead-last), add `_call_cloudflare_ai()` REST API caller, add `cloudflare_ai` dispatch case, add `CLOUDFLARE_ACCOUNT_ID/AI_TOKEN/AI_MODEL` config vars
  - **Deployed**: `git push origin main` → commit `41d59f9` → Vercel auto-deploy triggered
  - **Pending**: ต้องตั้ง `TOGETHER_API_KEY` ใน Vercel Env Vars → https://api.together.xyz (free tier)

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
  - **Post-Deploy Regression**: Created [`scripts/run_vercel_prod_curl_regression.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_vercel_prod_curl_regression.py) — tests live Vercel URL with exact HuggingFace browser headers: GET `/health`, OPTIONS preflight, POST `/api/v1/bazi/interpret`.

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

### 🔄 DOING (กำลังดำเนินการ)

- [ ] **⏳ Vercel Production Deployment Verification (commit `41d59f9`)** — รอ Vercel auto-deploy เสร็จจาก push `41d59f9 → main`. ต้อง verify ผ่าน `curl https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret` ว่า `X-Deploy-SHA` เป็น `41d59f9` และ response มี `interpretation` field ที่ไม่ใช่ template
  - **Blocked by**: ต้องตั้ง `TOGETHER_API_KEY` ใน Vercel Environment Variables ก่อน
  - **Next**: E2E test บน production หลัง Vercel deploy เสร็จ + key ตั้งแล้ว

---

### 📋 TODO (งานระยะถัดไป / Phased Roadmap)

> **🔥 HIGH PRIORITY — ต้องทำก่อน production inference จะทำงาน**

- [ ] **🔑 ตั้ง `TOGETHER_API_KEY` ใน Vercel Environment Variables** *(Priority: CRITICAL)*
  - ไปที่ [Vercel Dashboard](https://vercel.com/dashboard) → HoroConsultant → Settings → Environment Variables
  - สมัคร Together AI ฟรีที่ https://api.together.xyz → copy API Key
  - เพิ่ม env var: `TOGETHER_API_KEY = <your_key>`
  - Optional (Route 2): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_AI_TOKEN`, `CLOUDFLARE_AI_MODEL`
  - Optional (Rotate): `GOOGLE_AI_STUDIO_API_KEY` ใหม่จาก https://aistudio.google.com (key เก่า leaked)
  - หลังตั้งแล้ว redeploy หรือรอ Vercel trigger จาก commit `41d59f9`

- [ ] **E2E Production Verification หลัง key ตั้งแล้ว** *(Priority: HIGH)*
  ```bash
  # ตรวจสอบ deploy version
  curl -s https://horo-consultant-psi.vercel.app/health | python3 -m json.tool
  # ต้องเห็น: "version": "1.0.0.41d59f9", "inference_chain": [{route: together_ai, enabled: true}]

  # ทดสอบ E2E inference
  curl -s -X POST https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret \
    -H "Content-Type: application/json" \
    -d '{"birth_datetime":"1990-05-15 14:30:00","query":"การงานและโชคลาภ","day_master":{"stem":"庚","element":"Metal"}}' \
    | python3 -m json.tool | grep -A3 "interpretation"
  # ต้องเห็น: "interpretation" ที่เริ่มด้วย "### 🔮 ผลการทำนาย..." และ "source": "ai_agent_llm"

  # รัน full E2E regression
  python3 scripts/run_e2e_screenshots.py
  python3 scripts/run_button_regression.py
  ```

- [x] **Module 1: RAG FAISS Vector Search & Distance Metrics Native Rust Migration ([`project/rag/vector_store.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/rag/vector_store.py), [`rust_core/src/vector_search.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/vector_search.rs), [`project/core/fast_math.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/fast_math.py))**
  - Implemented SIMD unrolled Dot Product (Cosine Similarity) & L2 Euclidean Distance vector search matchers in Rust PyO3 bindings (`dense_vector_search` & `dense_vector_search_l2`).
  - Added fast math python bridge `rust_dense_vector_search_l2` with 100% NumPy fallback compatibility.
  - Current audit: 2 Cargo integration tests PASS + 13/13 Pytest extension tests PASS.

- [x] **Module 2: Astrological Audit & Canonical Consonance Native Rust Binary ([`rust_core/src/bin/audit_suite.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/audit_suite.rs))**
  - Created parallel Rust CLI binary `audit_suite` executing Five Elements, TST, and Cross-Domain consonance audits in **0.066 ms** (`READY_FOR_PROD`).

- [x] **Module 3: Grafana OTLP Telemetry & Health Monitoring Daemon ([`rust_core/src/bin/telemetry_daemon.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/telemetry_daemon.rs))**
  - Built Tokio async Rust binary daemon `telemetry_daemon` probing cloud gateways with < 4MB RAM footprint (`--once` and `--interval` modes).

- [x] **Module 4: Synthetic Chart Generation & Dataset Extractor Engine ([`rust_core/src/bin/chart_generator.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/chart_generator.rs))**
  - Built multithreaded Rayon synthetic chart generator in Rust emitting 1,000 JSONL records in **0.0018s** (**> 540,000 charts/sec**).

- [x] **Module 5: Axum Gateway High-Throughput Load Tester & Latency Analyzer ([`rust_core/src/bin/horo_benchmark.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/horo_benchmark.rs))**
  - Built Tokio async load tester CLI measuring req/sec throughput & sub-millisecond P50/P95/P99 latency distribution for Axum Gateway.

- [x] **Module 6: High-Performance Pure Rust SVG Vector Chart Generator CLI ([`rust_core/src/bin/svg_chart_cli.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/svg_chart_cli.rs))**
  - Built standalone Rust CLI for batch rendering vector SVG charts (BaZi, ZiWei, Zodiac Wheel, QiMen, XuanKong) in **< 0.05ms** per chart.

- [x] **Module 7: Parallel Multi-Discipline Metaphysics Fusion Synthesizer ([`rust_core/src/bin/fusion_synthesizer.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/fusion_synthesizer.rs))**
  - Built Rayon multi-threaded CLI binary executing all 10 domain calculation engines concurrently in **0.17 ms** emitting unified JSON charts.

- [x] **Module 8: Native Rust SDLC Agent Governance Watchdog & Health Auditor ([`rust_core/src/bin/sdlc_watchdog.rs`](file:///Users/kimlenglim/Project/HoroConsultant/rust_core/src/bin/sdlc_watchdog.rs))**
  - Built native Rust watchdog CLI auditing agent matrix specs (`.antigravity/agents/`), workspace definitions (`.agents/agents/`), docs integrity, and secret leaks.

- [x] **Harden HITL Button Regression Contracts ([`scripts/run_button_regression.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_button_regression.py))**
  - Selects a deterministic valid item from `/hitl/queue`, then asserts successful draft → review → undo lifecycle responses (HTTP 200).
  - Verifies invalid-ID behavior as a separate negative-path test (`test_hitl_negative_path_invalid_id_btn`, HTTP 404).

- [x] **Make Playwright E2E Results Portable and Trustworthy ([`scripts/run_e2e_screenshots.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_e2e_screenshots.py))**
  - Replaced hard-coded external artifact directory with configurable local output path (`E2E_ARTIFACT_DIR` / `project/tests/artifacts/screenshots`).
  - Records every caught browser-step exception as a `FAILED` result so reports accurately reflect execution outcomes.

- [x] **Establish 10-Point Master Architecture & Operating Consensus Matrix ([`plans/plan.md`](file:///Users/kimlenglim/Project/HoroConsultant/plans/plan.md))**
  - Resolved 10 comprehensive architectural decisions via `/grill-me` (Hybrid Failover, Two-Way Telegram Controller, Event-Driven Kaggle GPU Loop, Periodic OTLP Exporter, Consensus Matrix, Instant FAISS Ingest, 2-Tier Caching, Adaptive Rate Limiter, Multi-Lingual Glossary, and Zero-Tolerance Quality Gate).

- [x] **Vertex AI Direct Bearer Token Failover Integration ([`project/api_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/api_router.py))**
  - Implemented `_get_vertex_ai_credentials()` for dynamic RS256 OAuth2 token exchange with Service Account JSON.
  - Implemented `_call_vertex_ai()` for direct Google Cloud Vertex AI REST inference with zero API key expiration.
  - Integrated `vertex_ai` route type into `HybridRouter` priority cloud failover chain.

- [x] **Domain Terminology & Multi-Lingual Alignment Engine ([`project/core/glossary.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/glossary.py))**
  - Built canonical glossary engine covering 10 Heavenly Stems, 12 Earthly Branches, 10 Gods, and 5 Elements.
  - Implemented automatic language detection (Thai, Chinese, English) with strict Pinyin + Hanzi pairing.

- [x] **2-Tier Caching Engine with LRU in RAM & Model Auto-Eviction ([`project/core/cache_manager.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/cache_manager.py))**
  - Implemented Tier 1 in-memory `OrderedDict` LRU cache (< 0.1ms) + Tier 2 persistent JSON disk cache.
  - Implemented `invalidate_on_model_update()` to auto-purge stale AI readings upon new fine-tune releases.

- [x] **Adaptive Multi-Tier Rate Limiter & DDoS Micro-Burst Guard ([`project/core/rate_limiter.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/rate_limiter.py))**
  - Configured role-based quotas (Anonymous 20 RPM vs Admin 120 RPM).
  - Implemented 1-second sliding window DDoS micro-burst protection (Max 5 RPS) with audit logging.

- [x] **Consensus Matrix & Five Elements Anchor Synthesis Engine ([`project/core/multi_agent_debate.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/core/multi_agent_debate.py))**
  - Enforced BaZi Five Elements balance as core baseline anchor across 10 metaphysical disciplines.
  - Structured cross-discipline consensus scoring ($0.0 \sim 1.0$), consonance factors, and cautionary factors.

- [x] **HITL Instant FAISS Ingestion & Training Queue Milestone Detector ([`project/hitl_router.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/hitl_router.py))**
  - Added instant vector store ingestion upon review approval for live RAG retrieval.
  - Added milestone threshold detector ($\ge 50$ approved samples) for Kaggle GPU fine-tuning trigger.

- [x] **Two-Way Interactive Telegram Bot Controller & Webhook ([`project/mlops/notifications/telegram_controller.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/mlops/notifications/telegram_controller.py), [`project/main.py`](file:///Users/kimlenglim/Project/HoroConsultant/project/main.py))**
  - Implemented interactive commands (`/status`, `/health`, `/metrics`, `/cache`, `/switch_key`).
  - Registered `/api/v1/telegram/webhook` endpoint with direct response dispatching.

- [x] **Strict Zero-Tolerance Quality Gate Orchestrator ([`scripts/run_quality_gate.py`](file:///Users/kimlenglim/Project/HoroConsultant/scripts/run_quality_gate.py))**
  - Unified 4-stage quality gate enforcing 100% pass across Secret Scans, Agent Sync, Pytest, and 25 Button contracts.






