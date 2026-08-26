# ADR-008 — Service and Deployment Boundary

**Status:** Accepted target boundary; no deployment authorization.

## Current facts

Rule 07 fixes production to Vercel static UI -> HF Docker backend and prohibits
Fly.io, public Azure and HF Static as the backend. The Docker image builds Rust,
an ABI3 PyO3 wheel and a Python 3.12 runtime, then starts the Rust gateway
([Dockerfile](../../../Dockerfile#L3-L26), [Dockerfile](../../../Dockerfile#L46-L70)).

## Target decision

- Begin as a modular monolith with explicit logical packages: Domain contains
  pure state/reducers; Application contains commands/use cases; Ports define
  authority-neutral interfaces; Adapters contain PostgreSQL/SQLite, API,
  provider and effect integrations. One composition root creates exactly one
  ControlPlane command handler.
- No internal network hop or microservice is mandatory initially. The modules
  may run in the existing HF Docker deployment unit, but store credentials and
  privileged command entry points remain internal-only and cannot be exposed as
  an unguarded public FastAPI/browser route.
- Vercel static UI may submit authenticated user commands through the approved
  backend boundary and consume sanitized notifications. It holds no provider,
  database, lease or signing keys and cannot issue canonical transitions.
- Rust/PyO3/FastAPI are data-plane/compatibility consumers. They submit bounded
  commands/evidence; none becomes a second transition writer.
- Extraction to a separate process/service is allowed only after load,
  failure-containment and security evidence justifies it, without changing the
  command/event contracts or creating a second writer. Transitional
  `migration/**` code remains isolated from runtime authority.
- Production path remains `Browser -> Vercel static UI -> HF Docker backend`.
  Fly.io is retired; Azure is historical/inactive; HF Static backend, direct
  browser provider keys and Realtime/WebRTC are prohibited/excluded.

## Operational gate

Production needs Postgres HA/backups/migrations, internal auth/TLS, tenant
isolation, outbox monitoring, lease/fence telemetry, capacity limits, audit
retention and exact rollback evidence. C0 records design only; MAREF-056 always
requires fresh session/target approval.

C0-C5 uses PostgreSQL transactional outbox polling plus SSE; Redis, Kafka and
NATS are not initial dependencies. A later broker requires its own ADR and may
never become command, event-ordering, approval, lease or fence authority.
