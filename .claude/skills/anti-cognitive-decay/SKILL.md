---
name: anti-cognitive-decay
description: Bounded context handoff and operator-only lifecycle management.
---

# Anti-Cognitive Decay Skill

Governs bounded context preservation across runtimes without authority drift.

## Principles & Authority

- Primary authority resides in `PROJECT_TASKS.md` and `plans/plan.md`.
- `HANDOFF.md` is a derived, non-authoritative handoff capsule adhering to `HandoffSnapshotV1`.
- Raw transcript files are never read or parsed; only structured state is evaluated.
- Any unresolved lane status leaves `clear_ready` false. Missing or unverified metrics evaluate to `UNKNOWN`.

## Budget Thresholds & Limits

- State payload and hook inputs are bounded to `64 KiB`.
- Generated derived capsules must not exceed `16 KiB`.
- Percentage thresholds: alert at `40%`, snapshot at `45%`, critical at `80%`.
- Transcript byte thresholds: alert at `400 KiB`, snapshot at `450 KiB`, critical at `900 KiB`.

## Governance & Safety

- Only an `operator` may clear, compact, or reset sessions; hooks never execute automated clearing.
- Codex project hooks operate under non-managed user review of the exact current hash.
- Native Codex CLI may expose `--dangerously-bypass-hook-trust`; repository instructions never invoke or recommend this bypass, and managed hooks remain outside this local implementation.

## Gotchas

- Never select a generated mirror as the canonical source.
- Never inspect raw transcript content directly.
- Never self-declare hook trust in repository configuration.
