---
name: hf-static-release-verification
description: Enforce fail-closed HF Static health, version, visual, and evidence release gates.
owner: devops
responsible_agents:
  - devops
  - qa_tester
  - code_reviewer
  - orchestrator
---

# HF Static Release Verification

Use this skill for every HF Static production publish, post-deploy check, release
approval, or investigation of stale, duplicate, or composite frontend versions.

## Owners

- `devops` runs SDK-aware health and exact-cardinality version verification.
- `qa_tester` runs publisher regression tests and the live five-viewport visual
  audit, then captures the reports and screenshots.
- `code_reviewer` blocks release when any result is failing, missing, stale, or
  indeterminate.
- `orchestrator` makes the final release decision from the collected evidence.

## Workflow

1. Run the Static SDK health gate:

   ```bash
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --check-health --sdk static
   ```

2. Run the fail-closed live identity gate:

   ```bash
   python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --verify-version --sdk static
   ```

   Require the expected version and commit exactly once in each required identity
   location. Treat missing, duplicate, composite, stale, malformed, unreachable,
   or indeterminate values as failures.

3. Run regression and governance tests:

   ```bash
   python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py
   ```

4. Audit the production V3 Consensus screen:

   ```bash
   python3 scripts/run_visual_layout_audit.py --url https://pphothidaen-horoconsultant-core-backend.static.hf.space --scenario v3-consensus --no-server
   ```

5. Confirm `project/tests/artifacts/visual_layout_report.json`, the post-deploy
   evidence artifact, and five files under
   `project/tests/screenshots/visual_audit/` are current and green.

   An indeterminate gradient is unresolved by default. It may pass only after a
   manual reviewer records the viewport, finding, reviewer, decision, and timestamp
   in the evidence artifact.

6. Stop on any non-zero command, incomplete evidence, or unresolved indeterminate
   finding. Do not publish or claim a successful release. Report `[ERROR] BLOCKED`
   to the Orchestrator.

Use only ASCII log tags: `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.

## Standard report

```text
[INFO] Target: <space-id>
[INFO] SDK: static
[INFO] Revision: <revision>
[INFO] Expected version: <version>
[INFO] Expected commit: <commit>
[OK|ERROR] Health gate: <result>
[OK|ERROR] Exact-cardinality version gate: <result>
[OK|ERROR] Publisher tests: <result>
[OK|ERROR] Visual audit: <result>
[INFO] Visual report: <path>
[INFO] Screenshots: <five paths>
[INFO] Manual gradient reviews: <resolved decisions or none>
[INFO] Evidence artifact: <path>
[INFO] Owners: devops, qa_tester, code_reviewer, orchestrator
[OK] READY_FOR_PROD
```

Emit `[ERROR] BLOCKED` instead of `[OK] READY_FOR_PROD` whenever any required
field, command, artifact, screenshot, or reviewer decision is not green.
