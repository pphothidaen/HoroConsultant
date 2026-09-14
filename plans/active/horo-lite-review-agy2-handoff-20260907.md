# Horo Lite review remediation: AGY2 team handoff

Status: QUOTA_BLOCKED_PARENT_TERMINAL_CHILD_STATES_UNVERIFIED

Latest authoritative progress and control-review rejection:
[TODO/DOING/DONE checkpoint](horo-lite-agy2-checkpoint-20260907.md).
AGY2 continuation returned a provider quota error; packages 02/04 require
corrections and are not accepted DONE. Existing wave-2 child states must be
reconciled before another dispatch. No push/release gate is green.
Parent: TICKET-HLITE-REVIEW-REMEDIATION-20260907
Requested execution account: agy2
Reviewed source: 77cbe84a728e93e7f7c9007ce31b50936967dddb
Authorization: Owner message on 2026-09-07 explicitly requests AGY2 execution
with subagents for the eight review findings; this account coordinates and
verifies to preserve its quota. Do not substitute a Codex worker account.

## Human session exception (2026-09-07T01:25:31Z recorded)

Owner explicitly grants a temporary exception to
PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED for this session. Scope: direct AGY2
terminal handoff, bounded worker execution/monitoring for these eight findings.
Owner: current orchestrator. Reason: canonical transport unconditionally denies
AGY before spawn. The orchestrator may launch/monitor this approved AGY2 channel;
implementation and QA remain delegated. No permanent guard edits, provider
substitution, secret disclosure, deployment or publishing. Expires when this
session ends or the owner revokes it. Stop on account mismatch, failed auth,
quota exhaustion, unexpected writes, or completion of scoped work.
The exception waives this repository pre-spawn receipt gate only; runtime/tool
sandbox approvals remain separate. It is not proof of native nested workers.

## Two-team contract

Latest owner instruction: codex1 must minimize quota usage until completion;
AGY2 owns all workers, implementation, QA, push and deployment. No substitution
with codex1 implementation/QA workers is authorized. Control team monitors
meaningful checkpoints and reviews returned evidence only.

### Dispatch attempt 1

Correction at 2026-09-07T01:33:03Z: terminal response was ERROR/timeout after
306 seconds, exit 1, conversation c0520ec9-d22c-48b0-b53d-33d5278ba4b1.
Despite background token-source errors, current worktree now proves AGY2 made
planning changes and created a ticket context file. Thus the earlier blanket
authentication-block conclusion below is superseded; no valid WorkResult or
native-child receipt was returned. Preserve these edits and resume the same
conversation, never start duplicate workers solely because observation timed out.

Fresh owner-reported AGY2 quota: Gemini weekly 15.86%, five-hour 94.95%;
Claude/GPT weekly 66.44%, five-hour 100%. These are separate provider pools,
not independently queried runtime telemetry. Select Claude on AGY2 for remaining
work; preserve Gemini's critical weekly pool. Requested model for continuation:
claude-opus-4-6-thinking, high effort, one bounded orchestration turn at a time.
Nested worker count remains unverified until returned evidence proves execution.

2026-09-07: AGY2 model listing succeeded. Direct session-exception dispatch used
the existing agy2 wrapper, accept-edits with sandbox, gemini-3.1-pro-high/high,
JSON WorkResult schema and 15-minute turn limit. Host process PID 80869, tool
session 99140. The process started but no worker result or source mutation was
observed. Sanitized runtime diagnostics repeatedly report:
`error getting token source: You are not logged into Antigravity`.
Model listing success is not authenticated worker execution proof. The owned
process was sent SIGTERM to stop futile waiting. User must authenticate the
AGY2 account in its isolated Antigravity context before resuming this packet.
Do not borrow codex1/agy1 authentication or print/copy credentials.

### Subsequent owner production authorization (2026-09-07)

The owner explicitly instructs AGY2, after remediation is completed, to push to
origin/main and run CI/CD into production. This supersedes the no-push/no-deploy
clauses below ONLY after verified remediation and release gate completion.
Bind devops-deployment and hf-static-release-verification for release lanes.
Targets: existing HF Docker backend pphothidaen/horoconsultant-core-backend and
the configured existing Vercel production UI; verify target identity before
publication. Preserve branch protection; use the normal PR/merge route if
direct main pushes are protected. Never force-push or disable CI checks.
Track the pushed SHA through hosted CI, deployment, backend/UI version and
health, smoke/E2E and five-viewport verification. Record rollback revisions.
No further generic push/deploy confirmation is needed for this authorized scope.
Report incomplete gates honestly and remediate in-scope failures through AGY2.

