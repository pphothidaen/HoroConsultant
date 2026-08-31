# Rule 20: Cross-Runtime Context Handoff and Lifecycle Governance

## 1. Authority and Derived State

1. `PROJECT_TASKS.md` and `plans/plan.md` are the sole primary authorities.
2. `HANDOFF.md` is a derived, non-authoritative capsule under `HandoffSnapshotV1`.
3. The engine never parses a raw transcript; only bounded state is evaluated.
4. Any unresolved lane forces `clear_ready` false; unverified metrics evaluate to `UNKNOWN`.

## 2. Quantitative Bounds

1. State input payloads are strictly bounded to `64 KiB`.
2. Derived handoff capsules must not exceed `16 KiB`.
3. Percentage thresholds: alert at `40%`, snapshot at `45%`, critical at `80%`.
4. Transcript byte thresholds: alert at `400 KiB`, snapshot at `450 KiB`, critical at `900 KiB`.

## 3. Operator Actions and Native Hook Trust

1. Only an `operator` may clear, compact, or reset sessions; hooks cannot automate clearing.
2. Codex project hooks require non-managed user review of the exact current hash.
3. Native Codex CLI may expose `--dangerously-bypass-hook-trust`; repository instructions never invoke or recommend this bypass, and managed hooks remain outside this local implementation.
