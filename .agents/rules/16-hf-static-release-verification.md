# Rule 16 — HF Docker Backend + Vercel UI Release Verification

## Purpose

Prevent a release claim when the HF Docker backend, Vercel static UI, provenance,
health, version identity, visual evidence, or rollback record is incomplete.
The legacy filename and skill identifier remain for compatibility; they do not
authorize a Static SDK publish to the backend Space.

## Mandatory release gate

1. Use SDK-aware health verification for the HF backend with Docker `/health`.
   Verify the separately recorded Vercel UI root and version surface; neither
   target may substitute for the other.
2. Run fail-closed exact-cardinality checks for the expected version and
   immutable `release_source_commit` on every required backend and UI identity
   surface. Missing, duplicate, composite, stale, malformed, or unreachable
   evidence is a failure.
3. Run publisher and governance regressions, then the five canonical viewport
   visual audit against the verified Vercel UI target.
4. Treat non-zero commands, stale reports, missing screenshots, network errors,
   and unresolved indeterminate findings as blockers. A manual reviewer may
   resolve an indeterminate only by recording viewport, finding, reviewer,
   decision, and timestamp. Never make a release claim on failure.

## Required commands

```bash
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk docker
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk docker
python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py
python3 scripts/run_visual_layout_audit.py --url <verified-vercel-static-ui-url> --scenario v3-consensus --no-server
```

## Provenance, evidence, and rollback

Committed release metadata is the provenance authority. It records the metadata
path and SHA-256 digest, version, `release_source_commit`, source revision, and
later `packaging_commit`; prove the source commit is an ancestor of the packaging
commit. `packaging_commit` is evidence-only and never replaces deployed identity.
No environment value, CLI default, runtime `HEAD`, or external override may
weaken this contract.

Evidence identifies the Docker backend target/revision, verified Vercel UI
target/revision, command outcomes, exact-cardinality checks, reports/screenshots,
timestamp, owners, and prior revisions for rollback. Receipt, WorkResult, and
public outcome are validated in-process with stdout/stderr elided; they are not
an independently portable or offline evidence bundle. Never restore or log raw
provider streams.

Rollback requires the exact release-commit revert plus the recorded prior HF
Docker and Vercel production revisions. Any unavailable or conflicting rollback
identity is a release blocker.

## Ownership and generated boundary

- `devops`: Docker backend health/version, release evidence, and rollback record.
- `qa_tester`: regressions, Vercel UI E2E/visual audit, screenshots, strict failures.
- `code_reviewer`: blocks failed, absent, stale, indeterminate, or inconsistent evidence.
- `orchestrator`: final decision after green DevOps, QA, and reviewer evidence.

Generated compatibility outputs exist only for synchronization; never hand-edit them.
After intentional rule or skill changes, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`, then require
`python3 scripts/sync_ai_agent_ecosystem.py --check` to pass.

## Completion gate

A release is `READY_FOR_PROD` only when every Docker backend and Vercel UI gate,
exact-cardinality check, five canonical viewport artifact, rollback record, and
Code Reviewer verdict is green. Otherwise report `[ERROR] BLOCKED`.
