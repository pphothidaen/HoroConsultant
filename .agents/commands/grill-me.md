---
description: Run fail-closed 9-dimension requirement intake before planning or implementation.
argument-hint: "<task or change request>"
---

# Grill Me

Treat `$ARGUMENTS` as the raw request. Read and follow
`.agents/skills/requirement-grill-gate/SKILL.md` completely.

## Preflight

1. If `$ARGUMENTS` is empty, ask exactly one question: "What outcome should
   `/grill-me` define?" Then stop and wait.
2. Auto-scan only relevant repository context and applicable instructions.
3. Preserve the user's stated scope, exclusions, authority, and existing dirty
   worktree changes.

## Interview

1. Assess all nine dimensions and auto-fill answers supported by current
   evidence as `[AUTO]` with source paths.
2. Queue unresolved CRITICAL ambiguities first.
3. Ask exactly one question per interaction. Never bundle questions or treat
   silence as a waiver.
4. Recompute the gate after each answer until it reaches a terminal state.

## Decision and output

Return the skill's `GRILL REPORT` contract with exactly one state:
`APPROVED`, `WAIVED`, or `BLOCKED`.

- `APPROVED` and `WAIVED`: name the next already-authorized phase, then stop.
- `BLOCKED`: include the current blockers, ask at most the next single
  question, then stop and wait.
- Do not plan, implement, delegate implementation, or mutate repository task
  artifacts as part of this command unless the current request explicitly
  authorizes that artifact.
