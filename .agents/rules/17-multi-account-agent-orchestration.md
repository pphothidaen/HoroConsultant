# Rule 17: Multi-Account Dispatch and Orchestrator-Only Control

## Purpose

Govern auditable alias dispatch without mistaking a configured alias, route, or
rendered prompt for execution. The current/root session is an orchestrator, not
an implementation or release worker.

## Ownership

- The root/current session may decompose, assign aliases or native sub-agents,
  monitor, collect receipts, resolve ownership conflicts, request HITL, and
  make a final gate decision.
- An assigned child owns only the files, commands, and evidence in its ticket.
- The BSA owns this rule, its skill/mirrors, `PROJECT_TASKS.md`, and
  `plans/plan.md`; generated output changes only through ecosystem sync.
- Give each writable file one editor. Any other participant is read-only.

## Orchestrator-only hard boundary

The root/current session MUST NOT directly edit implementation, run
implementation or QA commands, stage, commit, push, deploy, publish, or claim
that it performed a child's work. It delegates those actions to a bounded
child, then reports the child's attributed receipt. Monitoring and read-only
state collection are permitted only to coordinate the child work.

### Explicit user-waiver exception

Only a fresh, explicit user waiver can permit one otherwise-prohibited root
action. Before acting, record in the active ticket and plan: the user's exact
approval reference and timestamp, one action class and exact scope/target,
reason delegation is not viable, owner, and a stop condition. The waiver is
single-use, does not authorize related actions, does not bypass secrets or
production safeguards, and expires when its recorded action ends. Missing any
field means `NEEDS_HITL`; prior broad approval is not a standing waiver.

## Dispatch contract and execution proof

Apply Rule 18 before executable dispatch: bind the versioned `DispatchDecision`
digest and policy version to the receipt. Quota cannot silently lower its floor.

Every child prompt names objective, one-editor ownership, boundaries, expected
evidence, stop condition, and the non-reversion warning. Require: `Status`,
`Scope owned`, `Evidence`, `Findings`, `Changed files`, `Residual risk`, and
`Recommended next action`.

For meaningful multi-agent work, explicitly select the required configured alias(es) from
`codex1`, `codex2`, `agy1`, and `agy2` and execute a bounded terminal dispatch.
When the user explicitly names multiple aliases, dispatch each named alias to a
separate bounded lane; do not silently substitute, duplicate ownership, or
claim unselected aliases ran. A valid receipt includes alias, provider,
objective, ownership, timestamp, command outcome, safe process/session id when
available, actual child result, and non-secret evidence. Prompt rendering,
alias availability, route/model labels, or configuration alone are not proof.

### Result Contract v2

The owner authorized Result Contract v2 on 2026-08-25 for a fresh four-alias
dispatch. This authorization does not waive, relabel, or repair any earlier
receipt. The three-attempt counters and `BLOCKED` outcomes from the earlier
`codex1`, `codex2`, `agy1`, and `agy2` protocol remain immutable historical
evidence. A v2 ticket starts a new attempt counter at 1 for each required alias.

Validate two bound objects independently and fail closed:

1. `ExecutionReceipt` records `protocol_version`, dispatch ticket and attempt
   ids, alias, provider, adapter, bounded objective, ownership, safe quota
   status, start/end timestamps, exit/transport status, safe process/session id
   when supplied by the provider, output byte count and SHA-256, and the
   SHA-256 of the normalized `WorkResult`.
2. `WorkResult` records `Status`, `Scope owned`, `Evidence`, `Findings`,
   `Changed files`, `Residual risk`, and `Recommended next action`.

Use a provider-native adapter: structured JSON/JSONL plus output-schema support
for Codex, and native stream-JSON event parsing for AGY. Provider prose is
evidence input, never the receipt itself. Reject a missing field, malformed
event stream, schema/version mismatch, alias/ticket/attempt mismatch, digest
mismatch, secret-bearing field, ambiguous final event, nonzero execution
without a typed failure result, or exit zero without a valid `WorkResult`.
Adapter fallback or free-form-output inference requires new HITL authorization.

### Public outcome and portable-evidence boundary

The public `ExecutionOutcome` is validated in-process. Its public
`stdout`/`stderr` are elided, so the receipt, WorkResult, and public outcome
together are not an independently portable or offline-verifiable evidence
bundle. `portable=True` does not change that boundary: it still requires a
separately retained, trusted, exact raw-stdout record for any portable/offline
verification claim. No approved private retention channel exists now. Never
restore, log, or persist raw streams to work around this limitation.

For a successful AGY outcome, use the exact evidence language **validated
in-process only**. Do not describe an AGY success as independently portable,
offline verified, or receipt-only verified. This is a Medium residual risk.
An encrypted, access-controlled raw-output sidecar is only a future design
option requiring separate scope, retention/trust design, and HITL; do not
implement it under this rule.

Because the owner explicitly named all four aliases, v2 must dispatch
`codex1`, `codex2`, `agy1`, and `agy2` as four distinct bounded lanes. A child
lane may use a terminal CLI workaround and capture its safe receipt; the
root/current session may only assign, monitor, collect, and decide the gate. It
must not run the workaround itself.

Before any v2 read-only review dispatch, validate an approved runtime config
path and either an explicit read-only role or a provider-supported sandbox
override proven to prevent writes. Example config is not execution config, and
the default Codex `workspace-write` role cannot satisfy a read-only lane. If
the approved config path or effective read-only boundary cannot be proved,
return `BLOCKED` before starting the alias command; prompt text alone is not a
sandbox control.

## Failure, quota, and closure

If an alias cannot run, record alias, timestamp, safe failure class, and `no
child ran`; return `BLOCKED` or obtain HITL before changing ownership. Recheck
only a non-secret quota band before large work. Below 10%, stop broad work,
update `TICKET-META-008` and the plan, and run the quota guard. Retry only the
same bounded actionable failure; after three failures, or immediately for
credentials, permissions, billing, production mutation, ownership conflict, or
high-impact judgment, return `NEEDS_HITL`.

Close a child only with its receipt and evidence. The root may close the parent
only when every required child is `DONE` or explicitly `BLOCKED` with an
operator action, mirrors are synchronized, no secrets are recorded, and the
final record uses only `[OK]`, `[ERROR]`, `[WARNING]`, or `[INFO]` log tags.
