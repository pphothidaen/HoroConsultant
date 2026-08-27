# Rule 11: Delegate-First Orchestrator and Sub-Agent Governance

## Purpose

Delegate meaningful mutation, QA, review, and operations by default. The `orchestrator`
owns intake, scheduling, bounded read-only coordination, synthesis, updates,
conflict resolution, and final decisions.

## Default Boundary and Role Selection

Use the narrowest specialist whose primary responsibility matches the lane. Root
may answer a trivial no-tool question or perform bounded read-only orchestration.
These exceptions do not authorize root implementation, test mutation, review
closure, deployment, publishing, or another operation. Do not delegate merely
to restate an answer the root already has.

## Eligibility and Scheduling

Before executable spawn, apply Rule 18 and record its `DispatchDecision`; static
role hints are not proof. Exclude tickets not `TODO`/`READY`, lacking valid
`Severity`/`Work Effort`, or having unmet dependencies, explicit blockers,
ownership conflicts, quota/HITL failure, or invalid Rule 18 decisions. Missing
metadata or duplicate IDs fail `BLOCKED: INVALID_SCHEDULING_METADATA`.

Sort eligible tickets by `(-severity_rank, work_effort_rank, ticket_id_ascii)`:
`CRITICAL > HIGH > MEDIUM > LOW`, then `XS < S < M < L < XL`, then ASCII ID.
`Work Effort` is delivery size, not model effort; models never change order.
Historical `Priority` is evidence only. Do not preempt `DOING` work.

## Full-Capacity Invariant and Dispatcher Loop

While actionable session work remains, the orchestrator MUST continuously
recompute live capacity and keep every available collaboration slot assigned to
a useful, independent, evidence-bearing lane. Apply this dispatcher loop:
`observe capacity -> inventory useful work -> decompose -> reserve ownership ->
dispatch -> collect -> immediately refill`. Repeat until terminal session
completion; a lane ending is a scheduling event, not permission to leave its
slot vacant.

Decompose current tickets into the smallest coherent bounded lanes without
artificial fragmentation. Permit one editor per file/module; reserve ownership,
recompute Rule 11 and capacity, then dispatch the next lane. When primary
implementation is dependency-blocked, form useful non-mutating fallback tickets
from independent verification, QA baseline, risk/threat review,
documentation/evidence reconciliation, lifecycle/process audit, test design,
or dependency-resolution analysis. Each fallback lane requires its own ticket,
scope/ownership, boundaries, evidence, acceptance criteria, and stop condition.

Full capacity never permits duplicate or redundant work, concurrent same-file
editors, stale or fake busywork, bypassed dependencies, daemons/background
quota burn, unauthorized provider/quota use, or false completion. If exhaustive
decomposition finds no useful safe lane for a free slot, emit
`CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE` with capacity snapshot, ticket and
dependency inventory, rejected candidates/reasons, and quota/HITL evidence;
immediately escalate to orchestrator replanning. This is a blocking invariant
violation requiring action, never ordinary or silently allowed idle capacity.

### Governed short-fallback lane

When a source editor is active and final QA is waiting for source freeze, an
otherwise idle slot may take a short fallback only when its ticket is
`TODO`/`READY`, every dependency and normal Rule 11 gate passes, and ownership
is disjoint from every active source and documentation editor. The lane must be
read-only, evidence-bearing, independent of the pending freeze, naturally
terminating, non-daemon/non-background, leased for `1..600` seconds, and use
`preemption_policy: NEVER`. The current Stage A structural guard applies an
effective maximum of `300` seconds; a trusted configured limit may be stricter
but no scan, prompt, or caller field may raise either that effective limit or
the normative `600`-second ceiling. Stage A requires provider mode `NONE`.

A fallback never preempts or cancels running work. Once source is frozen and QA
is eligible, keep an already-running fallback until its bounded lease ends. If
a slot is idle, select QA before any new fallback. If every slot is busy, record
QA as next-slot priority; the next completion/refill must dispatch QA before
another fallback. When no safe candidate exists, the capacity exception must
list the exact rejected ticket IDs and typed reason codes, bound to the current
snapshot digest; never invent work to suppress the exception.

### Governed Stage A structural boundary

Current `full-capacity-governance-v2` Stage A is a structural validator and
decision recorder only. It MUST derive Rule 11 order, Rule 18 validity, exact
rejection reasons, QA priority, and authorization bindings from a closed input
record. The record contains exactly the capacity, complete ticket inventory,
dependency/blocker/HITL/quota state, ownership reservations, normalized Rule 18
decision and policy bindings, execution window, short-lane controls, alias
evaluations, and source-to-QA handoff needed for that computation. Missing,
duplicate, unknown, omitted, or extra controls fail closed. Caller declarations
such as `rule11_passed`, `rule18_passed`, `dependencies_passed`, hashes, model
labels, or proof booleans never substitute for recomputation.

The Stage A comparator MUST select the highest-ranked eligible ticket before a
lower-severity fallback. Rejection and alias reason codes MUST be derived from
the same normalized snapshot and match it exactly; contradictory reasons fail
closed. Authorization structure MUST bind its authorization ID and evidence
digest to provider, alias, session, ticket, role, ownership digest, normalized
Rule 18 decision digest, policy version, and policy digest. Such internal
binding remains `STRUCTURALLY_BOUND_NOT_PROVEN`, never provider proof.

