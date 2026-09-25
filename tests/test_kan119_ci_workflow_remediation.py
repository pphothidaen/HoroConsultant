"""TDD regression tests for KAN-119: CI Workflow Remediation."""

from __future__ import annotations

import subprocess
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


def test_scripts_payload_file_modes_are_regular_644():
    """Verify that gate scripts do not have executable permission bits in git."""
    for script_rel in ("scripts/jira_label_gate.py", "scripts/runtime_guardrails_gate.py"):
        ls_out = subprocess.check_output(
            ["git", "ls-files", "-s", script_rel],
            cwd=ROOT,
            text=True,
        ).strip()
        assert ls_out, f"Script {script_rel} not tracked in git"
        mode = ls_out.split()[0]
        assert mode == "100644", f"Script {script_rel} has mode {mode}, expected 100644"


def test_all_workflows_registered_in_trigger_inventory():
    """Verify that the 4 Sprint J workflows are registered in trigger_all_github_actions."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "trigger_all_github_actions",
        ROOT / "scripts" / "trigger_all_github_actions.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    configured_active = {w[0] for w in mod.WORKFLOWS}
    for required in (
        "governance-drift.yml",
        "jira-sync.yml",
        "workflow-auto-disable.yml",
        "workflow-mttr-monitor.yml",
    ):
        assert required in configured_active, f"{required} missing from WORKFLOWS inventory"


def test_production_monitor_fail_closed_contract():
    """Verify production_monitor.yml has no degraded bypass and enforces 2 surfaces."""
    content = (WORKFLOWS_DIR / "production_monitor.yml").read_text(encoding="utf-8")
    assert 'len(report["surfaces"]) != 2' in content, "Missing exact surface cardinality check"
    assert "raise SystemExit(0 if report[\"success\"] else 1)" in content, "Missing fail-closed exit"
    assert "degraded" not in content, "Degraded mode bypass must not be present in monitor"


def test_workflow_auto_disable_has_workflow_dispatch():
    """Verify workflow-auto-disable.yml has workflow_dispatch trigger."""
    parsed = yaml.load(
        (WORKFLOWS_DIR / "workflow-auto-disable.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    triggers = parsed.get("on", {})
    assert "workflow_dispatch" in triggers, "workflow-auto-disable.yml missing workflow_dispatch trigger"
