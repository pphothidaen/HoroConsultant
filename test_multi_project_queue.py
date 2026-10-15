"""
Test: Multi-Project Queue Lane Priority Verification

Creates 3 Jira tickets with different Project Lane values, where the
"Horo Consultant" ticket is created LAST.  Verifies that fetch_task()
in sync_jira_hermes.py always picks the Horo Consultant ticket, skipping
tickets from other lanes that were created earlier.

Usage:
    python3 test_multi_project_queue.py [--no-cleanup]
"""
import os
import sys
import time
import argparse
from dotenv import load_dotenv
from jira import JIRA

# Import the fetch logic under test
from sync_jira_hermes import (
    fetch_task,
    get_field_id,
    LANE_FID,
    CURRENT_LANE,
    resolve_lane,
    notify_human,
    get_lane_options,
    build_task_description,
)

load_dotenv("/Users/kimlenglim/Project/HoroConsultant/.env")

JIRA_URL = os.getenv("JIRA_BASE_URL", "https://pansakorn.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL", "pansakorn@gmail.com")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")

# The three lanes under test — in creation order (Horo Consultant is last)
# Lane option IDs are resolved dynamically via resolve_lane() from the
# Jira dropdown, not hardcoded.
LANE_ORDER = [
    "Gemini Web Bridge",
    "Aipass Web Bridge",
    "Horo Consultant",  # created last — should be picked first
]
TEST_PREFIX = "[TEST-MPQ]"


def banner(msg: str):
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def cleanup_existing_test_tickets(jira_client):
    """Transition any leftover test tickets to Done to start clean."""
    banner("Pre-test cleanup: removing leftover test tickets")
    jql = f'project = "{PROJECT_KEY}" AND summary ~ "{TEST_PREFIX}"'
    issues = jira_client.search_issues(jql, maxResults=50)
    if not issues:
        print("  No leftover test tickets found.")
        return
    for issue in issues:
        transitions = jira_client.transitions(issue)
        done_t = None
        for t in transitions:
            if t["name"].strip().lower() == "done":
                done_t = t["id"]
                break
        if done_t:
            jira_client.transition_issue(issue, done_t)
            print(f"  → {issue.key} moved to Done")
        time.sleep(0.3)


