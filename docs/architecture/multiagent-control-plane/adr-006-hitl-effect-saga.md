# ADR-006 — HITL Governance and Effect Saga

**Status:** Accepted target; implementation held behind Ticket39 and C1-C3.

## Current facts and risk

Saving an approved/edited review currently writes gray-zone/JSONL data, mutates
and saves FAISS, then schedules fine-tuning in one request path
([HITL](../../../project/hitl_router.py#L835-L899)). Manual `force=true` skips
the autotrain-enabled, missing-human-gate and threshold checks
([trigger](../../../project/hitl_router.py#L383-L438)). Undo deletes only the
review record ([undo](../../../project/hitl_router.py#L910-L917)). External
OpenAI fine-tuning uploads a file and creates a job directly
([adapter](../../../project/rag/external_finetune.py#L36-L63)). These are current
facts, not approved target semantics.

## Governance classes

| Class | Meaning | Default gate |
|---|---|---|
| P0 | pure/read-only query or validation | authenticated capability |
| P1 | reversible workspace/control metadata mutation | ticket child grant |
| P2 | durable canonical data/effect preparation | scoped approval + lease/fence |
| P3 | external, paid-capable or provider job mutation | fresh target/action approval |
| P4 | production activation, destructive/history, secrets/permissions | fresh explicit owner HITL; no parent-grant inheritance |

## Saga stages, classes and mandatory gates

The stage labels describe effect intensity, not an automatic pipeline. They
replace the ambiguous earlier shorthand in which `ReviewRecord` appeared at E0:

| Stage | Exact target meaning | Class | Approval/authority | Lease/fence | Idempotency, outcome and compensation |
|---|---|---|---|---|---|
| E0 | Local read, validation or ephemeral preview; no durable ReviewRecord/export/index mutation | P0 | Authenticated read capability | None | Pure request identity; no durable effect or compensation |
| E1 | Append-only audit record, ReviewRecord or HITL request only | P1 | Standing system authority plus the bounded ticket child grant; never reviewer self-assertion | None for the append-only request | `command_id` required; correction/supersession is appended, never deletion |
| E2 | Durable business record, immutable export generation, index generation or activation | P2 | Exact scoped approval for object/action | Active effect lease plus current DB attempt/fence | Idempotency key and receipt required; compensate with a new generation/pointer, preserving history |
| E3 | Provider upload/job or training submission/reconciliation | P3 | Fresh target/action approval, including billing classification | Active effect lease plus current DB attempt/fence | Internal and provider idempotency where available; `unknown` reconciles and is never blindly retried; cancel/supersede receipt preserves provider history |
| E4 | Model/release activation, production authority switch, destructive/history, secrets or permissions action | P4 | Fresh explicit owner HITL; no parent-grant inheritance | Active release/effect lease plus current DB attempt/fence | Exact one-shot command/manifest; compensation creates a new linked action/authority epoch and never erases external history |

Every E1-E4 durable command and receipt binds tenant/run/task/effect, stage and
P-class, `command_id`, `expected_version`, normalized input/output digests and
causation/correlation. E2-E4 additionally bind the exact approval, DB-allocated
attempt and current fencing token. Unknown, unclassified or ambiguous stage,
class, approval, effect identity or outcome is rejected and becomes
`NEEDS_HITL`; it never defaults downward.

When execution/approval is `NEEDS_HITL`, E2-E4 are frozen. E0 may continue and
E1 may append only the audit/HITL request under standing system authority; E0
or E1 cannot satisfy the missing decision or activate a generation.

Automatic, background and `force` training remain blocked until MAREF-041/042
implements the Saga and Approval Service authorizes the exact effect. Unknown
provider outcomes require reconciliation, not retry. Undo is a compensating
action over resulting generations/effects; deleting one review record is not a
rollback.

There is no `force` bypass at any stage. A failing execution with committed
effects enters compensation before terminalization. Once terminal, remediation
is a new linked execution with its own command, approval, lease/fence and
receipt; external or append-only history is never described as “rolled back.”

Ticket `TICKET-RELEASE-COMPLETE-20260826-39-ADMIN-HITL-ROUTING` and its scope
audit/sign-off must freeze before MAREF-042 owns `project/hitl_router.py`.
