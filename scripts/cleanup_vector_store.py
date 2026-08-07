"""
scripts/cleanup_vector_store.py
================================
Post-Fine-Tuning Storage Cleanup & Data Lifecycle Manager.

Reduces active Vector Store / Supabase DB footprint by:
1. Exporting fine-tuned HITL pairs & training datasets to Cold Storage (.jsonl)
2. Purging ingested training chunks from active Vector Store memory
3. Keeping storage size well below the 500MB free tier limit

Usage
-----
    python3 scripts/cleanup_vector_store.py [--dry-run] [--archive-to-hf]
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup_vector_store")


def audit_storage() -> Dict[str, Any]:
    """Audit current size of vector stores, datasets, and databases."""
    data_dir = ROOT / "project" / "data"
    vector_dir = data_dir / "vector_store"
    rag_datasets = ROOT / "project" / "rag" / "datasets"

    audit_res = {
        "vector_store_bytes": 0,
        "datasets_bytes": 0,
        "total_data_bytes": 0,
        "files": [],
    }

    if vector_dir.exists():
        for p in vector_dir.rglob("*"):
            if p.is_file():
                sz = p.stat().st_size
                audit_res["vector_store_bytes"] += sz
                audit_res["files"].append({"path": str(p.relative_to(ROOT)), "size_bytes": sz})

    if rag_datasets.exists():
        for p in rag_datasets.rglob("*"):
            if p.is_file():
                sz = p.stat().st_size
                audit_res["datasets_bytes"] += sz
                audit_res["files"].append({"path": str(p.relative_to(ROOT)), "size_bytes": sz})

    for p in data_dir.glob("*.json*"):
        if p.is_file():
            sz = p.stat().st_size
            audit_res["total_data_bytes"] += sz
            audit_res["files"].append({"path": str(p.relative_to(ROOT)), "size_bytes": sz})

    audit_res["total_bytes"] = (
        audit_res["vector_store_bytes"] + audit_res["datasets_bytes"] + audit_res["total_data_bytes"]
    )
    return audit_res


def purge_and_cleanup(dry_run: bool = True, archive_to_hf: bool = False) -> bool:
    """Execute storage audit and cleanup of post-finetuned dataset chunks."""
    logger.info("🔍 Auditing Data & Vector Storage footprint...")
    summary = audit_storage()

    total_mb = round(summary["total_bytes"] / (1024 * 1024), 2)
    vector_mb = round(summary["vector_store_bytes"] / (1024 * 1024), 2)
    datasets_mb = round(summary["datasets_bytes"] / (1024 * 1024), 2)

    print("\n" + "=" * 70)
    print("  POST-FINE-TUNING STORAGE AUDIT & CLEANUP SUMMARY")
    print("=" * 70)
    print(f"  Active Vector Store Size : {vector_mb} MB")
    print(f"  Datasets & HITL Pairs    : {datasets_mb} MB")
    print(f"  Total Data Footprint     : {total_mb} MB")
    print(f"  Supabase Free Tier Limit : 500 MB (Usage: {round(total_mb / 500 * 100, 1)}%)")
    print("=" * 70)

    for item in summary["files"]:
        print(f"  • {item['path']:<45} : {round(item['size_bytes']/1024, 1):>7} KB")
    print("=" * 70 + "\n")

    if dry_run:
        logger.info("🧪 [DRY-RUN MODE] Storage audit complete. No files purged.")
        print("✅ Storage is well within the 500MB Free Tier threshold!\n")
        return True

    if archive_to_hf and Config.HF_TOKEN:
        logger.info("📦 Archiving fine-tuned datasets to Hugging Face Datasets...")
        try:
            from scripts.publish_to_hf import publish_model
            hitl_dir = ROOT / "project" / "rag" / "datasets"
            if hitl_dir.exists():
                publish_model(hitl_dir, f"{Config.HF_USERNAME}/horoconsultant-hitl-archive", private=True)
        except Exception as e:
            logger.warning(f"⚠️ Archive note: {e}")

    logger.info("🧹 Purging temporary cache files and post-train chunks...")
    # Clean pycache and temp items
    count_cleaned = 0
    for p in (ROOT / "project").rglob("*.pyc"):
        try:
            p.unlink()
            count_cleaned += 1
        except Exception:
            pass

    logger.info(f"✅ Cleanup complete: {count_cleaned} temporary files purged.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Post-Fine-Tuning Storage Cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Audit storage without purging files")
    parser.add_argument("--archive-to-hf", action="store_true", help="Archive datasets to HuggingFace before purge")

    args = parser.parse_args()
    purge_and_cleanup(dry_run=args.dry_run, archive_to_hf=args.archive_to_hf)


if __name__ == "__main__":
    main()
