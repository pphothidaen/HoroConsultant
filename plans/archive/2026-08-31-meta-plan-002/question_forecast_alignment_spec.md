# 📋 Requirements & Forecast Alignment Specification: 6-Domain Question Benchmark & Expected Answer Criteria

**Project:** HoroConsultant — Computational Metaphysics Engine  
**Lead Agent:** Master Orchestrator (`orchestrator`) & Business System Analyst (`business_analyst`)  
**Status:** APPROVED; implementation evidence complete, release handoff externally blocked
**Last Updated:** 2026-08-21 14:16 (UTC+7)
**Ticket disposition:** Benchmark and prompt/debate routing are closed under `TICKET-META-004`; the only remaining release gates are `TICKET-META-005`/`006` in [`PROJECT_TASKS.md`](../PROJECT_TASKS.md).

---

## 1. 🔍 Audit Findings: Requirement vs Prediction Alignment

### 1.1 การประเมินความสอดคล้องระหว่างคำถามผู้ใช้ (User Query) กับบทพยากรณ์ (Astrological Forecast)
จากการตรวจสอบโครงสร้างความต้องการ (Requirements Audit) และระบบประมวลผลคำทำนาย Multi-Branch Metaphysics Engine พบว่า:

1. **จุดแข็งที่มีในระบบ (Strengths):**
   - มี Pure Python Engine ในการคำนวณตำแหน่งดวงชะตาเชิงกลศาสตร์ดาราศาสตร์ (Deterministic Astronomical Math) ทั้ง 10 สายวิชา (BaZi, Zi Wei, Qi Men Dun Jia, Da Liu Ren, I Ching, Xuan Kong, Ze Ji, Thai-Vedic 10-Lagna, Western/Uranian, Satta-Lek Numerology)
   - มีระบบ Multi-Agent Peer Debate (`project/core/multi_agent_debate.py`) ดึงมุมมองจาก 8 ปรมาจารย์สายวิชา พร้อมอ้างอิงคัมภีร์คลาสสิก (滴天髓, 子平真詮, 煙波釣叟歌, 周易, 協紀辨方書)
   - มี Prediction Validator Agent (`project/validator.py`) สอบทานความถูกต้องของกำลังธาตุ (Day Master), ปฏิกิริยากิ่งดินลำต้นฟ้า (Stem/Branch Interactions) และเวลาเกิดจริง (True Solar Time)

2. **ประเด็นที่ต้องเพิ่มความเข้มงวด (Areas for Enhancement):**
   - บทพยากรณ์ดวงชะตาทั่วไปมักเน้นภาพรวมพื้นดวงชะตา (Natal Chart) หากผู้ใช้ถามคำถามที่มีประเด็นเน้นย้ำเฉพาะเจาะจง (Focus Question) เช่น การเลือกตัดสินใจย้ายงาน, การเปิดบริษัทใหม่, หรือดวงสมพงษ์หุ้นส่วน ระบบต้อง **บังคับโฟกัสและตอบตรงประเด็น (Direct Focused Answering)** ไม่ถูกกลืนหายไปในคำทำนายภาพรวม
   - ต้องเพิ่ม **ชุดคำถามเพิ่ม (Benchmark Questions)** พร้อม **ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)** เพื่อให้ระบบและ Gemini External Validator ใช้เป็นเกณฑ์ในการวัดผลความสอดคล้อง 100%

---

## 2. 🎯 ชุดคำถามเน้นย้ำ 6 หมวดหลัก (6-Domain Question Benchmark) & ความคาดหวังในชุดคำตอบ

### หมวดที่ 1: การงานและการลงทุนธุรกิจ (Career, Promotion & Business Strategy)

