# Spark Safety Lane Dispatch Queue (Active)

- วันที่: 2026-09-05
- เป้าหมาย: รักษา `gpt-5.3-codex-spark` เฉพาะสายความปลอดภัย/ปล่อยระบบ
- กติกาแข็ง: role-phase-effort ของ Spark ต้องผ่าน policy เท่านั้น (`devops|code_reviewer`, `qa|review|release|operations`, effort `high`)
- สถานะ delegations ล่าสุด: `USER_APPROVED_ALL_LANES`
- อนุมัติจากผู้ใช้: `approve all lane`

## Status Snapshot

- DevOps safety lane: `[USER_APPROVED]` (dry-run render-pass; route/role/effort/phase policy บล็อกจุดนอกสเปก)
- Code Reviewer safety lane: `[USER_APPROVED]` (dry-run render-pass; route/role/effort/phase policy บล็อกจุดนอกสเปก)
- QA governance lane: `[USER_APPROVED]` (รอ queue ขนานตามธรรมชาติ, ไม่ใช้ Spark)

- หลักฐานการยืนยัน policy ล่าสุด (local, dry-run + regression):
  - `tests/test_spark_model_governance.py` (ผ่านแล้ว): ผูก `gpt-5.3-codex-spark` กับ roles `devops|code_reviewer` และ phases `qa|review|release|operations` เท่านั้น; ปฏิเสธ phase planning/implementation และ unauthorized roles
  - `tests/test_multiagent_prompt_command.py -k spark` (ผ่านแล้ว): policy validation ถูกบังคับแบบ fail-closed สำหรับ model-roles-effort/phase mismatch และ request/effective mismatch
  - สปอตเช็ค offline โดยตรง (ผ่าน): `bad_phase`, `bad_role`, `bad_effort` ถูกบล็อก, `good_devops`, `good_code_reviewer` ผ่านด้วย `validate_dispatch_decision`

## Objective-alignment audit (3 lanes, by evidence)

1) `devops`/`code_reviewer` เท่านั้น (ไม่ใช่ feature dev):
  - Policy: `.agents/config/multiagent_model_policy.yaml`
  - Route map: `.agents/config/multiagent_prompt_command.yaml`
  - Governance contract: `tests/test_spark_model_governance.py`, `tests/test_multiagent_prompt_command.py`
  - Status: **PASS (local policy/test enforcement)**

2) Risk-control high-effort + phase strict (`qa|review|release|operations`):
  - Policy: `allowed_phases`, `efforts` กำหนดไว้ใน policy
  - Proof: dry-run/block tests (bad_phase, bad_role, bad_effort) และ tests in the two suites
  - Status: **PASS (local policy/test enforcement)**

3) ทำงานแบบ safety lane: release stability / secret scan / pytest / HF static release evidence / docs/pipeline / rollback:
  - Packet 1 owner scope: `.agents/AGENTS.md`, `.agents/agents/devops/*`, `HANDOFF.md`, `docs/architecture/external-dispatch-platform-contract.md` และ deploy/release/rollback artifacts
  - Packet 2 owner scope: `project/core/code_reviewer.py`, `project/core/` audit docs, `hf-static-release-verification` contracts
  - Packet 3 owner scope: governance test contracts only, no Spark execution
  - Status: **PARTIAL (งานสืบเสาะและแผนรับรองยังคงถูกวางไว้, ยังไม่ execute ตาม Rule 11 chain)**

- สถานะ Execution-Readiness จริง: การ `--execute` ยังไม่สามารถรันใน lane นี้ได้จนกว่าจะมี `DispatchDecision` schema v2 + Rule 11 `scheduling_snapshot` + runtime probe/approval artifacts ที่ผูกกับ ticket ของ lane ตามฟอร์มระบบ (root session proof + quota evidence)

## Dispatch Packet 1 — DevOps Safety + Release Gates

