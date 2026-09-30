# HoroConsultant governance

- ทุก ticket: test-first — commit 1 = tests + manifest (plans/test_provenance/),
  commit 2 = source; แยก source/test ออกจากกันเด็ดขาด (pre-commit guard)
- ticket_id ใน manifest ต้องขึ้นต้น "TICKET-"; baseline_parent = HEAD จริง;
  supersedes ต้องเป็น full SHA
  - guard: scripts/test_provenance_guard.py (MANIFEST_TICKET_INVALID,
    MANIFEST_PARENT_INVALID, MANIFEST_SUPERSEDES_INVALID, BASELINE_PARENT_MISMATCH)
- รัน: .venv/bin/python -m pytest <target> -q   (venv = Python 3.11)
- ก่อน release: .venv/bin/python scripts/sync_ai_agent_ecosystem.py --check ต้อง exit 0
- hooks ของ repo นี้: core.hooksPath=.githooks — commit subject ต้องขึ้นต้น `KAN-<id>:`
- ห้าม commit secret — ไฟล์นี้อยู่ใน git; ดึงค่าสดจาก Doppler หรือ .env ที่ gitignore ไว้
