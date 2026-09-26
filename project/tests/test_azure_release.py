"""Fail-closed contracts for retired cloud lanes and the HF Docker release."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"

RETIRED_DEPLOYMENT_WORKFLOWS = (
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
    "hf_backend_deploy.yml",
)


def _workflow(name: str) -> tuple[str, dict[str, Any]]:
    path = WORKFLOWS / name
    assert path.exists(), f"missing workflow: {path.relative_to(ROOT)}"
    text = path.read_text(encoding="utf-8")
    parsed = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict)
    return text, parsed


def _step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected one step named {name!r}, found {len(matches)}"
    return matches[0]


def _run_inline_python_step(
    step: dict[str, Any], env: dict[str, str], output_path: Path
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Execute one workflow Python heredoc with an isolated event environment."""
    match = re.fullmatch(
        r"python3 - <<'PY'\n(?P<script>.*)\nPY\n?",
        step["run"],
        flags=re.DOTALL,
    )
    assert match is not None
    completed = subprocess.run(
        [sys.executable, "-c", match.group("script")],
        cwd=ROOT,
        env={
            **env,
            "GITHUB_OUTPUT": str(output_path),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    return completed, output


@pytest.mark.parametrize("workflow_name", RETIRED_DEPLOYMENT_WORKFLOWS)
def test_retired_deployment_workflows_are_visible_inert_tombstones(
    workflow_name: str,
):
    """Manual visibility must not make a retired deployment executable."""
    text, workflow = _workflow(workflow_name)

    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["on"]["workflow_dispatch"] == ""
    assert workflow["permissions"] == {}
    assert "env" not in workflow
    assert len(workflow["jobs"]) == 1

    job = next(iter(workflow["jobs"].values()))
    assert job["if"] == "${{ false }}"
    assert set(job) == {"name", "if", "runs-on", "steps"}
    assert len(job["steps"]) == 1

    notice = job["steps"][0]
    assert set(notice) == {"name", "run"}
    commands = [line.strip() for line in notice["run"].splitlines() if line.strip()]
    assert len(commands) == 2
    assert commands[0].startswith('echo "::error::')
    assert commands[1] == "exit 1"

    # Tombstones may describe the retired platform, but may not receive a
    # credential, invoke an action, or contain an executable mutation hook.
    assert "uses:" not in text
    assert not re.search(r"\$\{\{\s*(?:secrets|vars|env)\.", text)
    assert not re.search(
        r"(?:\baz\s+|\bflyctl\b|\bdocker\s+(?:login|build|push)\b|"
        r"publish_space_hf\.py|container-apps-deploy-action|\bcurl\b|\bwget\b)",
        notice["run"],
        flags=re.IGNORECASE,
    )


def test_azure_cost_guard_is_a_dormant_manual_tombstone():
    """The retired cost guard must be visible but impossible to execute."""
    text, workflow = _workflow("azure_cost_guard.yml")

    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {}
    assert "env" not in workflow
    assert "concurrency" not in workflow
    assert set(workflow["jobs"]) == {"retired"}

    job = workflow["jobs"]["retired"]
    assert job["if"] == "${{ false }}"
    assert set(job) == {"name", "if", "runs-on", "steps"}
    assert "environment" not in job
    assert "permissions" not in job
    assert "env" not in job
    assert len(job["steps"]) == 1

    notice = _step(job, "Retirement notice")
    assert set(notice) == {"name", "run"}
    commands = [line.strip() for line in notice["run"].splitlines() if line.strip()]
    assert len(commands) == 2
    assert commands[0].startswith('echo "[ERROR]')
    assert commands[1] == "exit 1"

    assert "uses:" not in text
    assert "scripts/azure_usage_guard.py" not in text
    assert "--enforce" not in text
    assert "--resume-after-reset" not in text
    assert not re.search(r"\$\{\{\s*(?:secrets|vars|env)\.", text)
    assert not re.search(
        r"(?:\baz\s+|\bcurl\b|\bwget\b|https?://|azure/login|doppler|"
        r"\btoken\b|\bcredential\b)",
        notice["run"],
        flags=re.IGNORECASE,
    )


def test_hf_backend_deploy_is_retired_tombstone():
    """Hugging Face Space backend is permanently retired in favor of Render primary backend."""
    text, workflow = _workflow("hf_backend_deploy.yml")
    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {}
    assert set(workflow["jobs"]) == {"retired"}
    job = workflow["jobs"]["retired"]
    assert job["if"] == "${{ false }}"
    notice = _step(job, "Retirement notice")
    assert "permanently retired in favor of Render primary backend" in notice["run"]



def test_unrequested_external_training_is_manual_only():
    """The separate Kaggle mutation lanes cannot run on timers or pushes."""
    for name in ("kaggle_finetune.yml", "kaggle_sync.yml"):
        _, workflow = _workflow(name)
        assert set(workflow["on"]) == {"workflow_dispatch"}

    ai_text, ai_workflow = _workflow("ai_cicd.yml")
    assert "schedule" not in ai_workflow["on"]
    assert "kaggle-ai-cicd" not in ai_workflow["jobs"]
    assert "git push origin main" not in ai_text


def test_quality_workflows_fail_closed_instead_of_masking_findings():
    """Lint and security findings must stop CI."""
    for name in ("ci.yml", "lint.yml"):
        text, _ = _workflow(name)
        assert "--exit-zero" not in text

    ci_text, _ = _workflow("ci.yml")
    assert "pytest" in ci_text.split("Run Pytest Test Suite", maxsplit=1)[0]


def test_production_container_is_reproducible_and_non_root():
    """The approved HF Docker image has pinned builders and no host artifacts."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "FROM rust:1.97.1-bookworm AS rust-builder" in dockerfile
    assert "FROM python:3.12-slim-bookworm AS runtime" in dockerfile
    rust_builder = dockerfile.split("FROM python:3.12-slim-bookworm", maxsplit=1)[0]
    assert "ARG GIT_COMMIT_HASH=unknown" in rust_builder
    assert 'GIT_COMMIT_HASH="${GIT_COMMIT_HASH}" cargo build' in rust_builder
    assert "maturin==1.14.1" in dockerfile
    assert "patchelf" in rust_builder
    assert (
        "cargo build --locked --release --no-default-features --features server "
        "--bin horo_server"
    ) in dockerfile
    assert "COPY scripts ./scripts" in dockerfile
    assert 'ENTRYPOINT ["/usr/bin/tini", "--"]' in dockerfile
    assert 'CMD ["/app/horo_server"]' in dockerfile
    assert "USER appuser" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    for pattern in ("**/*.so", "**/*.dylib", "**/*.dll"):
        assert pattern in dockerignore
    for runtime_exclusion in (
        "project/tests",
        "project/grafana",
        "project/kaggle_kernel",
        "project/rag/datasets",
    ):
        assert runtime_exclusion in dockerignore
