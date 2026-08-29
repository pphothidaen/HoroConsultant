# 📘 คู่มือการใช้งานและ How-To Guide ครอบคลุมทุกแพลตฟอร์ม (HoroConsultant Manual)

> **โครงการ:** HoroConsultant — Computational Metaphysics Engine  
> **วัตถุประสงค์:** คู่มือขั้นตอนการใช้งานระบบอย่างละเอียด สำหรับ End-User, ผู้ดูแลระบบ (Admin), นักโหราศาสตร์ผู้ตรวจทาน (HITL Reviewer) และนักพัฒนาซอฟต์แวร์บนหลากหลายแพลตฟอร์ม

---

> 🚨 **MANDATORY UPDATE GOVERNANCE RULE (กฎบังคับการอัปเดตเอกสาร):**  
> **เอกสาร How-To และคู่มือการใช้งานทุกส่วนในไฟล์นี้ จะต้องได้รับการอัปเดตให้เป็นปัจจุบันอยู่เสมอ หากมีการเปลี่ยนแปลง แก้ไข หรือพัฒนาระบบเพิ่มเติมในโปรเจกต์** เพื่อให้แน่ใจว่าผู้ใช้งาน นักพัฒนา และ AI Agents สามารถใช้งานและดูแลระบบได้อย่างถูกต้องไม่คลาดเคลื่อน

---

## Test provenance workflow for developers and agents

1. Write black-box acceptance tests before implementation and run them to
   capture a real failing result or negative control.
2. Create a closed manifest under `plans/test_provenance/` with the exact test
   SHA-256 values, baseline parent, allowed source paths, and failure evidence.
3. Commit only tests, fixtures, and that manifest. Use
   `Test-Baseline-Ticket: <ticket>` in the baseline commit message.
4. Start source coding only after the commit is marked
   `TEST_BASELINE_VERIFIED`. Add `Test-Baseline: <full-sha>` to every owned
   source commit.
5. Do not edit a frozen test from the source lane. If it is wrong, stop work
   and create an independently reviewed, test-only superseding baseline.
6. Finish with `scripts/test_provenance_guard.py`, full QA,
   `sync_ai_agent_ecosystem.py --check`, the secret scan, and
   `project/core/code_reviewer.py` using the same ticket/baseline/manifest.

The repository pre-commit hook performs read-only early checks and never runs
version stamping or stages files. Configure `.githooks` locally if desired,
but rely on the required `Test Provenance` CI check for merge enforcement.

---

## 📑 สารบัญ (Table of Contents)

