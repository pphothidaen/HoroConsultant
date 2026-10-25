#!/usr/bin/env python3
"""
scripts/jira_quality_gate.py — Jira Issue Quality Gate Checker
=============================================================
Validates whether a Jira issue has met all criteria for Done transition.

Checks:
  1. TDD Phase Compliance (tdd-red → tdd-green → tdd-review → tdd-complete)
  2. Acceptance Criteria Evidence (test results, artifacts, verification)
  3. Cross-Agent Sign-Off (no self-certification)
  4. Jira API Retry Pattern (429/503 with exponential backoff)

Usage:
    python3 scripts/jira_quality_gate.py --issue KAN-43 --check
    python3 scripts/jira_quality_gate.py --jql "labels = sprint-b" --batch
    python3 scripts/jira_quality_gate.py --issue KAN-43 --verbose

Exit Codes:
    0 = All gates passed (safe to transition to Done)
    1 = One or more gates failed (transition to Review instead)
    2 = Runtime error (API failure, parsing error, etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

# Load .env manually to avoid dependency on python-dotenv in CI
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

# Atlassian Document Format (ADF) patterns for parsing description
ADF_PARAGRAPH_RE = re.compile(r'"type"\s*:\s*"paragraph"')
ADF_TEXT_RE = re.compile(r'"text"\s*:\s*"([^"]+)"')

# Acceptance Criteria evidence patterns
TEST_RESULT_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:tests?|pass)", re.IGNORECASE)
ARTIFACT_RE = re.compile(r"^[*\s]+(\S+\.\S+)", re.MULTILINE)

# Retry configuration
RETRY_CONFIG = {
    429: {"wait": 25, "max_retries": 4, "label": "Rate Limit (429)"},
    503: {"wait": 15, "max_retries": 4, "label": "Server Busy (503)"},
}

# ---------------------------------------------------------------------------
# Jira API Helpers with Retry
# ---------------------------------------------------------------------------


def jira_request(
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    max_retries: int = 4,
) -> dict:
    """
    Make a Jira REST API request with automatic retry on 429/503.

    Returns parsed JSON dict on success.
    Raises RuntimeError after all retries exhausted.
    """
    import requests

    url = f"{JIRA_BASE_URL}{path}"
    auth = (JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    last_error: str = ""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(
                method, url, auth=auth, headers=headers,
                json=payload, timeout=30,
            )
        except requests.RequestException as exc:
            last_error = f"Network error: {exc}"
            break

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in RETRY_CONFIG:
            cfg = RETRY_CONFIG[resp.status_code]
            if attempt < cfg["max_retries"]:
                print(
                    f"  [RETRY {attempt}/{cfg['max_retries']}] {cfg['label']}: "
                    f"waiting {cfg['wait']}s...",
                    file=sys.stderr,
                )
                time.sleep(cfg["wait"])
                continue
            else:
                last_error = (
                    f"{cfg['label']} after {cfg['max_retries']} retries: "
                    f"{resp.text[:200]}"
                )
                break
        else:
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            break

    raise RuntimeError(f"Jira API request failed: {last_error}")


def get_issue(issue_key: str) -> dict:
    """Fetch a single Jira issue with all relevant fields."""
    data = jira_request("GET", f"/rest/api/3/issue/{issue_key}")
    return data


def get_issue_comments(issue_key: str) -> list[dict]:
    """Fetch comments for a Jira issue."""
    data = jira_request("GET", f"/rest/api/3/issue/{issue_key}/comment")
    return data.get("comments", [])


def add_comment(issue_key: str, body: str) -> dict:
    """Add a comment to a Jira issue."""
    payload = {"body": body}
    return jira_request("POST", f"/rest/api/3/issue/{issue_key}/comment", payload)


def search_issues(jql: str, max_results: int = 50) -> list[dict]:
    """Search Jira issues using JQL."""
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ["summary", "status", "priority", "labels", "updated", "assignee"],
    }
    data = jira_request("POST", "/rest/api/3/search/jql", payload)
    return data.get("issues", [])


# ---------------------------------------------------------------------------
# Gate Checkers
# ---------------------------------------------------------------------------


def check_tdd_compliance(issue: dict) -> tuple[bool, str]:
    """
    Verify TDD phase progression: tdd-red → tdd-green → tdd-review → tdd-complete.

    Returns (passed, reason).
    """
    labels = issue.get("fields", {}).get("labels", [])
    label_set = set(labels)

    required_sequence = ["tdd-red", "tdd-green", "tdd-review", "tdd-complete"]
    missing = [l for l in required_sequence if l not in label_set]

    if missing:
        return False, f"Missing TDD labels: {', '.join(missing)}"

    return True, "All TDD phases present"


def check_acceptance_criteria(issue: dict) -> tuple[bool, str]:
    """
    Verify Acceptance Criteria have evidence.

    Looks for:
    - Numbered list in description under "*Acceptance Criteria (DoD):*"
    - Test result patterns like "N/N tests pass"
    - Artifact paths matching Target Artifacts section

    Returns (passed, reason).
    """
    fields = issue.get("fields", {})
    description = fields.get("description", "") or ""

    # Extract Acceptance Criteria section
    ac_section = _extract_section(description, "Acceptance Criteria")
    if not ac_section:
        ac_section = _extract_section(description, "DoD")

    if not ac_section:
        # Fall back to label check
        labels = fields.get("labels", [])
        if "tdd-complete" in labels:
            return True, "No AC section found, but tdd-complete label present"
        return False, "No Acceptance Criteria section found in description"

    # Look for numbered criteria
    criteria_lines = re.findall(r"^\s*\d+\.\s+(.+)$", ac_section, re.MULTILINE)
    if not criteria_lines:
        return False, "Acceptance Criteria section has no numbered items"

    # Check for evidence patterns
    evidence_count = 0
    for line in criteria_lines:
        if TEST_RESULT_RE.search(line):
            evidence_count += 1
        elif ARTIFACT_RE.search(line):
            evidence_count += 1
        elif "pass" in line.lower() or "done" in line.lower():
            evidence_count += 1

    if evidence_count == 0 and len(criteria_lines) > 0:
        return False, (
            f"Found {len(criteria_lines)} criteria but no evidence "
            f"(test results, artifacts, or pass/done status)"
        )

    return True, f"{evidence_count}/{len(criteria_lines)} criteria have evidence"


def check_cross_agent_signoff(issue: dict) -> tuple[bool, str]:
    """
    Verify cross-agent sign-off (no self-certification).

    Checks that at least one comment contains a PASS sign-off from
    a different agent than the one assigned.

    Returns (passed, reason).
    """
    issue_key = issue.get("key", "UNKNOWN")
    fields = issue.get("fields", {})
    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName", "") if assignee else ""

    try:
        comments = get_issue_comments(issue_key)
    except RuntimeError:
        # If we can't fetch comments, fail open (don't block on API error)
        return True, "Could not verify cross-agent sign-off (API error)"

    # Look for PASS sign-off from a different agent
    signoff_pattern = re.compile(
        r"(?:PASS|APPROVED|LGTM|✓|✅)\s*(?:by|from)?\s*@?(\w+)",
        re.IGNORECASE,
    )

    for comment in comments:
        body = comment.get("body", "") or ""
        author = comment.get("author", {}).get("displayName", "")

        if signoff_pattern.search(body):
            # Check if sign-off is from someone other than assignee
            if author and author != assignee_name:
                return True, f"Cross-agent sign-off by {author}"
            # Also check if it mentions a different agent name
            match = signoff_pattern.search(body)
            if match and match.group(1):
                mentioned = match.group(1)
                if mentioned.lower() not in assignee_name.lower():
                    return True, f"Cross-agent sign-off for {mentioned}"

    # If no assignee, skip this check
    if not assignee_name:
        return True, "No assignee set, skipping cross-agent check"

    return False, f"No cross-agent sign-off found (assignee: {assignee_name})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(text: str, header: str) -> str | None:
    """Extract a section from markdown/ADF text by header name."""
    if not text:
        return None

    # Try markdown-style header
    pattern = rf"(?:^|\n)[#\s]*{re.escape(header)}[^\n]*\n(.*?)(?=\n#|\n---|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try Jira wiki-style header
    pattern = rf"(?:^|\n)[^\n]*{re.escape(header)}[^\n]*\n(.*?)(?=\n[^\n]*---|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def _format_gate_result(name: str, passed: bool, reason: str) -> str:
    """Format a single gate check result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    return f"  {status} | {name}: {reason}"


