# AGY4 Integration Preflight Receipt

Date: 2026-09-01

## Isolated Candidate

- Base: `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`
- Candidate worktree: `/Users/kimlenglim/Project/HoroConsultant-agy4-integration-cb1df9f`
- Cherry-pick 1: `c071c2209b145379f79efe0fa2f76e5fe6d38833` -> `55002e65959cabf058e05a778b292b7ca1dd5e18`
- Cherry-pick 2: `d4a28bb3eebf5251992f3ac6d930363dfea9499c` -> `76fcf0548deed32a0bd8aa793b9556a379a80f66`
- Cherry-pick 3: `5d3e12c2890aee4a282250a35aaf031e4c30d5e9` -> `29a483f36025903627f2a5a548cd11c93698e985`
- All three cherry-picks applied without conflicts. The candidate was clean before its separate evidence record was written.

## Local Evidence

- `python3 -m pytest -q tests/test_agy4_runtime_config_baseline.py tests/test_agy4_runtime_config.py` -> `4 passed`.
- `python3 scripts/sync_ai_agent_ecosystem.py --check` -> passed.
- `git diff --check cb1df9f..29a483f` -> passed.
- The runtime config retained `provider_execution_denials.agy: PLATFORM_NATIVE_PRESPAWN_RECEIPT_REQUIRED`.
- No AGY/provider transport, remote, auth, push, deploy, or publish command ran.

## Provenance Limitation

Candidate-local provenance verification reported `BASELINE_PARENT_MISMATCH`. The source-baseline manifest binds original parent `c071c220...`, while cherry-pick reconstruction uses candidate parent `55002e6...`; its frozen test hash still verified. This receipt does not claim primary integration, original-chain provenance validity, release readiness, or provider readiness.
