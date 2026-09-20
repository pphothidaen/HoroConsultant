# Jira Sync Protocol — HoroConsultant

## Overview
Jira (Atlassian Cloud) is used **alongside** the existing markdown-based task system (ATOMIC_TICKET.md).
Both systems maintain the same work items in parallel.

## Jira Instance
- **URL**: https://pansakorn.atlassian.net
- **Project**: KAN (Hermes Agent Team)
- **Epic**: KAN-38 (HOROC Audit Remediation)
- **Cloud ID**: 45765a55-d652-421c-8096-940cebfd0bf7

## Issue Hierarchy
Epic KAN-38 (HOROC Audit Remediation)
├── KAN-39 Task — Sprint A: CRITICAL+HIGH (A1-A8) — DONE
├── KAN-40 Task — Sprint B: MEDIUM (B1-B10) — DONE
├── KAN-41 Task — Sprint C: LOW (C1-C4) — DONE
└── KAN-42 Task — Sprint D: Jira Migration — IN PROGRESS

## Sync Protocol

### 1. Source of Truth
- Jira = source of truth for **work status** and **sprint progress**
- ATOMIC_TICKET.md = source of truth for **local offline reference** and **detailed test specs**

### 2. Mapping
| ATOMIC_TICKET.md | Jira |
|---|---|
| A1-A8 / B1-B10 / C1-C4 | Child Tasks under relevant Sprint Task |
| Sprint labels (sprint-a, etc.) | Jira Labels |
| Severity (CRITICAL/HIGH/MEDIUM/LOW) | Jira Priority |
| TDD state (RED/GREEN/REVIEW) | Jira Status |

### 3. JQL Saved Searches
```jql
# Completed audit work
parent = KAN-38 AND issuetype = Task AND status = Done

# In-progress sprint work
parent = KAN-38 AND issuetype = Task AND status != Done
ORDER BY priority DESC

# All audit findings
parent = KAN-38 ORDER BY issuetype DESC, priority DESC
```

### 4. TDD Workflow in Jira
| TDD Phase | Jira Status | Transition ID |
|---|---|---|
| RED (tests written, failing) | TDD RED | 21 |
| GREEN (fixes applied) | TDD GREEN | 31 |
| Review (audit complete) | Review | 41 |
| Done | Done | 51 |
| Not started | Ready | 11 |

### 5. Sync Cadence
- Sprint Tasks: transitioned in Jira immediately after completion
- Individual tickets: created as child Tasks under Sprint Tasks
- ATOMIC_TICKET.md: updated with Jira key references

### 6. Specialist Assignment
Issues are assigned per 6-Lane Concurrency:
- `ba_auditor` → audit findings (read-only)
- `qa_tester` → RED phase (test creation)
- `developer_core` → GREEN phase (code fixes)
- `code_reviewer` → RED TEAM audit

### 7. Known Issues
- `assignee_account_id` may fail if user lacks Jira license — leave unassigned or use email
- Batching Atlassian tool calls fails — use single calls
- `AI_ZERO_COST_ONLY` account ID format: `557058:56aab1ce-116f-4d33-b261-05f55ad671e3`
