# ADR-007 — Legacy Compatibility, Shadowing, and Migration

**Status:** Accepted proposal for planning; production cutover is not approved.

## Current facts

Result Contract v2 is implemented for Codex JSONL and AGY native stream JSON
([Codex adapter](../../../scripts/multiagent_prompt_command.py#L2713-L2777),
[AGY adapter](../../../scripts/multiagent_prompt_command.py#L2780-L2824)).
Historical receipts can have privacy/portability limitations; existing
verifiers and immutable prior outcomes remain evidence, not canonical
control-plane events.

## Target decision

- Preserve active v2 compatibility for at least **two production releases and
  90 days, whichever is later**, measured only from MAREF-057 final authority
  acceptance. MAREF-056 deployment alone cannot start the clock. Extension is
  allowed; early removal is not.
- Retain historical verifier code needed to interpret retained records for the
  full record-retention lifetime. Never relabel, re-sign or reinterpret an old
  receipt as a new event/grant/lease.
- Run shadow mode before authority changes: legacy executes, the new plane
  independently derives expected commands/projections, and divergence is
  recorded without taking production authority or executing any shadow effect.
- Import one immutable legacy snapshot with source paths/digests, schema and
  importer version. Re-running the manifest is idempotent; changed source bytes
  require a new manifest.
- Database migrations are checksum-locked, monotonic and protected by one
  migrator lock. Use expand/contract compatibility; never rewrite or truncate
  the frozen ledger. POSIX claim/ledger locks remain host-local defense only.
- A monotonic `authority_epoch` fences every legacy and new writer. There is no
  dual-authority interval: shadow has no effects, cutover switches one authority
  once under the immutable approved manifest, and rollback advances the epoch
  while restoring the exact prior routing point. A retry or second cutover
  needs a new manifest and fresh P4 approval.
- New post-cutover records are preserved and reconciled, never deleted or
  relabelled as legacy history.

## Exit gate

At least 100 deterministic replay/shadow fixtures must show zero unexplained
divergence; platform conformance, load/fault tests, reviewer verdict and a
non-production/offline rollback rehearsal must pass before MAREF-056. The live
rollback/restoration drill is MAREF-057 under a separate fresh P4 grant. The
compatibility clock starts only after MAREF-057 accepts final authority and
records its calendar anchor.
