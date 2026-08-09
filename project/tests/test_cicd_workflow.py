"""Regression checks for production CI dependencies."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ai_cicd_installs_pytest_for_the_release_audit():
    """The audit invokes ``python -m pytest`` and needs pytest in CI."""
    workflow = (ROOT / ".github" / "workflows" / "ai_cicd.yml").read_text(
        encoding="utf-8"
    )

    assert "pip install -r requirements-ci.txt pytest" in workflow


def test_release_audit_collects_only_portable_test_directories():
    """Avoid collecting standalone scripts with optional browser dependencies."""
    pytest_config = (ROOT / "pytest.ini").read_text(encoding="utf-8")

    assert "testpaths = project/tests tests" in pytest_config
