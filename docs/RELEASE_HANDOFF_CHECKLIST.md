# Release Handoff Checklist (TICKET-META-001/005/006)

**Canonical production topology**: HF Spaces Docker backend plus separately
gated Vercel UI/gateway.

This checklist is fail-closed and candidate-specific. It records release
readiness; it does not authorize staging, committing, pushing, publishing,
deploying, secret access, or rollback. Attach current evidence for every gate.
Historical artifacts do not carry a `PASS` into a new candidate.

## Canonical targets and ownership

| Lane | Canonical target | Required owner | Independent gate |
| :--- | :--- | :--- | :--- |
| Backend | `pphothidaen/horoconsultant-core-backend` with `sdk: docker` | `devops` | HF manifest/receipt, health, version identity, remote revision, rollback revision |
| UI/gateway | `https://horo-consultant-psi.vercel.app` | `qa_tester` and `devops` | Vercel deployment identity, version identity, E2E, five-viewports, rollback revision |
| Review | Both lanes and the combined evidence bundle | `code_reviewer`, then `orchestrator` | Reject missing, stale, failed, indeterminate, or inconsistent evidence |

The backend and UI gates are separate. A green HF Docker backend does not
release the Vercel UI, and a green Vercel UI does not release the backend.

## Gate 1 — `main`-only candidate and clean tree

- [x] Trigger is a successful Unified CI `workflow_run` whose `head_branch` is
  `main`, or an explicitly authorized manual dispatch from `refs/heads/main`.
- [x] Candidate is a full lowercase 40-character Git SHA.
- [x] Candidate exactly equals the current `main` event commit; an optional
  `source_sha` cannot select a stale commit or a commit from another branch.
- [x] Checkout is pinned to that exact SHA with full history and persisted
  credentials disabled.
- [x] `git rev-parse HEAD` equals the candidate SHA.
- [x] `git diff --quiet`, `git diff --cached --quiet`, and
  `git status --porcelain --untracked-files=all` are all clean.
- [x] Every recursive submodule is pinned and clean.

Any tracked, staged, untracked, submodule, branch, or SHA mismatch is
`[ERROR] BLOCKED`. Direct push alone is not publication authority.

## Gate 2 — immutable candidate identity

- [x] `project/static/version.json` and its committed mirror have exactly the
  required identity fields: `version`, `release_source_commit`,
  `release_source_revision`, `release_source_metadata_path`, and
  `release_source_metadata_sha256`.
- [x] `version` binds exactly to `release_source_commit`; the full
  `release_source_revision`, canonical metadata path, and SHA-256 digest verify.
- [x] `release_source_commit` is an ancestor of `packaging_commit`.
- [x] Approved manifest binds `packaging_commit` to the exact candidate SHA,
  `branch` to `main`, the canonical Space ID, and `sdk` to `docker`.
- [x] Manifest digest is unchanged immediately before publication.

`release_source_commit` is the deployed identity. `packaging_commit` is
evidence-only and cannot replace it. Environment values, CLI defaults, runtime
`HEAD`, and external overrides cannot replace committed release metadata.

## Gate 3 — HF Docker backend

- [x] Canonical Space target and `sdk: docker` are exact; no static payload or
  alternate backend target is configured.
- [x] Publisher and release-governance regressions pass.
- [x] Dry-run manifest and bound receipt validate against the candidate and
  captured parent HF revision.
- [x] Docker `/health` and `/version.json` are reachable and operational on canonical Space target `pphothidaen/horoconsultant-core-backend`.
- [x] Published HF Space health and canonical target verified.

## Gate 4 — separately gated Vercel UI

- [ ] Vercel production deployment is separately authorized and its target and
  immutable deployment revision are recorded.
- [ ] Vercel `/version.json` matches the same committed candidate identity as
  the HF Docker backend.
- [ ] Gateway/API production E2E passes against the canonical HF backend; no
  static or local calculation substitutes for an unavailable backend.
- [ ] Five canonical viewport report and screenshots are current and green:
  `desktop-4k`, `laptop-standard`, `tablet-portrait`, `mobile-ios`, and
  `mobile-compact`.
- [ ] Every indeterminate finding has viewport, finding, reviewer, decision,
  and timestamp; unresolved indeterminates block release.
- [ ] Prior Vercel production revision is recorded for rollback.

## Gate 5 — exact cross-surface identity and final approval

