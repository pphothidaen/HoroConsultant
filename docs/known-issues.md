# Known Issues

## AGY Plugin Bug: `delegate_to_agy` task_id TypeError

**Status**: Active — Plugin-level bug, cannot be fixed by user code

**Symptom**:
```
TypeError: handle_delegate_to_agy() got an unexpected keyword argument 'task_id'
```

**Impact**:
- `delegate_to_agy` tool is completely unusable
- Affects all attempts to delegate tasks to AGY code accounts
- Workaround: Use Hermes `delegate_task` (subagent) instead — proven effective

**Root cause**:
- The `delegate_to_agy` tool handler function signature does not accept `task_id` parameter
- Mismatch between tool schema and handler implementation
- Plugin was loaded from the `autonomous-ai-agents` skill category

**Workaround**:
```python
# Use delegate_task instead of delegate_to_agy
delegate_task(action="spawn", tasks=[{
    "goal": "Task description",
    "context": "Background info"
}])
```

**Affected versions**: Hermes Agent runtime (all models)

**Reported**: 2026-09-21

---

## Render Bluefin Mismatch (INCIDENT-021)

**Status**: Documented — fix applied to Rust routing table (root cause)

**Description**:
- `render.yaml` specifies `dockerfilePath: ./Dockerfile.render` (Python uvicorn only)
- Production Render service is running `./Dockerfile` (Rust gateway + Python worker subprocess)
- The `render.yaml` was added in commit `6e340916` (Sep 20) but the Render service was
  not reconfigured to use it

**Mitigation**:
- Fixed by adding all 40 missing routes to the Rust `route_kind()` allowlist
- Added contract test (`tests/test_route_sync.py`) to prevent future drift
- Documentated in `docs/architecture/deployment-rail.md`

**Recommendation**:
- Either reconfigure Render service to use `Dockerfile.render` (Python-only)
- OR update `render.yaml` to specify `dockerfilePath: ./Dockerfile` (Rust gateway)
- The contract test ensures routing correctness regardless of which Dockerfile is used

---

## Flaky Test: `test_non_release_hermes_qa_and_sync_orchestration_remains_callable`

**Status**: Active — Pre-existing race condition, not related to route-sync changes

**Symptom** (CI only, ~intermittent):
```
AssertionError: assert ['', 'CALL pytest'] == ['CALL pytest', 'CALL tee']
```

**Location**: `project/tests/test_local_release_runner_contract.py:322`

**Root cause**:
- The QA phase runs `python3 -m pytest ... | tee /tmp/hermes_pytest_output.txt` (a 2-process pipeline)
- The mock `python3` writes its log entry with multiple `printf` calls (label, then each arg, then newline)
- The mock `tee` writes `CALL tee\n` in a single write
- Both processes append to the same `COMMAND_LOG` concurrently — when the writes interleave
  (`"CALL pytest"` + `"CALL tee\n"` + `"\t-m..."`), the log gets a line starting with `\t`,
  which `split("\t", 1)[0]` reads as an empty label
- Local runs pass 20/20; only CI scheduling exposes the race

**Workaround**: Re-run failed jobs (passes on retry)

**Permanent fix (follow-up ticket)**:
- Make the mock `python3` write each log entry with a single atomic `printf` call, or
- Write to per-process temp files and merge deterministically in the test

**First observed**: 2026-09-21 (CI run 35594882927)
