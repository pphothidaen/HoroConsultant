# Rule 11: Orchestrator Sub-Agent Delegation & Background Work Governance

## Purpose

This rule governs how the `orchestrator` distributes work to sub-agents, monitors background tasks, collects results, and prevents overlapping edits or unsafe external actions.

## Mandatory Delegation Controls

1. **Bounded Task Requirement**
   - Every sub-agent task must have a concrete objective, ownership boundary, expected evidence, and stop condition.
   - Vague instructions such as "continue everything" are not enough for sub-agent assignment; the orchestrator must decompose them first.

2. **File Ownership Isolation**
   - Do not assign concurrent agents to edit the same file or module.
   - If shared files such as `PROJECT_TASKS.md`, release handoff docs, or workflow files are involved, assign one editor and make other agents read-only reviewers.

3. **Non-Reversion Mandate**
   - Every delegated task must tell the sub-agent that other agents may be working in the same tree and that it must not revert user or peer changes.

4. **Evidence-First Result Collection**
   - Sub-agent outputs must include command results, artifact paths, workflow run ids, or exact file references.
   - The orchestrator must verify release and production claims against evidence before marking any gate `DONE`.

5. **External Mutation Authorization**
   - Sub-agents must not publish, deploy, rotate secrets, push commits, or run production-impacting actions unless the user or root orchestrator explicitly authorized that action class and target.
   - Authorization for investigation does not authorize deployment or secret propagation.

6. **Secret Handling**
   - Sub-agents must never print secret values.
   - If a command unexpectedly prints a secret, the secret is compromised. Stop using it, require rotation, and document only that leakage occurred without repeating the value.

7. **Background Monitoring**
   - Long-running workflows may be monitored by DevOps or QA sub-agents, but the root orchestrator remains responsible for user updates and final synthesis.
   - Poll at reasonable intervals and report only meaningful state changes: job started, job passed, job failed, blocker identified, or artifact produced.

8. **HITL Escalation**
   - Escalate to Human-in-the-Loop when progress requires a credential value, platform permission, production approval, external billing decision, or unresolved high-impact domain judgment.
   - Provide the human operator with the exact command, UI path, or decision needed, and wait for fresh evidence after completion.

## Required Sub-Agent Handoff Fields

Each sub-agent final response must include:

- `Status`: `DONE`, `BLOCKED`, or `NEEDS_HITL`.
- `Scope owned`: the files, systems, or evidence areas handled.
- `Evidence`: commands, logs, artifact paths, or run ids.
- `Findings`: concise conclusions.
- `Changed files`: exact paths, or `None`.
- `Residual risk`: known remaining risks or external dependencies.
- `Recommended next action`: the next concrete step.

## Completion Gate

The orchestrator may close a parent task only after all delegated items are either `DONE` with evidence or explicitly `BLOCKED` with a documented operator action. A parent release task cannot be closed from local checks alone when external CI, production deployment, or live endpoint verification remains pending.

## Claude Code Governance Layering

For Claude Code, distribute orchestration controls across three layers:

1. **Level 1 Hooks (`.claude/settings.json`)**
   - Use `PreToolUse` hooks for hard blocks before execution.
   - Block secret-file reads, plaintext token output, force push, `rm -rf`, hard resets, and unsafe destructive cleanup.

2. **Level 2 Rules (`.claude/rules/*.md`)**
   - Use frontmatter `paths` so task-specific rules load only for matching files.
   - Keep separate files for API, frontend, testing/release, secrets/devops, and orchestrator/sub-agent governance.

3. **Level 3 Global Context (`.claude/CLAUDE.md` or root `CLAUDE.md`)**
   - Keep global context short: project priorities, generated-file boundaries, release evidence requirements, and the sub-agent result format.
   - Do not place detailed implementation standards here when they can live in path-scoped rules.
