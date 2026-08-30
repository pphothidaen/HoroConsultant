# HoroConsultant Release and Rollback Runbook

> **Version:** 2.0.0
>
> **Canonical targets:** Hugging Face Docker backend and Vercel UI/gateway
>
> **Owners:** `devops` (execution), `qa_tester` (verification),
> `code_reviewer` (independent verdict), and `orchestrator` (final decision)

This is a fail-closed operating contract. It does not authorize a merge, push,
workflow dispatch, publish, deployment, cancellation, rerun, secret operation,
or rollback, and it is not evidence that production is currently green.

## 1. Scope and canonical topology

The only canonical production lanes are:

| Lane | Canonical target | Release mechanism |
| :--- | :--- | :--- |
| Backend | Hugging Face Space `pphothidaen/horoconsultant-core-backend`, `sdk: docker` | A successful main-bound Unified CI `workflow_run` starts the HF Docker publication workflow |
| UI/gateway | `https://horo-consultant-psi.vercel.app` | Vercel's external Git integration deploys `main` independently |

Azure Container Apps, Fly.io, and HF Static publication are retired,
noncanonical release lanes. Historical records for them are audit-only. They
must not be used as fallback targets, and this runbook intentionally contains
no executable publish or rollback instructions for them.

The Vercel and HF lanes are independent. A successful deployment or healthy
response in one lane never proves the other lane is released.

## 2. Candidate-to-production sequence

### 2.1 Freeze the candidate on remote `main`

1. Record the full 40-character lowercase candidate SHA before any external
   action.
2. Through the separately authorized integration process, make that exact SHA
   the remote `main` head. A feature branch, local branch, pull request head, or
   unpushed commit is not a production candidate.
3. Require the Unified CI run for that exact remote-main SHA to finish green,
   including its required `Test Provenance` job. Record the workflow name, run
   identifier, run URL, event, branch, head SHA, conclusion, and completion
   time.
4. Resolve remote `main` again before acting on either deployment lane. Stop if
   it no longer equals the candidate SHA.

Direct push alone is not publication proof. A green run for another SHA, a
pull-request run, a superseded run, or an ambiguous run is stale evidence.

### 2.2 Observe the two independent deployment lanes

- **Vercel:** its main-only external Git integration deploys the candidate
  independently. Record the candidate-bound GitHub Vercel deployment record.
  Also record the native Vercel deployment identifier and immutable URL when
  repository or release-owner policy requires them. Never substitute an
  unbound CLI republish for the Git-integrated record.
- **HF Docker:** a successful Unified CI `workflow_run` whose `head_branch` is
  `main` starts the HF workflow. Its source SHA must equal both the CI head SHA
  and the current main event commit. Record the HF workflow run and its bound,
  sanitized manifest and publisher receipt.

Do not infer ordering between these lanes. Wait for both to converge on the
same approved release identity within the declared deadline.

### 2.3 Verify convergence before production monitoring

Only after both lanes have converged may a scheduled Production Synthetic
Monitoring run, or a separately authorized manual dispatch of that workflow,
be accepted as candidate evidence. An earlier scheduled run is stale even if
it is green.

The accepted monitor run must be bound to the candidate checkout and must
verify exactly two identity surfaces: the canonical HF Docker backend and the
canonical Vercel UI. Record its run identifier, checked SHA, timestamps,
reports, and conclusion.

## 3. Required evidence before cutover acceptance

Record all evidence without secret values. `present`, `missing`, or `invalid`
is sufficient for a secret prerequisite.

| Evidence | Required binding | Block when |
| :--- | :--- | :--- |
| Candidate | Full SHA equals current remote `main` | Main moved, SHA is partial, or ancestry is ambiguous |
| Unified CI | Exact candidate, `main`, green conclusion, and green `Test Provenance` | Run is missing, stale, incomplete, cancelled, or for another event/SHA |
| HF pre-state | Authenticated current HF `main` revision and its remote tree | Revision/tree is unavailable, unbound, or changes before publish |
| HF publish | Canonical target, Docker SDK, approved manifest, prior revision/tree, and sanitized bound publisher receipt | Manifest, receipt, prior tree, secret prerequisite, or binding is missing or invalid |
| Vercel deployment | Candidate-bound GitHub deployment record for the canonical alias | Record is missing, stale, ambiguous, or names another target/SHA |
| Native Vercel identity | Exact deployment ID and immutable URL when required by policy | Required identifier is unavailable or conflicts with the GitHub record |
| Rollback coordinates | Prior HF revision/tree and exact prior Vercel deployment ID/URL | Either target lacks an exact, recoverable prior identity |
| Review | Named reviewer verdict and orchestrator decision with timestamps | Decision is missing, indeterminate, or based on an incomplete bundle |

