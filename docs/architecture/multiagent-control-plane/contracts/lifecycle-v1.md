# Lifecycle Contract v1

## Status, Scope, and Normative Language

| Field | Normative value |
|---|---|
| Contract ID | `sdlc.control-plane.lifecycle` |
| Contract version | `1` |
| Lifecycle status | `NORMATIVE` |
| Ticket | `MAREF-010-LIFECYCLE-CONTRACT` |
| Authority scope | Canonical execution, approval, lease/fence, and effect-Saga lifecycle semantics |
| Release authority | None; this contract does not authorize implementation, migration, cutover, deployment, publishing, or production mutation |

This contract is the lifecycle-v1 normative input to the later C1 contracts. A
change to a state, transition, command, event, effect class, rejection, or
authority rule requires a separately authorized contract version and, when it
changes a C0 decision, a narrow superseding ADR with human approval.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, and **MAY** are normative. `ABSENT` in a table means
that the aggregate does not exist; it is not a stored state.

The tables in this document are closed catalogs. Only listed states,
transitions, commands, events, effect stages/classes, rejections, and
compatibility mappings are valid in lifecycle-v1. A reducer MUST reject an
unlisted value or source/target pair. A handler MUST NOT infer an intermediate
or terminal transition. Each state change requires the listed command and
event or ordered event set.

Lifecycle-v1 governs:

- execution, approval, lease/fence, and durable effect-Saga state;
- canonical identities, versions, attempts, fences, and authority epochs;
- command idempotency, preconditions, rejection results, and atomic writes;
- eventual-read and notification boundaries;
- compatibility ingestion of Result Contract v2 as evidence only; and
- reachability, immutable terminal states, compensation, and linked
  remediation.

## Canonical Identities, Versions, and Authority

The Authority Plane is the sole canonical writer. PostgreSQL and the sole
ControlPlane command handler own accepted transitions. SQLite WAL MAY preserve
the same observable semantics for local single-host development, but it MUST
NOT be production or multi-host authority.

| Field or concept | Applies to | Normative authority and invariant |
|---|---|---|
| `tenant_id` | Every command, event, aggregate, grant, lease, attempt, effect, and receipt | Supplied by authenticated Authority Plane context. The literal `system` is REQUIRED until authenticated tenant identity exists. An adapter MUST NOT invent or substitute it. |
| `run_id` | Every lifecycle command and event | Canonical run identity validated by the Authority Plane and treated as opaque by adapters. |
| `task_id` | Every lifecycle command and event | Canonical task identity within `tenant_id` and `run_id`. The execution aggregate key is `(tenant_id, run_id, task_id)`. |
| `predecessor_run_id`, `predecessor_task_id` | Linked remediation execution | Both are REQUIRED when a new execution remediates a terminal execution; they MUST identify a terminal execution in the same tenant. They are absent for an ordinary new execution. |
| `effect_id` | Durable E1-E4 command, lease, event, and receipt | Exact effect identity within the execution. It MUST NOT be derived from a provider job or stream identifier. |
| `approval_id` | Approval aggregate and each approval-gated command | Authority-issued identity bound to tenant/run/task/effect/action/scope/session/class. |
| `lease_id` | Lease aggregate and each leased command/result | Authority-issued identity bound to tenant/run/task/resource/stage and the database-issued attempt/fence. |
| `command_id` | Every lifecycle mutation command | Required idempotency identity within the tenant. It is recorded with the normalized command digest and result. |
| `expected_version` | Every lifecycle mutation command | Non-negative CAS value for the primary target aggregate. `0` asserts aggregate absence; an existing aggregate begins at version `1`. |
| `aggregate_version` | Every aggregate event and projection | Database-owned, strictly increasing by one for each event applied to that aggregate. A command that emits two events for one aggregate advances it twice. |
| `authority_epoch` | Every command, event, projection, read, receipt, and outbox item | Monotonic database-owned writer epoch. A command MUST equal the current epoch. A provider, client, stale projection, or legacy writer cannot choose it. |
| `attempt_no` | Execution work, worker result, E2-E4 effect, and relevant lease/receipt | Positive, monotonic per execution, and allocated only by the database during execution-lease acquisition. A client or worker MUST NOT choose it. Resuming a nonterminal execution retains the current attempt. |
| `fencing_token` | Active lease and every worker result/effect proposal under that lease | Monotonic database allocation for the leased resource. Only the current ACTIVE token may mutate canonical state. |
| `event_id`, `sequence` | Every canonical lifecycle event | Database-owned immutable event identity and monotonic stream sequence. They are not notification-transport sequence authority. |
| `catalog`, `catalog_version` | Every canonical lifecycle event | REQUIRED values are `sdlc.control-plane.lifecycle` and `1`. Frozen v3 domain events use their own catalog and namespace. |
| `causation_id`, `correlation_id` | Every durable command/event chain | Canonical correlation references. They do not grant authority. |
| `platform_metadata.<namespace>` | Command/event/receipt correlation only | Sanitized, namespaced, opaque adapter/provider values. Reducers, approvals, lease/capacity allocation, fencing, idempotency, attempts, sequence, and authority decisions MUST NOT read it. |

The normalized command digest covers every canonical command field and the
sanitized opaque correlation metadata, while excluding transport delivery
headers. Reusing a `command_id` with the same digest MUST return the recorded
result without new events, projection writes, or outbox rows. Reusing it with a
different digest MUST reject with `COMMAND_ID_REUSE_MISMATCH`.

Every durably accepted mutation command MUST, in one Authority Plane database
transaction, record the command result, append its canonical event or ordered
events, update every affected projection, and enqueue the corresponding outbox
items. `202` MUST be returned only after that commit. A transaction failure
commits none of those records.

## Global Lifecycle Invariants

| ID | Normative invariant |
|---|---|
| `G01` | Execution, Approval, and Lease are orthogonal machines. No state in one machine implies a state or authorization in another. |
| `G02` | The Authority Plane and sole ControlPlane handler are the only transition writer. Workers, providers, browsers, transports, projections, notifications, and compatibility adapters submit commands, proposals, or evidence only. |
| `G03` | Every mutation command binds `command_id`, `expected_version`, current `authority_epoch`, and exact `tenant_id`/`run_id`/`task_id`; effect and leased commands additionally bind their canonical effect/approval/lease/attempt/fence identities. |
| `G04` | Identical command duplication returns the recorded result. Non-identical `command_id` reuse rejects. Duplication MUST NOT repeat an effect or append lifecycle/outbox records. |
| `G05` | The database assigns `attempt_no`, `fencing_token`, aggregate versions, event sequence, timestamps used for lease policy, and authority epoch. |
| `G06` | Event append, projection update, command-result recording, and outbox enqueue are atomic. Notification delivery occurs only after commit. |
| `G07` | `SUCCEEDED`, `FAILED`, and `BLOCKED` are the complete execution terminal set. A terminal execution has no outgoing transition. |
| `G08` | Failure with a committed effect that requires correction MUST enter `COMPENSATING`; no terminal transition is permitted until every required correction has a known successful receipt. Successful compensation is durably recorded before execution becomes `FAILED`. |
| `G09` | Compensation failure moves execution to `NEEDS_HITL`. An unknown compensation outcome moves it to `RECONCILING`. |
| `G10` | An unknown external outcome MUST be durably recorded and reconciled. It MUST NOT be retried merely because delivery, connection, or provider status is uncertain. |
| `G11` | Terminal remediation creates a new execution linked to the terminal predecessor. It receives new commands, approvals, leases/fences, effects, and receipts. |
| `G12` | E2-E4 require the exact approval plus an ACTIVE lease with the current database attempt and fence. When execution or approval is `NEEDS_HITL`, E2-E4 are frozen. |
| `G13` | Unknown, unclassified, ambiguous, or semantically mismatched effect stage/class/approval/outcome fails closed into a recorded rejection and the exact `NEEDS_HITL` path in the closed rejection-to-HITL matrix; it MUST NOT be assigned a lower class. A deterministic invalid credential, identity, scope, session, version, or ordinary validation mismatch with no unresolved canonical decision is rejection-only and MUST NOT invent a state transition. |
| `G14` | Reviewer identity, grant issuer, tenant, session, attempt, fence, and authority MUST be server-derived or verified. Self-approval is prohibited. |
| `G15` | There is no `force` or equivalent bypass command. Automatic/background training and any action requesting a bypass remain prohibited. |
| `G16` | Compensation appends a linked corrective action, generation, pointer, cancel, or supersession receipt and preserves history. Deleting a record is not compensation. |
| `G17` | Lease policy is provisional: TTL `120` seconds, renewal no later than `40` seconds after acquisition or the last renewal, database clock only, and zero grace after database expiry. |
| `G18` | Stale projections, caches, notification cursors, provider IDs, and provider reconnects MUST NOT authorize or cause transitions. |
| `G19` | Under loss of Authority: no mutation, no new lease, no new approval, and no blind retry. Existing work may finish only through current canonical version/grant/attempt/fence checks. |
| `G20` | Result Contract v2 and historical receipts are compatibility evidence. Their statuses, claims, identifiers, and receipts do not become canonical state or authority. |
| `G21` | The frozen v3 event catalog and its history remain separate and unchanged; lifecycle-v1 events cannot validate or replay as v3 events. |
| `G22` | Raw provider streams MUST NOT be persisted, copied into events/outbox/projections, or repeated in evidence. Only sanitized metadata, digests, counts, and approved references may be retained. |

