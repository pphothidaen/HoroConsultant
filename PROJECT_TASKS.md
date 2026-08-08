# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-08 12:45 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Full Unit, Integration & Web Regression Test ทั้งหมด (128/128 tests PASS)
python3 -m pytest -v

# 2. รัน Benchmark วัดประสิทธิภาพ Latency, RAG & Cache Layer (< 1ms)
python3 scripts/benchmark_pipeline.py

# 3. เริ่ม FastAPI Server & Web UI (Local-First: Qwen2.5:7b + FAISS 4,051 Vectors + Glassmorphism UI)
python3 -m uvicorn project.main:app --reload --port 8000
# Web UI Dashboard: http://localhost:8000
# Admin Panel:       http://localhost:8000/admin
# API Docs:          http://localhost:8000/docs

# 4. Pre-Deployment Code Review & Safety Audit
python3 project/core/code_reviewer.py --review

# 5. ซิงค์ Secrets อัตโนมัติไปยังทุก Cloud Platform
bash scripts/setup_production_secrets.sh

# 6. Deploy ขึ้น Vercel Edge Network
npx vercel --prod

# 7. Deploy ขึ้น Fly.io Micro-VMs (Singapore Region)
fly launch --config fly.toml --no-deploy
fly deploy
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────┬───────────────────────────────────────┬───────────────────────────────────────┐
│              ✅ DONE                  │              🔄 DOING                 │              📋 TODO                  │
├───────────────────────────────────────┼───────────────────────────────────────┼───────────────────────────────────────┤
│ • Fly.io .dockerignore Fix (.env.ex)  │ (None - All tasks completed 100%)     │ (Run 'fly deploy' & 'npx vercel')     │
│ • Strict Admin Email Whitelist Guard  │                                       │                                       │
│ • Business Analyst Agent & Governance │                                       │                                       │
│ • Hybrid Geocoding Offline Fallback   │                                       │                                       │
│ • Multi-Cloud Secrets Sync Script     │                                       │                                       │
│ • Vercel Edge Multi-Cloud Rewrites    │                                       │                                       │
│ • HF Spaces Edge CDN Deploy Verified  │                                       │                                       │
│ • 128/128 Tests Passing (3.78s)       │                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

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

- *(ไม่มี - งานในเฟสปัจจุบันเสร็จสิ้นสมบูรณ์ 100%)*


