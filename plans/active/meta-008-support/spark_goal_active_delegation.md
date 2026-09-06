# Spark Safety Lane Delegation (Active)

- วันที่: 2026-09-05
- เป้าหมายหลัก: ใช้ `gpt-5.3-codex-spark` เฉพาะ safety lane เท่านั้น (no feature dev)

## Delegate binding (strict)

- เป้าหมาย 3 เส้นของ `gpt-5.3-codex-spark` (ชัดเจนและต้องไม่เปลี่ยนแปลง):
  - เส้น 1: เฉพาะ lane ความปลอดภัย/ปล่อยระบบ (`devops`, `code_reviewer`) เท่านั้น
  - เส้น 2: `effort=high` และ phase เฉพาะ `qa|review|release|operations`
  - เส้น 3: โฟกัสงานปลอดภัย (release stability / secret scan / pytest / HF static release evidence / release gate / rollback)

## งานที่ `gpt-5.3-codex-spark` ทำได้ทันที (authorized)

- ทำได้: lane `devops` และ `code_reviewer` ที่อยู่ใน safety context ที่ผูกชัดเจนกับ ticket/lane และ evidence bundle ตามด้านล่าง
- ทำได้: ทุกงานที่ต้องการ gate/release/review ระดับเสถียรภาพระบบ และ pre-deploy safety
- ไม่ควรทำ: feature implementation, API behavior change, planning/implementation phase dispatch, non-safety roles (`developer`, `qa_tester`, `ux_ui_designer`, `ui_visual_tester`, `business_analyst`, ฯลฯ)

## คำสั่งผู้ใช้ล่าสุดที่บังคับ

- `approve all lane` ถูกตีความเป็นการอนุมัติสาม lane safety workflow แล้วใน queue ปัจจุบัน
- ข้อจำกัดความปลอดภัยปิดเงื่อนไข: policy ยังทำหน้าที่ปิดการ route ที่ไม่ตรง role/phase/effort ทุกครั้งเสมอ

### 1) Safety Infrastructure Lane
- Ticket: `TICKET-SAFE-SPARK-DEVOPS-001`
- Lane: `TICKET-SAFE-SPARK-DEVOPS-001-L1`
- Owner role: `devops`
- Scope: policy enforcement / release gate / rollback integrity / deployment evidence
- Files: `.agents/AGENTS.md`, `.agents/agents/devops/*`, `docs/architecture/external-dispatch-platform-contract.md`, `HANDOFF.md`
- Acceptance criteria:
  - ชี้ว่านโยบาย `gpt-5.3-codex-spark` ใช้เฉพาะงาน devops/code_reviewer และ phase ที่อนุญาต
  - ยืนยัน `effort=high` + phase `qa|review|release|operations` ครอบคลุม packet นี้
  - ระบุข้อห้าม feature edit ภายใต้ Spark lane
  - แนวทาง release gate/rollback/integrity ชัดเจนและทำได้ภายใต้ policy

### 2) Safety Review Lane
- Ticket: `TICKET-SAFE-SPARK-CR-001`
- Lane: `TICKET-SAFE-SPARK-CR-001-L1`
- Owner role: `code_reviewer`
- Scope: pre-deploy safety checks / READY_FOR_PROD governance / secret/provenance rules
- Files: `.agents/agents/code_reviewer/*`, `project/core/code_reviewer.py`, `project/core/` audit-related docs
- Acceptance criteria:
  - ตำแหน่งงานยืนยันว่ามีหน้าที่ pre-deploy safety และ READY_FOR_PROD gate
  - มีข้อบังคับว่า secret scan, pytest, release evidence ผูกกับการอนุมัติ deploy
  - ยืนยันการรับงานเฉพาะ `effort=high` + phase `qa|review|release|operations`

### 3) Safety Verification Lane
- Ticket: `TICKET-SAFE-SPARK-QA-001`
- Lane: `TICKET-SAFE-SPARK-QA-001-L1`
- Owner role: `qa_tester`
- Scope: enforce role/phase/effort governance as regression proof
- Files: `tests/test_spark_model_governance.py`, `tests/test_multiagent_prompt_command.py`, `scripts/multiagent_prompt_command.py`
- Acceptance criteria:
  - unauthorized role/phase/effort ต้องถูกปฏิเสธแบบ fail-closed
  - authorized `role=devops|code_reviewer`, `phase=qa|review|release|operations`, `effort=high` ผ่าน

## กติกาคืนสรุปสำหรับการ delegate ถัดไป

- route/scope ต้องผูกกับ Ticket + Lane + Owner + Files ชัดเจน
- Spark ไม่รับงานที่เป็น feature implementation/lifecycle ปกติของ `developer`
- ทุกงานที่ delegate ต้องมี checkpoint สั้น ๆ: จุดเริ่ม/สิ้นสุด, คำสั่งหลัก, เงื่อนไข fail-closed

## ข้อจำกัดที่ยังยืนยันอีกครั้ง (no change)

- ไม่ delegate งาน `TICKET-DISPATCH-ACTIVATION-001` และ dependency ที่ยังมี blocker `TICKET-RELEASE-002` ต่อไปใน full set จนกว่าจะผ่าน security/platform admission
- งานโหมด feature ที่ไม่ใช่ `qa/review/release/operations` หรือไม่ใช่ effort high ยังคง blocked ตาม policy
