# Horo Lite AGY2 checkpoint

Updated: 2026-09-07T08:43:31+07:00 (Asia/Bangkok)
Parent: TICKET-HLITE-REVIEW-REMEDIATION-20260907
Initial reviewed HEAD: 77cbe84a728e93e7f7c9007ce31b50936967dddb
Execution account: agy2. Control account: codex1 (quota preservation).
Full scope: [handoff](horo-lite-review-agy2-handoff-20260907.md).

## Owner decisions in this session

1. AGY2 owns all implementation, QA, source review, commit/push and deployment
   workers. Codex1 only coordinates, monitors, keeps checkpoint records and
   checks returned evidence. Do not silently move worker work to codex1.
2. After the eight fixes are verified, push through the normal origin/main
   workflow and complete CI/CD and production verification for the existing HF
   Docker backend and Vercel UI. Owner approval already covers these actions.
3. Human temporarily waives repository dispatch/permission restrictions for
   this session so AGY2 can execute. This includes the pre-spawn receipt block
   and AGY tool auto-approval. Do not modify permanent governance configuration.
   Tool-platform/OS approvals remain separately enforced. The waiver expires
   at session end or revocation and never proves tests, runtime or release PASS.
4. User requests this TODO/DOING/DONE checkpoint with per-item required actions
   and prohibitions. AGY2 updates this file at every meaningful checkpoint.
5. Fresh user-reported AGY2 pools: Gemini weekly 15.86%, five-hour 94.95%;
   Claude/GPT weekly 66.44%, five-hour 100%. Prefer Claude workers on AGY2.
   Pool values are separate planning observations; do not claim native telemetry.
6. Fresh user-reported Codex1 five-hour quota is 15% remaining. This triggers
   the Codex1 quota-preservation guardrail below immediately.

## Codex1 quota-preservation guardrail: active at 15%

Codex1 is an orchestration and acceptance-control plane only until its five-hour
window resets or the owner explicitly revises this decision. It MUST NOT:

- implement, edit source/tests, run test suites, run deployments, stage, commit,
  push, open parallel workers, or retry AGY2 provider work;
- inspect broad source trees, repeat prior reviews, poll more than a meaningful
  worker/process checkpoint, or consume quota to compensate for AGY2 limits;
- declare any ticket, CI, deployment or production state DONE without AGY2's
  exact evidence and an independently attributable hosted result.

Codex1 MAY only update this checkpoint, record a returned AGY2 result, compare
the named changed files against existing guardrails, and issue one compact
correction or acceptance decision. Stop immediately after each such checkpoint.

AGY2 remains the sole worker account for remediation, QA, review, commits,
origin/main push, hosted CI/CD, and production verification. Its next resume
must reconcile existing handles 206ba523, 63a8c841, and a323bccf before creating
any replacement worker. A provider quota error, missing result, timeout, or
ambiguous child status is BLOCKED, never an instruction for Codex1 to take over.

Resume this control plane only when one of these conditions holds: a schema-valid
AGY2 WorkResult arrives; a hosted CI/deployment becomes terminal; the owner
provides a materially changed AGY2 capacity/authorization; or Codex1's quota
window resets. Keep all current worktree changes intact for AGY2 reconciliation.

## Strict acceptance and stop-before-exhaustion protocol

### Acceptance is fail-closed

An item may become DONE only when all of the following are bound to the same
identified source SHA:

1. The required behavior and every prohibition in its row have concrete,
   relevant evidence; a passing unrelated suite is insufficient.
2. QA proves a meaningful negative/control case and the original reported
   failure is reproduced as fixed. Tests must not weaken assertions or broaden
   contracts silently.
3. The change remains within assigned ownership; test provenance is valid or
   explicitly marked prospective/reconstructed without being misrepresented.
4. An independent AGY2 reviewer returns a typed result. For P1 findings, the
   reviewer must explicitly address the control-review findings above.
5. No remaining source/API/UI compatibility, privacy, HITL, security or release
   guardrail is contradicted. Ambiguous, missing, stale or self-reported-only
   evidence is BLOCKED.

Integrated acceptance additionally requires all eight rows accepted, a clean
scope review, exact commit and origin/main identity, hosted CI for that SHA,
and release evidence for both HF Docker backend and Vercel UI. Production is
DONE only after deployed identities, health/API/HITL smoke, UI/export E2E and
all five required viewports are green at the same release revision.

### Codex1 stop thresholds

