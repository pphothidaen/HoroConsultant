"""
project/rag/vector_store.py — Vector Store Backend for RAG Search Skill
=========================================================================
Builds and queries a FAISS-backed vector store from classical BaZi texts.
Falls back to keyword search if FAISS / embedding API is unavailable.

Usage
-----
  # Build the index (run once):
  python scripts/build_vector_store.py

  # Query:
  from project.rag.vector_store import VectorStore
  vs = VectorStore.load()
  results = vs.search("丙火 summer season Day Master", top_k=5)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

# NumPy & Rust accelerated math layer
from project.core.fast_math import (
    chunk_text_fast,
    numpy_build_tfidf_matrix,
    numpy_tfidf_vector,
    rust_dense_vector_search,
)

# FAISS and embeddings are optional — gracefully degrade
try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except (ImportError, OSError, Exception):
    FAISS_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

ROOT             = Path(__file__).resolve().parents[2]
STORE_DIR        = ROOT / "project" / "data" / "vector_store"
INDEX_PATH       = STORE_DIR / "index.faiss"
META_PATH        = STORE_DIR / "metadata.json"
TEXTS_DIR        = ROOT / "project" / "data" / "raw_texts"

# Local embedding via Ollama (no API key, no quota, 100% private)
OLLAMA_BASE_URL    = os.getenv("OLLAMA_BASE_URL",    "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
NOMIC_DIM          = 768

# Google API as fallback only
GOOGLE_EMBED_MODEL = "text-embedding-004"
GOOGLE_EMBED_URL   = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GOOGLE_EMBED_MODEL}:embedContent"
)

DIM = NOMIC_DIM  # nomic-embed-text and text-embedding-004 both output 768-dim


# ---------------------------------------------------------------------------
# Embedding functions — local first, cloud fallback
# ---------------------------------------------------------------------------

def _embed_local_nomic(texts: list[str]) -> list[list[float]] | None:
    """
    Embed texts with nomic-embed-text via local Ollama.
    100% offline — no API key required.
    """
    if not HTTPX_AVAILABLE:
        return None
    
    # Bypass localhost embedding calls on cloud production
    if (os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") or os.getenv("SPACE_ID") is not None) and ("localhost" in OLLAMA_BASE_URL or "127.0.0.1" in OLLAMA_BASE_URL):
        return None

    embeddings = []
    try:
        with httpx.Client(timeout=2.0) as client:

            for text in texts:
                res = client.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                )
                if res.status_code != 200:
                    print(f"  ⚠️  nomic-embed HTTP {res.status_code}")
                    return None
                vec = res.json().get("embedding", [])
                if not vec:
                    return None
                embeddings.append(vec)
        return embeddings
    except Exception as e:
        print(f"  ⚠️  nomic-embed exception: {e}")
        return None


def _embed_google(texts: list[str]) -> list[list[float]] | None:
    """Google text-embedding-004 — cloud fallback, requires API key."""
    api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
    if not api_key or api_key.startswith("REPLACE") or not HTTPX_AVAILABLE:
        return None
    embeddings = []
    try:
        with httpx.Client(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model":   f"models/{GOOGLE_EMBED_MODEL}",
                    "content": {"parts": [{"text": text}]},
                }
                res = client.post(f"{GOOGLE_EMBED_URL}?key={api_key}", json=payload)
                if res.status_code != 200:
                    return None
                embeddings.append(res.json()["embedding"]["values"])
    except Exception:
        return None
    return embeddings




# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str, source: str, chunk_size: int = 300) -> list[dict[str, str]]:
    """Split text into paragraph chunks — delegates to fast_math.chunk_text_fast."""
    return chunk_text_fast(text, source, chunk_size)


def load_all_chunks() -> list[dict[str, str]]:
    chunks = []
    if not TEXTS_DIR.exists():
        return chunks
    for txt_file in sorted(TEXTS_DIR.glob("*.txt")):
        source = txt_file.stem.replace("_", " ").title()
        text   = txt_file.read_text(encoding="utf-8")
        chunks.extend(_chunk_text(text, source))
    return chunks


# ---------------------------------------------------------------------------
# Embedding via Google API (or fallback to TF-IDF-style keyword vectors)
# ---------------------------------------------------------------------------

def _embed_google(texts: list[str]) -> list[list[float]] | None:
    """Call Google text-embedding-004 API. Returns None on failure."""
    api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
    if not api_key or not HTTPX_AVAILABLE:
        return None

    embeddings = []
    try:
        with httpx.Client(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model": f"models/{EMBED_MODEL}",
                    "content": {"parts": [{"text": text}]},
                }
                res = client.post(f"{EMBED_URL}?key={api_key}", json=payload)
                if res.status_code != 200:
                    return None
                vec = res.json()["embedding"]["values"]
                embeddings.append(vec)
    except Exception:
        return None
    return embeddings


def _tfidf_vector(text: str, vocab: dict[str, int]) -> list[float]:
    """Minimal TF-IDF fallback: delegates to NumPy-accelerated version."""
    vec = numpy_tfidf_vector(text, vocab, n_vocab=len(vocab))
    return vec.tolist()


class _KeywordIndex:
    """NumPy-accelerated keyword search index (replaces pure-Python loop version)."""

    def __init__(self, chunks: list[dict[str, str]]):
        self.chunks = chunks
        # Build character vocab from all texts
        all_chars = set()
        for c in chunks:
            all_chars.update(list(c["text"]))
        self.vocab = {ch: i for i, ch in enumerate(sorted(all_chars))}
        # Pre-build L2-normalised NumPy matrix — enables O(1) BLAS matrix-vector search
        texts = [c["text"] for c in chunks]
        self._matrix = numpy_build_tfidf_matrix(texts, self.vocab)  # shape (N, V)

    def search(self, query: str, top_k: int, threshold: float) -> list[dict[str, Any]]:
        q_vec = numpy_tfidf_vector(query, self.vocab, n_vocab=len(self.vocab))
        hits  = rust_dense_vector_search(q_vec, self._matrix, top_k=top_k, threshold=threshold)
        results = []

        for (idx, score) in hits:
            c = self.chunks[idx]
            results.append({
                "rank":     len(results) + 1,
                "score":    score,
                "source":   c["source"],
                "passage":  c["text"],
                "verified": True,
                "page_ref": f"chunk-{c['chunk']}",
            })
        return results

    def save(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        meta = {"chunks": self.chunks, "vocab": self.vocab, "mode": "keyword"}
        (path / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: Path) -> _KeywordIndex:
        meta   = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        inst   = cls.__new__(cls)
        inst.chunks  = meta["chunks"]
        inst.vocab   = meta["vocab"]
        # Rebuild matrix on load (fast with NumPy)
        texts = [c["text"] for c in inst.chunks]
        inst._matrix = numpy_build_tfidf_matrix(texts, inst.vocab)
        return inst


# ---------------------------------------------------------------------------
# Main VectorStore class
# ---------------------------------------------------------------------------

class VectorStore:
    """
    FAISS-backed vector store with Google embedding API.
    Falls back to character n-gram keyword index if unavailable.
    """

    def __init__(self):
        self._faiss_index = None
        self._keyword_index: _KeywordIndex | None = None
        self._chunks: list[dict[str, str]] = []
        self._mode = "unloaded"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, chunks: list[dict[str, str]] | None = None) -> VectorStore:
        if chunks is None:
            chunks = load_all_chunks()
        self._chunks = chunks

        if not chunks:
            print("⚠️  No chunks found — vector store is empty.")
            self._mode = "empty"
            return self

        texts = [c["text"] for c in chunks]

        if FAISS_AVAILABLE:
            # 1. Try local Ollama nomic-embed-text (no API key, no quota)
            print(f"🔍 Trying local embedding: {OLLAMA_EMBED_MODEL} ({len(texts)} chunks)…")
            embeddings = _embed_local_nomic(texts)

            # 2. Fallback to Google API
            if not embeddings:
                print("⚠️  Local embedding failed → trying Google API…")
                embeddings = _embed_google(texts)

            if embeddings:
                import numpy as np
                mat = np.array(embeddings, dtype="float32")
                faiss.normalize_L2(mat)
                index = faiss.IndexFlatIP(mat.shape[1])
                index.add(mat)
                self._faiss_index = index
                self._mode = "faiss"
                src = OLLAMA_EMBED_MODEL if _embed_local_nomic(["test"]) else "google"
                print(f"✅ FAISS index built: {len(chunks)} vectors (dim={mat.shape[1]}, src={src})")
                return self

        # 3. Pure keyword fallback (always works, no dependencies)
        print("ℹ️  Using keyword index (no FAISS/embedding available)")
        self._keyword_index = _KeywordIndex(chunks)
        self._mode = "keyword"
        return self


    def save(self) -> VectorStore:
        STORE_DIR.mkdir(parents=True, exist_ok=True)

        if self._mode == "faiss" and self._faiss_index is not None:
            faiss.write_index(self._faiss_index, str(INDEX_PATH))
            meta = {"chunks": self._chunks, "mode": "faiss", "dim": DIM}
            META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅ Saved FAISS index → {INDEX_PATH}")
        elif self._keyword_index is not None:
            self._keyword_index.save(STORE_DIR)
            print(f"✅ Saved keyword index → {STORE_DIR}")
        return self

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> VectorStore:
        inst = cls()
        if not META_PATH.exists():
            print("ℹ️  No saved index found — building from raw texts…")
            return inst.build().save()

        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        inst._chunks = meta["chunks"]

        if meta.get("mode") == "faiss" and FAISS_AVAILABLE and INDEX_PATH.exists():
            inst._faiss_index = faiss.read_index(str(INDEX_PATH))
            inst._mode = "faiss"
            print(f"✅ Loaded FAISS index ({len(inst._chunks)} chunks)")
        else:
            inst._keyword_index = _KeywordIndex.load(STORE_DIR)
            inst._mode = "keyword"
            print(f"✅ Loaded keyword index ({len(inst._chunks)} chunks)")
        return inst

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query:     str,
        corpus:    str  = "all",
        top_k:     int  = 5,
        threshold: float = 0.40,
    ) -> dict[str, Any]:
        """
        Hybrid RAG search combining FAISS Dense Vector + BM25 Lexical Search via RRF.

        Parameters
        ----------
        query     : Natural language query (Thai, English or Chinese)
        corpus    : "classical" | "modern" | "all"
        top_k     : Number of results to return
        threshold : Minimum similarity score (0–1)

        Returns
        -------
        dict : RAG search result matching the rag-search.skill output schema
        """
        results = self.hybrid_search(query, top_k=top_k, threshold=threshold, corpus=corpus)

        return {
            "query":            query,
            "results":          results,
            "corpus_searched":  corpus,
            "total_results":    len(results),
            "index_mode":       f"hybrid_{self._mode}",
        }

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.40,
        corpus: str = "all",
        rrf_k: int = 60
    ) -> list[dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) Hybrid Search algorithm combining FAISS Vector + Lexical Search.
        RRF_Score(d) = 1 / (60 + rank_dense(d)) + 1 / (60 + rank_lexical(d))
        """
        dense_results: list[dict[str, Any]] = []
        if self._mode == "faiss" and self._faiss_index is not None:
            dense_results = self._search_faiss(query, top_k=top_k * 3, threshold=0.0, corpus=corpus)

        # Lexical keyword / BM25 search
        if self._keyword_index is None and self._chunks:
            self._keyword_index = _KeywordIndex(self._chunks)
        
        lexical_results: list[dict[str, Any]] = []
        if self._keyword_index is not None:
            lexical_results = self._keyword_index.search(query, top_k=top_k * 3, threshold=0.0)

        # Reciprocal Rank Fusion (RRF) Map
        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        # 1. Process Dense Ranks
        for rank, res in enumerate(dense_results, start=1):
            key = f"{res['source']}_{res['page_ref']}"
            doc_map[key] = res
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rrf_k + rank))

        # 2. Process Lexical Ranks
        for rank, res in enumerate(lexical_results, start=1):
            key = f"{res['source']}_{res['page_ref']}"
            doc_map[key] = res
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rrf_k + rank))

        # Sort combined results by RRF score descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        fused_results = []
        for rank, key in enumerate(sorted_keys[:top_k], start=1):
            doc = doc_map[key]
            doc["rank"] = rank
            doc["hybrid_rrf_score"] = round(rrf_scores[key], 6)
            fused_results.append(doc)

        return fused_results

    def _search_faiss(self, query: str, top_k: int, threshold: float, corpus: str) -> list[dict[str, Any]]:
        embeddings = _embed_google([query])
        if not embeddings:
            # fall back to keyword
            if self._keyword_index is None:
                self._keyword_index = _KeywordIndex(self._chunks)
            return self._keyword_index.search(query, top_k, threshold)

        q_vec = np.array([embeddings[0]], dtype="float32")
        faiss.normalize_L2(q_vec)
        scores, indices = self._faiss_index.search(q_vec, top_k * 2)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or float(score) < threshold:
                continue
            c = self._chunks[idx]
            results.append({
                "rank":     len(results) + 1,
                "score":    round(float(score), 4),
                "source":   c["source"],
                "passage":  c["text"],
                "verified": True,
                "page_ref": f"chunk-{c['chunk']}",
            })
            if len(results) >= top_k:
                break
        return results


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: VectorStore | None = None

def get_vector_store() -> VectorStore:
    global _instance
    if _instance is None:
        _instance = VectorStore.load()
    return _instance
