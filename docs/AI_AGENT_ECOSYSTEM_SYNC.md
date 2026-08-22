# AI Agent Ecosystem Sync

This project keeps one coordinated agent ecosystem for Claude Code, ChatGPT/OpenAI Codex, Gemini/Google AGY, Hermes, AGY Subagent, and thClaws CLI.

## Source and target layers

| Platform | Repo surface | Purpose |
| --- | --- | --- |
| Claude Code | `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/rules/*.md` | Hard hooks, short global context, path-scoped rules |
| ChatGPT/OpenAI Codex | `.codex/agents/*.toml`, `AGENTS.md` | Native Codex sub-agent roles generated from legacy source |
| Gemini / Google AGY | `.antigravity/agents/*.agent`, `.agents/agents/*` | Legacy/source role definitions and workspace agent specs |
| Hermes | `scripts/hermes_agy_router.py`, `scripts/hermes_sdlc_runner.sh`, `.agents/config/gemini_parity.yaml` | Task routing, quota-aware AGY fallback, Gemini parity |
| AGY Subagent | `.antigravity/agents/*`, `.agents/config/gemini_parity.yaml` | Account/complexity routing and sub-agent role behavior |
| thClaws CLI | `scripts/run_universal_bridge.py`, `scripts/run_thclaws_bridge.py` | Local/hybrid metaphysics bridge execution |

## Always-sync command

Use read-only validation before release claims, PRs, or after agent/rule edits:

```bash
python3 scripts/sync_ai_agent_ecosystem.py --check
```

Use write synchronization after changing legacy agent definitions or skills:

```bash
python3 scripts/sync_ai_agent_ecosystem.py --sync
```

The umbrella script runs these gates:

- required platform files exist;
- `settings.json`, `.mcp.json`, and `.claude/settings.json` parse;
- Claude Code `PreToolUse` guard is registered;
- `.claude/rules/*.md` files have `description` and `paths` frontmatter;
- core Codex roles exist;
- Hermes/AGY/thClaws routing markers exist;
- `scripts/sync_sdlc_agents.py --check --use-python` passes;
- `scripts/sync_codex_agents.py --check` passes.

## Required change order

1. Edit source definitions first:
   - `.antigravity/agents/*.agent` for legacy/AGY roles;
   - `.agents/skills/*/SKILL.md` for repository skills;
   - `.claude/rules/*.md` for Claude path-scoped rules.
2. Run:

   ```bash
   python3 scripts/sync_ai_agent_ecosystem.py --sync
   ```

3. Run targeted tests:

   ```bash
   python3 -m pytest -q project/tests/test_ai_agent_ecosystem_sync.py project/tests/test_claude_governance.py
   ```

4. Run secret scan before release or push:

   ```bash
   python3 project/core/code_reviewer.py --scan-secrets
   ```

## Human-in-loop rules

- Do not read `.env`, key files, provider credential stores, or token output commands.
- If any token appears in terminal output, CI logs, chat, or screenshots, treat it as leaked and rotate before reuse.
- Production deploys, public ingress changes, secret rotations, and production browser tests require explicit target authorization.
