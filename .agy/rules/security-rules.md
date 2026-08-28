---
description: 2-Tier secrets policy, zero credential leakage, and sandboxed execution boundaries.
paths: "**/*"
---

# Security, Privacy & Secret Governance

## 2-Tier Priority Secrets Policy
- Tier 1: System Environment Variables (local process memory, `.env`, Doppler CLI).
- Tier 2: Encrypted Vault / Cloud Key Management.
- Never hardcode API keys, secrets, or bearer tokens into code, tests, or documentation.

<important if="handling_credentials">
- Strictly forbid reading `.env` files in tool commands or displaying secrets in plaintext output.
- All subprocess execution logs must sanitize auth headers and bearer tokens before streaming.
- Sub-agents must execute with least-privilege toolsets.
</important>
