# Jira REST API Workflow for HOROC Project

## Overview
This document describes the workflow for using Atlassian REST API directly to create Jira Plans and Automation Rules that are not supported by twg CLI.

## Authentication

### OAuth 2.0 (Preferred - Already Configured)
The `twg login` command stores OAuth tokens at `~/.config/twg/auth.conf`:
- `oauth-access-token` — For API calls (expires, auto-refreshed by twg)
- `oauth-refresh-token` — For token renewal
- `cloud-id` — Cloud instance identifier (required for some endpoints)

### Alternative: API Token
If OAuth fails, create a personal API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Use: `Authorization: Basic base64(email:api_token)`

---

## Base URLs
| Environment | Base URL |
|-------------|----------|
| Jira Cloud (Standard) | `https://pansakorn.atlassian.net/rest/api/3` |
| Jira Plans (Advanced Roadmaps) | `https://pansakorn.atlassian.net/rest/plans/1.0` |
| Automation Rules | `https://pansakorn.atlassian.net/rest/api/3/automation` |

---

## Common Headers
```bash
# OAuth (using access token from twg)
-H "Authorization: Bearer <oauth-access-token>"
-H "Content-Type: application/json"
-H "Accept: application/json"
```

---

## 1. Jira Plans (Advanced Roadmaps)

### Create a Plan
```bash
curl -X POST "https://pansakorn.atlassian.net/rest/plans/1.0/plan" \
  -H "Authorization: Bearer <oauth-access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HOROC Audit Remediation",
    "description": "Plan for audit remediation across Sprints A-D",
    "projects": ["KAN"],
    "privacy": "private",
    "planType": "scrum"
  }'
```

### Add Issues to Plan
```bash
# After plan creation, get planId from response
curl -X POST "https://pansakorn.atlassian.net/rest/plans/1.0/plan/{planId}/issue" \
  -H "Authorization: Bearer <oauth-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"issueIds": ["KAN-38", "KAN-39", "KAN-40", "KAN-41", "KAN-42"]}'
```

### Configure Plan Views (Sprints, Teams, Releases)
```bash
# Add sprints
curl -X POST "https://pansakorn.atlassian.net/rest/plans/1.0/plan/{planId}/sprint" \
  -H "Authorization: Bearer <oauth-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"sprints": [{"name": "Sprint A", "startDate": "2026-09-01", "endDate": "2026-09-14"}]}'
```

---

## 2. Automation Rules

### Rule Structure (Common to all 6 rules)
```json
{
  "name": "Rule Name",
  "description": "Rule description",
  "trigger": {
    "type": "jira.issue.created",
    "configuration": {
      "projectKey": "KAN",
      "issueType": "Sub-task"
    }
  },
  "conditions": [],
  "actions": [],
  "enabled": true
}
```

### 6 Rules to Create

| # | Rule Name | Trigger | Conditions | Actions |
|---|-----------|---------|------------|---------|
| 1 | Auto-assign agent by sub-task path | Issue created | Path matches `agent-*/**` | Assign to user from label |
| 2 | Auto-assign agent by label | Issue created | Label matches `agent-*` | Assign to user from label |
| 3 | Sprint transition on sub-task Done | Issue transitioned to Done | All sibling sub-tasks Done | Transition parent sprint task to Done |
| 4 | Enforce effort label on create | Issue created | No `effort-*` label | Comment asking for effort label |
| 5 | Notify on CRITICAL/HIGH creation | Issue created | Priority = CRITICAL or HIGH | Slack/email notification |
| 6 | Auto-assign Team by agent label | Issue created | Label `agent-*` exists | Add Team from mapping |

### Create Rule via API
```bash
curl -X POST "https://pansakorn.atlassian.net/rest/api/3/automation/rule" \
  -H "Authorization: Bearer <oauth-access-token>" \
  -H "Content-Type: application/json" \
  -d @rule1.json
```

### Full Rule JSON Example (Rule 1)
See `automation_rules.md` for complete JSON payloads.

---

## Rate Limits
- **Jira REST API**: 100 requests/second per user
- **Automation Rules**: Additional limits may apply
- **Best practice**: Add 1-2 second delay between calls

---

## Error Handling
Common error codes:
- `401` — Authentication failed (token expired)
- `403` — Insufficient permissions
- `404` — Resource not found
- `429` — Rate limited (retry after `Retry-After` header)

---

## Verification Commands
```bash
# List plans
curl -H "Authorization: Bearer <token>" \
  "https://pansakorn.atlassian.net/rest/plans/1.0/plan"

# List automation rules
curl -H "Authorization: Bearer <token>" \
  "https://pansakorn.atlassian.net/rest/api/3/automation/rule?projectKey=KAN"
```

---

## Appendix: Files in This Workflow
- `automation_rules.md` — JSON templates for 6 rules
- `remaining_ui_tasks.md` — Task tracking for Plans + Rules
- `twg_commands_reference.md` — twg CLI commands used
- `api_token_setup.md` — How to create/use API tokens