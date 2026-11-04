#!/usr/bin/env python3
"""
Cost Governance & Retry Controller (Phase 2.3)

Prevents runaway token costs and infinite agent repair loops while providing
a deterministic escalation path to human engineers when automated loops fail
to converge.

Features:
- Per-agent retry limits and token caps
- Persistent SQLite tracking (token_ledger, agent_retry_tracker)
- JSONL fallback for escalation records
- CLI: check, record, escalate
- Integration with jira_sha_bind.py for escalation telemetry
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple


DB_PATH = Path("plans/ai_sdlc_metrics.db")

AGENT_LIMITS = {
    "qa_tester": {"max_retries": 3, "token_cap": 50_000},
    "developer": {"max_retries": 3, "token_cap": 100_000},
    "code_reviewer": {"max_retries": 2, "token_cap": 30_000},
}


class CostGovernor:
    """Manages retry checkpoints, enforces consumption caps, and coordinates escalation."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Initialize cost governance tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS token_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ticket_id TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0.0,
                session_id TEXT
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_retry_tracker (
                ticket_id TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER NOT NULL,
                total_tokens_consumed INTEGER DEFAULT 0,
                token_cap INTEGER NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ticket_id, agent_role)
            );
            """)
            conn.commit()

    def check_budget(self, ticket_id: str, agent_role: str) -> Tuple[bool, str]:
        """
        Validates whether an agent has remaining retries and token budget.

        Returns:
            (allowed, message): allowed=False means budget exceeded or escalated
        """
        limits = AGENT_LIMITS.get(agent_role, {"max_retries": 3, "token_cap": 50_000})

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT retry_count, total_tokens_consumed, status FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, agent_role)
            ).fetchone()

            if not row:
                return True, "Budget OK (First invocation)"

            if row["status"] == "ESCALATED":
                return False, f"Ticket {ticket_id} is already in ESCALATED state for role {agent_role}."

            if row["retry_count"] >= limits["max_retries"]:
                return False, f"Exceeded max retries ({row['retry_count']}/{limits['max_retries']}) for role {agent_role}."

            if row["total_tokens_consumed"] >= limits["token_cap"]:
                return False, f"Exceeded token cap ({row['total_tokens_consumed']}/{limits['token_cap']}) for role {agent_role}."

        return True, "Budget OK"

    def increment_attempt(self, ticket_id: str, agent_role: str, tokens_used: int = 0) -> int:
        """
        Records an attempt and accumulates token usage.

        Returns:
            Current retry count after increment
        """
        limits = AGENT_LIMITS.get(agent_role, {"max_retries": 3, "token_cap": 50_000})

        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO agent_retry_tracker (ticket_id, agent_role, retry_count, max_retries, total_tokens_consumed, token_cap, status)
            VALUES (?, ?, 1, ?, ?, ?, 'ACTIVE')
            ON CONFLICT(ticket_id, agent_role) DO UPDATE SET
                retry_count = retry_count + 1,
                total_tokens_consumed = total_tokens_consumed + excluded.total_tokens_consumed,
                last_updated = CURRENT_TIMESTAMP;
            """, (ticket_id, agent_role, limits["max_retries"], tokens_used, limits["token_cap"]))
            conn.commit()

            row = conn.execute(
                "SELECT retry_count FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, agent_role)
            ).fetchone()
            return row["retry_count"]

    def record_token_usage(
        self,
        ticket_id: str,
        agent_role: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost_usd: float = 0.0,
        session_id: Optional[str] = None
    ) -> None:
        """Records detailed token usage to token_ledger."""
        total = prompt_tokens + completion_tokens
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO token_ledger (ticket_id, agent_role, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticket_id, agent_role, model, prompt_tokens, completion_tokens, total, estimated_cost_usd, session_id))
            conn.commit()

    def trigger_escalation(self, ticket_id: str, agent_role: str, reason: str) -> None:
        """
        Flags the ticket as ESCALATED in local DB, records telemetry, and notifies Jira.
        """
        limits = AGENT_LIMITS.get(agent_role, {"max_retries": 3, "token_cap": 50_000})
        
        with self._get_connection() as conn:
            # Ensure row exists (upsert) then mark ESCALATED
            conn.execute("""
            INSERT INTO agent_retry_tracker (ticket_id, agent_role, retry_count, max_retries, total_tokens_consumed, token_cap, status)
            VALUES (?, ?, 0, ?, 0, ?, 'ESCALATED')
            ON CONFLICT(ticket_id, agent_role) DO UPDATE SET
                status = 'ESCALATED',
                last_updated = CURRENT_TIMESTAMP;
            """, (ticket_id, agent_role, limits["max_retries"], limits["token_cap"]))
            conn.commit()

        # Log escalation event to JSONL fallback (relative to db_path)
        esc_file = self.db_path.parent / "escalations.jsonl"
        esc_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ticket_id": ticket_id,
            "agent_role": agent_role,
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "max_retries": limits["max_retries"],
            "token_cap": limits["token_cap"],
            "status": "ESCALATED",
        }
        with open(esc_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        print(f"\n[COST-GOVERNANCE ESCALATION] {ticket_id} ({agent_role}): {reason}")
        print("[ACTION REQUIRED] Autonomous loop halted. Escalating to human engineer.")

        # Sync label to Jira via existing jira_sha_bind.py
        try:
            subprocess.run([
                sys.executable, "scripts/jira_sha_bind.py",
                "--ticket-id", ticket_id,
                "--event", f"ESCALATION_{agent_role.upper()}"
            ], capture_output=True, timeout=10)
        except Exception:
            pass  # Best effort

    def get_status(self, ticket_id: str, agent_role: str) -> Dict:
        """Returns current budget status for a ticket/role."""
        limits = AGENT_LIMITS.get(agent_role, {"max_retries": 3, "token_cap": 50_000})
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT retry_count, total_tokens_consumed, status FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, agent_role)
            ).fetchone()

            if not row:
                return {
                    "ticket_id": ticket_id,
                    "agent_role": agent_role,
                    "retry_count": 0,
                    "max_retries": limits["max_retries"],
                    "total_tokens": 0,
                    "token_cap": limits["token_cap"],
                    "status": "NOT_STARTED",
                    "allowed": True,
                    "message": "Budget OK (First invocation)"
                }

            allowed, msg = self.check_budget(ticket_id, agent_role)
            return {
                "ticket_id": ticket_id,
                "agent_role": agent_role,
                "retry_count": row["retry_count"],
                "max_retries": limits["max_retries"],
                "total_tokens": row["total_tokens_consumed"],
                "token_cap": limits["token_cap"],
                "status": row["status"],
                "allowed": allowed,
                "message": msg
            }

    def reset_ticket(self, ticket_id: str, agent_role: str) -> None:
        """Resets retry tracker for a ticket/role (use with caution)."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, agent_role)
            )
            conn.commit()


def main(argv: list[str] | None = None, db_path: Optional[Path] = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Cost Governance & Retry Controller (Phase 2.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check budget before running agent
  python3 scripts/cost_governance.py check --ticket-id KAN-122 --role developer

  # Record token usage after agent attempt
  python3 scripts/cost_governance.py record --ticket-id KAN-122 --role developer --tokens 14500

  # Trigger escalation manually
  python3 scripts/cost_governance.py escalate --ticket-id KAN-122 --role developer --reason "Exceeded 3 repair attempts"

  # Show current status
  python3 scripts/cost_governance.py status --ticket-id KAN-122 --role developer

  # Reset budget for a ticket (admin)
  python3 scripts/cost_governance.py reset --ticket-id KAN-122 --role developer
        """
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_p = subparsers.add_parser("check", help="Check if agent has budget to run")
    check_p.add_argument("--ticket-id", required=True)
    check_p.add_argument("--role", required=True, choices=list(AGENT_LIMITS.keys()))

    record_p = subparsers.add_parser("record", help="Record an agent attempt with token usage")
    record_p.add_argument("--ticket-id", required=True)
    record_p.add_argument("--role", required=True, choices=list(AGENT_LIMITS.keys()))
    record_p.add_argument("--tokens", type=int, default=0, help="Tokens used in this attempt")

    escalate_p = subparsers.add_parser("escalate", help="Trigger manual escalation")
    escalate_p.add_argument("--ticket-id", required=True)
    escalate_p.add_argument("--role", required=True, choices=list(AGENT_LIMITS.keys()))
    escalate_p.add_argument("--reason", required=True)

    status_p = subparsers.add_parser("status", help="Show current budget status")
    status_p.add_argument("--ticket-id", required=True)
    status_p.add_argument("--role", required=True, choices=list(AGENT_LIMITS.keys()))

    reset_p = subparsers.add_parser("reset", help="Reset budget for ticket/role (admin)")
    reset_p.add_argument("--ticket-id", required=True)
    reset_p.add_argument("--role", required=True, choices=list(AGENT_LIMITS.keys()))

    args = parser.parse_args(argv)

    gov = CostGovernor(db_path=db_path) if db_path else CostGovernor()

    if args.command == "check":
        ok, msg = gov.check_budget(args.ticket_id, args.role)
        if not ok:
            print(f"[BUDGET EXCEEDED] {msg}")
            return 2
        print(f"[BUDGET OK] {msg}")
        return 0

    elif args.command == "record":
        count = gov.increment_attempt(args.ticket_id, args.role, args.tokens)
        print(f"[ATTEMPT RECORDED] Current retry count: {count}")
        return 0

    elif args.command == "escalate":
        gov.trigger_escalation(args.ticket_id, args.role, args.reason)
        return 0

    elif args.command == "status":
        status = gov.get_status(args.ticket_id, args.role)
        print(f"Ticket: {status['ticket_id']}")
        print(f"Role: {status['agent_role']}")
        print(f"Retries: {status['retry_count']}/{status['max_retries']}")
        print(f"Tokens: {status['total_tokens']}/{status['token_cap']}")
        print(f"Status: {status['status']}")
        print(f"Allowed: {status['allowed']}")
        print(f"Message: {status['message']}")
        return 0 if status['allowed'] else 2

    elif args.command == "reset":
        gov.reset_ticket(args.ticket_id, args.role)
        print(f"[RESET] Budget cleared for {args.ticket_id} ({args.role})")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))