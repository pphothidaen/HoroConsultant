#!/usr/bin/env python3
"""
scripts/build_vector_store.py
==============================
One-shot script to build and save the RAG vector store from classical texts.

Usage
-----
    python scripts/build_vector_store.py [--force]

With GOOGLE_AI_STUDIO_API_KEY set → uses text-embedding-004 + FAISS
Without API key (or FAISS not installed) → uses keyword fallback index
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from project.rag.vector_store import VectorStore, load_all_chunks

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Rebuild even if index exists")
    args = p.parse_args()

    store_dir = root / "project" / "data" / "vector_store"
    if (store_dir / "metadata.json").exists() and not args.force:
        print("ℹ️  Index already exists. Use --force to rebuild.")
        return

    chunks = load_all_chunks()
    print(f"Loaded {len(chunks)} chunks from raw texts")
    vs = VectorStore().build(chunks).save()
    print(f"\n✅ Vector store built in mode: {vs._mode}")
    print(f"   Chunks indexed: {len(vs._chunks)}")
    print(f"   Directory: {store_dir}")

    # Smoke test
    result = vs.search("甲木 spring month pillar Day Master strength")
    print(f"\n🔍 Smoke test query returned {result['total_results']} results:")
    for r in result["results"]:
        print(f"  [{r['score']:.3f}] {r['source']}: {r['passage'][:60]}…")

if __name__ == "__main__":
    main()
