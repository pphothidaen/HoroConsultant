#!/usr/bin/env python3
"""Runtime Execution Guardrails Gate — KAN-118 / KAN-105.

Enforces execution guardrails across AI agents, pre-dispatch hooks, and pre-tool calls:
1. Eliminates synthetic/mock command strings from chat turns to prevent upstream policy triggers.
2. Enforces valid Jira Ticket ID (KAN-<ID>) before state mutations.
3. Enforces valid agent-* specialist label validation before task dispatch.
4. Provides hook implementations for .hermes/hooks/ and .githooks/.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Authorized specialist agent labels matching the active multi-agent ecosystem
ALLOWED_AGENT_LABELS = {
    "agent-orchestrator",
    "agent-hermes",
    "agent-developer_core",
    "agent-qa_tester",
    "agent-code_reviewer",
    "agent-devops",
    "agent-lead_ba",
    "agent-ba_intake",
    "agent-ba_auditor",
    "agent-default",
    "agent-agy1",
    "agent-agy2",
    "agent-agy3",
    "agent-agy4",
    "agent-agy5",
    "agent-codex1",
    "agent-codex2",
    "agent-codex3",
}

# Jira ticket pattern
KAN_TICKET_PATTERN = re.compile(r"\bKAN-\d+\b")

# Known synthetic/mock string patterns that indicate fake execution or unverified simulations
SYNTHETIC_MOCK_PATTERNS = [
    re.compile(r"fake_execution_result", re.IGNORECASE),
    re.compile(r"mock_response", re.IGNORECASE),
    re.compile(r"simulate_run_command", re.IGNORECASE),
    re.compile(r"synthetic_subagent", re.IGNORECASE),
]

# Read-only tools that do not mutate state
READ_ONLY_TOOLS = {
    "view_file",
    "search_files",
    "search_web",
    "list_resources",
    "read_resource",
    "manage_task",
    "manage_subagents",
    "git status",
    "git log",
    "git diff",
    "git branch",
}

# Mutation tools that alter codebase, deployment, or issues
MUTATION_TOOLS = {
    "write_to_file",
    "replace_file_content",
    "generate_image",
    "run_command",
    "call_mcp_tool",
}


def extract_jira_ticket(text: str) -> Optional[str]:
    """Extract first valid KAN-<NUM> ticket from text."""
    if not text:
        return None
    match = KAN_TICKET_PATTERN.search(text)
    return match.group(0) if match else None


def validate_agent_label(label: str) -> Tuple[bool, str]:
    """Validate agent label against allowed roster."""
    if not label or not isinstance(label, str):
        return False, "Agent label is empty or invalid"
    clean_label = label.strip()
    if clean_label in ALLOWED_AGENT_LABELS:
        return True, f"Valid agent label '{clean_label}'"
    return False, f"Unauthorized or invalid agent label: '{clean_label}'"


def detect_synthetic_mock(text: str) -> Tuple[bool, str]:
    """Detect synthetic/mock command strings that bypass real execution."""
    if not text:
        return False, "Empty text"
    for pattern in SYNTHETIC_MOCK_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Detected synthetic mock pattern: '{match.group(0)}'"
    return False, "Clean real output verified"


def validate_dispatch(prompt: str, agent_label: str) -> Tuple[bool, str]:
    """Validate task prompt and agent label before subagent dispatch."""
    ticket = extract_jira_ticket(prompt)
    if not ticket:
        return False, "Missing Jira ticket identifier (KAN-<NUM>) in dispatch prompt."

    label_ok, label_msg = validate_agent_label(agent_label)
    if not label_ok:
        return False, f"Unauthorized agent label: {label_msg}"

    return True, f"Dispatch approved for {ticket} assigned to {agent_label}."


def validate_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    context: Optional[str] = None,
) -> Tuple[bool, str]:
    """Validate tool call permissions and required ticket context."""
    tool_clean = tool_name.strip()

    # Read-only tools always permitted
    if tool_clean in READ_ONLY_TOOLS:
        return True, f"Read-only tool '{tool_clean}' permitted without ticket."

    # For mutation tools, ensure ticket context is present either in args or context
    args_str = str(arguments)
    ticket_in_args = extract_jira_ticket(args_str)
    ticket_in_context = extract_jira_ticket(context or "")

    if not (ticket_in_args or ticket_in_context):
        return (
            False,
            f"Tool '{tool_clean}' requires Jira ticket context (KAN-<NUM>) before execution.",
        )

    return True, f"Tool '{tool_clean}' authorized with ticket {ticket_in_args or ticket_in_context}."


def validate_mutation_command(command_str: str) -> Tuple[bool, str]:
    """Validate CLI command string for ticket and agent label compliance."""
    if not command_str:
        return False, "Empty command string"

    # Only enforce on git commit / mutation commands
    if "git commit" in command_str:
        ticket = extract_jira_ticket(command_str)
        if not ticket:
            return False, "Commit command missing Jira Ticket ID (KAN-<NUM>)."

        has_agent_label = any(label in command_str for label in ALLOWED_AGENT_LABELS)
        if not has_agent_label:
            return False, "Commit command missing authorized agent-* label."

        return True, f"Commit command verified with {ticket}."

    return True, "Command does not require commit governance check."


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime Execution Guardrails Gate.")
    parser.add_argument("--check-dispatch", action="store_true", help="Validate dispatch prompt & agent label")
    parser.add_argument("--check-tool", action="store_true", help="Validate tool call arguments")
    parser.add_argument("--check-command", action="store_true", help="Validate CLI command")
    parser.add_argument("--prompt", default="", help="Prompt or task description")
    parser.add_argument("--agent", default="", help="Agent label (e.g. agent-hermes)")
    parser.add_argument("--tool", default="", help="Tool name")
    parser.add_argument("--command", default="", help="CLI command string")

    args = parser.parse_args()

    if args.check_dispatch:
        ok, msg = validate_dispatch(args.prompt, args.agent)
        print(f"[{'OK' if ok else 'ERROR'}] {msg}")
        return 0 if ok else 1
    elif args.check_command:
        ok, msg = validate_mutation_command(args.command)
        print(f"[{'OK' if ok else 'ERROR'}] {msg}")
        return 0 if ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
