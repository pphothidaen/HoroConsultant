#!/usr/bin/env python3
"""Jira API Transition & Governance Helper — KAN-95/KAN-105.

Provides reliable Jira Cloud REST API interactions:
- Transition issue between states dynamically based on target status name.
- Fetch available transitions for any issue.
- Verify credentials and connectivity.
- Support execution directly from scripts or CI/CD pipelines.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional
import requests

DEFAULT_DOMAIN = "pansakorn.atlassian.net"


def get_jira_credentials() -> tuple[str, str, str]:
    """Retrieve Jira Cloud domain, user email, and API token."""
    domain = os.environ.get("JIRA_DOMAIN", DEFAULT_DOMAIN).strip()
    email = os.environ.get("JIRA_USER_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()

    # Fallback to local .env if missing in environment
    if not (email and token) and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if (line.startswith("JIRA_USER_EMAIL=") or line.startswith("JIRA_EMAIL=")) and not email:
                    email = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("JIRA_API_TOKEN=") and not token:
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif (line.startswith("JIRA_DOMAIN=") or line.startswith("JIRA_BASE_URL=")) and not domain:
                    raw_domain = line.split("=", 1)[1].strip().strip('"').strip("'")
                    domain = raw_domain.replace("https://", "").replace("http://", "").strip("/")

    return domain, email, token


def get_available_transitions(issue_key: str) -> List[Dict[str, Any]]:
    """Retrieve all available transitions for an issue from Jira Cloud."""
    domain, email, token = get_jira_credentials()
    if not (email and token):
        raise ValueError("Missing JIRA_USER_EMAIL or JIRA_API_TOKEN in environment/.env")

    url = f"https://{domain}/rest/api/3/issue/{issue_key}/transitions"
    resp = requests.get(
        url,
        auth=(email, token),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code == 404:
        raise ValueError(f"Issue '{issue_key}' not found.")
    resp.raise_for_status()
    return resp.json().get("transitions", [])


def transition_issue(issue_key: str, target_status: str) -> bool:
    """Transition a Jira issue to the specified target status name."""
    domain, email, token = get_jira_credentials()
    if not (email and token):
        raise ValueError("Missing JIRA_USER_EMAIL or JIRA_API_TOKEN in environment/.env")

    transitions = get_available_transitions(issue_key)
    target_clean = target_status.strip().lower()

    transition_id = None
    available_names = []
    for t in transitions:
        name = t.get("name", "")
        to_name = t.get("to", {}).get("name", "")
        available_names.append(to_name or name)
        if to_name.lower() == target_clean or name.lower() == target_clean:
            transition_id = t.get("id")
            break

    if not transition_id:
        print(
            f"❌ Transition target '{target_status}' not found for {issue_key}.\n"
            f"   Available transitions: {', '.join(available_names)}",
            file=sys.stderr,
        )
        return False

    url = f"https://{domain}/rest/api/3/issue/{issue_key}/transitions"
    payload = {"transition": {"id": transition_id}}
    resp = requests.post(
        url,
        auth=(email, token),
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code in (200, 204):
        print(f"✅ Issue {issue_key} successfully transitioned to '{target_status}'.")
        return True

    print(f"❌ Failed to transition {issue_key}: HTTP {resp.status_code} - {resp.text}", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Jira Issue Transition Helper.")
    parser.add_argument("--issue", required=True, help="Jira Issue Key (e.g. KAN-105)")
    parser.add_argument("--status", help="Target status name to transition to (e.g. 'Review', 'Done', 'TDD RED')")
    parser.add_argument("--list", action="store_true", help="List available transitions for the issue")

    args = parser.parse_args()

    try:
        if args.list:
            transitions = get_available_transitions(args.issue)
            print(f"Available transitions for {args.issue}:" )
            for t in transitions:
                to_name = t.get("to", {}).get("name", t.get("name"))
                print(f" - [{t.get('id')}] {to_name}")
            return 0

        if not args.status:
            print("ERROR: --status is required when not using --list.", file=sys.stderr)
            return 1

        success = transition_issue(args.issue, args.status)
        return 0 if success else 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
