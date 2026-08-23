"""
project/tests/test_distillation_checklist.py
============================================
Comprehensive test suite for:
1. DistillationChecklistTracker idempotency & persistence
2. HermesKnowledgeMiner diagram extraction & checklist skip
3. DatasetCurator multimodal VL JSONL export
4. Telegram Bot /checklist and /distill --force commands
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from project.mlops.distillation.checklist_tracker import DistillationChecklistTracker
from project.mlops.distillation.curator import DatasetCurator
from project.mlops.distillation.hermes_miner import HermesKnowledgeMiner, SyntheticSample
from project.mlops.notifications.telegram_bot import TelegramBotController


@pytest.fixture
def temp_checklist(tmp_path):
    checklist_file = tmp_path / "test_checklist.json"
    return DistillationChecklistTracker(checklist_path=checklist_file)


def test_checklist_tracker_lifecycle(temp_checklist):
    tracker = temp_checklist
    assert tracker.is_completed("bazi", "Topic A", "nb_01") is False

    tracker.mark_in_progress("bazi", "Topic A", "nb_01")
    stats_in_prog = tracker.get_summary_stats()
    assert stats_in_prog["in_progress"] == 1
    assert stats_in_prog["completed"] == 0

    tracker.mark_completed(
        domain="bazi",
        topic="Topic A",
        notebook_id="nb_01",
        sample_ids=["syn_001", "syn_002"],
        content_hash="hash123",
        has_diagram=True,
        diagram_type="palm_grid"
    )

    assert tracker.is_completed("bazi", "Topic A", "nb_01") is True
    stats_done = tracker.get_summary_stats()
    assert stats_done["completed"] == 1
    assert stats_done["diagrams_count"] == 1
    assert stats_done["by_domain"]["bazi"]["completed"] == 1


def test_hermes_miner_skips_completed_unless_forced(temp_checklist):
    tracker = temp_checklist
    tracker.mark_completed(
        domain="bazi",
        topic="การวิเคราะห์ดิถีธาตุไม้กะ (Yang Wood Jia) ในฤดูใบไม้ร่วงและธาตุปรับสมดุล",
        notebook_id="nb_bazi_classics",
        sample_ids=["s1"],
        content_hash="h1"
    )

    miner = HermesKnowledgeMiner(checklist_tracker=tracker)

    # 1. Normal run (should skip completed topic)
    samples_normal = miner.mine_domain(domain="bazi", force=False)
    # Total topics in bazi is 5, 1 completed -> 4 mined
    assert len(samples_normal) == 4 * 3  # 3 samples per topic (inst, trithinking, diagram)

    # 2. Force run (should re-mine all 5 topics)
    samples_forced = miner.mine_domain(domain="bazi", force=True)
    assert len(samples_forced) == 5 * 3


def test_curator_exports_both_chatml_and_multimodal_vl(tmp_path):
    curator = DatasetCurator(output_dir=tmp_path)
    samples = [
        SyntheticSample(
            id="sample_001",
            domain="bazi",
            format_type="chatml",
            instruction="วิเคราะห์ผังฝ่ามือ 12 นักษัตรอย่างละเอียดตามหลักวิชาการ",
            input_context="คำถามทางวิชาการอิงคัมภีร์ดั้งเดิมในระบบ BAZI",
            output="จากการวิเคราะห์ตามคัมภีร์หลัก โครงสร้างผังฝ่ามือแสดงตำแหน่งของ 12 นักษัตรโดยเริ่มจากโคนนิ้วนางชวดไปยังปลายนิ้ว",
            citations=[{"title": "Book A"}],
            diagram_type="palm_grid",
            diagram_image_path="project/rag/obsidian_vault/diagrams/palm.png",
            is_multimodal=True
        )
    ]

    stats = curator.curate_and_export(
        samples=samples,
        dataset_name="test_multimodal",
        target_format="chatml",
        export_multimodal=True
    )

    assert stats["final_unique_count"] == 1
    assert stats["multimodal_vl_count"] == 1
    assert Path(stats["output_path"]).exists()
    assert Path(stats["multimodal_vl_path"]).exists()

    vl_content = Path(stats["multimodal_vl_path"]).read_text(encoding="utf-8")
    record = json.loads(vl_content.strip())
    assert record["id"] == "sample_001"
    assert record["diagram_type"] == "palm_grid"
    user_parts = record["messages"][1]["content"]
    assert any(p.get("type") == "image_url" for p in user_parts)


def test_telegram_bot_checklist_and_force_distill(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    bot = TelegramBotController()

    res_chk = bot.handle_command("/checklist", "12345")
    assert "NotebookLM Distillation Checklist" in res_chk
    assert "Domain Breakdown" in res_chk

    res_distill = bot.handle_command("/distill bazi --force", "12345")
    assert "Hermes Agent สกัดความรู้สำเร็จ" in res_distill
    assert "Multimodal Diagrams" in res_distill
