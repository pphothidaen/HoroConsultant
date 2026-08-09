# Default Orchestrator Router Design

## Goal

Make the project default agent act as the persistent orchestration entrypoint for
every new task: analyze the request, create a proportionate plan, delegate only
the relevant work to specialized AI agents, and synthesize verified results.

## Constraints

- Keep the `default` agent identifier because Codex uses it for the root agent
  and may continue to display `Main [default]`.
- Keep `orchestrator` as the named orchestration role and legacy routing target.
- Edit `.agents/agents/default/agent.json` only as the Codex compatibility
  source; generated `.codex/agents/default.toml` is never edited directly.
- Preserve existing user work in the dirty worktree.

## Design

The `default` agent becomes an explicit **Default Orchestrator Router**. Its
instructions will require these steps for incoming work:

1. Classify the request and determine whether delegation materially helps.
2. Create a scoped plan and assign each independent workstream to the matching
   specialist role.
3. Give every delegated agent distinct file or responsibility ownership.
4. Avoid unnecessary delegation, deployment, external messaging, or secret
   actions.
5. Review combined outputs and run relevant verification before reporting a
   result.

The named `orchestrator` role remains available for direct invocation. Legacy
`settings.json` already selects it as `default_agent`; no change is needed to
that setting.

## Files and Synchronization

- Update: `.agents/agents/default/agent.json`
- Generated: `.codex/agents/default.toml` via `python3 scripts/sync_codex_agents.py --sync`
- Validate: configuration tests and `python3 scripts/sync_codex_agents.py --check`

## Acceptance Criteria

- The legacy default definition explicitly requires planning, selective agent
  routing, isolated ownership, aggregation, and verification.
- Generated Codex TOML reflects the updated legacy definition.
- Existing project setting remains `default_agent = orchestrator`.
- Relevant tests and the read-only synchronization check pass.
