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
- Include failure tails or exact run ids when reporting CI failures.
- Before release claims, run the project safety reviewer or explain the exact blocker that prevents it.