Control team (current account): dispatch, monitor, resolve ownership/dependencies,
review receipts and final diffs, accept or reject each finding's remediation.
Execution team (agy2): orchestrator with specialist subagents for planning,
independent QA baselines, implementation, review, and final verification.
Use at most three execution lanes with disjoint ownership, subject to verified
AGY2 capacity. Nested subagent capability and quota are currently UNVERIFIED;
do not infer either from configuration. Begin with one bounded planning lane.

You are not alone in the codebase; do not revert edits made by others. Work only
within your assigned ownership and adapt to visible changes from other agents.

No push, deployment, publishing, or credential/configuration changes are included.
The session-only transport exception above supersedes the earlier transport
block for this handoff. Local baseline/source commits may be prepared under
repository provenance rules; retain exact test-first history and normal hooks.
Never weaken frozen tests or replace verified calculations with proxies.

## First bounded assignment

Lane: TICKET-HLITE-REVIEW-REMEDIATION-20260907-PLAN
Role: business_analyst
Skills: bsa-doc-skill-management, agile-governance, requirement-grill-gate
Ownership: ATOMIC_TICKET.md and plans/plan.md only; source and tests read-only.
Objective: reconcile current source against the eight findings below, register
atomic baseline/source/review/QA successor tickets, and bind exact paths and
modular skills. Preserve all unrelated active work and historical evidence.
Read this packet and the Horo Lite implementation plan before planning.
Planning lane stop: DONE with a concrete dependency graph and reviewable planning diff;
BLOCKED with the precise missing capability if context/dispatch cannot resolve.
Do not implement during this lane.

The AGY2 orchestrator then advances admitted baseline/source/review/QA lanes
without waiting for generic permission, and continues to the owner-authorized
release phase when all prerequisites pass. Planning completion is not the
completion of the overall handoff. Return bounded checkpoints if the CLI turn
deadline approaches; preserve resumable session and child identities.

Before any dispatch, construct the approved ticket/lane context using canonical
governed tooling, resolve it through scripts/resolve_agent_context.py, retain
the actual context digest and resolver result, and bind the Rule 18 decision.
This packet is not itself a resolver PASS, quota receipt, or dispatch approval
artifact. Do not reuse historical context hashes as current authorization.

## Remediation work packages

| ID suffix | Finding / execution owner | Proposed source ownership | Required acceptance evidence |
| --- | --- | --- | --- |
| 01 | P1: proxy calculations; developer_core | project/core/annual_timing_engine.py, project/core/past_pattern_calibrator.py | Replace seed/modulo scoring and fixed-age cycle selection with shared verified Thai natal/transit and BaZi cycle calculations. Trace facts to actual engine outputs, validate reference vectors and boundaries, preserve <50ms core goal with measured evidence. No fabricated Zi Wei claims. |
| 02 | P1: cross-domain consensus; developer_core | project/debate/consensus_matrix.py | Compare traditions within each domain before aggregation. Three traditions all reporting career=9, finance=2, love=6 must not conflict merely because domains differ. Detect genuine within-domain disagreement; missing evidence cannot count as perfect agreement. |
| 03 | P1: HITL queue not written; developer_api | project/routers/unified_reading_router.py; existing project/hitl_router.py interface, changes only if specifically admitted | Forced, uncertain, conflict and low-consensus triggers create retrievable real review items. Claim QUEUED only after successful enqueue. Prove idempotency and storage-failure behavior using isolated test storage, preserving privacy and existing schemas. |
| 04 | P1: child birth date causes 500; developer_core then developer_api | project/core/past_pattern_calibrator.py, project/core/unified_reading_engine.py, project/routers/unified_reading_router.py | Reproduce birth_date=2020-05-15 and target_year=2026. Resolve insufficient history explicitly without invented events or unhandled response validation. Define young/future-birth/target-before-birth contracts with BA; document any required prospective schema amendment. |
| 05 | P2: unknown-time false precision; developer_core then developer_api then UI | project/core/annual_timing_engine.py, project/core/past_pattern_calibrator.py, project/core/unified_reading_engine.py, project/routers/unified_reading_router.py, public/lite.js, public/export_engine.js | unknown_hour=true must ignore supplied birth_time. Preserve real uncertainty ranges through API, UI and all exports. No midpoint-only substitution or calculations using unknown factors. Compatibility and OpenAPI evidence required for schema changes. |
| 06 | P2: identical topic copy / inert translation; developer_api | project/routers/unified_reading_router.py | Twelve topic-specific interpretations grounded in approved evidence, locale and focus question respected; optional translation actually works when enabled with immutable facts and bounded failure fallback. Tests must distinguish substantive topic content, not just nonempty strings. |
| 07 | P2: feedback has no explanatory effect; ux_ui_designer | public/lite.js | Feedback changes explanation emphasis while preserving scores/dates/facts; consent precedes persistence; withdrawal clears stored feedback. Browser tests verify actual DOM changes and profile isolation. |
| 08 | P2: plan/provenance mismatch; business_analyst + independent qa_tester/code_reviewer | BA: ATOMIC_TICKET.md, plans/plan.md; QA: newly admitted tests and plans/test_provenance successor records | Reconcile actual completion states; preserve historical FAILED and RECONSTRUCTED records. Freeze meaningful RED baselines prospectively; independently verify successor chains and source trailers. Never describe reconstructed history as verified TDD. |