At 15% remaining, Codex1 only processes one compact returned checkpoint and
then stops. It MUST NOT start any additional tool work if its observed remaining
quota is 12% or lower. At 10% or lower, it writes only this handoff update and
ends the turn without source inspection. At 5% or lower, it performs no further
tool actions; the next operator resumes from this file after quota reset.

### Required handoff state before Codex1 stops

The last Codex1 action must preserve this file with: timestamp and observed
quota; latest AGY2 conversation and child IDs; exact worktree status/HEAD if
already observed; each TODO/DOING/DONE row; accepted/rejected evidence; blocked
reason; live/unknown child handles; no-push/CI/production status; and the one
next safe AGY2 action. Do not clean, reset, amend, stash, commit or discard
visible worktree changes during handoff. The successor reads this file first,
checks worker handles before replacement, and continues only with AGY2.

## Status semantics

- TODO: not started, or awaiting a dependency; state the dependency separately.
- DOING: work actually started; name the active worker/session or concrete
  checkpoint. If execution stops, retain completed evidence and record the
  blocker; do not imply that a terminal process is still running.
- DONE: acceptance evidence exists at the stated source SHA and has been
  checked. A planned ticket, successful model listing, command start, role label,
  nonempty output, timeout, or green unrelated test does not establish DONE.
- Record blockers separately from these three lifecycle states. Never promote
  TODO/DOING to DONE just to close the sprint or permit production publication.

## Current checkpoint

### Latest runtime outcome: parent terminal, quota blocked

AGY2 tool session 69181 terminated: OS exit 0 but provider status ERROR,
`Individual quota reached. Please upgrade your subscription to increase your
limits. Resets in 4h51m41s.` Duration 893 seconds. Do not count the OS exit as
success. No schema-valid WorkResult was returned. Requested Claude selection
does not independently establish which model/pool every nested worker used.
The user-reported quota snapshot is superseded for admission by this actual
runtime limit; do not blindly retry, upgrade billing, or substitute codex1.

Parent reported native workers:
- 843c49b2 / package 02: reported complete; 5 new tests and 1 regression pass.
  Control review rejects completion (see CHANGES_REQUESTED below).
- 3c758f56 / package 04: reported complete; 6 new tests and 8 regression pass.
  Control review rejects completion pending contract/compatibility evidence.
- 206ba523 / package 01, 63a8c841 / package 03, a323bccf / package 08:
  reported started in wave 2. Their current live/terminal states are UNKNOWN
  after parent failure; preserve handles and revalidate before any new dispatch.

Counts above are AGY2-reported, not independently re-run by codex1. No source
fix is accepted DONE. Push/CI/CD/production remain TODO and NOT_READY.
Next eligible AGY2 continuation must FIRST read the control review below and
reconcile existing workers, then repair findings without duplicate ownership.
Use the session auto-approval waiver only for tool/repository permission gates;
it cannot remove provider quota limits. Resume after available capacity is
established through the normal AGY2 service.

### Control review checkpoint: CHANGES_REQUESTED

Codex1 performed read-only diff review; no implementation or QA executed here.
AGY2 has started packages 02 and 04 (source plus new tests are visible), but
neither is accepted as DONE. Address these findings before merge/release:

1. P1 / 02: `_default_tradition_claims` now copies identical scores to all
   traditions after removing the shifts. This manufactures consensus; do not
   change input claims to satisfy an arbitration test. The identical-traditions
   regression must pass explicitly identical `tradition_monthly_claims` fixtures.
2. P1 / 02: `_domain_agreement` returns 0.9 even for zero numeric observations.
   With an empty claim dictionary, all domains yield 0.9, above the HITL 0.75
   threshold. Missing evidence must remain unknown/require review, not certify
   high agreement. Add meaningful absent/partial-evidence negative controls.
3. P1 / 02: averaging domains can mask conflict: one domain with spread 7 has
   agreement 0.3; two agreeing domains yield monthly average ~0.767, so current
   `agreement_score < 0.75` test misses an actual tradition conflict. Preserve
   per-domain conflict independently of the aggregate score and test this case.
4. P2 / 04: globally changing response `past_patterns.min_length` from 3 to 0
   permits empty adult results too. Define/document the insufficient-history
   contract, protect adult completeness, surface the condition in UI, and
   update OpenAPI/compatibility evidence before acceptance. The new validator
   only checks year ordering; it is not proof of all future-date boundaries.
5. No baseline commits, independent QA/reviewer receipts or native-child proof
   have been accepted yet. Preserve test history honestly; do not reconstruct
   historical RED and call it verified. `vault_sync_status.json` is currently
   changed; account for the test artifact before staging.

