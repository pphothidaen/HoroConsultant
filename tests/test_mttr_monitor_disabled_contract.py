"""Contract test: the MTTR monitor must not raise an SLO breach for a
workflow an admin deliberately disabled.

Bug (KAN-264): the monitor scanned scheduled runs for a 'success' to clear the
breach. A workflow that is turned off produces no further runs, so no future
'success' can ever arrive and `stillFailing` stays true forever. The alert
becomes unresolvable and the monitor reports a breach indefinitely.

A disable is an administrative decision, not an incident. The monitor has to
distinguish the two.

Strategy: parse the inline `script:` body out of the workflow YAML and assert
the guard exists — disabled_* conclusions are excluded before the breach is
recorded. Source-level rather than execution-based because the logic runs
inside a GitHub Actions `actions/github-script` step with no local runtime.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github/workflows/workflow-mttr-monitor.yml"

DISABLED_CONCLUSIONS = ("disabled_manually", "disabled_automatically")


def _script_body() -> str:
    """Return the JS payload of the github-script step."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"script:\s*\|\n(.*?)\n\s*-\s*name:", text, re.S)
    assert m, "could not locate the inline script block in the monitor workflow"
    return m.group(1)


@pytest.fixture(scope="module")
def body() -> str:
    return _script_body()


# ── The guard exists ───────────────────────────────────────────────────────

@pytest.mark.parametrize("conclusion", DISABLED_CONCLUSIONS)
def test_guard_covers_disabled_conclusion(body: str, conclusion: str) -> None:
    """Both GitHub disable conclusions must be recognised."""
    assert conclusion in body, (
        f"{conclusion} is not handled — an admin-disabled workflow would "
        f"still be reported as an SLO breach"
    )


def test_guard_precedes_breach_recording(body: str) -> None:
    """The guard has to `continue` before `failures.push`.

    Asserting only that the strings are present would pass on a guard placed
    after the breach is already recorded — which fixes nothing.
    """
    guard = body.find("disabled_manually")
    guard = min(g for g in (guard, body.find("disabled_automatically")) if g != -1)
    skip = body.find("continue;", guard)
    push = body.find("failures.push")

    assert guard != -1, "no disabled-conclusion guard found"
    assert skip != -1, "guard does not skip the workflow"
    assert push != -1, "breach recording block not found"
    assert skip < push, (
        "guard runs AFTER failures.push — the breach is still recorded, so "
        "this change would be a no-op"
    )


def test_guard_uses_fresh_latest_run_not_failure_scan(body: str) -> None:
    """The conclusion must come from a latest-run query.

    The pre-existing query filters `status: 'failure'`, which can never
    return a disabled run — reading the conclusion from it would silently
    never match, reproducing the original bug in new code.
    """
    window = body[body.find("disabled_manually") - 800 : body.find("disabled_manually") + 200]
    assert "latestOverall" in window or "per_page: 1" in window, (
        "guard does not read a latest-run conclusion — the failure-filtered "
        "query cannot return disabled runs"
    )


def test_failure_scan_unchanged(body: str) -> None:
    """Regression: the real SLO detection must still work.

    Guards against 'fixing' the breach by never reporting anything.
    """
    assert "stillFailing" in body, "SLO detection logic was removed"
    assert "status: 'failure'" in body, "failure scan was removed"
    assert "sloHours" in body, "SLO threshold was removed"