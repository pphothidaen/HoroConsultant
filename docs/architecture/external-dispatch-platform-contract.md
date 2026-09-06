# External dispatch platform evidence contract

Status: DOCUMENT ONLY, 2026-09-05. Ticket: `TICKET-DISPATCH-WORKAROUND-001-PLATFORM-CONTRACT`. Overall implementation is `PARTIAL / BLOCKED`: Spark source/activation and platform requirements remain outstanding. This is a proposed acceptance contract, not documentation of an existing platform API. No platform owner has been contacted and no platform blocker is closed. [Supervisor design](agy-terminal-supervisor.md) describes the separate, currently unimplemented terminal boundary.

## Deliverables required from platform owners

| Owner / dependency | Required evidence | Rejection conditions |
|---|---|---|
| DSG-009A platform/runtime owner | Versioned host-native pre-spawn API and complete native-entrypoint coverage; authoritative scheduling snapshot; receipt binding authorization, ticket, attempt, session, normalized decision/policy and ownership digests; trusted issue/expiry time; single-use/replay protection; demonstrated start/deadline/lease/natural-exit enforcement; exact native request/result correlation | Repository hook/local token, caller assertions, interception after spawn, an uninstrumented native entrypoint, stale/replayed/cross-bound receipt, caller clock or unverifiable scheduler snapshot |
| Independent QA/security reviewer | Reproducible positive and adversarial platform tests against exact API/runtime revision, sanitized source evidence and authenticity-verification method; review verdict bound to that revision and receipt format | Prose-only PASS, missing candidate identity, self-review or fixtures presented as live platform evidence |
| DSG-009B trusted-provider-verifier owner, after reviewed DSG-009A | Telemetry independent of model prose and caller config, authentic effective provider/model/effort and privacy-preserving account binding, trusted CLI/provider session and request IDs, freshness and authenticity verification, downgrade/reroute detection | Requested identity copied as effective identity, model self-report, help/cache/argv/catalog/quota/exit-zero substituted for execution proof, missing session correlation, obsolete reviewed platform revision |
| Owner authorization, after preceding reviews | Fresh exact attempt authorization with selected alias/provider/model/effort, bounded task/ownership, deadline and current quota/health bindings under the applicable rules | Historical four-alias permission or broad implementation request substituted for an exact live grant |
| Spark platform owner (independent lane) | Exact `gpt-5.3-codex-spark` available in the system `spawn_agent` model enum, platform runtime/version identity, authorized native dispatch and native selected/effective-model evidence correlated to its attempt/session | Editing repo config/model cache, simulating the enum, selecting another model, or presenting local CLI success as native spawn proof |

DSG-009A independent acceptance precedes DSG-009B evaluation; trusted telemetry does not repair missing native interception. Both remain blocked until their actual evidence and fresh authorization are accepted. Native Spark whitelist acceptance is separate from either AGY gate and separate from project CLI capability.

The platform supplies its actual versioned schema/API and trust mechanism; this document does not invent signed host fields or credentials that the platform does not expose. Before integration, independently review the exact wire format, trust roots, freshness bounds, key rotation/revocation and missing/unknown-field behavior. If the host cannot supply a required guarantee, report `NOT_PROVEN`; do not reinterpret a local schema validator as that guarantee.

## Repository work that can proceed

New offline characterization uses synthetic fixtures explicitly labeled as such, with any subprocess/provider boundary replaced by a fail-on-call stub. It can verify current denial order, receipt validation, Spark read-only argv and role/phase/effort restrictions, and conflicting result handling. Its green result is `VERIFIED_OFFLINE`, not a source baseline authorization, native receipt, live model entitlement or provider execution proof. No new test joins or supersedes the existing exact 39-path combined baseline.

The planned project Spark adapter remains `scripts/multiagent_prompt_command.py`, with JSONL and WorkResult v2 plus private final-output cross-checking. Pin executable/version and exact governed alias; preserve Codex, `gpt-5.3-codex-spark`, `high`, rank 3, roles `devops`/`code_reviewer`, phases `qa`/`review`/`release`/`operations`, read-only sandbox and zero fallback. Existing catalog fallback order is not permission to substitute on this exact route.

