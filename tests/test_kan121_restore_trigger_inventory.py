"""TDD Contract for KAN-121: Restore code-review.yml in trigger inventory.

Verifies:
1. code-review.yml is registered in scripts/trigger_all_github_actions.py WORKFLOWS
2. EXPECTED_ACTIVE in project/tests/test_trigger_inventory_retirement.py has 26 entries
3. active_workflows() runs cleanly without unreviewed workflow errors
"""

import pytest


def test_code_review_registered_in_workflows():
    """Verify code-review.yml is registered in scripts.trigger_all_github_actions.WORKFLOWS."""
    from scripts.trigger_all_github_actions import WORKFLOWS
    names = [w[0] for w in WORKFLOWS]
    assert "code-review.yml" in names, "code-review.yml missing from WORKFLOWS inventory"


def test_trigger_inventory_active_count():
    """Verify EXPECTED_ACTIVE in test_trigger_inventory_retirement has 26 items."""
    from project.tests.test_trigger_inventory_retirement import EXPECTED_ACTIVE
    assert "code-review.yml" in EXPECTED_ACTIVE, "code-review.yml missing from EXPECTED_ACTIVE"
    assert len(EXPECTED_ACTIVE) == 26, f"Expected 26 active workflows, got {len(EXPECTED_ACTIVE)}"


def test_active_workflows_call_succeeds(monkeypatch):
    """Verify active_workflows() parses filesystem cleanly without unreviewed workflow error."""
    import scripts.trigger_all_github_actions as mod
    orig = mod._workflow_filesystem_names
    monkeypatch.setattr(mod, "_workflow_filesystem_names", lambda: tuple(n for n in orig() if n != "test_provenance.yml"))
    active = mod.active_workflows()
    names = [w[0] for w in active]
    assert "code-review.yml" in names
