"""Regression checks for production CI dependencies."""

from pathlib import Path
import tomllib

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_ai_cicd_installs_pytest_for_the_release_audit():
    """The source-only audit declares its explicit Python fallback boundary."""
    workflow = (ROOT / ".github" / "workflows" / "ai_cicd.yml").read_text(
        encoding="utf-8"
    )

    assert "pip install -r requirements-ci.txt pytest" in workflow
    assert 'HORO_ALLOW_PYTHON_FALLBACK: "1"' in workflow
    assert "--review --use-python" in workflow


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


def test_full_pytest_uses_the_linux_wheel_with_fallback_disabled():
    """The Python release suite must exercise the artifact built by Rust CI."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "actions/upload-artifact@v4" in workflow
    assert "actions/download-artifact@v4" in workflow
    assert "needs: rust-core-audit" in workflow
    assert "pip install --force-reinstall --no-deps wheelhouse/*.whl" in workflow
    assert "rust_core.__native_origin__" in workflow
    assert "shutil.copy2(native_origin, target)" in workflow
    assert 'package_dir.parent / "rust_core.libs"' in workflow
    assert "shutil.copytree(libs_dir, libs_target)" in workflow
    assert "HORO_ALLOW_PYTHON_FALLBACK: \"0\"" in workflow


def test_release_auditor_runs_only_after_the_native_wheel_is_installed():
    """The safety auditor reruns tests and must see the release artifact."""
    parsed = yaml.load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    pytest_steps = [step["name"] for step in parsed["jobs"]["pytest-suite"]["steps"]]
    lint_steps = [step["name"] for step in parsed["jobs"]["lint-and-security"]["steps"]]

    assert pytest_steps.index("Run Project Code Reviewer") > pytest_steps.index(
        "Run Pytest Test Suite"
    )
    assert "Run Project Code Reviewer" not in lint_steps
    review_step = next(
        step
        for step in parsed["jobs"]["pytest-suite"]["steps"]
        if step["name"] == "Run Project Code Reviewer"
    )
    assert "--review --use-python" in review_step["run"]


def test_rust_ci_enforces_format_and_clippy_before_packaging():
    """Formatting or warning regressions must stop the release artifact."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "cargo fmt --all -- --check" in workflow
    assert "cargo clippy --no-default-features --features server --all-targets" in workflow
    assert "-D warnings" in workflow


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
