---
description: Mandate decomposing monolithic skills, agents, rules, hooks, and governance docs into single-responsibility specialist files when they grow too large or cover multiple domains.
paths:
  - ".agents/skills/**/SKILL.md"
  - ".agents/agents/**/*.md"
  - ".agents/agents/**/*.json"
  - ".antigravity/agents/*.agent"
  - ".agents/rules/*.md"
  - ".claude/rules/*.md"
  - ".claude/settings.json"
  - ".agents/hooks/*.py"
  - "AGENTS.md"
  - "CLAUDE.md"
---

# Specialist Decomposition Rule

When any skill, agent definition, rule, hook, or governance document becomes too long or needs deep specialist coverage, **create a new dedicated file** rather than expanding the existing one.

## Hard Size Limits

| Artifact | Limit | Action if Exceeded |
|---|---|---|
| Skill `description` field | 100 chars | Rewrite to be concise; specialist detail goes in body |
| Agent `description` | 120 chars | Trim; move detail to `system_prompt` |
| SKILL.md total content | 300 lines | Split into 2+ domain-specific skills |
| Agent `system_prompt` | 50 lines | Extract sub-responsibilities to dedicated agent |
| `.agents/rules/*.md` file | 80 lines + mixed concerns | Create `<NN+1>-<new-topic>.md` |
| `.claude/rules/*.md` file | 40 lines + mixed concerns | Create new scoped Claude rule |
| Hook script (`.py`) | 150 lines | Extract specialized guard script |

## When to Create a New Specialist Agent

Create a new agent definition when:
- A skill requires an agent persona with no overlap with existing agents.
- A domain (color design, security audit, MLOps, metaphysics sub-discipline) needs its own accountability boundary.
- An existing agent's `tools` list would exceed 5 entries by adding new domain tools.

Required files for a new agent:
```
.agents/agents/<name>/agent.md        ← workspace source
.agents/agents/<name>/agent.json      ← JSON config
.antigravity/agents/<name>.agent      ← AGY runtime
```
Then run: `python3 scripts/sync_ai_agent_ecosystem.py --sync`

## When to Create a New Specialist Skill

Create a new SKILL.md when:
- An existing skill is referenced by 3+ unrelated agents.
- A specialist capability needs its own reference tables, code recipes, or compliance checklists.
- Two domains within one skill could each stand alone (e.g., split `web-design` into `web-color-design` + `web-layout-system`).

## When to Create a New Rule

- New governance concern with no existing rule owner.
- Existing rule section grows beyond 60 lines of distinct policy.
- A domain team (UX, Security, MLOps) needs a scoped enforcement file.

## Enforcement

- `orchestrator`: validates before any SDLC phase begins.
- `business_analyst`: audits in Phase 2 Skill & Agent Governance.
- `code_reviewer`: checks sizes in pre-deploy audit.
- `python3 scripts/sync_ai_agent_ecosystem.py --check` must pass after any split.
