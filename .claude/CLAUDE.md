# HoroConsultant Claude Code Context

Use this file as the short global context for Claude Code. Detailed rules live in `.claude/rules/*.md`; hard safety checks live in `.claude/settings.json` hooks.

## Operating priorities

1. Preserve secrets: never read `.env`, credential files, tokens, keychain exports, or cloud provider config files.
2. Preserve user work: inspect `git status` before edits and do not revert unrelated changes.
3. Preserve generated boundaries: `.codex/agents/*.toml` is generated output; update legacy sources and run sync scripts instead.
4. Preserve release truth: do not claim production completion without CI, deployment, and live endpoint evidence.
5. Preserve deterministic quality: run targeted tests for scoped changes and the safety reviewer before release claims.

## Agent orchestration

- Use sub-agents only for bounded work with isolated ownership.
- Root orchestrator owns final synthesis, HITL escalation, and task closure.
- Use the report format from `.claude/rules/orchestrator-subagents.md` for every delegated result.

## Local commands

```bash
python3 -m pytest -q
python3 project/core/code_reviewer.py --scan-secrets
python3 project/core/code_reviewer.py --review --use-python
python3 scripts/sync_codex_agents.py --check
```
