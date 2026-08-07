# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-07 20:53 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Full Unit, Integration & Web Regression Test ทั้งหมด (93 tests PASS)
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
│ • Cross-Platform AI Agent Framework   │ • Kaggle GPU Model Training Push      │ • 5-Branch SVG Visualizer Charts      │
│ • 5-Branch Domain Master Agents       │ • Multi-Branch Synthesis Analysis     │ • Qi Zheng Si Yu Ephemeris Engine     │
│ • Peer Debate Engine & HITL Auto-Route│                                       │ • Post-Train GGUF Fusion & Ollama Reg │
│ • High-Perf Runtime Cache (< 1ms)     │                                       │                                       │
│ • Continuous Vault Growth (4,051 vec) │                                       │                                       │
│ • 5-Branch Pure Python Core Engines   │                                       │                                       │
│ • Pure ASCII Logging & Rulebook       │                                       │                                       │
│ • 93/93 Full Regression Test Suite    │                                       │                                       │
│ • Shared MCP Server (.mcp.json)       │                                       │                                       │
│ • Custom Slash Commands (/test,/review│                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

- [x] **Continuous Knowledge Vault Growth & Dataset Expansion (`project/rag/obsidian_vault/`, `project/rag/ingest_vault.py`)**
  - สกัดไฟล์คัมภีร์โบราณ 5 สายวิชา (`zi_wei_dou_shu_classics.md`, `qi_men_dun_jia_classics.md`, `da_liu_ren_classics.md`, `iching_liu_yao_classics.md`, `xuan_kong_feng_shui_classics.md`, `ze_ji_classics.md`)
  - สร้าง FAISS RAG Vector Store ขยายเป็น **4,051 vectors** และสกัดชุด ShareGPT Dataset (`train.jsonl`, `valid.jsonl`)
- [x] **5-Branch Metaphysics Pure Python Calculation Engines (`project/core/`, `project/tests/test_5_branch_engines.py`)**
  - **Zi Wei Dou Shu (`zi_wei_engine.py`)**: 12 ภพ, 14 ดาวหลัก, 五行局, 四化 (化祿, 化權, 化科, 化忌)
  - **Qi Men Dun Jia (`qi_men_engine.py`)**: 24 ฤดูกาล, 陰陽 18 局, ผัง 4 ชั้น (地盤, 天盤, 門盤, 神盤)
  - **Da Liu Ren (`liu_ren_engine.py`)**: 月將加時, 四課, 三傳 (初傳, 中傳, 末傳), 十二天將
  - **I Ching & Liu Yao (`iching_engine.py`)**: 64 卦, 納甲地支, 六親, 六神 (青龍, 朱雀 ฯลฯ)
  - **Xuan Kong Flying Stars (`xuan_kong_engine.py`)**: 24 山 องศาเข็มทิศ, 九運 (2024-2043) 運盤, 山星, 向星 (順飛/逆飛)
  - **Date Selection (`ze_ji_engine.py`)**: 建除十二神, 歲破/月破, 評分 1-5 ดาว
- [x] **5-Branch Metaphysics Domain Master Agents, Peer Debate Engine & Orchestrator HITL Router (`.agents/agents/`, `project/core/multi_agent_debate.py`)**
- [x] **High-Performance Runtime Caching Layer & Automated Benchmark Tool (`project/core/cache_manager.py`, `scripts/benchmark_pipeline.py`)**
- [x] **MCP Server & REST API Endpoints Expansion (`project/mcp_server.py`, `project/main.py`)**
  - เพิ่ม MCP tools (`ziwei_calculate`, `qimen_calculate`, `liuren_calculate`, `iching_calculate`, `xuankong_calculate`, `zeji_calculate`)
  - เพิ่ม REST endpoints `/api/v1/ziwei/calculate`, `/api/v1/qimen/calculate`, `/api/v1/liuren/calculate`, `/api/v1/iching/calculate`, `/api/v1/xuankong/calculate`, `/api/v1/zeji/calculate`
- [x] **Glassmorphism Web UI Control Integration (`project/static/index.html`, `project/static/app.js`)**
- [x] **Pre-Deployment Code Reviewer & Safety Auditor (`project/core/code_reviewer.py`)**
  - **Pass Rate**: 93/93 Pytest Unit & Integration Tests PASS (100% success rate), สถานะ `READY_FOR_PROD`

---

### 🔄 DOING (กำลังดำเนินการ / ระยะถัดไป)

- [ ] **Kaggle GPU Fine-Tuning Execution (`scripts/kaggle_notebook_manager.py`)**
  - Push ชุดข้อมูล 5-branch dataset ล่าสุด (`project/rag/datasets/train.jsonl`) ขึ้น Kaggle GPU fine-tuning pipeline
- [ ] **Multi-Branch Composite Synthesis Agent (`project/core/multi_agent_debate.py`)**
  - เชื่อมโยงผลคำนวณ BaZi + Zi Wei + Qi Men เพื่อวิเคราะห์ดวงชะตาและยุทธศาสตร์แบบบูรณาการ

---

### 📋 TODO (งานระยะถัดไป / Feature Backlog)

- [ ] **5-Branch SVG Vector Chart Generators (`project/core/svg_generator.py`)**
  - สร้างไฟล์ SVG แบบ Vector Interactive สำหรับ Zi Wei 12 Palaces Chart, Qi Men 4-Plate Grid และ Xuan Kong 9-Grid Star Map
- [ ] **Qi Zheng Si Yu Ephemeris Calculation (`project/core/swiss_ephemeris.py`)**
  - คำนวณตำแหน่งจริงของ 7 ดาวเคราะห์ (七政) และ 4 ดาวเงา (四餘) พร้อม 28 กลุ่มดาวนักษัตร
- [ ] **GGUF Post-Train Model Fusion & Local Ollama Registration (`scripts/post_train_fuse.py`)**
  - รวม LoRA adapter จาก Kaggle แปลงเป็น GGUF 4-bit / 8-bit และลงทะเบียนโมเดลใน Ollama / thClaws Harness
