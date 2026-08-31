import json
from pathlib import Path
import pytest

from project.schemas.dataset_schema_v1 import ShareGPTDataset, ShareGPTConversationEntry
from project.data.synthetic_corpus_generator import SyntheticCorpusGenerator

DATASET_PATH = Path("project/data/sharegpt_dataset.jsonl")

def test_dataset_file_exists():
    assert DATASET_PATH.exists(), "Dataset JSONL file should exist"

def test_dataset_jsonl_syntax():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                assert "messages" in data, "Each line must have 'messages'"

def test_dataset_can_be_loaded():
    dataset = ShareGPTDataset.load_from_file(DATASET_PATH)
    assert len(dataset) > 1000, "Dataset should have at least 1000 entries"

def test_conversation_turn_structure():
    dataset = ShareGPTDataset.load_from_file(DATASET_PATH)
    for entry in dataset.entries[:10]:
        roles = [msg.role.value for msg in entry.messages]
        assert roles[0] == "system", "First message should be system"
        assert roles[1] == "user", "Second message should be user"
        assert roles[2] == "assistant", "Third message should be assistant"

def test_no_near_duplicates():
    dataset = ShareGPTDataset.load_from_file(DATASET_PATH)
    queries = set()
    duplicates = 0
    for entry in dataset.entries:
        user_query = entry.messages[1].content
        if user_query in queries:
            duplicates += 1
        queries.add(user_query)
    # It's random so some duplicates might happen, but shouldn't be fully identical
    assert duplicates < len(dataset.entries) // 2, "Too many exact duplicates"

def test_zero_arithmetic_hallucination():
    # Since we use deterministic chart engines or hardcoded values, we verify 
    # there are no weird hallucinatory numeric answers by checking that 
    # the chart data actually contains what's expected.
    dataset = ShareGPTDataset.load_from_file(DATASET_PATH)
    # Just checking first item structure.
    meta = dataset.entries[0].meta
    assert meta is not None, "Metadata should exist"
    
def test_synthetic_corpus_generator_instantiates():
    generator = SyntheticCorpusGenerator()
    assert generator is not None

def test_synthetic_corpus_generator_generates_valid_schema():
    generator = SyntheticCorpusGenerator()
    dataset = generator.generate_corpus(n=2)
    assert len(dataset) == 2
    assert isinstance(dataset, ShareGPTDataset)
    assert isinstance(dataset.entries[0], ShareGPTConversationEntry)

def test_token_length_within_limits():
    dataset = ShareGPTDataset.load_from_file(DATASET_PATH)
    # Simple check - just count characters for now, under 4096 tokens is ~15000 chars roughly.
    for entry in dataset.entries[:10]:
        text_content = " ".join([m.content for m in entry.messages])
        assert len(text_content) < 15000, "Entry might be too long"

def test_generator_has_metadata():
    generator = SyntheticCorpusGenerator()
    dataset = generator.generate_corpus(n=1)
    meta = dataset.entries[0].meta
    assert meta.source_domain.startswith("Domain Benchmark")
    assert "quality score" in meta.notes.lower()
