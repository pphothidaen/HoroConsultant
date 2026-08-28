---
description: FastAPI and API contract rules for HoroConsultant endpoints.
paths:
  - "project/main.py"
  - "project/api_router.py"
  - "project/routers/**/*.py"
  - "project/api/**/*.py"
---

# API Contract Rules

- Keep `/health` stable for deployment monitors. If a canonical backend changes, update CI, synthetic monitoring, and release handoff docs in the same change.
- Preserve backward-compatible response shapes unless the project task explicitly authorizes a breaking API change.
- Validate input at the router boundary and keep deterministic metaphysics calculations in core modules, not route handlers.
- Do not log secrets, bearer tokens, birth data payloads, or raw user profile data.
- For endpoint changes, add or update contract tests in `project/tests/`.