## Execution State Machine

The execution aggregate is absent before `X01`. Terminality in this table is
authoritative and applies only to the execution machine.

| State | Terminal | Closed definition |
|---|---:|---|
| `PLANNED` | No | Canonical execution intent exists; readiness evidence is incomplete or not yet declared. |
| `READY` | No | Planning prerequisites are recorded. Approval and Lease remain independent and are checked when their protected action is requested. |
| `RUNNING` | No | The database-issued current attempt has started under its ACTIVE execution lease and fence. |
| `NEEDS_HITL` | No | A human decision is required. E2-E4 are frozen; only E0 and the bounded E1 audit/HITL request remain eligible. |
| `RECONCILING` | No | At least one external or compensation outcome is unknown and is being resolved from durable evidence without repeating the effect. |
| `COMPENSATING` | No | A failure path has committed effects and linked corrective effects are in progress. |
| `SUCCEEDED` | Yes | Required work and effect outcomes are known successful, with no pending, unknown, or required compensation. |
| `FAILED` | Yes | Work failed with no required compensation, or all required compensation was recorded first. |
| `BLOCKED` | Yes | Work cannot proceed under current authority. Any acknowledged residual external state is preserved and remediation requires a new linked execution. |

| Transition | Source | Target | Command | Canonical event or ordered events | Additional closed precondition |
|---|---|---|---|---|---|
| `X01` | `ABSENT` | `PLANNED` | `execution.plan` | `execution.planned.v1` | `expected_version=0`; identity is unused; a remediation link, when present, names a terminal predecessor. |
| `X02` | `PLANNED` | `READY` | `execution.mark_ready` | `execution.ready.v1` | Planning prerequisites and exact classification evidence are recorded. |
| `X03` | `PLANNED` | `NEEDS_HITL` | `execution.require_hitl` | `execution.hitl_required.v1` | A typed unresolved decision is recorded. |
| `X04` | `PLANNED` | `BLOCKED` | `execution.block` | `execution.blocked.v1` | Typed blocker and authority decision are recorded; no attempt or effect exists. |
| `X05` | `READY` | `RUNNING` | `execution.start` | `execution.running.v1` | Current ACTIVE execution lease, database attempt, and fence match. |
| `X06` | `READY` | `NEEDS_HITL` | `execution.require_hitl` | `execution.hitl_required.v1` | A typed unresolved decision is recorded. |
| `X07` | `READY` | `BLOCKED` | `execution.block` | `execution.blocked.v1` | Typed blocker is recorded; no committed or unknown effect exists. |
| `X08` | `RUNNING` | `NEEDS_HITL` | `execution.require_hitl` | `execution.hitl_required.v1` | A typed human decision is required; current attempt is retained. |
| `X09` | `RUNNING` | `RECONCILING` | `effect.record_unknown` | `effect.outcome_unknown.v1` (`F05`), then `execution.reconciling.v1` | Unknown external outcome and its durable evidence reference are recorded. |
| `X10` | `RUNNING` | `COMPENSATING` | `effect.begin_compensation` | `effect.compensating.v1` (`F06` or `F07`), then `execution.compensating.v1` | At least one committed effect requires compensation; the linked compensation action satisfies its E/P gates. |
| `X11` | `RUNNING` | `SUCCEEDED` | `execution.succeed` | `execution.succeeded.v1` | All required outcomes are known; no pending, unknown, failed-required, or uncompensated effect exists. |
| `X12` | `RUNNING` | `FAILED` | `execution.fail` | `execution.failed.v1` | No committed effect requires compensation and no outcome is unknown. |
| `X13` | `RUNNING` | `BLOCKED` | `execution.block` | `execution.blocked.v1` | No unknown outcome or pending/failed required compensation exists; each committed effect is either compensation-free or has a known successful corrective receipt, and residual state has explicit owner acknowledgement. |
| `X14` | `NEEDS_HITL` | `READY` | `execution.resolve_hitl` | `execution.ready.v1` | Decision is durably resolved; no attempt has started; other gates remain independent. |
| `X15` | `NEEDS_HITL` | `RUNNING` | `execution.resolve_hitl` | `execution.running.v1` | Decision is durably resolved; current attempt/lease/fence remain valid. |
| `X16` | `NEEDS_HITL` | `RECONCILING` | `execution.resolve_hitl` | `execution.reconciling.v1` | The authorized resolution is reconciliation, not effect repetition. |
| `X17` | `NEEDS_HITL` | `COMPENSATING` | `effect.begin_compensation` | `effect.compensating.v1` (`F06` or `F07`), then `execution.compensating.v1` | The authorized resolution is a newly linked compensation effect with all required gates. |
| `X18` | `NEEDS_HITL` | `FAILED` | `execution.fail` | `execution.failed.v1` | A current attempt exists; no compensation is required or required compensation is already recorded; no outcome is unknown. |
| `X19` | `NEEDS_HITL` | `BLOCKED` | `execution.block` | `execution.blocked.v1` | Explicit owner decision records the blocker and residual-state disposition; no outcome remains unknown. |
| `X20` | `RECONCILING` | `RUNNING` | `effect.reconcile` | `effect.succeeded.v1` (`F08`), then `execution.running.v1` | Reconciliation proves primary success without reinvocation and work remains. |
| `X21` | `RECONCILING` | `COMPENSATING` | `effect.reconcile` | `effect.compensating.v1` (`F10`), then `execution.compensating.v1` | Reconciliation proves committed state that requires a linked corrective effect. |
| `X22` | `RECONCILING` | `SUCCEEDED` | `effect.reconcile` | `effect.succeeded.v1` (`F08`), then `execution.succeeded.v1` | Reconciliation proves primary success and all completion preconditions of `X11`. |
| `X23` | `RECONCILING` | `FAILED` | `effect.reconcile` | `effect.failed.v1` (`F09`) or `effect.compensated.v1` (`F12`), then `execution.failed.v1` | `F09` proves primary failure with no required compensation; `F12` proves corrective success. No outcome remains unknown. |
| `X24` | `RECONCILING` | `RECONCILING` | `effect.reconcile` | `effect.reconciliation_observed.v1` (`F11`) | Outcome remains unknown; new evidence/cursor is recorded and no effect is repeated. |
| `X25` | `RECONCILING` | `NEEDS_HITL` | `effect.reconcile` | `effect.compensation_failed.v1` (`F13`) or `effect.reconciliation_observed.v1` (`F11`), then `execution.hitl_required.v1` | `F13` proves corrective failure; `F11` is used only when evidence still cannot resolve a typed human decision. Neither path repeats the effect. |
| `X26` | `COMPENSATING` | `FAILED` | `effect.record_compensated` | `effect.compensated.v1`, then `execution.failed.v1` | All required compensation receipts are committed in this transaction before terminal failure. |
| `X27` | `COMPENSATING` | `NEEDS_HITL` | `effect.record_compensation_failed` | `effect.compensation_failed.v1`, then `execution.hitl_required.v1` | Compensation outcome is known failure. |
| `X28` | `COMPENSATING` | `RECONCILING` | `effect.record_compensation_unknown` | `effect.outcome_unknown.v1`, then `execution.reconciling.v1` | Compensation outcome is unknown and binds `unknown_operation=COMPENSATION`. |

