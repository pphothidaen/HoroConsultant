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