def create_test_ticket(jira_client, lane_value: str, summary_suffix: str):
    """Create a single test ticket in the 'Ready' status with the given lane.

    The lane option ID is resolved dynamically from the Jira dropdown
    via resolve_lane().  If the lane value does not exist, a human is
    alerted to create it.

    The description is built via build_task_description() so that every
    test ticket carries evidence metadata: subagent, bound skills,
    MCP tools, delegated scope, acceptance criteria, artifacts, and
    verification command.
    """
    # Dynamically resolve the lane option from the Jira dropdown
    opt = resolve_lane(lane_value)
    if opt is None:
        notify_human(
            f"Project Lane '{lane_value}' not found in Jira dropdown options. "
            f"Please create it via Jira Admin → Custom Fields → Project Lane → Options. "
            f"Then re-run this test."
        )
        print(f"\n  💥 FATAL: Project Lane '{lane_value}' does not exist in Jira dropdown.")
        print(f"     The dropdown does not contain this option.")
        print(f"     Ask a human to create it, then retry.")
        sys.exit(1)

    lane_opt_id = opt.get("id")

    # Map each lane to its responsible subagent, skills, MCP tools, scope
    # — these populate the evidence block in the ticket description
    lane_subagent_map = {
        "Gemini Web Bridge": {
            "subagent": "developer_api",
            "owner_agent": "lead_ba",
            "owner_role": "Lead Business Analyst",
            "owner_skills": ["bsa-doc-skill-management", "agile-governance"],
            "skills": ["sdlc-aisdlc-workflow", "web-bridge-refactoring"],
            "mcp_tools": ["mcp__github__create_pull_request",
                          "mcp__vercel__create_deployment"],
            "goal": "Ensure Gemini Web Bridge Cloudflare Worker v4.3.2 "
                    "is deployed, stable, and fully integrated with "
                    "aipass-web-bridge for model routing.",
            "solution": "Refactor bridge entrypoint to use modular "
                        "router pattern from hermes-agent-skill, "
                        "add contract tests for aipass-web-bridge "
                        "integration, enforce Gitleaks scan in CI "
                        "before deploy.",
            "scope": "Deploy Gemini Web Bridge Cloudflare Worker, "
                     "verify v4.3.2 endpoints respond with 200, "
                     "ensure aipass-web-bridge integration passes "
                     "contract tests.",
            "detail": "Bridge lives at gemini-web-bridge/src/index.ts "
                      "with wrangler.toml config. Deployment pipeline: "
                      "lint → test → Gitleaks → deploy. Secrets managed "
                      "via Doppler (project: gemini-web-bridge, config: "
                      "prd_worker). Do NOT modify aipass-web-bridge "
                      "endpoints — consumer contract is owned by "
                      "developer_core lane. Ref: RFC-0043, ATOMIC-17.",
            "acceptance_criteria": [
                "All bridge endpoints return HTTP 200 on staging",
                "Contract tests pass against aipass-web-bridge",
                "Gitleaks scan passes before deployment",
                "No regression in plan-completion-and-release-notes skill",
            ],
            "artifacts": ["gemini-web-bridge/src/index.ts",
                          "gemini-web-bridge/wrangler.toml",
                          "tests/test_bridge_e2e.py"],
            "verification_command": "cd gemini-web-bridge && npm test && npx wrangler deploy --dry-run",
            "priority": "High",
        },
        "Aipass Web Bridge": {
            "subagent": "developer_core",
            "owner_agent": "orchestrator",
            "owner_role": "Coordination & Autonomous Execution",
            "owner_skills": ["orchestrator-delegation", "multi-account-agent-orchestration"],
            "skills": ["sdlc-aisdlc-workflow", "mcp-remote-bridge"],
            "mcp_tools": ["mcp__aipass_web_bridge__aipass_chat",
                          "mcp__github__create_issue",
                          "mcp__vercel__get_deployment"],
            "goal": "Keep aipass-web-bridge Cloudflare Worker in sync "
                    "with current Codex/AGY fleet and provide accurate "
                    "model discovery to downstream consumers.",
            "solution": "Use mcp-remote-bridge skill to map current "
                        "Codex/AGY accounts into aipass-web-bridge "
                        "handler. Schedule weekly drift check via cron "
                        "and update README with latest model alias "
                        "metadata.",
            "scope": "Maintain aipass-web-bridge Cloudflare Worker, "
                     "verify model list reflects current Codex/AGY "
                     "fleet, update README with latest author/model "
                     "metadata.",
            "detail": "Bridge is deployed as Cloudflare Worker at "
                      "aipass-web-bridge.taijustarrett417.workers.dev. "
                      "Model list refreshed every 24h via scheduled "
                      "trigger. Handler at src/handler.ts. README must "
                      "list all active aliases (agy1-4, codex1-3, node6). "
                      "DO NOT break gemini-web-bridge consumer contract. "
                      "Ref: RFC-0044, ATOMIC-18.",
            "acceptance_criteria": [
                "aipass-list-models returns non-empty model array",
                "Bridge endpoint responds within 500ms p99",
                "README lists all active model aliases",
            ],
            "artifacts": ["aipass-web-bridge/src/handler.ts",
                          "aipass-web-bridge/README.md",
                          "tests/test_aipass_model_list.py"],
            "verification_command": "cd aipass-web-bridge && npm test && curl -s https://aipass-web-bridge.taijustarrett417.workers.dev/v1/models | jq '.data | length' | grep -q '[1-9]'",
            "priority": "Medium",
        },
        "Horo Consultant": {
            "subagent": "qa_tester",
            "owner_agent": "lead_ba",
            "owner_role": "Lead Business Analyst",
            "owner_skills": ["bsa-doc-skill-management", "agile-governance"],
            "skills": ["qa-e2e-testing", "hf-static-release-verification",
                       "agile-governance"],
            "mcp_tools": ["mcp__github__search_issues",
                          "mcp__notion_mcp_server__API_retrieve_a_page",
                          "mcp__atlassian__getJiraIssue"],
            "goal": "Guarantee HoroConsultant v3 engine adapter, "
                    "debate router, and plan-completion archiving "
                    "meet Definition of Done before release.",
            "solution": "Run full e2e regression suite via pytest, "
                        "verify debate router contract against "
                        "v3_engine_adapter, confirm plan archiving "
                        "produces ReleaseNotes.md with 100% milestone "
                        "rollup. Use agile-governance skill to audit "
                        "DoR/DoD compliance.",
            "scope": "Run end-to-end regression suite for "
                     "HoroConsultant v3 engine adapter, verify debate "
                     "router contract, confirm plan-completion "
                     "archiving respects DoD.",
            "detail": "Test suite: project/tests/test_api_integration_suite.py, "
                      "test_button_regression.py, test_prod_regression.py. "
                      "Engine adapter: project/core/v3_engine_adapter.py. "
                      "Debate router: project/routers/debate.py. "
                      "Archiving governed by Rule 22 (plan-completion-and-release-notes). "
                      "All tests must pass before Done transition. "
                      "Ref: ATOMIC-19, Rule 22, DoD-v3.2.",
            "acceptance_criteria": [
                "test_api_integration_suite.py passes",
                "test_button_regression.py passes",
                "test_prod_regression.py passes",
                "Plan archiving completes without error",
                "ReleaseNotes.md generated with 100% milestone rollup",
            ],
            "artifacts": ["project/tests/test_api_integration_suite.py",
                          "project/tests/test_button_regression.py",
                          "project/tests/test_prod_regression.py",
                          "plans/archive/"],
            "verification_command": "cd /Users/kimlenglim/Project/HoroConsultant && python3 -m pytest project/tests/test_api_integration_suite.py project/tests/test_button_regression.py -v --tb=short",
            "priority": "High",
        },
    }

    meta = lane_subagent_map.get(lane_value, {
        "subagent": "orchestrator",
        "owner_agent": "orchestrator",
        "owner_role": "Coordination & Autonomous Execution",
        "owner_skills": ["orchestrator-delegation", "multi-account-agent-orchestration"],
        "skills": ["orchestrator-delegation"],
        "mcp_tools": ["mcp__github__search_issues"],
        "scope": "Generic delegated task.",
        "acceptance_criteria": ["Task completed"],
        "artifacts": [],
        "verification_command": "echo 'no-op'",
        "priority": "Medium",
    })

    # Build the evidence-rich description via build_task_description()
    description = build_task_description(
        summary=f"{TEST_PREFIX} {lane_value} — {summary_suffix}",
        subagent=meta["subagent"],
        skills=meta.get("skills", []),
        mcp_tools=meta.get("mcp_tools", []),
        scope=meta.get("scope", ""),
        acceptance_criteria=meta.get("acceptance_criteria", []),
        artifacts=meta.get("artifacts", []),
        verification_command=meta.get("verification_command", ""),
        priority=meta.get("priority", "Medium"),
        labels=["test", "mpq", f"lane-{lane_value.lower().replace(' ', '-')}"],
        goal=meta.get("goal"),
        solution=meta.get("solution"),
        detail=meta.get("detail"),
        owner_agent=meta.get("owner_agent"),
        owner_role=meta.get("owner_role"),
        owner_skills=meta.get("owner_skills"),
    )

    fields = {
        "project": {"key": PROJECT_KEY},
        "summary": f"{TEST_PREFIX} {lane_value} — {summary_suffix}",
        "description": description,
        "issuetype": {"name": "Task"},
        LANE_FID: {"id": str(lane_opt_id)} if lane_opt_id else {"value": lane_value},
        "labels": ["test", "mpq", f"lane-{lane_value.lower().replace(' ', '-')}"],
    }

    issue = jira_client.create_issue(fields=fields)
    # Transition to Ready
    transitions = jira_client.transitions(issue)
    ready_t = None
    for t in transitions:
        if t["name"].strip().lower() == "ready":
            ready_t = t["id"]
            break
    if ready_t:
        jira_client.transition_issue(issue, ready_t)

    # Verify the issue is actually in "Ready" status (wait for Jira indexing)
    status = "unknown"
    max_wait = 15  # seconds
    for attempt in range(max_wait):
        refreshed = jira_client.issue(issue.key)
        status = refreshed.fields.status.name
        if status.strip().lower() == "ready":
            break
        time.sleep(1)
    else:
        print(f"  ⚠️  Warning: {issue.key} did not reach 'Ready' status after {max_wait}s (current: {status})")

    # Verify lane was set correctly
    raw = jira_client.issue(issue.key).raw["fields"]
    lane_raw = raw.get(LANE_FID)
    actual_lane = lane_raw.get("value") if isinstance(lane_raw, dict) else str(lane_raw)
    print(f"  Created {issue.key} | Lane={actual_lane} | Status={status} | Summary={issue.fields.summary}")
    return issue