No execution transition exists outside `X01`-`X28`.

## Approval State Machine

Approval classification and scope are immutable for one `approval_id`.
Replacing or strengthening an approval creates a new aggregate; it never
reopens a closed approval or lowers the E/P class.

| State | Closed definition |
|---|---|
| `NOT_REQUIRED` | E0/P0 authenticated read capability was assessed; no durable effect approval is represented. |
| `PENDING` | An exact E1/P1 through E4/P4 approval request awaits a valid decision. |
| `NEEDS_HITL` | Classification, scope, session, ownership, billing, destructiveness, or another high-impact fact requires human resolution. |
| `APPROVED` | Exact grant is valid for its bound session/action/scope/class and has remaining use and time. This does not imply a lease or execution state. |
| `REJECTED` | Requested action was denied. No outgoing transition exists. |
| `REVOKED` | Issuer/owner authority invalidated the grant. No outgoing transition exists. |
| `EXPIRED` | Database time or canonical session termination ended validity. No outgoing transition exists. |
| `EXHAUSTED` | Atomic use count reached `max_uses`. No outgoing transition exists. |

| Transition | Source | Target | Command | Canonical event or ordered events | Additional closed precondition |
|---|---|---|---|---|---|
| `A01` | `ABSENT` | `NOT_REQUIRED` | `approval.assess_not_required` | `approval.not_required.v1` | Exact classification is E0/P0 and no durable mutation is requested. |
| `A02` | `ABSENT` | `PENDING` | `approval.request` | `approval.requested.v1` | Exact immutable E1/P1 through E4/P4 action/scope/session binding is complete. |
| `A03` | `ABSENT` | `NEEDS_HITL` | `approval.require_hitl` | `approval.hitl_required.v1` | Classification or a required binding is unknown or ambiguous. |
| `A04` | `PENDING` | `APPROVED` | `approval.grant` | `approval.granted.v1` | Server-derived issuer/reviewer; exact scope/session/action/class; unexpired; positive `max_uses`; no self-approval. |
| `A05` | `PENDING` | `NEEDS_HITL` | `approval.require_hitl` | `approval.hitl_required.v1` | A typed human decision is required. |
| `A06` | `PENDING` | `REJECTED` | `approval.reject` | `approval.rejected.v1` | Server-derived decision and reason are recorded. |
| `A07` | `PENDING` | `REVOKED` | `approval.revoke` | `approval.revoked.v1` | Authorized issuer/owner invalidates the request before decision. |
| `A08` | `PENDING` | `EXPIRED` | `approval.expire` | `approval.expired.v1` | Database time reached expiry or the canonical bound session ended. |
| `A09` | `NEEDS_HITL` | `APPROVED` | `approval.grant` | `approval.granted.v1` | Human resolution supplies every `A04` condition; P4 is fresh explicit owner HITL with no parent inheritance. |
| `A10` | `NEEDS_HITL` | `REJECTED` | `approval.reject` | `approval.rejected.v1` | Server-derived decision and reason are recorded. |
| `A11` | `NEEDS_HITL` | `REVOKED` | `approval.revoke` | `approval.revoked.v1` | Authorized issuer/owner invalidates the request. |
| `A12` | `NEEDS_HITL` | `EXPIRED` | `approval.expire` | `approval.expired.v1` | Database time reached expiry or the canonical bound session ended. |
| `A13` | `APPROVED` | `APPROVED` | `effect.submit` | `approval.use_consumed.v1` | Exact protected effect passes every gate; atomic use succeeds, validity remains, and `use_count < max_uses`; `F01` completes in the same transaction. |
| `A14` | `APPROVED` | `EXHAUSTED` | `effect.submit` | `approval.use_consumed.v1`, then `approval.exhausted.v1` | Exact protected effect passes every gate; atomic use makes `use_count = max_uses`; `F01` completes in the same transaction. |
| `A15` | `APPROVED` | `REVOKED` | `approval.revoke` | `approval.revoked.v1` | Authorized issuer/owner revokes before the next use. |
| `A16` | `APPROVED` | `EXPIRED` | `approval.expire` | `approval.expired.v1` | Database time reached expiry or the canonical bound session ended. |

`NOT_REQUIRED`, `REJECTED`, `REVOKED`, `EXPIRED`, and `EXHAUSTED` have no
outgoing approval transitions. No approval transition exists outside
`A01`-`A16`.

## Lease and Fencing State Machine

There is no lease aggregate or placeholder state before successful acquisition.
Each successor lease receives a new `lease_id` and a strictly greater
database-issued fencing token for the same resource.

| State | Terminal | Closed definition |
|---|---:|---|
| `ACTIVE` | No | Lease is current, database time is before `expires_at`, and its fencing token has not been superseded. |
| `RELEASED` | Yes | Holder explicitly relinquished the lease; its fence can only produce a rejection/audit event. |
| `EXPIRED` | Yes | Database time reached `expires_at`; zero grace applies and its fence can only produce a rejection/audit event. |
| `SUPERSEDED` | Yes | A successor lease owns a greater fence; the old fence can only produce a rejection/audit event. |

| Transition | Source | Target | Command | Canonical event or ordered events | Additional closed precondition |
|---|---|---|---|---|---|
| `L01` | `ABSENT` | `ACTIVE` | `lease.acquire` | `lease.acquired.v1` | Authority is available; exact tenant/run/task/resource/stage is bound; all capacity limits pass. DB allocates attempt/fence and sets `acquired_at=db_now`, `renew_by=db_now+40s`, `expires_at=db_now+120s`. |
| `L02` | `ACTIVE` | `ACTIVE` | `lease.renew` | `lease.renewed.v1` | Current holder/attempt/fence match; `db_now <= renew_by` and `db_now < expires_at`. DB sets new renewal time, `renew_by=db_now+40s`, and `expires_at=db_now+120s`. |
| `L03` | `ACTIVE` | `RELEASED` | `lease.release` | `lease.released.v1` | Current holder/attempt/fence match and database expiry has not occurred. |
| `L04` | `ACTIVE` | `EXPIRED` | `lease.expire` | `lease.expired.v1` | Authority observes `db_now >= expires_at`; client time is ignored. |
| `L05` | `ACTIVE` | `SUPERSEDED` | `lease.supersede` | Old `lease.superseded.v1`, then successor `lease.acquired.v1` | Same Authority Plane transaction closes the old lease, creates a distinct successor, and allocates a strictly greater fence. |

`RELEASED`, `EXPIRED`, and `SUPERSEDED` have no outgoing transitions. A new
lease is acquired as a new aggregate; no lease transition exists outside
`L01`-`L05`. Failure to renew by 40 seconds does not extend or replace the
recorded 120-second expiry, and a late renewal is rejected.

## Commands and Preconditions

The common preconditions in `G02`-`G06` apply to every row. A handler reads the
current authoritative aggregates and performs all related checks in the same
transaction; caller projections and metadata are not authority.

