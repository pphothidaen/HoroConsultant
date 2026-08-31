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

## Orchestrator-only hard boundary & host account protection

The root/current session MUST NOT directly edit implementation, run
implementation or QA commands, stage, commit, push, deploy, publish, or claim
that it performed a child's work. It delegates those actions to a bounded
child, then reports the child's attributed receipt. Monitoring and read-only
state collection are permitted only to coordinate the child work.

### Host account preservation & last-to-exhaust mandate

When dispatching child tasks and worker lanes, the Orchestrator MUST prioritize
using the quota of **other available accounts first** (e.g., if Orchestrator is on
account A, dispatch child workers to accounts B, C, D first). The Orchestrator's
host account is highest priority and MUST be preserved as the **LAST to be exhausted**,
ensuring the master brain session remains alive to coordinate, monitor, handle HITL,
and manage handoffs.

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

### QOBS local-observation boundary

`TICKET-ALIAS-RC2-004-QOBS-01` may collect and validate a content-free local
QuotaObservation only through its isolated source lanes. A schema-valid local
artifact, a DispatchDecision, or a Rule 11 snapshot is planning evidence, not
provider or alias execution proof. Provider/alias, network, secret, account,
sync, push, deploy, publish, and release actions require separate authority and
remain excluded from the QOBS recovery lane.

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

For a historical baseline AGY outcome, use the exact evidence language
**validated in-process only**. All parity flags currently remain `false`: a
local token anchor, Result Contract v3, repository hook, configuration, or
in-process result cannot make AGY eligible for native `spawn_agent`. Every
native spawn remains covered by the owner gate, with `DSG-009A` and `DSG-009B`
`BLOCKED` pending a host-native pre-spawn API/receipt and trusted provider
telemetry. Do not describe an AGY result as independently portable without
offline evidence or as authorization for a current dispatch.

The four-alias v2 language above is historical authorization context only; it
does not authorize a current dispatch. Before any future dispatch, re-run every
current dependency, owner, native-spawn, telemetry, quota, and Rule 18 gate.

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
update `TICKET-META-008` and the plan, and run the quota guard.

### Codex Multi-Account Quota Protocol & 4-Tier Adaptive Monitoring

Because Codex CLI lacks native percentage `/usage` output, assess `codex1`..`codex3`
via the 4-tier model in `scripts/codex_quota_workaround.py`:
- **Tier 1 (Normal / Green)**: 1h tokens < 1M (IDLE/LOW). Concurrency <= 3, poll 600s.
- **Tier 2 (Warning / Amber)**: Quota < 40% or 1h tokens 1M–10M. Concurrency <= 2, poll 120s, warn operator.
- **Tier 3 (Critical / Orange)**: Quota < 20% or 1h tokens > 10M. Concurrency = 1, poll 30s, pre-commit state.
- **Tier 4 (Exhausted / Red)**: Quota < 10%, `usageLimitExceeded`, or HTTP 429. Immediate freeze, auto-dump
  interrupted tasks to `HANDOFF.md` Rescue Queue, and failover to available IDLE alias (`codex2`/`codex3`/`agy`).

Run `python3 scripts/codex_quota_workaround.py --mode summary` before major dispatch.

Retry only the same bounded actionable failure; after three failures, or immediately for
credentials, permissions, billing, production mutation, ownership conflict, or
high-impact judgment, return `NEEDS_HITL`.

Close a child only with its receipt and evidence. The root may close the parent
only when every required child is `DONE` or explicitly `BLOCKED` with an
operator action, mirrors are synchronized, no secrets are recorded, and the
final record uses only `[OK]`, `[ERROR]`, `[WARNING]`, or `[INFO]` log tags.
