# Jira Webhook Integration Guide

This document describes how to configure the Jira Cloud webhook for the
HoroConsultant autonomous-worker platform, including HMAC signature
validation, available endpoints, and Telegram alert wiring.

## Environment Variables

All webhook-related configuration is loaded from environment variables
(via `.env` or your secret manager). Below is the canonical reference
for `.env.example`:

```bash
# ── Jira Webhook ──────────────────────────────────────────────
JIRA_WEBHOOK_SECRET=replace_with_secure_random_hex_32
JIRA_WEBHOOK_URL=https://your-app.example.com/webhook

# ── Telegram Alerts (optional) ─────────────────────────────────
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjkl...
TELEGRAM_CHAT_ID=-1001234567890

# ── Discord Alerts (optional) ──────────────────────────────────
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# ── Dry-Run Mode ───────────────────────────────────────────────
MLOPS_DRY_RUN=false
```

| Variable | Required | Description |
|---|---|---|
| `JIRA_WEBHOOK_SECRET` | Yes | HMAC-SHA256 secret used to validate incoming webhook payloads from Jira. Generate with `openssl rand -hex 32`. |
| `JIRA_WEBHOOK_URL` | Yes | The public URL registered as the webhook endpoint in the Atlassian admin console. |
| `TELEGRAM_BOT_USERNAME` | No | Telegram bot username (alternative to token, used by some Bot API wrappers). |
| `TELEGRAM_BOT_TOKEN` | No | Telegram Bot API token (from [@BotFather](https://t.me/BotFather)). Required for Telegram alerts. |
| `TELEGRAM_CHAT_ID` | No | Target chat ID (user, group, or channel) for Telegram alerts. |
| `DISCORD_WEBHOOK_URL` | No | Discord incoming webhook URL for alert delivery. |
| `MLOPS_DRY_RUN` | No | When `true`, external notification delivery is skipped (logging only). Defaults to `false`. |

## Configuring the Webhook in Jira

1. Navigate to **Jira Settings** → **Apps** → **Webhooks** (or
   **Project settings** → **Webhooks** for project-scoped webhooks).

2. Click **Create a webhook**.

3. Fill in the form:

   | Field | Value |
   |---|---|
   | **Name** | `HoroConsultant Autonomous Worker` |
   | **URL** | Value of `JIRA_WEBHOOK_URL` (e.g. `https://your-app.example.com/webhook`) |
   | **Secret** | Value of `JIRA_WEBHOOK_SECRET` (must match exactly) |
   | **Exclude issue details** | `Off` (default; the handler needs full payload data) |

4. Select the events you want to receive. The handler supports:
   - **Issue created** — auto-creates a worker ticket
   - **Issue updated** — updates ticket status
   - **Issue deleted** — releases associated lease

5. Click **Save**.

6. Test the webhook with the **Test connection** button in the modal.

## Endpoints

All endpoints are mounted under the Jira router with the prefix
`/jira`. The public-facing webhook URL is `/webhook` (see below).

### `POST /webhook` — Jira Webhook Handler

Accepts Jira Cloud webhook payloads, validates the HMAC-SHA256
signature, sanitizes the payload, and processes ticket lifecycle events.

**Request:**
- **Headers:**
  - `Content-Type: application/json`
  - `X-Atlassian-Event: jira:issue_created` (or `jira:issue_updated`,
    `jira:issue_deleted`)
  - `X-Atlassian-Webhook-Identifier: <uuid>`
  - `X-Hub-Signature: sha256=<hmac-sha256-signature>`
- **Body:** Jira webhook JSON payload (see
  [Atlassian documentation](https://developer.atlassian.com/cloud/jira/platform/webhooks/principls))
  for the full schema.

**Responses:**
| Status | Description |
|---|---|
| `200` | Payload accepted and processed |
| `400` | Empty body or malformed JSON |
| `401` | HMAC signature mismatch or empty body |
| `403` | Suspicious payload detected (injection pattern) |
| `429` | Rate-limited (dedup window not elapsed) |

**HMAC Validation:**
The handler computes `hmac-sha256(secret, body)` and compares it
against the `X-Hub-Signature` header using `hmac.compare_digest`
for constant-time comparison.

### `POST /tickets/{id}/claim` — Claim a Ticket

Claims a Jira ticket for an autonomous worker process, returning
a leasing token that must be presented for subsequent operations.

### `POST /lease/release` — Release a Lease

Releases a previously claimed ticket lease. This endpoint triggers
an `RELEASED` lifecycle alert via the `WebhookNotifier`.

## Telegram Alert Notifications

When a Jira webhook event is received, the `WebhookNotifier` sends
alerts to configured Telegram (and optionally Discord) channels.

### Alert Types

| Event | Emoji | Status | Trigger |
|---|---|---|---|
| Ticket Claimed | 🎫 | `CLAIMED` | Webhook handler receives a valid payload |
| Suspicious Payload | 🔓 | `SUSPICIOUS` | Payload contains injection patterns |
| Lease Released | 🔒 | `RELEASED` | Lease release endpoint is called |
| Lease Fenced | 🚧 | `FENCED` | Lease release denied (conflicting owner) |

### Alert Format

```
[CLAIMED] Jira Webhook: ticket TICKET-123 claimed by worker
Status: CLAIMED
---
Event: jira:issue_created
Ticket: TICKET-123
Owner:  autonomous-worker
Time:   2025-01-15T10:30:00Z
```

### WebhookNotifier

The notifier is implemented in `project/mlops/notifications/webhook_notifier.py`
and exposes the `notify_jira_webhook_event` method:

```python
from project.mlops.notifications.webhook_notifier import WebhookNotifier

notifier = WebhookNotifier()
notifier.notify_jira_webhook_event(
    event="CLAIMED",
    ticket_key="TICKET-123",
    owner="autonomous-worker",
    details={"endpoint": "/webhook", "ip": "10.0.0.1"},
)
```

## Security Considerations

1. **HMAC Secret Management:** The `JIRA_WEBHOOK_SECRET` should be
   generated with `openssl rand -hex 32` and stored in a secret
   manager (e.g., Doppler). Never commit the actual secret value —
   only the placeholder in `.env.example`.

2. **Constant-time Comparison:** The HMAC validation uses
   `hmac.compare_digest` to prevent timing attacks.

3. **Payload Sanitization:** All string fields from the webhook
   payload are passed through `jira.sanitizer` before being stored
   or logged, preventing XSS and injection attacks.

4. **Rate Limiting:** The dedup layer (`project/tests/test_webhook_dedup.py`)
   enforces a configurable rate window to prevent spam.

## Testing

Run the Jira webhook test suite:

```bash
python3 -m pytest tests/test_jira_webhook_router.py -v
```

Run the gateway contract test (validates OpenAPI golden snapshot):

```bash
python3 -m pytest project/tests/test_gateway_contract.py -v
```

## OpenAPI Schema

The OpenAPI contract snapshot is frozen at
`project/tests/goldens/openapi.json` and verified by
`test_gateway_contract.py`. Any new route or schema change requires
regenerating the golden file (see
[Architecture Design Spec](v3_api_specification.md)).
