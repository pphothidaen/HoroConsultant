"""KAN-279: structured cross-functional review system — integration tests.

Covers:
- 4-phase review CLI end-to-end (isolated HOME, JSON sidecar persistence)
- Integration validation suite (5/5 gates)
- Coordination workflow (5-task execution)
- Regression: workflow discovery must glob, not os.path.exists(pattern)
"""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEW_CLI = REPO / ".hermes" / "scripts" / "cross_functional_review.py"
REVIEW_DOC = REPO / ".hermes" / "reviews" / "KAN-279-cross-functional-review.md"
INTEGRATION_TEST = REPO / "scripts" / "integration_test.py"
INTEGRATION_VALIDATOR = REPO / "scripts" / "integration_validator.py"
INTEGRATION_COORDINATION = REPO / "scripts" / "integration_coordination.py"

ROLES = ("red_team", "blue_team", "worker_specialist", "research")


def run_cli(args, cwd=REPO, env_extra=None, timeout=180):
    """Run a repo script with the current interpreter."""
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_review_system_scripts_compile() -> None:
    """Every integration/review script must be valid Python."""
    for path in (REVIEW_CLI, INTEGRATION_TEST, INTEGRATION_VALIDATOR, INTEGRATION_COORDINATION):
        assert path.exists(), f"missing source file: {path}"
        py_compile.compile(str(path), doraise=True)


def test_core_review_cli_help_lists_protocol_commands() -> None:
    """The CLI must expose the 4-phase protocol commands."""
    assert REVIEW_CLI.exists(), "core review CLI missing"
    result = run_cli([str(REVIEW_CLI), "--help"])
    assert result.returncode == 0, result.stderr
    for command in (
        "init",
        "dispatch-prompts",
        "record-perspective",
        "synthesize",
        "decide",
    ):
        assert command in result.stdout, f"missing CLI command: {command}"


def test_four_phase_review_workflow_end_to_end(tmp_path: Path) -> None:
    """init -> dispatch -> 4 perspectives -> synthesize -> decide, across processes."""
    assert REVIEW_CLI.exists(), "core review CLI missing"
    home = {"HOME": str(tmp_path)}
    review_file = tmp_path / ".hermes" / "reviews" / "KAN_279-cross-functional-review.md"

    steps = [
        [str(REVIEW_CLI), "init", "--ticket", "KAN-279",
         "--title", "Structured review", "--problem", "Coordination",
         "--constraints", "Fail-closed", "--criteria", "All gates green"],
        [str(REVIEW_CLI), "dispatch-prompts", "--ticket", "KAN-279",
         "--design", "Option A"],
    ]
    for role in ROLES:
        steps.append(
            [str(REVIEW_CLI), "record-perspective", "--file", str(review_file),
             "--role", role, "--findings", f"findings-{role}"]
        )
    steps.append(
        [str(REVIEW_CLI), "synthesize", "--file", str(review_file),
         "--design-options", "A", "B", "--evaluation-matrix", '{"A": "best"}']
    )
    steps.append(
        [str(REVIEW_CLI), "decide", "--file", str(review_file),
         "--status", "APPROVED"]
    )

    for step in steps:
        result = run_cli(step, env_extra=home)
        assert result.returncode == 0, f"{' '.join(step)} failed:\n{result.stderr}"

    sidecar = tmp_path / ".hermes" / "reviews" / "KAN_279-cross-functional-review.json"
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    assert data["status"] == "COMPLETED"
    for phase in ("phase_1", "phase_2", "phase_3", "phase_4"):
        assert data["phases"][phase]["status"] == "COMPLETED", phase
    assert set(data["perspectives"]) == set(ROLES)

    markdown = review_file.read_text(encoding="utf-8")
    assert "Chosen Option:** APPROVED" in markdown
    assert "findings-red_team" in markdown


def test_integration_test_suite_passes_5_of_5() -> None:
    """The integration test suite must run (no import crashes) and pass 5/5."""
    assert INTEGRATION_TEST.exists(), "integration_test.py missing"
    result = run_cli([str(INTEGRATION_TEST), "test"])
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "Total Tests: 5" in result.stdout
    assert "Passed: 5" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Success Rate: 100.0%" in result.stdout


def test_integration_validator_full_validation_passes() -> None:
    """The validator's full run must report 100% success and exit 0."""
    assert INTEGRATION_VALIDATOR.exists(), "integration_validator.py missing"
    result = run_cli([str(INTEGRATION_VALIDATOR), "validate"])
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "Success Rate: 100.0%" in result.stdout
    assert "Overall Validation Status: SUCCESS" in result.stdout


def test_coordination_workflow_executes_all_five_tasks() -> None:
    """create-plan -> execute-plan -> get-summary: 5/5 tasks COMPLETED."""
    assert INTEGRATION_COORDINATION.exists(), "integration_coordination.py missing"
    create = run_cli([
        str(INTEGRATION_COORDINATION), "create-plan", "--ticket", "KAN-279",
        "--title", "Structured review", "--problem", "Coordination",
        "--constraints", "Fail-closed", "--criteria", "All gates green",
    ])
    assert create.returncode == 0, create.stderr

    execute = run_cli([str(INTEGRATION_COORDINATION), "execute-plan"])
    assert execute.returncode == 0, execute.stderr
    assert "Status: SUCCESS" in execute.stdout

    summary = run_cli([str(INTEGRATION_COORDINATION), "get-summary"])
    assert summary.returncode == 0, summary.stderr
    assert "Completed Tasks: 5" in summary.stdout


def test_workflow_discovery_globs_instead_of_exists_check() -> None:
    """Regression: workflow discovery must glob; os.path.exists('*.py') never matches."""
    assert INTEGRATION_TEST.exists(), "integration_test.py missing"
    spec = importlib.util.spec_from_file_location(
        "kan279_integration_test", INTEGRATION_TEST
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    tester = module.IntegrationTester()
    tester._test_workflow_integration()
    result = tester.test_results[0]
    assert result["status"] == "PASS", result["details"]
    assert any("Workflow scripts found" in detail for detail in result["details"])


def test_review_documentation_present_and_attributed() -> None:
    """The system documentation must exist and cite the correct ticket."""
    assert REVIEW_DOC.exists(), "review documentation missing"
    text = REVIEW_DOC.read_text(encoding="utf-8")
    assert "KAN-279" in text
    assert "KAN-277" not in text, "documentation must not mis-attribute to KAN-277"
    assert "Red Team" in text and "Blue Team" in text
    assert "4-phase" in text
