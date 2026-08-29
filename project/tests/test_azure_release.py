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


def test_hf_release_is_ci_gated_and_checks_out_one_exact_source_sha(tmp_path: Path):
    """CI and manual publication require the immutable main event commit."""
    text, workflow = _workflow("hf_backend_deploy.yml")
    triggers = workflow["on"]
    job = workflow["jobs"]["publish-and-verify"]

    assert set(triggers) == {"workflow_run", "workflow_dispatch"}
    assert triggers["workflow_run"] == {
        "workflows": ["Unified CI & Quality Audit Pipeline"],
        "types": ["completed"],
    }
    assert triggers["workflow_dispatch"]["inputs"]["source_sha"] == {
        "description": "Optional full commit SHA to publish; defaults to the dispatch commit",
        "required": "false",
        "type": "string",
    }
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "hf-backend-production",
        "cancel-in-progress": "false",
    }
    assert job["environment"] == "production"
    assert "github.event_name == 'workflow_dispatch'" in job["if"]
    assert "github.ref == 'refs/heads/main'" in job["if"]
    assert "github.event.workflow_run.conclusion == 'success'" in job["if"]
    assert "github.event.workflow_run.head_branch == 'main'" in job["if"]

    source = _step(job, "Resolve immutable release source")
    assert source["env"]["DEFAULT_BRANCH_SHA"] == "${{ github.sha }}"
    assert source["env"]["WORKFLOW_RUN_SHA"] == (
        "${{ github.event.workflow_run.head_sha }}"
    )
    assert source["env"]["MANUAL_SOURCE_SHA"] == "${{ inputs.source_sha }}"
    assert source["env"]["DISPATCH_SHA"] == "${{ github.sha }}"
    assert source["env"]["DISPATCH_REF"] == "${{ github.ref }}"
    assert 're.fullmatch(r"[0-9a-f]{40}", source_sha)' in source["run"]
    assert 'source_sha != os.environ.get("DEFAULT_BRANCH_SHA", "").strip()' in source["run"]

    main_event_sha = "e06b224a2c8d3ff103e662598830353700799b65"
    experimental_sha = "153170770b0830e85a5b413f11782583bb0c8f3b"
    dispatch_env = {
        "EVENT_NAME": "workflow_dispatch",
        "WORKFLOW_RUN_SHA": "",
        "DEFAULT_BRANCH_SHA": main_event_sha,
        "MANUAL_SOURCE_SHA": "",
        "DISPATCH_SHA": main_event_sha,
        "DISPATCH_REF": "refs/heads/main",
    }
    accepted, accepted_output = _run_inline_python_step(
        source,
        dispatch_env,
        tmp_path / "accepted-output.txt",
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert accepted_output == f"sha={main_event_sha}\n"

    wrong_ref, wrong_ref_output = _run_inline_python_step(
        source,
        {**dispatch_env, "DISPATCH_REF": "refs/heads/experimental"},
        tmp_path / "wrong-ref-output.txt",
    )
    assert wrong_ref.returncode == 1
    assert "Manual production publication is restricted to main." in wrong_ref.stdout
    assert wrong_ref_output == ""

    wrong_sha, wrong_sha_output = _run_inline_python_step(
        source,
        {**dispatch_env, "MANUAL_SOURCE_SHA": experimental_sha},
        tmp_path / "wrong-sha-output.txt",
    )
    assert wrong_sha.returncode == 1
    assert "Release source does not match the current main event commit." in (
        wrong_sha.stdout
    )
    assert wrong_sha_output == ""

    checkout = _step(job, "Checkout exact CI-verified source")
    assert checkout["uses"] == (
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
    )
    assert checkout["with"] == {
        "ref": "${{ steps.source.outputs.sha }}",
        "fetch-depth": "0",
        "persist-credentials": "false",
    }
    verify = _step(job, "Verify source identity and clean checkout")
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_SOURCE_SHA"' in verify["run"]
    assert "git diff --quiet" in verify["run"]
    assert "git diff --cached --quiet" in verify["run"]
    assert "git status --porcelain --untracked-files=all" in verify["run"]
    assert "github.event.workflow_run.head_sha" in text


def test_hf_release_keeps_docker_backend_and_vercel_ui_separate():
    """The backend Space may never receive the Vercel static UI payload."""
    text, workflow = _workflow("hf_backend_deploy.yml")
    job = workflow["jobs"]["publish-and-verify"]
    separation = _step(
        job,
        "Enforce Vercel static and HF Docker target separation (canonical)",
    )["run"]

    assert job["env"]["CANONICAL_HF_BACKEND_SPACE_ID"] == (
        "pphothidaen/horoconsultant-core-backend"
    )
    assert "VERCEL_STATIC_URL" in job["env"]
    assert "HF_BACKEND_URL" in job["env"]
    assert "backend_space_id != canonical_space_id" in separation
    assert 'static_host.endswith(".hf.space")' in separation
    assert "static_url == backend_url" in separation
    assert "HF_STATIC_SPACE_ID is retired" in separation
    assert "${{ vars." not in text
    assert "${{ env." not in text
    assert not re.search(r"(?:dotenv_values|load_dotenv)\s*\(", text)
    assert "--sdk static" not in text
    assert "Publish static frontend" not in text


def test_hf_release_masks_tokens_and_uses_the_supported_docker_publisher_cli():
    """Managed tokens stay masked and the workflow uses only supported CLI flags."""
    _, workflow = _workflow("hf_backend_deploy.yml")
    job = workflow["jobs"]["publish-and-verify"]
    token_step = _step(job, "Resolve and mask HF deployment token")
    publish = _step(job, "Publish canonical Docker API backend")

    assert all(
        value.startswith("${{ secrets.") and value.endswith(" }}")
        for value in token_step["env"].values()
    )
    assert token_step["run"].index("::add-mask::") < token_step["run"].index(
        "GITHUB_ENV"
    )
    assert 'env_file.write(f"HF_TOKEN={token}\\n")' in token_step["run"]
    assert "[REDACTED_HF_TOKEN]" in publish["run"]
    assert "Authenticated as Hugging Face user:" in publish["run"]
    assert "Bearer " in publish["run"]

    invocation = re.search(
        r"python3 scripts/publish_space_hf\.py\s+"
        r"(?P<args>.*?)\s+2>&1\s*\|",
        publish["run"],
        flags=re.DOTALL,
    )
    assert invocation is not None
    assert set(re.findall(r"--[a-z-]+", invocation.group("args"))) == {
        "--expected-parent-revision",
        "--manifest-path",
        "--receipt-path",
        "--space-id",
        "--sdk",
    }
    assert '--space-id "$HF_BACKEND_SPACE_ID"' in invocation.group("args")
    assert "--sdk docker" in invocation.group("args")
    assert '--manifest-path "$HF_RELEASE_MANIFEST_PATH"' in invocation.group("args")
    assert '--receipt-path "$HF_RELEASE_RECEIPT_PATH"' in invocation.group("args")
    assert '--expected-parent-revision "$EXPECTED_PARENT_REVISION"' in invocation.group(
        "args"
    )
    assert publish["env"]["EXPECTED_MANIFEST_SHA256"] == (
        "${{ steps.manifest.outputs.sha256 }}"
    )
    assert publish["env"]["EXPECTED_PARENT_REVISION"] == (
        "${{ steps.parent.outputs.revision }}"
    )
    assert (
        'manifest.get("manifest_sha256") != os.environ["EXPECTED_MANIFEST_SHA256"]'
        in publish["run"]
    )

    publisher_source = (ROOT / "scripts" / "publish_space_hf.py").read_text(
        encoding="utf-8"
    )
    assert 'parser.add_argument("--space-id"' in publisher_source
    assert (
        'parser.add_argument("--sdk", choices=["static", "docker"]' in publisher_source
    )
    for flag in (
        "--manifest-path",
        "--receipt-path",
        "--expected-parent-revision",
    ):
        assert f'"{flag}"' in publisher_source


def test_hf_release_artifact_hook_is_always_guarded_and_sanitized():
    """Only validated, guarded manifest and receipt evidence may be uploaded."""
    _, workflow = _workflow("hf_backend_deploy.yml")
    job = workflow["jobs"]["publish-and-verify"]
    validation = _step(job, "Validate bound publisher receipt and artifact safety")
    upload = _step(job, "Upload sanitized release evidence")

    assert validation["id"] == "release_evidence"
    validation_run = validation["run"]
    for guard in (
        "not stat.S_ISREG(file_stat.st_mode)",
        "stat.S_IMODE(file_stat.st_mode) != 0o600",
        "not 0 < file_stat.st_size <= max_bytes",
        "path.resolve().parent != expected_dir",
        'manifest = load_guarded("HF_RELEASE_MANIFEST_PATH", 16 * 1024 * 1024)',
        'receipt = load_guarded("HF_RELEASE_RECEIPT_PATH", 1024 * 1024)',
    ):
        assert guard in validation_run
    assert validation_run.index(
        "validate_release_receipt(receipt, manifest)"
    ) < validation_run.index('output.write("ready=true\\n")')

    assert upload["if"] == (
        "${{ always() && steps.release_evidence.outputs.ready == 'true' }}"
    )
    assert upload["uses"] == (
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
    )
    assert upload["with"]["name"] == (
        "hf-docker-release-evidence-${{ steps.source.outputs.sha }}"
    )
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["retention-days"] == "30"
    artifact_paths = set(upload["with"]["path"].splitlines())
    assert artifact_paths == {
        "${{ steps.evidence_paths.outputs.manifest }}",
        "${{ steps.evidence_paths.outputs.receipt }}",
    }
    assert not any(
        re.search(r"(?:token|secret|credential|\.env|\.log)", path, re.IGNORECASE)
        for path in artifact_paths
    )


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
