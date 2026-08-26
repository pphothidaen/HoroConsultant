---
name: hf-static-release-verification
description: Enforce fail-closed HF Docker backend and Vercel UI release gates.
owner: devops
responsible_agents:
  - devops
  - qa_tester
  - code_reviewer
  - orchestrator
---

# HF Docker Backend and Vercel UI Release Verification

Use this skill for a production publish, post-deploy check, release approval,
or stale identity investigation. The legacy directory and skill name remain for
compatibility only: the backend Space is Docker and the public static UI is
Vercel. Never publish a Static payload to the backend Space.

## Owners

- `devops` runs SDK-aware Docker backend health, version, rollback, and evidence gates.
- `qa_tester` runs publisher regressions plus Vercel UI E2E and five canonical viewport audit.
- `code_reviewer` blocks missing, stale, failing, or indeterminate evidence.
- `orchestrator` makes the final decision from the complete evidence bundle.

## Fail-closed workflow

1. Confirm the exact HF backend target, `--sdk docker`, a verified Vercel UI
   target, committed release metadata, and prior HF/Vercel revisions. Reject
   Azure, Fly, and Static-to-backend alternatives.
2. Verify Docker backend health and identity:

   ```bash
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk docker
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk docker
   ```

3. Require `release_source_commit` and expected version with fail-closed
   exact-cardinality in every required backend and Vercel UI identity surface.
   Missing, duplicate, composite, stale, malformed, unreachable, or unresolved
   indeterminate evidence fails the gate. `packaging_commit` is evidence-only.
4. Run publisher and governance regressions, then audit the verified Vercel UI:

   ```bash
   python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py
   python3 scripts/run_visual_layout_audit.py --url <verified-vercel-static-ui-url> --scenario v3-consensus --no-server
   ```

5. Confirm the current report, post-deploy evidence, and five canonical viewport
   screenshots. An unresolved indeterminate finding blocks release unless a manual
   reviewer records viewport, finding, reviewer, decision, and timestamp.
6. Stop on every non-zero command or incomplete evidence. Do not publish or make
   a release claim on failure; report `[ERROR] BLOCKED`.

## Provenance and evidence boundary

Committed metadata supplies its path, SHA-256 digest, version,
`release_source_commit`, source revision, and later `packaging_commit`; prove the
source commit is an ancestor of the packaging commit. No environment value, CLI
default, runtime `HEAD`, or external override may replace either identity.

Evidence names backend/UI targets and revisions, command outcomes, exact-cardinality
checks, report/screenshots, timestamp, owners, and rollback revisions. Receipt,
WorkResult, and public ExecutionOutcome are validated in-process with stdout/stderr
elided; they are not independently portable/offline evidence. Never restore or
log raw provider streams.

## Rollback and report

Rollback uses the exact release-commit revert and recorded prior HF Docker and
Vercel production revisions. If any rollback identity is unavailable, block the
release rather than switching platforms.

```text
[INFO] Backend target: <space-id>
[INFO] Backend SDK: docker
[INFO] Vercel UI target: <verified-url>
[INFO] Release source commit: <release_source_commit>
[INFO] Packaging commit: <packaging_commit>
[INFO] Source metadata: <path> sha256=<digest>
[OK|ERROR] Docker health and version: <result>
[OK|ERROR] Vercel identity, E2E, and visual audit: <result>
[OK|ERROR] Publisher and governance tests: <result>
[WARNING] Residuals: <none or exact non-blocking residual>
[INFO] Rollback revisions: <hf-docker>, <vercel>
[INFO] Outcome boundary: validated-in-process; streams elided; not portable
[OK] READY_FOR_PROD
```

Emit `[ERROR] BLOCKED` instead of `[OK] READY_FOR_PROD` whenever any required
field, command, artifact, screenshot, reviewer decision, or rollback record is
not green. Never hand-edit generated compatibility outputs; run ecosystem sync.
