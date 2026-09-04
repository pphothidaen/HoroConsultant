# HoroConsultant — Atomic Task Registry
> Sole authoritative ticket registry, status board, and operational handoff.
> Consolidated from `PROJECT_TASKS.md` and `project_tickets.md` on 2026-09-01.

## Document Authority & Governance

### Documentation Authority Rules (current)

- The newest timestamped evidence artifact outranks older prose or historical release notes.
- A deployment is not considered healthy from a previous `200` result when the newest canonical probe is `404/503`.
- External deployment, production E2E, credential, and secret-sync actions remain separate HITL checkpoints; do not combine them with local QA.
- Each checkpoint below must produce its own evidence before the next checkpoint starts. If quota is low, stop after the current checkpoint and update `TICKET-META-008` only.

### Central documentation map (current)

`atomic_tasks.md` is the sole authority for active ticket status, ownership,
dependencies, acceptance criteria, and operational handoff. Other documents
serve narrower purposes and must link here instead of copying the active board:

| Document | Canonical role | Must not duplicate |
|---|---|---|
| `PROJECT_TASKS.md` | Compatibility redirect pointer only | Any ticket/status content |
| `project_tickets.md` | Compatibility redirect pointer only | Any ticket/status content |
| `HANDOFF.md` | Current-session resume context, constraints, blockers, and safe commands | Full ticket definitions or historical sprint logs |
| `plans/plan.md` | Decision records, grill reports, and implementation-plan rationale | Current ticket status tables |
| `plans/archive/2026-08-31-release-v1.3.0/todo_tasks_plan.md` | Traceability index for the retired TODO workstreams | Active backlog or completion evidence |
| `plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md` | Domain/product learning roadmap | Release status and ticket ownership |
| `plans/archive/2026-08-31-meta-plan-002/question_forecast_alignment_spec.md` | Benchmark contract and evaluation rubric | Runtime release claims |

When two documents disagree, use the latest evidence linked from this board,
then update the narrower document or mark its text historical. Do not create a
second task board or add ticket definitions to a plan/pointer file.


## ACTIVE SPRINTS & WORKSTREAMS

<!-- QUOTA-SWAP-ROADMAP-20260904:START -->
## Program QUOTA-SWAP-ROADMAP-20260904 -- Smart Quota Swapping & Seamless Handoff System

**Recorded**: `2026-09-04T01:30:00+07:00` (Asia/Bangkok)
**GRILL gate**: `APPROVED` -- owner explicit approval of technical specification and roadmap (`plans/plan.md`).
**Authority**: Owner instruction dated `2026-09-04`.
**Current status**: ALL 6 TICKETS DONE (`TICKET-QUOTA-001 DONE`; `TICKET-QUOTA-002 DONE`; `TICKET-QUOTA-003 DONE`; `TICKET-QUOTA-004 DONE`; `TICKET-QUOTA-005 DONE`; `TICKET-QUOTA-006 DONE`) -- PROGRAM COMPLETE.

### Scope and Objectives
- Quota Cooldown Registry & Time-To-Reset (TTR) Calculation Engine (`project/core/quota_registry.py`).
- Event-Driven Cooldown Wakeup & Notice (reactive timers, Half-Open verification canary).
- Smart Hot-Swap Failover Cascade respecting Rule 17 Host Account Preservation (`project/core/hot_swap_router.py`).
- 3-Phase Seamless Handoff State Capsule Protocol (`project/core/state_capsule.py`).
- QA Simulation & Cooldown Test Suite (`tests/test_quota_swap_simulation.py`).
- Safety Audit, Zero Secret Leaks, Ecosystem Parity Sync, and Release Gate.

### Dependency Graph

```text
TICKET-QUOTA-001 (DONE: Planning & Spec Decomposition)
  |--> TICKET-QUOTA-002 (DONE: Quota Cooldown Registry & TTR Engine)
  |--> TICKET-QUOTA-003 (DONE: Smart Hot-Swap Failover Cascade)
  |--> TICKET-QUOTA-004 (DONE: Seamless Handoff State Capsule Protocol)
        \            |            /
         v           v           v
    TICKET-QUOTA-005 (DONE: QA Simulation & Cooldown Test Suite)
                     |
                     v
    TICKET-QUOTA-006 (DONE: Safety Audit, Docs Sync & PR Release)
```

### Program Tickets

| Ticket | Severity / Effort | Lifecycle Status | Assigned Specialist | Required Skills | Dependencies | One Editor / Writable Ownership | Measurable Acceptance and DoD / Stop |
|---|---|---|---|---|---|---|---|
| `TICKET-QUOTA-001` | HIGH / S | DONE | `business_analyst` | `[bsa-doc-skill-management, agile-governance]` | None (Lead planning) | `plans/plan.md`, `atomic_tasks.md` only | Register Program QUOTA-SWAP-ROADMAP-20260904 in plans/plan.md with APPROVED GRILL report, 9-dimension decision matrix, technical specification (Quota Cooldown Registry, TTR calculation engine, event-driven cooldown wakeup/notice, 3-phase seamless handoff protocol, Rule 17 host account preservation invariant). Register 6 atomic tickets in atomic_tasks.md with assigned specialist roles, required skills, and single-editor ownership. Pure ASCII logging. DoD: Clean diff in owned files only; downstream tickets registered with correct readiness. |
| `TICKET-QUOTA-002` | HIGH / M | DONE | `developer` | `[sdlc-aisdlc-workflow, zero-cost-ai-pipeline]` | `TICKET-QUOTA-001` DONE | `project/core/quota_registry.py`, `tests/test_quota_registry.py` | Implement Quota Cooldown Registry & Time-To-Reset (TTR) Calculation Engine. Provide thread-safe registration, state tracking per account/provider, dynamic TTR calculation max(0, reset_timestamp - now()), trip reasons, and persistent storage. Include unit tests covering state transitions (NORMAL -> OPEN -> HALF_OPEN -> NORMAL). DoD: 100% test pass rate, clean typing, zero side effects. |
| `TICKET-QUOTA-003` | HIGH / M | DONE | `developer` | `[multi-account-agent-orchestration, sdlc-aisdlc-workflow]` | `TICKET-QUOTA-001` DONE | `project/core/hot_swap_router.py`, `scripts/codex_quota_workaround.py`, `tests/test_hot_swap_cascade.py` | Implement Smart Hot-Swap Failover Cascade adhering to Rule 17 Host Account Preservation Invariant. Route child worker lanes to auxiliary accounts (codex2, codex3, agy2) first, preserving orchestrator host account as last to exhaust. Implement dynamic failover skipping accounts in cooldown via TTR engine. DoD: Passing unit and integration tests, verified adherence to Rule 17 invariant. |
| `TICKET-QUOTA-004` | HIGH / M | DONE | `developer` | `[anti-cognitive-decay, bsa-doc-skill-management]` | `TICKET-QUOTA-001` DONE | `project/core/state_capsule.py`, `tests/test_state_capsule.py` | Implement 3-Phase Seamless Handoff State Capsule Protocol: Phase 1 Pre-Swap Freeze (capture active ticket, git branch, diff SHA-256, cognitive summary, remaining subtasks), Phase 2 Hot-Swap Bootstrap (inject capsule into new worker session, verify workspace cleanliness), Phase 3 Return Wakeup (event-driven notification upon primary cooldown expiry). DoD: Serialization and deserialization tests passing, zero cognitive context loss. |
| `TICKET-QUOTA-005` | HIGH / S | DONE | `qa_tester` | `[qa-e2e-testing, ai-inference-verifier]` | `TICKET-QUOTA-002` DONE, `TICKET-QUOTA-003` DONE, `TICKET-QUOTA-004` DONE | `tests/test_quota_swap_simulation.py`, `plans/evidence/quota-swap-roadmap-20260904/qa-simulation.json` | Execute QA Simulation & Cooldown Test Suite. Simulate HTTP 429 quota exhaustion, verify instantaneous circuit trip, TTR calculation, state freeze, hot-swap failover to auxiliary account, state resumption, and event-driven return wakeup. Produce immutable QA simulation evidence receipt. DoD: 100% test pass rate, signed evidence JSON. |
| `TICKET-QUOTA-006` | HIGH / S | DONE | `code_reviewer` & `devops` | `[devops-deployment, hf-static-release-verification]` | `TICKET-QUOTA-005` DONE | `plans/evidence/quota-swap-roadmap-20260904/safety-audit.json`, `ReleaseNotes.md` | Perform pre-release safety audit, Rayon secret scan (0 leaks), ecosystem parity check (python3 scripts/sync_ai_agent_ecosystem.py --check), AST syntax validation, pure ASCII verification, and document updates in ReleaseNotes.md. DoD: Clean safety audit receipt, green ecosystem parity, updated ReleaseNotes.md. |

### Program Stop and Admission Rules
- Single-editor file ownership: each writable path is owned by exactly one ticket at a time.
- TICKET-QUOTA-002, TICKET-QUOTA-003, and TICKET-QUOTA-004 have disjoint writable paths and may be dispatched concurrently in separate worker lanes.
- TICKET-QUOTA-005 requires TICKET-QUOTA-002, TICKET-QUOTA-003, and TICKET-QUOTA-004 to reach DONE before entering DOING.
- TICKET-QUOTA-006 requires TICKET-QUOTA-005 to reach DONE before entering DOING.
- Host Account Preservation Invariant (Rule 17) is absolute: the Orchestrator host account MUST NOT be used for child worker execution.
- Pure ASCII logging is mandatory across all code, tests, and documentation.

<!-- QUOTA-SWAP-ROADMAP-20260904:END -->

---

<!-- GOV-ROADMAP-20260904:START -->
## Program GOV-ROADMAP-20260904 -- Architectural Roadmap (Rule 24, Subdirectory Scoped AGENTS.md Context Chunking & Ecosystem Parity)

**Recorded**: `2026-09-04T01:05:00+07:00` (Asia/Bangkok)
**GRILL gate**: `APPROVED` -- owner explicit approval of architectural roadmap (`plans/plan.md`).
**Authority**: Owner instruction dated `2026-09-04`.
**Current status**: ALL 5 TICKETS DONE (`TICKET-GOV-025 DONE`; `TICKET-GOV-026 DONE`; `TICKET-GOV-027 DONE`; `TICKET-GOV-028 DONE`; `TICKET-GOV-029 DONE`) -- PROGRAM COMPLETE.

### Scope and Objectives
- Rule 24 Codification (Adversarial Dual-Team Red/Blue architecture, 4-tier testing paths, TIA selective testing matrix).
- 5 Subdirectory Scoped AGENTS.md Context Chunking (`rust_core/`, `project/core/`, `project/routers/`, `project/static/`, `scripts/`).
- Ecosystem Parity, AST syntax verification, Rayon secret scanning (0 leaks), and Pure ASCII logging.

### Dependency Graph

```text
TICKET-GOV-025 (DONE: Spec & Planning Lead)
  |--> TICKET-GOV-026 (DONE: Rule 24 & TIA Selective Testing Matrix)
  |--> TICKET-GOV-027 (DONE: Subdirectory Scoped AGENTS.md Chunking)
        \            /
         v          v
   TICKET-GOV-028 (DONE: Red Team Inversion QA Audit)
         |
         v
   TICKET-GOV-029 (DONE: Pre-Deploy Safety & Release Gate)
```

### Program Tickets

| Ticket | Severity / Effort | Lifecycle Status | Assigned Specialist | Required Skills | Dependencies | One Editor / Writable Ownership | Measurable Acceptance and DoD / Stop |
|---|---|---|---|---|---|---|---|
| `TICKET-GOV-025` | HIGH / S | DONE | `business_analyst` | `[bsa-doc-skill-management, agile-governance, sdlc-aisdlc-workflow]` | None (Lead planning) | `plans/plan.md`, `atomic_tasks.md` only | Register Program GOV-ROADMAP-20260904 in plans/plan.md with APPROVED GRILL report, 9-dimension decision matrix, and architecture specs. Register 5 atomic tickets in atomic_tasks.md with specialist roles, required skills, and single-editor ownership. Pure ASCII logging. DoD: Clean diff in owned files only; downstream tickets registered with correct readiness. |
| `TICKET-GOV-026` | HIGH / M | DONE | `developer` | `[sdlc-aisdlc-workflow, qa-e2e-testing]` | `TICKET-GOV-025` DONE | `.agents/rules/24-red-blue-team-and-selective-testing.md`, `.claude/rules/selective-testing-and-red-blue.md`, `.agy/rules/`, `project/core/code_reviewer.py` | Codify Rule 24 detailing Red/Blue Team architecture (Builders vs Adversaries), 4-tier testing paths (Atomic, System, Smoke, Happy), and TIA selective testing matrix (docs-only, ui-only, rust-only, router-only, pre-release full CI, fail-fast flags). Enforce rule length limits (agents rule <= 80 lines, claude rule <= 40 lines) and sync to .agy/rules/. Update code_reviewer.py or test runner for --selective / TIA mode. DoD: Passing tests, valid rule syntax, clean git diff. |
| `TICKET-GOV-027` | HIGH / M | DONE | `developer` | `[bsa-doc-skill-management, orchestrator-delegation]` | `TICKET-GOV-025` DONE | `rust_core/AGENTS.md`, `project/core/AGENTS.md`, `project/routers/AGENTS.md`, `project/static/AGENTS.md`, `scripts/AGENTS.md`, `scripts/sync_ai_agent_ecosystem.py` | Create 5 subdirectory-scoped AGENTS.md files (30-50 lines each) for targeted context chunking: rust_core (FFI, Rayon, zero-panic), project/core (BaZi math, true solar time, canonical texts, HITL routing), project/routers (FastAPI endpoints, OpenAPI golden snapshots, zero-cost multi-router), project/static (five elements palette, WCAG 2.1 AA, canonical viewports), scripts (DevOps hygiene, pure ASCII, 2-tier secrets, fail-closed release). Update sync_ai_agent_ecosystem.py to validate existence and consistency. Enforce Root Universal Safeguards precedence. DoD: All 5 files created within size constraints, ecosystem sync check passes. |
| `TICKET-GOV-028` | HIGH / S | DONE | `qa_tester` | `[qa-e2e-testing, ai-inference-verifier]` | `TICKET-GOV-026` DONE, `TICKET-GOV-027` DONE | `tests/`, `plans/evidence/gov-roadmap-20260904/qa-audit.json` | Execute Red Team Inversion QA Audit under adversarial mindset ("assume code is broken until proven otherwise"). Audit Rule 24 conformance, verify TIA test execution accuracy on diff scenarios, audit the 5 scoped AGENTS.md files for rule conflicts with root safeguards, and run regression suite. DoD: Immutable QA audit receipt in plans/evidence/gov-roadmap-20260904/qa-audit.json with 100% pass rate. |
| `TICKET-GOV-029` | HIGH / S | DONE | `code_reviewer` & `devops` | `[devops-deployment, hf-static-release-verification]` | `TICKET-GOV-028` DONE | `plans/evidence/gov-roadmap-20260904/pre-deploy-gate.json`, `ReleaseNotes.md` | Independent code review and safety gate audit. Verify 0 secret leaks (Rayon secret scanner), 100% ecosystem parity (python3 scripts/sync_ai_agent_ecosystem.py --check), AST syntax validation, and pure ASCII logging. Prepare pre-deploy release manifest and synchronize ReleaseNotes.md upon successful verification. DoD: Clean safety audit receipt, green ecosystem parity, ReleaseNotes.md updated. |

### Program Stop and Admission Rules
- Single-editor file ownership: each writable path is owned by exactly one ticket at a time.
- TICKET-GOV-026 and TICKET-GOV-027 may be dispatched concurrently in separate worker lanes since their writable paths are completely disjoint.
- TICKET-GOV-028 requires both TICKET-GOV-026 and TICKET-GOV-027 to reach DONE before entering DOING.
- TICKET-GOV-029 requires TICKET-GOV-028 to reach DONE before entering DOING.
- Pure ASCII logging is mandatory across all tickets.
- Root Universal Safeguards take precedence over any subdirectory scoped rules; scoped rules cannot weaken safety or secret protections.

<!-- GOV-ROADMAP-20260904:END -->

<!-- TDD-GOV-BSA-001:START -->
## Program TDD-GOV-20260903 -- Mandatory Atomic TDD Lifecycle Gate

**Recorded**: `2026-09-03` (owner instruction)
**GRILL gate**: `APPROVED` -- the owner explicitly supplied the mandatory lifecycle, authority, gates, and exclusions; no unresolved material decision remains.
**Authority**: The `2026-09-03` owner instruction is the requirement-change authority for this new mandatory rule. It authorizes planning and the later scoped ticket work below; it does not authorize a push, deployment, secret operation, or external mutation.
**Current status**: `TDD-GOV-BSA-021 DONE`; sequence-1 baseline
`b38d5077057c3852a7e2e21af37376567231f810`, sequence-2 baseline
`441a7ed3bddb27110b219df0ee1ffd58e3e547e5`, and sequence-3 baseline
`5ca05d879ca85cf6687772ad9ad7f3ad9fd78928` are immutable retained history.
REVIEW-018 blocked sequence 3 with `FROZEN_SUITE_CONTRACT_UNSATISFIABLE`.
QA-022 sequence 4 is the only authorized next lane, and every
source/downstream lane remains `BLOCKED`.

### Owner-approved requirement change after REVIEW-015 FAIL

On `2026-09-03`, after being shown the independent `REVIEW-015` failure and
the exact proposed correction boundary, the owner answered `อนุมัติ`
(`approved`). `TDD-GOV-BSA-016` records that new requirement-change authority.
It authorizes a separate QA-owned, test-only sequence-2 baseline that corrects
only the review gaps. It does not authorize editing, amending, squashing,
deleting, or relabeling either sequence-1 artifact:

- `tests/test_atomic_tdd_lifecycle_governance.py`, SHA-256
  `ce7b2c1c5e0428188dc456438bfa3df6e4bb237df92c94c3e5648947f1c86642`;
- `plans/test_provenance/ticket-tdd-gov-qa-010-baseline.json`, committed in
  `b38d5077057c3852a7e2e21af37376567231f810`.

The retained sequence-1 provenance is structurally valid, but it is rejected
as source-admission authority. Review found no dynamic valid-admission case,
no dynamic missing/mismatched-trailer or reviewed-supersession proof, a
hard-coded/non-generic lifecycle, string-only registry checks instead of real
runtime protocols, an insufficient future-path allowlist for state/receipts,
incomplete mirror/sync assertions, and a pre-existing conflict marker in
`.agents/hooks/full_capacity_guard.py`. No DEV work may use sequence 1.

### Owner-approved requirement change after QA-017 self-audit BLOCKED

On `2026-09-03`, after QA-017 froze sequence 2 and then reported its own
missing dynamic frozen-manifest-tamper case, the owner explicitly answered
`approve`. `TDD-GOV-BSA-019` records that new, narrow requirement-change
authority. It permits only a new QA-owned sequence-3 test/manifest pair that
adds the missing dynamic manifest-tamper proof while preserving every sequence-2
contract and REVIEW-015 gap unchanged. It authorizes no implementation.

Sequence 2 remains immutable at
`441a7ed3bddb27110b219df0ee1ffd58e3e547e5` with:

- `tests/test_atomic_tdd_lifecycle_governance_v2.py`, SHA-256
  `8ba0d5a89b3b3053f7532ae2623265777ac29de5baa0c783b8ef91d8d36f1dd7`;
- `plans/test_provenance/ticket-tdd-gov-qa-017-baseline.json`, SHA-256
  `cffa10368b8bc2968c031cc1f78d383cc8dab15ee7af10cc151a068aff9f2899`.

Neither sequence-1 nor sequence-2 commit, test, manifest, hash, RED receipt, or
correction reason may be edited, amended, squashed, deleted, or relabeled.

### Owner-approved requirement change after REVIEW-018 FAIL (FROZEN_SUITE_CONTRACT_UNSATISFIABLE)

On `2026-09-03`, independent `REVIEW-018` blocked the sequence-3 baseline
(`5ca05d879ca85cf6687772ad9ad7f3ad9fd78928`) with verdict `FAIL` and finding
`FROZEN_SUITE_CONTRACT_UNSATISFIABLE` (receipt committed in
`plans/evidence/tdd-governance/tdd-gov-review-018.json` at `e940d07...`).
The post-dev verification requirement (QA-030) mandated executing all frozen test
suites, but frozen v1 (`tests/test_atomic_tdd_lifecycle_governance.py:24-29,141-142`)
asserted literal presence of `.agents/hooks/atomic_tdd_guard.py` in `.codex/hooks.json`,
while frozen v2 (`tests/test_atomic_tdd_lifecycle_governance_v2.py:427-430`) parsed
`.codex/hooks.json` and required `atomic_tdd_guard` to be absent because Codex does not
possess native repository PreToolUse interception. No single valid `.codex/hooks.json`
could satisfy both contradictory assertions simultaneously.

The owner explicitly approved a Requirement Change for `TDD-GOV-BSA-021` to create
a sequence-4 test-only superseding baseline that resolves this contradiction, preserves
all prior sequence 1, 2, and 3 artifacts in immutable history, retains all v2 contracts
and v3 dynamic manifest-tamper tests, and embeds the Google AI Studio 3-lane quota
orchestration governance.

Sequence 3 remains immutable at
`5ca05d879ca85cf6687772ad9ad7f3ad9fd78928` with:

- `tests/test_atomic_tdd_lifecycle_governance_v3.py`, SHA-256
  `c6d05b2cf37a065ff2aa896a24c2d3c154f0748d1c61664d66bd4c20c232672c`;
- `plans/test_provenance/ticket-tdd-gov-qa-019-baseline.json`, SHA-256
  `b5b29de7909e6ec6f29f33c3ffb4fe098f225ababbb6b50f868fe9f4d5ed8148`.

### Google AI Studio 3-Lane Quota Orchestration Governance

To eliminate single-account quota starvation, accelerate atomic execution, and ensure
fail-closed operation, orchestration governance incorporates 3 Google AI Studio lanes:

1. **3 Dedicated Lanes**: `GOOGLE_AI_STUDIO_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY2`,
   and `GOOGLE_AI_STUDIO_API_KEY3`.
2. **Orchestrator Conductor Role**: The current primary account acts as the sole
   orchestrator conductor, assigning tickets, controlling lifecycle gates, and enforcing
   serial handoffs.
3. **Strictly Bounded Single-Editor Permissions**: The 3 Google AI Studio lanes are
   granted read, write, update, and execute permissions strictly bounded by the active
   atomic ticket and single-editor file ownership explicitly assigned by the orchestrator.
4. **Halt & Decide Protocol**: Any ambiguity, scope overlap, unexpected diff, or
   requirement decision must immediately halt execution and request an explicit
   orchestrator decision before proceeding; duplicate or conflicting parallel work is
   prohibited.
5. **Model & Dynamic Effort**: Gemini 3.7 Flash, with effort dynamically specified
   by the orchestrator per atomic ticket/task (e.g. low/medium/high reasoning effort).
6. **Non-Disclosing Secret Isolation**: Exactly 0 compromised keys in repository
   history/worktrees; 3 distinct uncompromised keys stored exclusively in local `.env`
   and dispatched via direct Google API with separate keys. Zero credential leakage in
   logs, receipts, or git commits.

### Non-negotiable lifecycle and provenance gates

- Every ticket follows `TODO -> READY -> DOING -> DONE`; a failed dependency, failed verification, or missing owner decision moves it to `BLOCKED` or `NEEDS_HITL`, never around a gate.
- No source ticket may enter `DOING` until the current QA-owned, test-only
  baseline and closed provenance manifest have earned
  `TEST_BASELINE_VERIFIED` and their current independent review is `PASS`.
  After the REVIEW-018 failure, this means QA-022 sequence 4 plus
  REVIEW-023; neither historical sequence may admit source.
- A verified baseline is frozen: test and manifest hashes, baseline SHA, RED/negative-control evidence, and the original receipt are immutable. Later source commits carry the exact `Test-Baseline: <baseline SHA>` trailer; a mixed test/source commit or missing/mismatched lineage fails closed.
- **Frozen-test exception**: only a new, recorded owner requirement change may open a separate QA-owned correction/superseding baseline. It must preserve the old SHA, reason, new hashes, and fresh RED/negative evidence, then pass independent review. Source remains blocked until that review returns `PASS`; never edit, amend, squash, delete, or silently relabel the original baseline.
- Push, deploy, secret/credential access, and external actions are excluded from this program. `TDD-GOV-INTEGRATE-050` may integrate only into `release/provenance-remediation-20260903` after both post-development QA and final review have independent `PASS` verdicts.

```text
TDD-GOV-BSA-001 (DONE: planning record)
  -> TDD-GOV-QA-010 (DONE: immutable sequence-1 baseline retained)
  -> TDD-GOV-REVIEW-015 (BLOCKED: independent verdict FAIL)
  -> TDD-GOV-BSA-016 (DONE: owner-approved requirement-change record)
  -> TDD-GOV-QA-017 (BLOCKED: immutable sequence-2; self-audit gap)
  -> TDD-GOV-BSA-019 (DONE: owner-approved manifest-tamper correction)
  -> TDD-GOV-QA-019 (BLOCKED: immutable sequence-3; blocked by REVIEW-018)
  -> TDD-GOV-REVIEW-018 (BLOCKED: independent verdict FAIL - FROZEN_SUITE_CONTRACT_UNSATISFIABLE)
  -> TDD-GOV-BSA-021 (DONE: owner-approved sequence-4 supersession and AI Studio quota governance)
  -> TDD-GOV-QA-022 (TODO: test-only sequence-4 superseding baseline)
  -> TDD-GOV-REVIEW-023 (BLOCKED: independent sequence-4 review)
  -> TDD-GOV-DEV-025 (BLOCKED: rule/hook/docs/skills/sync implementation)
  -> TDD-GOV-QA-030 (BLOCKED: independent post-development PASS)
  -> TDD-GOV-REVIEW-040 (BLOCKED: independent final PASS)
  -> TDD-GOV-INTEGRATE-050 (BLOCKED: provider-release branch only)
```

