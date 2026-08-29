---
description: Frontend implementation rules for the production web UI.
paths:
  - "project/static/**/*"
  - "public/**/*"
  - "templates/**/*"
---

# Frontend Contract Rules

- Keep user-visible flows testable by selectors or stable text used in Playwright and regression tests.
- Do not hardcode production secrets, tokens, or private endpoints into static assets.
- Preserve the current Thai/English UX unless a task explicitly changes copy or locale behavior.
- When changing buttons, forms, or navigation, run or update the relevant web regression and Playwright checks.
- Keep generated version stamps from hooks intact; do not hand-edit them unless the release process requires it.
