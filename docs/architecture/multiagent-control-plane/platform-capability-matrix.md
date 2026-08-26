# Active-platform Capability Matrix

**Decision:** every active/approved repository platform is either supported by
a typed adapter/conformance contract or rejected with a typed unsupported
result. Reducer-authoritative fields are closed and platform-neutral.
Adapter/provider values are namespaced opaque correlation metadata, never
transition inputs. “Supported” never makes a provider or transport authority.

| Platform/surface | Current repository evidence | Target capability and fallback | Authority/loss boundary | Conformance owner |
|---|---|---|---|---|
| Native collaboration | Rule 11 defines bounded child result fields and one-editor ownership ([Rule 11](../../../.agents/rules/11-orchestrator-subagent-delegation.md)) | Map native task/result/mailbox metadata to AgentEnvelope; retain native correlation when available | No fabricated provider receipt/session; ControlPlane assigns run/task/attempt | `MAREF-030`, `MAREF-037` |
| `codex1`, `codex2` | Governed aliases and provider map are explicit ([dispatcher](../../../scripts/multiagent_prompt_command.py#L93-L103)); Codex JSONL parser is fail-closed ([parser](../../../scripts/multiagent_prompt_command.py#L2713-L2777)) | Preserve Result Contract v2 and output-schema adapter; typed failure on unavailable alias | Codex thread ID is correlation only; adapter cannot invent approval/lease/evidence | `MAREF-031`, `MAREF-033`, `MAREF-037` |
| `agy1`, `agy2` | Explicit aliases plus native stream-JSON parser ([dispatcher](../../../scripts/multiagent_prompt_command.py#L93-L103), [parser](../../../scripts/multiagent_prompt_command.py#L2780-L2824)) | Preserve AGY event dialect, in-process validation and typed result; no prose inference fallback | AGY conversation ID is correlation only; success remains validated in-process only | `MAREF-032`, `MAREF-033`, `MAREF-037` |
| OpenAI HTTP | Current `httpx` call uses `/chat/completions` ([router](../../../project/api_router.py#L387-L420)) | Mandatory model-I/O fallback; later Responses HTTP may be added behind the same adapter contract | Server-side key only; zero-cost policy may block direct paid route | `MAREF-035`, `MAREF-037` |
| OpenAI Responses WebSocket | Not currently implemented; no `response.create`/`previous_response_id` path | Optional server-side latency adapter with HTTP fallback, 60-minute rotation and reconnect recovery policy | Never event/session/approval/lease/fence authority; no browser key | `MAREF-035`, `MAREF-037` |
| Gemini / Cloudflare / Vertex / Ollama HybridRouter | Routes are built for local/cloud modes ([HybridRouter](../../../project/api_router.py#L554-L619)) and executed by provider type ([generate](../../../project/api_router.py#L623-L716)) | Compatibility model-I/O surfaces with typed capability/unavailable/zero-cost rejection | Existing provider behavior is preserved; none writes canonical transitions | `MAREF-014`, `MAREF-035`, `MAREF-037` |
| Local macOS ARM64 | MLX tooling targets Apple Silicon ([MLX extractor](../../../scripts/extract_dataset_mlx.py#L3-L25)); dispatcher uses POSIX `fcntl` when present ([dispatcher](../../../scripts/multiagent_prompt_command.py#L13-L16)) | SQLite WAL dev adapter, native/POSIX subprocess adapter, local conformance profile | Single-host only; local locks cannot prove production lease | `MAREF-022`, `MAREF-037` |
| Linux / Docker | Docker builds Linux Rust and Python runtime ([Dockerfile](../../../Dockerfile#L3-L33)) | Direct PostgreSQL driver/pool selected and pinned by MAREF-021; POSIX runtime plus typed non-POSIX unsupported behavior | Multi-host canonical state stays in Postgres, not container disk; POSIX locks are host defense only | `MAREF-021`, `MAREF-037`, `MAREF-053` |
| HF Docker Rust -> FastAPI/Python | Image builds Rust gateway, PyO3 wheel and Python app artifacts ([Dockerfile](../../../Dockerfile#L46-L70)) | Modular-monolith composition root in the HF Docker unit; authenticated internal command entry plus sanitized read/SSE boundary | No public/browser direct writer; Rust/FastAPI are not second writers; no mandatory internal network hop | `MAREF-005`, `MAREF-036`, `MAREF-056` |
| Vercel static boundary | Vercel routes browser API traffic through backend proxy rewrites ([vercel.json](../../../vercel.json#L1-L28)); Rule 07 makes it static UI | Authenticated command client and sanitized SSE notification consumer only | No provider/database/signing/lease keys; no direct canonical mutation | `MAREF-036`, `MAREF-037`, `MAREF-057` |
| JSON / JSONL / FAISS | HITL writes JSONL, saves FAISS and schedules training in one path ([HITL](../../../project/hitl_router.py#L835-L899)); FAISS persists index + metadata ([store](../../../project/rag/vector_store.py#L296-L330)) | Versioned immutable generation/effect adapters with idempotency and Saga compensation | Files/indexes are effect outputs, not canonical workflow state; activation is separate | `MAREF-041`, `MAREF-043`, `MAREF-044` |
| Supabase / Postgres | Current Supabase client is REST/httpx-based for domain datasets/checkpoints ([client](../../../project/core/supabase_db.py#L1-L43)); no direct PostgreSQL driver is declared in `pyproject.toml`/`requirements.txt` | Supabase/domain REST remains an effect/data adapter; MAREF-021 selects/pins one direct PostgreSQL driver and pool for transactions/`SKIP LOCKED` | Supabase REST is insufficient for canonical multi-row transactions/lease allocation; browser/anon/service key cannot grant authority | `MAREF-021`, `MAREF-037`, `MAREF-043` |
| MLX / Kaggle / OpenAI fine-tune effects | MLX runner is local; Kaggle orchestrator exists; OpenAI adapter uploads and creates job ([external adapter](../../../project/rag/external_finetune.py#L20-L63)) | P2-P4 effect adapters with scoped approval, idempotency key, receipt and unknown-outcome reconciliation | No automatic/forced training before Saga; paid/external action needs fresh approval | `MAREF-040..044`, `MAREF-056` |
| GitHub Actions | Active workflows include CI, HF Docker, Kaggle and governance under `.github/workflows/` | Contract, migration, platform-conformance, secret-scan and release gates; dry validation before external run | Workflow/config is intent; Actions receipt cannot bypass command/approval/store authority | `MAREF-037`, `MAREF-054..057` |

## Explicitly excluded, prohibited, or historical

| Surface | Disposition |
|---|---|
| Fly.io | Retired and prohibited by Rule 07; retain history only, no adapter/release route |
| Public Azure | Historical/inactive and prohibited for public ingress/release |
| HF Static backend | Prohibited for the Docker backend; Vercel owns static UI |
| Direct browser provider keys | Prohibited; all model/provider I/O is server-side |
| OpenAI Realtime / WebRTC | Out of scope; Responses WebSocket is not Realtime |

## Common conformance contract

Every adapter declares closed fields for: adapter name/version; supported
contracts/transports; streaming, resume, cancel and idempotency support;
read-only mode and portable-receipt support; ordering and durability scope;
concurrency and payload/event limits; billing class; retention mode;
`observed_at`, `expires_at` and provenance digest; preserved, unavailable and
dropped fields; auth/fallback; and typed `expired`, `unknown`, `unsupported` or
`unavailable` results.

Canonical fields stay at the platform-neutral root. Provider/platform values
must be inside an adapter namespace as opaque correlation metadata and cannot
be consulted by reducers, approvals, leases/fences, attempts, idempotency,
capacity, effects or release decisions. Conformance rejects unknown root
fields, canonical data supplied only through opaque metadata, metadata
promotion, secret-bearing evidence, identity substitution, cross-session
grants, stale fences, silent loss, expired/unknown capability treated as
success, and invented evidence absent from the source platform.

Read/notification adapters also disclose `stale`, projection/as-of version,
last event/sequence, `authority_epoch`, `read_at` and lag. Stale or unavailable
Authority Plane state cannot authorize mutation, lease, approval or blind retry.
