# Rule 13: AI Agent Ecosystem Always-Sync

## Purpose

Keep HoroConsultant agent definitions synchronized across Claude Code, ChatGPT/OpenAI Codex, Gemini/Google AGY, Hermes, AGY Subagent, and thClaws CLI.

## Required command

Run this read-only gate after any change to agent definitions, skills, rules, routing config, or global AI-agent context:

```bash
python3 scripts/sync_ai_agent_ecosystem.py --check
```

Run this write sync only after intentionally changing source agent definitions or skills:

```bash
python3 scripts/sync_ai_agent_ecosystem.py --sync
```

## Ownership boundaries

- Canonical `.agents/` definitions (`.agents/agents/`, `.agents/skills/`, `.agents/config/`) are the sole repository authority.
- Generated provider mirrors (`.codex/`, `.claude/`, `.agy/`, `.antigravity/`) and filesystem mtimes are NEVER authority; any mirror discrepancy is drift, not authority.
- Every lane dispatch MUST bind: ticket ID, lane ID, approved-context digest, role, permitted actions, all touched paths, and the context resolver result (`scripts/resolve_agent_context.py`).
- `.claude/settings.json` owns Claude Code hard hooks.
- `.claude/rules/*.md` owns Claude path-scoped behavior.
- `.agents/config/gemini_parity.yaml`, `scripts/hermes_agy_router.py`, and `scripts/hermes_sdlc_runner.sh` own Hermes/Gemini/AGY routing.
- `scripts/run_universal_bridge.py` and `scripts/run_thclaws_bridge.py` own thClaws/hybrid bridge integration.

## Completion gate

Do not mark agent governance work complete until:

- `python3 scripts/sync_ai_agent_ecosystem.py --check` passes;
- `python3 -m pytest -q project/tests/test_ai_agent_ecosystem_sync.py project/tests/test_claude_governance.py` passes;
- `python3 project/core/code_reviewer.py --scan-secrets` passes.
