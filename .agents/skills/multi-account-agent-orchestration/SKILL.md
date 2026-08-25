---
name: multi-account-agent-orchestration
description: Route bounded agent work across accounts with quota evidence and HITL gates.
---

# Multi-Account Agent Orchestration

Use this skill when work must be dispatched across Codex, AGY, Hermes, or
multiple provider accounts and the result must be auditable. It governs
planning and evidence; it does not authenticate accounts, print secrets,
deploy, publish, or alter provider configuration.

## Required dispatch record

Before dispatch, record:

- objective and acceptance criteria;
- one editor and explicit file ownership per lane;
- out-of-scope files and external actions;
- account alias/provider and non-secret quota band or status;
- evidence expected and stop condition.

## Root/current-session restriction

The root/current session is an orchestrator-only control plane. It may
decompose, delegate to native sub-agents or terminal aliases, monitor, collect
receipts, resolve conflicts, request HITL, and make final gate decisions. It
must not directly edit implementation, execute implementation or QA commands,
stage, commit, push, deploy, publish, or claim a child's work as its own.
Delegate each action to an ownership-scoped child and attribute the returned
evidence to that child.

Only an explicit, fresh user waiver permits a single prohibited root action.
Before that action, record in the active ticket and `plans/plan.md`: approval
reference/timestamp, one action class and exact target, reason delegation is
not viable, owner, and stop condition. It expires after that action, cannot
authorize adjacent work, and cannot bypass secret or production safeguards.
If any field is absent, return `NEEDS_HITL`.

Every prompt must include:

```text
You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.
```

Require the result contract: `Status`, `Scope owned`, `Evidence`, `Findings`,
`Changed files`, `Residual risk`, and `Recommended next action`.

## Result Contract v2

When an authorized ticket selects v2, preserve earlier attempts as immutable
history and start a new per-alias retry counter. Do not use v2 to waive or
retroactively validate an old receipt.

Return two independently validated objects:

- `ExecutionReceipt`: `protocol_version`, dispatch ticket/attempt ids, alias,
  provider, adapter, objective, ownership, safe quota status, start/end times,
  exit/transport status, safe process/session id when available, output byte
  count/SHA-256, and normalized `WorkResult` SHA-256.
- `WorkResult`: `Status`, `Scope owned`, `Evidence`, `Findings`, `Changed
  files`, `Residual risk`, and `Recommended next action`.

Use provider-native structured output: Codex JSON/JSONL with output-schema
support and AGY native stream-JSON event parsing. Fail closed on missing or
malformed fields/events, protocol/alias/ticket/attempt mismatch, digest
mismatch, secrets, ambiguous final events, nonzero execution without a typed
failure result, or exit zero without a valid `WorkResult`. Do not infer a pass
from prose or apply an adapter fallback without fresh HITL authorization.

When the user names `codex1`, `codex2`, `agy1`, and `agy2`, all four are
required as distinct lanes. A bounded child may invoke the terminal CLI
workaround and capture evidence. The root/current session may only assign,
monitor, collect receipts, and decide the gate; it must not run the workaround.

For a read-only lane, require an approved runtime config path plus an explicit
read-only role or a validated provider sandbox override. An example config,
prompt instruction, or default Codex `workspace-write` role does not enforce
read-only ownership. Fail closed before dispatch when the effective sandbox or
approved config path is missing or ambiguous.

## Routing and execution proof

Use `scripts/multiagent_prompt_command.py` through
`docs/templates/MULTIAGENT_PROMPT_COMMAND.md`. Render first; execution is an
explicit, separately authorized action. A rendered command, alias, Hermes
label, model name, YAML home path, or route is not proof that an account ran.
For execution proof, retain the child result and safe provider/session
telemetry. Never print or store tokens, cookies, passwords, emails, raw home
paths, or credential values.

## Meaningful multi-agent dispatch gate

When reporting or carrying out meaningful multi-agent orchestration, explicitly select
one configured alias and perform at least one bounded terminal dispatch
through it: `codex1`, `codex2`, `agy1`, or `agy2`. Meaningful work has an
agent-owned implementation, QA, review, research, or operations lane; a
planning-only discussion is not execution and must not be described as such.

1. Select one alias for the bounded task. The `or` list means one selected
   alias, not a requirement to call all four.
2. Record the selected alias, objective, ownership, timestamp, command start
   and outcome, safe process/session identifier when available, child result,
   and evidence. Rendering PromptCommand alone is not a dispatch.
3. Close the lane only after the child result satisfies the normal result
   contract. A shell function, configured account, route/model label, or
   rendered command is routing intent, never execution proof.
4. If the user explicitly names multiple aliases, dispatch every named alias to
   a separate bounded lane. Do not silently substitute an alias, assign
   overlapping writable ownership, or represent an undispatched alias as run.

### Alias-unavailable fallback

If the selected alias cannot run, record its alias, timestamp, a safe failure
class (`not configured`, `executable missing`, or `permission/authentication
required`), and `no child ran`. Do not claim the selected alias executed.

One other explicitly configured alias may be selected for the same bounded task
only if ownership, scope, and authorization are unchanged; record it as a new
attempt. If no alias can run the task, return `[ERROR] BLOCKED` with a safe
operator command or configuration decision. Return `NEEDS_HITL` immediately
for credentials, permissions, billing, production mutation, or ambiguous
alias/ownership choice. Never invent an alias or silently substitute the
orchestrator session.

## Quota, retries, and HITL

- Re-check quota before a large dispatch and record only a safe band/status.
- At below 10%, stop broad work, update `TICKET-META-008` and the account
  continuity section in `plans/plan.md`, then run:

```bash
python3 scripts/agent_quota_status_guard.py --remaining-percent <percent> --enforce
```

- Retry only the same bounded failure, recording attempt number and evidence.
- After three consecutive failed remediation attempts, or immediately for
  credentials, permissions, billing, production mutation, conflicting ownership,
  or high-impact judgment, return `NEEDS_HITL` with the exact decision or safe
  operator command required.

## Closure

Return `DONE` only when evidence matches acceptance criteria, ownership is clean,
all required children are closed, and sync checks pass. For meaningful
multi-agent work, this includes the selected-alias process/session evidence and
actual child result. Return `BLOCKED` when a safe in-scope action cannot resolve
missing evidence. Return `NEEDS_HITL` when a human authorization or decision is
required. Use only ASCII log tags:
`[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.
