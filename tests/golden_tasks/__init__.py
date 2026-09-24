#!/usr/bin/env python3
"""Golden task set for model routing eval harness (KAN-101).

Frozen, replayable prompts per agent role used to measure success rate
and token cost of routing decisions. Each task is scored pass/fail by
the orchestrator, then joined to a cost-ledger session entry.

Per role: 5 tasks x 4 roles = 20 tasks. Scale by adding new task files
under this directory (must end in _tasks.json)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_TASKS_DIR = REPO_ROOT / "tests" / "golden_tasks"

VALID_ROLES = ("qa_tester", "devops", "code_reviewer", "orchestrator")
VALID_INTERFACES = ("cli", "browser")
VALID_MODEL_TIERS = ("reasoning", "frontier-multimodal", "flash-lite")


def load_all_tasks() -> list[dict]:
    """Load and validate all golden task files in tests/golden_tasks/."""
    tasks: list[dict] = []
    if not GOLDEN_TASKS_DIR.is_dir():
        return tasks
    for f in sorted(GOLDEN_TASKS_DIR.glob("*_tasks.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        file_role = payload.get("role", "")
        for t in payload.get("tasks", []):
            t["_source_file"] = f.name
            if "role" not in t:
                t["role"] = file_role
            tasks.append(t)
    return tasks


def validate_task(task: dict) -> list[str]:
    """Return a list of validation errors for a single task."""
    errors: list[str] = []
    if not task.get("id"):
        errors.append("missing id")
    if task.get("role") not in VALID_ROLES:
        errors.append(f"invalid role: {task.get('role')}")
    if task.get("interface") not in VALID_INTERFACES:
        errors.append(f"invalid interface: {task.get('interface')}")
    if task.get("model_tier") not in VALID_MODEL_TIERS:
        errors.append(f"invalid model_tier: {task.get('model_tier')}")
    if "tool_calls_min" not in task or "tool_calls_max" not in task:
        errors.append("missing tool_calls_min/max range")
    elif task["tool_calls_min"] > task["tool_calls_max"]:
        errors.append(f"tool_calls_min > max: {task['tool_calls_min']} > {task['tool_calls_max']}")
    if not task.get("expected_outcome"):
        errors.append("missing expected_outcome")
    return errors


def validate_all() -> tuple[int, int, list[str]]:
    """Validate all golden tasks. Returns (total, valid, errors)."""
    tasks = load_all_tasks()
    errors: list[str] = []
    valid = 0
    for t in tasks:
        errs = validate_task(t)
        if errs:
            errors.append(f"{t.get('id', '?')}: {', '.join(errs)}")
        else:
            valid += 1
    return len(tasks), valid, errors


def summary() -> dict:
    tasks = load_all_tasks()
    by_role: dict[str, int] = {}
    for t in tasks:
        by_role[t["role"]] = by_role.get(t["role"], 0) + 1
    return {
        "total_tasks": len(tasks),
        "by_role": by_role,
        "interfaces": sorted({t["interface"] for t in tasks}),
        "model_tiers": sorted({t["model_tier"] for t in tasks}),
    }