#### ❓ คำถามทดสอบ (Benchmark Question 1.1)
> *"ในปี 2026 ชะตากำลังอยู่ในช่วงเปลี่ยนงาน ย้ายสายงาน หรือควรเปิดธุรกิจของตัวเองดี? และเดือนไหนคือช่วงจังหวะทอง?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** ต้องฟันธงเปรียบเทียบระหว่าง "การเป็นลูกจ้าง/ย้ายสายงาน" กับ "การเป็นเจ้าของธุรกิจ" พร้อมระบุเดือนมงคล (เดือนที่ดาว/ธาตุหนุน) และเดือนต้องระวังชะตาชง
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **BaZi:** วิเคราะห์กำลังดาว官星/七殺 (การงาน/ยศตำแหน่ง) เทียบกับดาว食傷/財星 (ความคิดสร้างสรรค์/โชคลาภธุรกิจ) ว่าธาตุใดเป็นธาตุให้คุณ (用神)
   - **Zi Wei:** ตรวจสอบภพ 官祿 (การงาน) และ 遷徙 (การเดินทาง/ย้ายที่) ร่วมกับดาวแปลงพลัง (化權 / 化忌)
   - **Qi Men Dun Jia:** ตรวจสอบตำแหน่งประตู開門 (ประตูเปิด/การงาน) และประตู生門 (ประตูเกิด/ธุรกิจ)
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** อ้างอิงหลักการจากคัมภีร์ *滴天髓* หรือ *子平真詮* พร้อมให้คำแนะนำแผนปฏิบัติเชิงรุก 3 ข้อ

---

### หมวดที่ 2: การเงิน โชคลาภ และทรัพย์สิน (Finance, Wealth & Investment)

#### ❓ คำถามทดสอบ (Benchmark Question 2.1)
> *"การเงินในปีนี้มีเกณฑ์โชคลาภลอยหรือได้ทรัพย์ใหญ่หรือไม่? และมีจุดรั่วไหลของเงินคงค้างในเรือนชะตาตรงไหน?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** แยกแยะชัดเจนระหว่าง "โชคลาภลอย (Speculative/Windfall Wealth)" กับ "ลาภตรงจากการทำงาน (Earned Wealth)" และระบุจุดรั่วไหลทางการเงิน
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **BaZi:** วิเคราะห์ดาว偏財 (ลาภลอย) vs 正財 (ลาภตรง) และตรวจดูดาว劫財 (ตัวขโมยทรัพย์/จุดเงินรั่ว)
   - **Zi Wei:** ตรวจสอบภพ 財帛 (การเงิน) และภพ 兄弟/奴僕 (เพื่อนฝูง/หุ้นส่วนที่อาจดึงเงินออก)
   - **Uranian / Western:** ตรวจจุดอิทธิพลสะท้อนศูนย์ลิขิต Jupiter / Kronos / Cupido vs Hades / Vulkanus
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** แนะนำกลยุทธ์บริหารการเงินและการแปลงเงินสดเป็นสินทรัพย์ถาวรตามธาตุให้คุณ

---

### หมวดที่ 3: ความรัก หุ้นส่วน และความสัมพันธ์ (Love, Marriage & Business Partnership)

#### ❓ คำถามทดสอบ (Benchmark Question 3.1)
> *"คนที่เพิ่งเข้ามาคบหาหรือหุ้นส่วนธุรกิจคนนี้ สอดคล้องดวงชะตา (ดวงสมพงษ์) หรือไม่? มีเกณฑ์ขัดแย้งหรือหลอกลวงในอนาคตหรือไม่?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** ระบุระดับความสมพงษ์ (Compatibility Index) ชี้แจงจุดเสริมและจุดเสี่ยงข้อขัดแย้งในสัญญาร่วมกัน
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **BaZi:** ตรวจสอบปฏิกิริยาภาค 支 (Branch Interaction): ฮะ (เหอ - 六合/三合) หรือ ชง (ภาคราม - 六沖/相害) ระหว่างเสาวันเกิด (Day Pillar / 夫妻宮)
   - **Zi Wei:** ตรวจสอบภพ 夫妻 (คู่ครอง) และภพ 奴僕/事業 (หุ้นส่วน/บริวาร)
   - **I Ching Divination:** ตรวจสอบกว้าอี้จิงและญาติทั้งห้า (五親 - 妻財 / 兄弟)
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** ให้คำแนะนำในการกำหนดเงื่อนไขทางสัญญาและแนวทางการปรับความเข้าใจตามหลักจิตวิทยาโหราศาสตร์

