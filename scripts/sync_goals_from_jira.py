#!/usr/bin/env python3
"""
sync_goals_from_jira.py — Sync Jira sprint status to Atlas Goals

Reads KAN-39/40/41/42 status from Jira and updates corresponding
Atlas Goals (RHSKKVUC-3/4/5/6) so the goal dashboard stays current
without manual updates.

Usage:
    python3 scripts/sync_goals_from_jira.py [--dry-run]
"""

import json
import subprocess
import sys
from datetime import datetime

# Mapping: Jira Sprint -> Atlas Goal Key
SPRINT_GOAL_MAP = {
    "KAN-39": "RHSKKVUC-3",  # Sprint A: CRITICAL+HIGH
    "KAN-40": "RHSKKVUC-4",  # Sprint B: MEDIUM
    "KAN-41": "RHSKKVUC-5",  # Sprint C: LOW
    "KAN-42": "RHSKKVUC-6",  # Sprint D: Jira Migration
}

# Atlas status from Jira status
JIRA_TO_GOAL_STATUS = {
    "Done": ("on_track", 100, "Sprint completed"),
    "In Progress": ("at_risk", 50, "Sprint in progress"),
    "To Do": ("off_track", 0, "Sprint not started"),
    "TDD RED": ("at_risk", 25, "RED phase — tests written, failing"),
    "TDD GREEN": ("on_track", 75, "GREEN phase — fixes applied"),
    "Review": ("on_track", 90, "Review phase"),
}


def twg_goal_status(goal_key: str) -> dict:
    """Get current goal status from Atlas."""
    result = subprocess.run(
        ["twg", "goals", "get", goal_key, "-o", "json", "--output-summary", "none"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[WARN] Failed to get status for {goal_key}: {result.stderr[:200]}")
        return {}
    try:
        data = json.loads(result.stdout)
        return data.get("data", {})
    except json.JSONDecodeError:
        print(f"[WARN] Invalid JSON from twg for {goal_key}")
        return {}


def twg_jira_status(issue_key: str) -> dict:
    """Get Jira issue status."""
    result = subprocess.run(
        ["twg", "jira", "workitem", "query", "--jql", f"key = {issue_key}",
         "-o", "json", "--output-summary", "none"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[WARN] Failed to query {issue_key}: {result.stderr[:200]}")
        return {}
    try:
        data = json.loads(result.stdout)
        issues = data.get("data", {}).get("issues", [])
        return issues[0] if issues else {}
    except (json.JSONDecodeError, IndexError):
        print(f"[WARN] No data for {issue_key}")
        return {}


def post_goal_update(goal_key: str, status: str, summary: str) -> bool:
    """Post a status update on the goal."""
    result = subprocess.run(
        ["twg", "goals", "status-update", "create",
         "--goal", goal_key,
         "--status", status,
         "--summary", summary,
         "--yes"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[ERROR] Failed to update {goal_key}: {result.stderr[:200]}")
        return False
    return True


def build_summary(issue: dict, goal_status: tuple) -> str:
    """Build a summary string from Jira issue data."""
    jira_status = issue.get("status", {}).get("name", "Unknown")
    summary = issue.get("summary", "")
    _, score, note = goal_status
    return f"{summary} [{jira_status}] \u2014 {note} ({score}%)"


def main():
    dry_run = "--dry-run" in sys.argv
    updated = 0
    skipped = 0

    print(f"[{'DRY RUN' if dry_run else 'LIVE'}] Jira -> Atlas Goals Sync")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    for jira_key, goal_key in SPRINT_GOAL_MAP.items():
        # Get Jira status
        issue = twg_jira_status(jira_key)
        if not issue:
            print(f"[SKIP] {jira_key} -> {goal_key}: no Jira data")
            skipped += 1
            continue

        jira_status = issue.get("status", {}).get("name", "")
        goal_info = JIRA_TO_GOAL_STATUS.get(jira_status)
        if not goal_info:
            print(f"[SKIP] {jira_key}: unknown status '{jira_status}'")
            skipped += 1
            continue

        atlas_status, score, note = goal_info
        summary = build_summary(issue, goal_info)

        # Check current goal status to avoid redundant updates
        current = twg_goal_status(goal_key)
        current_state = current.get("status", {}).get("value", "")
        if current_state == atlas_status:
            print(f"[OK] {goal_key}: already '{atlas_status}', skipping")
            skipped += 1
            continue

        print(f"[UPDATE] {jira_key} ({jira_status}) -> {goal_key} ({atlas_status}, {score}%)")
        print(f"  Summary: {summary}")

        if not dry_run:
            if post_goal_update(goal_key, atlas_status, summary):
                updated += 1
                print(f"  [OK] Updated successfully")
            else:
                print(f"  [ERROR] Update failed")
        else:
            updated += 1

    print("-" * 60)
    print(f"Done: {updated} updated, {skipped} skipped")
    return 0 if not dry_run else 0


if __name__ == "__main__":
    sys.exit(main())
