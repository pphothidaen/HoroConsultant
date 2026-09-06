# Delegate Round 1 (Spark Readiness Run)

- สร้างวันที่: 2026-09-05
- เป้าหมาย: แนะนำงานที่ `gpt-5.3-codex-spark` สามารถรับมือแบบ low-risk และงานที่ต้อง hold

## บทสรุป

- ไม่ควรส่งมอบงานทั้งก้อน
- ส่งมอบได้เฉพาะงานย่อยที่เป็นเอกสาร/เงื่อนไขนโยบาย/เสถียรภาพหน้าจอที่ไม่พึ่ง dependency ป้องกันการปล่อย

## Delegate-Ready (Spark สามารถเริ่มทำได้)

1. [Ticket] `TICKET-HLITE-006` (ส่วน fallback policy hardening)
   - งานย่อย: ตกลง policy ว่า fallback topic อนุญาตหรือไม่, ปรับ copy/ข้อความเพื่อไม่สื่อว่าข้อมูลเป็นความจริงจาก backend เมื่อเป็น fallback
   - เส้นทางไฟล์: `public/lite.js`

2. [Ticket] `TICKET-HLITE-009` (ส่วน schema documentation)
   - งานย่อย: ทำ schema matrix ที่แมป canonical fields -> response contract + error behavior
   - เส้นทางไฟล์: `project/core/unified_reading_engine.py`, `project/routers/unified_reading_router.py`, `tests/test_horo_lite_unified_reading.py`

3. [Ticket] `TICKET-HLITE-010`
   - งานย่อย: เพิ่ม/ปรับข้อความเคสทดสอบที่คาดหวังให้ตรงกับพฤติกรรมจริง (ไม่ต้องรันทดสอบในรอบนี้)
   - เส้นทางไฟล์: `tests/test_horo_lite_unified_reading.py`

4. [Ticket] `TICKET-HLITE-011`
   - งานย่อย: เอกสารและ implementation note ของ fallback route/roll-forward behavior
   - เส้นทางไฟล์: `public/lite.js`, `public/lite.html`

5. [Ticket] `TICKET-HLITE-012`
   - งานย่อย: draft monitoring evidence template (เชิงเอกสาร) สำหรับ runtime evidence ก่อนลง production
   - เส้นทาง: `plans/` และไฟล์ evidence ledger ใหม่ตามรูปแบบทีม

## Hold (ไม่ควร delegate ขณะนี้)

1. `TICKET-DISPATCH-ACTIVATION-001` subtask `001-B` onward
   - สาเหตุ: ยังมี blocker security/platform ทำให้ไม่ผ่าน exact capability/grant flow

2. `TICKET-HLITE-001`–`004` / `005` / `007` / `008`
   - สาเหตุ: หลักฐาน acceptance ยังไม่อยู่ในสถานะ DONE และต้องมี owner authorization ก่อนปล่อย production

3. `TICKET-RELEASE-002`
   - สาเหตุ: ยังถูกบล็อคโดย dependency chain `TICKET-QA-ADMIN-CATALOG-SUPERSESSION-001`, `TICKET-TRIAGE-API-INDEX-VERCEL-REWRITE-001`, `TICKET-HARDEN-ADMIN-SESSION-STORAGE-001`, `TICKET-QA-ADMIN-SESSION-STORAGE-MIRROR-001`

## เงื่อนไขที่ต้อง clear ก่อนส่งต่อ full set ต่อไป

- Context security review ผ่าน (`001-B`)
- External platform owner ให้น้ำหนักให้กับ `spawn_agent` exact model และ native provider whitelist
- Evidence chain ของ `001-C` ถึง `001-G` เสร็จ
- ทำ checklist ใหม่ใน `plans/spark_go_no_go_checklist.md` (เช่นนี้) ทุกครั้งเมื่อ unblock เดินหน้า
