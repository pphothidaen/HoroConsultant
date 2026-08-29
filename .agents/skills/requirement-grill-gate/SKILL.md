---
name: requirement-grill-gate
description: Run fail-closed 9-dimension intake before planning, delegation, or implementation.
---

# Requirement Grill Gate

## Purpose and invocation

Use this skill when `/grill-me <request>` is invoked or when a task needs its
requirements validated before planning, delegation, or implementation.

- `business_analyst` owns the canonical command and skill contract.
- `orchestrator` owns the final gate decision and any downstream dispatch.
- The gate validates authority and scope; it does not grant new authority.
- Running the gate is intake-only. Do not implement, delegate implementation,
  deploy, publish, or perform external mutations while grilling.
- Preserve explicit user scope and exclusions. Do not turn generic governance
  defaults into permission to edit files that the request excludes.

The only valid terminal states are `APPROVED`, `WAIVED`, and `BLOCKED`.

## Required inputs

Start with:

- the raw task or change request;
- the current workspace and applicable instructions;
- any owner answers, approvals, or waivers already present in the conversation.

If no task was supplied, ask exactly one question: "What outcome should
`/grill-me` define?" Then stop and wait.

## Workflow

### 1. Auto-scan relevant context

Before asking the owner, inspect only the context needed to answer safely:

1. Root and nearest `AGENTS.md` files plus applicable `.agents/rules/` files.
2. `plans/plan.md` and `PROJECT_TASKS.md` when they contain an active baseline
   relevant to the request; read-only exclusions do not imply edit permission.
3. `git status --short` to identify concurrent or pre-existing changes.
4. Targeted code, interfaces, schemas, tests, and docs named by the request or
   found through narrow repository search.
5. Current dependency, infrastructure, security, model-routing, and domain
   policies only when the corresponding dimension applies.

Do not read secret values, use the network, mutate files, or run destructive or
production commands during the scan. Do not infer an answer from a missing or
stale artifact.

Record each material answer with one of these evidence states:

- `[AUTO]`: directly supported by a current repository source; cite its path.
- `[CONFIRMED]`: explicitly confirmed by the owner in the current context.
- `[PENDING-OWNER]`: material ambiguity that needs an owner answer.
- `[WAIVED]`: explicitly waived by the owner, with impact recorded.
- `[NOT-APPLICABLE]`: assessed and excluded with a reason.

### 2. Assess all nine dimensions

Assess every dimension. Never silently skip one.

| ID | Dimension | Default severity | Required result |
|---|---|---|---|
| D1 | Scope boundary | CRITICAL | Explicit in-scope outcomes/files, out-of-scope exclusions, and interfaces that must remain stable. |
| D2 | Requirement delta | HIGH | What changes from the current baseline, including intentional compatibility or deprecation behavior. |
| D3 | Acceptance and stop conditions | CRITICAL | Measurable criteria mapped to verification, plus the exact success and stop conditions. |
| D4 | Inputs, constraints, and dependencies | HIGH | Required inputs, dependency/runtime/security constraints, prerequisites, and unavailable dependencies. |
| D5 | Architecture, ownership, and handoff | HIGH | Impacted components, single-editor ownership, execution order, and downstream consumers. |
| D6 | Assumption register | CRITICAL | Every material assumption classified as confirmed, pending, waived, or not applicable. |
| D7 | Risk and recovery | HIGH | Material failure modes, blast radius, rollback or recovery path, and escalation threshold. |
| D8 | Budget and evidence strategy | HIGH | Model/effort or cost constraints when relevant, bounded evidence, and trimmed ASCII logs. |
| D9 | Domain and HITL check | HIGH | Metaphysics scope, canonical-source needs, conflicts, and human-review requirements. |

For `metaphysical-domain-engine`, elevate D9 to `CRITICAL` and require all of
the following before handoff:

- confirmed `source_domain` and explicit out-of-scope exclusions;
- `required_human_review=True` for conflict, low-consensus, or force-review
  cases;
- a passing `/hitl/scope-audit?source_domain=metaphysical-domain-engine`
  result with `summary.pass_gate_check=true`;
- recorded owner sign-off for every previously unresolved item.

Missing evidence for any of these requirements keeps the gate `BLOCKED`.

### 3. Resolve ambiguity one question at a time

After the auto-scan, build an internal queue ordered by:

