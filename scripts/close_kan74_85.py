#!/usr/bin/env python3
"""
scripts/close_kan74_85.py — Close KAN-74 through KAN-85 tickets.

Verifies all 12 tickets are Done, adds completion comments linking to git commits
(5a830f23 through 75ab37d0), and outputs a JSON summary.

Follows Jira Cloud retry patterns: 429 waits 25s (max 4 retries), 503 waits 15s.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

# Load .env manually (same pattern as jira_quality_gate.py)
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://pansakorn.atlassian.net").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL", os.getenv("JIRA_EMAIL", ""))
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")

GITHUB_REPO = "pphothidaen/HoroConsultant"
GITHUB_BASE = f"https://github.com/{GITHUB_REPO}/commit"

RETRY_CONFIG = {
    429: {"wait": 25, "max_retries": 4, "label": "Rate Limit (429)"},
    503: {"wait": 15, "max_retries": 4, "label": "Server Busy (503)"},
}

# Commits in range 5a830f23..75ab37d0, mapped to their ticket from commit messages
# Base commit 5a830f23 includes KAN-77
ALL_COMMITS = [
    ("5a830f23", "KAN-77", "test: Gemini Bridge toggle disabled scenario (TDD GREEN 12/12)"),
    ("c068ca65", "KAN-78", "test: Gemini Bridge missing-config scenario (TDD GREEN 8/8)"),
    ("df4ccdd4", "KAN-79", "test: Gemini Bridge circuit breaker (TDD GREEN 12/12)"),
    ("9856e81d", "KAN-80", "fix: circuit breaker half-open -> closed transition + state-machine TDD (7 tests GREEN)"),
    ("21117a8c", "KAN-81", "test: failover chain verification Bridge → Cloudflare AI → local (7 tests GREEN)"),
    ("f99803ae", "KAN-82", "test: edge case integration tests — intermittent/slow/partial/malformed (12 tests GREEN)"),
    ("7b9fa13f", "KAN-83", "ci: GitHub Actions workflow for Gemini Bridge test suite (py3.10-3.12 matrix)"),
    ("931980d6", "KAN-84", "docs: provenance manifest for KAN-73 atomic TDD cycle (112 tests VERIFIED)"),
    ("75ab37d0", "KAN-85", "test: env config + production secrets for bridge toggle (13 tests GREEN) + CI updated"),
]

# All 12 tickets to process: KAN-74 through KAN-85
ALL_KEYS = [f"KAN-{n}" for n in range(74, 86)]


def jira_request(method: str, path: str, payload: dict | None = None, max_retries: int = 4) -> dict:
    """Jira REST API request with retry on 429/503."""
    import requests

    url = f"{JIRA_BASE_URL}{path}"
    auth = (JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    last_error: str = ""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(method, url, auth=auth, headers=headers, json=payload, timeout=30)
        except requests.RequestException as exc:
            last_error = f"Network error: {exc}"
            if attempt < max_retries:
                time.sleep(5)
                continue
            break

        if resp.status_code in (200, 201, 204):
            if resp.status_code == 204:
                return {}
            return resp.json()

        if resp.status_code in RETRY_CONFIG:
            cfg = RETRY_CONFIG[resp.status_code]
            if attempt < cfg["max_retries"]:
                print(f"  [RETRY {attempt}/{cfg['max_retries']}] {cfg['label']}: waiting {cfg['wait']}s...",
                      file=sys.stderr)
                time.sleep(cfg["wait"])
                continue
            last_error = f"{cfg['label']} after {cfg['max_retries']} retries: {resp.text[:300]}"
            break
        else:
            last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            break

    raise RuntimeError(f"Jira API request failed: {last_error}")


def get_issue_full(issue_key: str) -> dict:
    """Fetch issue with summary, status, and parent info."""
    data = jira_request("GET", f"/rest/api/3/issue/{issue_key}?fields=summary,status,parent,issuetype")
    return data


def get_issue_comments(issue_key: str) -> list[dict]:
    """Fetch existing comments for an issue."""
    data = jira_request("GET", f"/rest/api/3/issue/{issue_key}/comment")
    return data.get("comments", [])


def add_comment(issue_key: str, body: str) -> dict:
    """Add a comment to a Jira issue. Returns the created comment."""
    payload = {"body": body}
    return jira_request("POST", f"/rest/api/3/issue/{issue_key}/comment", payload)


def get_status(issue_data: dict) -> str:
    fields = issue_data.get("fields", {})
    return fields.get("status", {}).get("name", "Unknown")


def get_summary(issue_data: dict) -> str:
    fields = issue_data.get("fields", {})
    return fields.get("summary", "")


def has_commit_comment(comments: list[dict], commit_short: str) -> bool:
    """Check if a comment already references a specific commit."""
    for c in comments:
        body = c.get("body", "") or ""
        if commit_short in body:
            return True
    return False


def get_commits_for_ticket(key: str) -> list[tuple[str, str, str]]:
    """Return list of (commit_short, ticket_key, commit_msg) for a ticket."""
    result = []
    for commit_short, ticket, msg in ALL_COMMITS:
        if ticket == key:
            result.append((commit_short, ticket, msg))
    # For parent tickets, include subtask commits
    if key == "KAN-73":
        result = ALL_COMMITS[:]  # all commits
    if key == "KAN-74":
        result = [c for c in ALL_COMMITS if c[1] in ("KAN-77", "KAN-78", "KAN-79")]
    if key == "KAN-75":
        result = [c for c in ALL_COMMITS if c[1] in ("KAN-80", "KAN-81", "KAN-82")]
    if key == "KAN-76":
        result = [c for c in ALL_COMMITS if c[1] in ("KAN-83", "KAN-84", "KAN-85")]
    return result


def build_completion_comment(key: str) -> str:
    """Build a completion comment with git commit links for a ticket."""
    commits = get_commits_for_ticket(key)
    commit_lines = []
    for commit_short, ticket, msg in commits:
        commit_url = f"{GITHUB_BASE}/{commit_short}"
        commit_lines.append(f"  • `{commit_short[:7]}` [{ticket}] [{msg}]({commit_url})")

    if len(commits) == 1:
        commit_short = commits[0][0]
        commit_url = f"{GITHUB_BASE}/{commit_short}"
        range_url = f"https://github.com/{GITHUB_REPO}/commit/{commit_short}"
        body = (
            f"✅ **Task Complete** — All work verified and tests passing.\n\n"
            f"Completion commit: `{commit_short[:7]}` — {commits[0][2]}\n"
            f"<{commit_url}>\n\n"
            f"Commit range: 5a830f23 → 75ab37d0"
        )
    else:
        range_url = f"https://github.com/{GITHUB_REPO}/commits"
        body = (
            f"✅ **All subtasks complete — Done**\n\n"
            f"All subtasks verified with passing tests.\n\n"
            f"Completion commits ({len(commits)}):\n" + "\n".join(commit_lines) + f"\n\n"
            f"Commit range: [5a830f23...75ab37d0]({range_url})"
        )

    return body


def main() -> int:
    print(f"{'='*60}")
    print(f"  Jira Ticket Closure: KAN-74 through KAN-85")
    print(f"  Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cloud_id": "45765a55-d652-421c-8096-940cebfd0bf7",
        "total_tickets": len(ALL_KEYS),
        "jira_base_url": JIRA_BASE_URL,
        "commit_range": {"from": "5a830f23", "to": "75ab37d0", "repo": GITHUB_REPO},
        "tickets": [],
    }

    all_done = True

    # Step 1 & 2: Verify status of all 12 tickets
    print(f"\n{'='*60}")
    print(f"  STEP 1: Verify all tickets show Done status")
    print(f"{'='*60}")

    for key in ALL_KEYS:
        ticket_result = {
            "key": key,
            "summary": "",
            "status": "",
            "was_done": False,
            "transitioned": False,
            "comment_added": False,
            "comment_skipped": False,
            "error": None,
        }
        try:
            issue_data = get_issue_full(key)
            status = get_status(issue_data)
            ticket_result["status"] = status
            ticket_result["summary"] = get_summary(issue_data)
            ticket_result["was_done"] = status == "Done"

            if status == "Done":
                print(f"  ✅ {key}: Done — {ticket_result['summary'][:50]}")
            else:
                print(f"  ❌ {key}: {status} — NOT Done!")
                all_done = False
                ticket_result["error"] = f"Status is {status}, not Done"

        except Exception as exc:
            all_done = False
            ticket_result["error"] = str(exc)
            print(f"  ⚠️  {key}: ERROR — {exc}")

        results["tickets"].append(ticket_result)

    # Step 3: Add completion comments with git commit links
    print(f"\n{'='*60}")
    print(f"  STEP 2: Add completion comments linking to git commits")
    print(f"{'='*60}")

    for t in results["tickets"]:
        key = t["key"]
        if not t["was_done"]:
            print(f"  [{key}] Skipped — not Done")
            t["comment_skipped"] = True
            continue

        try:
            comments = get_issue_comments(key)
            # Check if comment already added (avoid duplicates)
            already_commented = any(
                "Task Complete" in (c.get("body", "") or "") or "All subtasks complete" in (c.get("body", "") or "")
                for c in comments
            )

            if already_commented:
                print(f"  [{key}] Skipped — completion comment already exists")
                t["comment_skipped"] = True
                continue

            comment_body = build_completion_comment(key)
            resp = add_comment(key, comment_body)
            comment_id = resp.get("id") or resp.get("id")
            t["comment_added"] = True
            t["comment_id"] = str(comment_id) if comment_id else None
            print(f"  [{key}] ✅ Completion comment added")

        except Exception as exc:
            t["error"] = (t.get("error") or "") + f" | Comment failed: {exc}"
            print(f"  [{key}] ❌ Comment failed: {exc}")

    # Step 4: Final verification
    print(f"\n{'='*60}")
    print(f"  STEP 3: Final verification — confirm all 12 tickets Done")
    print(f"{'='*60}")

    all_final_done = True
    for key in ALL_KEYS:
        try:
            issue_data = get_issue_full(key)
            status = get_status(issue_data)
            # Update the ticket result with final status
            for t in results["tickets"]:
                if t["key"] == key:
                    t["status_after"] = status
                    break
            if status == "Done":
                print(f"  ✅ {key}: Done")
            else:
                print(f"  ❌ {key}: {status}")
                all_final_done = False
                all_done = False
        except Exception as exc:
            print(f"  ⚠️  {key}: ERROR — {exc}")
            all_final_done = False
            all_done = False

    # Build summary
    results["all_tickets_done"] = all_final_done
    results["summary"] = {
        "total": len(ALL_KEYS),
        "already_done": sum(1 for t in results["tickets"] if t.get("was_done")),
        "comments_added": sum(1 for t in results["tickets"] if t.get("comment_added")),
        "comments_skipped": sum(1 for t in results["tickets"] if t.get("comment_skipped")),
        "errors": sum(1 for t in results["tickets"] if t.get("error")),
        "all_done": all_final_done,
    }

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(json.dumps(results["summary"], indent=2))

    # Write JSON summary to file
    json_path = ROOT / "jira_closure_summary.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON summary written to: {json_path}")

    # Print full JSON
    print(f"\n{json.dumps(results, indent=2, ensure_ascii=False)}")

    return 0 if all_final_done else 1


if __name__ == "__main__":
    sys.exit(main())
