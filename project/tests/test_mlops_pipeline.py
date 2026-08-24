"""
project/tests/test_mlops_pipeline.py
====================================
Comprehensive Test Suite for Autonomous MLOps, Distillation, and Fine-Tuning Components.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from project.main import app
from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import HermesKnowledgeMiner, SyntheticSample
from project.mlops.distillation.notebooklm_client import NotebookLMClient
from project.mlops.notifications.webhook_notifier import WebhookNotifier
from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_synthetic_list():
    return [
        SyntheticSample(
            id="test_001",
            domain="bazi",
            format_type="chatml",
            instruction="จงอธิบายหลักการดิถีธาตุไม้กะในฤดูใบไม้ร่วง",
            input_context="คำถามทางวิชาการปาจื่อ",
            output="ตามหลักคัมภีร์ตีเทียนสุย ไม้กะในฤดูใบไม้ร่วงจำเป็นต้องพึ่งพาน้ำเปียะเพื่อหล่อเลี้ยงและไฟเปียะเพื่อให้ความอบอุ่น",
            citations=[{"source_id": "src_1", "title": "Di Tian Sui", "snippet": "..."}],
            metadata={"source": "test"}
        ),
        SyntheticSample(
            id="test_002",
            domain="ziwei",
            format_type="cot_reasoning",
            instruction="โปรดวิเคราะห์ดาวจื่อเวยร่วมกับดาวเจ็ดพิฆาต",
            input_context="ดวงจักรพรรดิ",
            output="<thought>1. วิเคราะห์ดาวประธาน 2. วิเคราะห์ดาวประกอบ</thought>\nดาวจื่อเวยร่วมดาวเจ็ดพิฆาตบ่งชี้ถึงภาวะผู้นำที่กล้าได้กล้าเสีย",
            citations=[],
            metadata={"source": "test"}
        )
    ]


def test_notebooklm_client_mock_and_list():
    client = NotebookLMClient()
    assert client.check_connection() is True
    
    notebooks = client.list_notebooks()
    assert len(notebooks) >= 4
    assert any(nb["id"] == "nb_bazi_classics" for nb in notebooks)

    res = client.query_notebook("nb_bazi_classics", "ทดสอบคำถามดิถีธาตุ")
    assert "answer" in res
    assert "citations" in res
    assert res["confidence"] >= 0.90


def test_hermes_miner_generation_and_tri_thinking():
    miner = HermesKnowledgeMiner()
    bazi_samples = miner.mine_domain("bazi", force=True)
    assert len(bazi_samples) > 0
    assert all(isinstance(s, SyntheticSample) for s in bazi_samples)
    assert any(s.format_type == "tri_thinking" for s in bazi_samples)
    
    # Test Tri-Thinking Audit Structure
    audit = miner.perform_tri_thinking_audit(
        domain="bazi",
        topic="การวิเคราะห์ดิถีธาตุไม้กะ",
        initial_answer="คำตอบละเอียดมากกว่าแปดสิบตัวอักษรเพื่อทดสอบระบบวิเคราะห์เชิงลึกอย่างสมบูรณ์ตามหลักเกณฑ์",
        citations=[{"source_id": "src_1", "title": "Di Tian Sui", "snippet": "..."}]
    )
    assert "Systems Thinking" in audit.systems_perspective
    assert "Critical Thinking" in audit.critical_perspective
    assert "Inversion Thinking" in audit.inversion_perspective
    assert audit.confidence_score >= 0.90
    assert audit.requires_correction is False


def test_hermes_self_correction_loop():
    miner = HermesKnowledgeMiner(max_correction_rounds=2)
    # Test sample with missing citations and short answer triggering self-correction
    final_ans, audit, rounds = miner.execute_self_correction_loop(
        domain="bazi",
        topic="หัวข้อทดสอบที่มีข้อมูลสั้นมาก",
        initial_answer="สั้น",
        citations=[],
        notebook_id="nb_bazi_classics"
    )
    assert rounds > 0
    assert len(final_ans) > 50
    assert "Self-Correction" in final_ans


def test_dataset_curator_validation_and_export(tmp_path, sample_synthetic_list):
    curator = DatasetCurator(output_dir=tmp_path)
    
    # Test valid sample
    is_valid, msg = curator.validate_sample(sample_synthetic_list[0])
    assert is_valid is True
    
    # Test invalid sample
    invalid_sample = SyntheticSample(
        id="bad_001",
        domain="unknown_domain",
        format_type="chatml",
        instruction="สั้น",
        input_context="",
        output="",
        citations=[],
        metadata={}
    )
    is_valid_bad, msg_bad = curator.validate_sample(invalid_sample)
    assert is_valid_bad is False

    # Test export ChatML
    stats = curator.curate_and_export(sample_synthetic_list, dataset_name="test_dataset", target_format="chatml")
    assert stats["final_unique_count"] == 2
    assert Path(stats["output_path"]).exists()

    # Read exported file and verify structure
    with open(stats["output_path"], encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    assert len(records) == 2
    assert "messages" in records[0]
    assert records[0]["messages"][0]["role"] == "system"


def test_webhook_notifier_formatting(monkeypatch):
    # This contract covers formatting with delivery disabled; never inherit
    # real local credentials or make network calls from the unit suite.
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    notifier = WebhookNotifier()
    # Test that notify calls execute without throwing exceptions even with no secrets set
    res1 = notifier.notify_distillation_complete({"total_input": 10, "final_unique_count": 10, "output_path": "test.jsonl"})
    assert res1 is True

    res2 = notifier.notify_training_status("pphothidaen/test-kernel", "QUEUED", "Test status")
    assert res2 is True

    res3 = notifier.notify_error("UnitTest", "Test error message")
    assert res3 is True


def test_finetune_orchestrator_dry_run():
    orchestrator = FineTuneOrchestrator()
    res = orchestrator.trigger_kaggle_training(dry_run=True)
    assert res["status"] == "QUEUED (DRY-RUN)"
    assert res["target_model"] == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"


def test_mlops_fastapi_endpoints(client):
    # Test GET /api/v1/mlops/status
    res = client.get("/api/v1/mlops/status")
    assert res.status_code == 200
    data = res.json()
    assert "target_model" in data
    assert "available_domains" in data

    # Test GET /api/v1/mlops/datasets
    res = client.get("/api/v1/mlops/datasets")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Test POST /api/v1/mlops/distill
    res = client.post(
        "/api/v1/mlops/distill",
        json={"domain": "bazi", "dataset_name": "test_api_distill", "format": "chatml", "dry_run": True}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["stats"]["final_unique_count"] > 0

    # Test POST /api/v1/mlops/train (dry-run)
    res = client.post(
        "/api/v1/mlops/train",
        json={"dry_run": True}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "QUEUED (DRY-RUN)"
