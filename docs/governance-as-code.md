# Governance-as-Code (KAN-97)

Branch protection และ repository rulesets ของ repo นี้ถูกประกาศไว้เป็น declarative JSON ใน `governance/` เพื่อให้การเปลี่ยนแปลง governance มี audit trail ใน git history และตรวจจับ config drift อัตโนมัติ

## ไฟล์

| ไฟล์ | เนื้อหา |
| --- | --- |
| `governance/branch-protection.main.json` | Classic branch protection บน `main` (required reviews, enforce admins, ฯลฯ) |
| `governance/rulesets.json` | Repository rulesets (ปัจจุบัน: `Require Test Provenance`, id 21626253) |
| `scripts/governance_sync.py` | Sync/validate/export tool (stdlib-only, ใช้ `gh api`) |
| `.github/workflows/governance-drift.yml` | รัน validate รายวัน (01:00 UTC / 08:00 น. Bangkok) |

## กติกาหลัก

**การเปลี่ยน governance ทุกครั้ง = PR เสมอ** ห้ามแก้ branch protection / rulesets ผ่าน UI หรือ imperative `gh api` calls โดยตรง

Flow การเปลี่ยนแปลง:

1. แก้ `governance/*.json` ให้เป็น state ที่ต้องการ
2. เปิด PR (title ขึ้นต้น ticket id) — review + merge ตามปกติ
3. Maintainer รัน `python3 scripts/governance_sync.py apply --yes` เพื่อ push declaration ไป GitHub
4. Workflow รายวันจะ validate ว่า state จริงตรงกับ declaration

ถ้ามีคนแก้ governance บน GitHub ตรง ๆ (ข้าม PR) workflow รายวันจะ fail พร้อมรายการ drift ที่ชัดเจน

## คำสั่ง

```bash
# เทียบ declaration กับ state จริง (exit 0 = ตรงกัน, exit 1 = drift, exit 2 = error)
python3 scripts/governance_sync.py validate

# ดึง state จริงจาก GitHub มาเขียน governance/*.json (ใช้หลังเปลี่ยนจริงแล้วต้องการ capture)
python3 scripts/governance_sync.py export

# Push declaration ไป GitHub (ต้องมี --yes; ใช้เฉพาะหลัง PR merge)
python3 scripts/governance_sync.py apply --yes
```

ต้อง login `gh` ด้วย token ที่มีสิทธิ์ admin (อ่าน branch protection ต้องใช้ administration scope)

## เหตุผลที่เลือก JSON + script แทน Terraform (YAGNI)

- **Terraform ต้องการ state backend เพิ่ม** (S3/remote state + locking) สำหรับ repo เดี่ยวที่มี resource 2 ชิ้น — overhead สูงเกินประโยชน์
- GitHub เป็น source of truth อยู่แล้ว: `export` สร้าง declaration ใหม่ได้ทุกเมื่อ ไม่จำเป็นต้องเก็บ state file แยก
- Drift detection ทำได้ด้วยการ fetch + diff ตรง ๆ ซึ่ง `validate` ทำอยู่แล้ว — Terraform จะได้ `plan -detailed-exitcode` มาโดยตรวจผ่าน state ที่อาจ stale
- ไม่เพิ่ม runtime dependency (ไม่มี PyGithub, ไม่มี Terraform binary) — `gh` + Python stdlib ที่ CI มีอยู่แล้ว
- เกณฑ์ scripts/AGENTS.md: standard-library-first

ถ้าอนาคตต้องจัดการ governance หลาย repo หรือหลาย environment ค่อยพิจารณา Terraform ใหม่

## หมายเหตุเชิงเทคนิค

- การเปรียบเทียบ strip volatile fields (urls, node ids, timestamps, per-viewer fields) ออกทั้งสองฝั่ง — เทียบเฉพาะ settings ที่ `apply` เขียนจริง
- Ruleset `id` เก็บไว้ใน declaration เพื่อให้ `apply` target ตัวเดิม แต่ไม่นำมาเทียบ (server-assigned)
- Workflow รายวันใช้ secret `GH_TOKEN` (PAT ของ repo admin) เพราะ default `GITHUB_TOKEN` อ่าน classic branch protection ไม่ได้ (ต้องการ administration permission) — ถ้า secret หาย job จะ fail closed
- `apply` อ่าน live state ก่อนเสมอ (fail-closed) และปฏิเสธการทำงานถ้าไม่มี `--yes`
