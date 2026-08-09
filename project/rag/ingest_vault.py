"""
project/rag/ingest_vault.py
============================
NotebookLM / Obsidian Vault → Vector Store + Fine-Tune Dataset Pipeline.

Reads .md files from project/rag/obsidian_vault/, chunks them,
embeds via local nomic-embed-text (Ollama), and saves to FAISS.
Also exports Q&A chat logs as JSONL for MLX fine-tuning.

Usage
-----
    # Ingest vault → RAG vector store
    python project/rag/ingest_vault.py --input project/rag/obsidian_vault/

    # Also export fine-tune JSONL
    python project/rag/ingest_vault.py --input project/rag/obsidian_vault/ --export-finetune

    # Specify custom output paths
    python project/rag/ingest_vault.py \\
        --input  project/rag/obsidian_vault/ \\
        --vector-out project/data/vector_store/ \\
        --finetune-out project/rag/datasets/

Export format from NotebookLM
------------------------------
    project/rag/obsidian_vault/
        ├── *.md              ← Sources & Notes (documents)
        └── chat_logs/
            └── *.md          ← Chat history Q&A pairs
"""

from __future__ import annotations

import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ingest_vault")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VAULT_DIR        = ROOT / "project" / "rag" / "obsidian_vault"
VECTOR_STORE_DIR = ROOT / "project" / "data" / "vector_store"
DATASETS_DIR     = ROOT / "project" / "rag" / "datasets"
CHUNK_SIZE       = 400   # characters per chunk
CHUNK_OVERLAP    = 80

SYSTEM_PROMPT = (
    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ (Computational Metaphysics) "
    "เชี่ยวชาญทั้ง BaZi (四柱命理), การคำนวณ True Solar Time, "
    "และคัมภีร์จีนโบราณ อาทิ 子平真詮, 滴天髓, 窮通寶鑑 "
    "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราที่ผ่านการพิสูจน์ "
    "และระบุเสมอว่าใช้ True Solar Time ในการคำนวณ"
)


# ---------------------------------------------------------------------------
# Markdown Chunker
# ---------------------------------------------------------------------------

