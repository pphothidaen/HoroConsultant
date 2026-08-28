---
description: REST and WebSocket API architecture, response envelope, and authentication standards.
paths: "api/**/*, project/api/**/*, project/main.py"
---

# API Governance & Contract Standards

## Architecture & Response Envelope
- All REST API endpoints must return structured JSON responses within the standard envelope:
  ```json
  {
    "status": "success",
    "data": { ... },
    "error": null,
    "timestamp": "2026-08-28T00:00:00Z"
  }
  ```
- Error responses must provide deterministic error codes and sanitized message bodies without leaking stack traces.

<important if="modifying_endpoints">
- Always enforce schema validation pipes via Pydantic models.
- Ensure CORS, rate limiting, and input sanitization are configured on all public routes.
- WebSockets must handle graceful disconnection and heartbeat checks.
</important>

<important if="handling_websockets">
- Maintain connection heartbeat every 30 seconds.
- Buffer stream tokens gracefully and handle client disconnect without process termination.
</important>
