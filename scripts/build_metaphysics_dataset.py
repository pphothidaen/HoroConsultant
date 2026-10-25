#!/usr/bin/env python3
"""
scripts/build_metaphysics_dataset.py
====================================
CLI Orchestrator for Metaphysics Fine-Tuning Dataset Generation (v3.0).

Generates and validates ShareGPT JSONL & HuggingFace/MLX Instruction datasets
across all 16 disciplines and 6 consultation domains with Chain-of-Thought (CoT)
reasoning and classical treatise citations.

Outputs:
  - project/rag/datasets/train_sharegpt_v3.jsonl (1,000+ training records)
  - project/rag/datasets/eval_sharegpt_v3.jsonl (100+ validation records)
  - project/rag/datasets/train_instruction_v3.jsonl
  - project/rag/datasets/eval_instruction_v3.jsonl
  - project/data/mlx_finetune/train_sharegpt_v3.jsonl
  - project/data/mlx_finetune/valid_sharegpt_v3.jsonl

Usage:
  python3 scripts/build_metaphysics_dataset.py --generate
  python3 scripts/build_metaphysics_dataset.py --generate --target-count 1500 --val-split 0.1
  python3 scripts/build_metaphysics_dataset.py --verify-only

Pure ASCII logging standard ([INFO], [OK], [WARNING], [ERROR]).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project.rag.dataset_builder import (
    DEFAULT_BENCHMARK_PATH,
    DATASETS_DIR,
    MetaphysicsDatasetBuilder,
    build_and_export_pipeline,
)

# Configure pure ASCII logger
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("build_metaphysics_dataset")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Metaphysics Fine-Tuning Datasets for HoroConsultant v3.0"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate synthetic/golden ShareGPT and instruction datasets",
    )
    parser.add_argument(
        "--benchmark-file",
        type=str,
        default=str(DEFAULT_BENCHMARK_PATH),
        help="Path to domain benchmark JSON dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATASETS_DIR),
        help="Output directory for generated JSONL datasets",
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=1200,
        help="Target total number of samples to generate (default: 1200)",
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.10,
        help="Validation dataset split ratio (default: 0.10)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip generation and only verify integrity of existing JSONL datasets",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    benchmark_path = Path(args.benchmark_file)
    output_dir = Path(args.output_dir)

    log.info("================================================================================")
    log.info("HoroConsultant Metaphysics Dataset Pipeline (v3.0)")
    log.info("================================================================================")
    log.info(f"[INFO] Benchmark Source : {benchmark_path}")
    log.info(f"[INFO] Output Directory : {output_dir}")
    log.info(f"[INFO] Target Count     : {args.target_count}")
    log.info(f"[INFO] Validation Split : {args.val_split:.0%}")
    log.info("--------------------------------------------------------------------------------")

    builder = MetaphysicsDatasetBuilder(benchmark_path=benchmark_path)

    if args.verify_only:
        train_file = output_dir / "train_sharegpt_v3.jsonl"
        eval_file = output_dir / "eval_sharegpt_v3.jsonl"
        log.info(f"[INFO] Verifying existing dataset at {train_file}...")
        train_res = builder.validate_dataset_integrity(train_file)
        eval_res = builder.validate_dataset_integrity(eval_file)

        log.info(f"[INFO] Train Dataset: {train_res}")
        log.info(f"[INFO] Eval Dataset : {eval_res}")

        if train_res.get("valid") and eval_res.get("valid"):
            log.info("[OK] Dataset verification passed.")
            return 0
        else:
            log.error("[ERROR] Dataset verification failed.")
            return 1

    if not args.generate:
        log.warning("[WARNING] Neither --generate nor --verify-only specified. Use --generate to build datasets.")
        log.info("[INFO] For help: python3 scripts/build_metaphysics_dataset.py --help")
        return 0

    log.info("[INFO] Executing comprehensive dataset synthesis pipeline...")
    result = build_and_export_pipeline(
        benchmark_path=benchmark_path,
        output_dir=output_dir,
        target_count=args.target_count,
        val_split=args.val_split,
    )

    train_val = result["train_validation"]
    eval_val = result["eval_validation"]

    log.info("--------------------------------------------------------------------------------")
    log.info("Pipeline Execution Summary & Quality Assertions:")
    log.info("--------------------------------------------------------------------------------")
    log.info(f"[OK] Total Samples Generated : {result['total_samples']}")
    log.info(f"[OK] Training Split Count    : {result['train_samples']} (Target >= 1000: {'PASSED' if result['train_samples'] >= 1000 else 'FAILED'})")
    log.info(f"[OK] Evaluation Split Count  : {result['eval_samples']} (Target >= 100: {'PASSED' if result['eval_samples'] >= 100 else 'FAILED'})")
    log.info(f"[OK] Disciplines Represented : {train_val['disciplines_covered']}/16 disciplines")
    log.info(f"[OK] Domains Represented     : {train_val['domains_covered']}/6 domains")
    log.info(f"[OK] Chain-of-Thought (CoT)  : {train_val['cot_thought_percentage']}% verified")
    log.info("--------------------------------------------------------------------------------")
    log.info("Exported Artifacts:")
    for key, path_str in result["exported_files"].items():
        log.info(f"  - {key:<18}: {path_str}")
    log.info("================================================================================")
    log.info("[OK] Metaphysics Fine-Tuning Dataset Generation Completed Cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
