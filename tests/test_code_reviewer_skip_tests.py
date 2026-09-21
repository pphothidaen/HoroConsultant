"""Contract tests for CodeReviewer --skip-tests flag (CI nested-run prevention).

Root cause being fixed: the 'Run Project Code Reviewer' CI step in ci.yml
runs `code_reviewer.py --review --use-python` AFTER the Pytest Test Suite
step already ran the full suite. run_tests() then re-runs the entire suite
a second time (nested), which is redundant and intermittently hangs until
the 1800s subprocess timeout, failing CI on main (observed 2026-09-21,
run 35600839519, job 106337112183).

Contract:
  * --skip-tests makes run_full_review() report the test suite as SKIPPED
    (status "SKIPPED", no subprocess spawn) instead of re-running pytest.
  * SKIPPED must NOT trip the STOP_CONDITION_TEST_REGRESSION stop condition.
  * Default behavior (no flag) is unchanged: run_tests() still executes.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "project" / "core" / "code_reviewer.py"


@pytest.fixture(scope="module")
def reviewer_module():
    spec = importlib.util.spec_from_file_location("code_reviewer_under_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["code_reviewer_under_test"] = module
    spec.loader.exec_module(module)
    return module


class TestSkipTestsFlag:
    def test_flag_exists_in_argparse(self, reviewer_module):
        """--skip-tests must be an accepted CLI flag."""
        parser_cmds: list[str] = []

        import argparse

        original_add_argument = argparse.ArgumentParser.add_argument

        def spy_add_argument(self, *args, **kwargs):
            parser_cmds.append(str(args[0]))
            return original_add_argument(self, *args, **kwargs)

        with patch.object(
            argparse.ArgumentParser, "add_argument", spy_add_argument
        ):
            try:
                reviewer_module.main()
            except SystemExit:
                pass

        assert any("--skip-tests" in c for c in parser_cmds), (
            "--skip-tests flag not registered in argparse"
        )

    def test_run_full_review_skip_tests_reports_skipped(self, reviewer_module):
        """run_full_review(skip_tests=True) must NOT spawn a pytest subprocess."""
        reviewer = reviewer_module.CodeReviewer()

        with patch.object(
            reviewer_module.CodeReviewer, "run_tests", wraps=None
        ) as mock_run_tests, patch.object(
            reviewer_module.CodeReviewer, "scan_secrets"
        ) as ms, patch.object(
            reviewer_module.CodeReviewer, "audit_python_ast"
        ) as ma, patch.object(
            reviewer_module.CodeReviewer, "audit_kaggle_dependencies"
        ) as mk, patch.object(
            reviewer_module.CodeReviewer, "audit_notebooks"
        ) as mn, patch.object(
            reviewer_module.CodeReviewer, "audit_test_provenance"
        ) as mp:
            ms.return_value = {"status": "PASSED", "secret_leaks_found": 0}
            ma.return_value = {"status": "PASSED", "issues_found": 0}
            mk.return_value = {"status": "PASSED", "issues_found": 0}
            mn.return_value = {"status": "PASSED", "issues_found": 0}
            mp.return_value = {"status": "NOT_REQUESTED", "issues": []}

            report = reviewer.run_full_review(skip_tests=True)

            mock_run_tests.assert_not_called()
            assert report["test_suite"]["status"] == "SKIPPED"
            assert report["overall_status"] == "READY_FOR_PROD"

    def test_default_run_tests_still_executes(self, reviewer_module):
        """Without the flag, run_tests() must still be invoked (unchanged)."""
        reviewer = reviewer_module.CodeReviewer()

        with patch.object(
            reviewer_module.CodeReviewer, "run_tests"
        ) as mock_run_tests, patch.object(
            reviewer_module.CodeReviewer, "scan_secrets"
        ) as ms, patch.object(
            reviewer_module.CodeReviewer, "audit_python_ast"
        ) as ma, patch.object(
            reviewer_module.CodeReviewer, "audit_kaggle_dependencies"
        ) as mk, patch.object(
            reviewer_module.CodeReviewer, "audit_notebooks"
        ) as mn, patch.object(
            reviewer_module.CodeReviewer, "audit_test_provenance"
        ) as mp:
            ms.return_value = {"status": "PASSED", "secret_leaks_found": 0}
            ma.return_value = {"status": "PASSED", "issues_found": 0}
            mk.return_value = {"status": "PASSED", "issues_found": 0}
            mn.return_value = {"status": "PASSED", "issues_found": 0}
            mock_run_tests.return_value = {
                "passed": True,
                "exit_code": 0,
                "summary": "ok",
                "status": "PASSED",
            }
            mp.return_value = {"status": "NOT_REQUESTED", "issues": []}

            report = reviewer.run_full_review()

            mock_run_tests.assert_called_once()
            assert report["test_suite"]["status"] == "PASSED"
            assert report["overall_status"] == "READY_FOR_PROD"

    def test_ci_yml_uses_skip_tests_flag(self):
        """ci.yml reviewer step must pass --skip-tests (suite already ran)."""
        ci_yml = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        reviewer_step = ci_yml[ci_yml.find("Run Project Code Reviewer") :]
        assert "--skip-tests" in reviewer_step, (
            "ci.yml reviewer step does not pass --skip-tests; "
            "nested full-suite run will recur"
        )
