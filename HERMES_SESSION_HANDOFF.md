# Secret Scan Session Handoff — Gitleaks

> **Generated**: 2026-09-29 (Asia/Bangkok)
> **Updated (merge)**: 2026-09-29 ~22:15 — เติมผล working-tree scan และปรับสถานะ rotation (ดูหัวข้อ 2b, 4b)
> **Branch**: `main` @ `e5fd531f`
> **Scan tool**: gitleaks (local, `/opt/homebrew/bin/gitleaks` v8.30.1)
> **Scan command**: `gitleaks detect --source . --verbose` (history) + `gitleaks detect --no-git --source . --verbose` (working tree)
> **Report (full)**: `/tmp/gitleaks-report.json` (history, session แรก) · `/tmp/gitleaks-history.json` + `/tmp/gitleaks-worktree.json` (session ตรวจซ้ำ)

---

## 1. Executive Summary

สแกน secret ทั้ง git history (1,254 commits, ~257 MB) ด้วย gitleaks — **พบ 207 findings แต่แทบทั้งหมดเป็น false positive** ยกเว้น **1 กลุ่มจริง**: Google API key (Gemini) 2 ตัวที่เคยถูก hardcode ใน `api/index.js` และติดอยู่ใน **git history ของ public repo ตลอด** แม้จะถูก sanitize ออกจาก HEAD แล้ว

## 2. 🔴 Leak จริง — ต้อง Rotate ทันที

| รายการ | รายละเอียด |
|:---|:---|
| **Secret** | Google API key (`AIzaSy...`) จำนวน **2 ตัว** — RuleID `gcp-api-key` |
| **ตำแหน่ง** | `api/index.js` line 76–77 |
| **Commit ที่เพิ่ม** | `2a2dbd0e` — 2026-08-14 `feat(ai-llm): integrate real Google AI Studio Gemini Cloud LLM inference...` |
| **Commit ที่ sanitize** | `22b3c6e2` — 2026-08-15 `fix(security): sanitize hardcoded API keys...` |
| **สถานะใน HEAD** | ✅ ไม่มีอยู่แล้ว (แทนด้วย env/config) — ❌ แต่ยังอยู่ใน history |
| **ความเสี่ยง** | ⚠️ **Repo เป็น PUBLIC** (`pphothidaen/HoroConsultant` → visibility: PUBLIC) — ใครก็ clone แล้วดึง key ออกจาก history ได้ ค้างแรม ~6 สัปดาห์ |