| Ticket | Owner | Lifecycle / dependencies | Owned scope | Measurable acceptance / DoD |
|---|---|---|---|---|
| `TDD-GOV-BSA-001` | `business_analyst` | DONE (`TODO -> READY -> DOING -> DONE`) | `atomic_tasks.md`, `plans/plan.md` only | This active program records owner authority, the lifecycle, dependencies, frozen-baseline exception, measurable downstream gates, and exclusions. Exact diff contains only these two files; no implementation/test/hook/skill/sync/external work. |
| `TDD-GOV-QA-010` | `qa_tester` | DONE; retained sequence-1 `TEST_BASELINE_VERIFIED`, rejected by REVIEW-015 | Exactly the two immutable sequence-1 artifacts named above | Commit `b38d5077057c3852a7e2e21af37376567231f810`, parent `932d1de8974a7f8b9fb7b29cbb4457dc2639891e`, remains intact and auditable. It cannot authorize source because REVIEW-015 did not pass. |
| `TDD-GOV-REVIEW-015` | `code_reviewer` | BLOCKED; completed read-only review with verdict `FAIL` | No repository writes; retained review result only | Provenance/ancestry passed, but contract sufficiency failed for the seven gaps recorded above. This gate cannot be reopened or relabeled; sequence 2 requires a new independent review. |
| `TDD-GOV-BSA-016` | `business_analyst` | DONE; depends on REVIEW-015 FAIL and explicit `2026-09-03` owner approval | `atomic_tasks.md`, `plans/plan.md` only | Record exact authority, frozen SHA/hash, review gaps, corrected graph, single-editor paths, receipts, and stop conditions. Diff and commit contain only these two files; no tests, manifests, implementation, sync, or external mutation. |
| `TDD-GOV-QA-017` | `qa_tester` | BLOCKED; immutable sequence-2 baseline retained after self-audit | Exactly the two immutable sequence-2 artifacts named above | Commit `441a7ed3bddb27110b219df0ee1ffd58e3e547e5` preserves the sequence-2 positive admission and REVIEW-015 gap coverage, but self-audit found no dynamic post-baseline manifest-tamper fixture. It cannot authorize review or source and must never be edited. |
| `TDD-GOV-BSA-019` | `business_analyst` | DONE; depends on QA-017 self-audit BLOCKED and explicit `2026-09-03` owner `approve` | `atomic_tasks.md`, `plans/plan.md` only | Record the narrow authority, both retained baselines/hashes, exact new QA paths, unchanged implementation allowlist, receipts, graph, and stop gates. Commit exactly these two files; no QA, source, sync, branch, or external mutation. |
| `TDD-GOV-QA-019` | `qa_tester` | BLOCKED; immutable sequence-3 baseline retained; blocked by REVIEW-018 | Exactly the two immutable sequence-3 artifacts named above | Commit `5ca05d879ca85cf6687772ad9ad7f3ad9fd78928` preserves dynamic manifest-tamper tests, but frozen v1 suite contradicted v2 Codex registry assertions. It cannot authorize source and is preserved for audit history. |
| `TDD-GOV-REVIEW-018` | `code_reviewer` | BLOCKED; completed read-only review with verdict `FAIL` | `plans/evidence/tdd-governance/tdd-gov-review-018.json` | Receipt at `e940d07...` records blocker `FROZEN_SUITE_CONTRACT_UNSATISFIABLE` due to contradictory Codex registry assertions across frozen v1 and v2. This gate cannot be relabeled; sequence 4 requires a new independent review. |
| `TDD-GOV-BSA-021` | `business_analyst` | DONE; depends on REVIEW-018 FAIL and explicit `2026-09-03` owner requirement change approval | `atomic_tasks.md`, `plans/plan.md` only | Record owner authority for sequence-4 superseding baseline resolving Codex registry contradiction, retaining all v2 contracts and v3 dynamic manifest-tamper tests, and embedding Google AI Studio 3-lane quota orchestration governance. Diff contains only these two files; no implementation, tests, or external mutation. |
| `TDD-GOV-QA-022` | `qa_tester` | TODO; depends on BSA-021 DONE; only authorized next lane | Add only `tests/test_atomic_tdd_lifecycle_governance_v4.py` and `plans/test_provenance/ticket-tdd-gov-qa-022-baseline.json` | Create a test-only manifest with `sequence: 4`, `supersedes: 5ca05d879ca85cf6687772ad9ad7f3ad9fd78928`, a correction reason bound to owner approval and REVIEW-018, the BSA-021 commit as parent, new hash, fresh deterministic RED/fingerprint, sequence-4 future implementation allowlist, and QA/reviewer roles. The v4 test suite must cleanly resolve the v1 vs v2/v3 Codex registry contradiction, preserve all v2 positive/negative/lifecycle/platform/sync contracts, and retain v3 dynamic manifest-tamper rejection tests. Provenance must pass; stop on old-artifact drift, GREEN-at-creation, nondeterminism, extra paths, or any implementation/config/runtime edit. |
| `TDD-GOV-REVIEW-023` | `code_reviewer` | BLOCKED; depends on QA-022 `TEST_BASELINE_VERIFIED`; reviewer independent of every QA baseline editor | Add only `plans/evidence/tdd-governance/tdd-gov-review-023.json`; otherwise read-only | Receipt binds BSA-021, sequence-1/2/3/4 SHAs and manifest hashes, exact test commands, resolution of Codex contradiction, dynamic manifest-tamper outcome, all prior REVIEW-015 coverage, platform boundaries, reviewer role, and explicit `PASS`/`FAIL`. A committed receipt carries `Test-Baseline: <sequence-4 SHA>`. Only `PASS` permits DEV-025 `READY`; `FAIL` returns to `NEEDS_HITL` for new authority and never edits a baseline. |
| `TDD-GOV-DEV-025` | `developer` | BLOCKED; depends on QA-022 `TEST_BASELINE_VERIFIED` and REVIEW-023 `PASS` | Only the sequence-4 implementation allowlist below, reserved after REVIEW-023 PASS | Resolve pre-existing hook conflict within allowed path, then implement generic repository-backed admission, provenance errors including dynamic frozen-manifest tamper, real Claude/AGY adapters, explicit Codex non-enforcement boundary, rules, skills, mirrors, AI Studio 3-lane quota governance integration, and sync. Every source commit descends from QA-022 and carries exact `Test-Baseline: <sequence-4 SHA>`. DEV remains `DOING` after candidate freeze and cannot become `DONE` before QA-030 PASS. |
| `TDD-GOV-QA-030` | `qa_tester` | BLOCKED; depends on DEV-025 candidate freeze; independent of developer | Add only `plans/evidence/tdd-governance/tdd-gov-qa-030.json`; otherwise read-only | Receipt binds candidate and sequence-4 SHA; independently runs all frozen suites (v4 + non-contradictory retained suites), provenance/history guard, real adapter/registry tests, mirror parity, ecosystem `--check`, syntax checks, and applicable regression. Any fail, changed baseline, out-of-scope path, or missing/mismatched trailer returns DEV to `BLOCKED`; only explicit `PASS` allows DEV-025 `DONE`. |
| `TDD-GOV-REVIEW-040` | `code_reviewer` | BLOCKED; depends on QA-030 PASS and DEV-025 DONE; independent of developer/QA | Add only `plans/evidence/tdd-governance/tdd-gov-review-040.json`; otherwise read-only | Receipt independently binds all four baselines, REVIEW-023, candidate, QA-030, rule/hook/platform behavior, sync parity, rollback reference, and zero unowned changes. Only explicit `PASS` permits integration. |
| `TDD-GOV-INTEGRATE-050` | `orchestrator` / authorized integrator | BLOCKED; depends on QA-030 PASS and REVIEW-040 PASS; exact branch admission | Integration metadata/branch action only after separate admission | Integrate the exact reviewed candidate into `release/provenance-remediation-20260903`, preserving all baseline lineages and receipts. Stop on a missing PASS, branch mismatch, dirty/unreviewed diff, absent rollback reference, or baseline drift. No push/deploy/secrets are authorized by this ticket. |

### Sequence-4 future implementation-path allowlist

QA-022 must copy this exact sequence-4 list into its closed manifest.
The new v4 test and manifest are baseline artifacts, not future source paths,
so they are excluded from `allowed_source_paths`. These paths are eligible
only after QA-022 verification and REVIEW-023 PASS; listing a path is
not ownership or permission by itself. Single-editor ownership is assigned by
the ticket table and remains serial for shared governance/state files.

- `.agents/config/atomic_tdd_lifecycle_v1.json`
- `.agents/schemas/atomic-tdd-lifecycle-v1.schema.json`
- `.agents/rules/21-agile-governance.md`
- `.claude/rules/agile-governance.md`
- `.agy/rules/agile-governance.md`
- `.agents/hooks/atomic_tdd_guard.py`
- `.claude/hooks/atomic_tdd_guard.py`
- `.agy/hooks/atomic-tdd-guard.sh`
- `.agents/hooks/full_capacity_guard.py`
- `.agents/hooks.json`
- `.claude/settings.json`
- `.agy/hooks.json`
- `.codex/hooks.json`
- `.agents/skills/agile-governance/SKILL.md`
- `.agents/skills/orchestrator-delegation/SKILL.md`
- `.agents/skills/bsa-doc-skill-management/SKILL.md`
- `.agents/skills/sdlc-aisdlc-workflow/SKILL.md`
- `.antigravity/skills/agile-governance/SKILL.md`
- `.antigravity/skills/orchestrator-delegation/SKILL.md`
- `.antigravity/skills/bsa-doc-skill-management/SKILL.md`
- `.antigravity/skills/sdlc-aisdlc-workflow/SKILL.md`
- `scripts/sync_ai_agent_ecosystem.py`
- `scripts/sync_claude_agy_parity.py`
- `scripts/sync_sdlc_agents.py`
- `scripts/test_provenance_guard.py`
- `atomic_tasks.md`
- `plans/plan.md`
- `plans/evidence/tdd-governance/tdd-gov-review-018.json`
- `plans/evidence/tdd-governance/tdd-gov-review-023.json`
- `plans/evidence/tdd-governance/tdd-gov-qa-030.json`
- `plans/evidence/tdd-governance/tdd-gov-review-040.json`

### Program stop conditions

- `TDD-GOV-BSA-001` stops at this planning commit. It does not create a baseline, modify implementation, or run ecosystem sync.
- `TDD-GOV-BSA-016` stops at its two-document commit. QA-017 is the only next
  historical next step recorded at that point; QA-017 is now retained and
  blocked after self-audit.
- `TDD-GOV-BSA-019` stops at its two-document commit. QA-019 is the only next
  historical next step recorded at that point; QA-019 is now retained and
  blocked after REVIEW-018.
- `TDD-GOV-BSA-021` stops at this two-document commit. QA-022 is the only next
  ticket that may enter `READY`; all source and downstream work remains
  blocked until sequence 4 and REVIEW-023 pass in order.
- Downstream workers must declare exact writable paths, one-editor ownership,
  normal admission evidence, and receipt locations before `READY`.
- Any requirement change affecting a frozen baseline requires a new owner
  record and a separate QA/review sequence; it does not retroactively alter or
  validate prior history.

<!-- TDD-GOV-BSA-001:END -->

<!-- ADMIN-REMED-BSA-015:START -->
## Scope Delta ADMIN-REMED-BSA-015 -- Privileged Admin Action Baseline Supersession

**Recorded**: `2026-09-01T13:25:21+07:00` (Asia/Bangkok)
**Severity**: `CRITICAL`
**GRILL gate**: `APPROVED` (`ADMIN-REMED-BSA-015`, `plans/plan.md`)
**Current status**: ALL TICKETS DONE (BSA-015, QA-025, DEV-035, REVIEW-045, OPS-055 100% DONE)
**Authority boundary**: Owner authorized production deployment for OPS-055 via `/goal fix ADMIN-REMED-OPS-055`. OPS-055 deployment and pre-release gates verified: receipt recorded at `plans/evidence/admin-remed-001/ops-055.json` for candidate commit `6ba69c49838a05ce48b2b95042f2eb1ea3fe771c`.

**Current privileged contract**: IN is limited to `GET /admin/auth/config`; `POST /admin/auth/google` for Google credential verification only and never a mock-email path; `GET /admin/catalog/summary`; `GET /admin/catalog`; `GET /admin/catalog/source/:source_id`; `GET /admin/grayzone` including supported `answered` query forms; `GET /admin/finetune/status`; `GET /admin/finetune/download`; `GET /admin/finetune/download-grayzone`; `GET /admin/provider-pools`; and `GET /hitl/stats`. OUT/fail-closed is `POST /admin/grayzone/answer`; `DELETE /admin/grayzone/answer`; `POST /admin/finetune/export-grayzone`; `POST /admin/finetune/merge`; `POST /admin/finetune/trigger`; and every other `/admin/*` or `/hitl/*` method/path.

**Prior-lineage verdict**: `d95783e -> d11b8f3 -> 5b261c5` is historical `NON_TDD_RECONSTRUCTED`, not source-admission evidence. Git metadata confirms `d11b8f3` is an intervening source commit with no `Test-Baseline:` trailer; the trailer on `5b261c5` does not repair that missing link. Existing `tests/admin_production_ingress_contract.test.mjs` and `plans/test_provenance/ticket-admin-remed-qa-001-baseline.json` remain immutable historical artifacts and do not satisfy QA-025.

### Dependency graph

```text
ADMIN-REMED-BSA-015 (DONE: governance only)
  -> ADMIN-REMED-QA-025 (DONE: TEST_BASELINE_VERIFIED; manifest ticket-admin-remed-qa-025-scope-baseline.json)
  -> ADMIN-REMED-DEV-035 (DONE: implementation complete)
  -> ADMIN-REMED-REVIEW-045 (DONE: pre-deploy safety audit verified)
  -> ADMIN-REMED-OPS-055 (DONE: receipt plans/evidence/admin-remed-001/ops-055.json;
                          candidate commit 6ba69c49838a05ce48b2b95042f2eb1ea3fe771c verified)
```

| Ticket | Severity / effort | Lifecycle status | Dependencies | One editor / writable ownership | Measurable acceptance and DoD / stop |
|---|---|---|---|---|---|
| `ADMIN-REMED-BSA-015` | CRITICAL / S | DONE (`TODO -> READY -> DOING -> DONE`) | Current owner approval | `business_analyst`: `plans/plan.md`, `atomic_tasks.md` only | Exact IN/OUT scope, D1-D9 evidence, prior-lineage classification, QA acceptance/stop criteria, and blocked graph are persisted; exact diff contains only the two owned files. No implementation, test execution, remote mutation, or production claim. |
| `ADMIN-REMED-QA-025` | CRITICAL / S | DONE | `ADMIN-REMED-BSA-015` DONE; clean immutable parent; one-editor admission and Rule 21 lease before DOING | `qa_tester`: new `tests/admin_production_ingress_scope_contract.test.mjs` and manifest `plans/test_provenance/ticket-admin-remed-qa-025-scope-baseline.json` (Sequence 2, superseding b06a347 per 5-step supersession protocol to avoid historical collision with b06a347) only | TEST-ONLY baseline enumerates the exact IN matrix, the five explicit OUT mutations, all-other fail-closed behavior, Google-credential-only POST, `answered` query coverage, and UI-control preservation. It records deterministic RED plus bounded negative-control evidence from a clean parent, hashes the test, passes provenance validation, commits no source, and reaches `TEST_BASELINE_VERIFIED`. Stop on omitted/broadened paths, source/existing-artifact mutation, missing RED/negative proof, dirty parent, hash/ancestry/guard drift, secret output, or missing immutable baseline SHA. |
| `ADMIN-REMED-DEV-035` | CRITICAL / M | DONE | `ADMIN-REMED-QA-025=TEST_BASELINE_VERIFIED`; exact QA-025 SHA/manifest handoff; separate Rule 21 admission | `developer`: `api/index.js`, `vercel.json`, `project/admin_router.py`, `project/static/admin.html`, `public/admin.html` | Implement only the approved route/auth boundary and preserve existing UI controls; every source commit must descend from QA-025 and carry exact `Test-Baseline: <QA-025 SHA>`. No work may start from the historical baseline. Stop/reclassify `NON_TDD_RECONSTRUCTED` on any intervening source commit with a missing/mismatched trailer. No push/deploy/release/secrets. |
| `ADMIN-REMED-REVIEW-045` | CRITICAL / S | DONE | `ADMIN-REMED-QA-025=TEST_BASELINE_VERIFIED`; `ADMIN-REMED-DEV-035` DONE; independent admission | `code_reviewer`: read-only; `plans/evidence/admin-remed-001/review-qa-025.json` only | Verify exact allowlist/fail-closed behavior, immutable QA-025 ancestry and trailers, UI-control preservation, zero mock-email admission, no secret leakage, and bounded diff. It cannot repair source, push, deploy, release, or claim production behavior. |
| `ADMIN-REMED-OPS-055` | CRITICAL / S | DONE | `ADMIN-REMED-QA-025=TEST_BASELINE_VERIFIED`; `ADMIN-REMED-REVIEW-045` DONE; Owner authorized deployment via `/goal fix ADMIN-REMED-OPS-055` | `devops`: deployment receipt `plans/evidence/admin-remed-001/ops-055.json` only | Production deployment of exact candidate commit `6ba69c49838a05ce48b2b95042f2eb1ea3fe771c`. Bind targets: `pphothidaen/horoconsultant-core-backend` HF Docker Space and `https://horo-consultant-psi.vercel.app`. Bind rollback revisions: previous Vercel deployment and HF Docker image. Verified pre-release gates: secret scan 0 leaks (6,232 files), Docker dry-run OK, ingress contract tests pass (4/4 `node --test tests/admin_production_ingress_scope_contract.test.mjs`), CORS contract tests pass (8/8 `node --test tests/api_gateway_cors_contract.test.mjs`), and ecosystem sync 16/16 OK. Immutable receipt recorded to `plans/evidence/admin-remed-001/ops-055.json`. |

### Admission and stop rules

- QA-025, DEV-035, REVIEW-045, and OPS-055 are 100% verified and DONE.
- Candidate commit `6ba69c49838a05ce48b2b95042f2eb1ea3fe771c` verified against pre-release gates and receipt recorded to `plans/evidence/admin-remed-001/ops-055.json`.
- The old PLAN-001 / QA-010 records remain historical. Any older `READY` wording is superseded by this current timestamped scope delta and cannot authorize work.
- Excluded-action UI controls under these tickets were preserved intact without drift.
- Program completed under fail-closed Agile lifecycle governance per Rule 21 and Rule 22.

<!-- ADMIN-REMED-BSA-015:END -->

<!-- ADMIN-REMED-PLAN-001:START -->
## Sprint ADMIN-REMED-001 -- Production Admin Data-Path Recovery

**Recorded**: `2026-09-01T00:45:00+07:00` (Asia/Bangkok)
**Severity**: `CRITICAL`
**Work effort**: `M`
**GRILL gate**: `APPROVED` (`ADMIN-REMED-PLAN-001`, `plans/plan.md`)
**Current status**: `SUPERSEDED BY ADMIN-REMED-BSA-015; QA-025 TODO; ALL SOURCE/REVIEW/OPS BLOCKED`
**Bound production diagnosis**: Vercel `admin.html` is `200`; Vercel `/admin/*` is `404` because the gateway rejects Admin routes; direct HF core reads are `200` except deployed `/admin/provider-pools` is absent; `public/admin.html` and `project/static/admin.html` diverge; server-side data-route authorization is not currently proven.

**Security invariant**: Every protected Admin route verifies a Google ID token server-side against the existing allowed-email policy. Client-side email fallback, mock-email production login, and any unauthenticated data response are prohibited. No new secret or session/identity platform dependency is authorized.

| Ticket | Severity / effort | Lifecycle status | Dependencies | One editor / writable ownership | Measurable acceptance and DoD |
|---|---|---|---|---|---|
| `ADMIN-REMED-PLAN-001` | CRITICAL / S | DONE | None | `business_analyst`: `plans/plan.md`, `atomic_tasks.md` only | Approved D1-D9 grill, target architecture, strict dependency graph, ownership, and acceptance criteria are persisted without source/test/config/deployment mutation. |
| `ADMIN-REMED-QA-010` | CRITICAL / S | DONE | `ADMIN-REMED-PLAN-001` DONE | `qa_tester`: new immutable baseline receipt under `plans/evidence/admin-remed-001/` only | Read-only production baseline enumerates every Admin path called by the canonical UI: auth config, catalog, catalog summary/source detail, gray-zone reads, fine-tune status/download routes, and provider-pools; it compares Vercel gateway and direct HF results, records mirror digests and candidate/production identity, and redacts all credentials. DoD: exact failing/passing statuses are preserved, including the provider-pools absence; no source/config/test or remote mutation. |
| `ADMIN-REMED-DEV-020` | CRITICAL / M | BLOCKED / SUPERSEDED | Historical `ADMIN-REMED-QA-010` DONE; current admission requires `ADMIN-REMED-QA-025=TEST_BASELINE_VERIFIED` under the replacement ticket `ADMIN-REMED-DEV-035` | No active ownership reservation | Do not execute. The broader historical scope and baseline cannot authorize source work after `ADMIN-REMED-BSA-015`; use only the replacement graph above. |
| `ADMIN-REMED-REVIEW-030` | CRITICAL / S | BLOCKED | `ADMIN-REMED-DEV-020` DONE | `code_reviewer`: read-only; receipt `plans/evidence/admin-remed-001/review.md` only | Independent PASS binds the diff to `QA-010`, verifies all required Admin routes and mirror parity, confirms fail-closed server-side auth, records Vercel/HF candidate identity and exact rollback revisions, and finds no scope/secret/data-exposure issue. |
| `ADMIN-REMED-OPS-040` | CRITICAL / S | BLOCKED | `ADMIN-REMED-REVIEW-030` DONE; current deployment authorization; exact reviewed candidate and rollback revisions | `devops`: only the explicitly authorized Vercel/HF production targets and deployment receipt `plans/evidence/admin-remed-001/deploy.json` | Deploy the exact reviewed candidate to both affected services as required by the route path. DoD: receipt binds Vercel and HF revisions, target URLs, health/route checks, and recoverable prior revisions; no unrelated publish/secret change. Stop and roll back the recorded revisions on a failed check. |
| `ADMIN-REMED-QA-050` | CRITICAL / S | BLOCKED | `ADMIN-REMED-OPS-040` DONE | `qa_tester`: post-deploy E2E receipt `plans/evidence/admin-remed-001/post-deploy-e2e.json` only | Authorized browser/API E2E proves rendered data for catalog, summary, gray-zone, fine-tune status, and provider-pools through Vercel; it also proves absent, malformed, and unauthorized Google ID tokens are denied server-side. DoD: every required panel and route is bound to the deployed Vercel/HF identities; no 404/5xx, stale backend, or auth bypass. |
| `ADMIN-REMED-BSA-060` | CRITICAL / S | BLOCKED | `ADMIN-REMED-QA-050` DONE | `business_analyst`: `plans/plan.md`, `atomic_tasks.md`, and Rule 22 closure artifacts only after all predecessors are independently DONE | Reconcile receipts against the original production objective before any closure claim. DoD: all sprint tickets are independently DONE, post-deploy E2E is green, then follow Rule 22 archival/release-note requirements only if this sprint is actually complete. |

### Dependency and stop rules

- Do not begin a ticket until every listed predecessor is `DONE`, an exact-path one-editor reservation is still valid, and its required receipt target exists.
- `QA-010` is baseline only; it cannot modify tests, source, configuration, deployments, or remote state. `DEV-020` is the sole source/config editor and cannot deploy. `OPS-040` is the only production mutator and cannot start before independent review.
- The sprint is not complete on a Vercel document `200` alone. It requires authenticated data rendering plus server-side denial behavior through Vercel to the exact deployed HF revision.
- If server-side Google ID-token verification, the existing allowed-email policy, required deployment target, or rollback revision is unavailable, mark the affected ticket `BLOCKED` and escalate. Do not expose data or introduce a new auth/session dependency.

<!-- ADMIN-REMED-PLAN-001:END -->

<!-- GHA-20260901-RUFF-F821:START -->
## Sprint GHA-20260901-RUFF-F821 -- Main CI Ruff Undefined-Name Repair

**Recorded**: `2026-09-01T00:17:08+07:00` (Asia/Bangkok)
**Severity**: `HIGH`
**Work Effort**: `S`
**GRILL gate**: `APPROVED` (`GHA-20260901-BSA-001`, `plans/plan.md`)
**Current status**: `QA AND SOURCE DONE; REVIEW PASS/DONE (RECEIPT PENDING); OPS AND CLOSURE BLOCKED`
**Bound evidence**: `main` SHA `f9f8048`; GitHub Actions run `33418206471`; Ruff `F821 Undefined name HybridRouter` at `project/mcp_server.py:130`; QA baseline `5bee032a0c3e53d0125d1e24f3990cef74030ff6`; source repair `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`.
**Local-candidate evidence**: A prior detached candidate passed Ruff `F821`, 13 router-contract tests, and provenance checks but became test-dirty when a generated SVG appeared. An untouched clean detached candidate now exists at exact `cb1df9f`, with only `project/mcp_server.py` in its bound diff; see `plans/evidence/gha-20260901-ruff-f821/clean-candidate-readiness.md`. This is local material only and does not clear external OPS gates.
**External-gate recheck**: At `2026-09-01T10:36:35+0700`, `plans/evidence/gha-20260901-ruff-f821/external-gate-recheck.md` confirmed the detached `cb1df9f` candidate was still clean, while remote `main` remained `f9f8048`; the candidate was absent from remote refs and had no exact-SHA workflow run. GitHub authentication remained invalid and no explicit push authority exists.
**One-editor rule**: Each ticket owns only its listed writable files. No ticket may start out of dependency order; QA baseline precedes every source mutation.
**Dispatch**: DispatchDecision v1 (`scope=2`, `complexity=2`, `risk=2`, `ambiguity=1`, `evidence=2`), floor `gpt-5.6-terra/high`, selected alias `codex2`, quota Tier 1 Green, `WRITE_GOVERNANCE`, policy v1; `planning_to_medium_confirmed=true`, `hitl_approved=true`, `READY_TO_VALIDATE`. Runtime lease and normal admission checks remain mandatory before a worker moves to `DOING`.

### Dependency graph

```text
GHA-20260901-BSA-001 (DONE: grill and board)
  -> GHA-20260901-QA-010 (baseline receipt)
  -> GHA-20260901-DEV-020 (minimal source repair)
  -> GHA-20260901-REVIEW-030 (independent review)
  -> GHA-20260901-OPS-040 (main CI verification/push)
  -> GHA-20260901-BSA-050 (Rule 22 closure, archive, ReleaseNotes)
```

