# Jira Dashboard: HoroConsultant Audit Monitor

## Overview
Dashboard for PO monitoring of Epic KAN-38 (HOROC Audit Remediation) and all child issues.

## Dashboard Details
- **Name**: HoroConsultant Audit Monitor
- **Description**: Tracking KAN-38 audit remediation progress across Sprints A/B/C/D
- **Share Permissions**: Project KAN (10000)
- **Owner**: Pansakorn Phothidaen (accountId: 557058:56aab1ce-...)

## Gadgets Configuration

### 1. Epic Progress (Roadmap Gadget)
- **Filter**: `key = KAN-38`
- **Metric**: Sprint A/B/C/D completion percentage
- **Data**: Epic → child Task progress

### 2. Issue Statistics (Two-Dimensional Filter Statistics)
- **Filter**: `parent = KAN-38 ORDER BY priority DESC`
- **X-Axis**: Priority (Highest, High, Medium, Low)
- **Y-Axis**: Status (Done, In Progress, To Do)
- **Data**: Count of sub-tasks by severity × status

### 3. Sprint Health (Filter Results Gadget)
- **Filter**: `parent = KAN-38 AND status != Done ORDER BY priority DESC`
- **Columns**: Key, Summary, Priority, Labels, Assignee
- **Refresh**: Every 15 minutes

### 4. Timeline Tracking (Created vs. Resolved Chart)
- **Filter**: `project = KAN AND parent = KAN-38`
- **Period**: Last 30 days
- **Data**: created vs resolutiondate comparison
- **Metric**: Effort = DATEDIFF(created, resolutiondate)

## JQL Saved Searches
```jql
# All audit sub-tasks completed
parent = KAN-38 AND issuetype = Sub-task AND status = Done

# In-progress work
parent = KAN-38 AND status != Done ORDER BY priority DESC

# By severity
parent = KAN-38 AND labels = audit-critical AND status = Done
parent = KAN-38 AND labels = audit-high AND status = Done
parent = KAN-38 AND labels = audit-medium AND status = Done
parent = KAN-38 AND labels = audit-low AND status = Done

# By sprint
parent = KAN-38 AND labels = sprint-a AND status = Done
parent = KAN-38 AND labels = sprint-b AND status = Done
parent = KAN-38 AND labels = sprint-c AND status = Done
parent = KAN-38 AND labels = sprint-d AND status != Done
```

## REST API: Create Dashboard
```bash
curl -X POST \
  --url "https://pansakorn.atlassian.net/rest/api/3/dashboard" \
  --header "Authorization: Basic <BASE64_EMAIL:API_TOKEN>" \
  --header "Content-Type: application/json" \
  --data '{
    "name": "HoroConsultant Audit Monitor",
    "description": "PO monitoring for KAN-38 audit remediation",
    "sharePermissions": [{"type": "project", "project": {"id": "10000"}}]
  }'
```

## REST API: Add Gadget
```bash
curl -X POST \
  --url "https://pansakorn.atlassian.net/rest/api/3/dashboard/{dashboardId}/gadget" \
  --header "Authorization: Basic <BASE64_EMAIL:API_TOKEN>" \
  --header "Content-Type: application/json" \
  --data '{
    "gadgetUri": "com.atlassian.jira.gadgets:two-dimensional-filter-statistics-gadget",
    "config": {
      "filterId": "<filter_id>",
      "statisticType": "priority",
      "secondaryStatisticType": "status"
    }
  }'
```

> Note: Jira requires manual UI setup for initial dashboard+gadgets, then GET API to capture config for automation.

## Dashboard Metrics for PO
| Metric | JQL Source | Dashboard Gadget |
|--------|------------|-----------------|
| Audit Completion | `parent = KAN-38 AND status = Done` | Issue Statistics |
| Severity Distribution | `parent = KAN-38 ORDER BY priority` | Two-Dimensional Filter |
| Sprint Progress | `labels = sprint-X AND status = Done` | Filter Results |
| Effort Timeline | `created vs resolutiondate` | Created vs Resolved Chart |
| Velocity | `assignee IS NOT EMPTY AND status = Done` | Two-Dimensional Filter |