1. [🌐 คู่มือสำหรับ End-User (Website User Guide)](#1-คู่มือสำหรับ-end-user-website-user-guide)
   - [1.1 การกรอกข้อมูลวัน-เวลาเกิดและค้นหาพิกัด](#11-การกรอกข้อมูลวัน-เวลาเกิดและค้นหาพิกัด)
   - [1.2 การคำนวณผังดวง BaZi 4 เสา & True Solar Time](#12-การคำนวณผังดวง-bazi-4-เสา--true-solar-time)
   - [1.3 การดูผังภาพกราฟิกเวกเตอร์ SVG Chart](#13-การดูผังภาพกราฟิกเวกเตอร์-svg-chart)
   - [1.4 การดูบทวิเคราะห์ AI & Gemini Audit Tabs](#14-การดูบทวิเคราะห์-ai--gemini-audit-tabs)
   - [1.5 การกดคำนวณผัง 9 ศาสตร์ย่อย (5-Branch Metaphysics)](#15-การกดคำนวณผัง-9-ศาสตร์ย่อย-5-branch-metaphysics)
   - [1.6 การใช้งาน OpenAPI Interactive API Documentation (/docs, /redoc)](#16-การใช้งาน-openapi-interactive-api-documentation-docs-redoc)
2. [🔐 คู่มือสำหรับ Admin & นักอภิมหาโหร (Admin & HITL Reviewer Guide)](#2-คู่มือสำหรับ-admin--นักอภิมหาโหร-admin--hitl-reviewer-guide)
   - [2.1 การใช้งาน Admin Panel & Knowledge Catalog](#21-การใช้งาน-admin-panel--knowledge-catalog)
   - [2.2 การใช้งาน HITL Review Studio & Confidence Heatmap](#22-การใช้งาน-hitl-review-studio--confidence-heatmap)
3. [💻 คู่มือการใช้งานบนแพลตฟอร์มต่างๆ สำหรับนักพัฒนา (Multi-Platform Developer How-To)](#3-คู่มือการใช้งานบนแพลตฟอร์มต่างๆ-สำหรับนักพัฒนา-multi-platform-developer-how-to)
   - [3.1 Local Development Platform (macOS / Linux)](#31-local-development-platform-macos--linux)
   - [3.2 Docker Deployment Platform (Ubuntu Production)](#32-docker-deployment-platform-ubuntu-production)
   - [3.3 Local Ollama LLM Platform](#33-local-ollama-llm-platform)
   - [3.4 Kaggle GPU Fine-Tuning Platform CLI](#34-kaggle-gpu-fine-tuning-platform-cli)
   - [3.5 Model Context Protocol (MCP) Server Platform](#35-model-context-protocol-mcp-server-platform)
   - [3.5.1 Codex AI Agent Platform](#351-codex-ai-agent-platform)
   - [3.6 Canonical HF Docker + Vercel Release CLI](#36-canonical-hf-docker--vercel-release-cli)
   - [3.7 Canonical Production Targets and Retired Platform Matrix](#37-canonical-production-targets-and-retired-platform-matrix)
   - [3.8 Release Execution Boundary](#38-release-execution-boundary)

---

## 🌐 1. คู่มือสำหรับ End-User (Website User Guide)

**URL หน้าจอหลัก:** `http://localhost:8000/` (หรือ Domain Production)

```
+-----------------------------------------------------------------------+
|  🌌 Computational Metaphysics Engine (Dashboard)                       |
|  [วัน-เวลาเกิด] [ลองจิจูด] [โซนเวลา] [🔍 ค้นหาพิกัดสถานที่]             |
|  [ปุ่มเลือกเมืองสำเร็จรูป: กรุงเทพฯ | เชียงใหม่ | ภูเก็ต | สิงคโปร์]          |
|  [ ] ยามเกิดไม่แน่นอน   [✓] เปิดใช้ Gemini Validator                     |
|  [☯ คำนวณผังดวง & ตีความด้วย AI]                                        |
+-----------------------------------------------------------------------+
|  🎨 ผังดวงเวกเตอร์ SVG (Interactive SVG Vector Chart)                   |
|  🏛️ ผังดวงชะตา 4 เสา (Four Pillars) | ⚖️ สมดุลธาตุทั้ง 5               |
|  🤖 บทพยากรณ์ multi-Agent (📖 บทตีความ | 🛡️ Gemini Audit | 📚 RAG)   |
+-----------------------------------------------------------------------+
```

### 1.1 การกรอกข้อมูลวัน-เวลาเกิดและค้นหาพิกัด
1. **กรอกวัน-เวลาเกิด:** ป้อนวันและเวลาตามเวลาท้องถิ่นในรูปแบบ `YYYY-MM-DD HH:MM:SS` (เช่น `1990-05-15 14:30:00`)
2. **ค้นหาพิกัดอัตโนมัติ (Geocoding):** 
   - พิมพ์ชื่ออำเภอ/จังหวัด/เมือง ในช่อง **"🔍 ค้นหาพิกัดสถานที่ (เช่น บางกะปิ, กรุงเทพ)"**
   - กดปุ่ม **Enter** หรือคลิกปุ่ม **"ค้นหาพิกัด"**
   - ระบบจะทำการค้นหาพิกัดลองจิจูด (Longitude) และคำนวณ UTC Offset ให้อัตโนมัติ พร้อมแสดงเครื่องหมาย ✅
3. **ใช้ปุ่มเมืองสำเร็จรูป (Preset Buttons):**
   - สามารถคลิกปุ่ม **"กรุงเทพฯ"**, **"เชียงใหม่"**, **"ภูเก็ต"** หรือ **"สิงคโปร์"** เพื่อเติมพิกัดและโซนเวลาได้ทันที
4. **โหมดไม่ทราบยามเกิด (Probabilistic Matrix):**
   - หากไม่ทราบเวลาเกิดที่แน่นอน ให้ติ๊กเลือก **"ยามเกิดไม่แน่นอน"** ระบบจะคำนวณฉากทัศน์ยามเกิดทั้ง 12 ยามพร้อมถ่วงน้ำหนักความน่าจะเป็นให้อัตโนมัติ

---

### 1.2 การคำนวณผังดวง BaZi 4 เสา & True Solar Time
1. คลิกปุ่ม **"☯ คำนวณผังดวง & ตีความด้วย AI"** (`#btn-submit`)
2. ระบบจะทำการคำนวณเวลาสุริยคติจริง (True Solar Time — TST) โดยปรับแก้ค่าเวลาท้องถิ่นปานกลาง (LMT) ร่วมกับสมการเวลา (Equation of Time — EoT)
3. การอ่านผังดวง 4 เสา (Pillars Grid):
   - **เสาปี (Year Pillar):** แทนวัยเยาว์ บรรพบุรุษ และสิ่งแวดล้อมภายนอก
   - **เสาเดือน (Month Pillar):** แทนกุมารวัย การงาน อาชีพ และบิดามารดา
   - **เสาวัน (Day Pillar):** แถวบนคือ **ธาตุเจ้าตัว (Day Master)** แถวล่างคือเรือนคู่ครอง
   - **เสายาม (Hour Pillar):** แทนวัยชรา บริวาร บุตร ลาภยศ และความคิดลึกๆ
4. **สมดุล 5 ธาตุ (Five Elements Harmony):** ดูแถบเปอร์เซ็นต์สัดส่วน ไม้, ไฟ, ดิน, ทอง, น้ำ เพื่อวิเคราะห์ธาตุให้คุณ-ให้โทษ

---

### 1.3 การดูผังภาพกราฟิกเวกเตอร์ SVG Chart
- เมื่อกดคำนวณผังดวงแล้ว การแสดงผลจะปรากฏการ์ด **"🎨 ผังดวงเวกเตอร์ SVG (Interactive SVG Vector Chart)"**
- ผังจะวาดตัวอักษรจีนมงคล สัญลักษณ์ธาตุ และวงล้อราศีด้วยกราฟิก SVG ความละเอียดสูง สามารถย่อ-ขยายภาพได้โดยภาพไม่แตก

---

### 1.4 การดูบทวิเคราะห์ AI & Gemini Audit Tabs
ในการ์ดบทพยากรณ์ AI สามารถสลับแท็บดูข้อมูลได้ 3 ส่วน:
- **📖 บทตีความโหราศาสตร์:** อ่านบทพยากรณ์ที่สร้างจากโมเดล Local Ollama (หรือ Dual Gemini Cloud Fallback)
- **🛡️ Gemini Validator Audit:** ดูรายงานการตรวจสอบตรรกะธาตุจาก Gemini Agent (แสดงสถานะ, คะแนนความมั่นใจ, และข้อเสนอแนะ)
- **📚 คัมภีร์อ้างอิง (RAG):** ดูคัมภีร์โบราณอ้างอิง (子平真詮, 滴天髓 ฯลฯ) ที่สืบค้นจาก FAISS Vector Store 3,132 Chunks

---

### 1.5 การกดคำนวณผัง 16 ศาสตร์ย่อย (Extended Metaphysics Suite)
ที่ด้านบนของแดชบอร์ด สามารถคลิกปุ่มคำนวณศาสตร์โหราศาสตร์ย่อยทั้ง 16 สาขาวิชาได้แก่:
- 🔮 **紫微斗數 (Zi Wei Dou Shu):** ดูผัง 12 ภพ, ดาวหลัก 14 ดวง และดาวสี่化
- ⚡ **奇門遁甲 (Qi Men Dun Jia):** ดูผัง 4 จาน 9 ตาราง (ดาว, ประตู, เทพ)
- 🌊 **大六壬 (Da Liu Ren):** ดู 3 การส่งผ่าน (三傳) และ 4 บทเรียน (四課)
- ☯ **易經六爻 (I Ching):** ดูฉักกะหลัก-ฉักกะเปลี่ยน และ 6 ลายเส้นพร้อม 6 สัตว์มงคล
- 🏯 **玄空風水 (Xuan Kong):** ดูผังดาวเหินยุค 9 แบบ 9 ตาราง (ดาวประธาน, ดาวนั่ง, ดาวหัน)
- 📅 **擇吉 (Ze Ji):** ดูฤกษ์ยามมงคล 12 เทพผู้ตรวจการ และกิจกรรมที่ควร/ไม่ควรทำ
- 🐘 **โหราศาสตร์ไทย & ภารตวิทยา:** ดูลัคนาสุริยยาตร์, ดาวศิริ/กาลกิณี, มหาทักษา 8 เทวดา และนักษัตร 27 ดารา
- 🌌 **โหราศาสตร์สากล & ยูเรเนียน:** ดูตำแหน่งดาวเคราะห์สากล, ดาวทิพย์ 8 องค์ และจุดอิทธิพลสะท้อน (Midpoint)
- 🔢 **สัตตเลข 7 ฐาน & เลขศาสตร์:** ดูตารางสัตตเลข 4 แถว 7 ฐาน และผลรวมเลขศาสตร์ Chaldean
- 👑 **太乙神數 (Tai Yi Shen Shu):** วิเคราะห์ปีสะสมจักรวาลและดาวไท่อิก 16 ทิศทาง
- ⚔️ **六爻預測 (Liu Yao Divination):** วิเคราะห์ 6 เส้นพร้อมระบบนาเจี่ย (納甲) และเบญจญาติ (五親)
- 🌸 **梅花易數 (Mei Hua Yi Shu):** วิเคราะห์กว้าดอกเหมย ตัวตน-หน้าที่ (體用) และปฏิสัมพันธ์ 5 ธาตุ
- ⛰️ **三合風水 (San He Feng Shui):** วิเคราะห์ 24 ขุนเขาและวิธีทางน้ำ 12 วัฏจักรชีวิต (十二長生水法)
- 🪐 **七政四餘 (Qi Zheng Si Yu):** วิเคราะห์ 7 ดาวจริง + 4 เงาดาว (ราหู, เกตุ, จื่อชี่, เย่ว์เป่ย) บน 28 ดาวนักษัตร
- 👤 **麻衣神相 (Mian Xiang Physiognomy):** วิเคราะห์โหงวเฮ้ง 12 วังชะตา และ 5 ขุนนางบนใบหน้า

---

### 1.6 การใช้งาน API v2 Router และ OpenAPI Documentation
ระบบรองรับ API v2 สำหรับการคำนวณแบบรวมศูนย์ (Unified) และการทำนายแบบเจาะจงประเด็น (Question-Focused Answering):
- **POST `/api/v2/calculate/unified`:** คำนวณหลายศาสตร์พร้อมกันใน Request เดียว
- **POST `/api/v2/interpret/focused`:** วิเคราะห์คำถามแบบเจาะจง 6 มิติ (การงาน, การเงิน, ความรัก, สุขภาพ, ครอบครัว, ฤกษ์ยาม) พร้อมอ้างอิงคัมภีร์
- **POST `/api/v2/mian_xiang/analyze`:** วิเคราะห์โครงสร้างใบหน้า 12 วังชะตา
- **GET `/api/v2/health`:** ตรวจสอบสถานะและรายการ 16 ศาสตร์ที่รองรับ
- **📘 Swagger UI Interactive Documentation (`http://localhost:8000/docs`)**
- **📕 ReDoc Schema Explorer (`http://localhost:8000/redoc`)**


---

## 🔐 2. คู่มือสำหรับ Admin & นักอภิมหาโหร (Admin & HITL Reviewer Guide)

### 2.1 การใช้งาน Admin Panel & Knowledge Catalog
**URL:** `http://localhost:8000/admin`

```
+-----------------------------------------------------------------------+
|  🔐 Admin Panel — Knowledge Catalog & Fine-Tune Orchestrator          |
|  [Email Login: pansakorn@gmail.com] -> [คลิกเข้าสู่ระบบ]               |
+-----------------------------------------------------------------------+
|  📚 รายการคัมภีร์ใน Knowledge Catalog (38 เอกสาร)                        |
|  ⚡ Trigger Fine-Tuning Pipeline (Kaggle GPU)                          |
+-----------------------------------------------------------------------+
```

1. **การเข้าสู่ระบบ (Authentication):**
   - ระบบมีการป้องกันความปลอดภัย เข้าสู่ระบบด้วย Email Whitelist (เช่น `pansakorn@gmail.com`)
   - กรอก อีเมลที่ได้รับอนุญาต แล้วคลิก **"เข้าสู่ระบบ"**
2. **การจัดการ คัมภีร์ Knowledge Catalog:**
   - ตรวจสอบรายชื่อหนังสือ คัมภีร์ และตำราโหราศาสตร์ทั้ง 38 เล่มที่ถูก Ingest เข้าสู่ระบบ
3. **การสั่งรัน Fine-Tuning Pipeline:**
   - คลิกปุ่ม **"⚡ Trigger Fine-Tune Pipeline"** เพื่อส่งคำสั่งไปรันการเทรนโมเดลบน Kaggle GPU

---

### 2.2 การใช้งาน HITL Review Studio & Confidence Heatmap
**URL:** `http://localhost:8000/hitl-studio`

```
+-----------------------------------------------------------------------+
|  🔬 HITL Review Studio — Astrologer Ground-Truth Curation             |
|  Queue List: [Item #101 (BaZi Day Master)] [Item #102 (ZiWei MingGong)]|
+-----------------------------------------------------------------------+
|  [คำถามดวงชะตา] | [บทคำนวณ 4 เสา]                                       |
|  [Heatmap คำตอบ AI: เขียว=มั่นใจสูง | ส้ม/แดง=ควรปรับปรุง]               |
|  [ช่องแก้ไขบทพยากรณ์โดยนักโหราศาสตร์ (Ground-Truth Answer)]              |
|  ความถูกต้อง: ⭐⭐⭐⭐⭐                                                 |
|  [คลิกอนุมัติ (Approve)]   [คลิกบันทึกการแก้ไข]                        |
|  -------------------------------------------------------------------  |
|  [📥 Export Dataset (hitl_approved.jsonl)]                            |
+-----------------------------------------------------------------------+
```

1. **การเลือกรายการตรวจทาน:**
   - เลือกรายการคำตอบ AI จากคอลัมน์ด้านซ้าย (Pending Queue)
2. **การดู Confidence Heatmap Highlight:**
   - ข้อความสีเขียว = ความมั่นใจสูง (> 85%)
   - ข้อความสีส้ม/แดง = ความมั่นใจต่ำ/มีแนวโน้มคลาดเคลื่อน (ควรได้รับการตรวจทานโดยนักโหราศาสตร์)
3. **การแก้ไข & ให้คะแนน (Reviewing & Rating):**
   - แก้ไขบทวิเคราะห์ในช่อง **"Ground-Truth Final Answer"** ให้ถูกต้องตามหลักวิชาโหราศาสตร์
   - ให้คะแนนดาว 1 ถึง 5 ดาว
   - คลิกปุ่ม **"Approve & Save"**
4. **การส่งออกชุดข้อมูลเพื่อ Fine-Tune (Export JSONL):**
   - คลิกปุ่ม **"📥 Export Approved JSONL Dataset"** เพื่อดาวน์โหลดไฟล์ `hitl_approved.jsonl` นำไปใช้ปรับแต่งโมเดลในรอบถัดไป

---

## 💻 3. คู่มือการใช้งานบนแพลตฟอร์มต่างๆ สำหรับนักพัฒนา (Multi-Platform Developer How-To)

### 3.1 Local Development Platform (macOS / Linux)
**การรันและการทดสอบในเครื่องนักพัฒนา:**
```bash
# 1. ติดตั้ง Dependencies
pip install -r requirements.txt

# 2. ตั้งค่าไฟล์ .env
cp .env.example .env

# 3. รัน FastAPI Dev Server
python3 -m uvicorn project.main:app --reload --port 8000

# 4. รันชุดทดสอบความถูกต้อง Pytest (93 Test Cases)
python3 -m pytest project/tests -v

# 5. รันสคริปต์ตรวจจับภาพหน้าจอ Playwright E2E
python3 scripts/run_e2e_screenshots.py
```

---

### 3.2 Docker Deployment Platform (Ubuntu Production)
**การปรับใช้บนเซิร์ฟเวอร์ด้วย Docker & Docker Compose:**
```bash
# 1. Build และรันคอนเทนเนอร์ทั้งหมดในโหมด Background
docker compose up --build -d

# 2. ตรวจสอบสถานะการทำงานของคอนเทนเนอร์
docker compose ps

# 3. ดู Log การทำงานของแอปพลิเคชัน
docker compose logs app --tail=100 -f

# 4. หยุดการทำงานของเซิร์ฟเวอร์
docker compose down
```

---

### 3.3 Local Ollama LLM Platform
**การติดตั้งและการจัดการโมเดลในเครื่อง (Offline Mode):**
```bash
# 1. ดึงโมเดลมาตรฐาน
ollama pull qwen2.5:7b
ollama pull llama3:8b

# 2. สร้างโมเดลเฉพาะทาง qwen2.5-bazi จาก Modelfile
cd project/models
ollama create qwen2.5-bazi -f Modelfile

# 3. ทดสอบการเรียกใช้งานผ่าน Ollama CLI
ollama run qwen2.5-bazi "คำนวณผังดวง ดิถีเพลิงเกิดในเดือนชวด"
```

---

### 3.4 Kaggle GPU Fine-Tuning Platform CLI
**การสั่งงานและติดตามการเทรนบน Cloud GPU ผ่าน Terminal:**
```bash
# 1. ตรวจสอบสถานะ GPU Kernel บน Kaggle
python3 scripts/kaggle_notebook_manager.py --status

# 2. Push โค้ดและเริ่มการเทรน LoRA 4-bit บน Kaggle Nvidia T4
python3 scripts/kaggle_notebook_manager.py --push

# 3. ดึงผลลัพธ์การเทรนและ Log ลงมาที่เครื่อง
python3 scripts/kaggle_notebook_manager.py --pull
```

---

### 3.5 Model Context Protocol (MCP) Server Platform
**การเปิดใช้งาน MCP Server สำหรับเชื่อมต่อกับ AGY / thClaws Agent Harness:**
```bash
# รัน MCP Server ผ่าน Standard Input/Output Protocol
python3 project/mcp_server.py
```

**ตัวอย่างเครื่องมือ MCP (Exposed Tools):**
- `bazi_calculate` — คำนวณผังดวง 4 เสาและคืนค่าเป็น JSON
- `render_bazi_svg` — วาดรูปผังดวง BaZi SVG บันทึกลงไฟล์
- `render_zodiac_svg` — วาดรูปผังวงล้อ 12 ราศี SVG บันทึกลงไฟล์
- `rag_search` — สืบค้นข้อมูลคัมภีร์โบราณ 3,132 Vector Chunks

---

### 3.5.1 Codex AI Agent Platform

Codex uses the existing repository skills in `.agents/skills/` directly. Its custom subagent TOML files are generated from the legacy workspace role definitions, so Antigravity and Codex can coexist.

```bash
# Regenerate after modifying legacy Antigravity/workspace roles.
python3 scripts/sync_sdlc_agents.py --sync
python3 scripts/sync_codex_agents.py --sync

# Check both targets without writing files.
python3 scripts/sync_sdlc_agents.py --check --use-python
python3 scripts/sync_codex_agents.py --check
```

Edit `.agents/agents/*/agent.json` for role content. Do not manually edit `.codex/agents/*.toml`; the Codex generator will overwrite generated files. Provider-specific model names in legacy prompts are historical context, while Codex subagents use the active Codex model.

---

### 3.6 Canonical HF Docker + Vercel Release CLI

Production แยกเป็น Vercel UI/gateway และ HF Docker backend เท่านั้น:

- UI/gateway: `https://horo-consultant-psi.vercel.app`
- Backend: `pphothidaen/horoconsultant-core-backend` (`sdk: docker`)
- Vercel production config ที่บังคับ:
  `HF_BACKEND_URL=https://pphothidaen-horoconsultant-core-backend.hf.space`
  (เป็น public config ไม่ใช่ secret)

หากตัวแปรหายหรือไม่ตรง canonical origin gateway จะตอบ 503
`backend_not_configured` แบบ fail-closed ห้ามแทนด้วย static/local calculation.

Production publication ต้องมาจาก candidate ที่ผ่าน CI บน `main` เท่านั้น.
`.github/workflows/hf_backend_deploy.yml` รับ successful `workflow_run` ของ
`main` หรือ manual dispatch จาก `refs/heads/main`; direct push อย่างเดียวไม่
publish. Candidate SHA ต้องเป็น full lowercase 40-character SHA และต้องตรงกับ
current `main` event commit. ค่า `source_sha` ห้ามเลือก stale commit หรือ commit
จาก branch อื่น.

หลัง checkout candidate แบบ exact แล้ว gate ต้องยืนยันครบทั้งหมดก่อนสร้าง
manifest และยืนยันซ้ำทันทีก่อน publish:

- `git rev-parse HEAD` ตรงกับ candidate SHA;
- ไม่มี tracked, staged หรือ untracked change;
- recursive submodule state สะอาดและ pinned;
- manifest ระบุ `packaging_commit` ตรงกับ candidate SHA, `branch: main`,
  canonical Space ID และ `sdk: docker`.

หากข้อใดไม่ผ่านให้รายงาน `[ERROR] BLOCKED`. Local dry-run ใช้ตรวจ payload
และ provenance ได้เฉพาะ clean worktree; ห้ามใช้ output จาก dirty worktree เป็น
release evidence.

```bash
# 1. Payload + provenance audit โดยไม่ upload
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --dry-run

# 2. ตรวจ backend สดแบบ read-only
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --check-health
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --verify-version

# 3. ตรวจ Vercel UI ทั้งห้า viewport
python3 scripts/run_visual_layout_audit.py \
  --url https://horo-consultant-psi.vercel.app \
  --scenario v3-consensus \
  --no-server
```

#### Mandatory fail-closed release gate

```bash
python3 -m pytest -q \
  tests/test_publish_space_hf.py \
  tests/test_hf_release_governance.py \
  project/tests/test_production_monitor_release_contract.py
python3 project/core/code_reviewer.py --scan-secrets
python3 scripts/sync_ai_agent_ecosystem.py --check
```

ต้องมี Docker dry-run, reviewer, exact live health/version, production API E2E,
version consistency และ visual `5/5` เป็นสีเขียวทั้งหมดก่อนประกาศ
`READY_FOR_PROD`. ค่า `unknown`, `warning`, `indeterminate`, 503 หรือ version
ไม่ตรงถือว่าไม่ผ่าน. การ push/merge, Vercel production deploy และ HF publish
เป็นคนละ external gate และต้องผูก exact target/rollback ทุกครั้ง.

Candidate identity มาจาก committed release metadata เท่านั้น:

- `version` ต้อง bind กับ `release_source_commit` แบบ exact;
- `release_source_revision`, metadata path และ SHA-256 digest ต้องถูกต้อง;
- `release_source_commit` ต้องเป็น ancestor ของ `packaging_commit`;
- `packaging_commit` เป็น packaging evidence เท่านั้น ไม่ใช่ deployed identity;
- environment value, CLI default, runtime `HEAD` หรือ external override ห้ามแทน
  committed identity.

HF Docker backend และ Vercel UI เป็นคนละ gate:

| Gate | Required evidence | Stop condition |
| :--- | :--- | :--- |
| HF Docker backend | Canonical Space/`sdk: docker`, approved manifest and receipt, exact `/health` and `/version.json`, remote revision, prior rollback revision | Block on stale/missing identity, unhealthy runtime, receipt mismatch, or unavailable rollback identity |
| Vercel UI | Approved production deployment and revision, exact `/version.json`, gateway/API E2E, five canonical viewport report and screenshots, reviewer decision, prior rollback revision | Block on stale/missing identity, failed E2E, fewer than 5/5 viewports, unresolved indeterminate, or unavailable rollback identity |

Backend gate ที่ผ่านแล้วไม่อนุมัติ Vercel UI และ Vercel gate ที่ผ่านแล้วไม่
อนุมัติ backend. Production monitor ต้องพบ identity surface exactly two รายการ
(HF Docker และ Vercel) ที่ตรงกับ candidate เดียวกันก่อน final approval.

Vercel rollback ให้เก็บ deployment ก่อนหน้าและ env-entry ID ที่เพิ่มไว้ ห้ามลบ
production deployments. HF rollback ต้องใช้ validated receipt/CAS ตาม publisher
workflow; ห้าม publish จาก dirty worktree.

---

### 🌐 3.7 Canonical Production Targets and Retired Platform Matrix

ตารางนี้แยก canonical production targets ออกจาก historical/research platforms;
แถวที่ retired หรือ unselected ไม่ใช่ release alternative:

| Platform | Deployment Type | Suitable Use Case | Latency (TH) | Cost & SLA Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Hugging Face Static Edge CDN** | Retired backend lane | Historical evidence only; never deploy static bytes to the canonical backend Space | N/A | **PROHIBITED** |
| **Azure Container Apps / Fly** | Retired public lanes | Historical evidence only | N/A | **PROHIBITED** |
| **Hugging Face Spaces Docker** | Canonical backend (`sdk: docker`) | FastAPI API + Rust Fast Math + FAISS | Mid (~200ms US) | **ACTIVE TARGET** |
| **Vercel Edge Network** | Static UI + lightweight gateway | Browser UI and canonical backend proxy | Global Edge (< 20ms) | **ACTIVE TARGET** |
| **Render.com / Railway.app** | Unselected research options | No production authority | N/A | **NOT CONFIGURED** |
| **Kaggle GPU Accelerator** | GPU Fine-Tuning Notebook (`T4 Machine`) | LLM Fine-Tuning & Model Weight Fusion | Batch Pipeline | Free 30h/week Nvidia T4 GPU |

#### 🧩 เพิ่มเติม: Hugging Face S3-Compatible Storage Credentials

ข้อความ warning ที่บอกว่า:

> These credentials are paired with the access token HF_TOKEN...

หมายถึง credential ในส่วนนี้ใช้สำหรับเชื่อมต่อ Hugging Face Storage Bucket (S3-compatible) เท่านั้น ใช้คู่กับการใช้งาน client เช่น `aws`, `boto3`, `rclone`  
ค่าเหล่านี้ควรเก็บเป็น secret เท่านั้น (ไม่ควรใส่ใน source code)

ตัวแปรที่ใช้:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ENDPOINT_URL`

ตั้งค่าใน CI/CD เป็น Secrets และในเครื่อง dev-test ตามตัวอย่าง `~/.aws/config` / `~/.aws/credentials` ตามเอกสาร:  
https://huggingface.co/docs/hub/storage-buckets-s3

ตัวอย่าง (ค่าเฉพาะ namespace ของคุณ, อย่างเช่น `pphothidaen` หากเป็น personal namespace):

```ini
# ~/.aws/config
[default]
region = us-east-1
output = json
endpoint_url = https://pphothidaen.s3.us-east-1.amazonaws.com

# ~/.aws/credentials
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
```

### 🛠️ 3.8 Release Execution Boundary

ไม่มีคำสั่ง "deploy all platforms" ที่เป็น canonical production authority.
Legacy automation และ retired Azure/Fly workflows ใช้เป็น release path ไม่ได้.
Production handoff ต้องแยก approval และ evidence ดังนี้:

1. HF Docker backend ใช้ CI-gated workflow จาก exact `main` candidate ที่สะอาด.
2. Vercel UI ใช้ production deployment gate แยกต่างหากสำหรับ candidate เดียวกัน.
3. Code Reviewer และ Orchestrator อนุมัติ final release เมื่อ evidence bundle ของ
   ทั้งสอง targets ผ่านครบเท่านั้น.

การอ่านสถานะหรือรัน local dry-run ไม่ได้ให้สิทธิ์ stage, commit, push, publish,
deploy, secret sync หรือ rollback. การกระทำภายนอกแต่ละรายการต้องมี owner
authorization และ candidate-bound evidence ของตัวเอง.

---

### 📊 3.9 การติดตั้งและตรวจสอบระบบ Grafana Cloud Observability & Prometheus Metrics

ระบบ **HoroConsultant** รองรับการส่งข้อมูล Observability แบบ All-in-One ไปยัง **Grafana Cloud Free Tier (`vividlamp2135.grafana.net`)**:

1. **Official Grafana Cloud Production Dashboards:**
   - 🔮 **HoroConsultant Main Observability Dashboard (Public Shareable Link)**:  
     [https://vividlamp2135.grafana.net/public-dashboards/cab04a7907b74c2b9889a8ad811bbcdb](https://vividlamp2135.grafana.net/public-dashboards/cab04a7907b74c2b9889a8ad811bbcdb)  
     *(ไม่ต้องผ่านการเข้าสู่ระบบ - แสดงข้อมูลสุขภาพระบบ, HTTP RPM, API Latency Quantiles P95/P90/P50, FAISS RAG Search Volume และ LLM Inference Model Ratio)*

   - 🌐 **Authenticated Main Dashboard**:  
     [https://vividlamp2135.grafana.net/d/horoconsultant-observability/horoconsultant-observability-dashboard?from=now-1h&to=now&timezone=browser&var-DS_PROMETHEUS=grafanacloud-usage&refresh=5s](https://vividlamp2135.grafana.net/d/horoconsultant-observability/horoconsultant-observability-dashboard?from=now-1h&to=now&timezone=browser&var-DS_PROMETHEUS=grafanacloud-usage&refresh=5s)

   - 🚨 **Alert Groups Insights Dashboard**:  
     [https://vividlamp2135.grafana.net/d/e18b8570-27bc-4ab2-bb1c-baeea1363061/alert-groups-insights?from=now-7d&to=now&timezone=browser&var-datasource=grafanacloud-usage](https://vividlamp2135.grafana.net/d/e18b8570-27bc-4ab2-bb1c-baeea1363061/alert-groups-insights?from=now-7d&to=now&timezone=browser&var-datasource=grafanacloud-usage)  
     *(วิเคราะห์และติดตามสถานะการแจ้งเตือน Alert Trigger, Response Time, Resolution Latency และการแจ้งเตือนทีมงาน)*

   - 🌩️ **Incident Insights Dashboard**:  
     [https://vividlamp2135.grafana.net/d/39ac5605-b947-4c43-87dc-60575f57f219/incident-insights?from=now-90d&to=now&timezone=utc](https://vividlamp2135.grafana.net/d/39ac5605-b947-4c43-87dc-60575f57f219/incident-insights?from=now-90d&to=now&timezone=utc)  
     *(วิเคราะห์สถิติ Incident ย้อนหลัง, ระดับความรุนแรง Severity, MTTD และ MTTR)*

3. **การส่งข้อมูลจำลองและการตรวจสอบข้อมูลแดชบอร์ด (Telemetry Data Ingestion & Verification):**
   ```bash
   # 1. ฉีดข้อมูลจำลอง telemetry OTLP (Prometheus) + Grafana Incident Datasource พร้อมตรวจสอบคิวรี
   python3 scripts/inject_prod_dummy_data.py --stages 6 --target all --verify-queries

   # 2. ฉีดข้อมูลเฉพาะ Grafana Incident Datasource (Incidents, Severity, Labels, MTTR)
   python3 scripts/inject_grafana_incident_data.py --stages 6 --verify-queries

   # 3. ทดสอบการจำลองแบบ Dry-Run
   python3 scripts/inject_prod_dummy_data.py --dry-run
   python3 scripts/inject_grafana_incident_data.py --dry-run

   # 4. ส่งออกและเผยแพร่แดชบอร์ดไปยัง Grafana Cloud API
   python3 scripts/grafana_cloud_exporter.py --export-dashboard
   ```

4. **การเปิดใช้งานผ่าน Environment Variables:**
   ```bash
   PROMETHEUS_METRICS_ENABLED=true
   GRAFANA_CLOUD_URL=https://vividlamp2135.grafana.net
   GRAFANA_API_KEY=glsa_YOUR_GRAFANA_API_KEY
   ```

---

### 🔮 3.10 การใช้งาน Autonomous Knowledge Distillation & Fine-Tuning Pipeline

ระบบ **HoroConsultant MLOps** รองรับการสกัดความรู้จาก **Google NotebookLM** ผ่าน **Hermes Agent** แปลงเป็นชุดข้อมูลและยิงเทรนบน **Kaggle GPU**:

1. **การรัน Pipeline สกัดความรู้และสร้างชุดข้อมูลผ่าน CLI:**
   ```bash
   # สกัดทุกศาสตร์ (BaZi, ZiWei, FengShui, QiMen) และจัดฟอร์แมต ChatML
   python3 project/mlops/run_pipeline.py --domain all --format chatml

   # รันแบบจำลอง Dry-Run พร้อมทดสอบ Trigger Kaggle Training
   python3 project/mlops/run_pipeline.py --domain all --dry-run --trigger-training
   ```

2. **การเปิดใช้งาน Streamlit MLOps Monitoring Dashboard:**
   ```bash
   streamlit run project/mlops/dashboard/app.py
   ```

3. **REST API Endpoints สำหรับ MLOps (`/api/v1/mlops`):**
   - `GET /api/v1/mlops/status`: ตรวจสอบสถานะ Dataset, Target Model, และ Kaggle GPU Kernel
   - `GET /api/v1/mlops/datasets`: ดูรายการไฟล์ `.jsonl` และจำนวนตัวอย่าง
   - `POST /api/v1/mlops/distill`: สั่งสกัดความรู้ตาม Domain ที่ระบุ
   - `POST /api/v1/mlops/train`: สั่ง Trigger Kaggle Fine-Tuning

4. **GitHub Actions Scheduled Automation:**
   - ตารางเวลาอัตโนมัติ: รันทุกวันอาทิตย์ เวลา 02:00 UTC ผ่าน `.github/workflows/scheduled_distill_finetune.yml`
   - รองรับการ Trigger แบบ Manual พร้อมเลือก Domain และ Format ได้ทันที
