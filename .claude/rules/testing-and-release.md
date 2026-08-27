---
description: Test, CI, and release verification rules.
paths:
  - "project/tests/**/*.py"
  - "tests/**/*.py"
  - ".github/workflows/**/*.yml"
  - ".github/workflows/**/*.yaml"
  - "scripts/**/*"
  - "pytest.ini"
---

# Testing and Release Rules

- Do not claim release completion from local-only results when GitHub Actions, cloud deployment, or live endpoint verification is still pending.
- Gate live remote tests behind explicit opt-in environment variables so normal CI remains deterministic.
- Never fix tests by removing assertions, swallowing exceptions, or replacing real checks with dummy fallbacks.
- Before source coding, commit a test-only `test-provenance-v1` baseline with
  red or negative-control evidence and exact test hashes. Do not open the
  source lane until it is `TEST_BASELINE_VERIFIED`.
- Never edit a frozen test from the source lane. Stop and create a separately
  reviewed, test-only superseding baseline; reconstructed history remains
  `NON_TDD_RECONSTRUCTED` and is not test-first proof.
- Local hooks must be read-only. Required CI and the final Git-history review
  enforce ancestry, hashes, separated commits, and `Test-Baseline` trailers.
- Include failure tails or exact run ids when reporting CI failures.
- Before release claims, run the project safety reviewer or explain the exact blocker that prevents it.