All source paths are proposed reservations until the PLAN lane freezes exact
ownership. One editor per file: packages 01/04/05 share core paths and must be
sequential; packages 03/04/05/06 share router/schema paths and must be sequential;
packages 05/07 share UI paths and must be sequential. Package 02 can proceed
independently after its baseline. QA test files also need exclusive ownership.

For each source lane bind sdlc-aisdlc-workflow; for calculation work additionally
metaphysical-request-router and metaphysical-hitl-scope-gate. Resolve any legacy
skill labels to available canonical skills instead of inventing missing skills.
QA binds qa-regression-provenance and qa-api-ui-e2e; UI visual verification binds
ui-visual-auditor. Source review is read-only and independent of its author.

## Existing evidence and verification limits

Prior control-team review (2026-09-07):
- Horo Lite + release CI tests: 106 passed.
- Context generation/budget/evidence tests: 72 passed.
- Ecosystem sync --check: passed; this is not native runtime proof.
- Isolated FastAPI router reproduction: child input above returns HTTP 500.
- Identical-tradition consensus vector above returns agreement=0.3 and conflict.
- unknown_hour=true with null versus 14:30 time changes monthly scores.
- All 12 topics have one identical guidance string.
- Annual timing emits QUEUED_FOR_HUMAN_REVIEW without calling queue storage.
- Horo Lite provenance verify at baseline 6b67ab0 to reviewed HEAD fails with
  TEST_HASH_MISMATCH, FROZEN_TEST_CHANGED, SOURCE_COMMIT_MISSING_BASELINE_TRAILER.
- ticket-token-pre-000-checkpoint.json explicitly says RECONSTRUCTED and does
  not establish historical test-first compliance.

These observations must be revalidated on the execution team's actual HEAD.
The passing suites do not cover all findings and are not production sign-off.
Existing tests can update vault_sync_status.json or create tmp_test_render;
isolate tests and account for artifacts without reverting others' changes.

Final acceptance: all eight findings independently resolved or explicitly
reported unresolved; focused regression, API/OpenAPI/backward compatibility,
real HITL storage integration, meaningful calculation vectors, UI/export and
360/375/390/768/1440 viewport checks, privacy/security review, provenance and
ecosystem sync evidence bound to exact final source. Do not deploy. Do not
archive the sprint or declare full plan completion before all acceptance gates.

## Per-lane response contract

Return Status (DONE/BLOCKED/NEEDS_HITL), Scope owned, Evidence, Findings,
Changed files, Residual risk, Recommended next action. Include actual alias,
safe session/process identity, actual effective provider/model if observable,
commit/hash bindings, commands with results, and unresolved dependencies.
Never print secrets or persist raw provider streams. Distinguish in-process
validated AGY output from portable/offline evidence.

## Current dispatch blocker

Static inspection at reviewed HEAD confirms:
scripts/multiagent_prompt_command.py:7946-7960 rejects effective AGY transport
before Popen with PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED. Its error guidance
requires external DSG-009A / DSG-009B capability proof. The separate terminal
supervisor still has a SANDBOX_NOT_PROVEN rejection. Existing readonly role
configuration does not authorize a writing execution team.

At preparation no AGY2 worker had started. The owner subsequently granted the
session exception above; direct AGY2 preflight is now in progress. Do not edit
the permanent guard. Record actual worker start/result separately from preflight.
