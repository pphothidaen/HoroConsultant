#!/usr/bin/env python3
"""Test suite for Runtime Execution Guardrails Gate — KAN-118."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Import module under test (will fail in RED phase before implementation)
from runtime_guardrails_gate import (
    ALLOWED_AGENT_LABELS,
    extract_jira_ticket,
    validate_agent_label,
    validate_dispatch,
    validate_tool_call,
    detect_synthetic_mock,
    validate_mutation_command,
)


class TestTicketExtraction:
    """Verify Jira Ticket extraction from text/prompts/commands."""

    def test_valid_kan_ticket(self):
        ticket = extract_jira_ticket("Work on KAN-118 implementation")
        assert ticket == "KAN-118"

    def test_valid_kan_ticket_in_brackets(self):
        ticket = extract_jira_ticket("[KAN-105] Fix governance hook")
        assert ticket == "KAN-105"

    def test_missing_kan_ticket(self):
        ticket = extract_jira_ticket("Update documentation without ticket")
        assert ticket is None

    def test_malformed_kan_ticket_rejected(self):
        assert extract_jira_ticket("KAN-") is None
        assert extract_jira_ticket("KAN-ABC") is None
        assert extract_jira_ticket("PROJECT-123") is None


class TestAgentLabelValidation:
    """Verify agent label validation against allowed roster."""

    def test_allowed_agent_labels_roster(self):
        assert "agent-orchestrator" in ALLOWED_AGENT_LABELS
        assert "agent-hermes" in ALLOWED_AGENT_LABELS
        assert "agent-developer_core" in ALLOWED_AGENT_LABELS
        assert "agent-qa_tester" in ALLOWED_AGENT_LABELS
        assert "agent-code_reviewer" in ALLOWED_AGENT_LABELS
        assert "agent-devops" in ALLOWED_AGENT_LABELS
        assert "agent-lead_ba" in ALLOWED_AGENT_LABELS
        assert "agent-ba_intake" in ALLOWED_AGENT_LABELS
        assert "agent-ba_auditor" in ALLOWED_AGENT_LABELS

    @pytest.mark.parametrize("label", [
        "agent-orchestrator",
        "agent-hermes",
        "agent-developer_core",
        "agent-qa_tester",
        "agent-code_reviewer",
        "agent-devops",
        "agent-agy1",
        "agent-codex1",
    ])
    def test_valid_agent_labels(self, label: str):
        ok, msg = validate_agent_label(label)
        assert ok is True
        assert "valid" in msg.lower()

    @pytest.mark.parametrize("invalid_label", [
        "agent-unknown",
        "agent-hacker",
        "developer",
        "hermes",
        "",
        "None",
    ])
    def test_invalid_agent_labels(self, invalid_label: str):
        ok, msg = validate_agent_label(invalid_label)
        assert ok is False
        assert "invalid" in msg.lower() or "unauthorized" in msg.lower() or "empty" in msg.lower()


class TestDispatchValidation:
    """Verify pre-dispatch governance rules."""

    def test_dispatch_approved_with_ticket_and_label(self):
        prompt = "Implement TDD test suite for [KAN-118]"
        ok, reason = validate_dispatch(prompt, "agent-hermes")
        assert ok is True
        assert "approved" in reason.lower()

    def test_dispatch_denied_missing_ticket(self):
        prompt = "Just edit some code without referencing Jira"
        ok, reason = validate_dispatch(prompt, "agent-hermes")
        assert ok is False
        assert "missing jira ticket" in reason.lower()

    def test_dispatch_denied_invalid_agent_label(self):
        prompt = "Task for KAN-118"
        ok, reason = validate_dispatch(prompt, "agent-fake")
        assert ok is False
        assert "unauthorized agent" in reason.lower() or "invalid" in reason.lower()


class TestToolUseValidation:
    """Verify pre-tool-use interception for mutations."""

    def test_read_only_tools_allowed_without_ticket(self):
        for tool in ["view_file", "search_web", "list_resources", "git status"]:
            ok, reason = validate_tool_call(tool, {"path": "README.md"})
            assert ok is True

    def test_write_tools_require_ticket_in_args_or_context(self):
        ok, reason = validate_tool_call(
            "write_to_file",
            {"TargetFile": "src/foo.py", "Description": "Update foo"},
            context=None,
        )
        assert ok is False
        assert "requires jira ticket" in reason.lower()

    def test_write_tools_approved_with_ticket_in_context(self):
        ok, reason = validate_tool_call(
            "write_to_file",
            {"TargetFile": "src/foo.py", "Description": "Update foo [KAN-118]"},
            context="KAN-118",
        )
        assert ok is True


class TestSyntheticMockDetection:
    """Acceptance Criteria 1: Eliminate synthetic/mock execution strings."""

    @pytest.mark.parametrize("mock_str", [
        "fake_execution_result_123",
        "mock_response_from_api",
        "simulate_run_command_output",
        "synthetic_subagent_run",
    ])
    def test_detects_mock_execution_strings(self, mock_str: str):
        detected, reason = detect_synthetic_mock(mock_str)
        assert detected is True
        assert "synthetic" in reason.lower() or "mock" in reason.lower()

    def test_allows_clean_real_outputs(self):
        detected, reason = detect_synthetic_mock("PASSED 25 tests in 0.05s")
        assert detected is False


class TestMutationCommandValidation:
    """Verify CLI command guardrails."""

    def test_state_mutation_requires_ticket_and_agent(self):
        ok, reason = validate_mutation_command("git commit -m 'feat: update'")
        assert ok is False

        ok, reason = validate_mutation_command("git commit -m 'feat: update [KAN-118] agent-hermes'")
        assert ok is True