| Command | Permitted transition IDs | Command-specific preconditions and result |
|---|---|---|
| `execution.plan` | `X01` | Aggregate absent at version 0; exact identities unused; remediation link absent or identifies a same-tenant terminal predecessor. |
| `execution.mark_ready` | `X02` | Planning evidence/classification complete. Does not assert approval or lease. |
| `execution.start` | `X05` | ACTIVE execution lease owns the current DB attempt/fence; worker result binding is returned from authority. |
| `execution.require_hitl` | `X03`, `X06`, `X08` | Typed unresolved decision and reason; E2-E4 freeze is recorded. |
| `execution.resolve_hitl` | `X14`, `X15`, `X16` | Server-verified human resolution selects exactly one listed nonterminal target and all target preconditions pass. |
| `execution.succeed` | `X11` | Completion evidence is canonicalized; every effect is known and no compensation is pending or required. |
| `execution.fail` | `X12`, `X18` | Current attempt exists; no unknown outcome or committed uncompensated effect remains. |
| `execution.block` | `X04`, `X07`, `X13`, `X19` | Typed blocker; no unknown outcome or pending/failed required compensation; committed effects are compensation-free or have known successful corrective receipts; residual state has explicit acknowledgement when present. |
| `approval.assess_not_required` | `A01` | E0/P0 only; authenticated read capability; no durable effect. |
| `approval.request` | `A02`; rejection compound `A03` | Exact E1/P1-E4/P4 classification, session, action, object, scope digest, owner, expiry, and use limit are bound. Only the closed rejection-to-HITL row may use `A03`. |
| `approval.require_hitl` | `A03`, `A05` | Unknown/ambiguous classification or missing high-impact human decision; no downward default. |
| `approval.grant` | `A04`, `A09`; rejection compound `A05` | Issuer/reviewer are server-derived; grant is exact, unexpired, non-self-approved, and within authority; P4 is fresh owner HITL. Only the closed rejection-to-HITL row may use `A05`. |
| `approval.reject` | `A06`, `A10` | Authorized decision and typed reason. |
| `approval.revoke` | `A07`, `A11`, `A15` | Server verifies issuer/owner revocation authority and current session. |
| `approval.expire` | `A08`, `A12`, `A16` | Database clock or canonical session termination proves expiry. |
| `lease.acquire` | `L01` | No lease aggregate for the new ID; authority/capacity available; resource binding exact. Execution-lease acquisition allocates the next attempt and fence; effect-lease acquisition validates the current attempt and allocates its fence. |
| `lease.renew` | `L02` | ACTIVE and current holder/attempt/fence; DB renewal deadline and expiry checks pass. |
| `lease.release` | `L03` | ACTIVE and current holder/attempt/fence; release is durable before the worker stops claiming authority. |
| `lease.expire` | `L04` | Authority database clock has reached expiry. |
| `lease.supersede` | `L05` | ACTIVE old lease; exact successor/resource/capacity decision; atomic strictly greater fence. |
| `effect.submit` | `A13`, `A14`; `F01`, `F02`; rejection compound `A03`, `A05`, `X03`, `X06`, or `X08` | E1-E4 command binds exact E/P, effect, input digest, causation, idempotency, and required approval/lease/fence. Acceptance atomically consumes the exact grant through `A13` or `A14` and then creates the effect through `F01`. A failed gate always takes `F02`; it additionally takes exactly one rejection-to-HITL row only when canonical facts prove a human decision is unresolved. No grant use is consumed and no external effect is invoked. |
| `effect.record_succeeded` | `F03` | ACTIVE current attempt/fence where required; normalized output digest and durable known-success receipt. |
| `effect.record_failed` | `F04` | ACTIVE current attempt/fence where required; durable known-failure receipt states whether anything committed. |
| `effect.record_unknown` | `F05`; `X09` | External outcome cannot be proved; durable evidence/cursor and `unknown_operation=PRIMARY_EFFECT`; `F05` precedes `X09` atomically. |
| `effect.reconcile` | `F08`-`F13`; `X20`-`X25` | Reconciliation evidence targets the same effect and never invokes it. Only the pairings in the atomic cross-machine table are valid; the effect event precedes the execution event. |
| `effect.begin_compensation` | `F06`, `F07`; `X10`, `X17` | Linked corrective effect and original receipt are exact; required approval/lease/fence/idempotency pass; history remains. The selected F transition precedes the selected X transition atomically. |
| `effect.record_compensated` | `F14`; `X26` | Known compensation success. `F14` commits before execution terminal `FAILED`. |
| `effect.record_compensation_failed` | `F15`; `X27` | Known compensation failure. `F15` commits before execution enters `NEEDS_HITL`. |
| `effect.record_compensation_unknown` | `F16`; `X28` | Unknown corrective outcome with `unknown_operation=COMPENSATION`; no repetition; execution enters `RECONCILING`. |

Commands not listed in this table are invalid in lifecycle-v1. A command MUST
NOT combine listed transitions except for exactly one row in the following
closed table. Every row is one transaction; events are appended in the shown
order and all affected projections, command result, approval use, and outbox
rows commit or roll back together.

| Command | Closed transition combination and event order |
|---|---|
| `effect.submit` accepted | `A13` then `F01`: `approval.use_consumed.v1`, then `effect.accepted.v1`; or `A14` then `F01`: `approval.use_consumed.v1`, `approval.exhausted.v1`, then `effect.accepted.v1`. |
| `effect.submit` ordinary rejection | `F02`: `command.rejected.v1`, then `effect.rejected.v1`; approval use is unchanged, no effect aggregate is created, and no lifecycle state changes. |
| `approval.request` rejection to approval HITL | For `CLASSIFICATION_UNKNOWN_OR_AMBIGUOUS`, `SELF_APPROVAL_PROHIBITED`, `CLASS_DOWNGRADE_PROHIBITED`, or `AUTOMATIC_OR_BYPASS_ACTION_PROHIBITED`, and only when a valid human decision remains required: `A03` from `ABSENT`, with `command.rejected.v1` then `approval.hitl_required.v1`. The rejected command is `approval.request`. |
| `approval.grant` rejection to approval HITL | For `CLASSIFICATION_UNKNOWN_OR_AMBIGUOUS` or `SELF_APPROVAL_PROHIBITED`, and only while the approval source is `PENDING` and a valid human decision remains required: `A05`, with `command.rejected.v1` then `approval.hitl_required.v1`. The rejected command is `approval.grant`. |
| `effect.submit` rejection to approval HITL | For `EFFECT_STAGE_CLASS_MISMATCH`, `CLASSIFICATION_UNKNOWN_OR_AMBIGUOUS`, `SELF_APPROVAL_PROHIBITED`, `CLASS_DOWNGRADE_PROHIBITED`, or `AUTOMATIC_OR_BYPASS_ACTION_PROHIBITED`, and only when approval classification/binding is the unresolved decision: `F02`, then `A03` from approval `ABSENT` or `A05` from approval `PENDING`; event order is `command.rejected.v1`, `effect.rejected.v1`, then `approval.hitl_required.v1`. |
| `effect.submit` rejection to execution HITL | For the same five codes, only when approval is not the unresolved target and the execution/effect decision requires a human: `F02`, then `X03` from `PLANNED`, `X06` from `READY`, or `X08` from `RUNNING`; event order is `command.rejected.v1`, `effect.rejected.v1`, then `execution.hitl_required.v1`. |
| `effect.record_unknown` | `F05` then `X09`: `effect.outcome_unknown.v1`, then `execution.reconciling.v1`. |
| `effect.begin_compensation` | `F06` or `F07`, then `X10` or `X17` as permitted by the current execution state: `effect.compensating.v1`, then `execution.compensating.v1`. |
| `effect.reconcile` to work | `F08` then `X20`: `effect.succeeded.v1`, then `execution.running.v1`. |
| `effect.reconcile` to terminal success | `F08` then `X22`: `effect.succeeded.v1`, then `execution.succeeded.v1`. |
| `effect.reconcile` to compensation | `F10` then `X21`: `effect.compensating.v1`, then `execution.compensating.v1`. |
| `effect.reconcile` to terminal failure | `F09` or `F12`, then `X23`: the selected effect event, then `execution.failed.v1`. |
| `effect.reconcile` still unknown | `F11` then `X24`: `effect.reconciliation_observed.v1`; the self-transition has no second event. |
| `effect.reconcile` to HITL | `F13` or `F11`, then `X25`: the selected effect event, then `execution.hitl_required.v1`. |
| `effect.record_compensated` | `F14` then `X26`: `effect.compensated.v1`, then `execution.failed.v1`. |
| `effect.record_compensation_failed` | `F15` then `X27`: `effect.compensation_failed.v1`, then `execution.hitl_required.v1`. |
| `effect.record_compensation_unknown` | `F16` then `X28`: `effect.outcome_unknown.v1`, then `execution.reconciling.v1`. |

The four rejection-to-HITL rows are the only alternate command triggers for
their named A/X transition IDs; the ordinary command shown in each machine
table remains the standalone accepted path. For those compound rows, the
Authority Plane derives the target
from canonical state; the caller cannot select it. Approval `ABSENT`/`PENDING`
takes precedence only when approval classification or binding is the unresolved
decision. Otherwise an eligible `PLANNED`/`READY`/`RUNNING` execution takes its
listed X transition. Exactly one HITL transition may be appended. An aggregate
already in `NEEDS_HITL` receives no self-transition. A `RECONCILING` execution
uses accepted `effect.reconcile` behavior (`F11` then `X25`) when evidence
requires a human decision; an unknown corrective outcome in `COMPENSATING`
uses `F16` then `X28`. Closed/terminal states, ineligible source states, and
ordinary deterministic validation failures receive only the rejection events
permitted by their row. No other rejection code or command may append an
approval or execution state event.

