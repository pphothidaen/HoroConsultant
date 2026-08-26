# ADR-003 — Commands, Notifications, and OpenAI Responses WebSocket

**Status:** Accepted target transport split.

## Current facts

- OpenAI-compatible inference posts HTTP to `/chat/completions`
  ([router](../../../project/api_router.py#L387-L420)).
- Browser consultation streaming is FastAPI `StreamingResponse` with
  `text/event-stream`
  ([chat router](../../../project/routers/chat.py#L46-L70)).
- Repository search finds no implemented `response.create` or
  `previous_response_id` path. Therefore current code does **not** implement
  OpenAI Responses WebSocket.
- Neither `pyproject.toml` nor `requirements.txt` declares `websockets` as a
  direct dependency. Its presence in `uv.lock` is transitive evidence only and
  does not authorize a runtime import.

## Target decision

1. Internal commands use authenticated REST; one-way notifications use SSE and
   durable cursors by default. Add internal WebSocket only after a measured
   duplex requirement. Commit/outbox precedes notification.
2. OpenAI Responses WebSocket is an optional server-side model-I/O adapter.
   HTTP fallback is mandatory. It is never event ordering, approval, lease,
   attempt, fence, session or identity authority.
3. Browser provider keys, OpenAI Realtime and WebRTC are out of scope.
4. HTTP-only startup must not import or require `websockets`. MAREF-035 may add
   one selected, pinned direct dependency to `pyproject.toml`,
   `requirements.txt` and `uv.lock` only if the optional WS adapter is actually
   implemented, and only in a sequential manifest lane after MAREF-021 freezes
   its PostgreSQL-driver dependency edits. No version is chosen in C0.

## Provider facts and adapter limits

The [official OpenAI WebSocket Mode guide](https://developers.openai.com/api/docs/guides/websocket-mode)
states same-stream FIFO while different streams may interleave, up to 16 active
in-flight responses, 32 named stream IDs and a 60-minute connection lifetime.
The adapter must rotate/reconnect before expiry, demultiplex cross-stream
events, and resynchronize from canonical state. With `store=false` or Zero Data
Retention, reconnect recovery cannot assume server-stored response context; the
adapter must use an approved recovery/fallback path and fail closed if context
cannot be reconstructed.

The guide's up-to-roughly-40% observation applies only to rollouts with 20+
tool calls. It is not a latency guarantee, SLA or justification to remove HTTP.
A WebSocket reconnect alone does not end an unchanged authenticated canonical
ControlPlane session.
