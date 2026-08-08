# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-08 15:47 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Playwright E2E Visual Browser Suite (17/17 PASSED 100%)
python3 scripts/run_e2e_screenshots.py

# 2. รัน UI Button & Endpoint Contract Regression Suite (25/25 PASSED 100%)
python3 scripts/run_button_regression.py

# 3. รัน Pre-Deployment Safety Audit & Secret Scan (READY_FOR_PROD)
python3 project/core/code_reviewer.py --review

# 4. รัน Hugging Face Spaces Deployment Dry Run
python3 scripts/publish_space_hf.py --dry-run

# 5. รัน Full Unit, Integration & Universal Bridge Test ทั้งหมด (138/138 tests PASS)
python3 -m pytest -v --ignore=project/kaggle_kernel

# 6. ตรวจสอบสถานะซิงก์ของ SDLC Agents ข้ามแพลตฟอร์ม (Antigravity & Claude Code)
python3 scripts/sync_sdlc_agents.py --check
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────┬───────────────────────────────────────┬───────────────────────────────────────┐
│              ✅ DONE                  │              🔄 DOING                 │              📋 TODO                  │
├───────────────────────────────────────┼───────────────────────────────────────┼───────────────────────────────────────┤
│ • Playwright E2E Screenshots (17/17)  │ (None - All tasks completed 100%)     │ • Grafana Cloud All-in-One            │
│ • UI Button & Endpoint Suite (25/25)  │                                       │   Monitoring Integration (Phased)     │
│ • HF Spaces Live Deploy & Audit       │                                       │                                       │
│ • Static Assets & Async Route Fix     │                                       │                                       │
│ • Pre-Deploy Safety Audit (PASS)      │                                       │                                       │
│ • Doppler Secret Sync & Audit         │                                       │                                       │
│ • 138/138 Pytest Suite (100% PASS)    │                                       │                                       │
│ • Agent Spec & Skill Governance Sync  │                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

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
  - Verified `HF_TOKEN`, `GEMINI_API_KEY`, and `OPENAI_API_KEY` in environment config & fallback chain.
- [x] **Post-Finetune DB Vector Purge Execution & Pipeline ([`scripts/post_train_fuse.py`](file:///scripts/post_train_fuse.py))**
  - Configured model fusion, GGUF conversion, and vector store cleanup post-training pipeline.
- [x] **Vercel Edge API Gateway Proxy Setup ([`vercel.json`](file:///vercel.json))**
  - Configured `/api/hf/:path*` route forwarding to Hugging Face Spaces Core Backend (`pphothidaen-horoconsultant-core-backend.hf.space`).
- [x] **Unit, Integration & Pre-Deployment Audit Baseline**
  - Verified 111/111 tests passing cleanly in 2.85s.
  - Verified `project/core/code_reviewer.py` status `READY_FOR_PROD` with zero secret leaks.

---

### 🔄 DOING (กำลังดำเนินการ)

- *(ไม่มี - งานทั้งหมดอยู่ในสถานะ DONE)*

---

### 📋 TODO (งานระยะถัดไป / Phased Roadmap)

- [ ] **Grafana Cloud All-in-One Production Monitoring & Observability Integration**
  - **Goal**: ติดตั้งระบบ Centralized Observability แบบ All-in-One สำหรับ Hugging Face Spaces (Docker) และ Ollama Engine บน Grafana Cloud Free Tier
  - **Key Components & Features**:
    1. **Synthetic Uptime Monitoring**: ตั้งค่า Grafana Synthetic Ping ยิงไปที่ `/health` endpoint ทุกๆ 1-3 นาที เพื่อแจ้งเตือนเมื่อระบบเกิด Downtime และช่วยป้องกันไม่ให้ Hugging Face Space เข้าสู่ Sleep Mode
    2. **Centralized Log Aggregation (Grafana Loki)**: ส่ง stdout/stderr จาก FastAPI (`uvicorn`) และ Ollama Server ไปจัดเก็บแบบ Centralized บน Grafana Loki (ฟรี 50 GB/เดือน) สำหรับวิเคราะห์ error logs ย้อนหลัง
    3. **LLM Tracing & RAG Observability (Grafana Tempo / OpenTelemetry)**: ติดตั้ง `opentelemetry-distro` ใน FastAPI เพื่อติดตาม Response Latency, Token Generation Speed ($t/s$), และ Trace การทำงานในขั้นตอน RAG Vector Retrieval (FAISS)
    4. **System Metrics (Prometheus Metrics)**: ติดตั้ง Prometheus Middleware เพื่อดูสถิติ Request Rates (RPM), Status Code breakdown (2xx/4xx/5xx), และการใช้งาน CPU/RAM Memory ของ Container
  - **Implementation Action Items**:
    - [ ] สมัครบัญชี Grafana Cloud Free Tier & รับ OTLP Endpoint, Instance ID และ API Tokens
    - [ ] เพิ่ม `opentelemetry-distro` และ `opentelemetry-exporter-otlp` ลงใน [`requirements.txt`](file:///requirements.txt)
    - [ ] อัปเดต [`project/main.py`](file:///project/main.py) เพื่อติดตั้ง OpenTelemetry FastApiInstrumentor & Logging Handlers
    - [ ] ปรับปรุง [`Dockerfile`](file:///Dockerfile) / [`Dockerfile.hf`](file:///Dockerfile.hf) เพื่อส่ง Environment Variables สำหรับ Grafana OTLP Credentials
    - [ ] สร้าง Grafana Dashboard แบบกำหนดเองสำหรับแสดงผล Ollama Tokens/sec, RAG Latency, และ Uptime Metrics