---

### หมวดที่ 4: สุขภาพ อุบัติเหตุ และเคราะห์ยาม (Health, Longevity & Accident Hazards)

#### ❓ คำถามทดสอบ (Benchmark Question 4.1)
> *"ดวงชะตามีเกณฑ์เจ็บป่วยหนัก เลือดตกยางออก หรือสภาวะอารมณ์ดิ่งในช่วงปีนี้หรือไม่? ควรป้องกันหรือเสริมสุขภาพอย่างไร?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** ระบุกลุ่มอวัยวะที่ต้องระมัดระวังเป็นพิเศษ และระบุช่วงเดือนที่มีสภาวะเสี่ยงสูง
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **BaZi 5 Elements:** วิเคราะห์ธาตุที่ล้นเกิน (太過) หรือพิการขาดแคลน (不及) (เช่น ธาตุไม้=ตับ/สายตา, ธาตุไฟ=หัวใจ/ความดัน, ธาตุดิน=ม้าม/กระเพาะ, ธาตุทอง=ปอด/ลำไส้ใหญ่, ธาตุน้ำ=ไต/ระบบสืบพันธุ์)
   - **Thai-Vedic 10-Lagna:** ตรวจดาวกาลกิณีเสวยอายุ และดาวอริ/มรณะ/พยายะ
   - **Ze Ji & Duty Officers:** ตรวจสอบวันไท่ส่วยชง (歲破) และยามทุศีล
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** แนะนำกิจกรรมส่งเสริมสุขภาพเชิงป้องกัน และการทำบุญบริจาคเลือด/ช่วยเหลือโรงพยาบาลตามคติโหราศาสตร์

---

### หมวดที่ 5: ฤกษ์ยามมงคลและการดำเนินการสำคัญ (Auspicious Date & Action Timing - Ze Ji)

#### ❓ คำถามทดสอบ (Benchmark Question 5.1)
> *"ต้องการเลือกวันเปิดร้านใหม่/ขึ้นบ้านใหม่ ในไตรมาสที่ 3 ของปี ควรเลือกวันยามใดที่ส่งเสริมดวงชะตาเจ้าของงานมากที่สุด?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** ให้รายการวันและยามมงคลที่ดีที่สุด พร้อมให้คะแนนดาวความมงคล (1-5 ดาว)
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **Ze Ji Imperial Calendar:** คำนวณเทพ 12 องค์ (建除十二神: 成日/開日/滿日) หลีกเลี่ยงวัน 歲破 / 月破 / 四廢
   - **Qi Men Dun Jia:** เลือกจานหมุนยามมงคลประตู生門 (ประตูเกิด) และดาวมงคล (天輔/天心)
   - **Xuan Kong Flying Stars:** ปรับทิศทางรับดาว 9 ม่วงยุค 9 (2024-2043)
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** อ้างอิงคัมภีร์ *協紀辨方書* พร้อมลำดับขั้นตอนการเปิดงานมงคล

---

### หมวดที่ 6: การปรับสมดุลชะตาชีวิตและฮวงจุ้ย (Metaphysical Remediation & Feng Shui Alignment)

#### ❓ คำถามทดสอบ (Benchmark Question 6.1)
> *"ธาตุเจ้าตัวอ่อนแอ (身弱) ควรเสริมพลังงานด้วยสิ่งของ ทิศทาง สีกายภาพ และเบอร์โทรศัพท์มงคลอย่างไรให้เห็นผลจริง?"*