AGY2 must read this section before its next source/QA checkpoint and return
one disposition plus evidence per finding. Production gate is NOT_READY.

| Item | Status | Evidence / next action |
| --- | --- | --- |
| Review and eight-finding handoff | DONE | Review at initial HEAD; packet includes reproductions, scope and acceptance. |
| Human session exception and production authorization recorded | DONE | Owner decisions above and handoff; no permanent guard changes. |
| AGY2 route/model availability | DONE | Existing wrapper resolved; `agy2 models` listed Gemini/Claude models. This is not worker-auth proof. |
| AGY2 initial planning | DOING | AGY2 added ticket rows to ATOMIC_TICKET.md / plans/plan.md and created a ticket context JSON. Completeness and native-child evidence still require verification. |
| AGY2 worker execution channel | DOING / blocked | Parent conversation c0520ec9-d22c-48b0-b53d-33d5278ba4b1 is terminal on quota error. Wave-2 worker states require reconciliation. |
| Fixes 02 and 04 | DOING | AGY2 source and new tests observed; control diff review CHANGES_REQUESTED above. |
| Fixes 01, 03, 08 | DOING / state unverified | AGY2 reports wave-2 native workers; inspect existing handles before resume. |
| Fixes 05, 06, 07 | TODO | Await core/API dependencies; no accepted source evidence. |
| Integrated QA and independent review | TODO | Depends on the eight fixes; each fix also needs focused QA. |
| origin/main push and hosted CI | TODO | Depends on integrated QA, review and correct release metadata. |
| HF Docker + Vercel production verification | TODO | Depends on successful CI/release; prove both runtime identities and user flows. |
| Plan reconciliation, release notes and archive | TODO | Only after actual completion; preserve unrelated active plans. |

## Per-item TODO / DOING / DONE board and guardrails

| ID | Status / owner | Required actions | Prohibited actions | DONE evidence |
| --- | --- | --- | --- | --- |
| 01 | DOING / AGY2 206ba523; current worker state UNKNOWN | Replace seed/modulo scores and fixed-age past cycles with actual shared Thai natal/transit AND BaZi cycle engine output; trace score reasons to computed facts; verify domain vectors and time/location boundaries. | No renamed proxies, fabricated planetary positions, LLM-generated scores, artificial consensus claims, or silently dropping Thai calculations. | Reviewed engine integration; reference-vector results, traceable reasons, deterministic repeatability, measured performance; final source SHA. |
| 02 | DOING / AGY2 developer_core; CHANGES_REQUESTED | Compare traditions within each domain, then aggregate; cover genuine disagreement and missing evidence. | Do not compare career against finance/love as tradition conflict; do not treat empty claims as perfect agreement or hardcode consensus PASS. | Three identical traditions with career=9, finance=2, love=6 produce no false conflict; real within-domain conflicts detected; negative tests pass. |
| 03 | DOING / AGY2 63a8c841; current worker state UNKNOWN | Wire actual retrievable HITL enqueueing for force, uncertain time, tradition conflict and low consensus; verify idempotency and storage failure. | No QUEUED status before persisted enqueue; no silent storage failure or production PII in logs/test fixtures; no bypass of required review. | Isolated storage integration proves one retrievable item per trigger/request and honest failure status. |
| 04 | DOING / AGY2 core then API; CHANGES_REQUESTED | Reproduce child input birth_date=2020-05-15, target_year=2026; define insufficient-history behavior across generation, response schema and UI; test future dates and target-before-birth. | No invented childhood events to meet minimum count; no unhandled HTTP500; no unnoticed response-contract weakening. | Child/boundary HTTP tests and explicit insufficient-history contract; intentional schema change reviewed with compatibility evidence. |
| 05 | TODO / core then API then UI | Ignore birth_time when unknown_hour=true; preserve valid-factor uncertainty ranges in core, API, UI and exports; synchronize OpenAPI if needed. | No midpoint-only scores, hidden time dependency, unsupported HIGH confidence, or fake range widening. | Same unknown-time request with null/14:30 time yields equal valid facts; ranges survive all presentation/export surfaces; compatibility tests. |
| 06 | TODO / developer_api | Produce twelve meaningfully distinct evidence-grounded topic explanations; respect locale/focus; implement optional translation with fact immutability and fallback. | No repeated generic guidance disguised by headings; no flag-only translation implementation; no changed scores/dates or unsupported interpretation presented as fact. | Semantic topic assertions; locale/focus tests; translation enabled/disabled/failure checks; deterministic facts preserved. |
| 07 | TODO / ux_ui_designer | Apply feedback to explanatory emphasis, preserve facts, persist only with consent, remove stored data on withdrawal, isolate profiles. | No score/date changes, fake accuracy percentages, persistence before consent, or merely changing button styling as personalization. | Browser evidence shows changed explanatory content, unchanged facts, correct consent/revocation/profile behavior. |
| 08 | DOING / AGY2 a323bccf; current worker state UNKNOWN | Reconcile current plans and provenance; retain FAILED/RECONSTRUCTED history; freeze meaningful prospective RED successors and source ownership before fixes. | No rewriting frozen hashes, fake historical RED, reconstructed history relabeled VERIFIED, weakened assertions or DONE without evidence. | Reviewed successor manifests/commits and guard results; honest residual history; ticket statuses match actual source/results. |

