# AGY4-CFG-002-BASELINE-REVIEW — Independent Review Receipt

## Verdict

**PASS** for the immutable, test-only baseline commit
`c071c2209b145379f79efe0fa2f76e5fe6d38833`. It is a valid frozen QA
baseline for a subsequent, separately owned AGY4 runtime-configuration lane.
This receipt does not authorize provider execution, quota consumption, remote
actions, or configuration implementation by the reviewer.

## Provenance and Scope

- `c071c2209b145379f79efe0fa2f76e5fe6d38833` is the direct child of
  `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`; the ancestry check passed.
- Its exact changed paths are only
  `plans/test_provenance/agy4-config-baseline.json` and
  `tests/test_agy4_runtime_config_baseline.py`. No runtime configuration,
  production source, provider client, or generated artifact changed.
- The manifest declares the same parent, ticket
  `TICKET-AGY4-CFG-001-QA-BASELINE`, and future correction scope limited to
  `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml` and
  `tests/test_agy4_runtime_config.py`.
- The frozen test object's SHA-256 is
  `73c2b7a4e833c84a3d9eb89b7081471ee69610d24c1eaf819a0e582802383fae`,
  matching the manifest exactly.

## Deterministic Controls

- In detached worktree
  `/Users/kimlenglim/Project/HoroConsultant-agy4-qa-baseline-cb1df9f`,
  `python3 -m pytest -q tests/test_agy4_runtime_config_baseline.py` returned
  exit `1`: exactly `1 failed, 1 passed`. The red control fails because the
  runtime-readonly-v3 accounts contain only `agy1` and `agy2`, not `agy4`.
- The paired negative control passed: `_run_provider_process(["agy4"], ...)`
  raised `PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED` before the monkeypatched
  `subprocess.Popen` could run; observed transport-call count was zero.
- `python3 scripts/test_provenance_guard.py verify --manifest
  plans/test_provenance/agy4-config-baseline.json --baseline
  c071c2209b145379f79efe0fa2f76e5fe6d38833 --head
  c071c2209b145379f79efe0fa2f76e5fe6d38833` returned `PASSED`, zero issues,
  and one verified test file.

## Review Boundary

The future implementation must descend from this baseline and remain restricted
to the two manifest-listed paths. It must preserve the native-receipt guard and
add no provider invocation or dispatch enablement without an independently
authorized execution receipt.
