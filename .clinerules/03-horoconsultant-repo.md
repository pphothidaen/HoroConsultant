# HoroConsultant governance

- ทุก ticket: test-first — commit 1 = tests + manifest (`plans/test_provenance/`),
  commit 2 = source; แยก source/test ออกจากกันเด็ดขาด (pre-commit guard)
- `ticket_id` ใน manifest ต้องขึ้นต้น `TICKET-`; `baseline_parent` = HEAD จริง;
  `supersedes` ต้องเป็น full SHA
  - guard: `scripts/test_provenance_guard.py` — `MANIFEST_TICKET_INVALID`,
    `MANIFEST_PARENT_INVALID`, `MANIFEST_SUPERSEDES_INVALID`, `BASELINE_PARENT_MISMATCH`
- รัน: `.venv/bin/python -m pytest <target> -q` (venv = Python 3.11)
- ก่อน release: `.venv/bin/python scripts/sync_ai_agent_ecosystem.py --check` ต้อง exit 0
- hooks ของ repo นี้: `core.hooksPath=.githooks` — commit subject ต้องขึ้นต้น `KAN-<id>:`
- ทุก commit: `KAN-<id>: <description>` — ยืนยัน ticket มีจริงด้วย
  `twg jira workitem get KAN-<id>` ก่อน cite เสมอ
  (ห้าม `source ~/.zshrc`: `twg` auth จาก `~/.config/twg/auth.conf` ไม่ต้องใช้ env)
- ห้าม print/log secret (G1 Zero-Token-Leak) — ดึง secret สดด้วย Doppler
  หรืออ่านจาก `.env` ที่ถูก gitignore แล้วเท่านั้น
- fail-closed เสมอ: gate ที่อ่าน Jira/external oracle ไม่ได้ ต้องไม่ตีความว่า "ผ่าน"