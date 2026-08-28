---
description: Secret hygiene, deployment, and cloud operation rules.
paths:
  - ".github/workflows/**/*"
  - "scripts/**/*"
  - "project/core/config.py"
  - "docs/*RELEASE*"
  - "docs/*HANDOFF*"
---

# Secrets and DevOps Rules

- Treat any secret printed in a terminal, CI log, or chat as compromised. Revoke or rotate it before reuse.
- Prefer Doppler as the first-priority secret store, then platform stores such as GitHub Actions or cloud-native secret stores.
- Do not read `.env`, credential files, keychain exports, or provider config files. Ask the human operator to confirm by secret name, not value.
- Do not run production-impacting deploys, secret rotations, or public ingress changes unless the user authorized the exact action class and target.
- Report deployment evidence with workflow run id, environment, URL, status code, and timestamp.
