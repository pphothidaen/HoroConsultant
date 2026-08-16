"""
project/mlops/training/finetune_orchestrator.py
================================================
Fine-Tuning Orchestrator & Kaggle GPU Execution Bridge.
Packages datasets, triggers Kaggle GPU fine-tuning runs for target model
'pphothidaen/qwen2.5-7b-bazi-instruct-4bit', and tracks training lifecycle.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from project.core.config import Config
from project.core.model_activation import get_active_model, update_active_model
from project.mlops.notifications.webhook_notifier import WebhookNotifier

logger = logging.getLogger("finetune_orchestrator")

TARGET_MODEL_ID = Config.HF_REPO_ID
KAGGLE_KERNEL_ID = "pphothidaen/horoconsultant-finetune-pipeline"


class FineTuneOrchestrator:
    """Coordinates fine-tuning workflow with Kaggle GPU resources and Hugging Face Hub."""

    def __init__(
        self,
        target_model: str = TARGET_MODEL_ID,
        notifier: Optional[WebhookNotifier] = None
    ):
        self.target_model = target_model
        self.notifier = notifier or WebhookNotifier()
        self.root_dir = Path(__file__).resolve().parents[3]

    def trigger_kaggle_training(
        self,
        dataset_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger Kaggle GPU kernel execution for model fine-tuning.
        """
        logger.info(f"[ORCHESTRATOR] Initiating fine-tuning for model: '{self.target_model}'")
        
        if dry_run or os.getenv("MLOPS_DRY_RUN", "false").lower() == "true":
            logger.info("[ORCHESTRATOR] Dry-run mode enabled: Simulating training dispatch.")
            res = {
                "status": "QUEUED (DRY-RUN)",
                "kernel_id": KAGGLE_KERNEL_ID,
                "target_model": self.target_model,
                "dataset_path": dataset_path or "project/data/finetune_bazi_qwen25_chatml.jsonl",
                "active_model_update": "skipped (dry-run)",
                "message": "Simulated fine-tuning kernel push success."
            }
            self.notifier.notify_training_status(KAGGLE_KERNEL_ID, "QUEUED (DRY-RUN)", "Dry-run simulation dispatched.")
            return res

        try:
            # Execute push via kaggle_notebook_manager.py
            cmd = [
                sys.executable,
                str(self.root_dir / "scripts" / "kaggle_notebook_manager.py"),
                "--push",
            ]
            if dataset_path:
                cmd.extend(["--dataset-path", dataset_path])
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if proc.returncode == 0:
                logger.info(f"[ORCHESTRATOR] Kaggle kernel successfully pushed: {proc.stdout}")
                active_state = update_active_model(
                    self.target_model,
                    status="active",
                    source="kaggle_orchestrator",
                    notes="Auto-updated by successful Kaggle trigger",
                    training_metadata={
                        "kernel_id": KAGGLE_KERNEL_ID,
                        "dataset_path": dataset_path or "project/data/finetune_bazi_qwen25_chatml.jsonl",
                        "proc_returncode": proc.returncode,
                    },
                )
                self.notifier.notify_training_status(
                    KAGGLE_KERNEL_ID,
                    "RUNNING",
                    f"Fine-tuning kernel pushed to Kaggle T4 GPU. Target: {self.target_model}"
                )
                return {
                    "status": "RUNNING",
                    "kernel_id": KAGGLE_KERNEL_ID,
                    "target_model": self.target_model,
                    "active_model": active_state,
                    "output": proc.stdout
                }
            else:
                err = proc.stderr or proc.stdout
                logger.error(f"[ORCHESTRATOR] Kaggle push failed: {err}")
                self.notifier.notify_error("Kaggle Kernel Push", err)
                return {
                    "status": "FAILED",
                    "kernel_id": KAGGLE_KERNEL_ID,
                    "error": err
                }
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Exception during training trigger: {e}")
            self.notifier.notify_error("Kaggle Training Orchestration", str(e))
            return {
                "status": "ERROR",
                "error": str(e)
            }

    def get_training_status(self) -> Dict[str, Any]:
        """Check status of Kaggle Fine-Tuning Kernel."""
        try:
            cmd = [
                sys.executable,
                str(self.root_dir / "scripts" / "kaggle_notebook_manager.py"),
                "--status"
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            status_text = proc.stdout.strip()
            return {
                "kernel_id": KAGGLE_KERNEL_ID,
                "target_model": self.target_model,
                "raw_status": status_text,
                "returncode": proc.returncode
            }
        except Exception as e:
            return {
                "kernel_id": KAGGLE_KERNEL_ID,
                "error": str(e)
            }
