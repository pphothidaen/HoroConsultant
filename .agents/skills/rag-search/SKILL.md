---
name: rag-search
description: Perform ranked retrieval over FAISS-indexed classical metaphysics texts with configured embeddings.
---

# 📚 RAG Vector Store Search Skill

### Purpose
Retrieves relevant classical astrological literature and Thai/Chinese metaphysics passages from FAISS Index using Ollama `nomic-embed-text` embeddings.

### Usage
```python
from project.rag.vector_store import VectorStore
results = VectorStore().search("การฮะของกิ่งฟ้ากิ่งดิน", top_k=5)
```