## Canonical Lifecycle Events

Every event binds the canonical tenant/run/task, primary aggregate identity and
version, current `authority_epoch`, database timestamp, `event_id`, stream
`sequence`, catalog/version, causation/correlation, normalized payload digest,
and previous/event hash. `attempt_no`, `effect_id`, `approval_id`, `lease_id`,
and `fencing_token` are REQUIRED when applicable to the row. Provider metadata
may appear only under its opaque namespace.

| Event type | Aggregate/result | Transition coverage | Closed meaning |
|---|---|---|---|
| `execution.planned.v1` | Execution | `X01` | Creates PLANNED execution. |
| `execution.ready.v1` | Execution | `X02`, `X14` | Records READY target and source transition ID. |
| `execution.running.v1` | Execution | `X05`, `X15`, `X20` | Records RUNNING and current DB attempt/fence. |
| `execution.hitl_required.v1` | Execution | `X03`, `X06`, `X08`, `X25`, `X27` | Records typed human decision requirement and E2-E4 freeze. |
| `execution.reconciling.v1` | Execution | `X09`, `X16`, `X28` | Records unknown outcome and reconciliation reference. |
| `execution.compensating.v1` | Execution | `X10`, `X17`, `X21` | Records linked compensation work in progress. |
| `execution.succeeded.v1` | Execution | `X11`, `X22` | Records terminal success after known-outcome checks. |
| `execution.failed.v1` | Execution | `X12`, `X18`, `X23`, `X26` | Records terminal failure and compensation references when required. |
| `execution.blocked.v1` | Execution | `X04`, `X07`, `X13`, `X19` | Records terminal blocker and residual-state disposition. |
| `approval.not_required.v1` | Approval | `A01` | Creates E0/P0 NOT_REQUIRED assessment. |
| `approval.requested.v1` | Approval | `A02` | Creates exact pending approval. |
| `approval.hitl_required.v1` | Approval | `A03`, `A05` | Records approval-side human decision requirement. |
| `approval.granted.v1` | Approval | `A04`, `A09` | Records exact server-authorized grant. |
| `approval.rejected.v1` | Approval | `A06`, `A10` | Records closed rejection. |
| `approval.revoked.v1` | Approval | `A07`, `A11`, `A15` | Records closed revocation. |
| `approval.expired.v1` | Approval | `A08`, `A12`, `A16` | Records database/session expiry. |
| `approval.use_consumed.v1` | Approval | `A13`, `A14` | Records one exact atomic use. |
| `approval.exhausted.v1` | Approval | `A14` | Records closed max-use exhaustion after the final use event. |
| `lease.acquired.v1` | Lease | `L01`, successor part of `L05` | Creates ACTIVE lease with DB times, attempt, and fence. |
| `lease.renewed.v1` | Lease | `L02` | Records in-policy renewal and new DB deadlines. |
| `lease.released.v1` | Lease | `L03` | Records closed release. |
| `lease.expired.v1` | Lease | `L04` | Records closed DB-clock expiry. |
| `lease.superseded.v1` | Lease | old-lease part of `L05` | Records closed old fence before successor acquisition. |
| `effect.accepted.v1` | Effect/Saga receipt | `F01` | Durably accepts exact E1-E4 effect after every gate, before invocation. |
| `effect.rejected.v1` | Effect/Saga rejected receipt only | `F02` | Records rejection without creating an accepted effect aggregate or invoking an effect. |
| `effect.succeeded.v1` | Effect | `F03`, `F08` | Records known primary success. |
| `effect.failed.v1` | Effect | `F04`, `F09` | Records known primary failure and commit indicator. |
| `effect.outcome_unknown.v1` | Effect | `F05`, `F16` | Records unknown primary/compensation operation and reconciliation data. |
| `effect.reconciliation_observed.v1` | Effect | `F11` | Records additional evidence while the outcome remains UNKNOWN; it never invokes the effect. |
| `effect.compensating.v1` | Effect | `F06`, `F07`, `F10` | Records linked corrective action in progress. |
| `effect.compensated.v1` | Effect | `F12`, `F14` | Records known corrective success while preserving original history. |
| `effect.compensation_failed.v1` | Effect | `F13`, `F15` | Records known corrective failure. |
| `command.rejected.v1` | Command audit | All durable rejection codes | Records typed rejection/result without applying the prohibited target transition. |

An event whose catalog/version is lifecycle-v1 but whose type is outside this
table MUST fail with `UNRECOGNIZED_LIFECYCLE_EVENT_TYPE`. An event from another
catalog/version MUST fail with `CROSS_CATALOG_EVENT`; the two results are not
aliases. Neither event is applied to a lifecycle aggregate. A replay verifier
fails without mutating the stream. An Authority Plane ingestion command MAY
record only `command.rejected.v1` in its command-audit stream after it has
validated enough canonical envelope identity to do so. The separate
control-plane catalog may define other versioned domains, but they do not
become lifecycle-v1 events.

## Effect Saga and E0-E4/P0-P4 Mapping

The P-class catalog is closed and ordered by increasing impact. A class MUST
NOT be lowered to bypass a gate.

| Class | Meaning | Default gate |
|---|---|---|
| `P0` | pure/read-only query or validation | authenticated capability |
| `P1` | reversible workspace/control metadata mutation | ticket child grant |
| `P2` | durable canonical data/effect preparation | scoped approval + lease/fence |
| `P3` | external, paid-capable or provider job mutation | fresh target/action approval |
| `P4` | production activation, destructive/history, secrets/permissions | fresh explicit owner HITL; no parent-grant inheritance |

The following E/P mapping and gates are exact. Stage labels describe effect
intensity, not an automatic pipeline.

| Stage | Exact target meaning | Class | Approval/authority | Lease/fence | Idempotency, outcome and compensation |
|---|---|---|---|---|---|
| `E0` | Local read, validation or ephemeral preview; no durable ReviewRecord/export/index mutation | `P0` | Authenticated read capability | None | Pure request identity; no durable effect or compensation |
| `E1` | Append-only audit record, ReviewRecord or HITL request only | `P1` | Standing system authority plus the bounded ticket child grant; never reviewer self-assertion | None for the append-only request | `command_id` required; correction/supersession is appended, never deletion |
| `E2` | Durable business record, immutable export generation, index generation or activation | `P2` | Exact scoped approval for object/action | Active effect lease plus current DB attempt/fence | Idempotency key and receipt required; compensate with a new generation/pointer, preserving history |
| `E3` | Provider upload/job or training submission/reconciliation | `P3` | Fresh target/action approval, including billing classification | Active effect lease plus current DB attempt/fence | Internal and provider idempotency where available; `unknown` reconciles and is never blindly retried; cancel/supersede receipt preserves provider history |
| `E4` | Model/release activation, production authority switch, destructive/history, secrets or permissions action | `P4` | Fresh explicit owner HITL; no parent-grant inheritance | Active release/effect lease plus current DB attempt/fence | Exact one-shot command/manifest; compensation creates a new linked action/authority epoch and never erases external history |

E0 is an authenticated query, creates no effect aggregate, and is outside the
mutation-command catalog. E1-E4 durable commands and receipts bind
tenant/run/task/effect, stage/class, command/version, normalized input/output
digests, and causation/correlation. E2-E4 also bind exact approval and current
database attempt/fence.

| Saga status | Aggregate participation | Closed definition |
|---|---|---|
| `ACCEPTED` | Effect aggregate initial state | Authority durably accepted the exact effect command before invocation. |
| `SUCCEEDED` | Effect aggregate | Primary effect outcome is known success; it remains eligible for linked compensation if the execution later fails. |
| `FAILED` | Effect aggregate | Primary effect outcome is known failure; commit indicator determines whether compensation is required. |
| `UNKNOWN` | Effect aggregate | Primary or compensation outcome is not known; reconciliation is mandatory and invocation repetition is prohibited. |
| `COMPENSATING` | Effect aggregate | Linked corrective action is in progress. |
| `COMPENSATED` | Effect aggregate closed outcome | Corrective effect succeeded and original history remains. |
| `COMPENSATION_FAILED` | Effect aggregate closed outcome | Corrective effect failed; execution requires HITL. |
| `REJECTED` | Receipt-only closed outcome | Authority rejected the effect before invocation; no accepted effect aggregate exists. |