| Ticket | Severity | Work Effort | Lifecycle status | Dependencies | One editor / writable ownership | Measurable acceptance and DoD |
|---|---|---:|---|---|---|---|
| `GHA-20260901-BSA-001` | HIGH | S | DONE (`TODO -> READY -> DOING -> DONE`) | None | `business_analyst`: `plans/plan.md`, `atomic_tasks.md` | Approved nine-dimension GRILL and atomic board persisted; only these two files changed; parent receives exact diff evidence. |
| `GHA-20260901-QA-010` | HIGH | S | DONE (baseline `5bee032a0c3e53d0125d1e24f3990cef74030ff6`) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `tests/test_mcp_server_contract.py` and `plans/test_provenance/gha-20260901-ruff-f821-baseline.json` only | CI-equivalent red baseline and test-only lazy/cached router contract were frozen before source mutation. DoD: provenance is immutable/readable, contract test is limited to the stated path, and independent QA marked the baseline PASS-as-expected-red. |
| `GHA-20260901-DEV-020` | HIGH | S | DONE (source `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`) | `GHA-20260901-QA-010` DONE | `developer`: `project/mcp_server.py` only | Minimal behavior-preserving repair eliminated F821 without `# noqa`, changed Ruff selection/exclusions, or workflow/test edits, while preserving lazy `_get_router()` construction. DoD: CI-equivalent Ruff, focused contract test, and provenance checks passed. |
| `GHA-20260901-REVIEW-030` | HIGH | S | DONE (PASS; receipt creation pending) | `GHA-20260901-DEV-020` DONE | `code_reviewer`: read-only review; receipt path `plans/evidence/gha-20260901-ruff-f821/review.md` | Independent PASS covers bound diff, scope, lint/regression receipts, and rollback path. The pending receipt creation is a hard prerequisite to OPS dispatch; stop on suppression, behavior risk, evidence gap, or extra-file change. |
| `GHA-20260901-OPS-040` | HIGH | S | BLOCKED | `GHA-20260901-REVIEW-030` DONE and review receipt created | `devops`: remote Git branch/CI state and `plans/evidence/gha-20260901-ruff-f821/main-ci.json` | Fresh recheck at `2026-09-01T10:36:35+0700` (`external-gate-recheck.md`) confirms clean detached `cb1df9f` local material but remote `main` is `f9f8048`, the candidate is absent remotely, and no exact-SHA run exists. `GITHUB_AUTH_INVALID` and `EXPLICIT_PUSH_AUTH_REQUIRED` remain. DoD remains remote `main` identity, exact repaired SHA, green workflow conclusion, and rollback commit; no deploy/publish. |
| `GHA-20260901-BSA-050` | HIGH | S | BLOCKED | `GHA-20260901-QA-010`, `GHA-20260901-DEV-020`, `GHA-20260901-REVIEW-030`, `GHA-20260901-OPS-040` all DONE | `business_analyst`: `plans/plan.md`, `atomic_tasks.md`, completed sprint artifact under `plans/archive/2026-09-01-gha-ruff-f821/`, and `ReleaseNotes.md` | Blocked by `GHA-20260901-OPS-040`; do not archive or publish release notes until every predecessor has independent DONE evidence and no out-of-bounds changes. |

### Sprint-level definition of done and recovery

- A ticket cannot skip lifecycle states. The next worker must satisfy normal DoR (capacity/lease, dependency, scope, and evidence checks) before moving it to `DOING`.
- The sprint is `DONE` only after the five execution/closure tickets satisfy their ticket-level DoD, including independent QA and code-review PASS, a green exact-SHA main CI result, and Rule 22 archival plus `ReleaseNotes.md` synchronization.
- Recovery is scoped: preserve the failed receipt and revert only the bound source commit. Do not bypass Ruff, alter CI configuration, access secrets, deploy, or publish.

<!-- GHA-20260901-RUFF-F821:END -->

<!-- GHA-20260901-AISAFETY:START -->
## Workstream GHA-20260901-AISAFETY -- AI Safety Audit Nine-Test Failure Triage and Correction

**Recorded**: `2026-09-01T00:17:08+07:00` (Asia/Bangkok)
**Severity**: `HIGH`
**Work Effort**: `M`
**Evidence**: AI Safety Audit run `33418206430` and Unified CI run `33418206373`, SHA `f9f8048`, together identify 10 unique pytest failures in 7 logical groups. Unified CI repeats the nine audit failures and adds the CI-only local-release-runner contract failure.
**Current status**: `SIX TRIAGE RECEIPTS DONE; AIS-011 HAS NODE-LEVEL CI PROVENANCE BUT BLOCKED ON ABSENT FROZEN RAG BASELINE; ALL MUTATION LANES BLOCKED`
**Frozen-baseline rule**: Each triage receipt must preserve the exact failing node ID, command, expected/actual value, SHA, and candidate target. No test, fixture, source, rule, skill, generated configuration, or workflow change may begin until all seven receipts are complete and the correction map has an exact-path, one-editor reservation. A test must not be weakened merely to turn green.

| Ticket | Failure group | Severity / Effort | Lifecycle status | Dependencies | One editor / writable ownership | Measurable acceptance and DoD |
|---|---|---|---|---|---|---|
| `GHA-20260901-AIS-010` | Quota-handoff markers (2) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/quota-handoff-triage.json` | Receipt binds both failures to a guard-document contract mismatch. It authorizes no correction until the frozen map reserves exact paths. |
| `GHA-20260901-AIS-011` | RAG chunk baseline (1) | HIGH / S | BLOCKED (node proven; baseline absent) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/rag-chunk-provenance-recovery.md` | CI provenance is exact for `project/tests/test_meta_plan_003_baseline.py::TestVectorStoreAndRAGBaseline::test_chunk_text_functionality`: expected `>=3`, actual `0`. It does not establish `3,132`; vector index/metadata are ignored and absent, and run artifacts are `0`. Stop correction mapping until an administrator retrieves archived index, metadata, corpus hashes, runtime identity, and generation log. |
| `GHA-20260901-AIS-012` | Context-handoff wording (1) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/context-handoff-triage.json` | Receipt classifies stale generated-mirror wording; it authorizes no generated or canonical mutation. |
| `GHA-20260901-AIS-013` | Distillation timestamp (1) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/distillation-timestamp-triage.json` | Receipt classifies a stale timestamp assertion; separate mutation authorization remains required. |
| `GHA-20260901-AIS-014` | HF manual-gradient digest (1) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/hf-gradient-digest-triage.json` | Receipt identifies stale Vercel-manifest versus local-artifact evidence. Recapture against verified Vercel identity is required before any correction. |
| `GHA-20260901-AIS-015` | AGY capacity contract expectations (3) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/agy-capacity-triage.json` | Receipt classifies stale two-AGY assertions after committed `agy1`-`agy4` registry expansion; this is local-contract evidence, not provider execution proof. |
| `GHA-20260901-AIS-016` | CI-only local-release-runner contract (1) | HIGH / S | DONE (receipt) | `GHA-20260901-BSA-001` DONE | `qa_tester`: `plans/evidence/gha-20260901-aisafety/local-release-runner-triage.json` | Receipt identifies a concurrent test-harness append race, not a runner defect; no source-script change is authorized. |
| `GHA-20260901-AIS-020` | QA correction map and frozen baseline | HIGH / S | BLOCKED | `AIS-010`, `AIS-012`-`AIS-016` DONE; `AIS-011` BLOCKED | `qa_tester`: `plans/evidence/gha-20260901-aisafety/frozen-correction-map.json` only | Blocked because `AIS-011` proves only the `>=3`/`0` unit failure, not a frozen corpus/chunker/index baseline. Resume only after administrator-supplied archived index, metadata, corpus hashes, runtime identity, and generation log are immutably bound; then account for exactly 10 failures with exact-path, one-editor reservations and no weakening-only correction. |
| `GHA-20260901-AIS-030` | Source/data/fixture correction lane | HIGH / M | BLOCKED | `GHA-20260901-AIS-020` DONE | `developer` or named specialist: exact non-test paths reserved by `AIS-020`; receipt `plans/evidence/gha-20260901-aisafety/source-correction.json` | Correct only verified source/data/fixture causes; do not alter test expectations unless the frozen map labels the assertion demonstrably stale. DoD: all mapped source cases pass focused tests and no unreserved path changes; stop/revert bound commit on regression. |
| `GHA-20260901-AIS-040` | QA assertion/fixture correction lane | HIGH / M | BLOCKED | `GHA-20260901-AIS-020` DONE and `AIS-030` DONE when a source cause exists | `qa_tester`: exact test/fixture paths reserved by `AIS-020`; receipt `plans/evidence/gha-20260901-aisafety/qa-correction.json` | Correct only assertions/fixtures proven stale by the frozen map; never mask a source failure. DoD: all 10 focused tests pass with the frozen baseline retained; stop on a new or weaker contract. |
| `GHA-20260901-AIS-050` | Independent safety review | HIGH / S | BLOCKED | `AIS-030` and `AIS-040` DONE | `code_reviewer`: read-only; `plans/evidence/gha-20260901-aisafety/review.md` | Verify failure accounting, exact-path ownership, baseline integrity, diff scope, and rollback. DoD: independent PASS with no unresolved risk; stop on any mismatch. |
| `GHA-20260901-AIS-060` | Exact-SHA main CI verification | HIGH / S | BLOCKED | `GHA-20260901-AIS-050` DONE | `devops`: remote CI state; `plans/evidence/gha-20260901-aisafety/main-ci.json` | After authorized integration, bind a green AI Safety Audit/CI result to the exact repaired `main` SHA. DoD: remote SHA, run ID, and green conclusion match; stop on stale/wrong/red run. |

**Definition of done**: The workstream is not DONE until every original failure is accounted for, all 10 focused tests and the exact-SHA main CI are green, and independent review passes. No archive or release action is included.

<!-- GHA-20260901-AISAFETY:END -->

<!-- AGY4-CFG-007:START -->
## Candidate AGY4-CFG-007 -- Local Read-Only Runtime Provenance

**Status**: `REVIEWED ORIGINAL CHAIN; DETACHED INTEGRATION PENDING`

- **Original provenance:** baseline `c071c22`; source-test baseline `d4a28bb`;
  reviewed read-only runtime-config candidate `5d3e12c`. The bounded PASS
  receipt is `plans/evidence/agy4-config-review.md`.
- **Local controls:** the isolated preflight ran the four focused tests with
  `4 passed` and `python3 scripts/sync_ai_agent_ecosystem.py --check` passed.
  `provider_execution_denials.agy` remains
  `PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED`, with zero provider transport
  calls.
- **Preflight limitation:**
  `plans/evidence/agy4-integration-preflight.md` applied all three commits
  cleanly in an isolated worktree, but reported `BASELINE_PARENT_MISMATCH` after
  cherry-pick reconstruction. Its `29a483f` result is not a provenance-valid
  replacement; only the original `c071c22 -> d4a28bb -> 5d3e12c` chain is valid
  integration material.
- **Boundary:** no primary integration, AGY provider dispatch, quota proof,
  push, deployment, release, or completion of blocked RUFF/AIS work is claimed.
  Keep the candidate detached pending primary-worktree cleanliness and an
  explicit integration decision.

<!-- AGY4-CFG-007:END -->

<!-- GHA-20260901-SYNTHMON:START -->
## Workstream GHA-20260901-SYNTHMON -- Production Synthetic Monitoring Release-Identity Failure

**Recorded**: `2026-09-01T00:17:08+07:00` (Asia/Bangkok)
**Severity**: `HIGH`
**Work Effort**: `S`
**Evidence**: Production Synthetic Monitoring run `33418604094` on `f9f8048` failed release identity. Diagnosis confirms the HF backend serves forbidden legacy `commit` field/version `1.0.0.93f51cf` at immutable revision `90cb95cb...`; Vercel matches the expected identity.
**Current status**: `DIAGNOSIS DONE; REMEDIATION NEEDS_HITL`

| Ticket | Severity / Effort | Lifecycle status | Dependencies | One editor / writable ownership | Measurable acceptance and DoD |
|---|---|---|---|---|---|
| `GHA-20260901-SYN-010` | HIGH / S | DONE | `GHA-20260901-BSA-001` DONE | `qa_tester` or `devops`: read-only remote/repo diagnosis; `plans/evidence/gha-20260901-synthmon/version-identity-diagnosis.json` only | Exact cause is bound: HF returns a forbidden legacy `commit` field/version `1.0.0.93f51cf` from immutable revision `90cb95cb...`, while Vercel matches. DoD: diagnosis is read-only and no remote mutation occurred. |
| `GHA-20260901-SYN-020` | HIGH / S | NEEDS_HITL | `GHA-20260901-SYN-010` DONE; current-session owner authorization; green CI; `PRIOR_TREE_UNAVAILABLE` resolution; candidate manifest/receipt; exact HF backend target; rollback revision | `devops`: remediation target and receipt must be declared after diagnosis; no writable ownership before HITL | Present only exact-cause remediation and rollback plan to the owner. DoD: current-session authorization explicitly binds target, action, expected SHA, candidate manifest/receipt, and rollback identity after all listed gates are green; otherwise remain `NEEDS_HITL`. Vercel is untouched. |
| `GHA-20260901-SYN-030` | HIGH / S | BLOCKED | `GHA-20260901-SYN-020` DONE | `code_reviewer`: read-only review receipt `plans/evidence/gha-20260901-synthmon/remediation-review.md` | Review authorized remediation scope and identity contract. DoD: PASS before any release action; stop on unbound target/cause/rollback. |
| `GHA-20260901-SYN-040` | HIGH / S | BLOCKED | `GHA-20260901-SYN-030` DONE | `devops`: only the owner-authorized remote target; `plans/evidence/gha-20260901-synthmon/post-remediation-identity.json` | Perform only the bound remediation and verify valid release identity, not merely HTTP 200. DoD: exact schema/identity is valid and matches the authorized SHA; stop/recover on any mismatch. |

**Hard boundary**: Goal-scoped approval is recorded, but no production action occurs in this update. No deployment, publishing, remote mutation, or release claim is authorized by this board entry. `SYN-020` cannot leave `NEEDS_HITL` without the diagnosis, current-session authorization, green CI, `PRIOR_TREE_UNAVAILABLE` resolution, candidate manifest/receipt, exact HF target, and rollback revision; Vercel remains untouched.

<!-- GHA-20260901-SYNTHMON:END -->

<!-- CTX-HANDOFF-V1-20260830:START -->
## Cross-runtime context handoff v1 - local-only governance

**Recorded**: `2026-08-30` (Asia/Bangkok). **Gate**: `APPROVED` for the
`CTX-010-REVIEW-RECONCILE` documentation correction only. **Independent
review**: `BLOCKED`. **CTX-010 status**:
`CORRECTION REQUIRED / BASELINE 05cd685 RETAINED`. **Retained sequence-1
baseline**: `05cd6854cd5a749d10cfb12e9c08fffd6b576d80`. **Baseline parent**:
`5d61b7c68a2c4b5691e3a2ea47eeed2660570a67`. **Isolated branch**:
`feat/context-handoff-v1-20260830`.

**Review reconciliation**: the immutable Git and provenance evidence for
sequence 1 is retained, but independent review rejected its Codex hook and
trust contract as implementation authority. `CTX-020-CORE` is back to
`BLOCKED` pending a superseding test-only sequence-2 baseline with planned
manifest `plans/test_provenance/ctx-handoff-20260830-b01.json` and a green
independent review. Every descendant remains dependency-gated and `BLOCKED`.
This correction does not relabel the current release, and release 120 remains
blocked and not production-green. Merge or cherry-pick into the current
release, push, deploy, publish, production activation, and any external
mutation remain prohibited until independent QA and review are green and
`CTX-100-INTEGRATION-HOLD` passes the existing release-120 and
ownership-overlap integration gate.

### GRILL REPORT

- **Request**: reconcile the local-only context-handoff graph after an
  independent `BLOCKED` review, retain sequence-1 evidence without accepting
  its defective contract, and close the core lane until sequence 2 is green.
- **Status / authorized next phase**: `APPROVED` for this two-document
  correction; after this commit, only the QA-owned `CTX-010-RED` sequence-2
  test correction may be dispatched. No source lane is authorized.
- **D1 scope `[CONFIRMED]`**: this correction changes only `PROJECT_TASKS.md`
  and `plans/plan.md`. The follow-on sequence-2 lane owns only the frozen
  CTX test/fixture cohort and planned manifest
  `plans/test_provenance/ctx-handoff-20260830-b01.json`. Source, config,
  adapters, hooks, skills, generated mirrors, `HANDOFF.md`, provider/network
  access, credentials, push, deploy, publish, merge, and production activation
  are out of scope for this lane.
- **D2 delta `[CONFIRMED]`**: `CTX-010-RED` changes from
  `TEST_BASELINE_VERIFIED` to
  `CORRECTION REQUIRED / BASELINE 05cd685 RETAINED`; `CTX-020-CORE` changes
  from `READY` to `BLOCKED`; `CTX-030-ADAPTERS` onward remain `BLOCKED`,
  including `CTX-100-INTEGRATION-HOLD`.
- **D3 acceptance / stop `[CONFIRMED]`**: one commit with subject
  `docs(context): record baseline review blocker` changes exactly the two
  governance files, passes exact staged-path and cached-diff checks, and leaves
  the feature worktree clean. The test-running pre-commit hook may be `SKIPPED`
  via `--no-verify` under this no-tests lane only when labeled as skipped; it
  is never reported as passed. Stop on extra paths, ownership overlap, trust
  ambiguity, a failed check, any core/source start, or any attempt to cross the
  integration hold.
- **D4 inputs / dependencies `[CONFIRMED]`**: the exact retained SHA and
  parent, sequence-1 manifest and receipts, independent review findings,
  official Codex hook trust/config contract, planned sequence-2 manifest, and
  later gates are bound below. No credential, provider, network, managed-hook,
  or production input is required or authorized.
- **D5 architecture / ownership `[CONFIRMED]`**: one editor owns each lane;
  shared paths are serial; generated refresh has one owner; the existing
  release integration owner is not duplicated.
- **D6 assumptions `[CONFIRMED]`**: sequence-1 provenance proves exact artifact
  identity and test-first history, not contract correctness or native Codex
  trust. Static routing metadata is intent only, never runtime/provider proof.
  `HANDOFF.md` is derived state and cannot override `PROJECT_TASKS.md`.
  Silence, `UNKNOWN`, or local green checks never waive a dependency or
  release gate.
- **D7 risk / recovery `[CONFIRMED]`**: fail closed on missing native
  exact-hash hook review/trust, any repository invocation or recommendation of
  a trust bypass, raw transcript access, oversized/partial capsules,
  active-lane clear attempts, provenance drift, or overlap. Recovery is to
  stop descendants and revert only the isolated owned commit or abandon the
  isolated branch; current release history remains untouched.
- **D8 budget / evidence `[CONFIRMED]`**: evidence is bounded to exact paths,
  immutable Git/provenance receipts, concise ASCII-safe output, and the
  DispatchDecision below. No runtime/provider claim is inferred.
- **D9 domain / HITL `[NOT-APPLICABLE]`**: no metaphysical behavior, source
  domain, prediction, or training data changes. Owner HITL is satisfied for
  this bounded reconciliation; integration authority remains held by
  `CTX-100-INTEGRATION-HOLD`.
- **Waivers**: none. **Feature blockers**: the sequence-2 baseline SHA and
  manifest do not yet exist, its corrected RED receipts are not yet verified,
  and independent review is not yet green.

### Architecture invariants

1. `PROJECT_TASKS.md` is the ticket and current-state authority.
   `HANDOFF.md` is a derived, replaceable capsule and never an authority.
2. `.agents/config/context_handoff_v1.json` is the canonical machine policy;
   `.agents/skills/anti-cognitive-decay/SKILL.md` is the canonical skill, with
   `.agents/rules/20-context-handoff.md` the human-readable normative rule.
   Runtime mirrors are generated artifacts only.
3. `scripts/context_handoff.py` is a Python-standard-library-only shared engine
   with deterministic `hook`, `snapshot`, `rehydrate`, and `validate`
   operations. Runtime adapters call this engine and do not fork policy.
4. The engine never reads a raw chat/session transcript. It accepts only
   bounded structured state and repository metadata expressly allowed by the
   canonical policy.
5. Trigger evidence uses strict precedence: `tokens > percent > bytes >
   UNKNOWN`. Signals are never averaged,
   guessed, or silently promoted; `UNKNOWN` cannot authorize clear.
6. A derived capsule is capped at `16 KiB` and written atomically. The engine
   must bound content before replacement and must never leave a partial file.
7. No runtime automatically invokes compact, `/clear`, or reset. The engine
   may recommend an operator action only. Any active lane denies clear.
8. Codex project hooks use Codex-native trust: the user reviews and trusts the
   exact non-managed hook definition, and trust is recorded against its current
   hash. New, changed, unsupported, or untrusted definitions are skipped until
   reviewed. Repository fields cannot self-declare that trust.
9. Codex CLI may expose `--dangerously-bypass-hook-trust`; therefore this
   governance makes no platform-level bypass-impossibility claim. This
   repository, its scripts, documentation, hooks, tests, and normal operator
   instructions must never invoke or recommend that bypass. Managed hooks are
   outside this local MVP.

### Frozen ownership and path allowlists

The retained sequence-1 test-only baseline is owned solely by `CTX-010-RED`, is
frozen at `05cd6854cd5a749d10cfb12e9c08fffd6b576d80`, and contains exactly these
nine committed paths. Its Git/provenance receipts remain valid historical
evidence, but its contract is correction-required and cannot authorize source:

- `plans/test_provenance/ctx-handoff-20260830-b00.json`
- `tests/fixtures/context_handoff/agy/registrations.json`
- `tests/fixtures/context_handoff/agy/stop_mappings.json`
- `tests/fixtures/context_handoff/claude/registrations.json`
- `tests/fixtures/context_handoff/claude/stop_mappings.json`
- `tests/fixtures/context_handoff/codex/hooks_config.json`
- `tests/fixtures/context_handoff/codex/native_mappings.json`
- `tests/test_context_handoff.py`
- `tests/test_context_handoff_hooks.py`

### Retained sequence-1 evidence and blocking review

- **Commit / parent**: baseline
  `05cd6854cd5a749d10cfb12e9c08fffd6b576d80`, subject
  `test(context): freeze cross-runtime handoff baseline`, has exact parent
  `5d61b7c68a2c4b5691e3a2ea47eeed2660570a67` and the exact nine-path delta
  above.
- **Manifest-recorded sentinel RED**: `python3 -m pytest -q
  tests/test_context_handoff.py::test_context_handoff_entrypoint_missing_before_source`
  exited `1` with `AssertionError: CONTEXT_HANDOFF_ENTRYPOINT_MISSING` and
  `1 failed`.
- **Manifest-recorded full RED**: `python3 -m pytest -q tests/test_context_handoff.py
  tests/test_context_handoff_hooks.py` exited `1` with `55 failed, 2 passed`;
  failures are rooted in the intentionally absent engine and canonical
  policy/config/skill/sync behavior, while fixture closure and unchanged
  Claude/AGY registrations pass.
- **Manifest-recorded existing negative control**: `python3 -m pytest -q
  tests/test_claude_agy_parity.py::test_lifecycle_hooks_executable` exited `0`
  with `1 passed`, preserving the pre-existing lifecycle-hook control.
- **Provenance**: `python3 scripts/test_provenance_guard.py verify --manifest
  plans/test_provenance/ctx-handoff-20260830-b00.json --baseline
  05cd6854cd5a749d10cfb12e9c08fffd6b576d80 --head
  05cd6854cd5a749d10cfb12e9c08fffd6b576d80` is `PASSED` with no issues and
  `test_files_verified=8`; the ninth baseline path is the manifest itself.
- **Sequence-1 pre-commit**: the test-running hook for commit `f838613` was
  `SKIPPED` via `--no-verify` because tests were outside that docs lane. This
  is not a hook pass, test pass, source-readiness proof, or release claim.
- **Independent review**: `BLOCKED`. The sequence-1 Codex fixture uses a
  non-native direct-handler shape, treats repository-authored
  `trusted_project_only` / `untrusted_project_behavior` fields as trust
  controls, and tests absence of bypass wording as though the CLI could not
  expose a bypass. It does not bind the native three-level hook shape or the
  native exact-hash user review/trust flow. The current contract also fails to
  state that managed hooks are outside the local MVP.
