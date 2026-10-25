"""
scripts/add_vault_entry.py
==========================
CLI Tool to Add Knowledge & Q&A Entries to Obsidian Vault, FAISS Vector Store, and Supabase DB.

Usage Examples
--------------
1. Add Q&A Entry via Command-line flags:
   python3 scripts/add_vault_entry.py \\
       --question "ดวงชะตาที่ธาตุทองพิฆาตธาตุไม้ มีแนวโน้มการทายผลอย่างไร" \\
       --answer "ตามตำรา子平真詮 ธาตุทองพิฆาตไม้ในดวงชะตาทำให้เกิดการเปลี่ยนแปลงเฉียบพลัน..." \\
       --source "子平真詮"

2. Import a markdown/text file directly into the Obsidian Vault & Vector Store:
   python3 scripts/add_vault_entry.py --file path/to/note.md --source "Obsidian Vault Note"

3. Interactive Mode (prompts user for question & answer):
   python3 scripts/add_vault_entry.py --interactive
"""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.supabase_db import SupabaseDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("add_vault_entry")

VAULT_DIR = ROOT_DIR / "project" / "rag" / "obsidian_vault"
CHAT_LOGS_DIR = VAULT_DIR / "chat_logs"


def add_qa_to_local_vault(question: str, answer: str, source: str = "User Entry") -> Path:
    """Save Q&A entry as a formatted Markdown file in project/rag/obsidian_vault/chat_logs/."""
    CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in question[:30]).strip("_")
    filename = f"entry_{timestamp}_{safe_title}.md"
    file_path = CHAT_LOGS_DIR / filename

    content = f"""---
source: "{source}"
created_at: "{datetime.datetime.now().isoformat()}"
---

## Q: {question}

A: {answer}
"""
    file_path.write_text(content, encoding="utf-8")
    logger.info(f"💾 Saved local Markdown file: {file_path}")
    return file_path


def copy_file_to_vault(file_path: Path, target_dir: Path = VAULT_DIR) -> Path:
    """Copy an existing file into the Obsidian Vault."""
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    dest_path = target_dir / file_path.name
    dest_path.write_bytes(file_path.read_bytes())
    logger.info(f"📂 Copied file to Obsidian Vault: {dest_path}")
    return dest_path


def sync_to_supabase(question: str, answer: str, source: str) -> bool:
    """Upsert Q&A record to Supabase `qa_knowledge_base` table."""
    db = SupabaseDB()
    if not db.is_configured():
        logger.info("ℹ️ Supabase not configured. Skipping Supabase sync.")
        return False

    record = {
        "question": question,
        "answer": answer,
        "source_book": source,
        "is_verified": True,
        "system_prompt": (
            "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ (Computational Metaphysics) "
            "เชี่ยวชาญทั้ง BaZi (四柱命理), การคำนวณ True Solar Time, "
            "และคัมภีร์จีนโบราณ อาทิ 子平真詮, 滴天髓, 窮通寶鑑"
        )
    }
    success = db.upsert("qa_knowledge_base", [record])
    if success:
        logger.info("☁️ Successfully synced entry to Supabase DB `qa_knowledge_base` table!")
    return success


def rebuild_vector_store() -> None:
    """Rebuild local FAISS vector store and update fine-tune dataset."""
    logger.info("⚡ Updating FAISS Vector DB & Fine-Tune JSONL dataset...")
    try:
        from project.rag.ingest_vault import (
            export_finetune_dataset,
            ingest_to_vector_store,
            load_vault,
        )
        VECTOR_STORE_DIR = ROOT_DIR / "project" / "data" / "vector_store"
        DATASETS_DIR = ROOT_DIR / "project" / "rag" / "datasets"

        chunks, qa_pairs = load_vault(VAULT_DIR)
        if chunks:
            ingest_to_vector_store(chunks, VECTOR_STORE_DIR)
        if qa_pairs:
            export_finetune_dataset(qa_pairs, DATASETS_DIR)
        logger.info("🎉 Local FAISS Vector Store & Datasets updated successfully!")
    except Exception as e:
        logger.warning(f"⚠️ Vector store rebuild note: {e}")


def main():
    parser = argparse.ArgumentParser(description="Add Knowledge Entry to HoroConsultant Vault & Vector Store")
    parser.add_argument("-q", "--question", help="Question or prompt text")
    parser.add_argument("-a", "--answer", help="Answer or detailed explanation text")
    parser.add_argument("-s", "--source", default="Manual Entry", help="Source reference / book name")
    parser.add_argument("-f", "--file", type=Path, help="Path to markdown/PDF file to add to Vault")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive prompt mode")
    parser.add_argument("--skip-vector", action="store_true", help="Skip FAISS vector store update")

    args = parser.parse_args()

    # Interactive mode fallback
    if args.interactive or (not args.question and not args.file):
        print("📝 --- Add New Vault Entry ---")
        question = input("Enter Question / Title: ").strip()
        answer = input("Enter Answer / Content: ").strip()
        source = input("Enter Source Reference (default: Manual Entry): ").strip() or "Manual Entry"
        if not question or not answer:
            print("❌ Question and Answer cannot be empty!")
            sys.exit(1)
        args.question = question
        args.answer = answer
        args.source = source

    if args.file:
        copy_file_to_vault(args.file)
    elif args.question and args.answer:
        add_qa_to_local_vault(args.question, args.answer, args.source)
        sync_to_supabase(args.question, args.answer, args.source)

    if not args.skip_vector:
        rebuild_vector_store()

    print("\n✅ Knowledge entry added successfully to HoroConsultant Vault!")


if __name__ == "__main__":
    main()
