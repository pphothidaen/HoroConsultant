---
description: Govern alias dispatch, receipts, and orchestrator-only control.
paths:
  - "PROJECT_TASKS.md"
  - "plans/**"
  - ".agents/rules/**"
  - ".agents/skills/**"
  - "docs/templates/**"
  - "scripts/multiagent_prompt_command.py"
---

# Multi-account orchestration

The current/root session is orchestrator-only: it may decompose, dispatch,
monitor, collect evidence, resolve conflicts, request HITL, and decide gates.
It must not directly edit implementation, run implementation/QA commands,
stage, commit, push, deploy, publish, or claim child work. Delegate each such
action to one bounded owner and report its attributed receipt.

Only a fresh, explicit user waiver permits one prohibited root action. Record
approval reference/timestamp, action/target, reason, owner, and stop condition
in both active ticket and plan. It is single-use, never standing approval, and
does not bypass secret or production controls; otherwise return `NEEDS_HITL`.

Every dispatch names objective, one-editor ownership, boundaries, evidence,
stop condition, and the non-reversion warning. A route, alias, model, or
rendered command is intent, not proof: retain a non-secret child result and
safe provider/session receipt. When dispatching, consume other accounts' quotas
first and preserve the host Orchestrator account as last to exhaust. For AGY,
Claude Bucket is Conductor-only; Gemini Bucket is primary worker pool.
For Codex (`codex1`..`codex3`), enforce the 4-tier model in `scripts/codex_quota_workaround.py`
(Tier 1 Normal >50%, Tier 2 Warning <40%, Tier 3 Critical <20%, Tier 4 Red <10%/429).
On Tier 4, auto-dump interrupted tasks to `HANDOFF.md` Rescue Queue and circuit break.
Escalate after three bounded failures or immediately for credentials, permissions,
billing, production mutation, or ownership conflict.

Before executable dispatch, apply Rule 18's bound, fail-closed
`DispatchDecision`; quota cannot weaken its quality floor.

For an authorized Result Contract v2 ticket, retain historical failed receipts
unchanged and start a fresh per-alias retry counter. Validate a provider-native
`ExecutionReceipt` independently from its schema-bound `WorkResult`; fail
closed on missing/malformed events or fields, identity/digest mismatch,
ambiguous completion, secrets, or exit zero without a valid result. Codex uses
structured JSON/JSONL with output-schema support; AGY uses its native
stream-JSON events. Only child lanes may invoke a terminal CLI workaround; the
root/current session monitors and decides the gate.

Before a read-only v2 dispatch, require an approved runtime config path and an
explicit read-only role or validated provider sandbox override. Example config,
prompt text, and the default Codex `workspace-write` role are insufficient;
missing effective isolation is `BLOCKED` before execution.

## Hierarchy and limitation

Apply governance policy first, Rule 17/this rule second, then PreToolUse. The
hook only enforces marked Claude sessions (`HORO_ORCHESTRATOR_ONLY=1`) and
recognizes `HORO_ROOT_WAIVER_ID` only with a ticket-and-plan marker. It cannot
identify a Codex root session or govern the Codex runtime; Codex therefore
relies on delegation policy plus receipt review.