| Transition | Source | Target | Command/event | Additional closed condition |
|---|---|---|---|---|
| `F01` | `ABSENT` | `ACCEPTED` | `effect.submit` / approval-use event set (`A13` or `A14`), then `effect.accepted.v1` | Every E/P, approval, lease/fence, idempotency, identity, and version gate passes. Approval use and effect acceptance are one atomic result. |
| `F02` | `ABSENT` | `ABSENT` | `effect.submit` / `command.rejected.v1`, then `effect.rejected.v1`; followed by exactly one HITL event only when the closed rejection-to-HITL matrix requires it | A gate fails; receipt outcome is REJECTED, approval use is unchanged, and no effect is invoked or aggregate created. Ordinary rejection stops after `effect.rejected.v1`. |
| `F03` | `ACCEPTED` | `SUCCEEDED` | `effect.record_succeeded` / `effect.succeeded.v1` | Known primary success. |
| `F04` | `ACCEPTED` | `FAILED` | `effect.record_failed` / `effect.failed.v1` | Known primary failure with commit indicator. |
| `F05` | `ACCEPTED` | `UNKNOWN` | `effect.record_unknown` / `effect.outcome_unknown.v1` | Primary outcome unknown; execution atomically enters RECONCILING. |
| `F06` | `SUCCEEDED` | `COMPENSATING` | `effect.begin_compensation` / `effect.compensating.v1` | Later execution failure requires a linked corrective effect. |
| `F07` | `FAILED` | `COMPENSATING` | `effect.begin_compensation` / `effect.compensating.v1` | Failed effect committed durable state requiring correction. |
| `F08` | `UNKNOWN` | `SUCCEEDED` | `effect.reconcile` / `effect.succeeded.v1` | Primary success is proved without reinvocation. |
| `F09` | `UNKNOWN` | `FAILED` | `effect.reconcile` / `effect.failed.v1` | Primary failure is proved without reinvocation. |
| `F10` | `UNKNOWN` | `COMPENSATING` | `effect.reconcile` / `effect.compensating.v1` | Committed state requiring correction, or corrective work in progress, is proved. |
| `F11` | `UNKNOWN` | `UNKNOWN` | `effect.reconcile` / `effect.reconciliation_observed.v1` | Outcome remains unknown; new durable evidence is recorded without reinvocation. |
| `F12` | `UNKNOWN` | `COMPENSATED` | `effect.reconcile` / `effect.compensated.v1` | Reconciliation proves corrective success. |
| `F13` | `UNKNOWN` | `COMPENSATION_FAILED` | `effect.reconcile` / `effect.compensation_failed.v1` | Reconciliation proves corrective failure. |
| `F14` | `COMPENSATING` | `COMPENSATED` | `effect.record_compensated` / `effect.compensated.v1` | Known corrective success; execution then terminalizes FAILED. |
| `F15` | `COMPENSATING` | `COMPENSATION_FAILED` | `effect.record_compensation_failed` / `effect.compensation_failed.v1` | Known corrective failure; execution then enters NEEDS_HITL. |
| `F16` | `COMPENSATING` | `UNKNOWN` | `effect.record_compensation_unknown` / `effect.outcome_unknown.v1` | Corrective outcome unknown; execution then enters RECONCILING. |

No Saga transition exists outside `F01`-`F16`. When execution or approval is
`NEEDS_HITL`, E2-E4 cannot accept or advance an effect. E1 may append only the
audit/HITL request under its bounded authority; E0/E1 cannot satisfy the
missing decision or activate a generation.

## Rejection Taxonomy and HTTP Mapping

A rejection prevents the requested protected transition/effect. When Authority
is available, its typed result and `command.rejected.v1` audit event are
recorded atomically without applying the prohibited transition. When exactly
one closed rejection-to-HITL row is eligible, the same transaction MUST append
its listed HITL event in the specified order; when no row is eligible, it MUST
NOT append a state event. Authority-unavailable
responses cannot claim durable recording. In the table, "rejection audit only"
includes the ordered `effect.rejected.v1` receipt after
`command.rejected.v1` when the rejected command is `effect.submit`; that
receipt creates no effect aggregate and consumes no approval use.

| Rejection code | HTTP | Closed trigger | Permitted canonical side effect |
|---|---:|---|---|
| `AUTHORITY_UNAVAILABLE` | `503` | Canonical store/handler cannot decide or commit | None |
| `REQUIRED_FRESHNESS_UNAVAILABLE` | `503` | Requested authoritative freshness cannot be met | None |
| `EXPECTED_VERSION_CONFLICT` | `409` | `expected_version` is stale, future, or not current | Rejection audit only |
| `AUTHORITY_EPOCH_CONFLICT` | `409` | Command epoch differs from current database epoch | Rejection audit only |
| `COMMAND_ID_REUSE_MISMATCH` | `409` | Existing `command_id` has a different normalized digest | Rejection audit only; original result unchanged |
| `UNRECOGNIZED_COMMAND_OR_STATE` | `409` | Command/state value is outside the closed catalogs | Rejection audit only |
| `UNLISTED_TRANSITION` | `409` | Source/target pair is not in the relevant transition table | Rejection audit only |
| `TERMINAL_EXECUTION_IMMUTABLE` | `409` | Command targets a terminal execution | Rejection audit only |
| `CROSS_CATALOG_EVENT` | `409` | Event catalog/version is not lifecycle-v1 or attempts v3 replay | Rejection audit only |
| `UNRECOGNIZED_LIFECYCLE_EVENT_TYPE` | `409` | Catalog/version is lifecycle-v1 but event type is absent from the closed canonical event table | Rejection audit only; event is not applied |
| `STALE_READ_PRECONDITION` | `409` | Caller presents stale projection/cursor/cache/provider data as authority | Rejection audit only |
| `ATTEMPT_INVALID` | `409` | Attempt is client-chosen, absent where required, or differs from DB current attempt | Rejection audit only |
| `LEASE_NOT_ACTIVE` | `409` | Required lease is absent, released, expired, or superseded | Rejection audit only |
| `FENCE_STALE_OR_SUPERSEDED` | `409` | Fence is not the current database token | Rejection/audit event only; no execution/effect mutation |
| `LEASE_RENEWAL_LATE` | `409` | DB time is after `renew_by` or at/after expiry | Rejection audit only |
| `LEASE_IDENTITY_MISMATCH` | `409` | Lease tenant/run/task/resource/stage/holder does not match | Rejection audit only |
| `COMPENSATION_REQUIRED` | `409` | Terminal success/failure is requested before required correction | Rejection audit only |
| `UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION` | `409` | Caller requests terminalization or repetition while an outcome is unknown | Rejection audit only |
| `BLIND_RETRY_PROHIBITED` | `409` | Caller attempts to repeat an unknown or unclassified external effect | Rejection audit only |
| `EFFECT_STAGE_CLASS_MISMATCH` | `409` | E-stage and P-class are not the exact E0/P0-E4/P4 pair | Closed rejection-to-HITL matrix; otherwise rejection-only |
| `CLASSIFICATION_UNKNOWN_OR_AMBIGUOUS` | `409` | Stage/class/approval/effect identity/outcome cannot be determined | Closed rejection-to-HITL matrix; otherwise rejection-only |
| `EFFECT_IDEMPOTENCY_BINDING_MISSING` | `409` | Durable effect lacks required command/idempotency/input binding | Rejection audit only |
| `DELETION_AS_COMPENSATION_PROHIBITED` | `409` | Corrective request proposes erasing history instead of a linked action | Rejection audit only |
| `APPROVAL_MISSING_OR_NOT_APPROVED` | `403` | Protected action lacks exact APPROVED grant | Rejection audit only |
| `APPROVAL_REVOKED_OR_EXPIRED` | `403` | Grant is REVOKED or EXPIRED, including canonical session expiry | Rejection audit only |
| `APPROVAL_EXHAUSTED` | `403` | Grant has no remaining use | Rejection audit only |
| `APPROVAL_SCOPE_OR_SESSION_MISMATCH` | `403` | Tenant/run/task/effect/action/scope/class/session does not match | Rejection audit only |
| `SELF_APPROVAL_PROHIBITED` | `403` | Request payload asserts issuer/reviewer or actor approves itself | Closed rejection-to-HITL matrix only when a valid human decision remains required; otherwise rejection-only |
| `CLASS_DOWNGRADE_PROHIBITED` | `403` | Caller proposes a lower class to avoid a gate | Closed rejection-to-HITL matrix; otherwise rejection-only |
| `OPAQUE_METADATA_AS_AUTHORITY` | `403` | Provider/platform/correlation metadata is offered as identity, grant, attempt, fence, sequence, or transition proof | Rejection audit only |
| `AUTOMATIC_OR_BYPASS_ACTION_PROHIBITED` | `403` | Automatic/background training or a bypass action is requested | Closed rejection-to-HITL matrix only when owner action remains required; otherwise rejection-only |
| `CAPACITY_OR_RATE_LIMIT_REACHED` | `429` | Global, tenant, provider, or alias capacity/rate limit rejects allocation | Rejection audit only; no lease/effect |