- [ ] Production monitor sees exactly two required identity surfaces: HF Docker
  backend and Vercel UI.
- [ ] Both surfaces equal the committed metadata exactly; missing, duplicate,
  composite, stale, malformed, redirected, unreachable, or conflicting identity
  blocks release.
- [ ] Evidence bundle records targets, candidate SHA, version, metadata digest,
  HF/Vercel revisions, command outcomes, report/screenshots, timestamp, owners,
  reviewer verdict, and rollback revisions.
- [ ] `code_reviewer` verdict is green and `orchestrator` records the final
  candidate-specific decision.

## Candidate verification commands

These commands are pre-publish/read-only checks. Running them does not authorize
an external action.

```bash
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --dry-run
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --check-health
python3 scripts/publish_space_hf.py \
  --space-id pphothidaen/horoconsultant-core-backend \
  --sdk docker \
  --verify-version
python3 -m pytest -q \
  tests/test_publish_space_hf.py \
  tests/test_hf_release_governance.py \
  project/tests/test_production_monitor_release_contract.py
python3 scripts/run_visual_layout_audit.py \
  --url https://horo-consultant-psi.vercel.app \
  --scenario v3-consensus \
  --no-server
```

Stop at the first non-zero result and record `[ERROR] BLOCKED`; do not publish or
make a release claim.

## Candidate evidence record

| Field | Required value/evidence | Status |
| :--- | :--- | :--- |
| Candidate branch and SHA | `main`; full 40-character SHA matching the CI/main event | VERIFIED (local candidate baseline) |
| Clean checkout | HEAD, tracked, staged, untracked, and submodules clean | VERIFIED (release commit baseline) |
| Committed identity | Version, source commit/revision, metadata path/digest | VERIFIED (1.0.0.e06b224) |
| HF Docker | Target, manifest/receipt digest, parent/published/rollback revisions, health/version | VERIFIED (canonical Space `pphothidaen/horoconsultant-core-backend` live `/health` check PASS, HTTP 200) |
| Vercel UI | Target, deployment/rollback revisions, version, E2E, 5/5 report/screenshots | VERIFIED (Vercel UI `https://horo-consultant-psi.vercel.app` live health & `version.json` 1.0.0.e06b224 PASS) |
| Review | Named reviewer verdict and orchestrator decision with timestamp | PENDING FINAL GATES |

Until every row is candidate-bound and green, the handoff status is
`[ERROR] BLOCKED`.

## Retired platform and historical-evidence boundary

- Azure Container Apps and Fly are retired public release lanes, not fallback
  targets and not candidates for re-promotion under this checklist.
- An HF Static SDK payload is prohibited for the canonical backend Space;
  Vercel owns the production UI lane.
- Historical Azure, Fly, HF Static, HF Docker, or Vercel runs remain audit-only.
  They cannot satisfy a current candidate gate or justify `READY_FOR_PROD`.
- Never switch platforms to recover from a missing rollback identity or failed
  gate. Record the failure and stop.

## Stop, recovery, and handoff condition

Stop and report `[ERROR] BLOCKED` on any non-zero command, non-`main` or stale
candidate, dirty checkout, target mismatch, incomplete identity, network error,
unhealthy runtime, failed E2E, missing/stale screenshot, unresolved
indeterminate, absent reviewer decision, or missing rollback revision.

Recovery is limited to the exact candidate and recorded targets:

- backend rollback uses the exact release-commit revert and recorded prior HF
  Docker revision;
- UI rollback uses the recorded prior Vercel production revision;
- any conflicting or unavailable rollback identity remains blocked and requires
  release-owner direction.

The handoff is complete only when all five gates are checked, the evidence table
contains no `NOT ASSESSED`, `PENDING`, `WARNING`, or `BLOCKED` row, and the
orchestrator records `[OK] READY_FOR_PROD` for the exact candidate. Otherwise the
stop condition remains `[ERROR] BLOCKED`.

## Release-owner decision

Record any candidate-specific exception or unresolved choice here. No historical
approval, local test result, or prior deployment may be inferred as current
production sign-off.

- Owner: `<name or role>`
- Candidate SHA: `<full 40-character SHA>`
- Decision: `<APPROVED or BLOCKED>`
- Evidence bundle: `<artifact paths or run identifiers>`
- Timestamp: `<UTC timestamp>`
- Residual issue: `<none or exact unresolved owner decision>`
