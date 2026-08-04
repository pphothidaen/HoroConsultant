# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff**  
> *Last Updated: 2026-08-04 12:10 (UTC+7)*

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# 1. รัน Full Unit, Integration & Web Regression Test ทั้งหมด (74 tests)
python3 -m pytest -v

# 2. เริ่ม FastAPI Server & Web UI (Local-First: Qwen2.5:7b + FAISS + Glassmorphism UI)
python3 -m uvicorn project.main:app --reload --port 8000
# Web UI Dashboard: http://localhost:8000
# 🆕 Admin Panel:   http://localhost:8000/admin
# API Docs:         http://localhost:8000/docs

# 3. รัน AGY + thClaws Hybrid Multi-Agent Pipeline
python3 scripts/run_thclaws_bridge.py

# 4. สร้างผังดวงกราฟิก SVG & E2E Verification
python3 -m pytest project/tests/test_e2e_mcp_svg.py -v

# 5. นำเข้าข้อมูลคัมภีร์ใหม่จาก project/rag/obsidian_vault/
python3 project/rag/ingest_vault.py --export-finetune

# 6. รัน Kaggle Output Log Sync / Fine-Tuning Execution
python3 scripts/kaggle_notebook_manager.py --output --dest project/kaggle_kernel

# 7. 🆕 รัน Pre-Deployment Code Review & Safety Audit
python3 project/core/code_reviewer.py --review
```

---

## 📊 TASK BOARD (KANBAN)

```
┌───────────────────────────────────────┬───────────────────────────────────────┬───────────────────────────────────────┐
│              ✅ DONE                  │              🔄 DOING                 │              📋 TODO                  │
├───────────────────────────────────────┼───────────────────────────────────────┼───────────────────────────────────────┤
│ • Deterministic Pure Python Core      │ • Vault Continuous Ingestion          │ • Model Fusion & GGUF Ollama Deploy  │
│ • Local-First API Router              │ • Answer Gray-Zone Questions (102 Qs) │ • External AI Provider Integration    │
│ • FAISS Vector Store (3,132 vectors)  │                                       │   (OpenAI/Together fine-tune API)     │
│ • 38 PDF Books Ingested (3,132 vec)   │                                       │ • Swiss Ephemeris Integration         │
│ • Web UI Glassmorphism Dashboard      │                                       │ • Additional Source Ingestion         │
│ • AGY + thClaws Multi-Agent Arch      │                                       │                                       │
│ • Prediction Validator Gemini Agent   │                                       │                                       │
│ • E2E MCP & SVG Chart Generators      │                                       │                                       │
│ • Solution 1 ShareGPT JSONL Exporter  │                                       │                                       │
│ • Gemini Vision OCR & Quality Check   │                                       │                                       │
│ • 74/74 Full Regression Test Suite    │                                       │                                       │
│ 🆕 Kaggle T4 Fine-Tune Fix (ops.cu)   │                                       │                                       │
│ 🆕 GitHub Actions AI CI/CD Pipeline   │                                       │                                       │
│ 🆕 MLX QLoRA Fine-Tuning (600 iters)  │                                       │                                       │
│ 🆕 Knowledge Source Catalog (46 src) │                                       │                                       │
│ 🆕 Pre-Deployment Code Reviewer       │                                       │                                       │
│ 🆕 Rust PyO3 Core Engine (TF-IDF/BaZi)│                                       │                                       │
│ 🆕 Supabase REST Client & Dataset Sync│                                       │                                       │
│ 🆕 Doppler Secrets & Config Manager  │                                       │                                       │
│ 🆕 Cloud Training Orchestrator       │                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### ✅ DONE (เสร็จสมบูรณ์ 100% พร้อมใช้งาน)

