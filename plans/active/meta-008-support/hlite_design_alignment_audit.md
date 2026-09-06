# Horo Lite Design Alignment Audit

- วันที่: 2026-09-05
- วัตถุประสงค์: ตรวจว่า `TICKET-HLITE-001`–`TICKET-HLITE-012` สอดคล้องกับงานออกแบบหรือไม่ และระบุจุดที่ `gpt-5.3-codex-spark` ควร/ไม่ควรดึงมาทำได้

## สรุปภาพรวม

- สถานะ ticket อ้างอิง: ทั้งหมดยังเป็น `READY (Awaiting Owner Authorization)` ใน `ATOMIC_TICKET`
- งานที่ตรวจพบจาก code base หลัก:
  - API หลัก `POST /api/v3/unified-reading` พร้อมจดทะเบียน router แล้ว
  - Core engine ทำ canonical topic ordering, consensus และ guardrail
  - มี timing/pattern outputs ที่ deterministic (`annual_timing_engine`, `past_pattern_calibrator`)
  - มีหน้า `public/lite.html` และ script `public/lite.js` สำหรับ render HITL, export, และ fallback

## Mapping ความสอดคล้องต่อ ticket

### TICKET-HLITE-001
- เนื้อหาโดยรวม: bootstrap/readiness ของ unified reading
- สถานะ ticket: `READY`
- สอดคล้องในงานรันไทม์: `YES` (endpoint/route มีอยู่)
- จุดค้าง: ไม่ได้เป็น DONE; ไม่มีหลักฐาน DoR/DoD และ test provenance ที่ชัดเจน

### TICKET-HLITE-002
- เนื้อหา: topic canonicalization / engine schema
- สถานะ: `READY`
- สอดคล้อง: `YES` (core engine enforce canonical topic IDs และ strict ordering)
- ความเสี่ยง: ต้องยืนยัน mapping สุดท้ายใน acceptance matrix

### TICKET-HLITE-003
- เนื้อหา: consensus matrix / confidence layer
- สถานะ: `READY`
- สอดคล้อง: `YES` (`project/core/consensus_matrix.py` แสดง logic หลัก)
- ความเสี่ยง: ต้องมี scenario test ที่ผูกกับ acceptance ของผู้ใช้

### TICKET-HLITE-004
- เนื้อหา: annual timing projection
- สถานะ: `READY`
- สอดคล้อง: `YES` (`annual_timing_engine.py` deterministic 12-month output)
- ความเสี่ยง: validation เอกสารผลลัพธ์เดือนสุดท้าย/ขอบเขตข้อมูล

### TICKET-HLITE-005
- เนื้อหา: past pattern calibration
- สถานะ: `READY`
- สอดคล้อง: `YES` (`past_pattern_calibrator.py` มีการคำนวณ/normalization)
- ความเสี่ยง: ต้องยืนยันว่าพารามิเตอร์ match spec เฉพาะ product

### TICKET-HLITE-006
- เนื้อหา: lite response rendering + technical basis
- สถานะ: `READY`
- สอดคล้อง: `PARTIAL`
- สอดคล้องบางส่วน:
  - `public/lite.js` มี technical basis/HITL hooks และ export
  - **ข้อขัดแย้งออกแบบที่สำคัญ**: มี fallback ข้อความสำหรับหัวข้อที่ไม่มีใน API (`fill missing topics...`) แล้ว render กล่อง `(fallback topic)` โดยอิงข้อความที่ผู้ใช้ไม่ใช่ข้อมูลจริงจาก backend โดยตรง
- ข้อเสนอ: ต้องมี policy ว่า fallback นี้อนุญาตหรือไม่ก่อนยืนยัน DONE

### TICKET-HLITE-007
- เนื้อหา: consent/privacy behavior ใน export
- สถานะ: `READY`
- สอดคล้อง: `YES` (มี consent/privacy toggle ใน `public/lite.js`)

### TICKET-HLITE-008
- เนื้อหา: unknown-hours / missing-time warning
- สถานะ: `READY`
- สอดคล้อง: `YES` (มีแจ้งเตือนเวลาไม่แน่นอน)

### TICKET-HLITE-009
- เนื้อหา: API schema/validation
- สถานะ: `READY`
- สอดคล้อง: `PARTIAL`
- หลักฐาน: มี schema ใน core และ router แต่ยังไม่เห็น evidence ที่จับคู่กับ DoD spec/negative test ครบ

### TICKET-HLITE-010
- เนื้อหา: regression tests / test coverage baseline
- สถานะ: `READY`
- สอดคล้อง: `PARTIAL`
- หลักฐาน: มี `tests/test_horo_lite_unified_reading.py` ชื่อ case อยู่ แต่ผลผ่าน/ผลลัพธ์ต้องยืนยันจาก run ใหม่ก่อนทำ DoD

### TICKET-HLITE-011
- เนื้อหา: rollout + feature flag / fallback handling
- สถานะ: `READY`
- สอดคล้อง: `PARTIAL`
- รายละเอียด: มี fallback route behavior ฝั่ง UI ที่ช่วยไม่ให้หน้าแตก แต่ยังขาดเอกสารกฎการทำงานเมื่อ fallback

### TICKET-HLITE-012
- เนื้อหา: operations + monitoring evidence (metadata/logging)
- สถานะ: `READY`
- สอดคล้อง: `UNKNOWN`
- ข้อสังเกต: ไม่พบไฟล์หลักฐาน monitoring/reliability ในชุดที่ตรวจในรอบนี้

## ระดับสามารถส่งต่อให้ `gpt-5.3-codex-spark`

- ส่งต่อได้ทันที: งานเชิงเอกสารที่ไม่ต้องตัดสินใจ architecture ใหม่, task-specific test file updates, และ patch เล็กที่อยู่ใน scope ชัดเจน (เช่น hardening ของ fallback policy)
- ส่งต่อไม่ควรทันที: งานที่ต้องมี approvals/owner auth, dependency unblock, หรือมีความเสี่ยงด้าน design mismatch (`HLITE-006`, `HLITE-009`, `HLITE-011`, `HLITE-012`)

## ข้อเสนอการเดินงาน

1. ยืนยัน DoR/DoD ของ `TICKET-HLITE-001`–`012` ใหม่โดยละเอียดก่อนส่งต่อ
2. แก้ประเด็น design risk ของ fallback topic ก่อนทำการ mark DONE
3. เติม coverage สำหรับ validation/failover paths (`HLITE-009`,`010`,`011`)
4. เพิ่ม evidence artifact แยก per ticket เพื่อให้ `ba_auditor` audit ได้แบบ deterministic

## สรุปสำหรับผู้มอบหมาย

- งานมีโครงสร้างหลักครบหลายส่วนแล้ว แต่เกือบทั้งหมดยังไม่อยู่ในสถานะ DONE
- `gpt-5.3-codex-spark` สามารถดึงงานเชิงปฏิบัติบางส่วนได้ (`frontend polish`, `test case alignment`, `policy/docs`) แต่ **ไม่ควรถูกใช้เป็นผู้รับงานทั้งหมด** จนกว่าจะคลียร์ blockers และ owner authorization ของทุก ticket
