#!/usr/bin/env python3
"""
scripts/trigger_all_github_actions.py
=====================================
Automated Orchestrator to Trigger All 14 GitHub Actions Workflows via GitHub CLI (`gh`).
Triggers:
 1. ai_agent_ecosystem_sync.yml (AI Agent Ecosystem Sync)
 2. ai_cicd.yml (AI Safety Audit)
 3. azure_cost_guard.yml (Azure Free Grant Guard)
 4. azure_deploy.yml (Azure Container Apps — Production Deployment)
 5. ci.yml (Unified CI & Quality Audit Pipeline)
 6. deploy.yml (Azure Container Apps Production Release)
 7. hf_backend_deploy.yml (Hugging Face Docker Backend - Production Deployment)
 8. kaggle_finetune.yml (HoroConsultant Kaggle Fine-Tuning Pipeline)
 9. kaggle_sync.yml (Kaggle Output Sync Workflow)
10. lint.yml (Lint & Security Check)
11. notebooklm_cookie_heartbeat.yml (NotebookLM Cookie Health Heartbeat)
12. production_monitor.yml (Production Synthetic Monitoring)
13. scheduled_distill_finetune.yml (Scheduled Autonomous Knowledge Distillation & Fine-Tuning)
14. fly_deploy.yml ([RETIRED] Fly.io Deployment — Optional)

Usage:
    python scripts/trigger_all_github_actions.py
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gha_trigger")

WORKFLOWS = [
    ("ci.yml", "Unified CI & Quality Audit Pipeline", {}),
    ("ai_cicd.yml", "AI Safety Audit", {}),
    ("ai_agent_ecosystem_sync.yml", "AI Agent Ecosystem Sync", {}),
    ("lint.yml", "Lint & Security Check", {}),
    ("production_monitor.yml", "Production Synthetic Monitoring", {}),
    ("notebooklm_cookie_heartbeat.yml", "NotebookLM Cookie Health Heartbeat", {}),
    ("kaggle_finetune.yml", "HoroConsultant Kaggle Fine-Tuning Pipeline", {"epochs": "3"}),
    ("scheduled_distill_finetune.yml", "Scheduled Autonomous Knowledge Distillation & Fine-Tuning", {"domain": "all", "format": "chatml", "trigger_training": "true", "dry_run": "false", "force": "false"}),
    ("kaggle_sync.yml", "Kaggle Output Sync Workflow", {}),
    ("azure_cost_guard.yml", "Azure Free Grant Guard", {}),
    ("azure_deploy.yml", "Azure Container Apps — Production Deployment", {}),
    ("deploy.yml", "Azure Container Apps Production Release", {}),
    ("hf_backend_deploy.yml", "Hugging Face Docker Backend - Production Deployment", {}),
]


def trigger_workflow(file_name: str, title: str, inputs: dict) -> dict:
    """Trigger a single GitHub Actions workflow via `gh workflow run`."""
    cmd = ["gh", "workflow", "run", file_name]
    for k, v in inputs.items():
        cmd.extend(["-f", f"{k}={v}"])

    logger.info(f"🚀 Triggering workflow: {file_name} ({title})...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=25)
        if res.returncode == 0:
            logger.info(f"   ✅ Successfully triggered {file_name}")
            return {"file": file_name, "title": title, "status": "TRIGGERED", "error": None}
        else:
            err = res.stderr.strip() or res.stdout.strip()
            logger.warning(f"   ⚠️ Trigger returned code {res.returncode}: {err}")
            return {"file": file_name, "title": title, "status": "FAILED", "error": err}
    except Exception as e:
        logger.error(f"   ❌ Exception triggering {file_name}: {e}")
        return {"file": file_name, "title": title, "status": "ERROR", "error": str(e)}


def list_recent_runs() -> list:
    """Fetch recent workflow runs."""
    try:
        cmd = ["gh", "run", "list", "--limit", "15", "--json", "databaseId,workflowName,status,conclusion,url,createdAt"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=20)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception as e:
        logger.warning(f"Note fetching run list: {e}")
    return []


def main():
    print("\n" + "=" * 75)
    print("🐙 HoroConsultant — Master GitHub Actions Workflow Trigger")
    print("=" * 75)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Workflows to Trigger: {len(WORKFLOWS)}\n")

    results = []
    for fname, title, inps in WORKFLOWS:
        res = trigger_workflow(fname, title, inps)
        results.append(res)
        time.sleep(1)  # small buffer to prevent secondary rate-limit

    print("\n" + "=" * 75)
    print("📋 Trigger Summary:")
    print("=" * 75)
    for r in results:
        sym = "✅" if r["status"] == "TRIGGERED" else "⚠️"
        print(f"{sym} {r['file']:<32} | {r['status']:<10} | {r['title']}")

    print("\n⏳ Fetching live active runs from GitHub Actions...")
    time.sleep(3)
    runs = list_recent_runs()
    if runs:
        print("\n" + "=" * 75)
        print("🏃 Active / Recent Runs on GitHub Actions:")
        print("=" * 75)
        for run in runs[:10]:
            print(f"• [{run.get('status', 'QUEUED').upper()}] {run.get('workflowName')}: {run.get('url')}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
