# CAPACITY-RECORD-001: Native Lane Capacity Load-Test Evidence

## Record type

- Date: 2026-08-31 (Asia/Bangkok)
- Classification: concise, non-secret runtime evidence record
- Evidence boundary: facts below are limited to the supplied observed run and user attestation. No provider credentials, keys, or raw provider output are recorded.

## Observed runtime facts

- The native platform admitted six simultaneous lanes.
- A seventh spawn was rejected with an agent thread limit.
- Two completion/refill cycles admitted immediately.
- Sustained-run evidence: focused QA passed 300/300 in 110.70s; release contract passed 59/59 in 5.36s; secret scan found 0/3,595; ecosystem sync completed in 0.24s.
- Host snapshot: 10 CPU / 16 GiB. Free memory was 76% initially and 66% later while an external AGY process contended for resources.
- The current orchestrator session is user-attested as a five-hour quota at 37% remaining, resetting at 14:24.

## Capacity terms: do not conflate

| Term | Record |
| --- | --- |
| Native platform limit | Runtime-proven admission reached 6 simultaneous lanes; a 7th native spawn was rejected by the agent thread limit. |
| Configured safe cap | No numeric configured safe-cap value was observed in this record. Dispatch policy reserves native slots for the critical path, so it must not treat all 6 slots as discretionary capacity. |
| Theoretical AGY cap | 3 lanes per admitted alias. This is a theoretical cap, not runtime-provider proof. |
| Runtime-proven provider capacity | Not established for AGY/Codex wrappers. The only proven concurrent admission in this record is the native platform's 6 lanes. |

## Cost-aware dispatch policy

- Treat 6 as the native hard cap; reserve slots for critical-path work before admitting discretionary lanes.
- Do not retry a seventh native spawn after the thread-limit rejection.
- Keep AGY/Codex wrappers circuit-broken until broker and security gates pass.
- Admit only atomic Read, Write, or Execute tickets that have explicit ownership, Definition of Ready (DoR), and Definition of Done (DoD).
- Record any capacity exception and require a quota refresh before dispatching against refreshed quota state.

## Acceptance and stop condition

- Acceptance: this record states the supplied observed facts, separates native, safe, theoretical AGY, and provider-proven capacity, and contains no secrets.
- Stop: no runtime tests, provider/keychain/secret commands, external changes, or edits outside this file are performed for CAPACITY-RECORD-001.
