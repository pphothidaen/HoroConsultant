# Architecture Design Specification: Multi-Agent Parity & Module-Bounded Concurrency
> **Document ID**: `DESIGN-SPEC-20260827-PARITY`
> **Consensus Owners**: `orchestrator` (`gpt-5.6-sol` / `high`) 🤝 `hermes` (`Gemini 3.7 Pro` / `high`)
> **Status**: `IN_REVIEW — DESIGN REJECTED / IMPLEMENTATION BLOCKED`
> **Target Framework**: HoroConsultant AI SDLC Governance (Rules 10, 11, 13, 17, 18)

---

## 1. Executive Summary & Problem Statement

### Current-session disposition (2026-08-27)

- **Historical rejected design review**: C/H/M/L `1/5/1/0`. `PARITY-001`
  remains `IN_REVIEW` with the design rejected; `PARITY-002` through
  `PARITY-006` remain `BLOCKED` by that chain.
- **Fail-closed state**: all three flags remain `false`. `DSG-009` is `DONE —
  LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY PASS; RUNTIME NOT_PROVEN`; its
  prior 5/11 drift is superseded historical failed-candidate evidence.
  `DSG-009A` and `DSG-009B` remain `BLOCKED`.
- **Native-spawn owner gate**: a local token, flag, repository hook,
  configuration, or test result cannot make AGY eligible. Every native
  `spawn_agent` requires a future host-native pre-spawn API/receipt, trusted
  telemetry, and a fresh owner decision before it can be evaluated.
- **Historical and final QA evidence**: the superseded pre-remediation baseline
  was `543/545` with two token failures. The local re-freeze records guard QA
  `552`, integrated safe mocked QA `823` (`552 + 271`, four intentional
  local-child deselections), PromptCommand QA `275` plus adversarial `33`, and
  named security `761` at C/H/M/L `0/0/0/0`; sync/check is green and the secret
  scan reports `1,967` files / `0` leaks. This is local-only evidence and does
  not approve the rejected design or release runtime authority.

### 1.1 The Challenge
1. **Asymmetric Evidence Barrier**: Codex (`codex1`, `codex2`) operates with in-process CLI capture and structured JSONL output schema in Stage A/B, whereas AGY (`agy1`, `agy2`) is hard-blocked with `CAPACITY_ALIAS_RUNTIME_PROOF_UNAVAILABLE` pending external platform-native pre-spawn hooks (`DSG-009A/B`).
2. **Quota Misalignment**: User-attested quota marks `agy1` as `healthy`, causing the scheduler to select `agy1`, which immediately fails closed at execution time.
3. **Global Single Source Editor Bottleneck**: Current Rule 11 restricts the entire project to exactly one active `SOURCE_EDITOR` at any time, underutilizing available collaboration slots and causing artificial serialization across unrelated modules.

### 1.2 Historical proposal (not implementation authorization)
1. **Dual-Orchestrator Consensus**: rejected design proposal only, not a runtime route.
2. **Feature Flagging**: all flags remain `false`; this document authorizes no flag change.
3. **Module-Bounded Path Isolation**: future concept that grants no concurrent editor authority.
4. **Token-Anchored Pre-Spawn Protocol**: internal structural/test concept only; it cannot establish AGY eligibility or replace the host-native gate.
5. **Rule 10 cleanup**: blocked pending a newly approved design and dependencies.

---

## 2. Feature Flag Specification

In `.agents/config/full_capacity_guard.v2.json` and `.agents/config/multiagent_model_policy.yaml`:

```json
{
  "feature_flags": {
    "enable_agy_parity": false,
    "enable_module_level_source_isolation": false,
    "enable_granular_lane_roles": false
  }
}
```

### 2.1 Behavior Modes

| Feature Flag | Current `false` baseline | Future `true` request |
| :--- | :--- | :--- |
| `enable_agy_parity` | `agy1`/`agy2` are `NOT_ELIGIBLE`; `dispatched: false`. | Not authorized. A local token cannot make either alias eligible; host-native API/receipt, trusted telemetry, owner decision, and review are required first. |
| `enable_module_level_source_isolation` | No module-level concurrency permission is released. | Not authorized; requires an approved design and independent verification. |
| `enable_granular_lane_roles` | Baseline roles apply. | Not authorized; requires an approved design and independent verification. |

---

## 3. Module-Bounded Path Isolation Architecture

### 3.1 Disjoint Prefix Verification
If a future approved implementation is considered, it must validate that for any two concurrently active or proposed `SOURCE_EDITOR` lanes:
`Prefix(R_A) \cap Prefix(R_B) = \emptyset`

Historical design example only (not an allocation permission):
- Lane 1 (`codex1`): `project/core/`
- Lane 2 (`agy1`): `project/api/`
- Lane 3 (`agy2`): `web/`
- Lane 4 (`codex2`): `project/tests/`

---

## 4. Token-Anchored Pre-Spawn Protocol

### 4.1 Token Derivation
For a hypothetical future AGY child spawn attempt:
`Token = SHA256(SessionID || TicketID || AttemptID || SnapshotHash || DecisionDigest)`

No repository hook or local ledger may allow native child execution. A token is
not eligibility evidence and cannot substitute for the host-native gate.

### 4.2 Owner Gate & Native Platform Boundary
The token proposal is a repository-level structural/test concept only. Per the Owner Decision on DSG-009A (`อนุญาติตามแผนงาน ต้องการครอบคลุม native spawn_agent ทุกตัว งานต้องคง BLOCKED จนแพลตฟอร์มมี pre-spawn hook/receipt API`), every live native `spawn_agent` remains strictly `BLOCKED` until the host platform exposes and documents the pre-spawn hook and receipt APIs. No authority is released to live AGY execution, regardless of a local token or flag value.

---

## 5. Historical migration proposal (blocked)

Do not perform these actions under this rejected design:
1. Purge legacy hardcoded `NOT_ELIGIBLE` evaluations in `.agents/hooks/full_capacity_guard.py`.
2. Purge disabled state markers for `agy2` in governance configs.
3. Clean obsolete fallback loops and ensure `python3 scripts/sync_ai_agent_ecosystem.py --check` passes cleanly.

---

## 6. Verification & Rollback Plan

- **Historical failed candidate**: `543/545`, including two token failures,
  and the 5/11 drift are superseded evidence only.
- **Current local evidence**: stable 11-file manifest plus PromptCommand
  dependency; guard `552`, integrated safe mocked `823`, PromptCommand `275`
  plus adversarial `33`, named security `761` at C/H/M/L `0/0/0/0`, green
  sync/check, and `1,967` scanned files / `0` leaks.
- **Current stop**: all flags remain `false`; a newly approved design and
  separate future scope-gated verification are required before implementation or
  release claims. `DSG-009A/B` and all native-spawn/provider authority remain
  blocked.