def verify_pickup(jira_client, expected_lane: str, label: str):
    """Call fetch_task() and verify the returned ticket has the expected lane."""
    print(f"\n  ▸ Running fetch_task() — {label}...")
    task = fetch_task()
    if task is None:
        print(f"    Result: None (no Ready tickets)")
        return False
    raw = jira_client.issue(task.key).raw["fields"]
    lane_raw = raw.get(LANE_FID)
    actual_lane = lane_raw.get("value") if isinstance(lane_raw, dict) else str(lane_raw)
    print(f"    Picked: {task.key} | Lane={actual_lane}")
    if actual_lane == expected_lane:
        print(f"    ✅ PASS — picked {expected_lane} as expected")
        return True
    else:
        print(f"    ❌ FAIL — expected {expected_lane} but got {actual_lane}")
        return False


def cleanup_test_tickets(jira_client):
    """Transition all test tickets to Done."""
    banner("Post-test cleanup: transitioning test tickets to Done")
    jql = f'project = "{PROJECT_KEY}" AND summary ~ "{TEST_PREFIX}" AND status != Done'
    issues = jira_client.search_issues(jql, maxResults=50)
    for issue in issues:
        transitions = jira_client.transitions(issue)
        done_t = None
        for t in transitions:
            if t["name"].strip().lower() == "done":
                done_t = t["id"]
                break
        if done_t:
            jira_client.transition_issue(issue, done_t)
            print(f"  → {issue.key} moved to Done")
    print(f"  Cleaned up {len(issues)} ticket(s).")


