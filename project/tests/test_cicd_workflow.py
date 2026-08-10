"""Regression checks for production CI dependencies."""

from pathlib import Path
import tomllib


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


def test_rust_ci_exercises_each_feature_boundary_and_installed_wheel():
    """Rust CI must test core, server, and the installed mixed wheel explicitly."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "cargo test --no-default-features" in workflow
    assert (
        "cargo test --no-default-features --features server --all-targets"
        in workflow
    )
    assert "cargo tree --no-default-features --features server" in workflow
    assert "python tests/test_installed_wheel.py" in workflow


def test_pyo3_cli_is_not_server_eligible_without_python_feature():
    """The SVG CLI must not enter the PyO3-free server target matrix."""
    cargo = tomllib.loads(
        (ROOT / "rust_core" / "Cargo.toml").read_text(encoding="utf-8")
    )
    svg_target = next(
        target for target in cargo["bin"] if target["name"] == "svg_chart_cli"
    )

    assert svg_target["required-features"] == ["python", "server"]


def test_maturin_version_is_pinned_in_package_and_ci():
    """Wheel builds must use the same exact maturin version locally and in CI."""
    pyproject = tomllib.loads(
        (ROOT / "rust_core" / "pyproject.toml").read_text(encoding="utf-8")
    )
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert pyproject["build-system"]["requires"] == ["maturin==1.14.1"]
    assert "maturin==1.14.1" in workflow