| Command disposition | HTTP/result rule | Idempotency rule |
|---|---|---|
| Newly accepted and durably committed | `202` with canonical command result and event IDs | Recorded once |
| Identical duplicate of a recorded command | Return the original recorded HTTP/result | No new event, projection update, outbox item, approval use, lease, or effect |
| Non-identical reuse of recorded `command_id` | `409 COMMAND_ID_REUSE_MISMATCH` | Original record remains authoritative |
| Authority unavailable before durable decision | `503 AUTHORITY_UNAVAILABLE` | No acceptance or durable-result claim; caller must reconcile authority state before any new submission |
| Capacity/rate rejection | `429 CAPACITY_OR_RATE_LIMIT_REACHED` | The response is not permission for automatic or blind resubmission |

## Stale Reads and Notifications

The Read/Notification Plane is eventually consistent and never authorizes a
mutation. Every read that can lag MUST disclose the following closed metadata.

| Metadata | Presence | Normative meaning |
|---|---|---|
| `stale` | Required | Boolean derived by the read adapter against its declared freshness observation. It is never permission. |
| `as_of_version` or `projection_version` | At least one required | Aggregate/projection version represented. If both appear, they MUST describe the same represented snapshot. |
| `last_event_id` or `sequence` | At least one required | Durable canonical event cursor represented. If both appear, they MUST identify the same cursor position. |
| `authority_epoch` | Required | Epoch observed by the read; the handler still compares command epoch to current database authority. |
| `read_at` | Required | Read-plane observation time. It is not lease or approval time authority. |
| `lag_type` | Required | Typed unit/category for measured lag, such as event-count or duration. |
| `lag_value` | Required | Non-negative measured lag in `lag_type`; unknown measurement is an explicit typed unknown value, never zero. |

An authenticated caller MAY submit `expected_version` learned from a read, but
the Authority Plane MUST independently compare it with current canonical state
and MUST independently verify identity, grant, attempt, fence, capacity, and
epoch. The read itself supplies none of those authorities. A request that
requires freshness and cannot obtain it returns `503`.

Outbox enqueue and canonical commit precede notification. SSE and any later
notification transport deliver sanitized, replayable notifications with a
durable cursor. Duplicate, delayed, reordered across-stream, missed, or replayed
notifications do not append events or move state. Reconnect only resumes from
canonical event/outbox position; it cannot mint identity, approval, lease,
attempt, fence, sequence, or authority epoch. Provider job IDs, stream IDs,
thread IDs, process/session IDs, and notification cursors remain opaque
correlation metadata.

## Result Contract v2 Compatibility

Result Contract v2 is ingested through a compatibility adapter as sanitized
evidence and proposals. The sole ControlPlane handler performs a new canonical
command and all current precondition checks before any lifecycle transition.

| v2 field or evidence | Compatibility projection | Prohibited promotion |
|---|---|---|
| WorkResult `status=DONE` | Proposal/evidence for `execution.succeed` | Does not mean `SUCCEEDED`, does not bypass effect/compensation checks, and is not a terminal event. |
| WorkResult `status=BLOCKED` | Proposal/evidence for `execution.block` | Does not mean canonical `BLOCKED` and does not supply owner acknowledgement. |
| WorkResult `status=NEEDS_HITL` | Proposal/evidence for `execution.require_hitl` or `approval.require_hitl` | Does not itself move either machine or grant approval. |
| `scope_owned` | Sanitized asserted-scope evidence | Is not canonical ownership, tenant identity, approval scope, or grant. |
| `evidence.commands` | Sanitized command-description evidence | Is not a canonical command, `command_id`, acceptance receipt, or effect proof. |
| `evidence.outcomes` | Sanitized observed-outcome evidence | Is not a known external outcome until authority reconciliation validates it. |
| `evidence.artifacts` | Sanitized artifact references/digests | Does not authorize reads, writes, effects, or terminalization. |
| `findings` | Sanitized observations | Cannot drive a reducer directly. |
| `changed_files` | Claimed change evidence | Is not repository truth, ownership authority, approval scope, or compensation. |
| `residual_risk` | Risk evidence for review | Does not choose E/P class or satisfy HITL. |
| `recommended_next_action` | Non-authoritative command proposal | Is never executed automatically. |
| Receipt `ownership`, objective, ticket, dispatch identity, and ownership-token digests | Historical dispatch/correlation evidence | Do not mint canonical tenant/run/task ownership or approval. |
| Receipt alias, provider, adapter, model, effort, route, and safe process/session ID | `platform_metadata.<namespace>` correlation only | Cannot drive state, capacity authority, approval, lease, attempt, fence, sequence, or epoch. |
| Receipt `attempt_id` | Legacy/provider dispatch-attempt evidence | Is not canonical `attempt_no`; any association requires an explicit authority-validated import reference. |
| Receipt timestamps, exit/transport state, quota status, byte count, and output/WorkResult digests | Sanitized historical evidence | Do not prove canonical acceptance, success, freshness, capacity, or known provider outcome. |
| ClaimProof and receipt digest fields | Integrity evidence under their original v2 meaning | Do not establish authenticity, grant authority, lease/fence authority, or lifecycle event identity. |
| Any historical v1/v2 receipt or prior retry counter | Immutable compatibility history | Must not be relabelled, re-signed, converted into a lifecycle event/grant/lease, or used to reopen a terminal execution. |

Active v2 compatibility MUST remain for at least two production releases and
90 days after MAREF-057 final authority acceptance, whichever ends later. The
clock starts only when MAREF-057 records final authority acceptance and its
calendar anchor; MAREF-056 does not start it. Historical verifier capability
needed to interpret retained records MUST remain for their full retention
lifetime. Extension is allowed; early removal is not.

Raw provider streams remain outside the compatibility projection and are not
persisted or repeated. A sanitized digest does not turn an unavailable raw
stream into portable or canonical authority.

## Reachability, Terminality, and Compensation

| Machine | State/outcome | Required reachability witness | Outgoing-set rule |
|---|---|---|---|
| Execution | `PLANNED` | `X01` | `X02`, `X03`, `X04` only |
| Execution | `READY` | `X02` or `X14` | `X05`, `X06`, `X07` only |
| Execution | `RUNNING` | `X05`, `X15`, or `X20` | `X08`-`X13` only |
| Execution | `NEEDS_HITL` | `X03`, `X06`, `X08`, `X25`, or `X27` | `X14`-`X19` only |
| Execution | `RECONCILING` | `X09`, `X16`, `X24`, or `X28` | `X20`-`X25` only |
| Execution | `COMPENSATING` | `X10`, `X17`, or `X21` | `X26`, `X27`, `X28` only |
| Execution | `SUCCEEDED` | `X11` or `X22` | Empty; terminal |
| Execution | `FAILED` | `X12`, `X18`, `X23`, or `X26` | Empty; terminal |
| Execution | `BLOCKED` | `X04`, `X07`, `X13`, or `X19` | Empty; terminal |
| Approval | All eight states | `A01`-`A16` cover each state | Only source rows listed in the Approval table; closed states have empty outgoing set |
| Lease | All four states | `L01`-`L05` cover each state; no pre-acquisition aggregate | ACTIVE uses `L02`-`L05`; all other states have empty outgoing set |
| Effect | All eight Saga statuses | `F01`-`F16` plus receipt-only `F02` cover each status | Only the Effect Saga table; REJECTED, COMPENSATED, and COMPENSATION_FAILED receipts are closed |

