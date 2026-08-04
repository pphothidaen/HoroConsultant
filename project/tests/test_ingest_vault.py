"""
project/tests/test_ingest_vault.py
===================================
Unit tests for Vault & Additional Source Ingestion Pipeline.
"""

from pathlib import Path
from project.rag.ingest_vault import chunk_markdown, extract_qa_pairs, qa_to_sharegpt


def test_chunk_markdown_basic():
    text = "# Header 1\nThis is a sample document text for testing chunking algorithm."
    chunks = chunk_markdown(text, source="TestSource", chunk_size=50)
    assert len(chunks) > 0
    assert chunks[0]["source"] == "TestSource"


def test_extract_qa_pairs_patterns():
    md_text = """
## Q: What is Jia Wood?
A: Jia Wood represents Yang Wood, symbolizing a large tall tree.

**User:** How does TST work?
**Assistant:** True Solar Time adjusts local clock time with Equation of Time and longitude offset.
"""
    pairs = extract_qa_pairs(md_text, source="ChatLog")
    assert len(pairs) == 2
    assert pairs[0]["question"] == "What is Jia Wood?"
    assert "Yang Wood" in pairs[0]["answer"]


def test_qa_to_sharegpt():
    qa = {"question": "Q text", "answer": "A text"}
    res = qa_to_sharegpt(qa)
    assert "conversations" in res
    assert len(res["conversations"]) == 3
    assert res["conversations"][1]["value"] == "Q text"
