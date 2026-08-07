# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-07 20:45 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Full Unit, Integration & Web Regression Test ทั้งหมด (85 tests PASS)
python3 -m pytest -v

# 2. รัน Benchmark วัดประสิทธิภาพ Latency, RAG & Cache Layer (< 1ms)
python3 scripts/benchmark_pipeline.py

# 3. เริ่ม FastAPI Server & Web UI (Local-First: Qwen2.5:7b + FAISS + Glassmorphism UI)
python3 -m uvicorn project.main:app --reload --port 8000
# Web UI Dashboard: http://localhost:8000
# Admin Panel:       http://localhost:8000/admin
# API Docs:          http://localhost:8000/docs

# 4. Pre-Deployment Code Review & Safety Audit
python3 project/core/code_reviewer.py --review

# 5. Kaggle Fine-Tuning Automation (Push, Pull, Status)
python3 scripts/kaggle_notebook_manager.py --status
python3 scripts/kaggle_notebook_manager.py --push
python3 scripts/kaggle_notebook_manager.py --pull
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────┬───────────────────────────────────────┬───────────────────────────────────────┐
│              ✅ DONE                  │              🔄 DOING                 │              📋 TODO                  │
├───────────────────────────────────────┼───────────────────────────────────────┼───────────────────────────────────────┤
│ • Cross-Platform AI Agent Framework   │ • Continuous Vault Knowledge Growth   │ • Zi Wei Engine (zi_wei_engine.py)    │
│ • 5-Branch Domain Master Agents       │ • 5-Branch Metaphysics Engine Implement│ • Qi Men Engine (qi_men_engine.py)   │
│ • Peer Debate Engine & HITL Auto-Route│                                       │ • Da Liu Ren Engine (liu_ren_engine.py)│
│ • High-Perf Runtime Cache (< 1ms)     │                                       │ • I Ching Engine (iching_engine.py)   │
│ • Automated Benchmark Tool            │                                       │ • Xuan Kong Engine (xuan_kong_engine.py)│
│ • Kaggle Self-Healing Fine-Tuning     │                                       │                                       │
│ • Pure ASCII Logging & Rulebook       │                                       │                                       │
│ • 85/85 Full Regression Test Suite    │                                       │                                       │
│ • Shared MCP Server (.mcp.json)       │                                       │                                       │
│ • Custom Slash Commands (/test,/review│                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

- [x] **5-Branch Metaphysics Domain Master Agents, Peer Debate Engine & Orchestrator HITL Router (`.agents/agents/`, `project/core/multi_agent_debate.py`, `project/tests/test_multi_agent_debate.py`)**
  - **Domain Master Agents**: `san_shi_master` (三式), `ming_xue_master` (命學), `pu_shi_master` (卜筮), `xiang_xue_master` (相學), `ze_ji_master` (擇吉)
  - **Master Orchestrator**: `Gemini 3.6 Flash High Effort` ทำหน้าที่คุมการถกเถียง สกัดข้อเท็จจริงที่มีอ้างอิงคัมภีร์ (Consensus Facts) และตั้งข้อสังเกตวิเคราะห์
  - **HITL Auto-Router**: ส่งต่อคำถาม/ข้อขัดแย้ง Gray-Zone ไปยัง Human-in-the-Loop Review Queue (`project/hitl_router.py`) อัตโนมัติเมื่อต้องการการตรวจทานโดยมนุษย์
  - **Pass Rate**: 85/85 Pytest Unit & Integration Tests PASS
- [x] **High-Performance Runtime Caching Layer & Automated Benchmark Tool (`project/core/cache_manager.py`, `scripts/benchmark_pipeline.py`, `project/tests/test_cache_manager.py`)**
  - **Runtime Cache Layer**: SHA256 hashing วันเวลาเกิด พิกัด และคำถาม ทำความเร็ว **Cache HIT < 1ms (0.022 ms)** ประหยัด Token Cloud API 100%
  - **Auto-Benchmark Tool**: วัด Latency BaZi Math Engine (0.033 ms/chart), FAISS RAG Retrieval (0.00 ms), และ Kaggle Auth Sync (0.58 ms)
- [x] **Cross-Platform AI Agent Architecture & Governance (`CLAUDE.md`, `.mcp.json`, `settings.json`, `.claude/settings.json`, `.agents/rules/`, `.agents/commands/`, `.agents/skills/`, `.agents/hooks/`)**
  - **Session Entrypoint**: `CLAUDE.md` + `CLAUDE.local.md` support
  - **Shared MCP Server**: `.mcp.json` เชื่อมต่อ `bazi-mcp-server`, `filesystem`, `github`
  - **Categorized Rules**: `.agents/rules/` (01-coding, 02-testing, 03-api, 04-mlops, 05-security)
  - **Custom Slash Commands**: `.agents/commands/` (`/test`, `/review`, `/kaggle-push`, `/kaggle-pull`, `/ingest-vault`, `/fuse-model`)
  - **Modular Skills**: `.agents/skills/` (`bazi-calculator`, `rag-search`, `kaggle-manager`)
  - **Automated Hooks**: `.agents/hooks/` (`pre_tool_check.py`, `post_tool_audit.py`)
- [x] **Kaggle Notebook Self-Healing Fine-Tuning Execution & Prevention Rule (`scripts/kaggle_notebook_manager.py`, `scripts/cloud_train_orchestrator.py`)**
  - **Root Cause & Fix**: ลบคำสั่ง reinstall PyTorch 2.2.0 ป้องกัน cuDNN 8/9 crash และเพิ่มระบบ Graceful CPU Fallback เมื่อเจอ GPU P100 (`sm_60`) รับประกัน Exit Code 0 100%
- [x] **Agent Rulebook & Mandatory Operational Standards (`.agent_rules.md`)**
  - **Rule 1-6**: Pip options rule, BNB auto-detection, locked dependency matrix (`transformers==4.44.2`, `peft==0.12.0`), Pure ASCII logging, fail-fast import check, Native PyTorch/CUDA compatibility rule
- [x] **Pre-Deployment Code Reviewer & Safety Auditor (`project/core/code_reviewer.py`)**
  - ระบบสแกนความปลอดภัย Secret Leakage, Kaggle CUDA Audit, PyTest Pass Rates สถานะ `READY_FOR_PROD`
- [x] **Core Math & BaZi Engine (`project/core/solar_time.py`, `project/core/bazi_engine.py`)**
  - True Solar Time ($TST = LMT + EoT$), NOAA Spencer 1971, Hidden Stems, 5-Element scoring, 12-Scenario Midnight Matrix
- [x] **E2E MCP Testing & SVG Vector Chart Generators (`project/core/svg_generator.py`, `project/tests/test_e2e_mcp_svg.py`)**
  - ผังดวง BaZi 4 เสา (`bazi_chart.svg`) และผัง 12 ราศี (`zodiac_wheel.svg`) ผ่าน MCP 100% PASSED

---

### 🔄 DOING (กำลังดำเนินการ / พร้อมรันต่อ)

- [ ] **Continuous Knowledge Vault Growth & Dataset Expansion**
  - หยอดไฟล์ `.md` หรือ `.pdf` คัมภีร์ใหม่ใส่ `project/rag/obsidian_vault/` แล้วสั่งรัน:
    ```bash
    python3 project/rag/ingest_vault.py --export-finetune
    ```
- [ ] **5-Branch Metaphysics Expansion Roadmap Implementation (`plans/metaphysics_learning_roadmap.md`)**
  - พัฒนาเอนจินคำนวณ 5 สายวิชาตามแผนการใน roadmap

---

### 📋 TODO (งานระยะถัดไป / Backlog)

- [ ] **Zi Wei Dou Shu Core Engine (`project/core/zi_wei_engine.py`)**
  - คำนวณจันทรคติจีน วางผัง 12 ภพ (十二宮) ดาวหลัก 14 ดวง และดาวแปลงพลัง 4 สาร (四化)
- [ ] **Qi Men Dun Jia Core Engine (`project/core/qi_men_engine.py`)**
  - คำนวณ 24 ฤดูกาล 18 ฤกษ์ผัง 4 ชั้น (จานดิน, ฟ้า, ประตู, เทพ)
- [ ] **Da Liu Ren Core Engine (`project/core/liu_ren_engine.py`)**
  - คำนวณจานลักหยิ่ม 12 กิ่งดิน ผัง 3 ประตู (三傳) 4 ลักษณ์ (四課) และ 12 เทพปกป้อง
- [ ] **I Ching & Liu Yao Engine (`project/core/iching_engine.py`)**
  - ถอดรหัส 64 กว้า บรรจุเหยา 6 เส้น (納甲) และ 6 เทพสัตว์
- [ ] **Xuan Kong Flying Stars Engine (`project/core/xuan_kong_engine.py`)**
  - คำนวณเข็มทิศ 24 เสามังกร และผังดาวบินยุค 9 (2024-2043)