An authenticated prior-tree and bound publisher receipt are mandatory whenever
the HF publisher produces them. If the publisher cannot retrieve and validate
the prior tree, stop; never fabricate it from local files, a historical
artifact, or an unauthenticated listing.

## 4. Health and release identity

`HTTP 200` from `/health`, the UI root, or an API endpoint proves availability
only. It is not release-identity, candidate, deployment, or rollback proof.

The committed `project/static/version.json` and `public/version.json` objects
must be identical and use the closed release schema:

- `version`
- `release_source_commit`
- `release_source_revision`
- `release_source_metadata_path`
- `release_source_metadata_sha256`

No extra `commit` or `packaging_commit` member is allowed on a deployed identity
surface. The version suffix must bind to `release_source_commit`; the full
source revision, canonical metadata path, and metadata digest must validate.
The source revision must resolve reproducibly and be an ancestor of the
candidate packaging commit.

Release proof requires all of the following:

1. The HF manifest and publisher receipt bind `packaging_commit` to the exact
   candidate SHA, the canonical Space, `main`, and `sdk: docker`.
2. The Vercel GitHub deployment record, and native deployment identity when
   required, bind to the exact candidate SHA and canonical alias.
3. The HF and Vercel `/version.json` bodies each exactly equal the committed
   closed-schema metadata; there must be exactly two required surfaces.
4. Health, API, UI, and visual checks are green in addition to identity, not in
   place of it.

Use the publisher's separate `--check-health` and `--verify-version` modes for
read-only HF checks. A green health mode cannot substitute for a green version
mode or for the cross-target identity evidence above.

`packaging_commit` is evidence in the manifest and receipt only. It never
replaces `release_source_commit` as the deployed identity.

## 5. Mandatory stop conditions

At any stop condition, record `[ERROR] BLOCKED`, preserve sanitized evidence,
and return control to the release owner. Never automatically rerun, cancel,
republish, roll back, or switch platforms.

| Stop condition | Required response |
| :--- | :--- |
| Remote `main` moves away from the candidate | Stop both lanes; require a new candidate-bound decision |
| CI, deployment, or monitor run is stale, ambiguous, incomplete, or bound to another SHA | Reject the run; do not choose a nearby or latest successful run |
| Required manifest, receipt, prior tree, deployment identifier, or secret prerequisite is missing/invalid | Stop the affected lane; do not infer or reconstruct the evidence |
| Declared CI/deployment/convergence/monitor deadline expires | Stop; preserve the last status and timeout evidence |
| Canonical target, release identity, SHA, tree digest, or deployment record mismatches | Stop; escalate the exact mismatch |
| Any required command is nonzero or any review is failed/indeterminate | Stop downstream work; no automatic recovery action |

A source revert is a new release candidate, not a shortcut around these gates.
It must pass the same remote-main, Test Provenance, Unified CI, independent
deployment, convergence, identity, and review sequence.

## 6. HF Docker rollback

HF rollback is a new production mutation and requires separate, action-specific
authorization. Deployment approval, incident severity, or a failed check does
not authorize it.

Before rollback, require all of the following:

1. The exact canonical Space and `sdk: docker` are named in the authorization.
2. The original immutable manifest and sanitized publish receipt validate
   together. The receipt must be an eligible publish receipt with a recorded
   `new_revision`, `new_tree_sha256`, `prior_revision`, and
   `prior_tree_sha256`.
3. The authenticated current HF head equals the publish receipt's
   `new_revision`, and its tree digest equals `new_tree_sha256`. Any movement is
   a rollback conflict.
4. The prior revision and complete prior tree are retrievable and their digest
   equals `prior_tree_sha256`.
5. The required managed secret is present and valid without being printed,
   copied into evidence, or exposed to a monitor.