**Action ที่ต้องทำ (ทำด้วยตัวเอง — owner account เท่านั้น)**:
1. Revoke/rotate key 2 ตัวที่ [Google AI Studio → API Keys](https://aistudio.google.com/apikey) และ/หรือ Google Cloud Console
2. เปิด API restriction บน key ใหม่ (จำกัด API + referrer/server IP)
3. (ถ้าต้อง scrub history) `git filter-repo` + force-push — แต่ rotate สำคัญกว่า เพราะ clone เก่ามี key อยู่แล้ว

## 2b. ✅ สถานะล่าสุดของเคสนี้ (อัปเดตโดย session ตรวจซ้ำ)

`.gitleaksignore` (สร้าง 2026-09-29 22:04) ระบุใน comment ว่า:
> gcp-api-key in `api/index.js`: historical commits `2a2dbd0e` (added) / `22b3c6e2` (removed); **keys revoked in Google AI Studio on 2026-09-29 per owner**

⇒ ตามบันทึกนั้น **key ถูก revoke แล้วในวันเดียวกัน** — เหลือเพียงให้ owner **ยืนยันด้วยตัวเองอีกครั้ง** ใน Google AI Studio ว่า key เดิมทั้ง 2 ตัวเป็นสถานะ revoked/disabled จริง แล้วหัวข้อ 2 ถือว่าปิด

## 2c. ผลตรวจซ้ำด้วย gitleaks v8.30.1 (session ที่สอง, 2026-09-29 ~22:12)

- **Git history**: `gitleaks detect --source . --verbose` → ✅ **no leaks found** (1,254 commits, exit 0) — สะอาดเพราะ `.gitleaksignore` suppress 207 fingerprints ไว้แล้ว (consistent กับผลของ session แรก)
- **Working tree**: `gitleaks detect --no-git --source . --verbose` → 122 raw findings ตรวจแยกแล้วทั้งหมด:
  1. **70 ในไฟล์ TRACKED = false positive** (SHA-256 fingerprint ของไฟล์/skill, ชื่อ symlink `*.keychain-db`, คำว่า "secret scan" ใน prose) — ตรงกับกลุ่ม FP ในหัวข้อ 3 และถูก suppress ใน `.gitleaksignore` แล้ว
  2. **50 ในไฟล์ local = ไม่หลุดเข้า repo**: `.env` (25), `.env.production` (22), `.env.local` (1), `.aws/credentials` (1), `gen-lang-client-0821704500-6831370efa0e.json` — GCP service account (1) — ทุกไฟล์ untracked + gitignore ครบ เป็น secret ใช้จริงบนเครื่องเท่านั้น
  3. **2 ในไฟล์ test = fixture** — `tests/test_lease_manager.py` (`fence-KAN-502-WRONG`), `tests/test_keychain_isolation.py`

## 3. ✅ False Positive (205 findings, 47 unique pairs)

ยังอยู่ใน HEAD 44 รายการ จำแนกได้เป็น:

| กลุ่ม | ไฟล์หลัก | เหตุผลที่ไม่ใช่ leak |
|:---|:---|:---|
| SHA-256 hash manifest (evidence receipts) | `plans/evidence/context-opt-001/*.json` (168 findings), `plans/evidence/release-001/*.json` | เป็น content hash ของไฟล์ test/screenshot ไม่ใช่ credential |
| Keychain filesystem paths | `plans/evidence/keychain-purge-20260904/ops-purge-003.json`, `tests/test_keychain_isolation.py` | จับคำว่า "key" จากชื่อไฟล์ `*.keychain-db` |
| Internal routing/test identifiers | `project/data/hitl_reviews.json` (`routing_key: horo_v3_cons...`), `project/tests/artifacts/.../smoke-result.json` (`claim_key`), `tests/test_lease_manager.py` (`fence-KAN-50`) | identifier ภายในระบบ / test fixture ไม่ใช่ secret |
| คำว่า "secret" ใน prose | `plans/active/meta-008-support/spark_safety_lane_dispatch_queue.md` | จับจากคำ "secret scan" ในเอกสาร |

## 4. CI Gap ที่พบ (แก้โน้ต session ก่อน)

- ❌ **ไม่มี Gitleaks action ใน CI** — ค้นทั้ง 31 ไฟล์ใน `.github/workflows/` ไม่พบ gitleaks / secret scan (โน้ตของ session ก่อนที่ว่า "CI มี Gitleaks อยู่แล้วใน ci.yml" ไม่ถูกต้อง)
- แนะนำ: เพิ่ม `gitleaks/gitleaks-action@v2` workflow + ไฟล์ `.gitleaksignore` ที่ whitelist fingerprint ของ hash-manifest evidence files (ไม่ commit ให้จนกว่าจะยืนยัน)

## 5. สิ่งที่ทำเสร็จแล้ว (จาก session ก่อน + session นี้)

- ✅ gitleaks ติดตั้งแล้ว (`/opt/homebrew/bin/gitleaks`) — ไม่ต้อง `brew install` ซ้ำ
- ✅ สแกน git history ทั้งหมด (1,254 commits) — สรุปอยู่ในเอกสารนี้
- ✅ Credential pattern ใน source/test/scripts/config (session ก่อน) — ไม่พบ secret จริงใน HEAD
- ✅ `.gitignore` coverage — บล็อก `.env` / logs / artifacts ครบ

## 6. สิ่งค้างอื่นใน working tree (ไม่เกี่ยวกับ secret scan)

- `M scripts/test_provenance_guard.py` — modified จากงาน KAN-179
- `?? tests/test_dev_branch_guard.py` — untracked จากงาน KAN-179
- `?? .gitleaksignore` — **untracked** — baseline ของ history scan ถ้าไม่ commit CI จะไม่มี baseline อ้างอิง (แต่ CI ก็ยังไม่มี gitleaks job)
- `?? .hermes/cache/` — working cache (`kan178_red_proof.py`, PR bodies) — พิจารณาเพิ่ม `.hermes/cache/` ลง `.gitignore`
- `?? HERMES_SESSION_HANDOFF.md` — ไฟล์นี้ (session แรกสร้าง, session ที่สอง merge อัปเดต)

## 7. Next Steps (เรียงตามลำดับความสำคัญ — อัปเดตแล้ว)

1. ~~🔴 ทันที: Rotate Google API key 2 ตัว~~ → **ยืนยันสถานะ revoke ใน Google AI Studio** (ตาม `.gitleaksignore` revoke แล้วเมื่อ 2026-09-29 — เหลือ owner ตรวจยืนยัน)
2. ตัดสินใจ commit `.gitleaksignore` (ปัจจุบัน untracked) — **⚠️ ต้อง commit พร้อมกับ `gitleaks.yml`** ไม่งั้น CI run แรกจะ fail ด้วย 207 false positives
3. ~~เพิ่ม Gitleaks CI workflow~~ → **ทำแล้ว** (`.github/workflows/gitleaks.yml`, ยัง untracked — ตรวจแล้ว: fetch-depth 0 + gitleaks-action@v2 ถูกต้อง)
4. ~~พิจารณาเพิ่ม `.hermes/cache/` ลง `.gitignore`~~ → **ทำแล้ว** (แก้ใน working tree แล้ว ยังไม่ commit)
5. ~~เก็บงาน KAN-184 red test~~ → **GREEN แล้ว** — implement `_get_current_branch` + `_dev_branch_skip_provenance` ใน `scripts/test_provenance_guard.py` (fail-closed: branch ที่ไม่รู้จัก/detached HEAD ต้อง full provenance เสมอ) — `tests/test_dev_branch_guard.py` ผ่าน, regression 69 ผ่าน

### ⚠️ สถานะที่ session ใหม่ต้องรู้ (ยังค้าง)

- **`test_full_ai_agent_ecosystem_check_passes` FAIL อยู่แล้วก่อนการแก้ทั้งหมด** — `sync_ai_agent_ecosystem.py --check` exit 1 ที่ "codex3: Policy violation (missing 15 disabled remote plugin(s)...)" พิสูจน์แล้วว่า fail เหมือนกันบน HEAD สะอาด (ทดสอบผ่าน temp git worktree) — เป็น config drift ของ codex3 ไม่เกี่ยวกับงาน secret scan หรือ KAN-184 ควรเปิด ticket แยกแก้
- `.zcode/` + `.zcodeignore` เป็น untracked artifacts ของ ZCode tooling — พิจารณาเพิ่ม `.gitignore` ด้วย
- ทุกไฟล์ที่แก้/สร้างใน session นี้ **ยังไม่ได้ commit** — รอ owner ตัดสินใจ