## Ownership and dependency rules

- Source 01/04/05 overlap annual_timing_engine.py, past_pattern_calibrator.py
  or unified_reading_engine.py: serialize exact file ownership.
- Source 03/04/05/06 overlap unified_reading_router.py/schema: serialize them.
- UI 05/07 overlap public/lite.js; UI/export work must coordinate ownership.
- Source 02 may run beside a disjoint lane after its baseline is ready.
- QA owns new tests and successor manifests; one editor per test file.
- Preserve other agents' edits, existing user changes and committed history.
- Use only genuinely available AGY2 subagents, with at most three workers if
  capacity permits. Record actual child identifiers; a role name is not proof.
- Do not spawn duplicate workers after a timeout. Query the previous process
  or conversation and reconcile current files before resuming.
- Never expose/copy credentials, switch account identity, force-push, disable
  branch protection, publish on failed gates, or alter production data for tests.

## Release guardrails

| Stage | Must do | Must not do | Evidence required |
| --- | --- | --- | --- |
| Commit / origin/main | Review exact diff, freeze source, verify focused/integrated tests and provenance, commit traceably; obey protected-branch workflow. | No unrelated-file staging, force push, fabricated baseline or hidden failing test. | Commits, reviewed scope, final source SHA and origin/main containing it. |
| Hosted CI/CD | Follow exact pushed SHA to terminal CI and deployment outcomes; fix failures via AGY2. | No skipped/old/unrelated run counted as PASS; no disabling failing checks. | Run URLs/IDs, SHA, job conclusions and resulting deployment revisions. |
| Production | Verify existing HF Docker backend and configured Vercel UI; bind release metadata, source/packaging identity and prior rollback revisions. | No Static SDK publish to backend, target substitution, mismatched versions or local-only PASS called production success. | Health/version, API/HITL smoke, UI/export E2E and 360/375/390/768/1440 viewport results at deployed revisions. |
| Closeout | Reconcile tickets and docs, publish accurate ReleaseNotes, archive only completed sprint artifacts when all acceptance passes. | No premature archival, 100% DONE claim or removal of unrelated active work. | Final eight-item matrix, live endpoints, verification matrix and archive list. |

## Attempt log

| Attempt | Transport outcome | Verified work | Residual / next step |
| --- | --- | --- | --- |
| 1 / tool session 99140 / PID 80869 | Terminal exit 1; ERROR timeout after 306s; conversation c0520ec9-d22c-48b0-b53d-33d5278ba4b1. Owned process was sent SIGTERM. | Planning edits and new context file observed after response. | Background login-error messages were insufficient to conclude no work ran. No valid WorkResult/native-child receipt. Resume same conversation. |
| 2 / session 61995 | Terminal exit 1 before turn; Claude rejects --effort high; zero usage. | None. | Remove unsupported effort flag. |
| 3 / session 69181 | Terminal: provider ERROR quota reached; OS exit 0; duration 893s. | AGY2 reported completed 02/04 and started 01/03/08 native workers. Control rejects 02/04 completion pending corrections. | Preserve conversation/child IDs. No blind retry; reconcile child states and current capacity before continuation. Owner auto-approval remains session scoped. |

## Worker checkpoint format

At every meaningful checkpoint, AGY2 reports and updates:

```text
Timestamp / source HEAD:
Conversation / worker IDs:
TODO IDs and dependencies:
DOING IDs and exact exclusive paths:
DONE IDs and acceptance evidence:
Changed files / commits:
Commands / exit codes / result artifacts:
Guardrail checks / exceptions used:
Blockers / live handles / exact next action:
CI and production status (UNKNOWN unless verified):
```

Keep reports concise and sanitized. The control team uses these records to
review progress instead of repeating implementation/QA on codex1.
