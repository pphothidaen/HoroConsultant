"""Contract tests for distillation checklist and dataset integrity."""

import json
from pathlib import Path


def test_distillation_checklist_structure():
    path = Path("project/data/distillation_checklist.json")
    assert path.is_file(), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "version" in data
    assert "topics" in data
    assert isinstance(data["topics"], dict)
    for key, topic in data["topics"].items():
        assert "key" in topic
        assert "has_diagram" in topic
        assert "completed_at" in topic


def test_distillation_checklist_updated_timestamp():
    path = Path("project/data/distillation_checklist.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["last_updated"].startswith("2026-08-31T06:13:19")