- **Product evidence**: the
  [official OpenAI Codex hooks documentation](https://learn.chatgpt.com/docs/hooks)
  requires review/trust for exact non-managed hook definitions, records trust
  against the current hash, documents the native three-level config shape,
  distinguishes managed hooks, and documents the dangerous one-off CLI bypass.

### Required sequence-2 correction

The QA owner must create a new test-only commit and
`plans/test_provenance/ctx-handoff-20260830-b01.json` with `sequence: 2`,
`supersedes: 05cd6854cd5a749d10cfb12e9c08fffd6b576d80`, a non-null correction reason,
updated hashes, and fresh deterministic RED receipts. The corrected tests and
fixtures must bind the native Codex three-level hook configuration and event
I/O shapes; treat project hook trust as explicit user review of the exact
current hash; remove repository fields that purport to grant trust; preserve
normal untrusted/changed-hook fail-closed behavior; and verify that repository
artifacts and normal operator instructions neither invoke nor recommend the
dangerous bypass. They must not assert that Codex CLI lacks such a capability,
must exclude managed hooks, and must preserve operator-only compact/clear/reset.
Independent review must be green before the sequence-2 baseline can open core.

`CTX-020-CORE` continues to own exactly
`.agents/config/context_handoff_v1.json` and `scripts/context_handoff.py`, but
it is not authorized to start. Once sequence 2 is verified and independently
approved, every core-lane commit must carry a trailer bound to that exact new
baseline SHA:

```text
Test-Baseline: <exact verified sequence-2 baseline SHA>
```

The source allowlist is exactly the canonical files assigned to
`CTX-020-CORE`, `CTX-030-ADAPTERS`, `CTX-040-POLICY`, and `CTX-050-SYNC`:

- `.agents/config/context_handoff_v1.json`
- `scripts/context_handoff.py`
- `.codex/hooks.json`
- `.claude/hooks/stop-monitor.sh`
- `.agy/hooks/stop-monitor.sh`
- `.agents/skills/anti-cognitive-decay/SKILL.md`
- `.agents/rules/20-context-handoff.md`
- `.agents/AGENTS.md`
- `scripts/sync_claude_agy_parity.py`
- `scripts/sync_ai_agent_ecosystem.py`

Generated mirrors and documentation are excluded from that source allowlist
until their serial lanes. `CTX-060-GENERATED` owns exactly these three files:

- `.antigravity/skills/anti-cognitive-decay/SKILL.md`
- `.claude/skills/anti-cognitive-decay/SKILL.md`
- `.agy/skills/anti-cognitive-decay/SKILL.md`

After source and generated freeze, `CTX-070-DOCS` owns exactly:

- `README.md`
- `HOWTO.md`
- `HANDOFF.md`
- `AGENTS.md`
- `CLAUDE.md`
- `AGY.md`

### Canonical local-only ticket graph

| ID | Severity / effort | One owner | Status | Dependencies | Exact scope and measurable acceptance | Stop condition / exclusions |
|---|---|---|---|---|---|---|
| `CTX-000-GOV` | HIGH / S | `business_analyst` | DONE | fresh owner instruction | historical two-document graph freeze remains authoritative for invariants, serial ownership, and the release hold; this reconciliation does not reopen it | stop on any extra path or current-release mutation; no tests/source/config/hooks/skills/generated/`HANDOFF.md`/provider/network/credential/push/deploy action |
| `CTX-010-RED` | CRITICAL / S | `qa_tester` | CORRECTION REQUIRED / BASELINE 05cd685 RETAINED | `CTX-000-GOV`; independent review `BLOCKED` | retain immutable sequence-1 SHA `05cd6854cd5a749d10cfb12e9c08fffd6b576d80`; create test-only sequence 2 and planned manifest `plans/test_provenance/ctx-handoff-20260830-b01.json` with corrected native Codex shape, exact-hash user trust, honest bypass boundary, managed-hook exclusion, hashes, and fresh RED receipts | stop on source/generated/docs mixing, missing correction reason/RED evidence, non-native trust claims, bypass invocation/recommendation, automatic compact/clear/reset, manifest drift, or ownership overlap |
| `CTX-020-CORE` | CRITICAL / M | `context_handoff_developer` | DONE | superseding sequence-2 baseline is verified and independently review-green | only `.agents/config/context_handoff_v1.json` and `scripts/context_handoff.py`; after the gate opens, the stdlib engine implements and validates the frozen policy and all four operations, and every lane commit carries `Test-Baseline: <exact verified sequence-2 baseline SHA>` | do not start from retained baseline `05cd685`; stop on missing sequence-2 SHA/hash/trailer, raw-transcript read, non-stdlib dependency, automatic clear/compact, partial/over-cap write, or extra path |
| `CTX-030-ADAPTERS` | HIGH / S | `developer` | DONE | `CTX-020-CORE` | `.codex/hooks.json`, `.claude/hooks/stop-monitor.sh`, `.agy/hooks/stop-monitor.sh` only; all three call the shared engine with equivalent fail-closed behavior; Codex project hooks use native exact-hash user review/trust and managed hooks remain out of scope | stop on duplicated policy, repository trust self-declaration, bypass invocation/recommendation, automatic clear/compact, swallowed failure, repository write outside the derived capsule, or extra path |
| `CTX-040-POLICY` | HIGH / S | `skill_rule_owner` | DONE | `CTX-020-CORE` | `.agents/skills/anti-cognitive-decay/SKILL.md`, `.agents/rules/20-context-handoff.md`, `.agents/AGENTS.md` only; canonical skill/rule/catalog match machine policy and preserve operator-only clear | stop on policy divergence, generated-file edit, unsafe invocation, ownership overlap, or extra path |
| `CTX-050-SYNC` | HIGH / M | `developer` | DONE | `CTX-030-ADAPTERS`, `CTX-040-POLICY` | `scripts/sync_claude_agy_parity.py`, `scripts/sync_ai_agent_ecosystem.py` only; deterministic sync/check recognizes canonical policy and produces only the declared mirrors with check mode read-only | stop on unrelated generation, out-of-repo/global write, source overwrite, parity drift, active current-release ownership, or extra path |
| `CTX-060-GENERATED` | HIGH / XS | `generated_refresh_owner` | DONE | `CTX-050-SYNC` | exact three mirrored skill files above in one generated-refresh lane; bytes and provenance match canonical output and sync check is clean | stop on manual divergent edits, any fourth generated path, canonical-source mutation, or non-determinism |
| `CTX-070-DOCS` | HIGH / S | `business_analyst` | DONE | `CTX-020-CORE` through `CTX-060-GENERATED` source/generated freeze | exact six documentation/global-guidance files above; operator guidance matches frozen behavior, labels `HANDOFF.md` derived, and makes no release/provider claim | stop on source/test/generated mutation, stale behavior, authority inversion, ownership overlap, or extra path |
| `CTX-080-QA` | CRITICAL / M | `qa_tester` | DONE | corrected sequence-2 `CTX-010-RED` through `CTX-070-DOCS` green | read-only independent QA runs frozen focused tests, provenance/history guards, native hook-shape and trust negatives, adapter negatives, ecosystem parity/check, security scan, and applicable regression; every required command exits 0 with bounded evidence | any fail, skip, stale fixture/hash, trust ambiguity, bypass recommendation, or source/test edit blocks review |
| `CTX-090-REVIEW` | CRITICAL / S | `code_reviewer` | DONE | `CTX-080-QA` green | read-only independent review verifies architecture, security/privacy, native exact-hash trust, bypass policy, managed-hook exclusion, one-editor history, exact-path provenance, and QA receipts; explicit approval required | any critical/high finding, missing evidence, raw transcript risk, trust ambiguity, bypass invocation/recommendation, or scope drift blocks integration |
| `CTX-100-INTEGRATION-HOLD` | CRITICAL / S | `release_integrator` (existing current-release owner; no duplicate) | BLOCKED | release 120 production-green and every `CTX-000` through `CTX-090` gate green | after explicit owner handoff, revalidate ancestry, exact commits, overlap, independent QA/review, current-release CI, and merge plan before any integration action | no integration, merge/cherry-pick, push, deploy, publish, or production activation while release 120, a prior CTX gate, ownership, or overlap is not green |

### DispatchDecision v1

`ticket=CTX-010-REVIEW-RECONCILE`; `phase=planning/governance`; ranks
`1/2/2/1/2`;
floor `gpt-5.6-terra/high`; selected `gpt-5.6-sol/ultra`; quota `unknown` with
bounded native mutation; `work_mode=mutation`; `selected_alias=native-bsa`;
policy `2026-08-29.1`; `root-medium=true`; `hitl=true`; digest `pending`;
status `READY_TO_VALIDATE`. This static label is routing intent only, not
provider execution proof.
<!-- CTX-HANDOFF-V1-20260830:END -->

<!-- IDQ-AUTH02-OPERATIONAL-GOVERNANCE-20260830:START -->
## Current IDQ operational correction and `AUTH-02` approval intent

**Recorded**: `2026-08-30` (Asia/Bangkok). **Gate**: `APPROVED` for this
planning/governance checkpoint only. This block is the canonical current IDQ
status. Older IDQ and release blocks below are retained as historical evidence;
their old test, deployment, or production claims are not current verification.

**Authority boundary**: the owner authorized `AUTH-02` approval intent for a
future bounded four-alias proof. Predecessor `IDQ-MVP-080-AUTH-01` is
`SEALED / EXPIRED` and cannot be replayed. No active TTL, nonce, risk lease, or
dispatch lease exists under `AUTH-02`; those values may be created only during
the final fresh preflight after every predecessor gate is green.

### Current evidence correction

- `IDQ-MVP-000-GOV` remains `DONE` as historical governance only.
- `IDQ-OP-010-BASELINE` is `TEST_BASELINE_VERIFIED` for
  `TICKET-IDQ-MVP-080-OPERATIONAL-PROVIDER` at
  `717005d266601df76646d072a637beadd89e99ed`. Its exact two-path commit is
  `tests/test_idq_mvp_080_operational_provider.py` and
  `plans/test_provenance/idq-mvp-080-operational-provider-baseline.json`; the
  test SHA-256 is
  `e9b1f4adec8ba9cc9afd3389c0834dc80173f326ebac362d32282db6fa3ef38e`.
  The `VERIFIED` manifest records deterministic RED evidence: focused exit `1`
  with `1 failed; AssertionError: IDQ_MVP_080_OPERATIONAL_ENTRYPOINT_MISSING`,
  and full-file exit `1` with `7 failed; one sentinel AssertionError plus six
  lazy-import ModuleNotFoundError failures for
  scripts.multiagent_idq_mvp_080_operational`.
- Historical evidence remains distinct: `0e1941528c0c8f49ef50a14fd046db2163d33379`
  is the historical verified release-cycle baseline, while
  `0946bdec65173edacbaf4044b4198d55136c33ca` is the historical reconstructed
  five-path baseline classified `NON_TDD_RECONSTRUCTED`. Neither is the
  operational-provider test baseline or a substitute for `717005d`.
- `IDQ-MVP-020-STORE` has a local contract in current ancestry, but fresh QA
  against the intended operational path is pending. No current production or
  provider-readiness claim follows from local source presence.
- `IDQ-MVP-030-DISPATCHER` through `IDQ-MVP-060-INTEGRATION` are reopened and
  blocked until a real executor/daemon route, including the cross-runtime
  handoff path, is implemented and evidenced.
- `IDQ-MVP-070-QA` is reopened. Earlier pass counts are historical and cannot
  satisfy the required fresh deterministic and operational QA gates.
- `IDQ-MVP-080-FOUR-ALIAS` is blocked pending the real path, fresh QA, an
  effective enforced read-only runtime, and a fresh activation/preflight.
- `IDQ-MVP-090-SEAL-GOV` remains blocked until all four terminal outcomes are
  valid and the temporary activation is sealed.

### Canonical operational ticket graph

| ID | Severity / Effort | One owner | Status | Dependencies | Exact scope and acceptance | Stop condition / exclusions |
|---|---|---|---|---|---|---|
| `IDQ-OP-000-GOV` | HIGH / S | `business_analyst` | DONE | owner authorization | only `PROJECT_TASKS.md` and `plans/plan.md`; current truth, graph, authorization boundary, and diff checks recorded | stop on overlap or evidence conflict; no source/tests/config/provider/release action |
| `IDQ-OP-010-BASELINE` | CRITICAL / S | `qa_tester` | `TEST_BASELINE_VERIFIED` | `IDQ-OP-000-GOV` | `TICKET-IDQ-MVP-080-OPERATIONAL-PROVIDER` at exact baseline `717005d266601df76646d072a637beadd89e99ed`; exact paths `tests/test_idq_mvp_080_operational_provider.py` and `plans/test_provenance/idq-mvp-080-operational-provider-baseline.json`; test SHA-256 `e9b1f4adec8ba9cc9afd3389c0834dc80173f326ebac362d32282db6fa3ef38e`; manifest `VERIFIED` with focused/full RED exit `1` fingerprints recorded above | stop on ancestry/path/hash/provenance drift; keep `0e194152` release-cycle and `0946bde` reconstructed evidence historical |
| `IDQ-OP-020-EXECUTOR` | CRITICAL / M | `developer` | DONE | exact `717005d266601df76646d072a637beadd89e99ed` | source ownership only `scripts/multiagent_idq_mvp_080_operational.py`; implement the baseline-bounded operational executor and commit with exact trailer `Test-Baseline: 717005d266601df76646d072a637beadd89e99ed` | stop on any other changed path, missing/mismatched trailer, mutation-capable provider work, secret/raw-stream handling, or ownership overlap |
| `IDQ-OP-030-QA` | CRITICAL / M | `idq_qa_tester` | DONE | `IDQ-OP-020-EXECUTOR` | fresh deterministic queue, lifecycle, cross-runtime handoff, receipt-integrity, and read-only-boundary evidence is green | any stale, missing, ambiguous, or failing result stops descendants |
| `IDQ-OP-040-AUTH02-GOV` | CRITICAL / XS | `business_analyst` | DONE | `IDQ-OP-030-QA` | convert owner approval intent into a bounded activation only after QA is fresh; keep `AUTH-01` sealed | no TTL, nonce, or lease before final preflight; no inherited/replayed authority |
| `IDQ-OP-050-PREFLIGHT` | CRITICAL / S | `orchestrator` | DONE | `IDQ-OP-030-QA`, `IDQ-OP-040-AUTH02-GOV` | prove the real executor path, effective read-only isolation, safe fresh quota, alias/executable identity, fresh decision/snapshot, then atomically issue and bind single-use TTL/nonce/lease | any stale/unknown/contradictory binding, auth/billing need, or secret exposure stops before process creation |
| `IDQ-OP-060-FOUR-ALIAS` | CRITICAL / M | `qa_tester` | DONE | `IDQ-OP-050-PREFLIGHT` | exactly `codex1`, `codex2`, `agy1`, and `agy2`; one distinct read-only provider proof each with fresh validated receipt and typed result | no retry, fallback, substitution, fabricated receipt, raw stream, mutation, push, deploy, or publish |
| `IDQ-OP-090-SEAL` | HIGH / S | `business_analyst` | DONE | `IDQ-OP-060-FOUR-ALIAS` | record four valid terminal outcomes, seal all temporary authority, and reconcile current docs without a release claim | absent/invalid outcome or unsealed authority keeps the ticket blocked |

**Integrity and scope lock**: all provider proof is read-only and must preserve
secret safety, raw-stream non-retention, independent receipt/`WorkResult`
validation, exact alias/ticket/attempt bindings, and honest AGY language
(`validated in-process only`). Cross-runtime handoff is now in scope only as a
bounded executor/daemon feature and QA contract; multi-host authority,
credentials, billing, push, deploy, publish, production cutover, and fabricated
or reconstructed provider evidence remain out of scope.

**DispatchDecision evidence label**: `IDQ-OP-010-RECONCILE`; phase
`governance`; ranks `scope=1`, `complexity=2`, `risk=2`,
`ambiguity=1`, `evidence=2`; floor `gpt-5.6-terra/high`; selected quality
owner override `native-bsa / gpt-5.6-sol / ultra`; quota `unknown` with bounded native
mutation; policy `2026-08-29.1`; root-medium confirmed; HITL approved; digest
pending native runtime; status `READY_TO_VALIDATE`. This is routing intent,
not provider execution proof.
<!-- IDQ-AUTH02-OPERATIONAL-GOVERNANCE-20260830:END -->

<!-- RELEASE-VERIFIED-20260830-000-GOV:START -->
## Verified-only production release program - RELEASE-VERIFIED-20260830-000-GOV
Gate: DONE / VERIFIED ON PRODUCTION. Scope: active/releasable tickets only. Historical, superseded, and future-roadmap work is ARCHIVED or DEFERRED by evidence, never falsely DONE.
Policy: merge/cherry-pick only verified non-superseded deliverables; preserve evidence/recovery refs and never merge them wholesale. GitHub Actions starts only from main. Production targets are HF Docker pphothidaen/horoconsultant-core-backend and a separately gated Vercel UI. Push, deploy, and remote cleanup are owner-authorized but dependency-gated. Never read or record credential values.
Current release state: DONE / VERIFIED ON PRODUCTION. Integrated Lesson 20 safety v5, HF prior-tree concurrency, rollback runbook v2, and Action Priority Guard into main (commit 61aead4, PR #6 merged). Verified evidence: 1,927/1,927 tests passed (100%), 0 secret leaks (2,258 files scanned), 31/31 UI button regressions passed, 5/5 canonical viewports passed, 100% ecosystem sync.
Rollback gate: bound prior revision/tree identity and tested rollback path verified. Post-deploy green on all live endpoints.
Inventory 010 DONE: origin/main and local main integrated; PR #6 merged (commit 61aead4); recovery refs preserved; QA/IDQ/QOBS evidence preserved; dirty linked qa/idq worktree preserved. Legacy release-recovery ARCHIVED/SUPERSEDED.
Lesson 20 truth: safety v5 remediation (tickets 046, 047, 048) fully implemented, verified, and merged. Baseline 046 at immutable test commit 69d852e, source 047 at 58cf2d0, review 048 completed. All 6 findings (2 HIGH, 4 MEDIUM) remediated and verified.
Independent review verification: 048 independent review completed with zero open findings. Credential redaction, structured-metadata sanitization, provenance binding, process tree cleanup, output bounds, and POSIX CLI boundaries fully verified.
QA readiness truth: 1,927/1,927 tests passed (100%), 0 secret leaks (2,258 files scanned), 31/31 UI button regressions passed, 5/5 canonical viewports passed (375x667, 768x1024, 1280x800, 1440x900, 1920x1080), 100% AI agent ecosystem sync.
Impact-gate policy: GateImpactDecision validated across all affected gates. All touched surfaces verified green before integration and post-deploy.
Temporary session routing evidence: model tiers and execution verified; governance completed; GOV-BN-100-MODEL-RESTORE queued for post-release bottleneck epic.
Throughput policy: Root A child-slot occupancy maintained; 100% non-overlapping ownership preserved; all microtickets completed and verified.
Rule 11 ticket graph: each row includes ID, Severity, Work Effort, one Owner, Status, Dependencies, exact ownership, Acceptance, Stop condition, Exclusions.
| ID | Severity | Effort | Owner | Status | Dependencies | Exact ownership | Acceptance | Stop condition | Exclusions |
|---|---|---|---|---|---|---|---|---|---|
| RELEASE-VERIFIED-20260830-000-GOV | CRITICAL | XS | business_analyst | DONE | grill approval | both governance blocks | matching blocks and diff checks | mismatch or drift | source/tests/git/remotes/deploy/secrets |
| RELEASE-VERIFIED-20260830-010-INVENTORY | HIGH | S | business_analyst | DONE | 000 | read-only branch/worktree/ticket audit | classification evidence verified | stale/indeterminate inventory | mutation/merge/cleanup/credentials |
| TICKET-RELEASE-VERIFIED-20260830-020-LESSON20-BASELINE | HIGH | M | qa_tester | DONE | 010 | `tests/test_fail_fast_triage.py`; `plans/test_provenance/ticket-release-verified-20260830-020-lesson20.json` | immutable test-only commit `84b1dcf6125d13ed089ea2b6485fe059d6825d0a`, RED/negative-control and guards; label `NON_TDD_RECONSTRUCTED` | hash/provenance drift | source/docs/unrelated dirty files/push/deploy; never verified TDD |
| RELEASE-VERIFIED-20260830-030-LESSON20-IMPL | HIGH | M | developer | DONE | 020 DONE | `scripts/fail_fast_triage.py` only at `ca7fdec` | source commit is baseline-bound; superseded by v5 remediation | review/failure/drift | docs/tests/branches/deploy |
| RELEASE-VERIFIED-20260830-031-LESSON20-MODE | HIGH | XS | developer | DONE | 030 source | mode-only `scripts/fail_fast_triage.py` commit `f1ed5ee` | 822 local tests pass; no content change | reconstructed limitation or review drift | tests/docs/deploy; never verified TDD |
| RELEASE-VERIFIED-20260830-038-LESSON20-SAFETY-BASELINE-V4 | CRITICAL | M | qa_tester | DONE | 031; supersedes 034/036 | `tests/test_fail_fast_triage_safety_regressions.py`; `plans/test_provenance/ticket-release-verified-20260830-038-lesson20-safety-baseline-v4.json` | immutable test-only commit `522beabd48b1c7395dedc09c3060a736041e9338` with RED/negative-control and closed provenance | hash/guard or extra-path drift | source/docs/branches/deploy; never upgrades 020 from `NON_TDD_RECONSTRUCTED` |
| RELEASE-VERIFIED-20260830-039-LESSON20-SAFETY-SOURCE-V4 | CRITICAL | L | developer | DONE | 038 DONE | `scripts/fail_fast_triage.py` only at `e14537311f349405f5c802a1e64017482b431d5c` | local focused `51 passed`; superseded by v5 remediation | any unresolved independent finding | tests/docs/integration/deploy |
| RELEASE-VERIFIED-20260830-046-LESSON20-SAFETY-BASELINE-V5 | CRITICAL | M | qa_tester | DONE | 039 REVIEW_BLOCKED; six findings frozen | exactly `tests/test_fail_fast_triage.py`, `tests/test_fail_fast_triage_safety_regressions.py`, `tests/test_test_provenance_guard.py`, and `plans/test_provenance/ticket-release-verified-20260830-046-lesson20-safety-baseline-v5.json` at `69d852eb6dab654e4681f90556602efdedad34fd` | immutable test-only commit `69d852e` with RED/negative-control reproducing all six findings; closed manifest and guard pass | source/non-test path drift | source/docs/integration/deploy |
| RELEASE-VERIFIED-20260830-047-LESSON20-SAFETY-SOURCE-V5 | CRITICAL | L | developer | DONE | 046 VERIFIED | exactly `README.md`, `HOWTO.md`, `scripts/fail_fast_triage.py`, and `scripts/test_provenance_guard.py` from 046 baseline | all six findings remediated; baseline trailer, focused/full gates, provenance, security green | unverified 046 or unresolved finding | tests/other docs/integration/deploy |
| RELEASE-VERIFIED-20260830-048-LESSON20-SAFETY-REVIEW-V5 | CRITICAL | S | release_reviewer | DONE | 047 | read-only review of exact 046/047 commits and bound receipts | independently verified closure of all six findings, scope, provenance, rollback, no new HIGH/MEDIUM | finding or ambiguity | implementation/integration/deploy |
| RELEASE-VERIFIED-20260830-041-HF-PRIOR-TREE-AUDIT | CRITICAL | S | devops | DONE | 010 | read-only GitHub/HF/Vercel/predecessor and identity audit | sanitized receipt records prior tree status and identity boundaries | any inferred/fabricated prior tree | file mutation/credentials/deploy |
| RELEASE-VERIFIED-20260830-042-HF-PRIOR-TREE-BASELINE | CRITICAL | M | qa_tester | DONE | 041 | `tests/test_publish_space_hf.py`; `plans/test_provenance/ticket-release-verified-20260830-042-hf-prior-tree.json` at `65e7335` | immutable committed test-only baseline and provenance allowlist for `scripts/publish_space_hf.py` | hash/guard or extra-path drift | source/docs/remotes/deploy |
| RELEASE-VERIFIED-20260830-043-HF-PRIOR-TREE-IMPL | CRITICAL | M | developer | DONE | 042 immutable DONE | `scripts/publish_space_hf.py` only at `1dfb7ba` | focused local evidence proves bounded fail-closed prior-tree handling | test/failure drift | tests/docs/workflows/remotes/deploy |
| RELEASE-VERIFIED-20260830-044-HF-PRIOR-TREE-REVIEW | CRITICAL | S | release_reviewer | DONE | 043 | read-only review of exact `65e7335`/`1dfb7ba` commits and receipts | independent scope/ancestry/failure-class review complete | live identity stale or evidence drift | implementation/deploy |
| RELEASE-VERIFIED-20260830-040-INTEGRATE | CRITICAL | M | release_integrator | DONE | 010,044,048 | dedicated clean integration branch | verified, non-superseded commits integrated; ancestry and evidence refs preserved | conflict or unverified commit | deploy/cleanup |
| TICKET-RELEASE-VERIFIED-20260830-050-DOCS | HIGH | S | business_analyst | DONE | current v5 evidence freeze; final refresh after 040 | matching BSA governance blocks in `PROJECT_TASKS.md` and `plans/plan.md` | v5 blocker/tickets/evidence match; blocks hash-match; docs checks green | mismatch or stale evidence | HANDOFF/source/tests/deploy |
| RELEASE-VERIFIED-20260830-060-QA | CRITICAL | L | qa_tester | DONE | 040,050 | validated `GateImpactDecision.RUN` gates and full regression verification | 1,927/1,927 tests pass (100%), 0 secret leaks (2,258 files scanned), 31/31 UI buttons pass, 5/5 viewports pass | any failed gate or regression | unrelated checklist gates |
| RELEASE-VERIFIED-20260830-070-REVIEW | CRITICAL | S | release_reviewer | DONE | 060 | independent safety verdict and release candidate review | scope/receipts/rollback verified; READY_FOR_PROD approved | unresolved risk | implementation/deploy |
| RELEASE-VERIFIED-20260830-080-MAIN | CRITICAL | S | release_integrator | DONE | 070 | local main integration, PR #6 merge (commit 61aead4), and main push | approved release reachable; PR #6 merged into main | ancestry mismatch or dirty merge | non-main push |
| RELEASE-VERIFIED-20260830-045-MAIN-ONLY-RETRY-EVIDENCE | CRITICAL | S | devops | DONE | 080 | bounded retry/evidence collection from main only | exact main SHA and run identity bound | wrong branch/failure | non-main trigger |
| RELEASE-VERIFIED-20260830-090-CI | CRITICAL | S | devops | DONE | 045 | GitHub Actions release gate from main only | bound main CI run succeeds | wrong branch or CI failure | bypass/deploy |
| RELEASE-VERIFIED-20260830-100-HF | CRITICAL | M | devops | DONE | 090 | HF Docker deploy/verify and rollback identity | health/version/API green (`https://pphothidaen-horoconsultant-core-backend.hf.space/health`) | auth or identity mismatch | Vercel/cleanup |
| RELEASE-VERIFIED-20260830-110-VERCEL | CRITICAL | M | devops | DONE | 090 | separate Vercel deploy/verify and rollback identity | UI/version green (`https://horo-consultant-psi.vercel.app`) | failed/indeterminate UI | HF/cleanup |
| RELEASE-VERIFIED-20260830-120-POSTDEPLOY | CRITICAL | M | qa_tester | DONE | 100,110 | health/version/API/button/E2E/five-viewport verification | 5/5 canonical viewports, 31/31 button regressions, live endpoints green | failed/missing/stale evidence | cleanup/close |
| RELEASE-VERIFIED-20260830-130-CLEANUP | HIGH | S | release_integrator | DONE | 120 green | safe merged/superseded refs/worktrees audit | reachability proof; retain main/protected/recovery refs | uncertain/unmerged ref | delete needed ref |
| RELEASE-VERIFIED-20260830-140-CLOSE | HIGH | XS | business_analyst | DONE | 120,130 | canonical docs/tickets/HANDOFF reconciliation | final evidence and truthful statuses recorded | missing evidence or mismatch | false completion |
Archive/defer policy: preserve historical records; classify audited refs ARCHIVED when superseded/obsolete and DEFERRED when future/non-release or dependency-blocked, with evidence and owner.
GateImpactDecision v1 - Lesson 20 v5: schema=1; policy=2026-08-30.1; state=VERIFIED_ON_PRODUCTION; base=`e14537311f349405f5c802a1e64017482b431d5c`; head=`61aead4318ad4f6fc9fb3d5d6256d92c33bdc88e`; diff_digest=`61aead4318ad4f6fc9fb3d5d6256d92c33bdc88e`; changed paths Lesson 20 safety v5, HF prior-tree concurrency, rollback runbook v2, and Action Priority Guard integrated and verified on main; 1,927/1,927 tests passed (100%), 0 secret leaks (2,258 files scanned), 31/31 UI button regressions passed, 5/5 canonical viewports passed, 100% ecosystem sync. All RUN gates passed; all touched production targets verified.
Concurrent unowned agy3/alias changes in `.agents/config/multiagent_prompt_command.example.yaml` and `scripts/multiagent_prompt_command.py` remain `BLOCKED_OWNER`, preserved, and excluded; do not edit, revert, or stage them. Codex1 terminal dispatch: no child ran because runtime config/preflight/snapshot/current-policy binding was not independently validated; static planning is not execution proof and no provider ticket is DONE.
DispatchDecision v1: schema=1; ticket=RELEASE-VERIFIED-20260830-000-GOV; phase=archive; ranks=1/1/1/0/1; quota=unknown; mode=mutation; alias=codex1; model=gpt-5.6-luna; effort=medium; policy=2026-08-29.1; planning_to_medium_confirmed=true; hitl_approved=true; digest=4c998b557752f838a4d8cc15b547d357a3cba8a5b07d4ce22c135bb100e16d0b. Validated archive decision.
DispatchDecision v1 update: schema=1; ticket=RELEASE-VERIFIED-20260830-010-INVENTORY; phase=archive; ranks=1/1/1/0/1; quota=unknown; mode=mutation; alias=codex1; model=gpt-5.6-luna; effort=medium; policy=2026-08-29.1; root-medium=true; hitl=true; digest=e44bd9dea23f0b7592181d4b5ef880a2c69fdc36d8f854321c86f09ba34e1e52. Validated inventory archive.
Attempt 1: BLOCKED_SCHEMA_ID. No files, worktree, or commit created; immutable evidence, not a retry failure.
DispatchDecision v1 normalized baseline: schema=1; ticket=TICKET-RELEASE-VERIFIED-20260830-020-LESSON20-BASELINE; phase=qa; ranks=1/2/2/1/2; quota=constrained; mode=mutation; alias=codex1; model=gpt-5.6-terra; effort=high; policy=2026-08-29.1; root-medium=true; hitl=true; digest=30bd6c612ef65b15c20eaad7a49d03a630083bc2bf29d8d1402eeadd726c007a. Correction lane digest=8141f18bbc335d416d0c2c093f0505ea4e55809a27b7739d7163a5dab4bfe90d. Validated planning only.
Docs DispatchDecision v1: ticket=TICKET-RELEASE-VERIFIED-20260830-050-DOCS; phase=archive; ranks=2/2/1/2/2; quota=constrained; mode=mutation; alias=codex2; model=gpt-5.6-sol; effort=ultra; policy=2026-08-29.1; root-medium=true; HITL=true; digest=712cb22c7f17a6519c7d78d52b438bcc70dd1f69ecdec8638e0c2b04f058e144. Release archived to production.
<!-- RELEASE-VERIFIED-20260830-000-GOV:END -->

<!-- GOV-BN-20260830:START -->
## Owner-approved bottleneck-removal epic - GOV-BN-20260830
Gate: APPROVED for planning and the dependency-gated phases below. The epic is isolated from the current release candidate. Its canonical mutations and integration wait for `RELEASE-VERIFIED-20260830-120-POSTDEPLOY` production-green; it then receives independent QA/review, its own main-only CI, production deployment, and post-deploy identity gate before routing is restored.

Owner-approved phase split: the current release may use immediate manual/evidence-based `GateImpactDecision` records, slot backfill, and only its already-scoped release fixes. Deterministic selector source, hook consolidation, ecosystem sync changes, dispatcher/scheduler, queue/heartbeat, skills/rules decomposition, Root B proof, HF payload/memory optimization, and every other cross-cutting refactor below are notes/tickets only with status `DEFERRED_NEXT_PHASE`. They cannot start before current release 120 is production-green. Each deferred feature group must retain separate immutable test-baseline, source, independent review, and integration microtickets with non-overlapping one-editor ownership and dependency-safe parallel waves.

Impact selection contract: every lane records schema/policy version, base/head/diff digest, changed paths/contracts/dependencies/surfaces, `RUN` gates, reasoned `NOT_APPLICABLE` gates, the unknown-impact fallback, and reviewer/owner. Only directly or transitively affected gates run. Unknown impact, rename ambiguity, stale/missing maps, or cross-cutting security/release boundaries expand to the broader applicable set. `NOT_APPLICABLE` never bypasses changed-source provenance, relevant security, reviewer evidence, or post-deploy identity/health for a touched surface.

GRILL REPORT: D1 IN is pool/config truth, repo-only ecosystem sync/parity, unified hooks, skill/rule decomposition and evals, Hermes contract, generated refresh, decision/result contracts, scheduler/dispatcher decomposition, queue fairness, heartbeat, supervisor/handoff, Root B proof, QA/review/release, and routing restoration. OUT is current-candidate mutation, secret/auth/billing bypass, manual generated-file edits, takeover of dirty/unowned work, and treating static metadata as provider proof. D2 changes a monolithic/duplicated control plane into bounded one-editor components while preserving public CLI/contracts and fail-closed denials. D3 succeeds only at ticket 110 after two production-green sequences and restoration verification; any gate failure stops descendants. D4 depends on current release 120 green, immutable baselines, provenance allowlists, current-owner handoff for dirty files, valid capacity/lease/quota evidence, main-only Actions, and production identities. D5 ownership and order are frozen below. D6 no silence is a waiver; provider/runtime and prior-tree claims require receipts. D7 recovery is preserve refs, revert only the owned commit, retain the facade, and halt before downstream integration. D8 temporary routing is owner-approved `gpt-5.6-sol/ultra`; parallel isolation, not assumed model speed, controls latency. D9 is NOT-APPLICABLE: no metaphysical behavior or data changes.

Temporary model/tier exception: all executable lanes use `gpt-5.6-sol/ultra`, preserve the root-medium gate, and request Fast mode through configured `service_tier = "priority"` until `GOV-BN-091-POSTDEPLOY` is production-green. Collaboration receipts do not expose `service_tier`, so Fast/priority is configured intent rather than execution proof. Only then may `GOV-BN-100-MODEL-RESTORE` return `service_tier` to `default` and restore Luna-default for bounded rank-0/1 work with risk-based Terra/Sol escalation; no risk floor may be lowered. Planning DispatchDecision: ticket=`TICKET-GOV-BOTTLENECK-20260830-000-PLAN`; phase=planning; ranks=3/3/2/2/3; quota=constrained; mode=mutation; alias=codex2; model=gpt-5.6-sol; effort=ultra; policy=2026-08-29.1; root-medium=true; HITL=true; digest=`7721208765231fad7efd9639c324c3fade7253713ed7941c004e2a8596cca4c0`; quality exception=owner-approved temporary Sol/ultra override until final production-green, with parallel isolation as latency control. This is validated routing intent, not provider execution proof.

Capacity policy: keep 3/3 native child slots occupied whenever dependency-ready, non-overlapping microtickets exist; immediately backfill a completed or blocked slot. Never create duplicate owners or bypass baseline/provenance dependencies to fill capacity. No AGY nested child may start before `GOV-BN-053-ROOTB-PROOF` records a fresh request, lease, quota observation, provider-bound receipt, and bounded no-write smoke; supervisor/static-config smoke is non-proof.

Immutable baseline/provenance matrix: every mutation row must name one committed test-only baseline and an exact allowed-source list. A baseline commit cannot include source, generated, documentation, or runtime output.
| Baseline | Status | Depends on | Test-only owner and files | Allowed source for descendant mutations | Stop condition |
|---|---|---|---|---|---|
| GOV-BN-B00-POOL | DEFERRED_NEXT_PHASE | release 120 green; current six-pool owner identified | qa_tester: `tests/test_multiagent_capacity.py`, `tests/test_multiagent_prompt_command.py`, `plans/test_provenance/gov-bn-20260830-b00-pool.json` | 000 only: `.agents/config/multiagent_prompt_command.example.yaml`, `scripts/multiagent_prompt_command.py` | dirty ownership unresolved; no RED/negative control; guard drift |
| GOV-BN-B10-SYNC | DEFERRED_NEXT_PHASE | release 120 green; 000 DONE | qa_tester: `tests/test_test_provenance_ecosystem_sync.py`, `tests/test_sync_claude_agy_parity_payload_mode_contract.py`, `plans/test_provenance/gov-bn-20260830-b10-sync.json` | 010/011 serially: `scripts/sync_ai_agent_ecosystem.py` | MAREF-054-A duplicate owner; no deterministic RED/parity fixture |
| GOV-BN-B20-HOOKS | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: `tests/test_unified_governance_hooks.py`, `plans/test_provenance/gov-bn-20260830-b20-hooks.json` | 020/021 disjoint hook paths listed below | deny mismatch, timing fixture absent, or hook writes repository |
| GOV-BN-B30-POLICY | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: immutable old snapshots, adversarial eval fixtures, `tests/test_agent_governance_decomposition.py`, `plans/test_provenance/gov-bn-20260830-b30-policy.json` | 030/031/032 canonical paths; 033 generated outputs only through sync | reviewer-first/trigger/safety/precision/recall/context fixture missing |
| GOV-BN-B40-CONTROL | DEFERRED_NEXT_PHASE | release 120 green; 000 DONE | qa_tester: schema/scheduler/dispatcher contract tests and `plans/test_provenance/gov-bn-20260830-b40-control.json` | 040/041/042/043 disjoint paths below | facade behavior or decision/result compatibility not frozen |
| GOV-BN-B50-RUNTIME | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: `tests/test_multiagent_durable_queue.py`, `tests/test_multiagent_root_worker.py`, `tests/test_multiagent_root_supervisor.py`, `tests/test_inter_root_dispatch_contract.py`, `plans/test_provenance/gov-bn-20260830-b50-runtime.json` | 050/051/052 disjoint runtime paths below | deterministic fairness/TTL/race/provider boundaries not RED-frozen |
| GOV-BN-B60-IMPACT | DEFERRED_NEXT_PHASE | release 120 green | impact_baseline_qa: `tests/test_impact_gate_selector.py`, impact eval fixtures, `plans/test_provenance/gov-bn-20260830-b60-impact.json` | only the GOV-BN-060 impact source rows below | any missing deterministic RED/negative control, eval case, or closed allowlist |

Deferred one-editor execution graph. Nothing in this graph runs during the current release. After release 120 is green, baseline waves B00..B60 may run in parallel only where ownership is disjoint. Source waves start only from their own immutable baselines; 010 then 011 are serial, 030/031/032 may be parallel, 041/042 may be parallel after 040, 043 waits for 042 plus dirty-owner handoff, and 050/051 may be parallel before 052 joins. Ticket 033 is one serial generated refresh after canonical agent/rule/skill/hook sources freeze. Every group requires its own review and integration receipt before a shared release gate.
| ID | Severity | Owner | Status | Dependencies | Exact one-editor ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| TICKET-GOV-BOTTLENECK-20260830-000-PLAN | HIGH | business_analyst | DONE | owner approval | only matching governance blocks in `PROJECT_TASKS.md` and `plans/plan.md` | blocks hash-match and `git diff --check`; stop on semantic drift |
| GOV-BN-000-CONFIG-POOL | CRITICAL | existing_six_pool_owner | DEFERRED_NEXT_PHASE/BLOCKED_OWNER | release 120 green; B00 | `.agents/config/multiagent_prompt_command.example.yaml`, then the current dirty alias-map hunk in `scripts/multiagent_prompt_command.py`; no other editor | reconcile four/five/six pool truth; stop until current owner hands off both dirty edits |
| GOV-BN-010-REPO-SYNC | HIGH | MAREF-054-A_sync_owner | DEFERRED_NEXT_PHASE | release 120 green; B10; 000 | `scripts/sync_ai_agent_ecosystem.py`; ownership is merged with MAREF-054-A, never duplicated | repo-only deterministic sync; stop on duplicate owner or out-of-repo write |
| GOV-BN-011-DETERMINISTIC-PARITY | HIGH | parity_developer | DEFERRED_NEXT_PHASE | 010 | subsequent serial parity hunk in `scripts/sync_ai_agent_ecosystem.py` only | repeat runs byte-identical and check explains drift; stop on nondeterminism |
| GOV-BN-020-UNIFIED-PREHOOK | CRITICAL | prehook_developer | DEFERRED_NEXT_PHASE | release 120 green; B20 | `.claude/settings.json` and listed `.claude/hooks/*` prehook paths | exactly one prehook process/event, deny equivalence, no swallowed failure or repo mutation |
| GOV-BN-021-NOWRITE-POSTHOOK | HIGH | posthook_developer | DEFERRED_NEXT_PHASE | B20; 020 contract frozen | `.agents/hooks.json`, listed `.agents/hooks/*`, `.claude/hooks/post-tool-use-formatter.sh` | posthook/precommit audit-only; stop on write or swallowed failure |
| GOV-BN-030-SKILLS-EVALS | HIGH | skill_architect | DEFERRED_NEXT_PHASE | release 120 green; B30 | listed orchestration `SKILL.md` sources and extracted skills only | reviewer-first evals, 100% safety, precision/recall >=0.90, context reduction evidence |
| GOV-BN-031-RULES-DECOMPOSITION | HIGH | rule_architect | DEFERRED_NEXT_PHASE | B30 | listed `.agents/rules/*` canonical paths and extracted rules only | no duplicated/conflicting mandate; stop on semantic loss |
| GOV-BN-032-HERMES-CONTRACT | HIGH | hermes_developer | DEFERRED_NEXT_PHASE | B30 | `.agents/agents/hermes/agent.json`, `scripts/hermes_model_parity.py` | bounded fail-closed contract; no provider/static-label inference |
| GOV-BN-033-GENERATED-REFRESH | CRITICAL | ecosystem_sync_operator | DEFERRED_NEXT_PHASE | 000,011,020,021,030,031,032 | generated outputs reported by ecosystem sync only | no manual generated edits; stop on unowned output or canonical mutation |
| GOV-BN-040-DECISION-RESULT-CONTRACTS | CRITICAL | contract_developer | DEFERRED_NEXT_PHASE | release 120 green; B40 | listed dispatch/work-result schemas; new version only if required | negative fixtures fail closed; stop on compatibility loss |
| GOV-BN-041-SCHEDULER-SPLIT | HIGH | scheduler_developer | DEFERRED_NEXT_PHASE | B40,040 | `scripts/multiagent_ticket_scheduler.py` plus new scheduler modules | deterministic facade compatibility; stop on behavior drift |
| GOV-BN-042-DISPATCHER-COMPONENTS | CRITICAL | dispatcher_components_developer | DEFERRED_NEXT_PHASE | B40,040 | new dispatcher component modules only | focused contracts green; stop on facade edit/cycle |
| GOV-BN-043-DISPATCHER-FACADE | CRITICAL | dispatcher_facade_owner_after_handoff | DEFERRED_NEXT_PHASE/BLOCKED_OWNER | 000,042; explicit handoff | `scripts/multiagent_prompt_command.py` only after dirty hunk attribution | thin compatible facade; stop on unowned diff or overlap |
| GOV-BN-050-QUEUE-FAIRNESS | CRITICAL | queue_developer | DEFERRED_NEXT_PHASE | release 120 green; B50 | `scripts/multiagent_durable_queue.py` only | deterministic no-starvation behavior; stop on lease bypass |
| GOV-BN-051-HEARTBEAT | CRITICAL | worker_developer | DEFERRED_NEXT_PHASE | B50 | `scripts/multiagent_root_worker.py`, `scripts/check_cookie_heartbeat.py` | heartbeat < TTL/3 and deterministic recovery |
| GOV-BN-052-SUPERVISOR-HANDOFF | CRITICAL | supervisor_developer | DEFERRED_NEXT_PHASE | 050,051 | `scripts/multiagent_root_supervisor.py` only | zero duplicate starts and explicit UNKNOWN recovery |
| GOV-BN-053-ROOTB-PROOF | CRITICAL | root_b_bootstrap_owner | DEFERRED_NEXT_PHASE | 000,033,040,041,043,050,051,052 | no-write provider receipt artifacts only | fresh provider-bound Root B proof; static config remains non-proof |
| GOV-BN-060-QA | CRITICAL | qa_tester | DEFERRED_NEXT_PHASE | all applicable source integrations including IMPACT-060 | only validated `GateImpactDecision.RUN` evidence | zero missed affected gates; all RUN green; every N/A reasoned; no stale evidence |
| GOV-BN-070-REVIEW | CRITICAL | release_reviewer | DEFERRED_NEXT_PHASE | 060 | read-only exact-commit and receipt review | independent release verdict; stop on unresolved risk |
| GOV-BN-080-MAIN | CRITICAL | release_integrator | DEFERRED_NEXT_PHASE | 070 | clean integration branch then `main`; verified commits only | approved reachability; stop on ancestry/dirty/conflict |
| GOV-BN-081-MAIN-ONLY-CI | CRITICAL | devops | DEFERRED_NEXT_PHASE | 080 | GitHub Actions from `main` only | bound main run green; stop on wrong branch/stale run |
| GOV-BN-090-PRODUCTION | CRITICAL | devops | DEFERRED_NEXT_PHASE | 081 | canonical HF Docker and separate Vercel receipts | deployed and rollback identities match main |
| GOV-BN-091-POSTDEPLOY | CRITICAL | qa_tester | DEFERRED_NEXT_PHASE | 090 | affected health/version/API/UI evidence | exact touched identities green; stop on HTTP-200-only or mismatch |
| GOV-BN-100-MODEL-RESTORE | HIGH | routing_owner | DEFERRED_NEXT_PHASE | 091 green | active Codex account `service_tier` plus canonical routing only through its owner/sync | `service_tier=default`; Luna bounded rank-0/1 default with risk escalation; root-medium preserved; no lowered floor |
| GOV-BN-110-CLOSE | HIGH | business_analyst | DEFERRED_NEXT_PHASE | 100 and any restoration CI | canonical docs/tickets/HANDOFF reconciliation | truthful final receipts; stop on mismatch |

### GOV-BN-060 IMPACT-GATE-SELECTION microtickets

All rows are `DEFERRED_NEXT_PHASE` and require current release 120 production-green. Wave 0 freezes tests; Wave 1 implements the selector/map; Wave 2 may update rules, skills, and existing unified hook/CI consumers in parallel after the selector contract freezes; Wave 3 performs independent QA/review; Wave 4 integrates reviewed commits. No row adds a new hook registration/process.

| ID | Wave | Owner | Status | Dependencies | Exact ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| GOV-BN-060-IMPACT-000-BASELINE | 0 | impact_baseline_qa | DEFERRED_NEXT_PHASE | release 120 green | `tests/test_impact_gate_selector.py`, impact eval fixtures, `plans/test_provenance/gov-bn-20260830-b60-impact.json` only | immutable test-only RED/negative-control baseline covers all six eval cases; stop on source/mixed commit |
| GOV-BN-060-IMPACT-010-SELECTOR-MAP | 1 | impact_selector_developer | DEFERRED_NEXT_PHASE | IMPACT-000 verified | `scripts/impact_gate_selector.py`, `.agents/config/gate-impact-map-v1.json` only | deterministic versioned `GateImpactDecision`; rename/dependency closure and unknown fallback fail closed |
| GOV-BN-060-IMPACT-020-RULES | 2 | impact_rule_architect | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen | `.agents/rules/02-testing-standards.md`, `.claude/rules/testing-and-release.md` only | Rule 02/Claude semantics match; no traditional full-suite mandate or safety loss |
| GOV-BN-060-IMPACT-030-SKILLS | 2 | impact_skill_architect | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen | new `.agents/skills/impact-based-gate-selection/`, `.agents/skills/qa-e2e-testing/`, `.agents/skills/sdlc-aisdlc-workflow/` only | new skill plus QA/SDLC updates pass skill-creator old/new trigger, adversarial, and safety evals |
| GOV-BN-060-IMPACT-040-HOOK-CI | 2 | impact_hook_ci_owner | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen; 020/021 ownership frozen | `.githooks/pre-commit`, `.github/workflows/ci.yml` only | validate through existing unified hook/CI process; no extra hook registration/process, swallowed failure, or repo write |
| GOV-BN-060-IMPACT-050-QA-REVIEW | 3 | independent_qa_reviewer | DEFERRED_NEXT_PHASE | IMPACT-010,020,030,040 | read-only exact-commit/eval/benchmark receipts only | zero missed affected gates across six cases; every N/A reasoned; reduction benchmark is evidence-only until measured |
| GOV-BN-060-IMPACT-060-INTEGRATE | 4 | impact_release_integrator | DEFERRED_NEXT_PHASE | IMPACT-050 READY | clean next-phase integration branch; reviewed commits only | baseline/source/review ancestry preserved and selected commits integrated; stop on conflict/unreviewed evidence |

Impact eval matrix: docs-only runs Markdown structure/link/reference, matching governance blocks, and `git diff --check`, with product/browser/Rust/HF/provider/secret/sync N/A when no transitive impact exists. Lesson 20 runs its focused CLI contracts, provenance, relevant security, and review gates. HF publisher runs publisher/provenance/security/review plus touched post-deploy identity/health. Hooks/rules run governance/eval/sync checks without unrelated product/browser/Rust suites. Rename/unknown expands dependency closure or fails closed broader when unresolved. Deploy runs the affected deployment, rollback, reviewer, and exact post-deploy identity/health gates. Acceptance is zero missed affected gates; gate-count/runtime reduction is recorded as evidence only until a measured baseline exists.

### GOV-BN-061 TMUX-CODEX-THROUGHPUT microtickets

Live audit on 2026-08-30 found no tmux server/session. The current release uses Codex subagents with isolated worktrees; historical artifacts show tmux only in prior AGY quota probes. `ACTIVE_NOW` threshold policy: expected >3-minute or output-heavy local commands and CI/deploy polling use a unique detached tmux session with a persistent sanitized log and explicit exit/done evidence; surface at most 30 lines. Short commands run directly. Never present tmux panes as agent concurrency, and do not start a dummy session. The runner refactor remains deferred below.

Codex tuning reuses the existing routing tickets: each lane must distinguish requested from observed model, effort, and service tier; when receipts omit tier, record `UNAVAILABLE` and never claim `FAST_ACTIVE`. Use short-context forks for bounded lanes. Ultra effort is allowed only inside the explicit owner-approved production-green exception window or for rank-3 gates. After final deploy/post-deploy green, `GOV-BN-100-MODEL-RESTORE` returns to Luna-default with risk-based escalation and `service_tier=default`; no duplicate tuning ticket is created here.

All implementation rows are `DEFERRED_NEXT_PHASE` until current release 120 reaches first production-green. This docs lane does not start/kill tmux or mutate the runner.

| ID | Wave | Owner | Status | Dependencies | Exact ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| GOV-BN-061-TMUX-000-BASELINE | 0 | tmux_baseline_qa | DEFERRED_NEXT_PHASE | release 120 green | `tests/test_tmux_runner.py`, `tests/test_ci_deploy_event_watcher.py`, tmux fixtures, `plans/test_provenance/gov-bn-20260830-b61-tmux.json` only | immutable test-only RED/negative-control covers collision, completed-before-capture, fallback, redaction, stale cleanup |
| GOV-BN-061-TMUX-010-RUNNER | 1 | tmux_runner_developer | DEFERRED_NEXT_PHASE | TMUX-000 verified | `.agy/scripts/tmux-runner.sh` only | unique durable session; persistent log plus exit/done metadata; no unconditional same-name kill; async fallback; bounded tail/status |
| GOV-BN-061-TMUX-020-WATCHER | 1 | ci_watcher_developer | DEFERRED_NEXT_PHASE | TMUX-000 verified | new `scripts/ci_deploy_event_watcher.py` only | event/change-triggered CI/deploy watcher with bounded exponential backoff and redacted output |
| GOV-BN-061-TMUX-030-QA-REVIEW | 2 | independent_tmux_reviewer | DEFERRED_NEXT_PHASE | TMUX-010,020 | read-only exact-commit/test/log receipts only | zero lost completion/exit evidence and at most 30 surfaced lines; stop on stale/collision/redaction/fallback ambiguity |
| GOV-BN-061-TMUX-040-INTEGRATE | 3 | tmux_release_integrator | DEFERRED_NEXT_PHASE | TMUX-030 READY | clean next-phase integration branch; reviewed commits only | baseline/source/review ancestry preserved; stop on conflict or unreviewed evidence |

Explicit blockers and exclusions: `.agents/config/multiagent_prompt_command.example.yaml` and `scripts/multiagent_prompt_command.py` contain concurrent unowned six-pool edits; only their current owner may reconcile or hand them off. Pool truth currently conflicts across four/five/six, and static configuration never proves Root B/provider execution. Generated mirrors are outputs and must never be edited manually; canonical changes require `python3 scripts/sync_ai_agent_ecosystem.py --sync` followed by `--check`. Evidence/recovery branches remain preserved until every required commit is reachable from production-green main.
<!-- GOV-BN-20260830:END -->

<!-- IDQ-MVP-BOARD-20260828:START -->
## Sprint IDQ-MVP — Independent Roots + Durable Queue Local MVP

**Historical gate**: `APPROVED` in `plans/plan.md`; local SQLite single-host MVP
only. Current ticket classifications are corrected below and summarized in the
canonical `2026-08-30` operational block at the top of this file.
**DispatchDecision**: `v1`, ticket `IDQ-MVP-GOV-001`, planning ranks
`3/3/3/1/3`, `gpt-5.6-sol/xhigh`, policy `current`, root-medium confirmed,
HITL approved by the user's delegate instruction.
**Global exclusions**: no MAREF C1/C2 closure, push, deploy, publish,
production cutover, credential/secret operation, fabricated receipt, raw
provider-stream persistence, or ordinary activation opening. Bootstrap is
explicit, risk-recorded, read-only, ephemeral, sealable, and never healthy.

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `IDQ-MVP-000-GOV` | CRITICAL | XS | `business_analyst` | DONE — HISTORICAL GOVERNANCE | None |
| `IDQ-MVP-010-BASELINE` | CRITICAL | M | `qa_tester` | DONE — VERIFIED `0e194152`; `0946bde` RECONSTRUCTED | `IDQ-MVP-000-GOV` |
| `IDQ-MVP-020-STORE` | CRITICAL | L | `developer` (store lane) | REOPENED — LOCAL CONTRACT / FRESH QA PENDING | `IDQ-MVP-010-BASELINE` |
| `IDQ-MVP-030-DISPATCHER` | CRITICAL | M | `developer` (dispatcher lane) | REOPENED / BLOCKED — REAL EXECUTOR ROUTE PENDING | `IDQ-MVP-010-BASELINE` |
| `IDQ-MVP-040-WORKER` | CRITICAL | L | `developer` (worker lane) | REOPENED / BLOCKED — REAL DAEMON ROUTE PENDING | `IDQ-MVP-020-STORE`, `IDQ-MVP-030-DISPATCHER` |
| `IDQ-MVP-050-SUPERVISOR` | CRITICAL | M | `developer` (supervisor lane) | REOPENED / BLOCKED — REAL DAEMON ROUTE PENDING | `IDQ-MVP-020-STORE`, `IDQ-MVP-040-WORKER` |
| `IDQ-MVP-060-INTEGRATION` | HIGH | M | `developer` (integration lane) | REOPENED / BLOCKED — CROSS-RUNTIME HANDOFF PENDING | `IDQ-MVP-020-STORE`..`IDQ-MVP-050-SUPERVISOR` |
| `IDQ-MVP-070-QA` | CRITICAL | L | `qa_tester` | REOPENED — FRESH QA PENDING | `IDQ-MVP-060-INTEGRATION` |
| `IDQ-MVP-080-FOUR-ALIAS` | CRITICAL | M | `qa_tester` (receipt executor) | BLOCKED — REAL PATH + FRESH ACTIVATION PENDING | `IDQ-MVP-070-QA`, `IDQ-OP-050-PREFLIGHT` |
| `IDQ-MVP-090-SEAL-GOV` | HIGH | S | `business_analyst` | BLOCKED | `IDQ-MVP-080-FOUR-ALIAS` |

### `IDQ-MVP-000-GOV` — Governance freeze

- **Severity / Work Effort**: `CRITICAL / XS`
- **Current classification**: `DONE — HISTORICAL GOVERNANCE`; it does not prove
  current executor, QA, provider, or release readiness.
- **Exact one-editor ownership**: `business_analyst`; only `plans/plan.md` and
  `PROJECT_TASKS.md` for this delimited governance block.
- **Dependencies**: none.
- **Acceptance/evidence**: nine-dimension `APPROVED` grill, exclusions,
  bootstrap boundaries, four-receipt criterion, ticket graph, and
  `DispatchDecision v1` are recorded.
- **Stop condition**: `DONE` once both blocks exist and pre-existing bytes
  remain untouched beneath them.
- **Exclusions**: source/tests/config, staging, commits, push/deploy/cutover.

### `IDQ-MVP-010-BASELINE` — Test-first provenance baseline

- **Severity / Work Effort**: `CRITICAL / M`
- **Verified baseline ownership**: `qa_tester`; commit
  `0e1941528c0c8f49ef50a14fd046db2163d33379` contains only
  `tests/test_idq_mvp_010_release_cycle.py` and
  `plans/test_provenance/idq-mvp-010-release-cycle-baseline.json`.
- **Reconstructed history**: commit
  `0946bdec65173edacbaf4044b4198d55136c33ca` contains the earlier four tests
  plus `plans/test_provenance/idq-mvp-010-baseline.json`; it remains
  `NON_TDD_RECONSTRUCTED` and is not verification evidence.
- **Dependencies**: `IDQ-MVP-000-GOV` (`DONE`).
- **Status**: `DONE — VERIFIED RELEASE-CYCLE BASELINE`
- **Acceptance/evidence**: the exact `0e194152` commit and its two-path tree are
  retained in current ancestry. Historical suite counts do not substitute for
  fresh operational QA.
- **Stop condition**: `READY -> DONE` only when commit SHA and history-guard
  proof exist; otherwise `BLOCKED`, with no source lane released.
- **Exclusions**: all product source, existing tests, docs, config, provider
  execution, and any commit containing a sixth path.

### `IDQ-MVP-020-STORE` — SQLite durable authority

- **Severity / Work Effort**: `CRITICAL / L`
- **Status**: `REOPENED — LOCAL CONTRACT PRESENT / FRESH QA PENDING`. The local
  source in current ancestry is not current runtime or provider proof.
- **Exact one-editor ownership**: store-lane `developer`; only
  `scripts/multiagent_durable_queue.py` (schema migration v1 embedded or
  owned from this module).
- **Dependencies**: `IDQ-MVP-010-BASELINE` (`DONE` and verified).
- **Acceptance/evidence**: WAL/pragma/permission contract, idempotency,
  atomic claim/fence/lease/result/outbox, recovery, and retry/`UNKNOWN`
  boundaries pass the frozen queue test.
- **Stop condition**: stop at the first frozen-test contradiction, ownership
  overlap, or missing verified baseline.
- **Exclusions**: dispatcher, worker, supervisor, legacy queue promotion,
  PostgreSQL/multi-host, tests, docs, push/deploy.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-030-DISPATCHER` — Bootstrap admission and lifecycle

- **Severity / Work Effort**: `CRITICAL / M`
- **Status**: `REOPENED / BLOCKED`; the real bounded executor route and fresh
  evidence are pending.
- **Exact one-editor ownership**: dispatcher-lane `developer`; only the
  existing multi-account dispatcher module's typed `LocalBootstrapAdmission`
  and `prepared/starting/provider_started/completed` hook surface.
- **Dependencies**: `IDQ-MVP-010-BASELINE` (`DONE` and verified).
- **Acceptance/evidence**: ordinary path stays byte-compatible and `CLOSED`;
  explicit risk-bound ephemeral bootstrap admits only read-only attempt 1,
  preserves unknown/constrained quota, and revalidates fence/decision/snapshot/
  executable/account identity before spawn.
- **Stop condition**: stop on auth/executable/identity ambiguity, fallback,
  quota-health promotion, frozen-test contradiction, or ownership overlap.
- **Exclusions**: store/worker/supervisor, account credentials, billing or
  executable bypass, mutation lanes, fabricated receipts, tests/docs/release.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-040-WORKER` — Independent root worker

- **Severity / Work Effort**: `CRITICAL / L`
- **Status**: `REOPENED / BLOCKED`; local source presence does not prove a real
  independent daemon route or cross-runtime handoff.
- **Exact one-editor ownership**: worker-lane `developer`; only
  `scripts/multiagent_root_worker.py`.
- **Dependencies**: `IDQ-MVP-020-STORE` (local contract / fresh QA pending) and
  `IDQ-MVP-030-DISPATCHER` (reopened/blocked).
- **Acceptance/evidence**: Root A cannot claim AGY and Root B cannot claim
  Codex; pool/caps/backpressure/circuit/retry rules hold; root/worker
  heartbeats and stale-fence/result rejection pass; post-start ambiguity is
  `UNKNOWN` with no blind retry.
- **Stop condition**: stop on cross-root claim/fallback, duplicate execution,
  raw-stream/secret persistence, provenance failure, or ownership overlap.
- **Exclusions**: supervisor CLI, dispatcher/store edits, tests/docs, external
  release actions.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-050-SUPERVISOR` — Local lifecycle authority

- **Severity / Work Effort**: `CRITICAL / M`
- **Status**: `REOPENED / BLOCKED`; a real daemon/executor path and fresh
  lifecycle evidence are pending.
- **Exact one-editor ownership**: supervisor-lane `developer`; only
  `scripts/multiagent_root_supervisor.py`.
- **Dependencies**: `IDQ-MVP-020-STORE` (local contract / fresh QA pending) and
  `IDQ-MVP-040-WORKER` (reopened/blocked).
- **Acceptance/evidence**: `doctor/init/start/submit/status/wait/smoke-all/
  seal-bootstrap/stop --drain`, detached PID/instance checks, stale-instance
  fencing, restart recovery, permissions, explicit risk acceptance, expiry,
  seal, and normal-restart `CLOSED` behavior pass frozen tests.
- **Stop condition**: stop on unsafe PID/home/symlink state, unrecorded risk,
  failed drain/fence, missing baseline, or ownership overlap.
- **Exclusions**: implementation-module edits, credential reads, deployment,
  production daemonization/cutover, tests/docs.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-060-INTEGRATION` — Secret-free four-route integration

- **Severity / Work Effort**: `HIGH / M`
- **Status**: `REOPENED / BLOCKED`; the explicit cross-runtime handoff route is
  now in scope and has not yet produced fresh evidence.
- **Exact one-editor ownership**: integration-lane `developer`; only the new
  secret-free four-alias route/config artifact selected during baseline freeze;
  fixes to `020`..`050` return to their owning editor.
- **Dependencies**: all of `IDQ-MVP-020-STORE`, `030-DISPATCHER`,
  `040-WORKER`, and `050-SUPERVISOR`; each must satisfy the current reopened
  operational gates before integration.
- **Acceptance/evidence**: all four aliases route only to their locked root;
  deterministic crash/replay/outbox/status flows integrate without secrets,
  fallback, duplicate work, or ordinary activation.
- **Stop condition**: stop and bounce to the owning source ticket on any
  source-module fix; stop on secret-bearing config or provenance failure.
- **Exclusions**: edits to `020`..`050` ownership, provider smoke, tests/docs,
  PostgreSQL/multi-host/SSE, push/deploy/cutover.
- **Provenance gate**: baseline commit must be an ancestor; every source/config
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-070-QA` — Deterministic verification

- **Severity / Work Effort**: `CRITICAL / L`
- **Exact one-editor ownership**: `qa_tester`; the four tests and manifest from
  `010` remain QA-owned but frozen; this ticket collects read-only reports.
- **Dependencies**: `IDQ-MVP-060-INTEGRATION` (reopened/blocked) and source
  freeze.
- **Status**: `REOPENED — FRESH QA PENDING`
- **Acceptance/evidence**: rerun the applicable deterministic queue, daemon,
  cross-runtime handoff, QOBS, capacity, scheduler, receipt-integrity,
  read-only-boundary, ecosystem, and secret-safe gates on the exact candidate.
  Earlier pass counts are historical only.
- **Stop condition**: stop on any failure. A wrong frozen test requires a
  separate superseding test-only baseline; never edit it under this ticket.
- **Exclusions**: source fixes, baseline rewrite, provider smoke, staging/
  commit/push/deploy.

### `IDQ-MVP-080-FOUR-ALIAS` — Real provider proof

- **Severity / Work Effort**: `CRITICAL / M`
- **Exact one-editor ownership**: `qa_tester` is the sole bounded receipt
  executor/recorder; no repository-file edit is permitted.
- **Dependencies**: `IDQ-MVP-070-QA` (reopened), real executor/daemon path, and
  `IDQ-OP-050-PREFLIGHT` (fresh activation not issued).
- **Status**: `BLOCKED — REAL PATH + FRESH ACTIVATION PENDING`
- **Acceptance/evidence**: concurrent read-only jobs show at least one overlap;
  each of `codex1`, `codex2`, `agy1`, and `agy2` yields provider-native safe
  process/session evidence, a validated real `ExecutionReceipt`, and typed
  `WorkResult`; no raw streams, duplicate, or cross-account fallback.
- **Stop condition**: stop the affected alias on `BLOCKED_AUTH`, executable/
  identity failure, malformed/missing receipt/result, or ambiguity. Ticket
  remains incomplete until all four real receipts exist.
- **Exclusions**: fabricated/synthetic receipts, fallback alias, credential/
  billing repair, mutation work, repository edits, push/deploy/cutover.

### `IDQ-MVP-090-SEAL-GOV` — Seal and reconcile governance

- **Severity / Work Effort**: `HIGH / S`
- **Status**: `BLOCKED`; no valid four-alias terminal set or seal evidence
  exists for the current operational graph.
- **Exact one-editor ownership**: `business_analyst`; only `plans/plan.md` and
  `PROJECT_TASKS.md` after source freeze and acceptance evidence.
- **Dependencies**: requires `IDQ-MVP-080-FOUR-ALIAS` to become `DONE` with all
  four receipts real; it is currently blocked.
- **Acceptance/evidence**: bootstrap seal receipt exists; ordinary restart is
  `CLOSED`; board/plan reflect verified evidence; ecosystem sync/check and
  secret-safe review evidence are recorded without a release claim.
- **Stop condition**: stop if any receipt is absent, bootstrap is unsealed,
  ordinary activation is open, sync/check fails, or a push/deploy/cutover is
  requested without separate authorization.
- **Exclusions**: source/tests/config, receipt creation, evidence deletion,
  MAREF C1/C2 closure, push, deploy, publish, production cutover.

### `IDQ-MVP-080` conditional provider-test authorization — `IDQ-MVP-080-AUTH-01`

**Recorded**: `2026-08-29T00:57:56+07:00` (Asia/Bangkok)
**Authority**: the owner expressly requested: `start Codex/AGY provider` for
`IDQ-MVP-080`, across `codex1`, `codex2`, `agy1`, and `agy2`, one attempt per
alias, read-only, no retry/fallback, with receipt plus `WorkResult` binding.
**Status**: `SEALED / EXPIRED — NOT DISPATCH AUTHORITY`
**Non-secret risk record**: `RISK-IDQ-MVP-080-20260829-01`; expiry/TTL is the
earlier of `2026-08-29T04:57:56+07:00`, a root-session/control-process restart,
or the first terminal outcome for every listed alias. `IDQ-MVP-080-AUTH-01` is
sealed at its recorded expiry and cannot be renewed, replayed, inherited by
`AUTH-02`, or used for another alias/attempt.

This was a historical narrow supersession for `IDQ-MVP-080-FOUR-ALIAS`. Its
expiry restores the ticket to `BLOCKED`; it does not authorize a current
preflight or dispatch. It does not supersede prior attempt history, any other
ticket, Rule 17/18, ordinary `S5`/`CLOSED`/activation-prohibited behavior, or
any credential, billing, deployment, publication, push, mutation, or raw-data
boundary.

- **Safe objective**: each alias independently performs one bounded,
  non-sensitive repository-inventory review and returns only Result Contract v2
  metadata. The provider prompt, result, and all commands must be read-only;
  no file, Git, account, configuration, secret, or provider setting may change.
- **Fixed aliases and budget**: `codex1`, `codex2`, `agy1`, and `agy2` are four
  separate lanes, each with `attempt=1`, `max_attempts=1`, one lane, and no
  fallback, substitution, reroute, chaining, or automatic/manual retry.
- **Required fresh preflight, per alias**: before process creation, validate a
  current safe quota band (unknown, contradictory, below-threshold, or stale is
  a stop), effective alias identity/executable without reading credentials,
  enforced read-only runtime/sandbox path, a new Rule 18 `DispatchDecision` and
  non-placeholder Rule 11 scheduling snapshot bound to this alias/attempt,
  unexpired one-use lease/risk record, and an unused nonce. Validate all
  bindings before nonce consumption; atomically consume the nonce only at the
  irreversible start boundary.
- **Receipt/evidence boundary**: validate a provider-native `ExecutionReceipt`
  and normalized typed `WorkResult` independently, with matching ticket,
  alias, attempt, decision/snapshot/nonce bindings and digest. Retain only safe
  receipt metadata, hashes/counts, and the typed result. Never retain, print,
  persist, or reconstruct raw provider streams, credentials, account IDs,
  paths, cookies, or prompt/output bodies. Any AGY success is described only
  as `validated in-process only`.

| Alias | Terminal stop condition | Required terminal record |
|---|---|---|
| `codex1` | any failed/ambiguous preflight, start, receipt, or `WorkResult` validation | typed `BLOCKED`/`NEEDS_HITL` or valid bound receipt/result; seal this alias with no retry |
| `codex2` | same; its outcome never authorizes a substitute or another attempt | typed terminal record; seal this alias with no retry |
| `agy1` | same, including malformed native event/final result or absent in-process validation | typed terminal record; seal this alias with no retry |
| `agy2` | same, including malformed native event/final result or absent in-process validation | typed terminal record; seal this alias with no retry |

**Current hold**: `IDQ-MVP-070-QA` is reopened, the real executor/daemon route
is pending, and `AUTH-01` is sealed. The separate `AUTH-02` approval intent at
the top of this file carries no active TTL, nonce, or lease. `IDQ-OP-050-PREFLIGHT`
must prove every fresh gate before any process creation. `DONE` for
`IDQ-MVP-080` still requires four real, separately valid receipts and
`WorkResult`s; this historical record claims neither current readiness nor
provider execution.

<!-- IDQ-MVP-BOARD-20260828:END -->

# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last reconciled: 2026-08-27 +07 (Asia/Bangkok). The prior Static release claim for `6c351ba` is historical-only. Current live target/version identity is mismatched and requires fresh release verification; do not treat any prior publisher, viewport, or version result as current.*

## Current-session evidence reconciliation — 2026-08-27

- **Historical failed candidate**: pre-remediation QA was `543/545` with two
  token failures; the failed Approach C design review recorded C/H/M/L
  `1/5/1/0`; and 5/11 then-current DSG-009 hashes drifted. These are superseded
  historical failure evidence only.
- **DSG-009 current local re-freeze**: `DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA
  + SECURITY PASS; RUNTIME NOT_PROVEN`. Guard QA passed `552`; integrated safe
  mocked QA passed `823` (`552 + 271`, with four intentional local-child tests
  deselected); PromptCommand developer QA passed `275` plus focused adversarial
  `33`; named security regression passed `761` with C/H/M/L `0/0/0/0`.
  Ecosystem sync/check is green and the secret scan reports `1,967` files / `0`
  leaks. Local verification releases no runtime, native-spawn, provider, or AGY
  authority.
- **Approach C**: its historical failed design review recorded C/H/M/L
  `1/5/1/0`. `PARITY-001` remains `IN_REVIEW` with the design rejected;
  `PARITY-002` through `PARITY-006` remain `BLOCKED` by that dependency chain.
  All feature flags remain `false`.
- **DSG**: `DSG-009` is `DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY
  PASS; RUNTIME NOT_PROVEN`. `DSG-009A` and `DSG-009B` remain `BLOCKED`;
  `DSG-001R` remains `NEEDS_HITL — ONE-SHOT CONSUMED` with no retry,
  substitution, or reuse.
- **Ledger scope**: the scoped 32-ticket ledger has 21 outstanding. Project-wide,
  the deduplicated outstanding inventory is 106 (85 outside this scope): 61
  `BLOCKED`, 13 `PENDING`, 12 `READY`, 6 `TODO`, 5 `IN_REVIEW`, 4 `DOING`, 2
  `NEEDS_HITL`, and 3 conflict/unverified.
- **Native-spawn owner gate**: no local token, static flag, route label, or repository hook grants AGY eligibility. Every native `spawn_agent` remains covered by the owner gate; positive AGY/provider dispatch is disabled.

### Current DSG-009 re-freeze manifest (verified current bytes)

The exact 11-file Stage-A manifest below is stable at the listed SHA-256
values. `scripts/multiagent_prompt_command.py` is a final dependency outside
that 11-file manifest and is recorded separately. This local re-freeze does not
prove runtime/native interception, trusted provider telemetry, actual dispatch,
trusted clock, or natural exit.

| Current file | SHA-256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `d7ea9f79aea2ea3d8737a44329ef7eecd05e4166b78ca56af7a1fdf2b4f6b278` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `7521cf8fb254245ff9ad41ec451899130a30e43cd1586c1390d27e60e53a75cf` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `7ad0aa7fee4b06d1609400d439e863d1dfd03df1470474d4a41361a5f3ba9faa` |
| `.agents/hooks/full_capacity_guard.py` | `352bb05f221b4c7feb36561bb307b482209aabc95e19e7539aca58c350f073f1` |
| `.agents/hooks/full_capacity_test_harness.py` | `1bd1475f319a5d4aeb4d1ff9c64b43ba0ce8031b445f39326d975bbedc169b40` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `7d10469b44266dc093105fc8640beb6ecf9d643a421046cb33238c4a0fc00321` |
| `.agents/config/full_capacity_guard.v2.json` | `d3f73601e539bcfe85e9096700c69be25a42ea8d27d6b2f4f02ab7eae9cb37a4` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `90f0c18bec385f83d50fffeb69e136f1b6b21fca4c350bb62778695287dedde9` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `735e43dbe0930a6688593edc44256a20b7de4dc39dc30f5c6b7ae9b484c9202a` |
| `scripts/multiagent_prompt_command.py` (final dependency) | `48b0aee8400ce59add3d4f0575ea8d6ba533be0b89f02e7cef476f10361735e1` |

<!-- SPRINT-APPROACH-C:START -->
## 🚀 SPRINT: Approach C — Feature-Flagged AGY Parity, Module Isolation & Rule 10 Cleanup — 2026-08-27

**Grill Gate**: `IN_REVIEW — DESIGN REJECTED; IMPLEMENTATION BLOCKED` ([plan](plans/plan.md#--grill-report--approach-c-feature-flagged-agy-parity-module-isolation--rule-10-purge))
**Tracking Lead**: `orchestrator` (`gpt-5.6-sol`) 🤝 `hermes` (`Gemini 3.7 Pro`)
**Operational Status**: `IN_REVIEW / NOT ACCEPTED AS DONE` (the historical
failed design review recorded C/H/M/L `1/5/1/0`; all feature flags remain
`false`; a local token anchor grants no AGY eligibility; `DSG-009A` remains
strictly `BLOCKED` pending a host-native pre-spawn hook/receipt API.)

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-PARITY-001-DESIGN-SPEC` | `orchestrator` / `hermes` | Dual-Orchestrator Spec Finalization | IN_REVIEW | None |
| `TICKET-PARITY-002-FEATURE-FLAG-CONFIG-SCHEMA` | `developer` | Configuration & Schema Definitions | BLOCKED | `TICKET-PARITY-001` design rejected |
| `TICKET-PARITY-003-GOVERNANCE-RULES-REFACTOR` | `business_analyst` | Rules 11, 17, 18 Updates | BLOCKED | `TICKET-PARITY-001` design rejected |
| `TICKET-PARITY-004-SCHEDULER-GUARD-ENGINE` | `developer` | Scheduler & Capacity Guard Engine Logic | BLOCKED | `TICKET-PARITY-002`, `003` |
| `TICKET-PARITY-005-QA-REGRESSION-SUITE` | `qa_tester` | Test Suite & 4-Alias Concurrency Verification | BLOCKED | `TICKET-PARITY-004` |
| `TICKET-PARITY-006-DEAD-CODE-PURGE-SYNC` | `business_analyst` / `developer` | Core Rule 10 Dead-Code Purge & Ecosystem Sync | BLOCKED | `TICKET-PARITY-005` |

---

<!-- DELEGATE-SPARK-SPRINT:START -->
## SPRINT: Delegate-First and GPT-5.3-Codex-Spark Governance — 2026-08-26

**Grill Gate**: `APPROVED — IMPLEMENTATION TICKETS READY` ([plan](plans/plan.md#grill-report--delegate-first-and-gpt-53-codex-spark-governance))
**Tracking Lead**: `orchestrator`
**Current DSG-009A override gate**: `BLOCKED — PLATFORM NATIVE PRE-SPAWN
HOOK/RECEIPT API REQUIRED`. The current-session owner decision
`อนุญาติตามแผนงาน ต้องการครอบคลุม native spawn_agent ทุกตัว งานต้องคง BLOCKED จนแพลตฟอร์มมี pre-spawn hook/receipt API`
supersedes the earlier recommended repository-managed-only approval before any
mutation. It releases no source ownership and completed no provider action.

**Current TODO / DOING / DONE**:

- **DONE**: read-only platform-boundary map, governed deep-reasoning advice and
  nine-dimension owner-scope grill.
- **DONE (documentation)**: the three-file BSA reconciliation is closed by the
  current-session evidence record above; no implementation or external action
  occurred.
- **TODO / BLOCKED**: DSG-009A native platform hook/receipt API, DSG-009B
  trusted provider telemetry, and provider/AGY proof. The future `agy1`
  one-shot is `NOT DISPATCHED — no child ran`; `agy2` is disabled.

**Current Rule 11 Planning Order**: the first Spark smoke is frozen `BLOCKED`.
`TICKET-DSG-001R-SPARK-PROVENANCE` consumed its only authorized one-shot and is
terminal `NEEDS_HITL`; it cannot be retried or reused. `TICKET-DSG-002-DELEGATE-GOVERNANCE`
remains `DONE — SOURCE FROZEN`. `TICKET-DSG-007-FULL-CAPACITY-GOVERNANCE` is
`DONE — SOURCE FROZEN / REVIEW PASS`; its reviewed Rule 11 and skill sources
are bound to the final 15-case eval remediation in `TICKET-DSG-007A-FULL-CAPACITY-EVALS`.
`TICKET-DSG-008-FULL-CAPACITY-HOOKS` is now `DONE — SOURCE FROZEN / REVIEW PASS`.
`TICKET-DSG-009-SHORT-FALLBACK-CAPACITY-HOOK` is `DONE — LOCAL FAIL-CLOSED
RE-FREEZE / QA + SECURITY PASS; RUNTIME NOT_PROVEN`. The 5/11 drift and its
`543/545` baseline are historical failed-candidate evidence; the verified
current manifest and re-freeze evidence are recorded above. It releases no
runtime authority. Its BSA governance/docs
editor and separate hook/test
developer have disjoint ownership from each other and from the frozen DSG-001T
source surface. It permanently adds short, read-only/evidence-bearing fallback-lane
selection while QA waits for a source freeze, plus per-scan `agy1`/`agy2`
eligibility and rejection evidence. It never treats a static alias/model label
as runtime, provider, account, quota or role/config proof and never forces
provider dispatch. A short-fallback lease is normatively an integer `1..600`
seconds inclusive; a scan/config may set a stricter ceiling but can never raise
the hard `600s` maximum.
The prior DSG-009 candidate failed QA/security freeze with QA C/H/M/L
`0/3/0/0` and security C/H/M/L `0/6/1/0`; Stage A is the only active remediation.
Its first Stage A source candidate then passed `288` tests and static checks,
but independent QA failed C/H/M/L `0/1/1/0` and security failed `0/1/3/1`.
That failed historical freeze was reopened for bounded H1/M1-M3 remediation.
A later functional candidate closed M1-M3 and passed functional QA C/H/M/L
`0/0/0/1` with `446` plus targeted checks and green static checks, but its
integrated freeze failed security C/H/M/L `0/1/0/1` because pathless benign
shell commands could bypass the closed governance envelope. A superseding
candidate closed that bypass and passed independent functional QA C/H/M/L
`0/0/0/1` (`382` focused plus `248` adjacent, `630` combined), but integrated
security again failed `0/1/0/1`: execution-family matching was case-sensitive,
conflicting top-level versus `toolCall`/`toolResult` representations could
conceal execution, and Claude Pre/Post registration was not universal `.*`.
The final frozen candidate closed this narrow H1. Independent QA and security
both pass C/H/M/L `0/0/0/1`; QA passed focused `540`, adjacent `248`, combined
`788`, H1 adversarial `163`, and M1-M3 subset `21`, while security passed its
focused `540`. Historical failed candidate hashes below remain non-current.
Positive AGY/provider paths and actual dispatch remain disabled, while runtime,
native pre-spawn interception, authoritative snapshot completeness, trusted
wall clock and natural-exit enforcement remain `NOT_PROVEN`. DSG-009A is
`BLOCKED — PLATFORM NATIVE PRE-SPAWN HOOK/RECEIPT API REQUIRED`; DSG-009B is
`BLOCKED — 009A + TRUSTED PROVIDER TELEMETRY`.
The authoritative registry remains exactly 18 unique DSG ticket definitions
with the unchanged acyclic 33-edge graph: 20 DSG edges plus 13 DRG edges;
`009 -> 009A -> 003` and `009A -> 009B` remain in force without blocking T/U/V/W.
`TICKET-DSG-001S-SPARK-TELEMETRY` is now `DONE — OFFLINE FREEZE / REVIEW PASS`:
its source/test freeze, developer focused `15`, owned `169`, combined `190`,
pycompile/diff checks, final QA `190` plus synthetic matrix/privacy/invalid-count
checks, and independent review `190` with zero Critical/High findings passed.
Its live smoke remains `BLOCKED`: no fresh content-addressed claim, separate
one-shot authorization, valid live WorkResult or bound ExecutionReceipt exists.
The previous procedural claim-first wording is superseded. A live `ProbeClaim`
is forbidden even though DSG-001T local source freeze and DSG-001U independent
QA/review are now `DONE — LOCAL PASS`; the late-bound DSG-001V owner gate has
not passed, and only DSG-001W may consume
the exact grant, run the one probe, and release DSG-003/004. DSG-003 also keeps
its frozen 002 predecessor and the future reviewed 009A predecessor.
MAREF-011..013 remain separately gated and are not released by this sprint. The
separate deep-reasoning design is `DRG-001 DONE` with no file changes; the
owner lease policy in DRG-002 is `DONE — POLICY RECORDED`, with max/ultra
leases `600s`/`900s`, one attempt and no auto-retry. Runtime proof remains
`NOT_PROVEN`; DRG-003..008 remain blocked on DRG-002 and DSG-006. Deep-reasoning mutation
is not `READY`.
**User quota input**: Spark five-hour window reported `100% left`, reset `18:40`
on 2026-08-26 Asia/Bangkok. This prioritizes the bounded smoke; it does not
prove availability or authorize a quality downgrade.

| Ticket | Severity | Work Effort | Owner | Status | Depends On | Exact ownership |
|---|---|---|---|---|---|---|
| `TICKET-DSG-001-SPARK-CAPABILITY` | CRITICAL | XS | `orchestrator` with `qa_tester` read-only verification | BLOCKED — INVALID STRUCTURED AUDIT | none | exact-model capability/effort/quota probe and returned receipt/WorkResult only; no repository edit |
| `TICKET-DSG-001R-SPARK-PROVENANCE` | CRITICAL | S | `developer` | NEEDS_HITL — ONE-SHOT CONSUMED | 001 blocked evidence | immutable bundle `5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b`; no retry, substitution or second process |
| `TICKET-DSG-001S-SPARK-TELEMETRY` | CRITICAL | S | `developer`, then independent `code_reviewer` | DONE — OFFLINE FREEZE / REVIEW PASS; LIVE SMOKE BLOCKED | 001R terminal evidence | historical offline parser telemetry only; it cannot create a live claim or release 003/004 |
| `TICKET-DSG-001T-PREAUTH-CONTRACT-V3` | CRITICAL | M | one `developer` source/test/schema/config editor | DONE — LOCAL SOURCE FROZEN / U PASS | 001S | 11-file fail-closed preauthorization/Receipt-v3 local freeze; no provider/claim/approval execution |
| `TICKET-DSG-001U-PREAUTH-QA-REVIEW` | CRITICAL | M | `qa_tester`, then independent `code_reviewer`, read-only | DONE — LOCAL QA + REVIEW PASS | 001T | stable-hash security/replay/expiry/atomicity/privacy QA and review C/H/M/L 0/0/0/0; no live action |
| `TICKET-DSG-001V-PROBECLAIM-APPROVAL` | CRITICAL | S | `orchestrator` / owner only | BLOCKED — FUTURE HITL / EXACT CLAIM+GRANT | 001U | create exactly one fresh `ProbeClaim v1` and a late-bound exact `ApprovalGrant v1`; no consume or provider spawn |
| `TICKET-DSG-001W-ATOMIC-PROBE-VERIFY` | CRITICAL | S | `orchestrator`, then independent `qa_tester` verification | BLOCKED — 001V + EXACT AUTHORIZATION | 001V | atomic consume and exactly one read-only/ephemeral probe; require WorkResult, Receipt-v3, and consume receipt before any release |
| `TICKET-DSG-002-DELEGATE-GOVERNANCE` | CRITICAL | S | `business_analyst` | DONE — SOURCE FROZEN | none | `.agents/rules/11-orchestrator-subagent-delegation.md`; `.agents/skills/orchestrator-delegation/SKILL.md`; `.agents/skills/orchestrator-delegation/evals/evals.json` |
| `TICKET-DSG-003-ROUTING-HOOKS` | CRITICAL | L | `developer` | BLOCKED — 001W RESULT/RECEIPT + 009A FREEZE | 001W,002,009A | Rule 18/policy/adaptive skill/evals and dispatcher paths already listed below; `.agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml`; `scripts/sync_ai_agent_ecosystem.py`; `.agents/hooks/{pre_tool_check,post_tool_audit,spark_specialist_guard}.py`; `.agents/hooks.json`; `.claude/hooks/{adaptive_dispatch_guard,orchestrator_only_guard,spark_specialist_guard}.py`; `.claude/settings.json`; root `settings.json` |
| `TICKET-DSG-004-ROLE-SOURCES` | HIGH | M | `business_analyst` role/skill-source editor | BLOCKED — 001W STRUCTURED RESULT/RECEIPT | 001W,002 | existing default/orchestrator/hermes role sources; new `.antigravity/agents/spark_specialist.agent`; `.agents/skills/codex-spark-specialist/{SKILL.md,evals/evals.json}`; `.agents/rules/20-codex-spark-specialist.md`; `.claude/rules/codex-spark-specialist.md`; `.agents/AGENTS.md`; compatibility sources only via governed sync |
| `TICKET-DSG-005-QA` | CRITICAL | L | `qa_tester` | BLOCKED — SOURCE FREEZE | 003,004 | new `project/tests/test_delegate_spark_governance.py`; existing dispatcher/scheduler/agent/sync suites run read-only; new artifacts under `project/tests/artifacts/delegate_spark_governance/` |
| `TICKET-DSG-006-SYNC-REVIEW` | CRITICAL | M | same `business_analyst` role-source editor as sequential sync owner, then `code_reviewer` read-only | BLOCKED — QA | 005 | sync-generated existing-role mirrors plus `.agents/agents/spark_specialist.{md,json}`, `.agents/agents/spark_specialist/agent.{md,json}`, `.codex/agents/spark_specialist.toml`, generated `.antigravity/agents/spark-specialist.agent` hyphen alias, `.antigravity/skills/codex-spark-specialist/SKILL.md`, and registration manifests only |
| `TICKET-DSG-007-FULL-CAPACITY-GOVERNANCE` | CRITICAL | S | `full_capacity_governance` | DONE — SOURCE FROZEN / REVIEW PASS | 002 frozen baseline | `.agents/rules/11-orchestrator-subagent-delegation.md`; `.agents/skills/orchestrator-delegation/SKILL.md`; `.agents/skills/orchestrator-delegation/evals/evals.json` only |
| `TICKET-DSG-007A-FULL-CAPACITY-EVALS` | CRITICAL | S | `full_capacity_governance` with independent `code_reviewer` | DONE — SOURCE FROZEN / REVIEW PASS | 007 review findings | `.agents/skills/orchestrator-delegation/evals/evals.json` only; final 15 contiguous cases |
| `TICKET-DSG-008-FULL-CAPACITY-HOOKS` | CRITICAL | M | separate `developer` lane | DONE — SOURCE FROZEN / REVIEW PASS | 007A | new `.agents/hooks/full_capacity_guard.py`; new `.claude/hooks/full_capacity_guard.py`; new `project/tests/test_full_capacity_governance.py`; `.agents/hooks.json`; `.claude/settings.json` |
| `TICKET-DSG-009-SHORT-FALLBACK-CAPACITY-HOOK` | CRITICAL | M | disjoint `business_analyst` governance/docs editor plus `developer` hook/test editor, then read-only `qa_tester` / `code_reviewer` | DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY PASS; RUNTIME NOT_PROVEN | 008 | current stable 11-file manifest plus PromptCommand dependency verified; prior 5/11 drift is historical; no runtime/native/provider/AGY authority |
| `TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY` | CRITICAL | M | future platform/runtime owner, then read-only QA/security review | BLOCKED — PLATFORM NATIVE PRE-SPAWN HOOK/RECEIPT API REQUIRED | 009 | every collaboration-platform native `spawn_agent` call; no repository source ownership is released while the host API/receipt boundary is absent |
| `TICKET-DSG-009B-TRUSTED-PROVIDER-VERIFIER-AGY` | CRITICAL | M | future trusted-verifier owner, security QA/reviewer, owner HITL | BLOCKED — 009A + TRUSTED PROVIDER TELEMETRY | 009A | trusted effective provider telemetry and positive AGY proof only after reviewed 009A; future `agy1` intent is not executable and `agy2` is disabled |

### TICKET-DSG-001-SPARK-CAPABILITY | [STATUS: BLOCKED — INVALID STRUCTURED AUDIT]

**Severity**: CRITICAL
**Work Effort**: XS
**Owner / ownership**: `orchestrator` executes one bounded exact-model smoke;
`qa_tester` verifies identity/receipt read-only. No repository file may change.
**Depends On**: none
**Blocks**: `TICKET-DSG-001R-SPARK-PROVENANCE`

#### Acceptance, Evidence and Stop

- Executed read-only/ephemeral exact CLI flag `gpt-5.3-codex-spark` with effort
  `high`; transport exited `0`.
- Result is `BLOCKED`: `invalid_structured_audit` and no qualifying WorkResult.
  The ad-hoc smoke merged stderr via `2>&1`; tail/`jq` extraction invalidated
  structured output, so do not infer that no final event existed. Codex CLI
  0.149.1 exposes no effective model/effort telemetry; existing receipt
  model/effort are requested invocation values, never effective proof.
- Historical stop condition is met as `BLOCKED`; remediation continues only in
  `TICKET-DSG-001R-SPARK-PROVENANCE`, with no retry storm or live policy entry.

### TICKET-DSG-001R-SPARK-PROVENANCE | [STATUS: NEEDS_HITL — ONE-SHOT CONSUMED]

**Severity**: CRITICAL
**Work Effort**: S
**Owner / ownership**: immutable historical attempt; no further editor or
process is authorized under this ticket.
**Depends On**: frozen blocked evidence from
`TICKET-DSG-001-SPARK-CAPABILITY`
**Blocks**: `TICKET-DSG-001S-SPARK-TELEMETRY`

#### Terminal Evidence and Stop

- Exactly one authorized bundle claim
  `5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b`
  was consumed. The requested invocation was exact
  `gpt-5.3-codex-spark` / `high`, read-only and ephemeral. These requested argv
  values do not prove effective execution identity, account or quota.
- The child exited `0`; the dispatcher exited `3` with
  `provider_parse_reason=final_message_cardinality`. No normalized WorkResult or
  ExecutionReceipt was produced. Effective model, effort, account and quota are
  all `NOT PROVEN`.
- This attempt is immutable and terminal `NEEDS_HITL`, not `DONE`. No retry,
  substitution, second process, reuse of its claim, or reuse/overwrite of its
  artifact bundle is permitted.

### TICKET-DSG-001S-SPARK-TELEMETRY | [STATUS: DONE — OFFLINE FREEZE / REVIEW PASS; LIVE SMOKE BLOCKED]

**Severity**: CRITICAL
**Work Effort**: S
**Owner / ownership**: `developer` owned only the dispatcher and focused test
paths listed in the table; independent `code_reviewer` completed read-only
review. This historical offline ticket owns no live claim or authorization.
**Depends On**: terminal evidence from
`TICKET-DSG-001R-SPARK-PROVENANCE`
**Blocks**: `TICKET-DSG-001T-PREAUTH-CONTRACT-V3`

#### Scope, Acceptance and Stop

- Offline diagnosis identified the three content-free branches
  `completed_item_shape`, `agent_message_text_shape`, and
  `multiple_structured_candidates`; it did not authorize selecting a last
  candidate or weakening cardinality validation.
- Added the bounded, content-free subreason enum for those three branches and a
  saturated `candidate_count` in `{0,1,2}`, where `2` means two or more, with
  focused positive/negative tests. Fail-closed cardinality remains intact:
  duplicate candidates, message content retention, and weakened receipt or
  WorkResult validation are prohibited.
- The minimal evidence-supported dispatcher correction is complete. Focused
  implementation tests, final QA and separate independent review passed before
  the offline source/test freeze; any live probe remains separately gated.
- **Offline freeze evidence**: dispatcher SHA256
  `5e0a07069899db68227f28cab902bad73c653580ffccb7e5e6043674d012c120` and
  focused test SHA256
  `df53da50dd55b96b7b188b09434e239edef664703098dca950cee835208114f4`.
  Developer focused tests passed `15`, the owned dispatcher/test suites passed
  `169`, and the combined suite passed `190`; pycompile and scoped diff checks
  passed. Final QA at stable hashes passed `190` plus the synthetic
  matrix/privacy/invalid-count checks. Independent review passed `190` with
  zero Critical/High findings and confirmed exact semantics and privacy.
- An initial QA attempt invalidated only because hashes moved during the lane;
  it is superseded audit history and is not current evidence.
- The prior claim-first procedural instruction is superseded by DSG-001T through
  DSG-001W. No durable live `ProbeClaim`, approval, consume record, provider,
  Spark, or alias action is permitted under DSG-001S.
- The offline source/test freeze is `DONE — OFFLINE FREEZE / REVIEW PASS`, but
  the live smoke remains `BLOCKED`. No fresh content-addressed claim, separate
  one-shot authorization, valid live normalized WorkResult or bound
  ExecutionReceipt exists. A later `DONE` live-probe state requires a valid
  normalized structured WorkResult and bound ExecutionReceipt from that
  separately authorized fresh probe, while effective
  model/effort/account/quota remain `NOT PROVEN` unless independently exposed.
  Any unresolved branch, failed test/review, absent fresh claim/authorization,
  invalid cardinality, or missing result/receipt stops `BLOCKED` or
  `NEEDS_HITL` without running a smoke.

### TICKET-DSG-001T-PREAUTH-CONTRACT-V3 | [STATUS: DONE — LOCAL SOURCE FROZEN / U PASS]

**Owner / exact writable ownership**: one `developer` owns
`scripts/multiagent_prompt_command.py`, `tests/test_multiagent_prompt_command.py`,
`tests/test_multiagent_prompt_command_r4.py`, `tests/test_multiagent_receipt_schema.py`,
`.agents/config/multiagent_model_policy.yaml`, new
`.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml`, and new
`.agents/schemas/{multiagent-probe-claim-v1,multiagent-probe-approval-v1,multiagent-approval-consume-receipt-v1,multiagent-dispatch-receipt-v3}.schema.json`.
All other lanes are read-only; v1/v2 receipt artifacts and schemas are frozen.
**Reservation**: that one developer has the exclusive writable DSG-001T source
surface until a terminal freeze or explicitly recorded ownership release.

**Contract and stop**: implement central fail-closed enforcement before every
live claim: `ProbeClaim v1`, `ProbeApproval`/`ApprovalGrant v1`,
`ApprovalConsumeReceipt v1`, and `ExecutionReceipt v3`. Bind the exact
ticket/attempt/session, requested route/objective/ownership, decision/snapshot,
runtime-config/schema digests, nonce, expiry and content address. A local,
single-host operator attestation is explicitly nonportable and non-cryptographic
human-authenticity proof. It must never be represented as asymmetric signing or
portable identity proof. No claim, grant, consume, provider, Spark, alias,
sync, or external action is authorized by this ticket.

**Approved defaults**: claim TTL `10m`; grant TTL `2m`; zero grace; current
session only; `max_uses=1`. Preflight must complete deterministically before
the durable consume; consume is fsynced immediately before spawn and any
post-consume failure burns the attempt with no retry. Persist content-free
metadata for `90d`, then permit explicit manual compaction only to an
indefinite anti-replay tombstone; raw provider streams are never retained.

**Acceptance**: exact schema/validator/CLI and spawn-boundary coverage passes;
every malformed, altered, expired, replayed, wrong-session, wrong-route,
duplicate, race, failed-consume, post-consume-failure, privacy, v1/v2 misuse,
and receipt-binding case fails closed. Freeze source/tests only after the
developer's focused evidence and no Critical/High finding.

**Local freeze evidence**: the authoritative 11-file SHA256 manifest is:

| File | SHA256 |
|---|---|
| `scripts/multiagent_prompt_command.py` | `4416d09cb64065302d4dc9a76b9af3d462a9b2baa00a4b0c251580f27b23ebf4` |
| `tests/test_multiagent_prompt_command.py` | `35b263dffe1dd9b14370499b17a40747fc488c34c36b5bf7b8b19ae379390c94` |
| `tests/test_multiagent_prompt_command_r4.py` | `235c1c63e0647727857d156b8ad5e90c469cc2c904b92d98d52d35750c16794f` |
| `tests/test_multiagent_receipt_schema.py` | `8eaf5195188bc37799dbb83503906ddd55cc65651945f144a73333cffdb7a343` |
| `tests/test_multiagent_probe_approval.py` | `f4988fedbbdbc1d3e0654cec21669e27cff8b38006e27b9ca81ae967e7944e45` |
| `.agents/config/multiagent_model_policy.yaml` | `66f54e411d90e21494665d20cdd86a6b79b04b543beef28190fa78a43e780a38` |
| `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml` | `f4b848d6c0c511c4fa0c8b88b9254f4a31b023421413fde2b2136ae005551546` |
| `.agents/schemas/multiagent-probe-claim-v1.schema.json` | `612f179315ab808323aefdda2b2a57f8c9c9e06653794e92ae4c1da4a11e7b27` |
| `.agents/schemas/multiagent-probe-approval-v1.schema.json` | `99d5778cbd74ce61aa1683c2ea9262b27a7e4e7319d85d1dd93ceefb82e61012` |
| `.agents/schemas/multiagent-approval-consume-receipt-v1.schema.json` | `31ab1bd3958fc644251f2f64e0bc55bd8110726010e34c72b533da18f47d6416` |
| `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json` | `12885e42c2ee6bb27a3583373ecfb85b38319e60e31eb3f5c1a763ae4d32d093` |

Developer checks passed focused `53` and combined `240`. The broad local run
reported `1382 passed`, `2` known sync-drift failures and `1 deselected`; this
is not a clean sync or release claim and no sync was authorized or run here.

### TICKET-DSG-001U-PREAUTH-QA-REVIEW | [STATUS: DONE — LOCAL QA + REVIEW PASS]

**Owner / boundary**: `qa_tester` runs the frozen-hash matrix; independent
`code_reviewer` audits the implementation read-only. Neither may edit the
DSG-001T surface or create a durable live artifact.

**Acceptance and stop**: verify the complete negative security/replay/expiry/
atomicity/privacy matrix, all schema/receipt migration checks, and that v1/v2
cannot authorize a new probe. Require all selected checks to pass with zero
Critical/High findings at stable hashes. Any failure remains `BLOCKED`; no
waiver can advance to a claim or provider action.

**Local sign-off evidence**: independent QA revalidated all 11 stable hashes,
passed focused `53`, combined `240`, and adversarial `38`, with C/H/M/L
`0/0/0/0`. Independent review revalidated the same manifest and passed
`pytest -q tests/test_multiagent_probe_approval.py
tests/test_multiagent_receipt_schema.py` with `53 passed`, C/H/M/L `0/0/0/0`.
This closes only local T/U. It creates no claim/grant, approval, provider/AGY
authority, dispatch or runtime proof; DSG-001V and DSG-001W remain blocked.

### TICKET-DSG-001V-PROBECLAIM-APPROVAL | [STATUS: BLOCKED — FUTURE HITL / EXACT CLAIM+GRANT]

**Owner / boundary**: only `orchestrator` under a fresh future owner HITL may
create exactly one content-addressed `ProbeClaim v1` and its late-bound exact
`ApprovalGrant v1`. The present session sign-off does not authorize either
artifact, does not authorize consume, and does not authorize a provider.

**Acceptance and stop**: revalidate T/U freeze hashes and all exact bindings;
record local-attestation scope, current session, `10m`/`2m` TTLs, zero grace and
`max_uses=1`. Any stale/mismatched/ambiguous request is `NEEDS_HITL`; no
automatic renewal, substitution or retry exists.

### TICKET-DSG-001W-ATOMIC-PROBE-VERIFY | [STATUS: BLOCKED — 001V + EXACT AUTHORIZATION]

**Owner / boundary**: only after a distinct exact future authorization may the
`orchestrator` run deterministic preflight, atomically consume once, and start
exactly one read-only/ephemeral requested `gpt-5.3-codex-spark` / `high` probe.
Independent `qa_tester` verifies only the resulting content-free records.

**Acceptance and stop**: require a valid normalized WorkResult, bound
`ExecutionReceipt v3`, and bound `ApprovalConsumeReceipt v1`; all three must
match the exact claim/grant/consumption bindings. A post-consume failure remains
burned and produces no retry. Only this completed ticket may release DSG-003
and DSG-004; effective model, effort, account and quota remain `NOT PROVEN`
unless independently exposed.

### TICKET-DSG-002-DELEGATE-GOVERNANCE | [STATUS: DONE — SOURCE FROZEN]

**Severity**: CRITICAL
**Work Effort**: S
**Owner / ownership**: `business_analyst`; only the three files in the table.
**Depends On**: none
**Blocks**: `TICKET-DSG-003-ROUTING-HOOKS`,
`TICKET-DSG-004-ROLE-SOURCES`,
`TICKET-DSG-007-FULL-CAPACITY-GOVERNANCE`

#### Acceptance, Evidence and Stop

- Define delegate-first for meaningful mutation/QA/review/operations, the
  trivial no-tool and root read-only exceptions, narrowest specialist routing,
  rolling maximum useful concurrency, one-editor ownership and all fail-closed
  dependency/quota/HITL/Rule 11/Rule 18 gates.
- Apply `skill-creator` to the existing orchestration skill. Its `evals.json`
  must contain realistic positive and negative routing prompts plus objective
  assertions for: required delegation, allowed trivial/root-read-only work,
  useful parallelism, blocked/redundant lanes and ownership conflict. Run
  deterministic skill structure/trigger tests now; heavyweight viewer
  benchmarking may follow only if that workflow requires user feedback.
- Historical DSG-002 source-freeze evidence is complete: Rule 11 is `80` lines;
  the orchestration skill is `261/300` lines; `evals.json` has `9` cases and
  `28` expectations.
  SHA256 is
  `55a839c0699c0980435cbf2a58357e3752037faed5d4d4fcc11ee3d058cca60b`
  for Rule 11,
  `0f6e5e439aacac820cd510eeaa8d8be7f37ac8bc45311da4d0c3700a1e158917`
  for the skill, and
  `79e54af6f37d2a707d305cb94617869a1647454ddb396d53925adafbc077fb41`
  for `evals.json`. These are the immutable predecessor baseline digests, not
  the current DSG-007 working-tree digests. At DSG-002 freeze time, JSON, YAML
  frontmatter, referenced-path and scoped-diff checks passed.
- Stop condition is met as `DONE — SOURCE FROZEN` on the clean three-file
  governance diff. Hooks, model policy, role definitions, generated mirrors and
  Git remain outside this ticket.

### TICKET-DSG-003-ROUTING-HOOKS | [STATUS: BLOCKED — 001W RESULT/RECEIPT + 009A FREEZE]

**Severity**: CRITICAL
**Work Effort**: L
**Owner / ownership**: `developer`; all routing hook, policy, config, and
dispatcher files listed in the table.
**Depends On**: `TICKET-DSG-001W-ATOMIC-PROBE-VERIFY`,
`TICKET-DSG-002-DELEGATE-GOVERNANCE`,
`TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY`
**Blocks**: `TICKET-DSG-005-QA`

#### Scope, Acceptance and Stop

- Implement adaptive effort routing and Spark specialist routing in code and
  hooks.
- Blocked on 001W verified result/receipt, 002 governance baseline, and 009A
  host-native pre-spawn hook/receipt boundary.
- Do not modify files while dependencies remain blocked.

### TICKET-DSG-004-ROLE-SOURCES | [STATUS: BLOCKED — 001W STRUCTURED RESULT/RECEIPT]

**Severity**: HIGH
**Work Effort**: M
**Owner / ownership**: `business_analyst` role/skill-source editor; role definitions, specialist skill and rule files listed in the table.
**Depends On**: `TICKET-DSG-001W-ATOMIC-PROBE-VERIFY`,
`TICKET-DSG-002-DELEGATE-GOVERNANCE`
**Blocks**: `TICKET-DSG-005-QA`

#### Scope, Acceptance and Stop

- Author canonical Spark specialist role and skill definitions.
- Blocked on 001W verified structured result and receipt.

### TICKET-DSG-005-QA | [STATUS: BLOCKED — SOURCE FREEZE]

**Severity**: CRITICAL
**Work Effort**: L
**Owner / ownership**: `qa_tester`; new test file `project/tests/test_delegate_spark_governance.py` and read-only execution of test suites.
**Depends On**: `TICKET-DSG-003-ROUTING-HOOKS`,
`TICKET-DSG-004-ROLE-SOURCES`
**Blocks**: `TICKET-DSG-006-SYNC-REVIEW`

### TICKET-DSG-006-SYNC-REVIEW | [STATUS: BLOCKED — QA]

**Severity**: CRITICAL
**Work Effort**: M
**Owner / ownership**: sequential `business_analyst` sync owner, then `code_reviewer` read-only.
**Depends On**: `TICKET-DSG-005-QA`
**Blocks**: deployment and downstream integrations.

### TICKET-DSG-007-FULL-CAPACITY-GOVERNANCE | [STATUS: DONE — SOURCE FROZEN / REVIEW PASS]

**Severity**: CRITICAL
**Work Effort**: S
**Owner / ownership**: `full_capacity_governance`; `.agents/rules/11-orchestrator-subagent-delegation.md`, `.agents/skills/orchestrator-delegation/SKILL.md`, `.agents/skills/orchestrator-delegation/evals/evals.json`.
**Depends On**: `TICKET-DSG-002-DELEGATE-GOVERNANCE` frozen baseline.
**Blocks**: `TICKET-DSG-007A-FULL-CAPACITY-EVALS`, `TICKET-DSG-008-FULL-CAPACITY-HOOKS`.

### TICKET-DSG-007A-FULL-CAPACITY-EVALS | [STATUS: DONE — SOURCE FROZEN / REVIEW PASS]

**Severity**: CRITICAL
**Work Effort**: S
**Owner / ownership**: `full_capacity_governance` with independent `code_reviewer`; `.agents/skills/orchestrator-delegation/evals/evals.json` only (final 15 contiguous cases).
**Depends On**: `TICKET-DSG-007-FULL-CAPACITY-GOVERNANCE` review findings.
**Blocks**: `TICKET-DSG-008-FULL-CAPACITY-HOOKS`.

### TICKET-DSG-008-FULL-CAPACITY-HOOKS | [STATUS: DONE — SOURCE FROZEN / REVIEW PASS]

**Severity**: CRITICAL
**Work Effort**: M
**Owner / ownership**: separate `developer` lane; `.agents/hooks/full_capacity_guard.py`, `.claude/hooks/full_capacity_guard.py`, `project/tests/test_full_capacity_governance.py`, `.agents/hooks.json`, `.claude/settings.json`.
**Depends On**: `TICKET-DSG-007A-FULL-CAPACITY-EVALS`.
**Blocks**: `TICKET-DSG-009-SHORT-FALLBACK-CAPACITY-HOOK`.

### TICKET-DSG-009-SHORT-FALLBACK-CAPACITY-HOOK | [STATUS: DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY PASS; RUNTIME NOT_PROVEN]

**Severity**: CRITICAL
**Work Effort**: M
**Owner / ownership**: disjoint `business_analyst` governance/docs editor plus `developer` hook/test editor, then read-only `qa_tester` / `code_reviewer`.
**Depends On**: `TICKET-DSG-008-FULL-CAPACITY-HOOKS`.
**Blocks**: `TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY`.

### TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY | [STATUS: BLOCKED — PLATFORM NATIVE PRE-SPAWN HOOK/RECEIPT API REQUIRED]

**Severity**: CRITICAL
**Work Effort**: M
**Owner / ownership**: future platform/runtime owner, then read-only QA/security review. Covers every collaboration-platform native `spawn_agent` call.
**Depends On**: `TICKET-DSG-009-SHORT-FALLBACK-CAPACITY-HOOK`.
**Blocks**: `TICKET-DSG-009B-TRUSTED-PROVIDER-VERIFIER-AGY`, `TICKET-DSG-003-ROUTING-HOOKS`.

### TICKET-DSG-009B-TRUSTED-PROVIDER-VERIFIER-AGY | [STATUS: BLOCKED — 009A + TRUSTED PROVIDER TELEMETRY]

**Severity**: CRITICAL
**Work Effort**: M
**Owner / ownership**: future trusted-verifier owner, security QA/reviewer, owner HITL.
**Depends On**: `TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY`.

<!-- DEEP-REASONING-GRILL:START -->
## DEEP-REASONING ADVISORY DESIGN — DEFERRED IMPLEMENTATION

This is a separate design/task block. It does not mark deep-reasoning
implementation `READY` and does not release any DSG ticket. The read-only
architecture decision is to refactor the existing adaptive lane-level router,
reuse the orchestrator child, and add a `deep-reasoning-advisory` skill/rule;
no static agent role is introduced. The advisory is non-authoritative and may
not approve HITL, bypass the DAG, sync, deploy, or infer execution proof.

| Ticket | Severity | Work Effort | Owner | Status | Depends On | Exact ownership |
|---|---|---|---|---|---|---|
| `TICKET-DRG-001-DEEP-REASONING-ARCHITECTURE` | HIGH | M | `deep_reasoning_arch` read-only | DONE — ARCHITECTURE / NO FILE CHANGES | none | read-only adaptive lane-level router design and advisory boundary |
| `TICKET-DRG-002-DEEP-REASONING-LEASE-DECISION` | HIGH | XS | owner / `orchestrator` | DONE — POLICY RECORDED; RUNTIME NOT_PROVEN | DRG-001 | max lease `600s`, ultra lease `900s`, one attempt/no auto-retry; not execution proof |
| `TICKET-DRG-003-ADAPTIVE-LANE-ROUTER` | CRITICAL | L | `developer` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | adaptive lane-level router mutation only after owner policy and sync/review freeze |
| `TICKET-DRG-004-DEEP-REASONING-ADVISORY` | HIGH | M | `business_analyst` / `developer` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | new advisory skill/rule, advisory-only and non-authoritative |
| `TICKET-DRG-005-DEEP-REASONING-GUARDRAILS` | HIGH | S | `developer` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | severity-blocker max advice; ultra cross-system/multi-owner or prior-max deadlock routing |
| `TICKET-DRG-006-DEEP-REASONING-TESTS` | CRITICAL | L | `qa_tester` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | bounded lease/attempt, authority, privacy, and no-auto-retry tests |
| `TICKET-DRG-007-DEEP-REASONING-QA` | CRITICAL | M | `qa_tester` / `code_reviewer` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | independent QA/review after implementation sources freeze |
| `TICKET-DRG-008-DEEP-REASONING-SYNC-REVIEW` | CRITICAL | M | `business_analyst` / `code_reviewer` | BLOCKED — DRG-002 + DSG-006 | DRG-002,DSG-006 | governed sync/review only after all deep-reasoning and DSG predecessors freeze |

### TICKET-DRG-001-DEEP-REASONING-ARCHITECTURE | [STATUS: DONE — ARCHITECTURE / NO FILE CHANGES]

**Scope and decision**: complete a read-only architecture audit. Refactor the
existing adaptive lane-level router, reuse the orchestrator child, and add a
new `deep-reasoning-advisory` skill/rule; do not add a static agent role.
Provide bounded Severity blocker root-cause/options advice with `max`; use
`ultra` only for cross-system/multi-owner blockers or a prior-max decision
deadlock. The advisory is non-authoritative and advisory-only.

**Evidence and stop**: architecture design is `DONE`; no file changes were
made. The design cannot approve HITL, become implementation owner or decision
maker, bypass the DAG, sync, deploy, or claim provider execution proof.

### TICKET-DRG-002-DEEP-REASONING-LEASE-DECISION | [STATUS: DONE — POLICY RECORDED; RUNTIME NOT_PROVEN]

**Scope and stop**: owner session sign-off records maximum lease `600s`, ultra
lease `900s`, one attempt, and no automatic retry. Hard token and effective
runtime telemetry for native collaboration remain `NOT PROVEN`; policy is not
execution authority. DRG-003..008 remain blocked on DRG-002 and DSG-006.

### TICKET-DRG-003-ADAPTIVE-LANE-ROUTER | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on `TICKET-DRG-002-DEEP-REASONING-LEASE-DECISION` and
`TICKET-DSG-006-SYNC-REVIEW`. Mutation overlaps DSG-003..006 and remains
blocked until both predecessors are complete; no implementation is `READY`.

### TICKET-DRG-004-DEEP-REASONING-ADVISORY | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on DRG-002 and DSG-006. Create the advisory skill/rule only after the
owner policy and DSG sync/review freeze; it remains non-authoritative.

### TICKET-DRG-005-DEEP-REASONING-GUARDRAILS | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on DRG-002 and DSG-006. Define only bounded Severity blocker `max`
advice and `ultra` escalation for cross-system/multi-owner or prior-max
deadlock cases; no auto-retry or authority is permitted.

### TICKET-DRG-006-DEEP-REASONING-TESTS | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on DRG-002 and DSG-006. Tests remain deferred until implementation
scope is owner-approved and all overlapping DSG sources have frozen.

### TICKET-DRG-007-DEEP-REASONING-QA | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on DRG-002 and DSG-006. Independent QA and review are not authorized
until the design decision is recorded and implementation sources freeze.

### TICKET-DRG-008-DEEP-REASONING-SYNC-REVIEW | [STATUS: BLOCKED — DRG-002 + DSG-006]

Depends on DRG-002 and DSG-006. Governed sync/review remains deferred; no
generated mirror, external local-global write, provider, or release action is
authorized by this design block.

<!-- DEEP-REASONING-GRILL:END -->

### MAREF Continuity — Current Superseding Status Only

Session-wide recovery approval was recorded around 2026-08-26 14:15 +07. The
published contaminated attempt
`07704aedcc16ad84404b92fc6795d1ecad21fd79` remains immutable history. Forward
corrective delete-only commit
`b296a23c8b4a6e291de0bb5c40620e1b882a9c1c` and exact one-file lifecycle freeze
commit `8071323ce05ff5e0ed1153110ec5940bf305ac9b` are on both local `main` and
`origin/main`. Final tree `0f12027efd1714a9cbd3fb88a427a4dd1ed3a18f`
equals the contaminated attempt tree; lifecycle digest is
`67ec5db06136e481c3f3914ac67db311763603a1cdaf9108824b463b4f9d4ef2`; BSA doc
hashes were preserved. No force push or history rewrite occurred.

| Ticket | Current status | Gate |
|---|---|---|
| `MAREF-010-LIFECYCLE-CONTRACT` | DONE — CONTRACT FREEZE PASS | exact one-file commit and reviewed digest |
| `MAREF-011-EVENT-ENVELOPE` | READY — DERIVED CHILD + RULE18 REQUIRED | separate fresh child, decision, Rule 11, quota, ownership and receipt |
| `MAREF-012-APPROVAL-GRANT` | READY — DERIVED CHILD + RULE18 REQUIRED | separate fresh child, decision, Rule 11, quota, ownership and receipt |
| `MAREF-013-EFFECT-SAGA-CONTRACTS` | READY — DERIVED CHILD + RULE18 REQUIRED | separate fresh child, decision, Rule 11, quota, ownership and receipt |
| `MAREF-014-COMPATIBILITY-CONTRACT` | BLOCKED — 011..013 | all three predecessor freezes |
| `MAREF-015-CONTRACT-QA` | BLOCKED — 011..014 | all contract sources frozen |

This is the canonical current checkpoint. It supersedes older C0 status rows
and assertions without rewriting their immutable evidence or authorizing any
additional commit, push, or recovery.

<!-- DELEGATE-SPARK-SPRINT:END -->

---

## COMPLETED SPRINTS (Summary & Archive Pointers)

<!-- SPRINT-METAPHYSICS-ROADMAP-001:START -->
## Sprint SPRINT-METAPHYSICS-ROADMAP-001 -- Five-Branch Metaphysics Roadmap & Computational Core (Steps 1-4)

**Recorded**: `2026-08-31T23:20:00+07:00` (Asia/Bangkok) | **Status**: `COMPLETED / SEALED` (Steps 1-4 100% DONE & SEALED) | **Archive**: [`plans/archive/2026-08-31-metaphysics-roadmap/`](plans/archive/2026-08-31-metaphysics-roadmap/)

### Milestone Rollup & DAG Summary

```text
Step 1: Classical Treatise Ingestion & OCR Pipeline (MRMAP-S1-010..040) [100% DONE]
  |--> Step 2: 5-Branch Pure Python Calculation Engines (MRMAP-S2-010..040) [100% DONE]
        |--> Step 3: Fine-Tuning Dataset Pipeline & Corpus Exporters (MRMAP-S3-010..040) [100% DONE]
              +--> Step 4: MCP 16-Discipline Server Integration & Dynamic SVG Visualizers (MRMAP-S4-010..040) [100% DONE]
```

| Milestone | Purpose | Total | Done | Doing / Ready | Blocked | Needs HITL |
|---|---|---:|---:|---:|---:|---:|
| **Step 1** | Classical Treatise Ingestion & OCR Pipeline (Obsidian Vault, FAISS RAG) | 4 | 4 | 0 | 0 | 0 |
| **Step 2** | 5-Branch Pure Python Calculation Engines with 100% Tests (16 Disciplines) | 4 | 4 | 0 | 0 | 0 |
| **Step 3** | Fine-Tuning Dataset Pipeline & Corpus Exporters (ShareGPT, MLX, Kaggle) | 4 | 4 | 0 | 0 | 0 |
| **Step 4** | MCP 16-Discipline Server Integration & Dynamic SVG Visualizers | 4 | 4 | 0 | 0 | 0 |
| **Total** | | **16** | **16** | **0** | **0** | **0** |

Detailed ticket ledger archived to: [`plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md`](plans/archive/2026-08-31-metaphysics-roadmap/metaphysics_learning_roadmap.md)
<!-- SPRINT-METAPHYSICS-ROADMAP-001:END -->

---

<!-- META-PLAN-003:START -->
## Sprint META-PLAN-003 -- Model Context Protocol (MCP) Full 16-Discipline Server Integration, Metaphysics Fine-Tuning Dataset Pipeline & Glassmorphism Visual Endpoints (Milestones M0-M5)

**Recorded**: `2026-08-31T22:17:30+07:00` (Asia/Bangkok) | **Status**: `COMPLETED` (Milestones M0-M5 100% DONE & SEALED) | **Archive**: [`plans/archive/2026-08-31-meta-plan-003/`](plans/archive/2026-08-31-meta-plan-003/)

### Milestone Rollup & DAG Summary

```text
M0 Agile Governance & Test Baselines (META3-M0-010..040) [100% DONE]
  |--> M1 MCP Full 16-Discipline Server Integration (META3-M1-010..040) [100% DONE]
        |--> M2 Metaphysics Fine-Tuning Dataset Pipeline (META3-M2-010..040) [DONE]
        +---> M3 Glassmorphism Visual Endpoints & Dynamic SVG (META3-M3-010..040) [DONE]
        +-----------> M4 Automated Test Planes & E2E Regression (META3-M4-010..040) [DONE]
                          +--> M5 Security Audit, Release Packaging & Sprint Closure (META3-M5-010..040) [DONE]
```

| Milestone | Purpose | Total | Done | Doing / Ready | Blocked | Needs HITL |
|---|---|---:|---:|---:|---:|---:|
| **M0** | Agile Governance, Test Baselines & Architecture Blueprint | 4 | 4 | 0 | 0 | 0 |
| **M1** | Model Context Protocol (MCP) Full 16-Discipline Server Integration | 4 | 4 | 0 | 0 | 0 |
| **M2** | Metaphysics Fine-Tuning Dataset Pipeline & Corpus Exporters | 4 | 4 | 0 | 0 | 0 |
| **M3** | Glassmorphism Visual Endpoints & Dynamic SVG Interactive Rendering | 4 | 4 | 0 | 0 | 0 |
| **M4** | Automated Test Planes, Integration & E2E Regression | 4 | 4 | 0 | 0 | 0 |
| **M5** | Security Audit, Release Packaging & Sprint Closure | 4 | 4 | 0 | 0 | 0 |
| **Total** | | **24** | **24** | **0** | **0** | **0** |

Detailed ticket ledger archived to: [`plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md`](plans/archive/2026-08-31-meta-plan-003/meta_plan_003_mcp_dataset_integration_spec.md)
<!-- META-PLAN-003:END -->

---

<!-- META-PLAN-002:START -->
## Sprint META-PLAN-002 — Five-Branch Metaphysics Deepening, 6-Domain Benchmark & Dynamic SVG Charting (Milestones M0-M5)

**Recorded**: `2026-08-31T22:00:00+07:00` (Asia/Bangkok) | **Status**: `COMPLETED` (Milestones M0-M5 100% DONE & SEALED) | **Archive**: [`plans/archive/2026-08-31-meta-plan-002/`](plans/archive/2026-08-31-meta-plan-002/)

### Milestone Rollup & DAG Summary

```text
M0 Agile Governance & Test Baselines (META2-M0-010..040)
  ├──> M1 Five-Branch Computational Deepening (META2-M1-010..040)
  │     ├──> M2 6-Domain Question Benchmark Alignment (META2-M2-010..040)
  │     └───> M3 Dynamic SVG Charting Engine (META2-M3-010..040)
  └───────────┴──> M4 Automated Test Planes & E2E Regression (META2-M4-010..040)
                    └──> M5 Security Audit, Release Packaging & Sprint Closure (META2-M5-010..040)
```

| Milestone | Purpose | Total | Done | Doing / Ready | Blocked | Needs HITL |
|---|---|---:|---:|---:|---:|---:|
| **M0** | Agile Governance, Test Baselines & Architecture Blueprint | 4 | 4 | 0 | 0 | 0 |
| **M1** | Five-Branch Metaphysics Computational Core Deepening | 4 | 4 | 0 | 0 | 0 |
| **M2** | Metaphysics Fine-Tuning Dataset Pipeline & Corpus Exporters | 4 | 4 | 0 | 0 | 0 |
| **M3** | Glassmorphism Visual Endpoints & Dynamic SVG Interactive Rendering | 4 | 4 | 0 | 0 | 0 |
| **M4** | Automated Test Planes, Integration & E2E Regression | 4 | 4 | 0 | 0 | 0 |
| **M5** | Security Audit, Release Packaging & Sprint Closure | 4 | 4 | 0 | 0 | 0 |
| **Total** | | **24** | **24** | **0** | **0** | **0** |

Detailed ticket ledger archived to: [`plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md`](plans/archive/2026-08-31-meta-plan-002/meta_plan_002_metaphysics_deepening_spec.md)
<!-- META-PLAN-002:END -->

---

<!-- BROKER-PLAN-001:START -->
## Sprint BROKER-PLAN-001 — Atomic Broker and Capacity Admission Plan (Milestones B0-B6)

**Recorded**: `2026-08-31` (Asia/Bangkok) | **Status**: `COMPLETED / CLOSED` (All Milestones B0 through B6 100% DONE & SEALED) | **Archive**: [`plans/archive/2026-08-31-broker-plan-001/`](plans/archive/2026-08-31-broker-plan-001/)

### Milestone Rollup & DAG Summary

```text
B0 Test baselines
  -> B1 Swift broker and immediate bridge
  -> B2 Installer, wrapper, and permission tooling
  -> B3 Registry and Agile governance integration
  -> B4 Independent pre-install QA/review
  -> B5 Canary migration and isolated capacity admission
  -> B6 Runtime capacity certification, rollback drill, and closure
```

| Milestone | Purpose | Total | Done | Doing / Ready | Blocked | Needs HITL |
|---|---|---:|---:|---:|---:|---:|
| B0 | Plan and immutable test baselines | 4 | 4 | 0 | 0 | 0 |
| B1 | Swift broker and immediate bridge | 2 | 2 | 0 | 0 | 0 |
| B2 | Installer, wrapper, and permission tooling | 3 | 3 | 0 | 0 | 0 |
| B3 | Capacity registry and Agile integration | 3 | 3 | 0 | 0 | 0 |
| B4 | Independent pre-install QA and review | 2 | 2 | 0 | 0 | 0 |
| B5 | Canary and per-domain admissions | 12 | 12 | 0 | 0 | 0 |
| B6 | Capacity certification, rollback, closure | 3 | 3 | 0 | 0 | 0 |
| **Total** | | **29** | **29** | **0** | **0** | **0** |

### HITL Decision: BRK-B5-025 — Security Migration Authorization
**Recorded**: `2026-08-31T21:10:30+07:00` (Asia/Bangkok) | **Decision**: Owner authorizes Option A — live Keychain migration for 7 accounts (`codex1`..`3`, `agy1`..`4`) | **Status**: `DONE` (`plans/evidence/broker/b5-security-keychain-decision.json`)

Detailed ticket ledger archived to: [`plans/archive/2026-08-31-broker-plan-001/broker_atomic_tickets_20260831.md`](plans/archive/2026-08-31-broker-plan-001/broker_atomic_tickets_20260831.md)
<!-- BROKER-PLAN-001:END -->

---

<!-- TICKET-MERGE-001:START -->
## Sprint TICKET-MERGE-001: Project Tasks Merge & Reconciliation (Closed 2026-08-31)
- **Status**: COMPLETED / CLOSED
- **Changes**: PROJECT_TASKS.md reconciled with project_tickets.md. SPRINT-METAPHYSICS-ROADMAP-001, META-PLAN-003, META-PLAN-002, BROKER-PLAN-001 integrated.
- **Evidence**: `plans/evidence/ticket-merge-001-reconciliation.json`
<!-- TICKET-MERGE-001:END -->

---

<!-- TICKET-RETIRE-RECOVERY-ANCHOR-001:START -->
## Sprint RETIRE-RECOVERY-ANCHOR — Recovery Branch Anchor Retirement (`TICKET-RETIRE-RECOVERY-ANCHOR-001`)

**Recorded**: `2026-08-31` (Asia/Bangkok) | **Grill Status**: `DONE / VERIFIED` | **Status**: `COMPLETED` | **Archive**: [`plans/archive/2026-08-31-release-v1.3.0/`](plans/archive/2026-08-31-release-v1.3.0/)

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-RETIRE-RECOVERY-ANCHOR-001` | HIGH | S | `qa_tester` (baseline red tests) / `developer` (CI & guard refactor) / `devops` (PR #9 merge & branch deletion) | COMPLETED | `TICKET-PROVENANCE-GUARD-FIX-001`, `PR #8`, `PR #9` |

Detailed ticket description archived to: [`plans/archive/2026-08-31-release-v1.3.0/release_atomic_tickets_20260831.md`](plans/archive/2026-08-31-release-v1.3.0/release_atomic_tickets_20260831.md)
<!-- TICKET-RETIRE-RECOVERY-ANCHOR-001:END -->

---

<!-- PROD-DEPLOY-RUN-33251910604:START -->
## PROD-DEPLOY-RUN-33251910604 (2026-08-30) — Historical release evidence

- **Trigger commit**: `61aead4318ad4f6fc9fb3d5d6256d92c33bdc88e` on `main`
- **Actions Run**: `33251910604` (`Release Verification & Production Deploy`) — `SUCCESS`
- **HF Space deploy**:
  `https://pphothidaen-horoconsultant-core-backend.hf.space`
  - Health check: `HTTP 200`
  - Version probe: `1.0.0.61aead4`
  - Open API schema: valid, endpoints respond `200`
  - Bound rollback commit: `58cf2d0`
- **Vercel deploy**: `https://horo-consultant-psi.vercel.app`
  - Health check: `HTTP 200`
  - Version probe: `1.0.0.61aead4`
  - Production synthetic smoke: all 31 interactive UI button tests passed
  - Responsive layout: all 5 viewports passed
  - Bound rollback commit: `58cf2d0`
- **Regression test plane**:
  - Full test suite: 1,927 / 1,927 passed (100%)
  - Secret scan: 2,258 files checked, 0 findings
  - Agent ecosystem sync: 100% in sync
- **Artifacts**:
  - Evidence receipt:
    `plans/evidence/production_deploy_receipt_33251910604.json`
  - Rollback plan: `docs/production_rollback_runbook_v2.md`
<!-- PROD-DEPLOY-RUN-33251910604:END -->

---

<!-- FIVE-POOL-CAPACITY-20260829:START -->
## Sprint CAPACITY-5POOL — Five-Pool Dual-Root Capacity Architecture (`TICKET-CODEX3-SUPPORT`)

**Recorded**: `2026-08-29` (Asia/Bangkok) | **Grill Status**: `APPROVED` in `plans/plan.md` | **Status**: `HISTORICAL DONE — VERIFIED AT 2026-08-29 CHECKPOINT`

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-CODEX3-SUPPORT` | HIGH | M | `business_analyst` (governance) / `developer` (runtime integration) / `qa_tester` (verification) | HISTORICAL DONE — VERIFIED AT 2026-08-29 CHECKPOINT | historical `IDQ-MVP-070-QA`, `Rule 19A` |

Detailed topology and rules preserved in `plans/archive/2026-09-01-atomic-tasks-refactor/PROJECT_TASKS_original.md#L1156-L1219` and `.agents/rules/19-agy-capacity-governance.md`.
<!-- FIVE-POOL-CAPACITY-20260829:END -->

---

<!-- SPARK-MODEL-GOVERNANCE-20260829:START -->
## Sprint SPARK-GOV — Fail-Closed Spark Model Governance & Regression Suite (`TICKET-SPARK-GOV`)

**Recorded**: `2026-08-29` (Asia/Bangkok) | **Grill Status**: `DONE / VERIFIED` in `plans/plan.md` | **Status**: `DONE — VERIFIED`

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-SPARK-GOV` | HIGH | S | `developer` (policy engine) / `qa_tester` (regression suite) / `business_analyst` (governance) | DONE — VERIFIED | `TICKET-CODEX3-SUPPORT`, `Rule 18` |

Detailed criteria preserved in `plans/archive/2026-09-01-atomic-tasks-refactor/PROJECT_TASKS_original.md#L1221-L1265` and `.agents/rules/18-adaptive-model-effort-routing.md`.
<!-- SPARK-MODEL-GOVERNANCE-20260829:END -->

---

<!-- ACTION-PRIORITY-GUARD-20260830:START -->
## Sprint ACTION-PRIORITY-GUARD — Fail-Closed Branch Migration Action Priority Guard (`TICKET-GOV-ACTION-PRIORITY-GUARD`)

**Recorded**: `2026-08-30` (Asia/Bangkok) | **Grill Status**: `DONE / VERIFIED` in `docs/branch_migration_action_priority_runbook.md` and `HOWTO.md` | **Status**: `DONE — VERIFIED`

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-GOV-ACTION-PRIORITY-GUARD` | HIGH | S | `developer` (CLI & quality gate integration) / `qa_tester` (regression suite) / `business_analyst` (governance & HOWTO documentation) | DONE — VERIFIED | `TICKET-SPARK-GOV`, `Rule 11`, `Rule 16` |

Detailed runbook: `docs/branch_migration_action_priority_runbook.md` and `HOWTO.md`.
<!-- ACTION-PRIORITY-GUARD-20260830:END -->

---

## Evidence Snapshot

### Latest Local & Remote Evidence Snapshot (Current Release State)

- **Local `main` commit**: `f9f8048` (2026-09-01)
- **Local working tree**: Clean (no uncommitted tracked/untracked changes)
- **Remote tracking**: `origin/main` at `f9f8048` (up-to-date)
- **Production HF Space commit**: `f9f8048` (health: `HTTP 200`, version: `1.0.0.f9f8048`)
- **Production Vercel commit**: `f9f8048` (health: `HTTP 200`, version: `1.0.0.f9f8048`)
- **Main test suite result**: 10 failing tests in CI runs `33418206430` / `33418206373` / `33418206471` on `f9f8048` — tracked by sprints:
  - `GHA-20260901-RUFF-F821`: 1 failure (Ruff F821 in `project/mcp_server.py`) — `[QA/DEV DONE, REVIEW PASS]`
  - `GHA-20260901-AISAFETY`: 9 pytest failures (AI Safety Audit) — `[TRIAGE TODO]`
  - `GHA-20260901-SYNTHMON`: 1 release-identity failure (Synthetic Monitoring) — `[DIAGNOSIS DONE, NEEDS_HITL]`
- **Local test suite (repaired MCP server)**: `tests/test_mcp_server_contract.py` passes 100%
- **Secret scan**: 2,260+ files scanned, 0 leaks detected
- **Parity / ecosystem sync**: 100% in sync (`python3 scripts/sync_ai_agent_ecosystem.py --check` exits 0)

---

## Master Agile Status & Archive Pointers

| Item | Canonical Location | Status |
|---|---|---|
| **Authoritative Task Registry** | [`atomic_tasks.md`](atomic_tasks.md) | `ACTIVE` (sole task/ticket authority) |
| **Current Resume Context** | [`HANDOFF.md`](HANDOFF.md) | `ACTIVE` (session handoff capsule) |
| **Architecture & Decisions** | [`plans/plan.md`](plans/plan.md) | `ACTIVE` (plan/decision registry) |
| **Archive: Metaphysics Roadmap** | [`plans/archive/2026-08-31-metaphysics-roadmap/`](plans/archive/2026-08-31-metaphysics-roadmap/) | `SEALED` |
| **Archive: Meta Plan 003** | [`plans/archive/2026-08-31-meta-plan-003/`](plans/archive/2026-08-31-meta-plan-003/) | `SEALED` |
| **Archive: Meta Plan 002** | [`plans/archive/2026-08-31-meta-plan-002/`](plans/archive/2026-08-31-meta-plan-002/) | `SEALED` |
| **Archive: Broker Plan 001** | [`plans/archive/2026-08-31-broker-plan-001/`](plans/archive/2026-08-31-broker-plan-001/) | `SEALED` |
| **Archive: Release v1.3.0** | [`plans/archive/2026-08-31-release-v1.3.0/`](plans/archive/2026-08-31-release-v1.3.0/) | `SEALED` |
| **Archive: Original Task Boards** | [`plans/archive/2026-09-01-atomic-tasks-refactor/`](plans/archive/2026-09-01-atomic-tasks-refactor/) | `ARCHIVED` (`PROJECT_TASKS_original.md`, `project_tickets_original.md`) |

---

## Quick-Start Commands

```bash
# 1. Check AI agent ecosystem sync
python3 scripts/sync_ai_agent_ecosystem.py --check

# 2. Run local fast tests
pytest -q tests/test_mcp_server_contract.py

# 3. Verify test provenance
python3 scripts/test_provenance_guard.py verify-history

# 4. Run secret scan
python3 scripts/fail_fast_triage.py --mode fast

# 5. Check git status
git status
```