Capability evidence must independently bind CLI executable/version, alias, ticket/attempt/session, requested/effective model and effort, telemetry source and digest. It is separate from existing receipt types; no old receipt changes meaning retroactively. Existing `_execution_provenance` records CLI/effective-model/effort identity as `NOT_PROVEN`; a valid WorkResult alone does not upgrade those fields. Explicit production read-only Spark safety routes remain an outstanding activation dependency. JSONL/result consistency alone does not authenticate effective model. If the CLI lacks trusted effective-model telemetry, keep `CAPABILITY_NOT_PROVEN` even after exit zero. App Server `model/list` and `model/rerouted` are discovery candidates, not evidence that the installed CLI exports trusted effective identity. A catalog or absence of a reroute event is insufficient by itself; investigating that transport does not authorize switching the implementation route.

## Activation dependency and acceptance ledger

As assessed locally on 2026-09-05, Context Task A is absent under current authority (`DOING -- DRAFT_REBUILD_REQUIRED`); its prior draft had stale authority hashes and retained nine legacy eval locations. Corrected map/spec wording already addresses several historical review defects, but current independent corrected-contract acceptance and the verified combined baseline are still absent; the dispatch baseline manifest is absent. Historical task-17/18 reviews must not be represented as current-byte rejection of already corrected wording. Refresh and independently review current authority before advancing the existing activation chain.

The next already-scoped repository step is for QA to rebuild Task A with the approved `tests/fixtures/context_profiles/evals/` map, refresh its authority hashes, obtain current independent contract acceptance, prepare dispatch provenance and actual RED results, then independently review the exact 39-path combined baseline and verify its authorized commit. Only that real evidence admits source; the approved implementation request needs no repeated scope confirmation, and cannot itself stand in for test/review evidence.

| Outcome | What may be claimed | What remains blocked |
|---|---|---|
| Offline characterization/design reviewed | `VERIFIED_OFFLINE` for the named tests/docs and exact candidate only | Source admission, health/capability, AGY execution, native Spark whitelist |
| Existing activation chain completes with fresh trusted health and exact live Spark evidence | `VERIFIED_LOCAL_CODEX_ADAPTER` within receipt freshness/alias/task bounds | Native Spark whitelist and DSG-009A/B unless independently accepted |
| Platform owner evidence independently accepted | Only the corresponding native gate, revision and attempt proven by those receipts | Other gates, other aliases/sessions and stale evidence |

Maintain AGY hard denial until the actual applicable native requirements are met and the policy change is separately authorized. A future terminal supervisor design cannot close native gates. Do not publish ReleaseNotes, archive the active sprint or claim complete offload activation from offline delivery.

## Spark Safety & Release Lane Invariants (Fail-Closed Isolation)

Under SPRINT-SPARK-SAFETY-20260905 and TICKET-SAFE-SPARK-DEVOPS-001, execution authorization for `gpt-5.3-codex-spark` on dedicated pool / alias `codex2` (effort: `xhigh` / `high`) is strictly partitioned and governed by fail-closed invariants:

1. **Role & Phase Boundary Restriction**:
   - Authorized Roles: Strictly `devops` and `code_reviewer`.
   - Authorized Phases: Strictly `qa`, `review`, `release`, and `operations`.
   - Authorized Scopes: Infrastructure verification, release gate posture hardening, AST code safety auditing, secret leak scanning, rollback integrity pre-checks, post-deployment health verification, and deployment evidence compilation.
2. **Hard Denial on Feature Implementation**:
   - Dispatch of `gpt-5.3-codex-spark` into feature development, business logic authoring, metaphysics domain calculation engines, or public API modifications is strictly forbidden.
   - Any dispatch attempt targeting role `developer` or tickets outside the safety/release lane MUST fail closed immediately with error tag `[ERROR] BLOCKED: SPARK_FEATURE_DISPATCH_PROHIBITED`.
3. **Data Plane Decoupling**:
   - Spark auxiliary pool execution (`codex_bengalfox`) operates strictly on safety tooling and release governance.
   - Host Codex primary pool (`limitId: "codex"`) remains under strict `RED_FREEZE` data plane lock until fresh trusted non-secret observation proves quota recovery. Spark capacity does NOT lift or substitute for Host Codex quota freeze.