Execution windows require exact start, deadline, lease, natural-exit-only, and
never-preempt fields. Stage A checks their internal duration and the effective
`300`-second cap, but caller timestamps do not prove trusted wall-clock or
natural-exit enforcement. Lifecycle continuity MUST use a regular non-symlink
SQLite ledger in an owner-only local directory (`0700`) and file (`0600`),
transactionally chain exact `PRE` and `POST` records, and reject replay, fork,
stale sequence, session mismatch, or unbound tool input/result digests. This
ledger does not establish native interception or resist the same OS principal.

At every checkpoint, evaluate exactly `agy1` and `agy2`; both entries say
`EVALUATED`. All feature flags currently remain `false`; every AGY alias is
`NOT_ELIGIBLE`, `dispatched: false`, and receipt-free, with exact derived
per-alias reasons. A local token, Result Contract binding, feature flag,
repository hook, or static configuration can never make an AGY alias eligible
for a native `spawn_agent`. Every native spawn remains under the owner gate;
only a future host-native pre-spawn API/receipt, trusted effective-provider
telemetry, fresh exact owner decision, and independent review can be evaluated
for a later rule revision. Any module-bounded source roles
(`CORE_SOURCE_EDITOR`, `API_SOURCE_EDITOR`, `UI_SOURCE_EDITOR`, `TEST_SOURCE_EDITOR`)
are proposed only and grant no concurrency permission. Missing, conflicting,
or unauthorized dispatches fail closed.

Resolve the event tool identity before deciding whether an envelope is
required. Normalize execution-family names case-insensitively to canonical
`Task`, `Bash`, `run_command`, `shell`, or `terminal*`. Recognize both the
top-level `tool_name`/`tool_input` form and the native
`toolCall.name`/`toolCall.args` form, including a nested-only event. If both
forms exist, their normalized names and canonical JSON payloads must be exactly
equivalent; a partial, malformed, or contradictory pair fails
`CAPACITY_TOOL_ENVELOPE_CONFLICT`. Apply the same exact canonical-equivalence
rule to Post responses supplied in both `tool_response` and `toolResult`.

Every `Pre` and `Post` event in a normalized execution family requires the
exact closed governance envelope. Command text and path are not an allowlist:
pathless commands and apparently benign `pwd`, `echo`, `git status`, or
absolute binary paths remain governed shell events. A missing envelope fails
`CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED`; an unknown field, wrapper
translation, representation conflict, or normalized-name mismatch fails
closed. Only unrelated non-execution tools such as `Read`, `Grep`, or `Edit`
may remain outside this capacity envelope boundary; their normal ownership,
mutation, and authorization rules still apply. Claude registration must contain
the full-capacity guard exactly once under matcher `.*` in both `PreToolUse` and
`PostToolUse`, while preserving every other registered hook.

Even a structurally valid governed shell envelope cannot authorize actual
dispatch during Stage A. Reject that transition with
`AUTHORITATIVE_SNAPSHOT_NOT_PROVEN` until Stage C ticket `DSG-009A` proves the
authoritative scheduler/native pre-spawn boundary. Least-recently-served
metadata cannot select an alias in Stage A or change Rule 11 order.

Keep authoritative-snapshot completeness, native/pre-spawn interception,
provider runtime/provenance, actual dispatch, world state, trusted wall clock,
and natural exit `NOT_PROVEN`. A requested `gpt-5.6-sol`/`ultra` or `max` label
is advisory intent, not effective model/effort/account/quota/receipt proof.
Stage C ticket `DSG-009A` owns the authoritative scheduler and native pre-spawn
boundary. Only after it closes may Stage D ticket `DSG-009B`, with a trusted
provider verifier and fresh exact HITL authorization, enable positive AGY or
provider dispatch. Structural hooks never claim to be that scheduler or
verifier.

## Delegation Contract

Every lane must state objective, ownership, boundaries/exclusions, expected
evidence, and stop condition (`DONE`, `BLOCKED`, or `NEEDS_HITL`), and include:

```text
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

No concurrent editors may own the same file/module; make others read-only.
Never bypass quota, HITL, dependency, ownership, or external-action gates.
Sub-agents never print secrets; unexpected disclosure requires rotation/HITL.

Registered specialists are on-demand, not daemon/background quota consumers.
Spawn only for a selected ticket; bind parent/session/ticket, ownership,
timeout/lease, and receipt. Respect concurrency, clean terminal children, detect
orphan/zombie state, and return a typed quota-safe stop without blind retry.

## Monitoring and Results

Report active lanes, ownership, waits/blockers, and `active/available` slots.
After every spawn, completion, failure, cancellation, or capacity change,
re-enter the dispatcher loop before other synthesis. Poll meaningful changes
and merge verified evidence, not seniority or majority.

Each result must contain:

- `Status`: `DONE`, `BLOCKED`, or `NEEDS_HITL`
- `Scope owned`
- `Evidence`
- `Findings`
- `Changed files`
- `Residual risk`
- `Recommended next action`

## Completion Gate

Close only when evidence meets acceptance, changes stay within ownership, and
receipt gates pass. Parent closure requires evidenced `DONE` or terminal
`BLOCKED`/`NEEDS_HITL` with next action; local checks never replace live gates.
A capacity exception is never `DONE`; keep replanning until a safe lane is
dispatched or a separately evidenced terminal blocker/HITL condition ends work.
