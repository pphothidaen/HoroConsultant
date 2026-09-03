---
name: bsa-doc-skill-management
description: Requirements decomposition, live docs sync, quota/account handoff, and skill governance.
---

# BSA Doc Skill Management

Manage requirements decomposition, live docs sync, and quota/account handoff.

## Primary Responsibilities

1. **Requirements Decomposition**: Break down high-level business needs into actionable specs in `plans/plan.md` and atomic tickets in `atomic_tasks.md`.
2. **Specialist & Skill Mapping Audit**: Verify that every ticket declared in `atomic_tasks.md` has an assigned specialist from the Agent Matrix and a list of required modular skills.
3. **Documentation Sync**: Ensure `README.md`, `HOWTO.md`, `atomic_tasks.md`, `plans/plan.md`, and skill catalogs remain 100% accurate.
4. **Quota Handoff Continuity**: Manage quota status updates and migration continuity records.

## Gotchas

- Never edit generated mirror files directly; always update the canonical source in `.agents/skills/`.
- Never bypass the skill-governance validation when syncing across ecosystems.
- Reject any ticket in `atomic_tasks.md` that lacks a specialist role assignment or required skill list.