# Jira API Token Setup

## API Token Created

**Token Name**: `HOROC_REST_API`
**Created**: 2026-10-09 via kapture MCP browser automation
**Token**: `<REDACTED — revoked/rotated, see local secret store>`

### Usage in curl:
```bash
TOKEN="${JIRA_API_TOKEN:?set JIRA_API_TOKEN}"
AUTH=$(echo -n "pansakorn@gmail.com:$TOKEN" | base64)
curl -H "Authorization: Basic $AUTH" ...
```

---

## Option 1: OAuth Token (Already Available from twg)

The `twg login` command stores OAuth tokens at `~/.config/twg/auth.conf`:

```bash
# View tokens
cat ~/.config/twg/auth.conf

# Key fields:
# oauth-access-token=eyJraW... (use as Bearer token)
# oauth-refresh-token=eyJraW... (for renewal)
# cloud-id=45765a55-d652-421c-8096-940cebfd0bf7
# site=pansakorn
# domain=pansakorn.atlassian.net
```

### Usage in curl:
```bash
TOKEN=$(grep 'oauth-access-token' ~/.config/twg/auth.conf | cut -d'=' -f2)
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     "https://pansakorn.atlassian.net/rest/api/3/myself"
```

---

## Option 2: Personal API Token (Created Above)

Created via browser automation on 2026-10-09:
- **Token**: `HOROC_REST_API`
- **Value**: `<REDACTED — revoked/rotated, see local secret store>`

### Usage in curl:
```bash
# Base64 encode: email:api_token
AUTH=$(echo -n "pansakorn@gmail.com:${JIRA_API_TOKEN:?set JIRA_API_TOKEN}" | base64)
curl -H "Authorization: Basic $AUTH" \
     -H "Content-Type: application/json" \
     "https://pansakorn.atlassian.net/rest/api/3/myself"
```

---

## Option 3: OAuth for Automation API

For the Automation REST API (at `api.atlassian.com`), use the OAuth token from twg:
```bash
OAUTH_TOKEN=$(grep 'oauth-access-token' ~/.config/twg/auth.conf | cut -d'=' -f2)
curl -H "Authorization: Bearer $OAUTH_TOKEN" \
     -H "Content-Type: application/json" \
     "https://api.atlassian.com/automation/public/jira/45765a55-d652-421c-8096-940cebfd0bf7/rest/v1/rule"
```

---

## Token Scopes Required

For Plans + Automation Rules, the token/user needs:
- **Jira Administrator** or **Project Administrator** on KAN project
- **Jira Premium/Enterprise** (required for Advanced Roadmaps / Plans)
- **Automation** permissions (project or global)

### Check current permissions:
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "https://pansakorn.atlassian.net/rest/api/3/myself" | jq '.accountId, .displayName'
```

---

## Environment Variables (Recommended)

Add to `~/.zshrc` or shell profile:
```bash
export JIRA_OAUTH_TOKEN="eyJraW..."
export JIRA_CLOUD_ID="45765a55-d652-421c-8096-940cebfd0bf7"
export JIRA_DOMAIN="pansakorn.atlassian.net"
```

Then use in scripts:
```bash
curl -H "Authorization: Bearer $JIRA_OAUTH_TOKEN" \
     -H "Content-Type: application/json" \
     "https://$JIRA_DOMAIN/rest/api/3/..."
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired | Re-run `twg login` or refresh OAuth token |
| `403 Forbidden` | Insufficient permissions | Grant Project Admin on KAN, or use site admin token |
| `404 Not Found` | Wrong endpoint/cloud ID | Verify cloud-id matches; Plans requires `/rest/plans/1.0` |
| `429 Too Many Requests` | Rate limited | Add `sleep 2` between calls; check `Retry-After` header |

---

## Refreshing OAuth Token (if expired)

```bash
# twg handles this automatically on next command
twg doctor  # triggers refresh if needed

# Manual refresh (if needed):
# POST to https://auth.atlassian.com/oauth/token with refresh_token
```