- Ticket: `TICKET-SAFE-SPARK-DEVOPS-001`
- Lane ID: `TICKET-SAFE-SPARK-DEVOPS-001-L1`
- Role: `devops`
- Requested model: `gpt-5.3-codex-spark`
- Requested effort: `high`
- Requested phase: `release`
- Approved context digest: `0000000000000000000000000000000000000000000000000000000000000000`
- Touched paths (read/plan/write): `.agents/AGENTS.md`, `.agents/agents/devops/*`, `docs/architecture/external-dispatch-platform-contract.md`, `HANDOFF.md`
- Ownership: safety lane artifacts, release gate posture, rollback/integrity checks
- Deliverables:
  - `devops` lane evidence bundle อธิบายว่าการใช้ Spark ถูกจำกัดเฉพาะ release safety tasks
  - ระบุข้อบังคับว่า ไม่ใช้ Spark ใน implementation lane ของ feature
  - ผูก deliverable กับ env/deploy/release/rollback และ incident triage proof (docs + release gate + HF static checks)
  - ระบุเงื่อนไขปิด deployment gate เมื่อพบความเสี่ยงเสถียรภาพ/secret/compliance ล้มเหลว
  - รายงานสิ่งที่ยังต้องรอ (platform whitelist/DSG-009A/B) โดยไม่สับสนกับ local proof
- Status: `[APPROVED]` pending execution

## Dispatch Packet 2 — Code Reviewer Safety Audit

- Ticket: `TICKET-SAFE-SPARK-CR-001`
- Lane ID: `TICKET-SAFE-SPARK-CR-001-L1`
- Role: `code_reviewer`
- Requested model: `gpt-5.3-codex-spark`
- Requested effort: `high`
- Requested phase: `qa`
- Approved context digest: `0000000000000000000000000000000000000000000000000000000000000000`
- Touched paths (read/plan/write): `.agents/agents/code_reviewer/*`, `project/core/code_reviewer.py`, `project/core/` audit-related docs
- Ownership: pre-deploy safety audit, READY_FOR_PROD gate, secret scan, pytest/hardening posture, HF static evidence expectations
- Deliverables:
  - สรุป audit checklist ที่ enforce ว่า Spark ทำงานใน safety lane เท่านั้น
  - ยืนยัน ready-to-run condition ของ release stop conditions, rollback pre-checks, และความสอดคล้องของ README/pipeline rules
  - อัปเดต/ยืนยัน readiness condition สำหรับ release approval
- Status: `[APPROVED]` pending execution

## Dispatch Packet 3 — QA Governance Regression for Spark Constraints

- Ticket: `TICKET-SAFE-SPARK-QA-001`
- Lane ID: `TICKET-SAFE-SPARK-QA-001-L1`
- Role: `qa_tester`
- Requested model: `gpt-5.6-luna` (do not run Spark)
- Requested effort: `medium`
- Requested phase: `qa`
- Approved context digest: `0000000000000000000000000000000000000000000000000000000000000000`
- Touched paths (read/plan/write): `tests/test_spark_model_governance.py`, `tests/test_multiagent_prompt_command.py`, `scripts/multiagent_prompt_command.py`
- Ownership: ทดสอบ governance fail-closed ของ role/phase/effort ที่เกี่ยวกับ Spark โดยไม่แตะ lane นี้ด้วย Spark
- Deliverables:
  - ยืนยัน test case ว่า unauthorized role/phase ถูก reject อย่างชัดเจน
  - ยืนยัน authorized lane (`devops|code_reviewer` + `qa|review|release|operations` + high) ผ่าน
- Status: `[APPROVED]` pending execution

## Hard Hold (No-Go until unblocked)

- `TICKET-DISPATCH-ACTIVATION-001` และ dependency chain ที่ยังกดดัน platform capability
- `TICKET-RELEASE-002` และทุก upstream dependency ที่ยังบล็อก

## Execution readiness

