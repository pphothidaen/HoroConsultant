---
name: qa-e2e-testing
description: Run fail-closed regression, API/UI contract, and Docker/Vercel release verification.
---

# QA and E2E Testing

Use this skill for regression, API/UI contract, E2E, visual, and production
release verification. Production is the HF Docker backend plus a separately
verified Vercel static UI. A legacy script or hostname does not authorize a
Static publish to the backend Space, Azure public routing, or Fly deployment.

## Test sequence

1. Run the bounded owned regression matrix after source freeze, then full
   repository QA when its release ticket is unlocked:

   ```bash
   python3 -m pytest -v --ignore=project/kaggle_kernel
   ```

2. Run the local UI/API contract suite:

   ```bash
   python3 scripts/run_button_regression.py
   ```

3. Before production E2E, require DevOps evidence that the exact HF backend is
   Docker, healthy, provenance-bound, and version-verified. Record the Vercel UI
   target from the same release metadata/evidence; do not infer it from a legacy
   HF Static hostname.

4. Run Docker publisher/governance regressions and the five-viewport audit on
   the verified Vercel UI target:

   ```bash
   python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py
   python3 scripts/run_visual_layout_audit.py --url <verified-vercel-static-ui-url> --scenario v3-consensus --no-server
   ```

5. Capture only current machine-readable reports, five canonical viewport
   screenshots, and concise failure evidence. A network error, missing report,
   stale evidence, or unresolved indeterminate result is `[ERROR] BLOCKED`.

## QA rules

- Test the backend and UI as separate targets: Docker `/health` and provenance
  for the HF backend; UI version, browser console/network behavior, E2E, and
  visuals for Vercel.
- Do not comment out assertions, delete tests, add dummy fallbacks, or swallow
  exceptions. Return root-cause evidence to the owning editor.
- Validate real model inference where in scope; do not accept static-template
  substitution as a successful AI response.
- Public ExecutionOutcome data is validated in-process with stdout/stderr
  elided. It is not independent portable/offline release evidence; never log or
  restore raw provider streams.
- Report with concise `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]` lines only.

## Release stop condition

No `READY_FOR_PROD` claim is available until regression, Docker backend
health/version, Vercel UI identity/E2E/visual evidence, secret scan, package
dry-run, and reviewer verdict all pass. On failure, return only the owning fix
ticket and preserve the rollback evidence.