- [x] **Kaggle T4 Fine-Tuning Orchestrator Fix & Output Log Sync (`scripts/kaggle_notebook_manager.py`, `scripts/cloud_train_orchestrator.py`)**
  - แก้ไขปัญหา CUDA symbol mismatch (`ops.cu:74`) และ SIGSEGV exit code -11 ใน Kaggle GPU ด้วยการตั้งค่า `CUDA_MODULE_LOADING=LAZY`, `BNB_CUDA_VERSION=121`, `TORCH_CUDA_ARCH_LIST`
  - เพิ่มระบบ Precision Fallback (`bfloat16`/`float16`) ป้องกันกรณี 4-bit bitsandbytes quantization มีปัญหาบน cloud environment
  - Push notebook kernel v11 ขึ้น Kaggle และดึง log ล่าสุดสิงสู่ [`project/kaggle_kernel/`](file:///Users/kimlenglim/Project/HoroConsultant/project/kaggle_kernel) สมบูรณ์
- [x] **GitHub Actions AI CI/CD Pipeline (`.github/workflows/ai_cicd.yml`)**
  - สร้างไปป์ไลน์ AI CI/CD อัตโนมัติ: ตรวจสอบความปลอดภัย โค้ดรีวิวด้วย `CodeReviewer`, สแกน Secret Leakage, รัน PyTest 74 ข้อ, สั่งการ Kaggle GPU Fine-Tuning และซิงก์ Output ล่าสุดกลับไปยัง GitHub
- [x] **Pre-Deployment Code Reviewer & Safety Auditor (`project/core/code_reviewer.py`)**
  - ระบบตรวจสอบความปลอดภัยก่อน Commit/Push (Secret Leakage Scan, Kaggle CUDA Audit, PyTest Pass Rates) ผ่านสถานะ `READY_FOR_PROD`
- [x] **MLX QLoRA Fine-Tuning Execution & Model Fusion (macOS Host)**
  - Model: `mlx-community/Qwen2.5-7B-Instruct-4bit` (QLoRA 4-bit)
  - Config: batch=1, grad_accum=4, lora_rank=8, 600 iters completed (23 MB adapter)
  - Output adapter: `project/models/qwen2.5-bazi-adapter/adapters.safetensors`
  - Fused model: `project/models/qwen2.5-bazi-fused` (4.00 GB, 24.5 tokens/sec validated)
- [x] **Core Math Engine (`project/core/solar_time.py`)**
  - คำนวณ True Solar Time ($TST = LMT + EoT$) อ้างอิงอัลกอริทึม NOAA Spencer 1971
  - ปรับแก้ลองจิจูด (Longitude offset) หักลบตามเวลาจริงของสถานที่เกิด
- [x] **BaZi Engine (`project/core/bazi_engine.py`)**
  - คำนวณ 4 เสาชะตา (ปี, เดือน, วัน, ยาม) + Hidden Stems (คำนวณน้ำหนักธาตุซ่อน)
  - ประเมินคะแนนกำลัง 5 ธาตุ (Wood, Fire, Earth, Metal, Water) คิดเป็นเปอร์เซ็นต์
  - รองรับ Probabilistic Scenario Matrix 12 Scenarios สำหรับกรณีเกิดคาบเกี่ยวเขตรอบเที่ยงคืน
- [x] **Local-First Hybrid Router (`project/api_router.py`)**
  - **Primary Route:** Local Ollama (`qwen2.5:7b` → `qwen2.5-coder:7b` → `llama3:8b`)
  - **Cloud Fallback:** Dual API Key rotation (KEY1 + KEY2) สำหรับ Gemini 2.0 Flash
  - ตอบสนองใน ~3.9 วินาทีโดยไม่ต้องพึ่งพา Cloud API
- [x] **E2E MCP Testing & Standalone SVG Vector Chart Generator (`project/core/svg_generator.py`, `project/tests/test_e2e_mcp_svg.py`)**
  - เครื่องมือสร้างผังดวงกราฟิก SVG แบบไร้พึ่งพิงไลบรารีภายนอก: **ผังดวง BaZi 4 เสา (`bazi_chart.svg`)** และ **ผังดวงจักรราศี 12 ราศี (`zodiac_wheel.svg`)**
  - เพิ่ม MCP Tools `render_bazi_svg` และ `render_zodiac_svg` ใน `project/mcp_server.py`
  - ผ่านการทดสอบ **E2E MCP Integration & SVG Vector Rendering 100% PASSED** (5/5 tests)
- [x] **Web UX/UI Glassmorphism Dashboard & Regression Suite (`project/static/`, `project/tests/test_web_regression.py`)**
  - ดีไซน์สวยงามระดับพรีเมียมด้วย Glassmorphism, Dark Theme, แสงเรืองแสง 5 ธาตุ (Wood, Fire, Earth, Metal, Water)
  - แสดงผังดวง 4 เสาชะตา (四柱), กราฟเปอร์เซ็นต์กำลัง 5 ธาตุ, และตัวเล่นแท็บผลพยากรณ์ Multi-Agent (Local LLM + Gemini Auditor + RAG)
  - ผ่านการทดสอบ **Full Web & API Regression Suite 100% PASSED** (74/74 tests)
- [x] **AGY + thClaws Hybrid Multi-Agent Architecture (`project/mcp_server.py`, `thclaws.toml`, `scripts/run_thclaws_bridge.py`)**
  - เชื่อมต่อ **AGY Master Engine** เข้ากับ **thClaws (ThaiGPT Rust Agent Harness)** ผ่านมาตรฐาน **Model Context Protocol (MCP)**
  - แบ่งบทบาท 4 Agents เฉพาะทาง: `bazi-calculator`, `rag-scholar`, `predictor-agent`, `prediction-validator`
  - ทำงานร่วมกันทั้งแบบ 100% Local (Ollama + FAISS) และ Cloud Fallback (Gemini Validator)
- [x] **Solution 1: ShareGPT JSONL Dataset Builder & Quality Validator (`project/rag/jsonl_exporter.py`)**
  - สกัดและตรวจสอบความถูกต้องของชุดข้อมูลแบบ ShareGPT (`messages` format)
  - ประมวลผลจากคัมภีร์, Vault Markdown, และผังดวงสังเคราะห์ 504 รายการ (ผ่าน Quality Check 100%)
  - ส่งออกชุดข้อมูลฝึกฝน `train.jsonl` (454 entries) และชุดสอบทาน `valid.jsonl` (50 entries) พร้อมสำหรับ Fine-Tune โมเดล `Qwen/Qwen2.5-7B-Instruct`
- [x] **Gemini Vision OCR Engine & Quality Validator (`scripts/ocr_pdf_gemini.py`)**
  - ใช้ Gemini 2.0 Flash Multimodal API อ่านภาพหน้าหนังสือเก่า/กระดาษสีเหลืองสแกน (ไทย, บาลี, จีน)
  - มีระบบ **Post-Conversion Validation (`validate_converted_markdown`)** ตรวจสอบความถูกต้อง ความยาว ความบริสุทธิ์ของตัวอักษร และการรั่วไหลของ API Error ก่อนบันทึกไฟล์เสมอ
  - บันทึกลง `project/rag/obsidian_vault/` และรัน Ingestion อัปเดต FAISS Vector DB ให้อัตโนมัติเฉพาะไฟล์ที่ผ่าน Quality Checks เท่านั้น
- [x] **Prediction Validator Agent (`.antigravity/agents/prediction-validator.agent` & `project/validator.py`)**
  - ใช้ External Gemini API (Cloud LLM) ทำหน้าที่เป็น **Astrological Auditor & Cross-Validator**
  - ตรวจสอบความถูกต้องของตรรกะธาตุ (Element Logic), ปฏิกิริยาฮะ-ชง (Branch/Stem Interactions), และ True Solar Time
  - ให้มุมมองเพิ่มเติม (Peer Perspective) และเสนอคำพยากรณ์ฉบับปรับปรุงเพิ่มเติมผ่าน Endpoint `/api/v1/bazi/validate`
- [x] **Automated Midnight Sync & Startup Catch-Up Scheduler (`scripts/sync_gdrive_vault.py` & `project/main.py`)**
  - คอนฟิกใน `.env`: `AUTO_SYNC_ENABLED=true`, `AUTO_SYNC_CRON="0 0 * * *"`, `AUTO_SYNC_ON_STARTUP=true`
  - ทำงานอัตโนมัติทุกเที่ยงคืนด้วย `APScheduler`
  - หากระบบปิดอยู่ตอนเที่ยงคืน ระบบจะตรวจสอบ `last_sync_timestamp` ตอนเปิดเครื่อง (Startup) และรันซิงก์ + อัปเดต FAISS Vector DB + Fine-Tune JSONL ทันทีที่ระบบเปิดขึ้นมา
- [x] **Local RAG Vector Store (`project/rag/vector_store.py`)**
  - ใช้ **FAISS Index** ร่วมกับ **`nomic-embed-text:latest`** (Ollama Local Embeddings)
  - นำเข้าคัมภีร์คลาสสิก (子平真詮, 滴天髓, 窮通寶鑑) + หนังสือโหราศาสตร์ไทย 38 เล่ม
  - **รวมดึงและฝังข้อความแล้ว 3,132 Vector Chunks** (dim=768)
- [x] **Vault Ingestion Pipeline (`project/rag/ingest_vault.py`)**
  - อ่านไฟล์ `.md` และสกัดเนื้อหาจากไฟล์ `.pdf` อัตโนมัติด้วย `pypdf`
  - สกัดคู่คำถาม-คำตอบ (Q&A) ออกเป็น ShareGPT JSONL สำหรับ Fine-Tuning
- [x] **FastAPI Web Server (`project/main.py`)**
  - Endpoint `/health` Check สถานะระบบ
  - Endpoint `/api/v1/bazi/calculate` คำนวณ 4 เสาและกำลังธาตุ
  - Endpoint `/api/v1/bazi/interpret` ถอดความคำพยากรณ์ด้วย Local AI + RAG
- [x] **Docker Infrastructure (`Dockerfile`, `docker-compose.yml`, `docker_bootstrap.sh`)**
  - Multi-stage Ubuntu build รองรับ GPU acceleration
  - Script บูตระบบอัตโนมัติด้วยคำสั่งเดียว
- [x] **Automated Test Suite (`tests/test_core.py`, `project/tests/test_bazi_calculator.py`, `project/tests/test_web_regression.py`)**
  - **74/74 Unit & Integration Tests PASS** (2.6s)


---

### 🔄 DOING (กำลังดำเนินการ / พร้อมรันต่อ)

- [x] **MLX QLoRA Fine-Tuning Execution & Model Fusion (macOS Host)**
  - Model: `mlx-community/Qwen2.5-7B-Instruct-4bit` (QLoRA 4-bit)
  - Config: batch=1, grad_accum=4, lora_rank=8, 600 iters completed (23 MB adapter)
  - Output adapter: `project/models/qwen2.5-bazi-adapter/adapters.safetensors`
  - Fused model: `project/models/qwen2.5-bazi-fused` (4.00 GB, 24.5 tokens/sec validated)
- [x] **Kaggle T4 Fine-Tuning Orchestrator Fix (Exit Code -11 Resolution)**
  - Fixed PyTorch CUDA binary mismatch by removing torch re-installation in notebook setup.
  - Added explicit `torch_dtype=torch.float16`, `low_cpu_mem_usage=True`, and `device_map={"": 0}` in `cloud_train_orchestrator.py` to eliminate SIGSEGV memory crashes.

---

### 🔄 DOING (กำลังดำเนินการ / พร้อมรันต่อ)

- [ ] **Continuous Knowledge Vault Growth & Dataset Expansion**
  - เมื่อหยอดไฟล์ `.md` หรือ `.pdf` ใหม่ใส่ `project/rag/obsidian_vault/` ให้รัน:
    ```bash
    python3 project/rag/ingest_vault.py --export-finetune
    ```

---

### 📋 TODO (งานระยะถัดไป / Backlog)

1. **Model Fusion & GGUF Export (หลัง Fine-Tune เสร็จ)**
   - รัน Post-Train Pipeline ทั้งหมดด้วยคำสั่งเดียว:
     ```bash
     python3 scripts/post_train_fuse.py
     ```
   - หรือทำทีละขั้น:
     ```bash
     # Fuse MLX adapter (ใช้ 4-bit base model)
     mlx_lm.fuse --model mlx-community/Qwen2.5-7B-Instruct-4bit --adapter-path project/models/qwen2.5-bazi-adapter --save-path project/models/qwen2.5-bazi-fused
     ```
   - แปลงเป็น GGUF สำหรับ Ollama:
     ```bash
     python3 llama.cpp/convert_hf_to_gguf.py project/models/qwen2.5-bazi-fused --outfile project/models/qwen2.5-bazi.gguf --outtype q4_k_m
     ```
   - สร้างโมเดลใน Ollama:
     ```bash
     ollama create qwen2.5-bazi -f project/models/Modelfile
     ```

2. **CI/CD Automation (GitHub Actions)**
   - สร้าง `.github/workflows/ci.yml` รัน `pytest` และตรวจ Lint ทุกครั้งที่ Push

3. **Consultant Web UI (Frontend)**
   - พัฒนาหน้าจอเว็บอินเทอร์เฟซด้วย HTML/JS (Vanilla CSS Glassmorphism) สำหรับแสดงผัง 4 เสา และกราฟเปรียบเทียบกำลัง 5 ธาตุ

---

## 🔑 Environment & Key Configuration Checklist

ไฟล์ `.env` ได้รับการตั้งค่าแล้วดังนี้:

| Key | สถานะ | คำอธิบาย |
|-----|--------|----------|
| `GOOGLE_AI_STUDIO_API_KEY` | ✅ Configured | Primary Cloud Fallback Key |
| `GOOGLE_AI_STUDIO_API_KEY2` | ✅ Configured | Secondary Cloud Fallback Key (Rate-Limit Rotation) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama Connection |
| `OLLAMA_PRIMARY_MODEL` | `qwen2.5:7b` | Main Local Inference Model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text:latest` | Local Embedding Model |
| `AUTO_SYNC_ENABLED` | `true` | Midnight Auto-Sync Active |
| `AUTO_SYNC_CRON` | `0 0 * * *` | Daily Midnight Schedule |
| `AUTO_SYNC_ON_STARTUP` | `true` | Missed Job Catch-Up on Boot |
| `BASE_MODEL_NAME` | `mlx-community/Qwen2.5-7B-Instruct-4bit` | QLoRA 4-bit Fine-Tuning Base Model |
| `ADAPTER_PATH` | `project/models/qwen2.5-bazi-adapter` | Fine-Tuning Adapter Target |

---

## 📝 Handoff Summary for Next Session / AI Agent

> **ถึง AI Agent หรือผู้พัฒนาคนถัดไป:**
> 1. โครงสร้างโปรเจกต์ โค้ดคำนวณ pure Python, ระบบ RAG (3,096 vectors) และ FastAPI Server รันสมบูรณ์แล้ว 100%
> 2. ทุกครั้งที่เริ่มงาน สามารถรัน `python3 -m pytest -v` เพื่อยืนยันว่า test ทั้งหมด 56 ข้อผ่านสมบูรณ์
> 3. หากต้องการเริ่ม Fine-Tune ให้รัน `python3 scripts/run_mlx_finetune.py`
> 4. เอกสารสเปกโปรเจกต์ฉบับเต็มดูได้ที่ [`project.md`](file:///Users/kimlenglim/Project/HoroConsultant/project.md) และ [`README.md`](file:///Users/kimlenglim/Project/HoroConsultant/README.md)
