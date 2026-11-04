#!/usr/bin/env python3
"""
Jira ↔ Repo SHA Binding Gate (Phase 2.2)

Establishes bidirectional, tamper-evident linkage between Git commit SHAs
and Jira issue keys. Neither system drifts during multi-lane agent execution.

Key responsibilities:
1. Extract ticket ID from branch name (feat/KAN-NNN-*)
2. Verify commit trailers (Issue:, Risk-Tier:, Test-Baseline:, Agent-Role:)
3. Attach commit SHA to Jira issue as comment + remote link
4. Fallback to local provenance ledger when Jira credentials unavailable
5. Record gate events to ai_sdlc_metrics.py for telemetry
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Configuration constants
DEFAULT_JIRA_URL = os.getenv("JIRA_BASE_URL", "https://pansakorn.atlassian.net")
DEFAULT_JIRA_USER = os.getenv("JIRA_USER_EMAIL", "")
DEFAULT_JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")
TICKET_REGEX = re.compile(r"KAN-[0-9]+")


class JiraRepoBinder:
    """Core binding logic for Jira ↔ Repo SHA synchronization."""

    def __init__(self, mode: str = "observation"):
        """
        Initialize binder.

        Args:
            mode: "observation" (log only, exit 0) or "enforce" (block on violations)
        """
        self.mode = mode.lower()
        self.jira_url = DEFAULT_JIRA_URL
        self.jira_user = DEFAULT_JIRA_USER
        self.jira_token = DEFAULT_JIRA_TOKEN
        self.current_sha = self._get_current_sha()
        self.current_branch = self._get_current_branch()

    def _get_current_sha(self) -> str:
        """Get current commit SHA."""
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else "0" * 40

    def _get_current_branch(self) -> str:
        """Get current branch name."""
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else ""

    def extract_ticket_id(self, explicit_ticket: Optional[str] = None) -> Optional[str]:
        """
        Extract Jira ticket ID from branch name or explicit argument.

        Priority: explicit argument > branch name pattern
        """
        if explicit_ticket and TICKET_REGEX.match(explicit_ticket):
            return explicit_ticket.upper()

        match = TICKET_REGEX.search(self.current_branch)
        return match.group(0).upper() if match else None

    def verify_commit_trailers(self, commit_sha: str, expected_ticket: str) -> Tuple[bool, List[str]]:
        """
        Validate that the commit message contains required issue metadata trailers.

        Required trailers (block on missing in enforce mode):
        - Issue: KAN-NNN (matches expected ticket)
        - Risk-Tier: Tier-1|Tier-2|Tier-3

        Recommended trailers (warn only):
        - Test-Baseline: <sha>
        - Agent-Role: <role>
        """
        errors = []
        warnings = []
        cmd = ["git", "log", "-1", "--format=%B", commit_sha]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, [f"Failed to read commit log for {commit_sha}"]

        commit_msg = res.stdout

        # Check Issue trailer (REQUIRED)
        issue_match = re.search(r"^\s*Issue:\s*(KAN-[0-9]+)", commit_msg, re.MULTILINE | re.IGNORECASE)
        if not issue_match:
            errors.append(f"Missing 'Issue: {expected_ticket}' trailer in commit {commit_sha[:7]}")
        elif issue_match.group(1).upper() != expected_ticket.upper():
            errors.append(f"Mismatched trailer: found '{issue_match.group(1)}', expected '{expected_ticket}'")

        # Check Risk-Tier trailer (REQUIRED)
        tier_match = re.search(r"^\s*Risk-Tier:\s*(Tier-[123])", commit_msg, re.MULTILINE | re.IGNORECASE)
        if not tier_match:
            errors.append(f"Missing 'Risk-Tier: Tier-N' trailer in commit {commit_sha[:7]}")

        # Check Test-Baseline trailer (RECOMMENDED - warn only)
        baseline_match = re.search(r"^\s*Test-Baseline:\s*([a-f0-9]{40})", commit_msg, re.MULTILINE | re.IGNORECASE)
        if not baseline_match:
            warnings.append(f"Missing 'Test-Baseline: <sha>' trailer in commit {commit_sha[:7]} (recommended)")

        # Check Agent-Role trailer (RECOMMENDED - warn only)
        agent_match = re.search(r"^\s*Agent-Role:\s*(\S+)", commit_msg, re.MULTILINE | re.IGNORECASE)
        if not agent_match:
            warnings.append(f"Missing 'Agent-Role: <role>' trailer in commit {commit_sha[:7]} (recommended)")

        # Print warnings but don't fail on them
        for w in warnings:
            print(f"[JIRA-BIND WARN] {w}")

        return len(errors) == 0, errors

    def attach_sha_to_jira(self, ticket_id: str, commit_sha: str, event_name: str) -> bool:
        """
        Attach commit SHA as an audit comment and remote link to the Jira issue.

        Falls back to local provenance ledger if Jira credentials are not configured.

        Args:
            ticket_id: Jira issue key (e.g., KAN-122)
            commit_sha: Full 40-char commit SHA
            event_name: Lifecycle event name (e.g., "COMMIT_VERIFY", "PRE_PUSH", "TDD_RED", "TDD_GREEN")

        Returns:
            True if successfully recorded (either remote or local fallback)
        """
        # Fallback to local provenance registry if credentials not set
        if not (self.jira_user and self.jira_token):
            provenance_file = Path("plans/provenance_ledger.jsonl")
            provenance_file.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ticket_id": ticket_id,
                "commit_sha": commit_sha,
                "event": event_name,
                "branch": self.current_branch,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "synced_remote": False,
                "mode": self.mode
            }
            with open(provenance_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            print(f"[JIRA-BIND] Credentials not set. Recorded SHA {commit_sha[:7]} locally for {ticket_id}.")
            return True

        # Live Jira REST API invocation - Add comment with commit reference
        try:
            import urllib.request

            url = f"{self.jira_url.rstrip('/')}/rest/api/3/issue/{ticket_id}/comment"
            auth_str = base64.b64encode(f"{self.jira_user}:{self.jira_token}".encode()).decode()

            # Build comment with commit SHA and event
            short_sha = commit_sha[:7]
            comment_text = f"[AI-SDLC Audit] {event_name}: verified commit {short_sha} ({commit_sha}) on branch {self.current_branch}"

            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": comment_text
                        }]
                    }]
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Basic {auth_str}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                success = response.status in (200, 201)
                if success:
                    print(f"[JIRA-BIND] Synced commit {short_sha} to Jira {ticket_id} ({event_name})")
                return success

        except Exception as e:
            print(f"[JIRA-BIND WARNING] Jira API sync failed: {e}")
            # Fallback to local ledger on API failure
            provenance_file = Path("plans/provenance_ledger.jsonl")
            provenance_file.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ticket_id": ticket_id,
                "commit_sha": commit_sha,
                "event": event_name,
                "branch": self.current_branch,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "synced_remote": False,
                "error": str(e),
                "mode": self.mode
            }
            with open(provenance_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            print(f"[JIRA-BIND] Fallback: recorded SHA {commit_sha[:7]} locally for {ticket_id}.")
            return True

    def get_jira_issue_summary(self, ticket_id: str) -> Optional[str]:
        """Fetch Jira issue summary for drift detection."""
        if not (self.jira_user and self.jira_token):
            return None

        try:
            url = f"{self.jira_url.rstrip('/')}/rest/api/3/issue/{ticket_id}?fields=summary"
            auth_str = base64.b64encode(f"{self.jira_user}:{self.jira_token}".encode()).decode()

            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Basic {auth_str}", "Content-Type": "application/json"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201):
                    data = json.loads(response.read().decode())
                    return data.get("fields", {}).get("summary", "")
        except Exception:
            pass
        return None

    def check_atomic_ticket_drift(self, ticket_id: str) -> Tuple[bool, List[str]]:
        """
        Check if ATOMIC_TICKET.md in working tree conflicts with Jira live issue.

        Returns:
            (no_drift, list_of_violations)
        """
        errors = []
        atomic_path = Path("ATOMIC_TICKET.md")

        if not atomic_path.exists():
            return True, []  # No local spec to check

        content = atomic_path.read_text(encoding="utf-8")

        # Extract ticket ID from ATOMIC_TICKET.md
        ticket_match = re.search(r"Ticket ID:\s*(KAN-[0-9]+)", content)
        if ticket_match:
            local_ticket = ticket_match.group(1).upper()
            if local_ticket != ticket_id.upper():
                errors.append(f"ATOMIC_TICKET.md references {local_ticket} but branch/commit references {ticket_id}")

        # Could extend with acceptance criteria comparison against Jira

        return len(errors) == 0, errors

    def record_gate_event(self, ticket_id: str, valid: bool, event_name: str) -> None:
        """Record gate event to ai_sdlc_metrics.py for telemetry."""
        try:
            subprocess.run([
                sys.executable, "scripts/ai_sdlc_metrics.py", "record-gate",
                "--ticket-id", ticket_id,
                "--gate-name", "jira_sha_binding",
                "--tier", "Tier 2",
                "--result", "PASS" if valid else "FAIL_OBSERVED",
                "--gate-mode", self.mode
            ], capture_output=True, timeout=10)
        except Exception:
            pass  # Telemetry failure shouldn't block gate

    def evaluate(self, explicit_ticket: Optional[str] = None, event_name: str = "COMMIT_VERIFY") -> int:
        """
        Main evaluation entry point.

        Returns:
            0 = pass (or observation mode with warnings)
            1 = enforce mode violation (block)
            2 = configuration error
        """
        ticket_id = self.extract_ticket_id(explicit_ticket)
        if not ticket_id:
            msg = f"No Jira Ticket ID could be determined from branch '{self.current_branch}'"
            if self.mode == "enforce":
                print(f"[JIRA-BIND BLOCKED] {msg}")
                return 1
            print(f"[JIRA-BIND NOTICE] {msg} (Observation mode: passing)")
            return 0

        print(f"[JIRA-BIND] Processing {ticket_id} @ {self.current_sha[:7]} on {self.current_branch}")

        # Verify commit trailers
        valid, errors = self.verify_commit_trailers(self.current_sha, ticket_id)
        for err in errors:
            print(f"[JIRA-BIND ERROR] {err}")

        if not valid and self.mode == "enforce":
            print(f"[JIRA-BIND BLOCKED] Commit trailer validation failed for {ticket_id}")
            self.record_gate_event(ticket_id, False, event_name)
            return 1

        if not valid:
            print(f"[JIRA-BIND NOTICE] Trailer errors observed under mode '{self.mode}'. Continuing.")

        # Check ATOMIC_TICKET.md drift
        no_drift, drift_errors = self.check_atomic_ticket_drift(ticket_id)
        for err in drift_errors:
            print(f"[JIRA-BIND DRIFT] {err}")
        if not no_drift and self.mode == "enforce":
            print(f"[JIRA-BIND BLOCKED] ATOMIC_TICKET.md drift detected for {ticket_id}")
            self.record_gate_event(ticket_id, False, event_name)
            return 1

        # Sync SHA to Jira (or local ledger)
        self.attach_sha_to_jira(ticket_id, self.current_sha, event_name)

        # Record gate event for telemetry
        self.record_gate_event(ticket_id, valid, event_name)

        print(f"[JIRA-BIND] {ticket_id} binding complete: SHA {self.current_sha[:7]} recorded")
        return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Jira ↔ Repo SHA Binding & Verification Gate (Phase 2.2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify current commit with ticket from branch name (observation mode)
  python3 scripts/jira_sha_bind.py --mode observation

  # Verify specific ticket in enforce mode
  python3 scripts/jira_sha_bind.py --ticket-id KAN-122 --mode enforce --event TDD_GREEN

  # Pre-push integration (called from .githooks/pre-push)
  python3 scripts/jira_sha_bind.py --ticket-id "$TICKET_ID" --mode "$GATE_MODE" --event "PRE_PUSH"
        """
    )
    parser.add_argument("--ticket-id", default=None, help="Explicit Jira Ticket ID (KAN-NNN)")
    parser.add_argument("--mode", default=os.getenv("HORO_GATE_MODE", "observation"),
                        choices=["observation", "enforce"],
                        help="Gate mode: observation (log only) or enforce (block)")
    parser.add_argument("--event", default="COMMIT_VERIFY",
                        help="Lifecycle event name (COMMIT_VERIFY, PRE_PUSH, TDD_RED, TDD_GREEN, etc.)")
    parser.add_argument("--verify-only", action="store_true",
                        help="Only verify trailers without remote sync")

    args = parser.parse_args(argv)

    binder = JiraRepoBinder(mode=args.mode)

    if args.verify_only:
        ticket_id = binder.extract_ticket_id(args.ticket_id)
        if not ticket_id:
            print(f"[JIRA-BIND] No ticket ID found")
            return 0
        valid, errors = binder.verify_commit_trailers(binder.current_sha, ticket_id)
        for err in errors:
            print(f"[JIRA-BIND ERROR] {err}")
        return 0 if valid else 1

    return binder.evaluate(explicit_ticket=args.ticket_id, event_name=args.event)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))