# Human-in-the-Loop Operating Guide

สถานะ: APPROVED สำหรับการใช้งานภายใน (ผู้ใช้อนุมัติ 2026-08-21); การอนุมัติ production ต้องมีผู้ตรวจที่ได้รับมอบหมาย

## เมื่อใดต้องส่งให้คนตรวจ

ส่งเข้า `/hitl/queue` และตรวจผ่าน `/hitl/backoffice` เมื่อมีเงื่อนไขใดเงื่อนไขหนึ่ง:

- `required_human_review=true`
- `conflict_detected=true` หรือมี `conflicting_domains`
- `force_human_review=true`
- routing status เป็น `QUEUED_FOR_HUMAN_REVIEW`
- `consensus_score < 0.75`
- คำตอบเกี่ยวข้องกับการแพทย์ กฎหมาย การเงิน ความปลอดภัย หรือการตัดสินใจที่ย้อนกลับไม่ได้

## ขั้นตอนที่แนะนำ

1. ผู้ตรวจเปิด `/hitl/backoffice` และเลือกเคสที่ยัง `pending` โดยจัดการ conflict ก่อนเคสทั่วไป
2. ตรวจคำตอบ AI เทียบกับ source metadata, calculation trace และคำตอบจาก domain specialists
3. ส่ง `approve`, `edit` หรือ `reject` พร้อม `reviewer`, `confidence_rating` (1–5), tags และ notes
4. คำตอบที่ `approve`/`edit` ต้องมี `human_answer` ที่อ่านได้และไม่มี PII ก่อน export
5. เรียก `/hitl/export` เพื่อสร้าง dataset พร้อม metadata; ห้ามนำรายการที่ไม่มี human decision เข้า training
6. เมื่อ approved/edited ครบ 50 รายการ ระบบจึงพิจารณา auto-finetune trigger; production training ต้องมี human approval แยกอีกครั้ง

## ผู้รับผิดชอบและการอนุมัติ

| งาน | ผู้รับผิดชอบ | หลักฐานที่ต้องเก็บ |
|---|---|---|
| Domain correctness | domain specialist | source IDs, calculation trace, notes |
| Safety/privacy | QA or reviewer | PII check, safety disposition |
| Dataset release | ML/DevOps owner | export metadata, dataset hash |
| Model promotion | release approver | benchmark delta, rollback decision |

## กติกาไม่ให้ระบบข้ามคนตรวจ

- ไม่ promote โมเดลจาก dataset ที่มี `missing_required_human_gate > 0`
- ไม่ถือ `confidence_score` ของ AI เป็น human approval
- เคส conflict หรือคะแนนต่ำต้องมีผู้ตรวจอย่างน้อยหนึ่งคน; เคส high-impact แนะนำสองคนและบันทึกผู้อนุมัติคนสุดท้าย
- เก็บ audit trail ของ decision, reviewer, timestamp, tags และ source metadata
- หากผู้ตรวจไม่แน่ใจ ให้ `reject` หรือคงสถานะ `pending` พร้อมเหตุผล แทนการ approve แบบคาดเดา

## Production gate

HITL ถือว่าพร้อมสำหรับ release เมื่อ scope audit รายงาน `pass_gate_check=true`, ไม่มี pending high-impact cases และมีหลักฐาน export/benchmark/rollback ครบถ้วน ผู้ดูแลระบบยังต้องแก้ Azure RBAC, canonical HF health, external CI และ authorized Playwright ก่อนปิด release tickets.
