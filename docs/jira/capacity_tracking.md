# Jira Capacity Tracking — AI Agent Effort

## Overview
Track effort per AI agent/specialist without using Jira Assignee (account_id rejected in KAN project).

## Severity to Effort Labels

> ⚠️ Note: `customfield_10020` (Story Points) is NOT available in KAN next-gen project.
> Using `effort-N` labels as the workaround.

| Severity | Story Points | Color |
|----------|-------------|-------|
| CRITICAL | 13 | 🔴 |
| HIGH | 8 | 🟠 |
| MEDIUM | 5 | 🟡 |
| LOW | 3 | 🟢 |

## Agent Labels (use instead of Assignee)

| Specialist Role | Jira Label |
|-----------------|------------|
| agy1 (lead_ba) | `agent-agy1` |
| codex1 (developer_core) | `agent-codex1` |
| codex2 (developer_api) | `agent-codex2` |
| codex3 (qa_tester) | `agent-codex3` |
| ba_auditor | `agent-ba_auditor` |
| ba_intake | `agent-ba_intake` |
| lead_ba | `agent-lead_ba` |
| code_reviewer | `agent-code_reviewer` |

## Dashboard Gadgets (PO Monitoring)

### 1. Created vs. Resolved
- **JQL**: `project = KAN AND "Epic Link" = KAN-38`
- **Purpose**: Overall progress timeline

### 2. Two-Dimensional Filter Statistics
- **JQL**: `project = KAN AND "Epic Link" = KAN-38`
- **X-axis**: `labels`
- **Y-axis**: `status`

### 3. Pie Chart (Issue Statistics)
- **JQL**: `project = KAN AND "Epic Link" = KAN-38`
- **Statistic Type**: `labels`

### 4. Issue Statistics (Effort by Agent)
- **JQL**: `project = KAN AND "Epic Link" = KAN-38`
- **Statistic Type**: `labels`
- **Filter**: Use `effort-*` labels (effort-13, effort-8, effort-5, effort-3)
- *(Story Points field `customfield_10020` is not available in next-gen projects)*

## Automation Rules

### Rule: Add Effort Label on Creation
- **Trigger**: Issue Created
- **Condition**: Summary contains "CRITICAL" / "HIGH" / "MEDIUM" / "LOW"
- **Action**: Add label `effort-13` / `effort-8` / `effort-5` / `effort-3`

### Rule: Transition Parent When All Sub-tasks Done
- **Trigger**: Issue transitioned to Done
- **Condition**: Parent has all sub-tasks Done
- **Action**: Transition parent to Done (ID: 51)

## Agent Effort Summary (KAN-43 → KAN-66)

|| Sub-task | Agent | Effort | Severity | Sprint ||
||----------|-------|--------|----------|-------||
|| KAN-43 (A8.1, Val. bypass) | agent-agy1 | 13 | CRITICAL | Sprint A ||
|| KAN-44 (A8.2, Merkle DAG) | agent-agy1 | 13 | CRITICAL | Sprint A ||
|| KAN-45 (A1, env vars) | agent-agy1 | 8 | HIGH | Sprint A ||
|| KAN-46 (A2, model defaults) | agent-agy1 | 8 | HIGH | Sprint A ||
|| KAN-47 (A6, api_router.py) | agent-agy1 | 8 | HIGH | Sprint A ||
|| KAN-48 (B4, fast_return) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-49 (C1, solar_time.py) | agent-agy1 | 3 | LOW | Sprint C ||
|| KAN-50 (B1, validator.py) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-51 (A3, README C4) | agent-codex1 | 5 | MEDIUM | Sprint A ||
|| KAN-52 (A4, README model table) | agent-codex1 | 5 | MEDIUM | Sprint A ||
|| KAN-53 (A5, README env docs) | agent-codex1 | 5 | MEDIUM | Sprint A ||
|| KAN-54 (A7, api_router docstring) | agent-codex2 | 5 | MEDIUM | Sprint A ||
|| KAN-55 (B1, validator.py) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-56 (B2, v3_engine_adapter) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-57 (B3, solar_time docs) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-58 (B5, config.py) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-59 (B6, debate.py) | agent-codex2 | 5 | MEDIUM | Sprint B ||
|| KAN-60 (B7, README) | agent-codex1 | 5 | MEDIUM | Sprint B ||
|| KAN-61 (B8, .env.example) | agent-agy1 | 5 | MEDIUM | Sprint B ||
|| KAN-62 (B9, test files) | agent-codex3 | 5 | MEDIUM | Sprint B ||
|| KAN-63 (B10, Dockerfile) | agent-code_reviewer | 5 | MEDIUM | Sprint B ||
|| KAN-64 (C2, config.py Decimal) | agent-codex1 | 3 | LOW | Sprint C ||
|| KAN-65 (C3, README formatting) | agent-lead_ba | 3 | LOW | Sprint C ||
|| KAN-66 (C4, .env.example cleanup) | agent-agy1 | 3 | LOW | Sprint C ||

**Total effort: 137 points** (50 CRITICAL+HIGH, 75 MEDIUM, 12 LOW) — 24 sub-tasks — tracked via `effort-*` labels + Agent labels
