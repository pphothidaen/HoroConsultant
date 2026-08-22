# HoroConsultant — Codex Instructions

## Codex compatibility boundary

- `.agents/` and `.antigravity/` remain the legacy multi-agent configuration. Do not rename, delete, or manually rewrite those definitions for Codex work.
- `.agents/skills/*/SKILL.md` are native Codex skills and are discovered from this repository.
- `.agents/agents/*/agent.json` is the compatibility-layer source. `.codex/agents/*.toml` is generated output and must not be edited manually.
- After changing legacy agent definitions, skills, Claude rules, or routing config, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`. Use `python3 scripts/sync_ai_agent_ecosystem.py --check` for read-only validation.

## Working with Codex subagents

- Select a role from `.codex/agents/` only when its description matches the delegated task.
- Generated role prompts preserve legacy responsibilities. Provider/model allocations inside those legacy prompts are historical context; each Codex subagent inherits the active Codex model.
- Keep parallel work isolated by file ownership. Do not assign concurrent agents to edit the same file.

## Project safeguards

- Apply the relevant `.agents/rules/` documents and skills for the task at hand.
- Kaggle synchronization, deployment, publishing, external messages, and secret operations are opt-in: perform them only when the user requests them or the current task requires them.
- Before release claims, run the relevant tests and `python3 scripts/sync_ai_agent_ecosystem.py --check`.
