---
description: Sub-agent delegation and result collection rules.
paths:
  - "AGENTS.md"
  - "CLAUDE.md"
  - ".claude/**/*"
  - ".agents/**/*.md"
  - ".agents/agents/**/*.json"
  - ".agents/skills/**/SKILL.md"
  - "PROJECT_TASKS.md"
  - "plans/**/*.md"
---

# Orchestrator and Sub-Agent Rules

- Decompose requests into atomic tickets (`atomic_tasks.md`), explicitly bind each ticket to a specialist from the Agent Matrix and required modular skills, with objective, ownership, boundaries, evidence, and stop condition. Unbound dispatches fail closed.
- Before executable dispatch, apply Rule 18: record a versioned `DispatchDecision`, preserve its floor, and bind its digest to receipt evidence. Static model/effort metadata is not runtime proof.
- Rule 11 is the scheduling authority. Exclude any ticket with an ineligible status, invalid/missing scheduling fields, unmet dependency, ownership conflict, quota/HITL failure, explicit blocker, or invalid Rule 18 decision before comparing tickets.
- Sort only execution-eligible tickets by `(-severity_rank, work_effort_rank, ticket_id_ascii)`: `CRITICAL > HIGH > MEDIUM > LOW`, then `XS < S < M < L < XL`, then Ticket ID ASCII ascending. Reserve ownership and recompute for parallel selections; do not preempt running work.
- Apply `GOV_CRITICAL_PATH_FIRST_V1`: every implementation, QA, or operations objective declares `CRITICAL_PATH_UNLOCK=<dependency-or-gate-id>`, and `SPECULATIVE_ATOMIC_TICKET=DENY`; only a bounded blocker-resolution lane may instead declare both `BLOCKER_EVIDENCE_ONLY=<named-blocker-id>` and `BLOCKER_EVIDENCE_MODE=READ_ONLY`.
- After each completion or block, recompute Rule 11 and backfill only the next eligible dependency-unlocking lane. Preserve quota, HITL, ownership, immutable baseline, and release gates; static policy availability is not provider execution proof.
- `Work Effort` is delivery size, not model reasoning effort. Model effort never changes scheduling order; historical `Priority`-only passages are superseded for scheduling and retained as evidence.
- Use available concurrency for useful independent evidence-bearing lanes, but do not fill slots with redundant, stale, speculative, dependency-blocked, or ownership-conflicting work. Roles may have multiple instances and children may create bounded lanes only within the total slot limit.
- Decompose to the smallest coherent task without artificial fragmentation. Reserve ownership and recompute Rule 11 after every lane; reuse freed slots for the next eligible lane. For single-file work, prefer one source editor plus a read-only QA-prep/reviewer; final QA and release verdicts wait for source freeze and dependencies.
- Keep file ownership isolated. If multiple agents need the same file, assign one editor and make the others read-only reviewers.
- Include this handoff sentence in every delegated task: `You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.`
- Sub-agents must return: `Status`, `Scope owned`, `Evidence`, `Findings`, `Changed files`, `Residual risk`, and `Recommended next action`.
- Live status must report active lanes, owned scope, waits/blockers, and `active/available` slot utilization. Never bypass quota, HITL, dependency, or ownership gates to occupy capacity.
- Root orchestrator remains accountable for final user-facing synthesis and cannot close a parent task until delegated items are `DONE` or explicitly `BLOCKED` with HITL action.
- Use `/clear` when context becomes too large from logs, polling, or completed investigations, but first write a handoff summary containing objective, current phase, latest commit, active run ids, changed/staged files, verified checks, blockers/HITL actions, and next safe command.
- Use `/status` whenever account quota may be low. If remaining quota is below 10%, stop broad work and update `PROJECT_TASKS.md` ticket `TICKET-META-008` plus the `plans/plan.md` account migration section before continuing or handing off.
- Quota handoff summaries must include only non-secret credential state (`present`, `missing`, `invalid`) and must not include token values, Chat IDs, API keys, or credential JSON.
- After `/clear`, re-check authoritative current state before acting; do not rely on the handoff summary as proof when external CI, deployments, or files may have changed.
