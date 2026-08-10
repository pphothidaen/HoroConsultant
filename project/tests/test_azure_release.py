"""Executable contracts for the Azure Container Apps release lane."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> tuple[str, dict]:
    path = WORKFLOWS / name
    assert path.exists(), f"missing workflow: {path.relative_to(ROOT)}"
    text = path.read_text(encoding="utf-8")
    parsed = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict)
    return text, parsed


def test_release_is_ci_gated_and_checks_out_the_verified_commit():
    """Only a successful main-branch CI result may enter production."""
    text, workflow = _workflow("deploy.yml")
    triggers = workflow["on"]
    release_job = workflow["jobs"]["release"]

    assert triggers["workflow_run"]["workflows"] == [
        "Unified CI & Quality Audit Pipeline"
    ]
    assert triggers["workflow_run"]["types"] == ["completed"]
    assert "workflow_run.conclusion == 'success'" in release_job["if"]
    assert "workflow_run.head_branch == 'main'" in release_job["if"]
    assert "github.event.workflow_run.head_sha" in text
    assert "cat .env" not in text


def test_release_builds_amd64_once_and_deploys_the_digest():
    """Mutable convenience tags must never be the Azure deployment identity."""
    text, _ = _workflow("deploy.yml")

    assert "platforms: linux/amd64" in text
    assert "pansakorn/horoconsult:latest" in text
    assert "pansakorn/horoconsult:v1.0" in text
    assert "sha-" in text
    assert "steps.build.outputs.digest" in text
    assert "pansakorn/horoconsult@${IMAGE_DIGEST}" in text
    assert "resource-group rg-horoconsult" in text
    assert "name horoconsult-env-new" in text
    assert "containerapp env update" in text
    assert "logs-destination none" in text
    assert "revision set-mode" in text
    assert "mode multiple" in text
    assert "containerapp ingress enable" in text
    assert "target-port 8000" in text
    assert "revision-weight latest=100" in text
    assert "secrets.DOCKER_USERNAME" in text
    assert "secrets.DOCKER_PASSWORD" in text
    assert "secrets.AZURE_CREDENTIALS" in text
    assert "provenance: mode=max" in text
    assert "sbom: true" in text
    assert "docker buildx imagetools inspect" in text
    assert "Platform:[[:space:]]+linux/amd64" in text


def test_release_never_overwrites_the_v1_immutable_tag():
    """The human-readable v1.0 tag is created once and then treated immutable."""
    text, workflow = _workflow("deploy.yml")
    concurrency = workflow["concurrency"]

    assert concurrency["cancel-in-progress"] == "false"
    assert "scripts/dockerhub_tag_policy.py" in text
    assert "DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}" in text
    assert "DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}" in text
    assert "v1.0 already exists; preserving immutable tag" in text


def test_unrequested_external_training_and_fly_deploy_are_manual_only():
    """Kaggle and the exhausted Fly.io target cannot mutate on timers/pushes."""
    for name in ("fly_deploy.yml", "kaggle_finetune.yml", "kaggle_sync.yml"):
        path = WORKFLOWS / name
        if not path.exists():
            continue
        workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
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


def test_container_is_reproducible_non_root_and_scale_to_zero_ready():
    """The production image has pinned builders and no host native artifacts."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "FROM rust:1.97.1-bookworm AS rust-builder" in dockerfile
    assert "FROM python:3.12-slim-bookworm AS runtime" in dockerfile
    rust_builder = dockerfile.split("FROM python:3.12-slim-bookworm", maxsplit=1)[0]
    assert "ARG GIT_COMMIT_HASH=unknown" in rust_builder
    assert 'GIT_COMMIT_HASH="${GIT_COMMIT_HASH}" cargo build' in rust_builder
    assert "maturin==1.14.1" in dockerfile
    assert "cargo build --locked --release --no-default-features --features server --bin horo_server" in dockerfile
    assert 'ENTRYPOINT ["/usr/bin/tini", "--"]' in dockerfile
    assert 'CMD ["/app/horo_server"]' in dockerfile
    assert "USER appuser" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    for pattern in ("**/*.so", "**/*.dylib", "**/*.dll"):
        assert pattern in dockerignore


def test_bicep_caps_consumption_resources_and_exposes_port_8000():
    """IaC must encode the zero-idle-cost deployment policy."""
    bicep = (ROOT / "infra" / "azure" / "main.bicep").read_text(encoding="utf-8")

    assert "minReplicas: 0" in bicep
    assert "maxReplicas: 1" in bicep
    assert "targetPort: 8000" in bicep
    assert "cpu: json('0.5')" in bicep
    assert "memory: '1Gi'" in bicep
    assert "activeRevisionsMode: 'Multiple'" in bicep
    assert "transport: 'auto'" in bicep
    assert "managedEnvironment-rghoroconsult-b5b1" in bicep
    assert "location string = 'westus2'" in bicep
