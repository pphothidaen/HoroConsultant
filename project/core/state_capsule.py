#!/usr/bin/env python3
"""3-Phase Seamless Handoff State Capsule Protocol.

Implements zero-context-loss state migration during quota exhaustion:
- Phase 1: Pre-Swap Freeze (capture capsule, compute diff SHA, persist to disk & update HANDOFF.md)
- Phase 2: Hot-Swap Bootstrap (verify workspace state, deserialize capsule, resume execution)
- Phase 3: Return Wakeup (event-driven notification upon primary recovery, graceful archive)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional


@dataclass
class StateCapsule:
    capsule_id: str
    ticket_id: str
    source_account: str
    target_account: Optional[str] = None
    phase: str = "PHASE_1_FROZEN"  # "PHASE_1_FROZEN", "PHASE_2_BOOTSTRAPPED", "PHASE_3_ARCHIVED"
    git_branch: str = "main"
    git_commit_sha: str = ""
    modified_files: list[str] = field(default_factory=list)
    diff_sha256: str = ""
    cognitive_memory_summary: str = ""
    remaining_subtasks: list[str] = field(default_factory=list)
    created_at_utc: str = ""
    created_at_epoch: float = 0.0
    bootstrapped_at_epoch: Optional[float] = None
    archived_at_epoch: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateCapsule:
        return cls(**data)


class StateCapsuleManager:
    """Manages creation, serialization, bootstrap, and archiving of StateCapsules."""

    def __init__(self, workspace_root: Optional[Path | str] = None, capsule_dir: Optional[Path | str] = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[2]
        if capsule_dir:
            self.capsule_dir = Path(capsule_dir)
        else:
            self.capsule_dir = self.workspace_root / "plans" / "evidence" / "quota_capsules"
        self.capsule_dir.mkdir(parents=True, exist_ok=True)

    def get_git_info(self) -> tuple[str, str, list[str], str]:
        """Inspect git branch, HEAD commit, modified files, and diff SHA-256."""
        branch = "unknown"
        commit = ""
        modified_files = []
        diff_sha = hashlib.sha256(b"").hexdigest()

        try:
            r_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r_branch.returncode == 0:
                branch = r_branch.stdout.strip()

            r_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r_commit.returncode == 0:
                commit = r_commit.stdout.strip()

            r_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r_status.returncode == 0:
                for line in r_status.stdout.splitlines():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        modified_files.append(parts[1])

            r_diff = subprocess.run(
                ["git", "diff"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if r_diff.returncode == 0:
                diff_bytes = r_diff.stdout.encode("utf-8")
                diff_sha = hashlib.sha256(diff_bytes).hexdigest()
        except Exception:
            pass

        return branch, commit, modified_files, diff_sha

    def create_pre_swap_freeze(
        self,
        ticket_id: str,
        source_account: str,
        cognitive_summary: str,
        remaining_subtasks: list[str],
        metadata: Optional[dict[str, Any]] = None,
        custom_epoch: Optional[float] = None,
    ) -> StateCapsule:
        """Phase 1: Pre-Swap Freeze. Capture execution context and persist StateCapsule."""
        now_epoch = custom_epoch if custom_epoch is not None else time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        ts_id = int(now_epoch)
        capsule_id = f"CAPSULE-{ts_id}-{ticket_id}"

        branch, commit, mod_files, diff_sha = self.get_git_info()

        capsule = StateCapsule(
            capsule_id=capsule_id,
            ticket_id=ticket_id,
            source_account=source_account,
            target_account=None,
            phase="PHASE_1_FROZEN",
            git_branch=branch,
            git_commit_sha=commit,
            modified_files=mod_files,
            diff_sha256=diff_sha,
            cognitive_memory_summary=cognitive_summary,
            remaining_subtasks=list(remaining_subtasks),
            created_at_utc=now_iso,
            created_at_epoch=now_epoch,
            metadata=metadata or {},
        )

        # Save to disk
        self.save_capsule(capsule)

        # Update HANDOFF.md Rescue Queue if file exists
        self._append_to_handoff_queue(capsule)

        return capsule

    def bootstrap_hot_swap(
        self,
        capsule_id: str,
        target_account: str,
        verify_workspace: bool = True,
        custom_epoch: Optional[float] = None,
    ) -> StateCapsule:
        """Phase 2: Hot-Swap Bootstrap. Validate workspace state and deserialize capsule for new worker."""
        now_epoch = custom_epoch if custom_epoch is not None else time.time()
        capsule = self.load_capsule(capsule_id)
        if not capsule:
            raise FileNotFoundError(f"Capsule {capsule_id} not found in {self.capsule_dir}")

        if verify_workspace:
            cur_branch, _, _, _ = self.get_git_info()
            if cur_branch and capsule.git_branch and cur_branch != capsule.git_branch:
                raise ValueError(
                    f"Workspace branch mismatch: expected '{capsule.git_branch}', found '{cur_branch}'"
                )

        capsule.target_account = target_account
        capsule.phase = "PHASE_2_BOOTSTRAPPED"
        capsule.bootstrapped_at_epoch = now_epoch
        self.save_capsule(capsule)
        return capsule

    def complete_return_wakeup(
        self,
        capsule_id: str,
        archive_notes: str = "",
        custom_epoch: Optional[float] = None,
    ) -> StateCapsule:
        """Phase 3: Return Wakeup. Mark capsule as archived upon successful handback."""
        now_epoch = custom_epoch if custom_epoch is not None else time.time()
        capsule = self.load_capsule(capsule_id)
        if not capsule:
            raise FileNotFoundError(f"Capsule {capsule_id} not found in {self.capsule_dir}")

        capsule.phase = "PHASE_3_ARCHIVED"
        capsule.archived_at_epoch = now_epoch
        if archive_notes:
            capsule.metadata["archive_notes"] = archive_notes
        self.save_capsule(capsule)
        return capsule

    def save_capsule(self, capsule: StateCapsule) -> Path:
        """Persist capsule to JSON file atomically."""
        fpath = self.capsule_dir / f"{capsule.capsule_id}.json"
        temp_path = self.capsule_dir / f".{capsule.capsule_id}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(capsule.to_dict(), f, indent=2)
        os.replace(temp_path, fpath)
        return fpath

    def load_capsule(self, capsule_id: str) -> Optional[StateCapsule]:
        """Load capsule from JSON file."""
        fpath = self.capsule_dir / f"{capsule_id}.json"
        if not fpath.exists():
            return None
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StateCapsule.from_dict(data)

    def _append_to_handoff_queue(self, capsule: StateCapsule) -> None:
        """Append rescue entry to HANDOFF.md if it exists."""
        handoff_file = self.workspace_root / "HANDOFF.md"
        if not handoff_file.exists():
            return
        try:
            content = handoff_file.read_text(encoding="utf-8")
            rescue_entry = (
                f"\n- **Rescue Item**: `{capsule.capsule_id}` | Ticket: `{capsule.ticket_id}` | "
                f"Source: `{capsule.source_account}` | Frozen at: `{capsule.created_at_utc}` | "
                f"Diff SHA: `{capsule.diff_sha256[:12]}`\n"
                f"  Summary: {capsule.cognitive_memory_summary}\n"
            )
            if "## Rescue Queue" in content:
                content = content.replace("## Rescue Queue", f"## Rescue Queue\n{rescue_entry}")
            else:
                content += f"\n## Rescue Queue\n{rescue_entry}"
            handoff_file.write_text(content, encoding="utf-8")
        except Exception:
            pass
