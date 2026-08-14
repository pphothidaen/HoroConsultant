"""
project/mlops/run_pipeline.py
==============================
Master Autonomous MLOps Pipeline Runner for HoroConsultant.
Orchestrates:
1. NotebookLM Grounded Extraction via MCP / Session
2. Hermes Agent Knowledge Mining & CoT Synthesis
3. Quality Gate Validation, Deduplication & JSONL Export
4. Kaggle GPU Fine-Tuning Execution Trigger
5. Webhook Alerting (Telegram/Discord)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import HermesKnowledgeMiner, SyntheticSample
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mlops_pipeline")


def run_full_pipeline(
    domain: str = "all",
    dataset_name: str = "bazi_instruct_v1",
    target_format: str = "chatml",
    trigger_training: bool = False,
    dry_run: bool = False
) -> dict:
    """Execute complete end-to-end distillation and training cycle."""
    notifier = WebhookNotifier()
    miner = HermesKnowledgeMiner()
    curator = DatasetCurator(output_dir=ROOT_DIR / "project" / "data")
    orchestrator = FineTuneOrchestrator(notifier=notifier)

    logger.info(f"[PIPELINE START] Domain: {domain}, Format: {target_format}, Dry-run: {dry_run}")
    
    all_samples: list[SyntheticSample] = []
    
    try:
        # Step 1: Knowledge Mining
        if domain == "all":
            domain_dict = miner.mine_all_domains()
            for d_samples in domain_dict.values():
                all_samples.extend(d_samples)
        else:
            all_samples = miner.mine_domain(domain=domain)

        # Step 2: Quality Gate Curation & Export
        stats = curator.curate_and_export(
            samples=all_samples,
            dataset_name=dataset_name,
            target_format=target_format
        )

        # Step 3: Webhook Notification for Distillation
        notifier.notify_distillation_complete(stats)

        # Step 4: Fine-Tuning Trigger
        training_res = None
        if trigger_training:
            logger.info("[PIPELINE] Triggering fine-tuning on Kaggle GPU...")
            training_res = orchestrator.trigger_kaggle_training(
                dataset_path=stats["output_path"],
                dry_run=dry_run
            )

        logger.info("[PIPELINE COMPLETE] Pipeline execution succeeded.")
        return {
            "status": "SUCCESS",
            "stats": stats,
            "training": training_res
        }

    except Exception as e:
        logger.error(f"[PIPELINE FAILED] Error: {e}", exc_info=True)
        notifier.notify_error("Full Pipeline Runner", str(e))
        return {
            "status": "FAILED",
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Autonomous MLOps Distillation & Fine-Tuning Pipeline")
    parser.add_argument("--domain", type=str, default="bazi", choices=["bazi", "ziwei", "fengshui", "qimen", "all"])
    parser.add_argument("--dataset-name", type=str, default="finetune_bazi_qwen25")
    parser.add_argument("--format", type=str, default="chatml", choices=["chatml", "alpaca", "raw"])
    parser.add_argument("--trigger-training", action="store_true", help="Automatically trigger Kaggle GPU fine-tuning")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without external API calls")
    
    args = parser.parse_args()
    result = run_full_pipeline(
        domain=args.domain,
        dataset_name=args.dataset_name,
        target_format=args.format,
        trigger_training=args.trigger_training,
        dry_run=args.dry_run
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
