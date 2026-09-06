# Spark Capability Audit Matrix (gpt-5.3-codex-spark)

- วันที่: 2026-09-05
- เป้าหมาย: ยืนยันว่าการมอบงานยังคงอยู่แค่ 3 เส้นหลักด้านความปลอดภัย/ปล่อยระบบ และระบุส่วนที่ Spark ควร/ไม่ควรรับผิดชอบได้ชัดเจน

## สรุปผล 3 เส้นหลัก

1) Safety-only lane (ไม่พัฒนา feature)
- หลักฐาน: policy and route map + ticket context
- สถานะ: PASS
- อธิบาย:
  - Spark ถูกจำกัดที่ role `devops`, `code_reviewer` เท่านั้น
  - lane feature เช่น `developer`, `implementation`, `qa_tester` ไม่ได้รับ Spark model
  - `TICKET-SAFE-SPARK-QA-001` ใช้ `gpt-5.6-luna` เพื่อ governance regression ไม่ใช่ Spark

2) High-risk quality lane (effort/phase lock)
- หลักฐาน: policy config + regression tests
- สถานะ: PASS
- อธิบาย:
  - `gpt-5.3-codex-spark` จำกัด `effort` เป็น `high` เท่านั้น
  - จำกัด `phase` ที่รับได้เฉพาะ `qa`, `review`, `release`, `operations`
  - role/phase ที่ไม่ตรงถูก block โดย `validate_dispatch_decision`

3) Safety lane operations (release stability + security + evidence posture)
- หลักฐาน: roles definition + context packet + agent scopes
- สถานะ: PASS (policy level), INCOMPLETE (execution readiness)
- อธิบาย:
  - `devops` scope ครอบ env/deploy/release/rollback/incident triage/deployment gate
  - `code_reviewer` scope ครอบ pre-deploy safety audit, secret scan, READY_FOR_PROD gate
  - ยังไม่ execute lane จริงได้จนกว่าจะได้ external runtime evidence chain เต็มชุด

## สามารถมอบให้ Spark ได้ (Authorized)

- `TICKET-SAFE-SPARK-DEVOPS-001` (lane `TICKET-SAFE-SPARK-DEVOPS-001-L1`)
  - เงื่อนไขสำคัญ: role `devops`, phase `release`, effort `high`
  - ขอบเขตงาน: `release_gate_audit`, `rollback_integrity`, `pipeline_guard`

- `TICKET-SAFE-SPARK-CR-001` (lane `TICKET-SAFE-SPARK-CR-001-L1`)
  - เงื่อนไขสำคัญ: role `code_reviewer`, phase `qa`, effort `high`
  - ขอบเขตงาน: `predeploy_audit`, `ready_for_prod_gate`, `secret_scan`

## ไม่ควรมอบให้ Spark (Blocked / Not-in-scope)

- งาน feature หลัก/แนวพัฒนา API/logic (`developer`)
- งาน QA หลักที่ไม่ใช่ safety contract (`qa_tester` feature QA)
- `phase` นอก `qa|review|release|operations`
- `effort` นอก `high`
- งานที่ยังขาด external admission/probe/approval evidence (แม้จะ policy pass)

## Blockers ที่ยังเหลือก่อน execute จริง

- `DispatchDecision` v1 ที่ผูก ticket/lane และ context digest ใหม่ล่าสุด
- `scheduling_snapshot` สำหรับแต่ละ lane
- `RuntimeAdmissionV1` + `ActivationHealthEvidenceV1` (PASS/FAIL ต้องบอท)
- approval chain: `approval_grant` และ `approval-consume` ผูก owner/reviewer/session อย่างครบ
- `work_result`/schema-v2 receipt provenance ที่ผูกกับ native capability proof

## การตีความเชิง Design-vs-Execution

- สรุป: Spark สามารถ “ช่วยวิศวกรรมความปลอดภัยและปล่อยระบบ” ได้จริงในกรอบที่กำหนด แต่ยังไม่ควรถือว่าอัตโนมัติ ready to execute จนกว่าห่วงโซ่ evidence runtime จะครบและเชื่อม ticket/lane ได้.