| Compensation condition | Required ordered behavior | Terminal/remediation result |
|---|---|---|
| Failure and no effect committed | Record known failure | Execution may take `X12` or `X18` to terminal `FAILED`. |
| Failure and an effect committed | Record linked compensation start before terminalization | Execution enters `COMPENSATING`; direct `FAILED`/`SUCCEEDED` is rejected. |
| Compensation succeeds | Record `effect.compensated.v1` before `execution.failed.v1` in one transaction | Execution becomes terminal `FAILED`. |
| Compensation fails | Record `effect.compensation_failed.v1` before HITL event | Execution becomes `NEEDS_HITL`, not terminal. |
| Compensation outcome unknown | Record `effect.outcome_unknown.v1` before reconciliation event | Execution becomes `RECONCILING`; no corrective effect is repeated. |
| Work after any terminal execution | Plan a distinct tenant/run/task execution with predecessor link | Old execution remains immutable; new execution has independent version, command, approval, attempt, lease/fence, effect, and receipt history. |

Deterministic replay of the ordered lifecycle events MUST produce exactly the
same aggregate states, versions, attempts, fences, approval uses, and effect
outcomes. Replay cannot consult provider metadata, notification delivery, chat
history, or connection-local caches.

## Traceability and Acceptance Matrix

| Trace ID | Normative source | Lifecycle-v1 coverage |
|---|---|---|
| `T01` | [ADR-001 Canonical Authority](../adr-001-canonical-authority.md) | Canonical writer, identities, atomic event/projection/outbox, opaque provider metadata: `G02`, `G05`, `G06`, identity table. |
| `T02` | [ADR-002 Transitions, Attempts, Leases, and Fencing](../adr-002-transition-and-lease.md) | Orthogonal machines, CAS/idempotency, DB attempts/fences, 120/40/zero-grace lease policy: `G01`, `G03`-`G05`, `L01`-`L05`. |
| `T03` | [ADR-003 Commands and Notifications](../adr-003-transports-and-openai-websocket.md) | Commit/outbox before notification, provider transport non-authority, SSE cursor semantics: Stale Reads and Notifications. |
| `T04` | [ADR-004 Session-scoped Grants](../adr-004-session-scoped-approval.md) | Exact session/action/scope/use/expiry, server issuer/reviewer, no inheritance for P4: `A01`-`A16`, approval commands/rejections. |
| `T05` | [ADR-005 Frozen v3 Boundary](../adr-005-event-ledger-boundary.md) | Separate lifecycle catalog and rejection of cross-catalog replay: `G21`, canonical event table. |
| `T06` | [ADR-006 HITL and Effect Saga](../adr-006-hitl-effect-saga.md) | Exact E0/P0-E4/P4 mapping, NEEDS_HITL freeze, no automatic/bypass training, reconciliation and compensation: `G08`-`G16`, `F01`-`F16`. |
| `T07` | [ADR-007 Compatibility and Migration](../adr-007-compatibility-and-migration.md) | Authority epoch, terminal linked remediation, v2 window/history boundary: identities, compatibility mapping, terminality tables. |
| `T08` | [ADR-008 Service Boundary](../adr-008-service-boundary.md) | Sole modular ControlPlane handler; consumers submit commands/evidence only: `G02`. |
| `T09` | [ADR-CAP-001 Authority and Read/Notification Planes](../adr-cap-001-control-agent-plane.md) | Partition law, stale metadata, and exact 503/409/403/202/429 baseline: `G18`, `G19`, rejection and stale-read tables. |
| `T10` | [C1 MAREF-010 ticket](../tickets/c1.md) | Closed lifecycle machines, commands/events, terminal compensation, rejection coverage, stale reads, and v2 compatibility. |

| Coverage ID | Closed catalog/range | Command coverage | Event coverage | Primary rejection coverage | Acceptance condition |
|---|---|---|---|---|---|
| `CV01` | Execution states and `X01`-`X28` | Every X row names one listed command | Every X row names one event or ordered event set | Unlisted/terminal/version/compensation/unknown codes | All nine states reachable; terminal set exactly SUCCEEDED/FAILED/BLOCKED; no other edge. |
| `CV02` | Approval states and `A01`-`A16` | Every A row names one listed command | Every A row names one event or ordered event set | Approval/self/session/class codes | All eight states reachable; closed states have no outgoing edge; uses are atomic. |
| `CV03` | Lease states and `L01`-`L05` | Every L row names one listed command | Every L row names one event or ordered event set | Lease/fence/attempt/renew/capacity codes | No aggregate before acquisition; ACTIVE is the only nonterminal lease state. |
| `CV04` | Saga statuses and `F01`-`F16` | Every F row names one listed command | Every F row names one event or the exact ordered event set; F02 is receipt-only | Effect/class/idempotency/unknown/compensation codes | Exact E/P pairing; unknown never repeated; all compensation outcomes map to required execution state. |
| `CV05` | Canonical event catalog | Command and transition tables reference only listed event types | Event table lists every referenced type | `CROSS_CATALOG_EVENT` for wrong catalog/version; distinct `UNRECOGNIZED_LIFECYCLE_EVENT_TYPE` for an unknown type inside lifecycle-v1 | No event from frozen v3 is added, aliased, or reinterpreted; neither rejected event is applied. |
| `CV06` | Rejection and HTTP catalogs | All command families use a typed row | Rejections use `command.rejected.v1` when durable | Every lifecycle rejection maps to 503, 409, 403, or 429; accepted commit maps to 202 | Baseline meanings remain exact; no queue-memory-only acceptance. |
| `CV07` | Stale-read metadata | Commands revalidate canonical state | Notifications are post-commit only | Stale/freshness/authority codes | Every laggable read exposes flag, version, cursor, epoch, read time, and typed measured lag. |
| `CV08` | Result Contract v2 mapping | v2 values produce evidence/proposals only | Canonical event requires a new accepted command | Authority/metadata/terminal codes | DONE/BLOCKED/NEEDS_HITL, ownership, provider IDs, and historical receipts never become canonical authority. |
| `CV09` | Atomicity/idempotency | Common command preconditions apply to every command | Append/projection/outbox/result share one transaction | Duplicate mismatch and authority codes | Identical duplicate returns recorded result; non-identical reuse rejects. |
| `CV10` | Terminal/remediation rules | Terminal commands enforce effect disposition | Compensation record precedes FAILED | Terminal/compensation/unknown codes | No reopening; remediation is a new linked execution; no history deletion. |

## Explicit Exclusions and Deferred Decisions

| Area | Lifecycle-v1 boundary |
|---|---|
| Data contracts | This document defines normative semantics and tables only; concrete wire/data contract artifacts are separate C1 ownership. |
| Runtime implementation | No application, persistence, migration, adapter, UI, service, or provider implementation is authorized here. |
| Verification artifacts | No verification suite, fixture, or source artifact is created or changed here. |
| Dependencies | No database driver, pool, WebSocket library, broker, dependency, package, or version is selected. |
| Deployment and authority change | No deployment, publish, cutover, rollback drill, production target, command line, or MAREF-056/057 action is authorized. |
| Transport expansion | Internal WebSocket and any broker remain outside lifecycle-v1; HTTP fallback and transport mechanics cannot change authority semantics. |
| Capacity values | Global/tenant/provider/alias capacity numbers remain separately governed; reaching a configured limit uses the fixed `429` lifecycle result. |
| Lease tuning | The 120/40/zero-grace profile remains provisional until separately authorized telemetry review; lifecycle-v1 does not silently alter it. |
| Effect expansion | New E/P classes, automatic stage chaining, automatic/background training, bypass paths, down-classification, and self-approval are excluded. |
| Retry policy | lifecycle-v1 defines idempotent duplicate-result retrieval and reconciliation only. It authorizes no blind or automatic retry and no effect fallback. |
| Compensation | Terminal reopening, deletion/history erasure, receipt relabelling, and treating undo as record deletion are excluded. |
| Provider data | Provider/platform identifiers and sanitized metadata remain opaque correlation only; raw provider streams are neither retained nor authority. |
| Frozen history | The frozen v3 catalog/history and historical Result Contract receipts remain separate, immutable evidence. |

Any deferred high-impact lifecycle or classification choice requires fresh
human review and a separately authorized version; absence of such a decision
fails closed rather than creating behavior outside the tables above.
