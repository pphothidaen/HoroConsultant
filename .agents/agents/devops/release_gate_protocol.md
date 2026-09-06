# DevOps Release Gate & Rollback Integrity Protocol

Status: AUTHORITATIVE DEV-OPS SPECIFICATION (2026-09-05)
Sprint: SPRINT-SPARK-SAFETY-20260905
Ticket: TICKET-SAFE-SPARK-DEVOPS-001
Model Target: gpt-5.3-codex-spark on codex2 (effort: xhigh / high)
Bound Skills: [devops-deployment, hf-static-release-verification]

## 1. Safety & Dispatch Boundary Invariants

1. Fail-Closed Role Confinement:
   The devops agent under gpt-5.3-codex-spark is strictly restricted to safety, release gates, rollback integrity, and deployment evidence verification.
   It MUST NEVER be dispatched to author feature code, modify calculation logic, or implement business features.
2. Host Quota Protection:
   Operates strictly on the auxiliary Spark pool (alias codex2).
   Historical RED_FREEZE is not current quota evidence. Before dispatch, require a fresh account- and pool-bound quota observation under the orchestration policy; stale or unavailable evidence blocks admission. Never infer host capacity from the separate Spark pool.
3. Pure ASCII Logging:
   All logs, evidence outputs, and status tags MUST strictly use pure ASCII characters ([OK], [ERROR], [WARNING], [INFO]). No UTF-8 surrogate crashes.

Canonical release targets: HF Docker backend `pphothidaen/horoconsultant-core-backend` and separately verified Vercel static UI. Azure Container Apps and Fly.io are excluded public release targets. Never publish a Static SDK payload to the backend Space.

## 2. Pre-Deployment Safety Checklist

Before initiating any deployment or artifact publication, execute every check in sequence:

1. Step 1: Secret Leak Scan
   Command:
   python3 project/core/code_reviewer.py --scan-secrets
   Acceptance: 0 leaks found across repository.
   Failure: Abort immediately; emit [ERROR] BLOCKED: SECRET_LEAK_DETECTED.

2. Step 2: Docker Packaging Dry-Run
   Command:
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk docker --dry-run
   Acceptance: Exit code 0, archive generation and file exclusions verified.
   Failure: Abort immediately; emit [ERROR] BLOCKED: DRYRUN_FAILED.

3. Step 3: Rollback Anchors Capture
   Verify and record existing production target states:
   - Hugging Face Spaces: Current commit revision on pphothidaen/horoconsultant-core-backend
   - Vercel: Current production deployment UID and target URL
   Acceptance: Both rollback target IDs confirmed reachable and recorded.
   Failure: If ANY anchor is missing, abort immediately; emit [ERROR] BLOCKED: MISSING_ROLLBACK_ANCHOR.

4. Step 4: Reviewer Safety Verdict
   Command:
   python3 project/core/code_reviewer.py --review
   Acceptance: AST security analysis passes; formal READY_FOR_PROD status returned.
   Failure: Abort immediately; emit [ERROR] BLOCKED: REVIEWER_SAFETY_REJECTED.

## 3. Deployment Evidence Verification (Release Gates)

After artifact deployment, verify production endpoints using the three release gates:

1. Gate 1: SDK-Aware Health Probe
   Command:
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk docker
   Acceptance: HTTP 200 returned from /health endpoint with JSON healthy status.
   Timeout: 10s per probe, maximum 3 retries.
   Failure: Trigger Emergency Rollback Protocol immediately.

2. Gate 2: Fail-Closed Exact-Cardinality Version Check
   Command:
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk docker
   Acceptance: Deployed runtime exhibits exact-cardinality of 1 for expected version string and release_source_commit.
   Rejection: Missing (cardinality 0), multiple/ambiguous (cardinality > 1), composite, or stale identity tags.
   Failure: Trigger Emergency Rollback Protocol immediately.

3. Gate 3: UI Visual Audit and Publisher Regression
   Commands:
   python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py
   python3 scripts/run_visual_layout_audit.py --url <verified-vercel-url> --scenario v3-consensus --no-server
   Acceptance: All tests pass green, five canonical viewports verified clean.
   Failure: Trigger Emergency Rollback Protocol immediately.

## 4. Emergency Rollback Protocol

When any release gate fails or a circuit breaker trips:

1. HALT: Cease all forward deployment activities immediately.
2. REVERT CODE: Run git revert on release_source_commit, or point HEAD to prior release tag.
3. RESTORE HF SPACE: Push prior recorded Docker Space revision SHA to pphothidaen/horoconsultant-core-backend.
4. RESTORE VERCEL: Point production alias back to prior recorded Vercel deployment UID via CLI/API.
5. VERIFY ROLLBACK: Run health probe and version check against restored endpoints.
6. RECORD EVIDENCE: Log rollback details in terminal and dump incident to HANDOFF.md Rescue Queue with tag [ERROR] ROLLBACK_EXECUTED.

## 5. Standard Evidence Ledger Format

```text
[INFO] === DEPLOYMENT EVIDENCE LEDGER START ===
[INFO] TIMESTAMP: <ISO8601 UTC>
[INFO] DEPLOYMENT_LANE: devops (gpt-5.3-codex-spark / codex2)
[INFO] BACKEND_TARGET: pphothidaen/horoconsultant-core-backend (SDK: docker)
[INFO] UI_TARGET: <verified-vercel-static-ui-url>
[INFO] RELEASE_SOURCE_COMMIT: <source_commit_sha>
[INFO] PACKAGING_COMMIT: <packaging_commit_sha>
[INFO] METADATA_PATH: project/release_metadata.json (sha256:<digest>)
[INFO] ROLLBACK_ANCHORS: hf_rev=<prior_hf_sha>, vercel_id=<prior_vercel_id>
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