#### 🎯 ความคาดหวังในชุดคำตอบ (Expected Answer Criteria)
1. **การตอบตรงประเด็น (Direct Relevance):** ระบุองค์ประกอบเสริมดวงครบทั้ง 4 ด้าน (สี, ทิศ, วัตถุมงคล/หินธาตุ, ผลรวมตัวเลขมงคล)
2. **ตรรกะโหราศาสตร์ (Astrological Logic):**
   - **BaZi:** กำหนดธาตุให้คุณ (用神) และธาตุเสริม (喜神) อย่างเที่ยงตรง ปราศจากการเดา
   - **Numerology:** คำนวณฐานสัตตเลข 7 ฐาน 4 แถว และผลรวม Chaldean/Pythagorean Scoring ที่หนุนธาตุให้คุณ
   - **Feng Shui (Xiang Xue):** จัดวางทิศทางดาวซาน (山星) และดาวเสี่ยง (向星) ในยุค 9
3. **หลักฐานและคำแนะนำ (Evidence & Guidance):** อ้างอิงคัมภีร์ *青囊奧語* และหลักวิทยาศาสตร์พลังงานดาราศาสตร์

---

## 3. 📊 เกณฑ์การประเมินความสอดคล้อง (Evaluation Rubric: 100 Points Scale)

| หัวข้อประเมิน (Evaluation Metric) | น้ำหนักคะแนน | รายละเอียดและเกณฑ์การตรวจวัด |
| :--- | :---: | :--- |
| **1. Direct Relevance (ตอบตรงประเด็น)** | 30% | ตอบตรงตามเป้าหมายของคำถามผู้ใช้ ไม่หลุดประเด็น และไม่ใช้คำทำนายหรอยๆ ทั่วไป |
| **2. Astrological Logic Consistency (ความสอดคล้องทางตรรกะโหราศาสตร์)** | 30% | กำลังธาตุ (Day Master) และการวิเคราะห์ 10 สายวิชาไม่ขัดแย้งกันเอง หากมีความต่าง มีการนำเสนอผ่าน Orchestrator Debate |
| **3. Canonical Evidence (การอ้างอิงคัมภีร์และข้อมูลการคำนวณ)** | 20% | ระบุชื่อคัมภีร์คลาสสิก (滴天髓, 周易, 煙波釣叟歌 ฯลฯ) พร้อมตัวเลขและโครงสร้างดวงถูกต้อง |
| **4. Actionable Guidance (คำแนะนำเชิงรุกและการแก้ไขชะตา)** | 20% | ให้แนวทางปฏิบัติจริง 3-5 ข้อที่ผู้ใช้นำไปใช้ปรับชีวิต การงาน หรือฮวงจุ้ยได้ทันที |

---

## 4. 🔄 Agent Execution & Operational Routing Rules

1. **Orchestrator Agent (`orchestrator`):**
   - ทำหน้าที่กระจายงานและกำกับดูแลให้ทุก Domain Engine และ Prompt Template ปฏิบัติตามเกณฑ์ข้อ 2 และ 3 เคร่งครัด

2. **Business System Analyst Agent (`business_analyst`):**
   - ควบคุมและอัปเดตเอกสารสเปค `plans/question_forecast_alignment_spec.md`, `PROJECT_TASKS.md` และ `plans/plan.md` ให้ตรงกับระบบจริงเสมอ

3. **Developer Agent (`developer`):**
   - ปรับปรุง `project/core/prompt_manager.py` และ `project/core/multi_agent_debate.py` ให้รับค่า `user_query` และดึงประเด็นเน้นย้ำไปใส่ไว้ใน prompt หัวข้อคำทำนาย

4. **QA Tester & Prediction Validator (`qa_tester` / `validator`):**
   - ใช้งาน Gemini External Validator (`project/validator.py`) ในการตรวจประเมินคะแนนความตรงประเด็น (Confidence Score > 0.85)
