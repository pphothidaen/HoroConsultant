from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
RECOVERY_REF = "recovery/pre-test-provenance-20260827"
POST_DEPLOY_EVIDENCE = (
    ROOT
    / "project/tests/artifacts/hf_post_deploy_v3_verification_2026-08-25.json"
)
FULL_SUITE_JOBS = (
    (".github/workflows/ci.yml", "pytest-suite"),
    (".github/workflows/ai_cicd.yml", "code-review-and-audit"),
)


def _workflow(path: str) -> dict[str, object]:
    loaded = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


@pytest.mark.parametrize(("workflow_path", "job_name"), FULL_SUITE_JOBS)
def test_full_suite_jobs_restore_complete_history_and_recovery_ref(
    workflow_path: str,
    job_name: str,
) -> None:
    workflow = _workflow(workflow_path)
    job = workflow["jobs"][job_name]
    steps = job["steps"]
    checkout = next(
        step for step in steps if step.get("uses") == "actions/checkout@v4"
    )

    assert checkout.get("with", {}).get("fetch-depth") == 0
    run_scripts = "\n".join(str(step.get("run", "")) for step in steps)
    assert (
        f"refs/remotes/origin/{RECOVERY_REF}:refs/heads/{RECOVERY_REF}"
        in run_scripts
    )


def test_post_deploy_consensus_screenshots_are_tracked_and_allowlisted() -> None:
    evidence = json.loads(POST_DEPLOY_EVIDENCE.read_text(encoding="utf-8"))
    screenshots = evidence["visual_evidence"]["screenshots"]
    ignore_lines = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())

    assert len(screenshots) == 5
    for item in screenshots:
        path = item["path"]
        assert (ROOT / path).is_file()
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert tracked.returncode == 0
        assert f"!{path}" in ignore_lines
