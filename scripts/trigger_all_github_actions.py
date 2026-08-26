#!/usr/bin/env python3
"""
scripts/trigger_all_github_actions.py
=====================================
Automated orchestrator for the active GitHub Actions workflows via GitHub CLI
(`gh`). Retired workflow tombstones are excluded from both dispatch and counts.

Active workflows:
 1. ai_agent_ecosystem_sync.yml (AI Agent Ecosystem Sync)
 2. ai_cicd.yml (AI Safety Audit)
 3. ci.yml (Unified CI & Quality Audit Pipeline)
 4. hf_backend_deploy.yml (Hugging Face Docker Backend - Production Deployment)
 5. kaggle_dataset_auto_sync.yml (Kaggle Dataset Automated Inspection & Sync Schedule)
 6. kaggle_finetune.yml (HoroConsultant Kaggle Fine-Tuning Pipeline)
 7. kaggle_sync.yml (Kaggle Output Sync Workflow)
 8. lint.yml (Lint & Security Check)
 9. notebooklm_cookie_heartbeat.yml (NotebookLM Cookie Health Heartbeat)
10. production_monitor.yml (Production Synthetic Monitoring)
11. scheduled_distill_finetune.yml (Scheduled Autonomous Knowledge Distillation & Fine-Tuning)

Retired workflow tombstones (never dispatched):
 1. azure_cost_guard.yml
 2. azure_deploy.yml
 3. deploy.yml
 4. fly_deploy.yml

Usage:
    python scripts/trigger_all_github_actions.py
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Final, Literal, TypedDict

ROOT_DIR = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT_DIR / ".github" / "workflows"
WORKFLOW_FILE_PATTERNS: Final[tuple[str, ...]] = ("*.yml", "*.yaml")
WORKFLOW_FILE_SUFFIXES: Final[frozenset[str]] = frozenset({".yml", ".yaml"})

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("gha_trigger")

RETIRED_WORKFLOW_TOMBSTONES: Final[frozenset[str]] = frozenset(
    {
        "azure_cost_guard.yml",
        "azure_deploy.yml",
        "deploy.yml",
        "fly_deploy.yml",
    }
)

WORKFLOWS: tuple[tuple[str, str, dict[str, str]], ...] = (
    ("ai_agent_ecosystem_sync.yml", "AI Agent Ecosystem Sync", {}),
    ("ai_cicd.yml", "AI Safety Audit", {}),
    ("ci.yml", "Unified CI & Quality Audit Pipeline", {}),
    (
        "hf_backend_deploy.yml",
        "Hugging Face Docker Backend - Production Deployment",
        {},
    ),
    (
        "kaggle_dataset_auto_sync.yml",
        "Kaggle Dataset Automated Inspection & Sync Schedule",
        {"force_upload": "false"},
    ),
    (
        "kaggle_finetune.yml",
        "HoroConsultant Kaggle Fine-Tuning Pipeline",
        {"epochs": "3"},
    ),
    ("kaggle_sync.yml", "Kaggle Output Sync Workflow", {}),
    ("lint.yml", "Lint & Security Check", {}),
    ("notebooklm_cookie_heartbeat.yml", "NotebookLM Cookie Health Heartbeat", {}),
    ("production_monitor.yml", "Production Synthetic Monitoring", {}),
    (
        "scheduled_distill_finetune.yml",
        "Scheduled Autonomous Knowledge Distillation & Fine-Tuning",
        {
            "domain": "all",
            "format": "chatml",
            "trigger_training": "true",
            "dry_run": "false",
            "force": "false",
        },
    ),
)

WorkflowStatus = Literal["RETIRED", "TRIGGERED", "FAILED", "ERROR"]


class WorkflowResult(TypedDict):
    """Sanitized result for one workflow dispatch request."""

    file: str
    title: str
    status: WorkflowStatus
    error: str | None


def _ascii_text(value: object) -> str:
    """Return one printable ASCII representation for logs and summaries."""
    return str(value).encode("ascii", errors="backslashreplace").decode("ascii")


def _workflow_name_sort_key(name: str) -> bytes:
    """Return the deterministic UTF-8 ordering key for one workflow name."""
    return name.encode("utf-8")


def _workflow_logical_key(name: str) -> str:
    """Normalize case and YAML suffix aliases for ambiguity detection."""
    suffix = Path(name).suffix
    stem = name[: -len(suffix)] if suffix else name
    return stem.casefold()


def _validate_unambiguous_names(names: tuple[str, ...], source: str) -> None:
    """Reject duplicate, case-ambiguous, or extension-aliased workflow names."""
    if len(names) != len(set(names)):
        raise RuntimeError(f"duplicate workflow names in {_ascii_text(source)}")

    for normalizer, label in (
        (str.casefold, "case"),
        (_workflow_logical_key, "YAML extension"),
    ):
        grouped: dict[str, list[str]] = {}
        for name in names:
            grouped.setdefault(normalizer(name), []).append(name)
        collisions = sorted(
            (
                "/".join(sorted(group, key=_workflow_name_sort_key))
                for group in grouped.values()
                if len(group) > 1
            ),
            key=_workflow_name_sort_key,
        )
        if collisions:
            raise RuntimeError(
                f"workflow {label} ambiguity in {_ascii_text(source)}: "
                + _ascii_text(", ".join(collisions))
            )


def _workflow_filesystem_names() -> tuple[str, ...]:
    """Enumerate reviewed YAML extensions and reject ambiguous paths."""
    yaml_like_paths = sorted(
        (
            path
            for path in WORKFLOWS_DIR.rglob("*")
            if path.suffix.casefold() in WORKFLOW_FILE_SUFFIXES
        ),
        key=lambda path: _workflow_name_sort_key(
            path.relative_to(WORKFLOWS_DIR).as_posix()
        ),
    )
    invalid_paths: list[str] = []
    for path in yaml_like_paths:
        relative = path.relative_to(WORKFLOWS_DIR)
        if (
            len(relative.parts) != 1
            or path.suffix not in WORKFLOW_FILE_SUFFIXES
            or path.is_symlink()
            or not path.is_file()
        ):
            invalid_paths.append(relative.as_posix())
    if invalid_paths:
        raise RuntimeError(
            "workflow inventory contains ambiguous extension/path: "
            + _ascii_text(", ".join(invalid_paths))
        )

    candidates = sorted(
        (
            path
            for pattern in WORKFLOW_FILE_PATTERNS
            for path in WORKFLOWS_DIR.glob(pattern)
        ),
        key=lambda path: _workflow_name_sort_key(path.name),
    )
    candidate_names = tuple(path.name for path in candidates)
    discovered_names = tuple(path.name for path in yaml_like_paths)
    if candidate_names != discovered_names:
        raise RuntimeError("workflow YAML enumeration mismatch")
    _validate_unambiguous_names(candidate_names, "workflow filesystem")
    return candidate_names


def active_workflows() -> tuple[tuple[str, str, dict[str, str]], ...]:
    """Return the reviewed active inventory after fail-closed parity checks."""
    configured_active_names = tuple(workflow[0] for workflow in WORKFLOWS)
    configured_retired_names = tuple(
        sorted(RETIRED_WORKFLOW_TOMBSTONES, key=_workflow_name_sort_key)
    )
    configured_names = configured_active_names + configured_retired_names
    for name in configured_names:
        if (
            name != Path(name).name
            or "/" in name
            or "\\" in name
            or Path(name).suffix not in WORKFLOW_FILE_SUFFIXES
        ):
            raise RuntimeError(
                "workflow inventory contains ambiguous configured path: "
                + _ascii_text(name)
            )

    active_names = set(configured_active_names)
    retired_names = set(configured_retired_names)
    overlap = active_names & retired_names
    if overlap:
        raise RuntimeError(
            "workflow inventory marks entries active and retired: "
            + _ascii_text(
                ", ".join(sorted(overlap, key=_workflow_name_sort_key))
            )
        )
    _validate_unambiguous_names(configured_names, "configured inventory")
    filesystem_names = set(_workflow_filesystem_names())

    expected_names = active_names | retired_names
    if filesystem_names != expected_names:
        missing = sorted(
            expected_names - filesystem_names,
            key=_workflow_name_sort_key,
        )
        unreviewed = sorted(
            filesystem_names - expected_names,
            key=_workflow_name_sort_key,
        )
        raise RuntimeError(
            "workflow inventory/filesystem mismatch "
            f"(missing={_ascii_text(missing)}, "
            f"unreviewed={_ascii_text(unreviewed)})"
        )

    return WORKFLOWS


def trigger_workflow(
    file_name: str,
    title: str,
    inputs: dict[str, str],
) -> WorkflowResult:
    """Trigger a single GitHub Actions workflow via `gh workflow run`."""
    if file_name in RETIRED_WORKFLOW_TOMBSTONES:
        logger.warning("[WARNING] Refusing retired workflow tombstone: %s", file_name)
        return {
            "file": file_name,
            "title": title,
            "status": "RETIRED",
            "error": "retired workflow tombstone",
        }

    cmd = ["gh", "workflow", "run", file_name]
    for k, v in inputs.items():
        cmd.extend(["-f", f"{k}={v}"])

    logger.info("[INFO] Triggering workflow: %s (%s)", file_name, _ascii_text(title))
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
            timeout=25,
            check=False,
        )
        if res.returncode == 0:
            logger.info("[OK] Successfully triggered %s", file_name)
            return {"file": file_name, "title": title, "status": "TRIGGERED", "error": None}
        else:
            err = _ascii_text(res.stderr.strip() or res.stdout.strip())
            logger.warning("[WARNING] Trigger returned code %s: %s", res.returncode, err)
            return {"file": file_name, "title": title, "status": "FAILED", "error": err}
    except (OSError, subprocess.SubprocessError) as exc:
        error = _ascii_text(exc)
        logger.error("[ERROR] Exception triggering %s: %s", file_name, error)
        return {"file": file_name, "title": title, "status": "ERROR", "error": error}


def list_recent_runs() -> list[dict[str, object]]:
    """Fetch recent workflow runs."""
    try:
        cmd = [
            "gh",
            "run",
            "list",
            "--limit",
            "15",
            "--json",
            "databaseId,workflowName,status,conclusion,url,createdAt",
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
            timeout=20,
            check=False,
        )
        if res.returncode == 0:
            return json.loads(res.stdout)
    except (json.JSONDecodeError, OSError, subprocess.SubprocessError) as exc:
        logger.warning("[WARNING] Unable to fetch run list: %s", _ascii_text(exc))
    return []


def main() -> None:
    workflows = active_workflows()
    print("\n" + "=" * 75)
    print("HoroConsultant - Master GitHub Actions Workflow Trigger")
    print("=" * 75)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Active Workflows to Trigger: {len(workflows)}\n")

    results = []
    for fname, title, inps in workflows:
        res = trigger_workflow(fname, title, inps)
        results.append(res)
        time.sleep(1)  # small buffer to prevent secondary rate-limit

    print("\n" + "=" * 75)
    print("Trigger Summary:")
    print("=" * 75)
    for r in results:
        tag = "[OK]" if r["status"] == "TRIGGERED" else "[WARNING]"
        print(f"{tag} {r['file']:<32} | {r['status']:<10} | {_ascii_text(r['title'])}")

    print("\n[INFO] Fetching live active runs from GitHub Actions...")
    time.sleep(3)
    runs = list_recent_runs()
    if runs:
        print("\n" + "=" * 75)
        print("Active / Recent Runs on GitHub Actions:")
        print("=" * 75)
        for run in runs[:10]:
            status = _ascii_text(run.get("status", "QUEUED")).upper()
            name = _ascii_text(run.get("workflowName", "unknown"))
            url = _ascii_text(run.get("url", "unavailable"))
            print(f"- [{status}] {name}: {url}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
