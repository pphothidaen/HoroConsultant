# AGY terminal supervisor: proposed execution boundary

Status: DESIGN ONLY, 2026-09-05. Ticket: `TICKET-DISPATCH-WORKAROUND-001-SUPERVISOR-DESIGN`. No executable route, provider invocation, policy revision or new authorization is delivered by this document. DSG-009A/B remain blocked. See [platform evidence contract](external-dispatch-platform-contract.md).

## Decision and existing implementation

Design a terminal-only supervisor as a future, separately reviewed boundary for processes it starts and owns. It cannot intercept host `spawn_agent` calls or issue platform-native receipts. Until a reviewed Rule 11/17/18 revision explicitly admits this boundary and a separately verified test baseline admits implementation, AGY remains denied by `scripts/multiagent_prompt_command.py::_validate_transport_provider_binding`.

`scripts/multiagent_root_supervisor.py` already provides durable local queue coordination, root fencing, drain/stop and fixture smoke. Its default process factory returns a no-op object with PID 0, its default PID probe returns false, and its smoke uses `_FixtureProcess`. `submit()` accepting an AGY alias is queue metadata, not provider admission. Reuse its durable queue vocabulary and ownership/fencing concepts only after tests establish their needed invariants; do not treat the default factory, fixture receipt, `bootstrap-local-unsafe` switch, or successful smoke as a terminal execution implementation or trusted proof. Do not modify that module in this design ticket.

## Proposed interfaces and admission

These are design contracts, not installed schemas or public CLI flags. A future `supervise(request)` interface accepts a closed `TerminalTaskRequestV1` containing `ticket`, `attempt_id`, `alias`, `provider`, `session_id`, `role`, `phase`, bounded `objective`, `ownership_sha256`, `policy_sha256`, `command_sha256`, `admission_id`, `grant_id` and `deadline`. IDs resolve within code-fixed owner-only stores; caller-supplied executable, shell command, arbitrary store path, model fallback or approval boolean is forbidden. Requested model/effort are derived from the exact reviewed route, and included in the command/decision bindings.

Before process creation, resolve the pinned executable/version and exact argv, validate route/provider binding and sandbox enforcement, check ownership and one-process capacity, validate a fresh bound health/capability observation, then atomically consume the exact owner-issued grant with the durable admission chain. The current activation ticket defines the <=120-second admission TTL and its claim/grant/store bindings. This design neither duplicates that ledger nor adds a parallel approval path. No child starts on any validation failure. Consume remains burned on crash or ambiguous spawn outcome; recovery never retries automatically.

Future methods are `status(attempt_id)` for sanitized state, `drain()` to reject new submissions and `recover()` to fence uncertain attempts. Cancellation/revocation behavior must follow the explicitly reviewed lifecycle policy below; no caller-controlled signal or arbitrary PID operation is exposed.

## Lifecycle and recovery

Proposed initial concurrency is one provider process; no auto-retry, alias substitution or provider/model fallback. Use direct argv without a shell, an exact environment allowlist, verified read-only sandbox and a dedicated process group. The future implementation must prove that sandbox enforcement covers descendants; inability to do so is `SANDBOX_NOT_PROVEN` before spawn.

| State/event | Required transition and evidence |
|---|---|
| Received; invalid/missing/expired admission | `REJECTED`; sanitized reason, zero consume or child where rejection precedes consume |
| Valid grant atomically consumed | `ADMITTED`; durable one-use anchor before starting owned process |
| Spawn succeeds | `RUNNING`; bind instance identity, process group, monotonic start/deadline and trusted CLI session |
| Spawn fails or crashes after consume | `FAILED` or `INDETERMINATE`; retain consumed anchor, no retry |
| Natural exit with complete valid result and matching telemetry | `COMPLETED`; still distinguish local validation from provider-authenticated proof |
| Nonzero exit, conflicting/malformed final, missing telemetry or session mismatch | `FAILED` / `CAPABILITY_NOT_PROVEN`; never upgrade exit-zero to success |
| Deadline/revocation during execution | Fence new work and classify attempt as failed; process action only under the future approved lifecycle rule |
| Restart/orphan uncertainty | Reconcile durable instance/group identity; `INDETERMINATE` and no new admission if ownership cannot be proven; never signal a reused or unrelated PID |

The proposed terminal runtime cap is 300 seconds with a two-second TERM grace then KILL for an owned process group **only after lifecycle-policy approval**. Existing dispatcher constants are a 900-second provider cap and two-second termination grace; this document does not change them or claim 300 seconds is currently enforced for terminal execution. Rule 11's `natural-exit-only` and `never-preempt` contract conflicts with timeout termination. Implementation is blocked until independent review and explicit policy authorization resolve that conflict; the proposed TERM/KILL behavior cannot silently override it. A monotonic clock bounds runtime; trusted wall-clock evidence is still required for receipt freshness. On shutdown or orphan recovery, unknown ownership never justifies killing processes.

## Evidence and privacy

Keep `WorkResult` v2 unchanged. Proposed `LocalSupervisorReceiptV1` contains `artifact_type=LocalSupervisorReceipt`, `schema_version=1`, ticket/attempt/alias/provider/session bindings, supervisor instance identity, requested model/effort, executable/version/command digests, admission/consume/ownership/policy digests, start/end and exit classification, bounded output byte count/digest, normalized WorkResult digest, telemetry source/digest and `evidence_level`. It is a distinct type and cannot be submitted as a native pre-spawn receipt. Effective model/effort are recorded only when actually observed from the designated telemetry source; missing values remain unknown, never copied from requested values.

Evidence levels are independent: (1) local process lifecycle, (2) CLI-reported session/result, (3) authenticated provider execution. Level 1 does not prove level 2 or 3. A model's prose, argv, config, catalog or local digest cannot establish authenticated execution. Local receipts and owner-only files do not resist forgery by the same OS principal. Reject missing or conflicting trusted identity rather than accepting a self-identifying result.

Use bounded in-memory parsing (maximum 2,000,000 bytes, matching the existing output bound), strict final-event cardinality and schema validation. Persist sanitized metadata/digests only; no raw stdout/stderr, prompts, credentials or sensitive account identifiers. Preserve Rule 17: public outcomes with elided streams are **validated in-process only**, not independently portable/offline proof. No approved raw-stream retention channel exists. Recovery retains only sanitized evidence and burned admission anchors, never reconstructs authoritative receipts from model text.

## Acceptance before any executable successor

- Independent design review resolves the terminal-only policy boundary, natural-exit conflict, sandbox enforceability and telemetry authenticity. That approval cannot close DSG-009A/B or the platform Spark whitelist.
- A separately admitted QA baseline covers invalid/cross-bound/replayed/expired grants, concurrent consume, crash before/after consume/spawn, stale or forged health, PID reuse/orphan ownership, runtime limit, revocation, sandbox escape, stream overflow, ambiguous final and effective-model/session mismatch.
- A future owner-issued exact attempt grant and fresh health/capability proof are required for any live test. Fixtures exercise code contracts only. No live authority is implied by this document or its approval.
