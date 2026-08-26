# Requirement Grill Report — Multi-agent Control Plane Refactor

**Date:** 2026-08-26
**Grilled by:** `orchestrator` / `business_analyst`
**Gate:** `APPROVED FOR C0 DOCUMENTATION — RECONCILED`; C1+ remains blocked
until an independent C0 freeze review passes.

## D1 — Scope boundary

- **In:** C0 architecture, active-platform compatibility, approval/session
  semantics, store/transport decisions, checkpoint DAG, acceptance/evidence and
  stop gates for `MAREF-000..057`.
- **Out:** source, schemas, tests, rules, skills, generated `.codex`, config,
  dependencies, artifacts, secrets, Git mutation, paid APIs, external writes,
  deployment, production cutover, destructive migration and force bypass.
- Existing APIs and Result Contract v2 remain compatibility surfaces; frozen
  TDD-HORO-v3.0 history is not edited or reinterpreted.
- The new owner architecture handoff is accepted as design input only. It does
  not authorize C1 implementation, package changes, external actions or cutover.

## D2 — Requirement delta

The target replaces file/snapshot/local-process authority with one canonical,
multi-host-capable Authority Plane: PostgreSQL append-only events, projections
and transactional outbox. Its CP partition law is `No Authority -> No Mutation
-> No New Lease -> No New Approval -> No Blind Retry`; reads/notifications may
be eventual only with explicit staleness metadata. Workers submit
proposals/evidence only. SQLite WAL is a single-host dev/test adapter.

Implementation begins as a modular monolith with Domain/Application/Ports/
Adapters boundaries, one composition root and one command handler. PostgreSQL
outbox polling plus SSE is sufficient through C5; no Redis/Kafka/NATS or
mandatory internal network hop is planned.

## D3 — Success and stop

| Criterion | Evidence | Owner |
|---|---|---|
| Current facts and target decisions are separated and repository-cited | ADR set | BSA |
| Every active platform has capability, fallback, authority and conformance disposition | platform matrix | BSA / QA |
| Every ticket has valid severity/effort, owner, exact ownership, dependencies, acceptance, evidence and stop condition | C0-C5 registers | orchestrator / BSA |
| C0 documents pass scoped `git diff --check` without overwriting concurrent work | command exit plus scoped diff | BSA |
| No C1+ source/schema lane is marked eligible | board and DAG status audit | orchestrator |
| Independent review finds no unresolved C0 inconsistency before C1 release | reviewer WorkResult and exact reviewed digest set | code reviewer / orchestrator |

Stop `DONE — RECONCILED` for C0 when documentation evidence and scoped checks
pass. Keep C1 `BLOCKED` until independent freeze review passes. Stop `BLOCKED`
if dirty shared docs cannot be preserved. Use `NEEDS_HITL` only for a new
indispensable decision not already approved below.

## D4 — Constraints

Rules 05/06/07/08/11/14/17/18/19 apply. One editor owns each file. No secrets
are recorded. HF Docker backend plus Vercel static UI is the only approved
production pair; Fly.io, public Azure, HF Static backend, browser provider keys
and Realtime/WebRTC are excluded. Zero-cost policy still blocks paid fallback.

## D5 — Architecture and ownership

The ControlPlane command handler is the sole canonical transition writer.
Execution, Approval and Lease are orthogonal state machines. C1 contracts
precede C2 core, C3 adapters, C4 HITL Saga and C5 shadow/cutover. Ticket39 and
QOBS retain their existing ownership and must freeze before overlapping bridge
work. Canonical reducer fields are closed and platform-neutral; adapter/provider
fields remain namespaced opaque metadata. See [DAG](sprint-dag.md) and
[ADR-CAP-001](adr-cap-001-control-agent-plane.md).

## D6 — Confirmed assumptions

| Assumption | Status |
|---|---|
| Production store is PostgreSQL; SQLite WAL is local/single-host only | `CONFIRMED` |
| Design is multi-host; tenant is `system` until authenticated tenant identity exists | `CONFIRMED` |
| Session grants expire on new root session, `/clear`, app/process restart; transport reconnect alone does not end the authenticated canonical session | `CONFIRMED` |
| Legacy v2 compatibility lasts at least two production releases and 90 days, whichever is later | `CONFIRMED` |
| Lease profile starts at TTL 120s, renew by 40s, DB clock, no grace; telemetry tuning is mandatory before production | `CONFIRMED-PROVISIONAL` |
| Authority Plane is CP; read/notification plane may be eventual only with disclosed version/sequence/epoch/time/lag | `CONFIRMED` |
| Modular-monolith-first with Domain/Application/Ports/Adapters and one composition root/handler | `CONFIRMED` |
| No Redis/Kafka/NATS through C5; later broker needs a new ADR and cannot be authority | `CONFIRMED` |
| No direct PostgreSQL driver is currently declared; Supabase REST cannot provide required transactions/`SKIP LOCKED` | `CONFIRMED-CURRENT-FACT` |
| Driver/pool and optional WS direct versions are selected/pinned only in their future sequential dependency lanes | `CONFIRMED-LATE-BOUND` |
| Architecture planning floor is `gpt-5.6-sol/xhigh`; normal rank-3 implementation/security floor is `gpt-5.6-sol/high` | `CONFIRMED`; runtime proof still required |

No owner decision remains pending for C0. Driver/WS package choice and exact
MAREF-056 production target are intentionally late-bound ticket inputs, not
open C0 questions; missing values keep those tickets blocked.

## D7 — Risks and rollback

- Split authority or stale workers: expected-version CAS, command idempotency,
  DB attempts and fencing; stale fences fail closed.
- Notification loss: commit before outbox publication; reconnect from a durable
  cursor, never transport memory.
- Partition/stale read: return typed 503/409/403/429 semantics, emit 202 only
  after durable acceptance and disclose projection version/sequence/epoch/lag.
- HITL side effects: E2-E4 freeze under `NEEDS_HITL`; later Saga compensation,
  not deletion of history.
- Migration divergence: effect-free shadow, checksum-locked monotonic migration,
  one migrator lock, immutable import/cutover manifests and monotonic
  `authority_epoch`. No dual authority; legacy authority remains until C5.

## D8 — Model, quota and cost

Planning uses the rank-3 architecture exception. Every executable lane still
needs a fresh versioned Rule 18 decision, valid non-secret quota evidence and a
bound receipt. Static config is intent only. Paid/billing actions are excluded
from the session parent grant and Rule 19 remains fail-closed.

## D9 — Metaphysical/HITL impact

No astrology formula or interpretation changes. C4 touches HITL/export/index/
training boundaries and therefore depends on Ticket39 scope audit and owner
sign-off. `required_human_review=true` plus
`/hitl/scope-audit?source_domain=metaphysical-domain-engine` with
`summary.pass_gate_check=true` is mandatory before that integration handoff.
Unknown/unclassified/ambiguous stages or outcomes reject to `NEEDS_HITL`.