def chunk_markdown(text: str, source: str, chunk_size: int = CHUNK_SIZE) -> list[dict[str, str]]:
    """
    Split markdown into overlapping chunks.
    Respects heading boundaries where possible.
    """
    # Remove frontmatter
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    # Split by headings first
    sections = re.split(r"\n(?=#{1,3} )", text)

    chunks: list[dict[str, str]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract heading as context label
        heading_match = re.match(r"^(#{1,3})\s+(.+)", section)
        heading = heading_match.group(2) if heading_match else ""

        # Chunk by size with overlap
        words = section.split()
        buf   = []
        buf_len = 0

        for word in words:
            buf.append(word)
            buf_len += len(word) + 1
            if buf_len >= chunk_size:
                chunk_text = " ".join(buf).strip()
                if len(chunk_text) > 50:
                    chunks.append({
                        "text":    chunk_text,
                        "source":  source,
                        "heading": heading,
                        "chunk":   len(chunks),
                    })
                # Overlap: keep last CHUNK_OVERLAP chars worth of words
                overlap_words = []
                overlap_len   = 0
                for w in reversed(buf):
                    if overlap_len + len(w) + 1 > CHUNK_OVERLAP:
                        break
                    overlap_words.insert(0, w)
                    overlap_len += len(w) + 1
                buf     = overlap_words
                buf_len = overlap_len

        # Flush remaining
        if buf:
            chunk_text = " ".join(buf).strip()
            if len(chunk_text) > 50:
                chunks.append({
                    "text":    chunk_text,
                    "source":  source,
                    "heading": heading,
                    "chunk":   len(chunks),
                })

    return chunks


# ---------------------------------------------------------------------------
# Q&A Pair Extractor (for Fine-Tuning)
# ---------------------------------------------------------------------------

def extract_qa_pairs(md_text: str, source: str) -> list[dict[str, Any]]:
    """
    Extract Q&A pairs from NotebookLM chat log markdown.

    Expected format:
        ## Q: <question>
        A: <answer>

    Or alternating **User:**/**Assistant:** blocks.
    """
    pairs: list[dict[str, Any]] = []

    # Pattern 1: ## Q: ... / A: ...
    pattern1 = re.findall(
        r"#{1,3}\s*[Qq][:：]\s*(.+?)\n+[Aa][:：]\s*(.+?)(?=\n#{1,3}|\Z)",
        md_text, re.DOTALL
    )
    for q, a in pattern1:
        q, a = q.strip(), a.strip()
        if len(q) > 10 and len(a) > 20:
            pairs.append({"question": q, "answer": a, "source": source})

    # Pattern 2: **User:** / **Assistant:** blocks
    pattern2 = re.findall(
        r"\*\*(?:User|คำถาม)[:：]?\*\*\s*(.+?)\n+\*\*(?:Assistant|คำตอบ)[:：]?\*\*\s*(.+?)(?=\n\*\*(?:User|คำถาม)|\Z)",
        md_text, re.DOTALL
    )
    for q, a in pattern2:
        q, a = q.strip(), a.strip()
        if len(q) > 10 and len(a) > 20:
            pairs.append({"question": q, "answer": a, "source": source})

    # Pattern 3: Numbered Q&A
    pattern3 = re.findall(
        r"\d+\.\s*\*\*(.+?)\*\*\s*\n+(.+?)(?=\n\d+\.|\Z)",
        md_text, re.DOTALL
    )
    for q, a in pattern3:
        q, a = q.strip(), a.strip()
        if len(q) > 10 and len(a) > 20:
            pairs.append({"question": q, "answer": a, "source": source})

    return pairs


def qa_to_sharegpt(qa: dict[str, Any]) -> dict[str, Any]:
    """Convert a Q&A pair to ShareGPT fine-tune format."""
    return {
        "conversations": [
            {"role": "system",    "value": SYSTEM_PROMPT},
            {"role": "human",     "value": qa["question"]},
            {"role": "assistant", "value": qa["answer"]},
        ]
    }


# ---------------------------------------------------------------------------
# Vault Loader
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract clean text from a PDF file using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        text_parts = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                text_parts.append(f"--- Page {i+1} ---\n" + txt.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        log.warning(f"  Failed to parse PDF {pdf_path.name}: {e}")
        return ""


def load_vault(vault_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """
    Scan vault_dir for .md and .pdf files.
    Returns (chunks_for_rag, qa_pairs_for_finetune).
    """
    if not vault_dir.exists():
        log.warning(f"Vault directory not found: {vault_dir}")
        log.info("Create it and place your NotebookLM / PDF files there:")
        log.info(f"  mkdir -p {vault_dir}")
        return [], []

    all_chunks: list[dict[str, str]] = []
    all_qa:     list[dict[str, Any]] = []

    # Find both .md and .pdf files
    md_files  = list(vault_dir.rglob("*.md"))
    pdf_files = list(vault_dir.rglob("*.pdf"))
    log.info(f"Found {len(md_files)} .md files and {len(pdf_files)} .pdf files in {vault_dir}")

    # Process .md files
    for md_file in sorted(md_files):
        text   = md_file.read_text(encoding="utf-8")
        source = md_file.stem.replace("-", " ").replace("_", " ").title()
        rel    = md_file.relative_to(vault_dir)

        if "chat" in str(rel).lower() or "log" in str(rel).lower():
            qa_pairs = extract_qa_pairs(text, source)
            all_qa.extend(qa_pairs)
            log.info(f"  {rel}: {len(qa_pairs)} Q&A pairs extracted")
        else:
            chunks = chunk_markdown(text, source)
            all_chunks.extend(chunks)
            log.info(f"  {rel}: {len(chunks)} chunks → RAG")

    # Process .pdf files
    for pdf_file in sorted(pdf_files):
        rel    = pdf_file.relative_to(vault_dir)
        source = pdf_file.stem.replace("-", " ").replace("_", " ").title()
        log.info(f"  Extracting PDF text: {rel}…")
        text   = extract_text_from_pdf(pdf_file)
        if text.strip():
            chunks = chunk_markdown(text, source)
            all_chunks.extend(chunks)
            log.info(f"  {rel}: {len(chunks)} chunks → RAG")
        else:
            log.warning(f"  {rel}: No text extracted (scanned/image PDF)")

    return all_chunks, all_qa


# ---------------------------------------------------------------------------
# RAG Ingestion
# ---------------------------------------------------------------------------

def ingest_to_vector_store(
    chunks:     list[dict[str, str]],
    output_dir: Path,
) -> None:
    """Build and save FAISS vector store from vault chunks."""
    from project.rag.vector_store import VectorStore, load_all_chunks

    # Merge vault chunks with existing raw_texts chunks
    existing = load_all_chunks()
    merged   = existing + chunks
    log.info(f"Total chunks (existing + vault): {len(existing)} + {len(chunks)} = {len(merged)}")

    vs = VectorStore().build(merged)
    vs.save()
    log.info(f"Vector store saved → {output_dir}")


# ---------------------------------------------------------------------------
# Fine-Tune Dataset Export
# ---------------------------------------------------------------------------

def export_finetune_dataset(
    qa_pairs:   list[dict[str, Any]],
    output_dir: Path,
    val_split:  float = 0.10,
    seed:       int   = 42,
) -> None:
    """Save Q&A pairs as ShareGPT JSONL for MLX fine-tuning."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not qa_pairs:
        log.warning("No Q&A pairs to export — place chat logs in vault/chat_logs/*.md")
        # Still create empty files so scripts don't break
        (output_dir / "train.jsonl").write_text("", encoding="utf-8")
        (output_dir / "valid.jsonl").write_text("", encoding="utf-8")
        return

    entries = [qa_to_sharegpt(qa) for qa in qa_pairs]
    random.seed(seed)
    random.shuffle(entries)

    val_n    = max(1, int(len(entries) * val_split))
    val_set  = entries[:val_n]
    trn_set  = entries[val_n:]

    for name, dataset in [("train", trn_set), ("valid", val_set)]:
        out = output_dir / f"{name}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(entry, ensure_ascii=False) + "\n" for entry in dataset)
        log.info(f"Saved {name}: {len(dataset)} entries → {out}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="NotebookLM Vault → RAG + Fine-Tune Pipeline")
    parser.add_argument("--input",          default=str(VAULT_DIR),        help="Vault directory")
    parser.add_argument("--vector-out",     default=str(VECTOR_STORE_DIR), help="FAISS output dir")
    parser.add_argument("--finetune-out",   default=str(DATASETS_DIR),     help="JSONL output dir")
    parser.add_argument("--export-finetune", action="store_true",          help="Also export Q&A JSONL")
    parser.add_argument("--val-split",      default=0.10, type=float)
    args = parser.parse_args()

    vault_dir  = Path(args.input)
    vector_dir = Path(args.vector_out)
    ft_dir     = Path(args.finetune_out)

    log.info("=" * 60)
    log.info("  NotebookLM Vault Ingestion Pipeline")
    log.info("=" * 60)
    log.info(f"  Vault     : {vault_dir}")
    log.info(f"  Vector DB : {vector_dir}")
    log.info(f"  Datasets  : {ft_dir}")
    log.info("=" * 60)

    # 1. Load vault
    chunks, qa_pairs = load_vault(vault_dir)

    # 2. Build RAG
    if chunks:
        log.info(f"\n📚 Ingesting {len(chunks)} chunks → FAISS vector store…")
        ingest_to_vector_store(chunks, vector_dir)
    else:
        log.warning("No document chunks found — skipping vector store update")

    # 3. Fine-tune dataset
    if args.export_finetune:
        log.info(f"\n🎓 Exporting {len(qa_pairs)} Q&A pairs → {ft_dir}")
        export_finetune_dataset(qa_pairs, ft_dir, val_split=args.val_split)

    log.info("\n✅ Ingestion complete!")
    log.info(f"   RAG chunks  : {len(chunks)}")
    log.info(f"   Q&A pairs   : {len(qa_pairs)}")
    log.info("\nNext steps:")
    log.info("  1. Verify RAG: python scripts/build_vector_store.py")
    if args.export_finetune:
        log.info("  2. Fine-tune : python scripts/run_mlx_finetune.py --dataset project/rag/datasets/")


if __name__ == "__main__":
    main()
