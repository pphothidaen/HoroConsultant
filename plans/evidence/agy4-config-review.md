# AGY4-CFG-005-REVIEW

Status: PASS (bounded candidate review; not provider-dispatch or release approval)

## Candidate

- Test baseline: `d4a28bb3eebf5251992f3ac6d930363dfea9499c`
- Source candidate: `5d3e12c2890aee4a282250a35aaf031e4c30d5e9`
- Ancestry: the test baseline is a direct ancestor of the source candidate.
- Baseline parent: `c071c2209b145379f79efe0fa2f76e5fe6d38833`.

## Provenance and scope

- `d4a28bb` changes only `tests/test_agy4_runtime_config.py` and `plans/test_provenance/agy4-runtime-config-source-baseline.json`.
- The manifest binds test SHA-256 `c4f293bae93bd13077344fb0eee5b2b0e328d9f4b95b2bb407abf7bcd9a94058`; the same test hash is present at `5d3e12c`.
- The baseline parent has no change to `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml` relative to `d4a28bb`.
- `5d3e12c` changes only the manifest-authorized source path `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml` (12 additions, 0 deletions).
- The source commit carries the exact trailer `Test-Baseline: d4a28bb3eebf5251992f3ac6d930363dfea9499c`.

## Controls

- Frozen red control at clean `c071c22`: `python3 -m pytest -q tests/test_agy4_runtime_config_baseline.py` exited `1` with `AssertionError: AGY4 runtime account registration is required` and `1 failed, 1 passed`.
- The source-baseline test covers the same absent-account condition, while its parent configuration is byte-identical; this supports the recorded source-baseline red control without reconstructing history.
- Candidate green control: `python3 -m pytest -q tests/test_agy4_runtime_config.py` passed `2/2`.
- The native-denial test monkeypatches `subprocess.Popen`, receives `PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED`, and observes zero transport calls.
- Direct route resolution yields only `agy4`, `agy`, `plan`, and `sandbox=True`; a direct guarded runner invocation raises `PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED` before process creation.
- `python3 scripts/sync_ai_agent_ecosystem.py --check` passed.

## Safety

- Candidate-diff secret-pattern scan found no credentials, tokens, keys, or secret-bearing paths.
- The change is cleanly reversible by reverting `5d3e12c`; the reverse diff removes only the 12 AGY4 route lines.
- This PASS preserves the fail-closed provider boundary. It does not prove native pre-spawn receipts, provider transport, account quota, or authorization for a real AGY4 dispatch.
