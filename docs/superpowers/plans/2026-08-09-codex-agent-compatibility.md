# Codex Agent Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backward-compatible generator that turns the existing legacy agent definitions into native Codex subagent TOML files.

**Architecture:** `.agents/agents/*/agent.json` remains unchanged and authoritative for the compatibility layer. A standard-library Python synchronizer renders portable Codex TOML into `.codex/agents/`, while root `AGENTS.md` explains the target and generated-file boundary.

**Tech Stack:** Python 3.14 standard library (`argparse`, `json`, `pathlib`, `tomllib` for tests), pytest, TOML configuration.

> **Historical plan:** task-file references record the original plan context.
> `atomic_tasks.md` is the current operational task registry.

## Global Constraints

- Keep `.agents/` and `.antigravity/` valid for their current tooling.
- Do not copy legacy provider model names into Codex TOML.
- Emit ASCII status tags: `[OK]`, `[ERROR]`, `[WARNING]`, and `[INFO]`.
- Generated TOML must contain only Codex-compatible fields: `name`, `description`, and `developer_instructions`.
- Preserve each source `system_prompt` in generated developer instructions.

---

### Task 1: Define generator behavior with tests

**Files:**
- Create: `project/tests/test_sync_codex_agents.py`

**Interfaces:**
- Consumes: `scripts/sync_codex_agents.py --source-dir <path> --output-dir <path> [--check]`
- Produces: A test contract for generated TOML, legacy prompt preservation, and stale-file detection.

- [x] **Step 1: Write failing tests**

```python
result = subprocess.run(
    [sys.executable, str(SCRIPT), "--source-dir", str(SOURCE), "--output-dir", str(output_dir)],
    capture_output=True,
    text=True,
)
assert result.returncode == 0
assert {path.stem for path in output_dir.glob("*.toml")} == source_agent_names()
assert tomllib.loads((output_dir / "orchestrator.toml").read_text(encoding="utf-8"))["name"] == "orchestrator"
```

- [x] **Step 2: Run the targeted test to verify it fails**

Run: `python3 -m pytest project/tests/test_sync_codex_agents.py -q`

Expected: FAIL because `scripts/sync_codex_agents.py` does not exist.

- [x] **Step 3: Add stale-file test**

```python
(output_dir / "developer.toml").write_text("name = 'stale'\n", encoding="utf-8")
result = run_sync("--source-dir", str(SOURCE), "--output-dir", str(output_dir), "--check")
assert result.returncode == 1
assert "[ERROR] Stale Codex agent definition: developer.toml" in result.stdout
```

### Task 2: Implement and generate Codex agent files

**Files:**
- Create: `scripts/sync_codex_agents.py`
- Create: `.codex/agents/*.toml`

**Interfaces:**
- Consumes: legacy agent JSON fields `name`, `description`, `system_prompt`, and optional `tools`.
- Produces: one deterministic TOML file per input role and an exit status of zero for sync/clean check, one for drift or invalid input.

- [x] **Step 1: Implement source validation and deterministic TOML rendering**

```python
def render_codex_agent(source: Path, data: dict[str, object]) -> str:
    prompt = str(data["system_prompt"])
    return "\n".join((
        f"# Generated from {source.relative_to(ROOT)}. Do not edit manually.",
        f"name = {json.dumps(data['name'], ensure_ascii=False)}",
        f"description = {json.dumps(data['description'], ensure_ascii=False)}",
        f"developer_instructions = {json.dumps(prompt, ensure_ascii=False)}",
        "",
    ))
```

- [x] **Step 2: Implement `--sync` and `--check` modes**

```python
if args.check:
    return check_outputs(expected, output_dir)
write_outputs(expected, output_dir)
return 0
```

- [x] **Step 3: Generate the tracked target files**

Run: `python3 scripts/sync_codex_agents.py --sync`

Expected: `[OK] Generated 16 Codex agent definitions ...`

- [x] **Step 4: Run targeted tests**

Run: `python3 -m pytest project/tests/test_sync_codex_agents.py -q`

Expected: PASS.

### Task 3: Add Codex instructions and document compatibility

**Files:**
- Create: `AGENTS.md`
- Modify: `.agents/AGENTS.md`
- Modify: `atomic_tasks.md`
- Modify: `plans/plan.md`

**Interfaces:**
- Consumes: generated `.codex/agents/*.toml` and legacy `.agents/` governance.
- Produces: discoverable Codex project guidance and accurate operational documentation.

- [x] **Step 1: Add root Codex policy**

```markdown
## Compatibility boundary

`.agents/agents/*/agent.json` remains the legacy source. Run
`python3 scripts/sync_codex_agents.py --check` to validate `.codex/agents/`.
Do not edit generated TOML files manually.
```

- [x] **Step 2: Document the new target and command in legacy governance and task records**

Include the Codex command beside the current Antigravity synchronization command. Keep deployment and Kaggle commands opt-in for Codex work unless the current task requires them.

- [x] **Step 3: Run complete migration checks**

Run:

```bash
python3 scripts/sync_codex_agents.py --check
python3 scripts/sync_sdlc_agents.py --check --use-python
python3 -m pytest project/tests/test_sync_codex_agents.py project/tests/test_agent_configurations.py -q
```

Expected: all checks pass with no legacy source changes.