- `lane_id` ใน `.agents/context/tickets` ต้องถูกประกาศให้ตรงกับทั้ง 3 packet
- `approved context digest` ต้องคำนวณได้โดย `scripts/resolve_agent_context.py` ก่อนรัน
- `multiagent_prompt_command` รองรับ role ที่มอบ: `devops`, `code_reviewer` (`gpt-5.3-codex-spark`) และ route ถูกอัปเดตเสร็จใน `.agents/config/multiagent_prompt_command.yaml`
- Readiness proofs ที่ยังขาดก่อน execute (เช็คเป็นราย ticket):
  - `DispatchDecision` v1 (signed + ticket/lane-bound)
  - `scheduling_snapshot` (Rule 11) ที่ fresh และตรง `ticket/lane`
  - `approval_grant` + `approval-consume` ตอบโจทย์ session + owner/reviewer
  - `RuntimeAdmissionV1` health evidence (must be PASS)
  - `ActivationHealthEvidenceV1` + `work_result` receipts (schema v2)

## Rule Enforcement Reminder

- Any request to run Spark outside these dispatch packets must be treated as `[ERROR] BLOCKED`.
- Any request to route Spark to `developer`, `ba_intake`, `ba_auditor`, `ux_ui_designer`, `ui_visual_tester`, หรืองาน feature must be denied.
- Any request to route Spark with phase outside `qa|review|release|operations` must be denied.
- Any request to route Spark with effort ไม่ใช่ `high` must be denied.

## Safety lane non-feature constraint (execution intent guard)

- packet 1 and packet 2 are **read/plan/write only** for env/deploy/rollback/safety-gate artifacts, not feature implementation files.
- packet 3 is **test-and-contract proof only** and must not dispatch Spark.

## Latest local verification log

- `2026-09-05T09:43:20Z`
  - `python3 -m pytest -q tests/test_spark_model_governance.py tests/test_multiagent_prompt_command.py -k "spark" -q`
    - Result: **PASS** (`17` tests from both suites relevant to governance)
  - Policy spot-check via `validate_dispatch_decision`:
    - `good_devops_review` = PASS (quality_floor=3, model_quality_rank=3)
    - `good_code_reviewer_ops` = PASS (quality_floor=3, model_quality_rank=3)
    - `bad_role` (`developer`) = BLOCKED
    - `bad_phase` (`implementation`) = BLOCKED
    - `bad_effort` (`low`) = BLOCKED
  - `python3 scripts/resolve_agent_context.py` for each ticket/lane (all three) returns `approved_context_sha256=000..0`, expected with current governance design while closure/effective actions/phase/role are correct.

## Local objective compliance snapshot (3 lines)

- 2026-09-05T10:15:12Z
  - เส้น 1 (Safety lane only): PASS
    - `gpt-5.3-codex-spark` ถูกจำกัดเฉพาะ `allowed_roles=[devops, code_reviewer]`
    - lane `TICKET-SAFE-SPARK-DEVOPS-001` และ `TICKET-SAFE-SPARK-CR-001` ใช้ role/phase/scope safety จริง
    - `qa_tester` lane ใช้ `gpt-5.6-luna` เท่านั้น (ไม่ใช้ Spark)
  - เส้น 2 (risk-quality, phase-effort): PASS
    - `allowed_phases=[qa,review,release,operations]`
    - `efforts` ของ Spark จำกัด `high` เท่านั้น
    - `tests/test_multiagent_prompt_command.py` มี regression สำหรับ unauthorized role/phase และ authorized role+phase
  - เส้น 3 (safety lane, non-feature): PASS (policy/readiness level)
    - สถานีงาน `devops` ครอบคลุม env/deploy/release/rollback/incident triage
    - สถานีงาน `code_reviewer` ครอบคลุม pre-deploy audit / READY_FOR_PROD
    - ยังไม่ถึง execution ของ lane เพราะยังขาด external runtime evidence chain

## Execution blockers (remaining)

- `DispatchDecision` v1 + matching `lane_id` + approved context digest
- `scheduling_snapshot` bound to packet and ticket
- `RuntimeAdmissionV1` + `ActivationHealthEvidenceV1` proofs (PASS)
- one-use `approval_grant` + `approval-consume` chain bound to owner/reviewer/session
- platform-native model capability + effective-model proof (still external-blocked)
