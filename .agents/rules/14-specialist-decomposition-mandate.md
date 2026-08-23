# Rule 14: Specialist Decomposition Mandate — Skill, Agent, Rule, Hook & Governance Splitting

## Purpose

Prevent monolithic, bloated, or overly generic definitions that reduce agent effectiveness. When any artifact — skill, agent definition, rule, hook, or governance document — becomes too long, too broad, or needs deep specialist knowledge, it **must** be decomposed into dedicated, single-responsibility files before implementation proceeds.

---

## Triggers: When to Split and Create New Files

### 1. Skill / SKILL.md
Split or create a new dedicated skill file when ANY of the following is true:
- The `description` field would exceed **100 characters** (hard limit for context-budget compliance).
- A single SKILL.md covers more than **2 distinct technical domains** (e.g., both color theory AND BaZi calculation).
- The instruction content exceeds **300 lines**.
- A specialist capability (e.g., WCAG contrast, Five Elements color mapping, APCA) requires reference tables, recipes, or code blocks that justify a dedicated reference file.
- The skill is being reused across 3 or more agent types — extract to standalone skill.

**Action**: Create a new `.agents/skills/<specialist-name>/SKILL.md` and link it to the narrowly scoped agent(s).

### 2. Agent Definition (agent.md / agent.json / .agent)
Split or create a new specialist agent when ANY of the following is true:
- An existing agent handles more than **one primary delivery role** (e.g., both design AND code review).
- A specialist domain (metaphysics, color theory, security audit, MLOps) needs deeper responsibility coverage than the generic role allows.
- The `system_prompt` exceeds **50 lines** or mixes multiple unrelated concerns.
- A new expert persona is needed that has **no overlap** with existing agents' primary tools and responsibilities.

**Action**: Create a new agent definition set:
```
.agents/agents/<agent-name>/agent.md
.agents/agents/<agent-name>/agent.json
.antigravity/agents/<agent-name>.agent
```
Then run: `python3 scripts/sync_ai_agent_ecosystem.py --sync`

### 3. Rule File (.agents/rules/*.md)
Split or create a new rule file when ANY of the following is true:
- An existing rule file covers more than **one governance concern** (e.g., both secrets AND infrastructure constraints).
- A rule exceeds **80 lines** with distinct sub-sections that would function independently.
- A new enforcement domain emerges that has no existing rule file (e.g., color-system governance, specialist decomposition itself).
- A section in an existing rule is referenced from 3+ other rules — extract it to a standalone rule.

**Action**: Create `.agents/rules/<NN>-<topic>.md` with sequential numbering. Update `.agents/AGENTS.md` skill/rule catalog.

### 4. Claude Code Rule (.claude/rules/*.md)
Split or create a new Claude rule when:
- The rule's `paths` frontmatter covers 3+ unrelated directory trees.
- Content exceeds **40 lines** with mixed domain concerns.
- A new Claude-specific behavioral boundary is needed that isn't covered by existing rules.

**Action**: Create `.claude/rules/<topic>.md` with YAML frontmatter (`description`, `paths`). Verify the `.claude/settings.json` PreToolUse hook still applies.

### 5. Hook (.agents/hooks/ / .claude/settings.json hooks)
Split or add a new hook when:
- A new **tool category** requires a pre/post execution check not covered by existing hooks.
- An existing hook script exceeds **150 lines** of logic — extract a new specialized guard script.
- A new security boundary (e.g., UI rendering, color token publishing) requires a dedicated guard.

**Action**: Add a new hook entry to `.claude/settings.json` `PreToolUse` / `PostToolUse` array. Create companion script in `.agents/hooks/<hook-name>.py`. Update `pre_tool_check.py` if it is the umbrella dispatcher.

### 6. Governance Document (AGENTS.md, CLAUDE.md, plans/plan.md)
Decompose a governance document when:
- A section grows to more than **60 lines** of distinct policy detail.
- The section would be consumed by a narrow audience (e.g., only DevOps or only UX agents).
- Referenced repeatedly from multiple rules or skills.

**Action**: Extract to `.agents/rules/<NN>-<topic>.md` (or `.claude/rules/<topic>.md`), then replace the original section with a one-line reference link.

---

## Decomposition Quality Checklist

Before declaring a new specialist artifact complete:
- [ ] Single responsibility: file covers exactly ONE domain or concern.
- [ ] Skill `description` ≤ 100 chars; agent `description` ≤ 120 chars.
- [ ] No copy-paste duplication with existing files; shared content extracted to a common rule.
- [ ] Agent `.agent` file includes `fallback_agent: orchestrator`.
- [ ] Skill YAML frontmatter has `name` and `description` fields.
- [ ] Rule has a clear `## Purpose` section and `## Completion Gate` (or `## Triggers`).
- [ ] Claude rule has valid YAML frontmatter with `description` and `paths`.
- [ ] `python3 scripts/sync_ai_agent_ecosystem.py --sync` passes **all** [OK] gates.

---

## Naming Conventions

| Artifact Type | Naming Pattern | Example |
|---|---|---|
| Specialist skill | `<domain>-<specialty>` | `web-color-design`, `bazi-solar-time` |
| Specialist agent | `<role>_<domain>` | `ux_ui_designer`, `security_auditor` |
| Agent rule | `<NN>-<concern>.md` | `14-specialist-decomposition-mandate.md` |
| Claude rule | `<concern>.md` | `color-system-governance.md` |
| Hook script | `<guard-name>.py` | `color-token-guard.py` |

---

## Enforcement

- This rule is enforced by the **`orchestrator`** before any SDLC phase begins.
- The **`business_analyst`** must audit artifact sizes during Phase 2 (Skill & Agent Governance).
- The **`code_reviewer`** must check for oversized definitions in pre-deploy audits.
- Violation of this rule (leaving monolithic definitions in place) is treated the same as dead-code violations under Rule 10 (Migration Dead-Code Cleanup Mandate).

---

## Completion Gate

This rule is satisfied when:
1. No skill SKILL.md `description` exceeds 100 chars.
2. No agent definition `system_prompt` covers more than one primary delivery role.
3. No rule file mixes more than one governance concern.
4. `python3 scripts/sync_ai_agent_ecosystem.py --check` passes all [OK].
5. This rule is referenced in `.agents/AGENTS.md` skill/rule catalog section.
