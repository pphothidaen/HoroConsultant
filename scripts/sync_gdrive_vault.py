#!/usr/bin/env python3
"""
scripts/sync_gdrive_vault.py
=============================
Automated Google Drive Vault Sync & Ingestion Pipeline.

Monitors configured Google Drive shared folder URLs:
  1. Main Vault Folder 1 : https://drive.google.com/drive/folders/1uxm8knVltHHlGQAlREUBgLfrATlowH2E
  2. Main Vault Folder 2 : https://drive.google.com/drive/folders/1RWY9PS63rCpdFOj7edrnjF9fE44Hhs3I
  3. Original Shared Vault: https://drive.google.com/drive/folders/1ZemhmY8s1Ka5-AsUTXn8PL5WMmQQnKFV
  4. Additional Training Vault: https://drive.google.com/drive/folders/1e8nX-h3cKpcifUv6G2EjuJDey9DBm5b2

Automated Actions:
  - Recursively downloads all files & subfolders from all configured Drive links into project/rag/obsidian_vault/
  - Detects newly added .pdf or .md files
  - Triggers ingestion (PDF text extraction -> nomic-embed-text -> FAISS Vector Store + ShareGPT Fine-Tune JSONL)
  - Saves sync report to project/data/vault_sync_status.json

Usage:
  python scripts/sync_gdrive_vault.py [--force-reindex] [--dry-run]
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("sync_gdrive_vault")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Target Google Drive Folders Configuration
# ---------------------------------------------------------------------------

GDRIVE_FOLDERS = [
    {
        "id": "1uxm8knVltHHlGQAlREUBgLfrATlowH2E",
        "name": "Main Vault Folder 1 (โหราศาสตร์ & คัมภีร์)",
        "url": "https://drive.google.com/drive/folders/1uxm8knVltHHlGQAlREUBgLfrATlowH2E",
        "target_subfolder": "folder_1",
    },
    {
        "id": "1RWY9PS63rCpdFOj7edrnjF9fE44Hhs3I",
        "name": "Main Vault Folder 2 (ดวง & ตำราทำนาย)",
        "url": "https://drive.google.com/drive/folders/1RWY9PS63rCpdFOj7edrnjF9fE44Hhs3I",
        "target_subfolder": "folder_2",
    },
    {
        "id": "1ZemhmY8s1Ka5-AsUTXn8PL5WMmQQnKFV",
        "name": "Original Shared Vault (พิธีกรรม & พระเวท)",
        "url": "https://drive.google.com/drive/folders/1ZemhmY8s1Ka5-AsUTXn8PL5WMmQQnKFV",
        "target_subfolder": "folder_orig",
    },
    {
        "id": "1e8nX-h3cKpcifUv6G2EjuJDey9DBm5b2",
        "name": "Additional Training Vault (คัมภีร์ & ตำราเพิ่มเติม)",
        "url": "https://drive.google.com/drive/folders/1e8nX-h3cKpcifUv6G2EjuJDey9DBm5b2?usp=sharing",
        "target_subfolder": "folder_3",
    },
    {
        "id": "1vNh9IaFbBvXQdAiKVcCz61p59BTFR58E",
        "name": "HoroClip Master Vault & Treatise Summaries",
        "url": "https://drive.google.com/drive/folders/1vNh9IaFbBvXQdAiKVcCz61p59BTFR58E?usp=sharing",
        "target_subfolder": "folder_horoclip",
    },
]

VAULT_DIR   = ROOT / "project" / "rag" / "obsidian_vault"
STATUS_FILE = ROOT / "project" / "data" / "vault_sync_status.json"


# ---------------------------------------------------------------------------
# Inventory Helpers
# ---------------------------------------------------------------------------

def get_vault_inventory() -> set[str]:
    """Return relative paths of all .pdf and .md files in the vault."""
    if not VAULT_DIR.exists():
        return set()
    files = set()
    for ext in ["*.pdf", "*.md", "*.txt"]:
        for p in VAULT_DIR.rglob(ext):
            files.add(str(p.relative_to(VAULT_DIR)))
    return files


def download_gdrive_folder(folder_info: dict[str, str]) -> bool:
    """Download a single Google Drive folder via gdown."""
    target = VAULT_DIR / folder_info["target_subfolder"]
    target.mkdir(parents=True, exist_ok=True)

    log.info(f"📥 Syncing: {folder_info['name']}")
    log.info(f"   URL: {folder_info['url']}")
    log.info(f"   Target: {target}")

    cmd = [
        sys.executable, "-m", "gdown",
        "--folder", folder_info["url"],
        "-O", str(target),
        "--remaining-ok",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if res.returncode == 0 or "remaining-ok" in res.stderr:
            log.info(f"✅ Completed sync for {folder_info['name']}")
            return True
        else:
            log.warning(f"⚠️ Partial sync for {folder_info['name']}: {res.stderr[-200:]}")
            return True
    except subprocess.TimeoutExpired:
        log.warning(f"⏳ Download timed out for {folder_info['name']} (resuming on next sync)")
        return False
    except Exception as e:
        log.error(f"❌ Error downloading {folder_info['name']}: {e}")
        return False


# ---------------------------------------------------------------------------
# Main Sync Pipeline
# ---------------------------------------------------------------------------

def sync_all(force_reindex: bool = False, dry_run: bool = False) -> dict[str, Any]:
    log.info("=" * 65)
    log.info("  Google Drive Vault Sync & Automated Ingestion Pipeline")
    log.info("=" * 65)

    # 1. Inventory before sync
    before_files = get_vault_inventory()
    log.info(f"Inventory before sync: {len(before_files)} files")

    if dry_run:
        log.info("🔎 Dry-run mode — displaying configured target Google Drive folders:")
        for f in GDRIVE_FOLDERS:
            log.info(f"  • [{f['id']}] {f['name']} -> {f['url']}")
        return {"status": "dry_run", "before_count": len(before_files)}

    # 2. Download from all configured Google Drive links
    download_results = []
    for f_info in GDRIVE_FOLDERS:
        ok = download_gdrive_folder(f_info)
        download_results.append({"folder": f_info["name"], "success": ok})

    # 3. Inventory after sync
    after_files = get_vault_inventory()
    new_files   = after_files - before_files
    log.info(f"Inventory after sync: {len(after_files)} files ({len(new_files)} new files detected)")

    if new_files:
        log.info("\n🆕 New files detected:")
        for nf in sorted(list(new_files))[:15]:
            log.info(f"   + {nf}")
        if len(new_files) > 15:
            log.info(f"   ... and {len(new_files) - 15} more")

    # 4. Trigger Ingestion if new files arrived or force_reindex
    ingested = False
    if new_files or force_reindex or len(after_files) > 0:
        log.info("\n⚙️ Triggering Vault Ingestion (PDF extraction -> nomic-embed -> FAISS + JSONL)…")
        cmd_ingest = [
            sys.executable, "project/rag/ingest_vault.py",
            "--export-finetune"
        ]
        try:
            res = subprocess.run(cmd_ingest, check=True, cwd=str(ROOT))
            ingested = True
            log.info("✅ Vault ingestion completed successfully!")
        except Exception as e:
            log.error(f"❌ Ingestion failed: {e}")

    # 5. Build Sync Status Report
    pdf_count = len(list(VAULT_DIR.rglob("*.pdf")))
    md_count  = len(list(VAULT_DIR.rglob("*.md")))

    # Read vector count if available
    vector_count = 0
    meta_path = ROOT / "project" / "data" / "vector_store" / "metadata.json"
    if meta_path.exists():
        try:
            mdata = json.loads(meta_path.read_text(encoding="utf-8"))
            vector_count = len(mdata.get("chunks", []))
        except Exception:
            pass

    sync_summary = {
        "last_sync_timestamp": datetime.now().isoformat(),
        "total_files_in_vault": len(after_files),
        "pdf_count": pdf_count,
        "md_count": md_count,
        "indexed_vectors_count": vector_count,
        "new_files_added_this_run": len(new_files),
        "gdrive_folders_configured": GDRIVE_FOLDERS,
        "download_status": download_results,
        "ingestion_triggered": ingested,
    }

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(sync_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"\n📊 Status report saved -> {STATUS_FILE}")

    print("\n" + "=" * 65)
    print("  SUMMARY REPORT")
    print("=" * 65)
    print(f"  Total Files in Vault : {len(after_files)} ({pdf_count} PDFs, {md_count} MDs)")
    print(f"  FAISS Vectors Count  : {vector_count}")
    print(f"  New Files Added      : {len(new_files)}")
    print(f"  Folders Monitored    : {len(GDRIVE_FOLDERS)}")
    print("=" * 65 + "\n")

    return sync_summary


def check_and_run_if_missed() -> bool:
    """
    Check if today's sync has been performed.
    If the system was off at midnight or today's sync hasn't run yet,
    triggers sync_all() immediately.
    Returns True if sync was executed, False if already up-to-date.
    """
    enabled = os.getenv("AUTO_SYNC_ENABLED", "true").lower() in ("true", "1", "yes")
    if not enabled:
        log.info("ℹ️ Auto-sync is disabled in .env (AUTO_SYNC_ENABLED=false)")
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    last_sync_date = ""

    if STATUS_FILE.exists():
        try:
            status_data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            ts = status_data.get("last_sync_timestamp", "")
            if ts:
                last_sync_date = ts.split("T")[0]
        except Exception as e:
            log.warning(f"Failed to read last sync status: {e}")

    log.info(f"🔍 Auto-sync check: Today={today_str} | Last Sync Date={last_sync_date or 'Never'}")

    if last_sync_date != today_str:
        log.info("⏰ System missed today's midnight sync or startup check -> Running sync NOW!")
        sync_all()
        return True

    log.info("✅ Today's sync has already been executed.")
    return False


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Google Drive Vault Sync & Ingestion Pipeline")
    p.add_argument("--force-reindex", action="store_true", help="Force full re-indexing")
    p.add_argument("--dry-run",       action="store_true", help="List targets without downloading")
    p.add_argument("--catchup",       action="store_true", help="Run sync only if missed today")
    args = p.parse_args()

    if args.catchup:
        check_and_run_if_missed()
    else:
        sync_all(force_reindex=args.force_reindex, dry_run=args.dry_run)

