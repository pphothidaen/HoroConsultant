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

**Status**: RESOLVED — fix applied 2026-09-21

**Description**:
- `render.yaml` previously specified `dockerfilePath: ./Dockerfile.render` (Python uvicorn only)
- Production Render service was running `./Dockerfile` (Rust gateway + Python worker subprocess)
- The mismatch was introduced in commit `6e340916` (Sep 20) when `render.yaml` was added but the Render service was not reconfigured to use it

**Resolution**:
- Updated `render.yaml` to specify `dockerfilePath: ./Dockerfile` (Rust gateway) to match production reality
- The Rust gateway (`horo_server`) is the actual entrypoint in production, confirmed by:
  - `/admin/provider-pools` returning 401 from Python auth through Rust proxy
  - `route_kind()` allowlist routing working correctly in production
- The contract test (`tests/test_route_sync.py`) continues to ensure routing correctness

**Files changed**:
- `render.yaml`: `dockerfilePath: ./Dockerfile.render` → `dockerfilePath: ./Dockerfile`

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

---

## Cloudflare Workers Builds: `horoconsultant` (stale integration)

**Status**: Stale / Non-blocking  
**Discovered**: 2026-09-21  
**Build URL**: `https://dash.cloudflare.com/bda49e4e77e00609cb1ef68561b0d9eb/workers/services/view/horoconsultant/production/builds/2ce198c4-4347-4671-8a32-6b72932fe63e`

### Symptom

GitHub PR checks show `Workers Builds: horoconsultant` = **fail** on every CI run (since before PR #61). This is a Cloudflare Workers Builds git integration status check, not a GitHub Actions check.

### Root Cause

The `horoconsultant` Cloudflare Workers project is a **stale integration** from early experimentation with Cloudflare Pages/Workers deployment. Key evidence:

1. **Project name mismatch**: The failing build is for project `horoconsultant`, but the `wrangler.toml` in this repo defines `name = "horoconsultant-pages"` — a different project name. The `horoconsultant` project was likely created manually in Cloudflare Dashboard during early testing and never cleaned up.

2. **Commented-out account_id**: The `wrangler.toml` has `account_id` commented out (`# account_id = "bda49e4e77e00609cb1ef68561b0d9eb"`), indicating this was never fully configured for deployment.

3. **Not in production path**: Production architecture is Vercel (frontend gateway) → Render (Docker backend: Rust `horo_server` + Python worker). Cloudflare Workers is not part of the production deployment path (`docs/architecture/deployment-rail.md`).

4. **Analysis artifact only**: The `cloudflare-deployment-analysis.json` and `wrangler.toml` are migration analysis artifacts from a planned-but-abandoned migration from Vercel Pages Functions to Cloudflare Pages. The migration was never completed.

5. **Non-required check**: The HANDOFF.md explicitly notes "Workers Builds failure is non-required and untriaged" — it does not block merges.

### Recommendation

**Disconnect the stale Cloudflare Workers Builds integration** — the user should:

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/bda49e4e77e00609cb1ef68561b0d9eb/workers/services/view/horoconsultant/production)
2. Navigate to **Settings > Builds** (or **Settings > Git Integration**)
3. Click **Disconnect** to unlink the GitHub repo `pphothidaen/HoroConsultant`
4. Alternatively, delete the `horoconsultant` Workers project entirely if no longer needed

**Do NOT attempt to fix the build** — the project is not used in production, and fixing it would require active Cloudflare account access to debug the build configuration.

### Files in repo (analysis artifacts, safe to keep or remove)

- `wrangler.toml` — Cloudflare Pages config (project name: `horoconsultant-pages`, not `horoconsultant`)
- `cloudflare-deployment-analysis.json` — migration analysis (Vercel → Cloudflare Pages)
- `project/static/` — static assets with `_worker.js` (Pages Functions entry point)
- `.wrangler/cache/pages.json` — wrangler cache (account_id + project_name)

### Impact

- **No production impact** — Cloudflare Workers is not in the production path
- **No merge blockage** — the check is non-required
- **Cosmetic noise** — adds a red X to every PR, masking real CI status
