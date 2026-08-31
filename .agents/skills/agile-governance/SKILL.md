---
name: agile-governance
description: Govern atomic agile tickets, multi-lane capacity leases, and safe concurrent admission.
---

# Agile Governance Skill

Use this skill for atomic ticket lifecycle transitions, broker capacity admission,
and fail-closed execution gating. Rule 21 is the authoritative policy.

## Broker Admission and Capacity Truth

1. **Distinguish Capacity Truth Categories**:
   - *Theoretical capacity*: Total ceiling defined in configuration.
   - *Policy-admitted capacity*: Lanes passing quota band, account isolation, and circuit gates.
   - *Runtime-proven capacity*: Executable lanes backed by live execution receipts.
   - *Safe executable cap*: `min(theoretical, policy_admitted, runtime_proven, host_guard, tickets)`.

2. **Alias Pool Isolation**:
   - Each alias represents independent pools; do no aggregation, borrowing, or cross-pool leasing.
   - AGY per alias cap 3 is a hard safety upper bound, never an availability claim.
   - Mark an alias unknown without fresh quota proof and isolation proof.
   - Fail closed immediately on stale, unverified, or conflicting capacity state.

## Canonical Six-State Lifecycle

Manage ticket state transitions strictly across the six canonical states:
- `TODO`: Intake state. Unassigned or awaiting refinement.
- `READY`: Definition of ready satisfied and admitted to safe capacity.
- `DOING`: Exactly one editor actively working within bounded writable paths.
- `BLOCKED`: Dependency unresolved, quota unavailable, or circuit breaker open.
- `NEEDS_HITL`: Operator decision, authorization escalation, or irreconcilable state.
- `DONE`: Definition of done fully satisfied and independently verified.

Direct state skips (e.g. `TODO` to `DONE`) are prohibited.

## Strict Gate Enforcement

### Definition of Ready (DoR) Gate
Before transitioning to `READY` or `DOING`, verify all 9 prerequisites:
1. Test baseline verified (signed provenance reference).
2. One editor per resource ownership (single editor per file/ticket).
3. Dependency tickets verified in `DONE` status.
4. Quota band verified as healthy or constrained.
5. Circuit breaker verified closed on the target broker pool.
6. File permissions verified (0700 home directory, 0500 binary/wrapper).
7. Valid broker capacity lease ID obtained.
8. Valid Rule 18 model/effort decision digest.
9. Exact evidence artifact path defined.

### Definition of Done (DoD) Gate
Before transitioning to `DONE`, verify all 6 requirements:
1. Complete typed `WorkResult` with all 7 mandatory sections:
   - `Status`: Final resolution status.
   - `Scope owned`: Declared bounded files.
   - `Evidence`: Exact test results and provenance hashes.
   - `Findings`: Technical summary of changes.
   - `Changed files`: Exact list of modified files.
   - `Residual risk`: Identified remaining risks or edge cases.
   - `Recommended next action`: Clear next step for parent or dependent tickets.
2. Independent QA verdict `PASS`.
3. Independent code review verdict `PASS`.
4. Rollback verification confirmed.
5. Capacity classification explicit (theoretical vs policy-admitted vs runtime-proven).
6. Zero out-of-bounds file modifications outside owned scope.

## One-Editor Ownership & Collision Check

- Verify disjoint writable file sets for every active `DOING` ticket.
- If a candidate ticket shares a writable path with any active `DOING` ticket, hold candidate in `READY` or `BLOCKED`.
- Release ownership reservation immediately upon terminal state (`DONE`, `BLOCKED`, `NEEDS_HITL`).

## Capacity Exception Handling

- Prohibit exploratory probes, speculative tasks, and no fake full capacity busywork.
- When an execution slot is available but no safe critical-path lane exists, emit typed capacity exception:
  `CAPACITY_EXCEPTION: NO_SAFE_CRITICAL_PATH_LANE` (or `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE`).
- Include snapshot digest, dependency inventory, and rejected candidate reason codes.
- Leave the slot idle until replanning or dependency resolution occurs.

## Safety and Reporting Boundaries

- Logging format strictly enforces ASCII tags: `[INFO]`, `[OK]`, `[WARNING]`, `[ERROR]`.
- No credentials, tokens, or credential-store data in governance artifacts.
