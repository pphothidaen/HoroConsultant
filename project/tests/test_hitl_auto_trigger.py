"""
project/tests/test_hitl_auto_trigger.py
=======================================
Unit tests for continuous MLOps HITL autotrain triggering.
"""

from unittest.mock import patch, MagicMock
from project.hitl_router import _run_finetune_trigger, _approved_hitl_count


def test_approved_hitl_count_calculation():
    reviews = {
        "item_1": {"decision": "approve", "final_answer": "Valid explanation"},
        "item_2": {"decision": "edit", "final_answer": "Edited explanation"},
        "item_3": {"decision": "reject", "final_answer": ""},
        "item_4": {"decision": "approve", "final_answer": ""},  # empty answer ignored
    }
    assert _approved_hitl_count(reviews) == 2


def test_run_finetune_trigger_threshold_guard(monkeypatch):
    monkeypatch.setenv("HITL_AUTOTRAIN_TRIGGER_THRESHOLD", "50")

    mock_db = {
        "reviews": {
            f"id_{i}": {"decision": "approve", "question": f"Question {i}", "final_answer": f"Answer {i}"}
            for i in range(10)
        },
        "automation": {"threshold": 50, "next_trigger_count": 50},
    }

    with patch("project.hitl_router.load_hitl_db", return_value=mock_db):
        with patch("project.hitl_router._audit_metaphysical_scope", return_value={
            "scope_domain": "metaphysical-domain-engine",
            "summary": {"missing_required_human_gate": 0, "pass_gate_check": True}
        }):
            with patch("project.hitl_router._write_hitl_exports"):
                res = _run_finetune_trigger(force=False, dry_run=True, requested_by="test")
                assert res["status"] == "skipped"
                assert res["reason"] == "threshold_not_reached"
                assert res["approved_count"] == 10
                assert res["next_trigger_count"] == 50


def test_run_finetune_trigger_fires_when_forced_or_threshold_reached(monkeypatch):
    mock_db = {
        "reviews": {
            "id_1": {
                "decision": "approve",
                "final_answer": "Expert BaZi Reading",
                "question": "Analyze my chart",
                "category": "chinese_metaphysics",
            }
        },
        "automation": {"threshold": 1, "next_trigger_count": 1},
    }

    mock_training_res = {
        "status": "QUEUED (DRY-RUN)",
        "target_model": "qwen2.5:7b-instruct-q4_K_M",
    }

    with patch("project.hitl_router.load_hitl_db", return_value=mock_db):
        with patch("project.hitl_router.save_hitl_db"):
            with patch("project.hitl_router._audit_metaphysical_scope", return_value={
                "scope_domain": "metaphysical-domain-engine",
                "summary": {"missing_required_human_gate": 0, "pass_gate_check": True}
            }):
                with patch("project.hitl_router._write_hitl_exports"):
                    with patch("project.hitl_router.FineTuneOrchestrator") as mock_orch:
                        mock_orch.return_value.trigger_kaggle_training.return_value = mock_training_res
                        res = _run_finetune_trigger(force=True, dry_run=True, requested_by="test")
                        assert res["status"] == "QUEUED (DRY-RUN)"
                        assert res["requested_by"] == "test"
