#!/usr/bin/env python3
"""
Unit tests for Cost Governance & Retry Controller (Phase 2.3)

Tests for scripts/cost_governance.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cost_governance import CostGovernor, main, AGENT_LIMITS


class TestCostGovernor(unittest.TestCase):
    """Tests for CostGovernor class."""

    def setUp(self):
        """Set up test environment with temporary database."""
        self.original_env = dict(os.environ)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_metrics.db"

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        self.temp_dir.cleanup()

    def _create_governor(self):
        """Create a CostGovernor with temp database."""
        return CostGovernor(db_path=self.db_path)

    def test_fresh_ticket_within_budget(self):
        """Test that a new ticket returns allowed=True."""
        gov = self._create_governor()
        ok, msg = gov.check_budget("KAN-122", "developer")
        self.assertTrue(ok)
        self.assertIn("Budget OK", msg)

    def test_retry_limit_breached_blocks_execution(self):
        """Test that exceeding max retries returns exit code 2."""
        gov = self._create_governor()
        ticket_id = "KAN-122"
        role = "developer"

        # Increment up to max_retries (3 for developer)
        for i in range(AGENT_LIMITS[role]["max_retries"]):
            count = gov.increment_attempt(ticket_id, role, tokens_used=1000)
            self.assertEqual(count, i + 1)

        # Next check should fail
        ok, msg = gov.check_budget(ticket_id, role)
        self.assertFalse(ok)
        self.assertIn("Exceeded max retries", msg)

    def test_token_cap_breached_blocks_execution(self):
        """Test that exceeding token cap returns not allowed."""
        gov = self._create_governor()
        ticket_id = "KAN-123"
        role = "qa_tester"
        token_cap = AGENT_LIMITS[role]["token_cap"]

        # Use tokens up to cap
        gov.increment_attempt(ticket_id, role, tokens_used=token_cap)

        # Next check should fail
        ok, msg = gov.check_budget(ticket_id, role)
        self.assertFalse(ok)
        self.assertIn("Exceeded token cap", msg)

    def test_escalation_records_jsonl_and_db(self):
        """Test that escalation updates status to ESCALATED and writes to JSONL."""
        gov = self._create_governor()
        ticket_id = "KAN-124"
        role = "code_reviewer"

        # Trigger escalation
        gov.trigger_escalation(ticket_id, role, "Test escalation reason")

        # Check DB status
        with gov._get_connection() as conn:
            row = conn.execute(
                "SELECT status FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, role)
            ).fetchone()
        self.assertEqual(row["status"], "ESCALATED")

        # Check JSONL file (written to db_path.parent)
        esc_file = self.db_path.parent / "escalations.jsonl"
        self.assertTrue(esc_file.exists())
        content = esc_file.read_text().strip()
        record = json.loads(content)
        self.assertEqual(record["ticket_id"], ticket_id)
        self.assertEqual(record["agent_role"], role)
        self.assertEqual(record["reason"], "Test escalation reason")
        self.assertEqual(record["status"], "ESCALATED")

    def test_increment_attempt_accumulates_tokens(self):
        """Test that token usage accumulates correctly."""
        gov = self._create_governor()
        ticket_id = "KAN-125"
        role = "developer"

        gov.increment_attempt(ticket_id, role, tokens_used=5000)
        gov.increment_attempt(ticket_id, role, tokens_used=3000)
        gov.increment_attempt(ticket_id, role, tokens_used=2000)

        with gov._get_connection() as conn:
            row = conn.execute(
                "SELECT total_tokens_consumed FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, role)
            ).fetchone()
        self.assertEqual(row["total_tokens_consumed"], 10000)

    def test_different_roles_independent(self):
        """Test that different agent roles track independently."""
        gov = self._create_governor()
        ticket_id = "KAN-126"

        gov.increment_attempt(ticket_id, "developer", tokens_used=1000)
        gov.increment_attempt(ticket_id, "qa_tester", tokens_used=500)
        gov.increment_attempt(ticket_id, "developer", tokens_used=2000)

        with gov._get_connection() as conn:
            dev_row = conn.execute(
                "SELECT retry_count, total_tokens_consumed FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, "developer")
            ).fetchone()
            qa_row = conn.execute(
                "SELECT retry_count, total_tokens_consumed FROM agent_retry_tracker WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, "qa_tester")
            ).fetchone()

        self.assertEqual(dev_row["retry_count"], 2)
        self.assertEqual(dev_row["total_tokens_consumed"], 3000)
        self.assertEqual(qa_row["retry_count"], 1)
        self.assertEqual(qa_row["total_tokens_consumed"], 500)

    def test_get_status_returns_correct_info(self):
        """Test that get_status returns accurate status info."""
        gov = self._create_governor()
        ticket_id = "KAN-127"
        role = "developer"

        # Fresh ticket
        status = gov.get_status(ticket_id, role)
        self.assertEqual(status["retry_count"], 0)
        self.assertEqual(status["total_tokens"], 0)
        self.assertEqual(status["status"], "NOT_STARTED")
        self.assertTrue(status["allowed"])

        # After some attempts
        gov.increment_attempt(ticket_id, role, tokens_used=5000)
        status = gov.get_status(ticket_id, role)
        self.assertEqual(status["retry_count"], 1)
        self.assertEqual(status["total_tokens"], 5000)
        self.assertEqual(status["status"], "ACTIVE")
        self.assertTrue(status["allowed"])

    def test_reset_ticket_clears_tracker(self):
        """Test that reset clears the retry tracker."""
        gov = self._create_governor()
        ticket_id = "KAN-128"
        role = "developer"

        gov.increment_attempt(ticket_id, role, tokens_used=5000)
        gov.reset_ticket(ticket_id, role)

        status = gov.get_status(ticket_id, role)
        self.assertEqual(status["retry_count"], 0)
        self.assertEqual(status["total_tokens"], 0)
        self.assertEqual(status["status"], "NOT_STARTED")

    def test_record_token_usage_stores_details(self):
        """Test that token_ledger records detailed usage."""
        gov = self._create_governor()
        ticket_id = "KAN-129"
        role = "qa_tester"

        gov.record_token_usage(
            ticket_id=ticket_id,
            agent_role=role,
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            estimated_cost_usd=0.045,
            session_id="sess-123"
        )

        with gov._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM token_ledger WHERE ticket_id = ? AND agent_role = ?",
                (ticket_id, role)
            ).fetchone()

        self.assertEqual(row["model"], "gpt-4o")
        self.assertEqual(row["prompt_tokens"], 1000)
        self.assertEqual(row["completion_tokens"], 500)
        self.assertEqual(row["total_tokens"], 1500)
        self.assertEqual(row["estimated_cost_usd"], 0.045)
        self.assertEqual(row["session_id"], "sess-123")

    def test_escalated_ticket_blocks_future_checks(self):
        """Test that once escalated, future checks are blocked."""
        gov = self._create_governor()
        ticket_id = "KAN-130"
        role = "code_reviewer"

        gov.trigger_escalation(ticket_id, role, "Manual escalation")

        ok, msg = gov.check_budget(ticket_id, role)
        self.assertFalse(ok)
        self.assertIn("ESCALATED", msg)

    def test_token_cap_threshold_boundary(self):
        """Test exact token cap boundary."""
        gov = self._create_governor()
        ticket_id = "KAN-131"
        role = "qa_tester"
        token_cap = AGENT_LIMITS[role]["token_cap"]

        # Exactly at cap - should still be allowed for the check
        gov.increment_attempt(ticket_id, role, tokens_used=token_cap)
        ok, msg = gov.check_budget(ticket_id, role)
        self.assertFalse(ok)
        self.assertIn("Exceeded token cap", msg)


class TestCLI(unittest.TestCase):
    """Tests for CLI entry point."""

    def setUp(self):
        self.original_env = dict(os.environ)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_metrics.db"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)
        self.temp_dir.cleanup()

    def _run_cli(self, args: list[str]) -> int:
        """Run CLI with patched DB path."""
        with patch("sys.argv", ["cost_governance.py"] + args):
            return main(db_path=self.db_path)

    def test_cli_check_fresh_ticket(self):
        """Test CLI check command on fresh ticket."""
        result = self._run_cli(["check", "--ticket-id", "KAN-122", "--role", "developer"])
        self.assertEqual(result, 0)

    def test_cli_check_after_retries(self):
        """Test CLI check command after max retries."""
        # Pre-populate DB
        gov = CostGovernor(db_path=self.db_path)
        for _ in range(3):
            gov.increment_attempt("KAN-122", "developer")

        result = self._run_cli(["check", "--ticket-id", "KAN-122", "--role", "developer"])
        self.assertEqual(result, 2)

    def test_cli_record_attempt(self):
        """Test CLI record command."""
        result = self._run_cli(["record", "--ticket-id", "KAN-122", "--role", "developer", "--tokens", "5000"])
        self.assertEqual(result, 0)

    def test_cli_escalate(self):
        """Test CLI escalate command."""
        result = self._run_cli(["escalate", "--ticket-id", "KAN-122", "--role", "developer", "--reason", "Test"])
        self.assertEqual(result, 0)

    def test_cli_status(self):
        """Test CLI status command."""
        result = self._run_cli(["status", "--ticket-id", "KAN-122", "--role", "developer"])
        self.assertEqual(result, 0)

    def test_cli_reset(self):
        """Test CLI reset command."""
        gov = CostGovernor(db_path=self.db_path)
        gov.increment_attempt("KAN-122", "developer", tokens_used=5000)

        result = self._run_cli(["reset", "--ticket-id", "KAN-122", "--role", "developer"])
        self.assertEqual(result, 0)

        # Verify reset
        result = self._run_cli(["status", "--ticket-id", "KAN-122", "--role", "developer"])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)