1. unresolved CRITICAL items;
2. HIGH items that can change scope, safety, ownership, or acceptance;
3. optional refinements.

Ask exactly one owner-facing question per interaction. When supported, offer
two or three mutually exclusive choices and identify the recommended choice
and its tradeoff. Include the affected dimension and why the answer matters.
Do not bundle subquestions, repeat answered questions, or treat silence as a
waiver.

Before approval, at least these three controls must be confirmed or explicitly
waived where waiver is permitted:

- in-scope and out-of-scope boundaries;
- required inputs, assumptions, and dependencies;
- measurable success criteria and the stop condition.

After each answer, update the register, recompute the gate, ask the next single
question if needed, and stop to await the reply.

### 4. Decide the gate

Use these definitions exactly:

| State | Decision rule | Required action |
|---|---|---|
| `APPROVED` | All CRITICAL items are resolved, no waivers remain, acceptance and stop conditions are measurable, and no authority or safety blocker exists. | Emit the final report and identify only the next already-authorized phase. |
| `WAIVED` | All CRITICAL items are resolved and the owner explicitly accepted one or more non-critical omissions or risks. | Emit the final report with waiver owner, reason, impact, and boundary. |
| `BLOCKED` | Any CRITICAL item, required authority, required dependency, owner decision, or mandatory HITL evidence is unresolved. | Emit the partial report, ask at most the next single question, and halt downstream work. |

A waiver never bypasses unresolved scope, acceptance criteria, required
authorization, secrets/privacy controls, destructive or external action
approval, or mandatory metaphysics HITL review. Never invent or silently infer
a waiver.

### 5. Produce a clear report

Return a `GRILL REPORT` in the conversation with this minimum contract:

```text
GRILL REPORT
Request: <normalized task>
Status: APPROVED | WAIVED | BLOCKED
Authorized next phase: <bounded phase or NONE>

Context evidence: <paths scanned and material AUTO findings>
Nine-dimension matrix: <D1-D9 result, evidence state, remaining issue>
Scope: <IN / OUT / stable interfaces>
Inputs and dependencies: <required / available / missing>
Assumptions: <status and owner for each material assumption>
Acceptance matrix: <criterion / verification / owner / stop threshold>
Risks and recovery: <risk / mitigation / rollback or escalation>
Waivers: <owner / reason / impact / boundary, or NONE>
Blockers: <actionable blockers, or NONE>
Next question: <one question when BLOCKED, otherwise NONE>
```

Every deliverable needs at least one observable acceptance criterion. A vague
criterion such as "works correctly" is not measurable. Verification may be an
existing focused test, a read-only check, or named manual review; do not invent
a nonexistent script.

Repository persistence is conditional:

- By default, return the report in conversation only.
- Update `plans/plan.md`, `PROJECT_TASKS.md`, or another artifact only when the
  current request or higher-priority instruction explicitly includes that file.
- If an artifact is explicitly excluded, do not write it. Record the exclusion
  in the inline report; the exclusion alone is not a blocker unless delivery
  requires that artifact.
- If persistence is authorized, write only after `APPROVED` or `WAIVED`, retain
  the exact gate state, and preserve unrelated worktree changes.

## Acceptance and stop conditions for `/grill-me`

The command succeeds only when:

- all nine dimensions were assessed with an evidence state;
- D1, D3, and D6 have no unresolved item;
- required inputs, dependencies, assumptions, owners, and interfaces are clear;
- every output has measurable verification and a stop threshold;
- waivers and blockers are explicit and attributable; and
- the report identifies the exact next authorized phase without executing it.

Stop immediately when one of these conditions is reached:

- `APPROVED` or `WAIVED`: return the final report; do not begin the next phase.
- `BLOCKED`: return the partial report, ask no more than one question, and wait.
- Scope expansion or conflicting new evidence: reopen affected dimensions and
  return to `BLOCKED` until they are resolved.

## Gotchas

- Approval of the gate is not approval to commit, push, deploy, publish, access
  credentials, spend money, or perform destructive/external actions.
- Do not copy stale model names, dependency locks, test counts, or deployment
  claims from old plans; verify current sources or mark them pending.
- For subprocess evidence, keep logs trimmed and use ASCII tags only:
  `[INFO]`, `[OK]`, `[WARNING]`, and `[ERROR]`.
