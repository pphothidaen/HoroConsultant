---
description: Vector database FAISS indexing, embedding governance, and RAG retrieval optimization.
paths: ["project/rag/**/*, data/**/*"]
---

# Vector Database & RAG Governance

## Vector Dimensions & Embeddings
- Embedding model: `nomic-embed-text:latest` with fixed dimension 768.
- FAISS Index: IndexFlatIP (cosine similarity normalized) or IndexHNSWFlat for fast ANN lookup.

<important if="ingesting_vectors">
- Always normalize embeddings before adding to FAISS index.
- Metadata and chunks must be synchronized atomically to disk.
- Never ingest uncleaned HTML or raw binary blobs into semantic text storage.
</important>

<important if="querying_rag">
- Set Top-K to appropriate threshold (default k=5) to avoid context bloat.
- Filter low-confidence matches (score < 0.65) to prevent hallucinations.
</important>
