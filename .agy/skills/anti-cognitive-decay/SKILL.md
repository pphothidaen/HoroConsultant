---
name: anti-cognitive-decay
description: Monitor context usage, generate HANDOFF.md memory compaction snapshots, and execute context reset.
argument-hint: "[snapshot-reason]"
disable-model-invocation: false
user-invocable: true
allowed-tools: [Bash, Read, Write]
model: sonnet
context: fork
---

# Anti-Cognitive Decay — Memory Compaction & Handoff Protocol

Preserves operational precision and prevents token degradation across extended development sessions.

## Threshold & Trigger Conditions
- Trigger when session context crosses **40% - 50%** consumption.
- Trigger when task complexity transitions across major architectural boundaries.

## Compaction Procedure

1. **Audit Current State**:
   - Verify uncommitted changes: `git status --short`
   - Review active work breakdown in `PROJECT_TASKS.md` or ticket tracker.

2. **Generate `HANDOFF.md`**:
   Write a structured handoff document in the root directory covering:
   - **Current State & WBS Checklist**: Completed vs. pending items.
   - **Architectural Decisions & Contracts**: Schema modifications, data structures, invariants.
   - **Negative Knowledge & Gotchas**: Failed approaches, error logs, and paths to avoid.
   - **Working Tree Delta**: Active branch, uncommitted diffs, and exact modified file list.

3. **Output Rehydration Command**:
   Provide the single command required for the fresh instance to rehydrate context:
   ```bash
   git diff --stat $(git merge-base main HEAD)
   ```

4. **Instruct Context Clear**:
   Notify the operator to execute `/clear` or `/reset` in the AGY CLI prompt.

---

## Gotchas

- **Gotcha 1 (Oversized Handoff)**: Writing multi-megabyte logs into `HANDOFF.md` defeats compaction.  
  *Workaround*: Summarize error traces in under 10 lines with root cause analysis.
- **Gotcha 2 (Unsaved Worktree)**: Executing `/clear` without committing or documenting modified files.  
  *Workaround*: Ensure all touched files are documented with `git status --short` in `HANDOFF.md`.
