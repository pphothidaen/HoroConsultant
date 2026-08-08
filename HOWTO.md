# 📘 คู่มือการใช้งานและ How-To Guide ครอบคลุมทุกแพลตฟอร์ม (HoroConsultant Manual)

> **โครงการ:** HoroConsultant — Computational Metaphysics Engine  
> **วัตถุประสงค์:** คู่มือขั้นตอนการใช้งานระบบอย่างละเอียด สำหรับ End-User, ผู้ดูแลระบบ (Admin), นักโหราศาสตร์ผู้ตรวจทาน (HITL Reviewer) และนักพัฒนาซอฟต์แวร์บนหลากหลายแพลตฟอร์ม

---

> 🚨 **MANDATORY UPDATE GOVERNANCE RULE (กฎบังคับการอัปเดตเอกสาร):**  
> **เอกสาร How-To และคู่มือการใช้งานทุกส่วนในไฟล์นี้ จะต้องได้รับการอัปเดตให้เป็นปัจจุบันอยู่เสมอ หากมีการเปลี่ยนแปลง แก้ไข หรือพัฒนาระบบเพิ่มเติมในโปรเจกต์** เพื่อให้แน่ใจว่าผู้ใช้งาน นักพัฒนา และ AI Agents สามารถใช้งานและดูแลระบบได้อย่างถูกต้องไม่คลาดเคลื่อน

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
   - [3.6 Hugging Face Spaces Deployment Platform CLI](#36-hugging-face-spaces-deployment-platform-cli)

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

### 1.5 การกดคำนวณผัง 9 ศาสตร์ย่อย (5-Branch Metaphysics)
ที่ด้านบนของแดชบอร์ด สามารถคลิกปุ่มคำนวณศาสตร์โหราศาสตร์ย่อยได้แก่:
- 🔮 **紫微斗數 (Zi Wei Dou Shu):** ดูผัง 12 ภพ, ดาวหลัก 14 ดวง และดาวสี่化
- ⚡ **奇門遁甲 (Qi Men Dun Jia):** ดูผัง 4 จาน 9 ตาราง (ดาว, ประตู, เทพ)
- 🌊 **大六壬 (Da Liu Ren):** ดู 3 การส่งผ่าน (三傳) และ 4 บทเรียน (四課)
- ☯ **易經六爻 (I Ching):** ดูฉักกะหลัก-ฉักกะเปลี่ยน และ 6 ลายเส้นพร้อม 6 สัตว์มงคล
- 🏯 **玄空風水 (Xuan Kong):** ดูผังดาวเหินยุค 9 แบบ 9 ตาราง (ดาวประธาน, ดาวนั่ง, ดาวหัน)
- 📅 **擇吉 (Ze Ji):** ดูฤกษ์ยามมงคล 12 เทพผู้ตรวจการ และกิจกรรมที่ควร/ไม่ควรทำ
- 🐘 **โหราศาสตร์ไทย & ภารตวิทยา:** ดูลัคนาสุริยยาตร์, ดาวศิริ/กาลกิณี, มหาทักษา 8 เทวดา และนักษัตร 27 ดารา
- 🌌 **โหราศาสตร์สากล & ยูเรเนียน:** ดูตำแหน่งดาวเคราะห์สากล, ดาวทิพย์ 8 องค์ และจุดอิทธิพลสะท้อน (Midpoint)
- 🔢 **สัตตเลข 7 ฐาน & เลขศาสตร์:** ดูตารางสัตตเลข 4 แถว 7 ฐาน และผลรวมเลขศาสตร์ Chaldean

---

### 1.6 การใช้งาน OpenAPI Interactive API Documentation (/docs, /redoc)
ระบบรองรับเอกสารสเปก API แบบตอบโต้ได้เพื่อให้นักพัฒนาและแอปพลิเคชันภายนอกทดลองเรียกใช้งาน API:
- **📘 Swagger UI Interactive Documentation (`http://localhost:8000/docs`):** ทดลองส่ง Request, กรอกตัวแปร JSON และรับ Response สดๆ บนเบราว์เซอร์
- **📕 ReDoc Schema Explorer (`http://localhost:8000/redoc`):** อ่านสเปก OpenAPI Schema แบบเต็มสำหรับการนำไปสร้าง Client Code / SDK
- **⚙️ OpenAPI JSON Specification (`http://localhost:8000/openapi.json`):** สเปก OpenAPI 3.1.0 ในรูปแบบ JSON สำหรับนำไป Import เข้า Postman หรือ Insomnia

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

### 3.6 Hugging Face Spaces Deployment Platform CLI
**การสั่งงานจัดส่งโค้ดและแอปพลิเคชันขึ้น Hugging Face Spaces (Static Edge CDN & Docker):**
```bash
# 1. ตรวจสอบ Payload Audit และ Publish ขึ้น Hugging Face Static Space (0% CPU Quota / 24/7 Unlimited Uptime)
python3 scripts/publish_space_hf.py --sdk static

# 2. ตรวจสอบสถานะการเชื่อมต่อสด (Live Health Check)
python3 scripts/publish_space_hf.py --check-health

# 3. ทดสอบ Payload Audit แบบ Dry-Run (ไม่เปลี่ยนแปลงไฟล์บน Cloud)
python3 scripts/publish_space_hf.py --dry-run
```

**ลิงก์ใช้งานระบบบน Hugging Face Static Edge CDN:**
- 🔮 **Main Dashboard**: `https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html`
- 🔐 **Admin Panel**: `https://pphothidaen-horoconsultant-core-backend.static.hf.space/admin.html`
- 🔬 **HITL Review Studio**: `https://pphothidaen-horoconsultant-core-backend.static.hf.space/hitl.html`

---

### 🌐 3.7 Production Deployment Options & Platform Research Matrix

ตารางสรุปผลวิจัยและทางเลือกในการนำบริการไปติดตั้งบนระบบ Production เพิ่มเติม:

| Platform | Deployment Type | Suitable Use Case | Latency (TH) | Cost & SLA Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Hugging Face Static Edge CDN** | Frontend UIs (`sdk: static`) | Web UIs, Admin Panel, HITL Studio | Global Edge (< 20ms) | Zero Cost, 24/7 Unlimited Uptime, No Quota Limit |
| **Fly.io Micro-VMs (`fly.toml`)** | Docker Container (`Dockerfile.hf`) | FastAPI API + Rust Math (Singapore `sin`) | Ultra-Low (< 30ms) | $5 Free Monthly Credit (3x 256MB Micro-VMs) |
| **Hugging Face Spaces Docker** | Full Backend Container (`sdk: docker`) | FastAPI API + Rust Fast Math + FAISS | Mid (~200ms US) | Free Tier (16GB RAM, 2 vCPU Container) |
| **Vercel Edge Network** | Gateway Rewrites (`vercel.json`) | Global Edge Proxy & Reverse Proxy | Global Edge (< 20ms) | Free Tier (Unlimited Static & Serverless) |
| **Render.com / Railway.app** | Docker Web Service (`Dockerfile.hf`) | Full-stack FastAPI Production Container | Mid (~150ms) | Low Cost ($5/mo), Auto SSL & Custom Domain |
| **Kaggle GPU Accelerator** | GPU Fine-Tuning Notebook (`T4 Machine`) | LLM Fine-Tuning & Model Weight Fusion | Batch Pipeline | Free 30h/week Nvidia T4 GPU |

### 🛠️ 3.8 การสั่งงานคำสั่ง Deploy และ Sync Secrets ไปยังแต่ละ Platform

#### 🔑 คำสั่งซิงค์ Secrets ไปทุก Platform ในคำสั่งเดียว (Automated Multi-Cloud Secrets Sync):
```bash
# รันสคริปต์อัตโนมัติเพื่อซิงค์ ENV & Secrets ไปยัง Fly.io, Vercel และ Hugging Face
bash scripts/setup_production_secrets.sh
```

#### 🚀 การจัดส่งขึ้น Fly.io (Singapore Region `sin`):
```bash
# 1. ติดตั้ง Fly CLI และ Login
brew install flyctl
fly auth login

# 2. Deploy ผ่านไฟล์ fly.toml (targeting Singapore region < 30ms latency)
fly launch --config fly.toml --no-deploy
fly deploy
```




