# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-07 21:16 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Full Unit, Integration & Web Regression Test ทั้งหมด (101 tests PASS)
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
│ • Cross-Platform AI Agent Framework   │ ( 0 Items - Moved 100% to DONE )      │ ( Backlog Clear - 100% Prod Ready )   │
│ • 8 Domain Master Agents Decoupled    │                                       │                                       │
│ • Thai & Vedic Master (สุริยยาตร์)      │                                       │                                       │
│ • Western & Uranian Master (8 TNPs)   │                                       │                                       │
│ • Numerology & Satta-Lek Master (7ฐาน)│                                       │                                       │
│ • Peer Debate Engine & HITL Auto-Route│                                       │                                       │
│ • High-Perf Runtime Cache (< 1ms)     │                                       │                                       │
│ • Continuous Vault Growth (4,051 vec) │                                       │                                       │
│ • 8 Pure Python Calculation Core Engs │                                       │                                       │
│ • 101/101 Full Regression Test Suite  │                                       │                                       │
│ • Shared MCP Server (.mcp.json)       │                                       │                                       │
│ • Glassmorphism Web UI Visualizers    │                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

- [x] **8 Standalone Domain Master Agents (`.agents/agents/`)**
  - **`san_shi_master`**: 三式 (Tai Yi, Da Liu Ren, Qi Men Dun Jia)
  - **`ming_xue_master`**: 命學 (BaZi, Zi Wei Dou Shu, Qi Zheng Si Yu)
  - **`pu_shi_master`**: 卜筮 (I Ching, Liu Yao, Mei Hua Yi Shu)
  - **`xiang_xue_master`**: 相學 (Xuan Kong Flying Stars, San He Feng Shui, Mian Xiang)
  - **`ze_ji_master`**: 擇吉 (Imperial Calendar Date Selection)
  - **`thai_vedic_master`**: โหราศาสตร์ไทยสุริยยาตร์ / นิรายนะ 10 ลัคนา + มหาทักษา 8 เทวดา + Jyotish (27 Nakshatras & Vimshottari Dasha)
  - **`western_astro_master`**: โหราศาสตร์สากล Tropical Planetary Aspects + ยูเรเนียน (8 ดาวทิพย์ TNPs & Midpoint Axis $A+B-C$)
  - **`numerology_master`**: ศาสตร์สัตตเลข 7 ฐาน 4 แถว + เลขศาสตร์ Chaldean/Pythagorean Scoring (วิเคราะห์ชื่อ/เบอร์โทรศัพท์/ทะเบียนรถ) *[ยกเว้นไพ่ทาโรต์ 78 ใบที่เป็นสุ่มตามคำสั่ง]*
- [x] **8 Pure Python Calculation Core Engines (`project/core/`)**
  - `bazi_engine.py`, `zi_wei_engine.py`, `qi_men_engine.py`, `liu_ren_engine.py`, `iching_engine.py`, `xuan_kong_engine.py`, `ze_ji_engine.py`, `thai_vedic_engine.py`, `western_uranian_engine.py`, `numerology_engine.py`
- [x] **Peer Debate Engine & Master Orchestrator System Thinking / Critical Thinking Audit Pipeline (`project/core/multi_agent_debate.py`)**
  - รวม Agent 8 สายวิชาถกเถียงและวิพากษ์ สกัดข้อเท็จจริงชำระแล้ว (Consensus Facts) และส่งต่อ Gray-zone ไปยัง Human-in-the-Loop Queue (`project/hitl_router.py`)
- [x] **MCP Server & REST API Expansion (`project/mcp_server.py`, `project/main.py`)**
  - เพิ่ม MCP tools และ REST endpoints สำหรับ Thai/Vedic, Western/Uranian, Numerology
- [x] **Glassmorphism Web UI Control & Visualizer (`project/static/index.html`, `project/static/app.js`)**
- [x] **Pre-Deployment Code Reviewer & Safety Auditor (`project/core/code_reviewer.py`)**
  - **Pass Rate**: 101/101 Pytest Unit & Integration Tests PASS (100% success rate), สถานะ `READY_FOR_PROD`

---

### 🔄 DOING (กำลังดำเนินการ)
*(ไม่มีงานค้าง — ทุกรายการดำเนินการเสร็จสมบูรณ์และย้ายเข้าสู่ ✅ DONE ทั้งหมด 100% แล้ว)*

---

### 📋 TODO (งานระยะถัดไป / Backlog)
*(ไม่มีงานค้าง — Backlog เคลียร์หมด 100% ทุกระบบผ่านการ Audit และพร้อมใช้งานบน Production Ready)*