## Release Gate Conditions & Standards

Production deployment transitions across all cloud-first targets (Azure Container Apps backend, Hugging Face Spaces Docker backend, Vercel Edge Gateway) must satisfy three mandatory, non-waivable release gates before any artifact promotion:

1. **Gate 1: Pre-Deployment Safety & Cleanliness Gate**:
   - Zero Secret Leaks: Must pass clean Rayon-parallel secret scan via `python3 project/core/code_reviewer.py --scan-secrets` with 0 leaks across all repository files.
   - Dry-Run Payload Verification: HF Spaces Docker payload packaging dry-run must pass with exit code 0 via `python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk docker --dry-run`.
   - Reviewer Safety Verdict: Independent Code Reviewer sign-off via `python3 project/core/code_reviewer.py --review` returning formal `READY_FOR_PROD` status.
2. **Gate 2: SDK-Aware Health Probes**:
   - Hugging Face Spaces Backend: SDK-aware Docker health verification probe via `python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk docker`. Probe requires HTTP 200 from `/health` endpoint with healthy JSON status.
   - Azure Container Apps Backend: Ingress health probe against `https://<aca-ingress-host>/health` returning HTTP 200 within 5000ms.
   - Vercel Edge Gateway: Routing verification ensuring `/api/*` forwards cleanly to backend ACA and static route `/` serves application entrypoint without 5xx errors.
   - Prohibited Target Overrides: Deployment to Fly.io is permanently decommissioned. Deploying Static SDK payloads to the HF Docker backend is rejected. Target substitution fails closed.
3. **Gate 3: Fail-Closed Exact-Cardinality Version Verification**:
   - Single-Cardinality Requirement: Deployed live backend and UI surfaces must expose exactly one version string and exactly one `release_source_commit` SHA matching the committed release metadata.
   - Execution Command: `python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk docker`.
   - Cardinality Invariants: Cardinality must be exactly 1. If version or commit SHA is missing (cardinality 0), multiple/ambiguous (cardinality > 1), composite, malformed, or stale: FAIL CLOSED immediately with `[ERROR] BLOCKED: INVALID_VERSION_CARDINALITY`.
   - Ancestry Invariant: Committed `release_source_commit` must be proven an ancestor of any later evidence-only `packaging_commit`. `packaging_commit` is evidence-only and cannot replace deployed runtime version identity.

## Rollback Pre-Checks & Integrity Protocol

Every deployment workflow requires pre-flight rollback verification BEFORE mutating any production environment:

1. **Pre-Deployment Rollback Pre-Checks (Mandatory Prerequisites)**:
   - Prior HF Space Revision Recorded: Capture and record immutable prior HF Docker Space git revision commit SHA.
   - Prior Vercel Deployment ID Recorded: Capture and record immutable prior Vercel production deployment URL / UID.
   - Prior Azure ACA Revision Recorded: Capture and record active Azure Container App revision name.
   - Git Revert Feasibility Check: Verify that `git revert --no-commit <release_source_commit>` cleanly applies against current worktree without merge conflicts.
   - Missing Anchor Prohibition: If ANY prior target revision is unknown, unverified, or indeterminate, the release gate fails closed immediately: `[ERROR] BLOCKED: MISSING_ROLLBACK_ANCHOR`. Deployments without proven rollback anchors are strictly prohibited.
2. **Emergency Rollback Execution Protocol**:
   - Condition: Triggered immediately if Gate 2 (Health Probe) fails, Gate 3 (Exact-Cardinality) fails, post-deployment visual regression fails, or any Circuit Breaker trips.
   - Execution Order:
     1. `HALT`: Instantly terminate active deployment publishing pipeline.
     2. `CODE_REVERT`: Revert local and remote release commit, or switch to prior verified release tag.
     3. `HF_SPACE_RESTORE`: Force-push or checkout prior recorded Docker Space revision SHA to `pphothidaen/horoconsultant-core-backend`.
     4. `VERCEL_RESTORE`: Instantly re-assign production domain alias to prior recorded Vercel deployment ID.
     5. `ACA_REVERT`: Deactivate faulty ACA revision and route 100% traffic back to prior stable ACA revision.
     6. `VERIFY_ROLLBACK`: Re-run SDK-aware health probes and version cardinality checks against rolled-back endpoints to confirm restoration.
     7. `INCIDENT_RECORD`: Append rollback receipt and incident details into `HANDOFF.md` Rescue Queue with log tag `[ERROR] ROLLBACK_EXECUTED`.

