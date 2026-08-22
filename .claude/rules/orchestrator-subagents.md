---
description: Sub-agent delegation and result collection rules.
paths:
  - "AGENTS.md"
  - "CLAUDE.md"
  - ".claude/**/*"
  - ".agents/**/*.md"
  - ".agents/agents/**/*.json"
  - ".agents/skills/**/SKILL.md"
  - "PROJECT_TASKS.md"
  - "plans/**/*.md"
---

# Orchestrator and Sub-Agent Rules

- Decompose broad requests into bounded sub-agent tasks with objective, ownership, boundaries, expected evidence, and stop condition.
- Keep file ownership isolated. If multiple agents need the same file, assign one editor and make the others read-only reviewers.
- Include this handoff sentence in every delegated task: `You are not alone in the codebase; do not revert edits made by others. Work only within your assigned ownership and adapt to visible changes from other agents.`
- Sub-agents must return: `Status`, `Scope owned`, `Evidence`, `Findings`, `Changed files`, `Residual risk`, and `Recommended next action`.
- Root orchestrator remains accountable for final user-facing synthesis and cannot close a parent task until delegated items are `DONE` or explicitly `BLOCKED` with HITL action.
