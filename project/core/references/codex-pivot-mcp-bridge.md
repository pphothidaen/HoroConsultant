---
name: codex-pivot-mcp-reference
description: "Codex CLI MCP Bridge session reference."
version: 1.0.0
---
# Codex Pivot — MCP Bridge Reference
From session: `codexPivot/IDEA.md`, build at `~/codex-with-chatgpt`, tunnel PID 51746 → 20309.

## Verified workflow (6 steps)
1. Env: macOS 26.6.2, Node 26.7.0
2. Build: `pnpm build` → `dist/cli/index.js`
3. Skill: `~/.codex/skills/codex-with-chatgpt/SKILL.md`
4. Tunnel: `cloudflared` (Quick Tunnel worked; named blocked — `cert.pem` missing)
5. Connector: ChatGPT Web `Codex Native2` (Auth=None, Allow all)
6. `.env` vars: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_AI_TOKEN`

## Blocker recorded
Named tunnel (`cloudflared tunnel create`) fails: `Cannot determine default origin certificate path`. Fix: provide cert or stay on Quick Tunnel.

## Pre-commit
Repo uses `test_provenance` — separate source/test commits.
