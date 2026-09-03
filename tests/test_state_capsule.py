"""Unit tests for 3-Phase Seamless Handoff State Capsule Protocol."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.core.state_capsule import StateCapsule, StateCapsuleManager


@pytest.fixture
def capsule_env(tmp_path: Path) -> tuple[StateCapsuleManager, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    capsule_dir = ws_root / "plans" / "evidence" / "quota_capsules"
    handoff_file = ws_root / "HANDOFF.md"
    handoff_file.write_text("# HANDOFF PROTOCOL\n\n## Rescue Queue\n", encoding="utf-8")

    manager = StateCapsuleManager(workspace_root=ws_root, capsule_dir=capsule_dir)
    return manager, ws_root


def test_phase1_pre_swap_freeze(capsule_env: tuple[StateCapsuleManager, Path]) -> None:
    """Test Phase 1: Pre-Swap Freeze creates valid StateCapsule and updates HANDOFF.md."""
    manager, ws_root = capsule_env
    cognitive_summary = "Completed AST parser, working on TTR circuit trip logic."
    remaining_tasks = ["TICKET-DEV-002: Add unit tests", "TICKET-DEV-003: Hot-swap router"]

    capsule = manager.create_pre_swap_freeze(
        ticket_id="TICKET-QUOTA-004",
        source_account="codex1",
        cognitive_summary=cognitive_summary,
        remaining_subtasks=remaining_tasks,
        metadata={"priority": "HIGH"},
        custom_epoch=1000.0,
    )

    assert capsule.capsule_id == "CAPSULE-1000-TICKET-QUOTA-004"
    assert capsule.phase == "PHASE_1_FROZEN"
    assert capsule.source_account == "codex1"
    assert capsule.target_account is None
    assert capsule.cognitive_memory_summary == cognitive_summary
    assert capsule.remaining_subtasks == remaining_tasks

    # Verify disk persistence
    saved = manager.load_capsule(capsule.capsule_id)
    assert saved is not None
    assert saved.capsule_id == capsule.capsule_id
    assert saved.cognitive_memory_summary == cognitive_summary

    # Verify HANDOFF.md rescue queue
    handoff_content = (ws_root / "HANDOFF.md").read_text(encoding="utf-8")
    assert "CAPSULE-1000-TICKET-QUOTA-004" in handoff_content
    assert "codex1" in handoff_content


def test_phase2_hot_swap_bootstrap(capsule_env: tuple[StateCapsuleManager, Path]) -> None:
    """Test Phase 2: Hot-Swap Bootstrap assigns target account and advances phase."""
    manager, _ = capsule_env
    capsule = manager.create_pre_swap_freeze(
        ticket_id="TICKET-QUOTA-004",
        source_account="codex1",
        cognitive_summary="Midway through refactoring.",
        remaining_subtasks=["Task A", "Task B"],
        custom_epoch=2000.0,
    )

    bootstrapped = manager.bootstrap_hot_swap(
        capsule_id=capsule.capsule_id,
        target_account="codex2",
        verify_workspace=False,
        custom_epoch=2010.0,
    )

    assert bootstrapped.phase == "PHASE_2_BOOTSTRAPPED"
    assert bootstrapped.target_account == "codex2"
    assert bootstrapped.bootstrapped_at_epoch == 2010.0
    assert bootstrapped.cognitive_memory_summary == "Midway through refactoring."
    assert bootstrapped.remaining_subtasks == ["Task A", "Task B"]


def test_phase3_return_wakeup(capsule_env: tuple[StateCapsuleManager, Path]) -> None:
    """Test Phase 3: Return Wakeup marks capsule as archived upon primary recovery."""
    manager, _ = capsule_env
    capsule = manager.create_pre_swap_freeze(
        ticket_id="TICKET-QUOTA-004",
        source_account="codex1",
        cognitive_summary="All subtasks completed on failover account.",
        remaining_subtasks=[],
        custom_epoch=3000.0,
    )
    manager.bootstrap_hot_swap(capsule.capsule_id, target_account="codex2", verify_workspace=False, custom_epoch=3010.0)

    archived = manager.complete_return_wakeup(
        capsule_id=capsule.capsule_id,
        archive_notes="Primary account codex1 recovered. Work verified.",
        custom_epoch=3100.0,
    )

    assert archived.phase == "PHASE_3_ARCHIVED"
    assert archived.archived_at_epoch == 3100.0
    assert archived.metadata.get("archive_notes") == "Primary account codex1 recovered. Work verified."


def test_zero_cognitive_context_loss_roundtrip(capsule_env: tuple[StateCapsuleManager, Path]) -> None:
    """Test that all cognitive variables and metadata survive full JSON roundtrip."""
    manager, _ = capsule_env
    data_dict = {
        "capsule_id": "CAPSULE-TEST-ROUNDTRIP",
        "ticket_id": "TICKET-QUOTA-004",
        "source_account": "agy1",
        "target_account": "codex3",
        "phase": "PHASE_2_BOOTSTRAPPED",
        "git_branch": "feature/quota-swap",
        "git_commit_sha": "abc1234def5678",
        "modified_files": ["project/core/quota_registry.py", "project/core/hot_swap_router.py"],
        "diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "cognitive_memory_summary": "Extensive context with multi-step rationale and formulas.",
        "remaining_subtasks": ["Step 1", "Step 2", "Step 3"],
        "created_at_utc": "2026-09-04T01:30:00Z",
        "created_at_epoch": 5000.0,
        "bootstrapped_at_epoch": 5010.0,
        "archived_at_epoch": None,
        "metadata": {"complex_key": [1, 2, 3], "flag": True},
    }

    capsule = StateCapsule.from_dict(data_dict)
    manager.save_capsule(capsule)

    loaded = manager.load_capsule("CAPSULE-TEST-ROUNDTRIP")
    assert loaded is not None
    assert loaded.to_dict() == data_dict