## Emergency Circuit Breakers

Fail-closed emergency circuit breakers automatically abort workflows upon boundary violations:

| Breaker ID | Trigger Condition | Breaker Action | Recovery Gate |
|---|---|---|---|
| `CB-QUOTA-EXHAUST` | Decisive remaining quota < 10.0%, HTTP 429, or `usageLimitExceeded` | Halt data plane, freeze worktree, dump interrupted tasks to `HANDOFF.md` Rescue Queue | Verified quota recovery >= 10.0% via stdio collector |
| `CB-SECRET-LEAK` | Any potential secret, API key, or credential pattern detected by scanner | Halt pipeline, fail closed, discard staging, alert security | Zero leaks verified via Rayon security scanner |
| `CB-PROBE-TIMEOUT` | Health probe fails or times out (>10s per probe) for 3 consecutive attempts | Abort deployment, trigger Emergency Rollback Protocol | Root cause analysis and verified healthy staging endpoint |
| `CB-CARDINALITY-FAIL` | Deployed version cardinality != 1 (missing, composite, or duplicate version) | Abort release verification, trigger Emergency Rollback Protocol | Corrected metadata and clean exact-cardinality probe |
| `CB-UNAUTHORIZED-DISPATCH` | Attempt to dispatch `gpt-5.3-codex-spark` into feature code or unbound ticket | Reject dispatch with `BLOCKED: SPARK_FEATURE_DISPATCH_PROHIBITED` | Operator re-routing to authorized specialist role |
| `CB-WORKTREE-CORRUPT` | Destructive git command (`reset`, `checkout --`, `clean`) attempted | Intercept and reject command; preserve multi-owner dirty tree | Hard shell hook enforcement; operator inspection |

## Standard Deployment Evidence Ledger Protocol

All release verification activities must generate an immutable, machine-readable evidence ledger logged to terminal output and recorded in sprint provenance. The ledger uses pure ASCII formatting:

```text
[INFO] === DEPLOYMENT EVIDENCE LEDGER START ===
[INFO] TIMESTAMP: <ISO8601 UTC timestamp>
[INFO] DEPLOYMENT_LANE: devops (gpt-5.3-codex-spark / codex2)
[INFO] BACKEND_TARGET: pphothidaen/horoconsultant-core-backend (SDK: docker)
[INFO] UI_TARGET: <verified-vercel-static-ui-url>
[INFO] RELEASE_SOURCE_COMMIT: <immutable-source-commit-sha>
[INFO] PACKAGING_COMMIT: <packaging-commit-sha>
[INFO] METADATA_PATH: project/release_metadata.json (sha256:<digest>)
[INFO] ROLLBACK_ANCHORS: hf_rev=<prior_hf_sha>, vercel_id=<prior_vercel_id>, aca_rev=<prior_aca_rev>
[OK] PRE_DEPLOY_SECRETS: 0 leaks found across repository
[OK] PRE_DEPLOY_DRYRUN: docker payload packaging validated
[OK] REVIEWER_SAFETY_GATE: Code Reviewer READY_FOR_PROD confirmed
[OK] BACKEND_HEALTH_PROBE: SDK-aware Docker /health HTTP 200 OK
[OK] EXACT_CARDINALITY_VERSION: Exact 1 version instance matching release_source_commit
[OK] UI_VISUAL_AUDIT: Five canonical viewports verified clean
[INFO] OUTCOME_BOUNDARY: Validated in-process; raw provider streams elided; not portable
[OK] READY_FOR_PROD: Release gate posture verified green
[INFO] === DEPLOYMENT EVIDENCE LEDGER END ===
```

If ANY check fails, replace `[OK] READY_FOR_PROD` with `[ERROR] BLOCKED: <reason>` and execute the Rollback Integrity Protocol immediately.
