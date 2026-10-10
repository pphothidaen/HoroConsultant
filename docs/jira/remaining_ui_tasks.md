# Remaining UI Tasks: Jira Plans + Automation Rules

## Status Overview
| Task | Tool | Status | Notes |
|------|------|--------|-------|
| Jira Plan "HOROC Audit Remediation" | REST API | ⚠️ Blocked | Requires "Administer Jira" global permission (user is project admin only) |
| Rule 1: Auto-set Priority & Effort Label | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Rule 2: Auto-assign Agent Label by File Path | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Rule 3: Auto-transition Parent to Done | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Rule 4: Auto-add Effort Label by Priority | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Rule 5: Auto-link Sub-task by Finding ID Pattern | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Rule 6: Auto-assign Team by Agent Label | REST API | ⚠️ Blocked | Complex component schema; 400/403 errors |
| Verify Plan in UI | Browser | ⬜ Not started | |
| Verify Rules in UI | Browser | ⬜ Not started | |

---

## Blockers Summary

### Jira Plans API
- **Endpoint**: `POST /rest/api/3/plans/plan`
- **Required permission**: "Administer Jira" global permission
- **Current user**: Project admin on KAN (not Jira admin)
- **Solution**: Either grant Jira admin to user, or create plan manually via UI at https://pansakorn.atlassian.net/jira/plans

### Automation Rules API
- **Endpoint**: `POST /gateway/api/automation/public/jira/{cloudId}/rest/v1/rule`
- **Schema**: Extremely complex (requires `components` array with TRIGGER/CONDITION/ACTION, schemaVersion=2154, proper parentId references)
- **Errors encountered**: 400 "request body could not be parsed", 403 Forbidden
- **Solution**: Create rules manually via UI at https://pansakorn.atlassian.net/jira/software/projects/KAN/settings/automation

---

## Detailed Tasks

### 1. Create Jira Plan
**Endpoint**: `POST /rest/plans/1.0/plan`
**Plan Configuration**:
- Name: "HOROC Audit Remediation"
- Description: "Plan for audit remediation across Sprints A-D"
- Projects: ["KAN"]
- Plan Type: "scrum"
- Privacy: "private"

**Follow-up**:
- Add existing issues: KAN-38 (Epic), KAN-39/40/41/42 (Sprint tasks)
- Configure sprints: Sprint A-D with dates
- Configure teams: Management, DevCore, DevAPI, QA, Security, BA
- Configure releases: v1.5.0-audit, v1.6.0, v1.7.0

---

### 2. Create 6 Automation Rules

All rules use project KAN.

#### Rule 1: Auto-assign agent by sub-task path
- **Trigger**: Issue created (Sub-task)
- **Condition**: Issue path contains `agent-*/**` (sub-task hierarchy)
- **Action**: Assign to user based on `agent-*` label mapping

#### Rule 2: Auto-assign agent by label
- **Trigger**: Issue created (any type)
- **Condition**: Label matches regex `agent-(agy[1-5]|codex[1-3]|ba_.*|developer_.*|qa_.*|code_reviewer)`
- **Action**: Assign to corresponding user account

#### Rule 3: Sprint transition on sub-task Done
- **Trigger**: Issue transitioned to Done
- **Condition**: All sibling sub-tasks under same parent are Done
- **Action**: Transition parent Task to Done

#### Rule 4: Enforce effort label on create
- **Trigger**: Issue created
- **Condition**: Issue has no `effort-*` label AND is Sub-task
- **Action**: Add comment requesting effort label (effort-13/8/5/3)

#### Rule 5: Notify on CRITICAL/HIGH creation
- **Trigger**: Issue created
- **Condition**: Priority = Highest (CRITICAL) or High (HIGH)
- **Action**: Send Slack/email notification to team

#### Rule 6: Auto-assign Team by agent label
- **Trigger**: Issue created
- **Condition**: Label `agent-*` exists
- **Action**: Add Team from mapping table:
  - `agent-agy*`, `agent-ba_*` → Management Team
  - `agent-developer_core` → DevCore Team
  - `agent-developer_api` → DevAPI Team
  - `agent-qa_tester` → QA Team
  - `agent-code_reviewer` → Security Team

---

## Verification Checklist

### Plan Verification
- [ ] Plan visible at https://pansakorn.atlassian.net/jira/plans
- [ ] All 5 issues (KAN-38 to KAN-42) added to plan
- [ ] Sprints A-D configured with correct dates
- [ ] All 6 teams visible in plan
- [ ] Releases configured

### Rules Verification
- [ ] All 6 rules visible at https://pansakorn.atlassian.net/jira/software/projects/KAN/settings/automation
- [ ] Rules enabled
- [ ] Test each rule by creating test sub-task
- [ ] Verify actions execute correctly

---

## Dependencies
- OAuth access token (from `~/.config/twg/auth.conf`)
- Project admin permissions on KAN
- Jira Premium/Enterprise (for Plans and advanced Automation)

---

## Rollback Plan
If any rule causes issues:
1. Disable rule via UI or API (`PATCH /rest/api/3/automation/rule/{ruleId}` with `"enabled": false`)
2. Delete rule if needed (`DELETE /rest/api/3/automation/rule/{ruleId}`)