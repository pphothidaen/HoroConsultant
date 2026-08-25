---
description: Govern multi-account agent routing, quota evidence, retries, and HITL closure.
paths:
  - "PROJECT_TASKS.md"
  - "plans/**"
  - ".agents/rules/**"
  - ".agents/skills/**"
  - "docs/templates/**"
  - "scripts/multiagent_prompt_command.py"
---

# Multi-account orchestration

Use one editor per file; assign shared-file reviewers read-only. Every dispatch
must name objective, ownership, boundaries, evidence, and stop condition and
must include the non-reversion warning. An alias, route, model, or rendered
command is routing intent, not execution proof; require child result and safe
provider/session telemetry. Never print or store secrets.

Below 10% quota, stop broad work, update `TICKET-META-008`, preserve a safe
resume command, and run the quota guard. Retry only bounded actionable failures;
after three consecutive failures, or immediately for credentials, permissions,
billing, production mutation, ownership conflict, or high-impact judgment,
return `NEEDS_HITL`. Close only with attached evidence and synchronized mirrors.
