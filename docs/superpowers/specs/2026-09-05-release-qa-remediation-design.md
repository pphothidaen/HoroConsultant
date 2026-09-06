# Release QA Remediation Design

**Status**: Owner-approved design; written specification recorded
**Date**: 2026-09-05 (Asia/Bangkok)
**Sprint**: `SPRINT-RELEASE-QA-REMEDIATION-20260905`

## Objective

Restore a trustworthy local release candidate by resolving every reproducible deterministic repository failure disclosed by the 2026-09-05 aggregate preflight. Preserve authoritative production, security, release, and metaphysics contracts. Keep toolchain installation and all external release actions behind their existing gates.

## Chosen approach

Use contract-first sequential remediation. First reproduce and classify failures without source changes. Then create one bounded successor per proven failure cluster with exact writable paths, immutable baseline/provenance evidence, minimal implementation, focused verification, and a final full-suite gate.

This is preferred over bulk copying or changing expectations because the repository contains a large dirty candidate, generated mirrors, historical golden vectors, and security-sensitive Admin/gateway contracts. A release-scope waiver is also rejected because the current release workflow explicitly requires the full applicable QA preflight.

## Components and flow

1. **Failure inventory**
   - Start from the last full run (`102 failed, 4007 passed, 9 skipped, 36 errors`) and cached failed node IDs.
   - Re-run failures fail-fast with `python3 -m pytest -x --lf`, then use focused commands to separate persistent failures from stale cache, order dependence, platform behavior, and environmental setup errors.
   - Record node ID, command, exit status, fingerprint, affected paths, contract source, classification, and successor requirement in one sanitized inventory.

2. **Contract adjudication**
   - Use the newest repository evidence, current plan, release contract, implementation source, and Git provenance.
   - Classify each persistent result as source defect, configuration drift, stale test/golden, generated drift, environmental blocker, flaky external dependency, or domain/HITL conflict.
   - Never infer that a failing test is stale merely because current code disagrees with it.

3. **Bounded successors**
   - Governance/capacity parity: begin with the known mismatch between the four-alias full-capacity guard and the two-alias config. Repair only after a focused immutable failure proves the config drift.
   - Ecosystem/generator parity: verify after the already-authorized local account-profile synchronization. If still failing, mutate canonical `.agents/agents/*/agent.json` or generator sources only; never edit `.codex/agents/*.toml` manually.
   - UI mirror and browser error safety: determine the canonical static bytes from deployment and Git provenance, restore exact mirror parity, and preserve the safe structured error contract in both app bundles.
   - Gateway/workflow/report contracts: isolate stale golden/report artifacts from production defects before any mutation.
   - Domain engines: diagnose I Ching, Zi Wei, and other metaphysics-vector differences without changing source or golden expectations. Any domain behavior proposal reopens D9 and requires owner/HITL approval.
   - Swift broker: record compiler/SDK mismatch separately. Do not install or replace toolchains under this sprint.

4. **Verification ladder**
   - RED or negative-control evidence.
   - Focused test for the cluster.
   - Neighbouring contract/regression suite.
   - `pytest --lf` until no deterministic last-failed case remains.
   - Full `python3 -m pytest -v --ignore=project/kaggle_kernel`.
   - `python3 scripts/sync_ai_agent_ecosystem.py --check` after relevant canonical changes.
   - Repository secret scan and the release-specific QA/reviewer gates.

## Data and evidence

No application data model changes are planned. Each test-changing successor owns one closed `test-provenance-v1` manifest under `plans/test_provenance/`. Diagnostic and verification results live under `plans/evidence/release-qa-remediation-20260905/` and contain no secrets, raw provider streams, or invented runtime claims.

## Error handling and stop conditions

Stop the affected lane when evidence conflicts, an exact contract cannot be established, a test change would weaken security, a domain answer would change, generated output would need manual editing, or an external/toolchain action is required. Other independent local clusters may proceed only when their file ownership remains disjoint and their result cannot mask the blocker.

The sprint may report local deterministic remediation complete while the release stays `BLOCKED`; it may not claim full QA success unless the current collected suite exits 0.

## Ownership and recovery

Execution is sequential in the current shared dirty worktree. The controller preserves all pre-existing edits and assigns one editor to each exact path in successor tickets. Recovery is a path-scoped reversal of remediation-owned hunks or generated refresh from canonical sources; no reset, broad checkout, history rewrite, or user-work deletion is permitted.

## Explicit exclusions

- Installing or changing Swift/Xcode/toolchains.
- Reading or changing secrets, credentials, Keychain contents, or provider sessions.
- External provider execution, publishing, commit/push, deployment, tagging, or production rollback.
- Force push, alternate remote, target/platform substitution, or gate waiver.
- New features, broader routes, authentication relaxation, or metaphysics behavior/golden changes without a new approval.

## Success criteria

- Every persistent deterministic failure has an evidence-backed disposition and exact owner.
- Every implemented correction passes its focused and neighbouring regression suites.
- No test assertion, authorization boundary, release identity, or negative control is weakened.
- The full collected suite exits 0 before `TICKET-RELEASE-002` can become DONE.
- Ecosystem sync check and secret scan pass before release review.
- Any remaining toolchain/domain/external blocker is recorded accurately and prevents a false-green release claim.
