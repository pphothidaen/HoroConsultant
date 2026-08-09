# Codex Agent Compatibility Layer Design

## Goal

Enable Codex subagent workflows without changing the existing Antigravity-compatible `.agents/` and `.antigravity/` definitions.

## Context

The repository already has 16 role definitions under `.agents/agents/*/agent.json` and seven Codex-compatible skills under `.agents/skills/*/SKILL.md`. Codex discovers the skills natively, but it requires custom subagents as TOML files in `.codex/agents/` and reads project instructions from a root `AGENTS.md`.

## Chosen approach

Use a generated compatibility layer.

1. Keep `.agents/agents/*/agent.json` as the source used by this migration. Do not rename, delete, or rewrite any legacy definition.
2. Add `scripts/sync_codex_agents.py`. It reads every legacy JSON definition and writes one Codex TOML file per role to `.codex/agents/`.
3. Add `--check` mode so CI and developers can detect stale generated TOML files without writing.
4. Generate only portable Codex fields: `name`, `description`, and `developer_instructions`. Do not copy legacy Gemini, Claude, or DeepSeek model names; Codex agents inherit the active Codex model.
5. Preserve each legacy `system_prompt` verbatim in `developer_instructions`. Legacy skill names are recorded as workflow guidance; the two historical `.skill` suffixes are normalized only in generated guidance, leaving the source untouched.
6. Add a concise root `AGENTS.md` that explains the compatibility boundary and prevents generated files from becoming an editing source of truth.
7. Update `.agents/AGENTS.md`, `PROJECT_TASKS.md`, and `plans/plan.md` to document the added Codex target and verification command.

## Alternatives considered

### Copy and hand-maintain 16 TOML files

This is quick initially but silently diverges from the Antigravity source. It does not meet the backward-compatible requirement.

### Replace `.agents/` with Codex TOML

This would break Antigravity synchronization and removes existing editor/CLI compatibility.

### Generated compatibility layer (chosen)

This adds one small standard-library Python synchronizer, keeps the old format authoritative, and gives Codex a native configuration directory.

## Data flow

```text
.antigravity/agents/*.agent
          |
          v
scripts/sync_sdlc_agents.py
          |
          v
.agents/agents/<role>/agent.json  -- source for Codex compatibility layer
          |
          v
scripts/sync_codex_agents.py --sync / --check
          |
          v
.codex/agents/<role>.toml  -- Codex custom subagent definitions
```

The existing Antigravity synchronizer is not modified. When legacy roles change, run the existing synchronizer first, then run the Codex synchronizer.

## Error handling and validation

- A source definition must have non-empty string values for `name`, `description`, and `system_prompt`.
- A duplicate role name or malformed JSON causes a non-zero exit with an ASCII `[ERROR]` message. Historical `.skill` suffixes are normalized only in generated skill guidance.
- `--check` compares expected output byte-for-byte and reports missing or stale TOML files without writing.
- Tests parse generated TOML with Python `tomllib`, validate all source role names, verify legacy prompt preservation, and verify stale-file detection.

## Acceptance criteria

- All 16 existing roles produce valid `.codex/agents/*.toml` files.
- `.agents/` and `.antigravity/` retain their current formats and synchronization behavior.
- `python3 scripts/sync_codex_agents.py --check` succeeds after generation.
- The targeted Python test suite passes.
- Root `AGENTS.md` explains that generated Codex files must be regenerated rather than edited manually.