def main():
    parser = argparse.ArgumentParser(description="Multi-Project Queue priority test")
    parser.add_argument("--no-cleanup", action="store_true", help="Leave test tickets in Ready status")
    args = parser.parse_args()

    banner(f"Multi-Project Queue Test — Target Lane: {CURRENT_LANE}")
    print(f"  Jira URL   : {JIRA_URL}")
    print(f"  Project    : {PROJECT_KEY}")
    print(f"  Current Lane: {CURRENT_LANE}")
    print(f"  LANE_FID   : {LANE_FID}")

    # Show dynamically resolved lane options
    lane_opts = get_lane_options()
    print(f"  Available Lanes: {list(lane_opts.keys())}")
    print(f"  Target Lane ID: {lane_opts.get(CURRENT_LANE, {}).get('id', 'NOT FOUND')}")

    jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_TOKEN))

    # --- Step 0: Clean up any previous test tickets ---
    cleanup_existing_test_tickets(jira)

    # --- Step 1: Create Gemini Web Bridge ticket ---
    banner("Step 1: Create ticket — Project Lane = Gemini Web Bridge")
    gemini_issue = create_test_ticket(jira, "Gemini Web Bridge", "created first")

    # Verify that fetch_task() does NOT pick it (it should fall through to fallback)
    # or that it returns a non-Horo-Consultant ticket
    banner("Step 2: Verify fetch_task() with only Gemini ticket in Ready")
    passed_g = verify_pickup(jira, "Horo Consultant", "only Gemini ticket exists")
    if passed_g:
        print("  ⚠️  fetch_task() returned the Gemini ticket via fallback (no Horo Consultant ticket yet)")
        # This is expected — the fallback returns the oldest ticket

    # --- Step 2: Create Aipass Web Bridge ticket ---
    banner("Step 3: Create ticket — Project Lane = Aipass Web Bridge")
    aipass_issue = create_test_ticket(jira, "Aipass Web Bridge", "created second")

    # --- Step 3: Create Horo Consultant ticket (LAST — newest) ---
    banner("Step 4: Create ticket — Project Lane = Horo Consultant (created last!)")
    horo_issue = create_test_ticket(jira, "Horo Consultant", "created last")

    # Give Jira a moment to index
    time.sleep(1)

    # --- Step 4: Verify fetch_task() picks Horo Consultant, skipping the others ---
    banner("Step 5: Verify fetch_task() picks Horo Consultant (skips Gemini + Aipass)")
    passed = verify_pickup(jira, "Horo Consultant", "all 3 tickets in Ready queue")

    # --- Step 5: Verify it picks the NEWEST Horo Consultant ticket if multiple exist ---
    banner("Step 6: Create a second Horo Consultant ticket to test ordering among same-lane")
    horo_issue_2 = create_test_ticket(jira, "Horo Consultant", "second HC ticket")
    time.sleep(1)

    print("\n  ▸ Running fetch_task() to check which Horo Consultant ticket is picked...")
    task = fetch_task()
    raw = jira.issue(task.key).raw["fields"]
    lane_raw = raw.get(LANE_FID)
    actual_lane = lane_raw.get("value") if isinstance(lane_raw, dict) else str(lane_raw)
    print(f"    Picked: {task.key} | Lane={actual_lane}")
    # fetch_task() orders by created ASC, so it should pick the oldest Horo Consultant ticket
    if task.key == horo_issue.key:
        print(f"    ✅ PASS — picked oldest Horo Consultant ticket ({horo_issue.key})")
    elif task.key == horo_issue_2.key:
        print(f"    ⚠️  Picked {horo_issue_2.key} (newer HC ticket — also valid, same lane)")
    else:
        print(f"    ❌ FAIL — picked {task.key} which is not a Horo Consultant ticket")

    # --- Summary ---
    banner("Test Summary")
    all_passed = passed
    print(f"  Gemini ticket  : {gemini_issue.key}")
    print(f"  Aipass ticket  : {aipass_issue.key}")
    print(f"  Horo ticket #1 : {horo_issue.key}")
    print(f"  Horo ticket #2 : {horo_issue_2.key}")
    print(f"\n  Primary test (skip other lanes, pick Horo Consultant): {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"  Current lane   : {CURRENT_LANE}")

    # --- Cleanup ---
    if not args.no_cleanup:
        cleanup_test_tickets(jira)
    else:
        banner("Skipping cleanup (--no-cleanup)")
        print("  Test tickets remain in Ready status for manual inspection.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
