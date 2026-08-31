# Retired TODO Workstreams — Traceability Pointer

**Disposition (2026-08-28):** This file is a historical pointer, not an active
backlog or execution plan. The six TODO workstreams were retained for intent
and are closed or superseded by the evidence-backed tickets below. Do not copy
status, ownership, acceptance criteria, or release claims into this file.

## Authority map

- **Active authority:** [`PROJECT_TASKS.md`](../PROJECT_TASKS.md) is the sole
  authority for current ticket status, ownership, dependencies, acceptance
  criteria, evidence, checkpoints, and operational handoff.
- **Decision authority:** [`plans/plan.md`](plan.md) contains decision records,
  grill reports, and implementation rationale; it does not replace the board.
- **Resume authority:** [`HANDOFF.md`](../HANDOFF.md) contains current-session
  constraints, blockers, and safe commands.

## Historical workstream links

| Historical workstream | Current traceability authority |
|---|---|
| 1. Model fusion and GGUF/Ollama export | [`TICKET-META-003`](../PROJECT_TASKS.md#-ticket-meta-003--developer---status-done), [`TICKET-META-004`](../PROJECT_TASKS.md#-ticket-meta-004--developer--qa_tester---status-done) |
| 2. External AI provider integration | [`TICKET-META-003`](../PROJECT_TASKS.md#-ticket-meta-003--developer---status-done), [`TICKET-META-005`](../PROJECT_TASKS.md#-ticket-meta-005--devops--developer---status-done) |
| 3. Swiss Ephemeris integration | [`TICKET-META-003`](../PROJECT_TASKS.md#-ticket-meta-003--developer---status-done), [`TICKET-META-004`](../PROJECT_TASKS.md#-ticket-meta-004--developer--qa_tester---status-done) |
| 4. Additional source ingestion and vault expansion | [`TICKET-META-003`](../PROJECT_TASKS.md#-ticket-meta-003--developer---status-done), [`TICKET-META-004`](../PROJECT_TASKS.md#-ticket-meta-004--developer--qa_tester---status-done) |
| 5. CI/CD automation audit | [`TICKET-META-005`](../PROJECT_TASKS.md#-ticket-meta-005--devops--developer---status-done), [`TICKET-META-006`](../PROJECT_TASKS.md#-ticket-meta-006--qa_tester--code_reviewer--business_analyst---status-done) |
| 6. Consultant web UI enhancements | [`TICKET-META-004`](../PROJECT_TASKS.md#-ticket-meta-004--developer--qa_tester---status-done), [`TICKET-META-006`](../PROJECT_TASKS.md#-ticket-meta-006--qa_tester--code_reviewer--business_analyst---status-done) |

The retired SDLC intent was the [AI SDLC workflow](../.agents/workflows/aisdlc.md):
planning, implementation, QA, release verification, then board/handoff update.
Its current checkpoint state and evidence are maintained on the board and in
the linked plan/handoff records.

## Safe resume rule

Resume only from the latest status and evidence in [`PROJECT_TASKS.md`](../PROJECT_TASKS.md),
using [`HANDOFF.md`](../HANDOFF.md) for session constraints. Reopen a workstream
only when the board records a new ticket or contrary evidence; otherwise do not
restart Tasks 1–6 or infer release approval from this historical pointer.