The authorized operator may use the publisher's `--rollback-from` interface
only with that validated publish receipt, its matching `--manifest-path`, a
distinct `--receipt-path` for the new rollback receipt, and the canonical
`--space-id`/`--sdk` values. Generic republishing and an unbound historical
payload are prohibited.

Success requires a newly written, validated rollback receipt whose action and
status are `rollback` and `SUCCEEDED`, whose new tree exactly equals the recorded
prior tree, and whose new revision is captured. Then re-run read-only health and
closed-schema identity verification. On any failure, stop; do not retry the
rollback automatically.

## 7. Vercel rollback

Vercel rollback also requires separate, action-specific authorization. Before
the action:

1. Resolve the exact prior production deployment ID and immutable URL from the
   candidate-bound evidence bundle; never select "latest stable" by inspection.
2. Confirm the current canonical alias and current deployment identity have not
   moved since the rollback decision.
3. Confirm the prior deployment still exists, belongs to the canonical project,
   and has a candidate/source identity acceptable to the release owner.
4. Bind the authorization to that exact deployment ID or immutable URL.

Use the platform-controlled rollback/promotion operation only after those gates;
this runbook deliberately provides no generic executable rollback command.
Record the resulting native deployment identifier, GitHub deployment status,
canonical alias assignment, actor, and timestamps. Re-run closed-schema
identity, gateway/API, UI, and visual verification. Stop on any missing record,
timeout, alias movement, or identity mismatch; never automatically retry.

## 8. Tmux monitoring policy (`ACTIVE_NOW`)

Use a unique detached tmux session immediately for any local CI/deploy monitor
expected to run longer than three minutes or produce heavy output. Short,
bounded documentation checks may run directly. Tmux is a monitoring container,
not evidence of agent concurrency or release success.

Every qualifying monitor must:

- use a collision-resistant session name bound to the run/deployment ID; never
  kill or reuse a same-name session automatically;
- write to a persistent, sanitized log in a private directory and set the log
  mode to `0600` before provider output is captured;
- redact credentials, authorization headers, cookies, and secret-shaped values;
- persist the command/run identity, last observed status, start/end timestamps,
  numeric exit status, and an explicit done marker outside the transient pane;
- poll with bounded exponential backoff and a declared overall timeout;
- surface only state changes, failures, or periodic summaries, with no more than
  30 log lines in the primary terminal; and
- stop on stale identity, collision, lost log/status files, redaction failure,
  fallback ambiguity, or timeout.

The current [tmux runner](../.agy/scripts/tmux-runner.sh) must not be used
unchanged for release monitoring: it can return after an initial pane capture
without durable completion/exit evidence, and its fallback suppresses the
child's exit status. Use only a reviewed monitor/wrapper that satisfies the
evidence contract above. A tmux pane or process listing alone is never a
completion receipt.

Tmux monitoring is observation-only. It must never trigger an automatic rerun,
cancellation, deployment, publish, rollback, or secret operation.

## 9. Evidence handoff and decision

The handoff must name:

- candidate SHA and current remote-main SHA;
- Unified CI/Test Provenance run and conclusion;
- HF workflow run, current/prior/new revisions, tree digests, manifest digest,
  and publish or rollback receipt digest;
- Vercel GitHub deployment record, native deployment ID/URL when required,
  canonical alias, and prior deployment ID/URL;
- committed and deployed release identities for exactly both surfaces;
- health/API/UI/visual outcomes, monitor run, timestamps, and timeouts;
- named DevOps, QA, reviewer, and orchestrator decisions; and
- every residual risk or unavailable item.

Report `[OK] READY_FOR_PROD` only when every candidate-bound gate is current and
green. Otherwise report `[ERROR] BLOCKED`; never describe availability-only or
local evidence as a production release.

## 10. Current source references

- [Unified CI and Test Provenance](../.github/workflows/ci.yml)
- [HF Docker production workflow](../.github/workflows/hf_backend_deploy.yml)
- [Production Synthetic Monitoring](../.github/workflows/production_monitor.yml)
- [HF Docker publisher and receipt-bound rollback](../scripts/publish_space_hf.py)
- [Vercel main-only Git deployment policy](../vercel.json)
- [Release handoff checklist](RELEASE_HANDOFF_CHECKLIST.md)