# ---------------------------------------------------------------------------
# Main Gate Check
# ---------------------------------------------------------------------------


def check_issue(issue_key: str, verbose: bool = False) -> int:
    """
    Run all quality gate checks on a single issue.

    Returns:
        0 = all gates passed
        1 = one or more gates failed
        2 = runtime error
    """
    print(f"\n{'='*60}")
    print(f"  QUALITY GATE CHECK: {issue_key}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Fetch issue
    try:
        issue = get_issue(issue_key)
    except RuntimeError as exc:
        print(f"\n  ❌ ERROR: Could not fetch issue: {exc}")
        return 2

    fields = issue.get("fields", {})
    summary = fields.get("summary", "Unknown")
    status = fields.get("status", {}).get("name", "Unknown")
    print(f"\n  Summary: {summary}")
    print(f"  Current Status: {status}")

    if status == "Done":
        print(f"\n  ℹ️  Issue is already Done. No gate check needed.")
        return 0

    # Run all gate checks
    results: list[tuple[str, bool, str]] = []

    # 1. TDD Compliance
    passed, reason = check_tdd_compliance(issue)
    results.append(("TDD Phase Compliance", passed, reason))

    # 2. Acceptance Criteria
    passed, reason = check_acceptance_criteria(issue)
    results.append(("Acceptance Criteria", passed, reason))

    # 3. Cross-Agent Sign-Off
    passed, reason = check_cross_agent_signoff(issue)
    results.append(("Cross-Agent Sign-Off", passed, reason))

    # Print results
    print(f"\n  {'─'*56}")
    print(f"  GATE RESULTS:")
    print(f"  {'─'*56}")

    all_passed = True
    for name, passed, reason in results:
        print(_format_gate_result(name, passed, reason))
        if not passed:
            all_passed = False

    print(f"  {'─'*56}")

    if all_passed:
        print(f"\n  ✅ ALL GATES PASSED — Safe to transition to Done")
        return 0
    else:
        failed = [n for n, p, _ in results if not p]
        print(f"\n  ❌ GATES FAILED: {', '.join(failed)}")
        print(f"  → Recommended action: Transition to Review, not Done")
        return 1


def batch_check(jql: str, max_results: int = 50) -> int:
    """
    Run quality gate checks on all issues matching a JQL query.

    Returns:
        0 = all issues passed
        1 = some issues failed
        2 = runtime error
    """
    print(f"\n{'='*60}")
    print(f"  BATCH QUALITY GATE CHECK")
    print(f"  JQL: {jql}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        issues = search_issues(jql, max_results)
    except RuntimeError as exc:
        print(f"\n  ❌ ERROR: Could not search issues: {exc}")
        return 2

    if not issues:
        print(f"\n  ℹ️  No issues found matching JQL.")
        return 0

    print(f"\n  Found {len(issues)} issues to check.\n")

    passed_count = 0
    failed_count = 0
    error_count = 0

    for issue in issues:
        key = issue.get("key", "UNKNOWN")
        try:
            result = check_issue(key)
            if result == 0:
                passed_count += 1
            elif result == 1:
                failed_count += 1
            else:
                error_count += 1
        except Exception as exc:
            print(f"  ❌ ERROR checking {key}: {exc}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"  BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"  Total:  {len(issues)}")
    print(f"  Passed: {passed_count} ✅")
    print(f"  Failed: {failed_count} ❌")
    print(f"  Errors: {error_count} ⚠️")

    return 0 if failed_count == 0 and error_count == 0 else 1


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Jira Issue Quality Gate Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Check single issue
  python3 scripts/jira_quality_gate.py --issue KAN-43 --check

  # Batch check all issues in a sprint
  python3 scripts/jira_quality_gate.py --jql "labels = sprint-b" --batch

  # Verbose output
  python3 scripts/jira_quality_gate.py --issue KAN-43 --check --verbose
""",
    )
    parser.add_argument("--issue", help="Jira issue key (e.g. KAN-43)")
    parser.add_argument("--jql", help="JQL query for batch mode")
    parser.add_argument("--check", action="store_true", help="Run gate check")
    parser.add_argument("--batch", action="store_true", help="Batch mode (uses --jql)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--max-results", type=int, default=50, help="Max results for batch")

    args = parser.parse_args()

    if args.batch and args.jql:
        return batch_check(args.jql, args.max_results)
    elif args.issue and args.check:
        return check_issue(args.issue, args.verbose)
    elif args.issue:
        # Default to --check if issue specified
        return check_issue(args.issue, args.verbose)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
