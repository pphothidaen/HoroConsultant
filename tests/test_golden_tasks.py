#!/usr/bin/env python3
"""TDD contract tests for tests/golden_tasks/__init__.py (KAN-101).

Freezes the golden-task loader/validator behavior BEFORE implementation.
Tasks:
- load_all_tasks: reads every *_tasks.json and returns a flat list
- validate_task: reports invalid role/interface/model_tier and bad tool_calls range
- validate_all: (total, valid, errors) summary
- summary: aggregated counts per role, interfaces, model_tiers
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_TASKS_DIR = REPO_ROOT / "tests" / "golden_tasks"
sys.path.insert(0, str(GOLDEN_TASKS_DIR))

# Importing the package's __init__ module
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "golden_tasks", str(GOLDEN_TASKS_DIR / "__init__.py")
)
golden_tasks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(golden_tasks)


def test_load_all_tasks_returns_non_empty_list():
    tasks = golden_tasks.load_all_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) >= 20, f"expected at least 20 golden tasks, got {len(tasks)}"


def test_load_all_tasks_contains_four_roles():
    tasks = golden_tasks.load_all_tasks()
    roles = {t["role"] for t in tasks}
    assert roles == {"qa_tester", "devops", "code_reviewer", "orchestrator"}


def test_load_all_tasks_each_role_has_five_tasks():
    tasks = golden_tasks.load_all_tasks()
    by_role: dict[str, int] = {}
    for t in tasks:
        by_role[t["role"]] = by_role.get(t["role"], 0) + 1
    for role in ("qa_tester", "devops", "code_reviewer", "orchestrator"):
        assert by_role[role] == 5, f"{role} expected 5 tasks, got {by_role[role]}"


def test_load_all_tasks_ids_are_unique():
    tasks = golden_tasks.load_all_tasks()
    ids = [t["id"] for t in tasks]
    assert len(ids) == len(set(ids)), f"duplicate task ids: {ids}"


def test_load_all_tasks_interfaces_use_both_cli_and_browser():
    tasks = golden_tasks.load_all_tasks()
    interfaces = {t["interface"] for t in tasks}
    assert "cli" in interfaces
    assert "browser" in interfaces


def test_load_all_tasks_model_tiers_include_reasoning_and_frontier():
    tasks = golden_tasks.load_all_tasks()
    tiers = {t["model_tier"] for t in tasks}
    assert "reasoning" in tiers
    assert "frontier-multimodal" in tiers


def test_validate_task_accepts_valid_task():
    task = {
        "id": "qa-01",
        "name": "test",
        "role": "qa_tester",
        "interface": "cli",
        "model_tier": "reasoning",
        "tool_calls_min": 5,
        "tool_calls_max": 10,
        "expected_outcome": "ok",
        "pass_criterion": "yes",
    }
    errors = golden_tasks.validate_task(task)
    assert errors == [], f"unexpected errors: {errors}"


def test_validate_task_rejects_invalid_role():
    task = {"id": "x", "role": "wizard", "interface": "cli",
            "model_tier": "reasoning", "tool_calls_min": 1, "tool_calls_max": 5,
            "expected_outcome": "ok"}
    errors = golden_tasks.validate_task(task)
    assert any("invalid role" in e for e in errors)


def test_validate_task_rejects_invalid_interface():
    task = {"id": "x", "role": "qa_tester", "interface": "telepathy",
            "model_tier": "reasoning", "tool_calls_min": 1, "tool_calls_max": 5,
            "expected_outcome": "ok"}
    errors = golden_tasks.validate_task(task)
    assert any("invalid interface" in e for e in errors)


def test_validate_task_rejects_invalid_model_tier():
    task = {"id": "x", "role": "qa_tester", "interface": "cli",
            "model_tier": "quantum", "tool_calls_min": 1, "tool_calls_max": 5,
            "expected_outcome": "ok"}
    errors = golden_tasks.validate_task(task)
    assert any("invalid model_tier" in e for e in errors)


def test_validate_task_rejects_min_greater_than_max():
    task = {"id": "x", "role": "qa_tester", "interface": "cli",
            "model_tier": "reasoning", "tool_calls_min": 20, "tool_calls_max": 5,
            "expected_outcome": "ok"}
    errors = golden_tasks.validate_task(task)
    assert any("tool_calls_min > max" in e for e in errors)


def test_validate_task_rejects_missing_id():
    task = {"role": "qa_tester", "interface": "cli",
            "model_tier": "reasoning", "tool_calls_min": 1, "tool_calls_max": 5,
            "expected_outcome": "ok"}
    errors = golden_tasks.validate_task(task)
    assert any("missing id" in e for e in errors)


def test_validate_all_returns_correct_totals():
    total, valid, errors = golden_tasks.validate_all()
    assert total == 20
    assert valid == 20
    assert errors == []


def test_summary_structure():
    s = golden_tasks.summary()
    assert s["total_tasks"] == 20
    assert set(s["by_role"].keys()) == {"qa_tester", "devops", "code_reviewer", "orchestrator"}
    assert all(c == 5 for c in s["by_role"].values())
    assert "cli" in s["interfaces"]
    assert "browser" in s["interfaces"]
    assert "reasoning" in s["model_tiers"]


def test_each_task_has_required_fields():
    tasks = golden_tasks.load_all_tasks()
    required = {"id", "name", "role", "interface", "model_tier",
                "tool_calls_min", "tool_calls_max", "expected_outcome",
                "pass_criterion", "measures"}
    for t in tasks:
        missing = required - set(t.keys())
        assert not missing, f"task {t.get('id')} missing fields: {missing}"
