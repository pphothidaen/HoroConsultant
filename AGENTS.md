# HoroConsultant — Agent Gateway (Compact Index)

> **This file is a compact gateway.** Detailed architecture, tech stack, run commands, specialist matrix, and 6-lane concurrency live in `docs/PROJECT.md`. Task-specific rules live in `.agents/rules/*` and `skills/*/SKILL.md`. Do not bloat this file — add new rules to the appropriate skill or rule file, not here.

## 1. Core Operating Constraints (Non-Negotiable)

- **Read-Before-Modify:** ห้ามแก้ไขไฟล์ใดๆ ก่อนเรียกอ่านไฟล์นั้นและทำความเข้าใจโครงสร้างเดิมเสมอ
- **No Speculative Coding:** ห้ามสร้างไฟล์, เพิ่ม Dependency หรือแก้ไขโค้ดนอกเหนือขอบเขตที่ระบุใน `plan.md` / `ATOMIC_TICKET.md`
- **TDD Contract:** ห้ามแก้ไข Frozen Unit/Integration Tests ย้อนหลังเพื่อให้ Implementation ผ่าน
- **Iteration Safety Cap:** หากแก้ปัญหาไม่สำเร็จภายใน 5 รอบ หรือเกิด Action ซ้ำเดิม 3 ครั้ง (เรียกเครื่องมือเดิมด้วยพารามิเตอร์เดิม) ให้ยุติการทำงานและบันทึกเหตุผลเพื่อ Escalate ต่อมนุษย์ทันที
- **Doom-Loop Detection:** หากเรียกใช้เครื่องมือเดิมด้วยพารามิเตอร์เดิมซ้ำกันเกิน 2–3 ครั้ง ให้หยุดและส่งต่อให้มนุษย์ทันที (ก่อนแตะเพดาน Iteration ที่ 5)
- **Secret Hygiene:** ห้าม commit secret/token/credential; redact headers ใน logs; ใช้ Doppler สำหรับ secrets
- **Pure ASCII Logging:** ใช้ `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` เท่านั้น

## 2. Context Navigation Matrix

- **System Architecture & Tech Stack:** อ่าน `docs/PROJECT.md`
- **Architectural Decisions (ADR):** ตรวจสอบ `docs/adr/` ก่อนเริ่มงาน Tier 3
- **Phase Instructions:**
  - Planning/Intake: `.agents/rules/intake.md`
  - TDD & Development: `.agents/rules/developer.md`
  - Review & Audit: `.agents/rules/reviewer.md`
- **Codex compatibility:** `.agents/` และ `.antigravity/` ยังคงเป็น legacy config (ดูด้านล่าง)

## 3. Risk-Tiering Routing

- **Tier 1 (Trivial/Docs):** แก้ไขเฉพาะข้อความหรือคอมเมนต์ ข้ามลูป TDD เต็มรูปแบบ
- **Tier 2 (Feature/Fix):** รันลูป TDD ปกติ (Test -> Code -> Manifest)
- **Tier 3 (Core/Security):** บังคับตรวจ ADR + Security Audit + Human Approval

## 4. Codex Compatibility Boundary

- `.agents/` and `.antigravity/` remain the legacy multi-agent configuration. Do not rename, delete, or manually rewrite those definitions for Codex work.
- `.agents/skills/*/SKILL.md` are native Codex skills and are discovered from this repository.
- `.agents/agents/*/agent.json` is the compatibility-layer source. `.codex/agents/*.toml` is generated output and must not be edited manually.
- After changing legacy agent definitions, skills, Claude rules, or routing config, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`. Use `python3 scripts/sync_ai_agent_ecosystem.py --check` for read-only validation.

<!-- gitbook-agent-instructions:start -->

## GitBook Documentation Editing

This repository contains documentation synced with GitBook via Git Sync.

Before editing GitBook-synced Markdown, YAML, or asset files, make sure the GitBook skill is available and up to date in your local agent environment. Prefer installing or updating it with:

```bash
npx skills add gitbookio/gitbook-skills
```

This command may add or update local agent skill files. Use them only as local agent instructions; do not commit those installed skill files or any tool-generated agent configuration unless the user explicitly asks for it.

If `npx` is unavailable, load the skill from:

https://gitbook.com/docs/skill.md

When making changes, preserve GitBook sync metadata such as frontmatter, `SUMMARY.md`, `gitbook-docs.yaml`, `.gitbook/`, and asset links unless the requested edit explicitly requires changing them.

<!-- gitbook-agent-instructions:end -->
