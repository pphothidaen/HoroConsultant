"""Herdr Runtime Adapter Implementation for macOS agent-aware environments (AT-02).

Implements RuntimeBackend ABC using the local `herdr` binary.
Supports workspace/pane lifecycle, bounded output capture, and state tracking.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from project.core.execution_identity import ExecutionIdentity
from project.core.worker_runtime import (
    ProcessState,
    ProcessStatus,
    RuntimeBackend,
    RuntimeHealth,
    SpawnRequest,
)


class HerdrRuntimeAdapter(RuntimeBackend):
    """Herdr-based agent-aware execution backend."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        self._binary_path = binary_path or shutil.which("herdr") or "herdr"

    @property
    def name(self) -> str:
        return "herdr"

    def detect(self) -> bool:
        """Check if herdr binary is available in PATH or specified location."""
        return shutil.which(self._binary_path) is not None or os.path.exists(self._binary_path)

    def health(self) -> RuntimeHealth:
        """Probe herdr binary version and health."""
        if not self.detect():
            return RuntimeHealth(
                backend_name=self.name,
                available=False,
                healthy=False,
                detail="herdr executable not found in PATH",
            )
        try:
            res = subprocess.run(
                [self._binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                version = res.stdout.strip()
                return RuntimeHealth(
                    backend_name=self.name,
                    available=True,
                    healthy=True,
                    version=version,
                    detail="herdr binary operational",
                )
            return RuntimeHealth(
                backend_name=self.name,
                available=True,
                healthy=False,
                detail=f"herdr --version returned exit code {res.returncode}",
            )
        except Exception as exc:
            return RuntimeHealth(
                backend_name=self.name,
                available=True,
                healthy=False,
                detail=f"herdr probe failed: {exc}",
            )

    def _workspace_name(self, identity: ExecutionIdentity) -> str:
        """Generate isolated workspace identifier from execution identity."""
        return f"ws-{identity.execution_id}"

    def _pane_name(self, identity: ExecutionIdentity) -> str:
        """Generate isolated pane identifier from execution identity."""
        return f"pane-{identity.worker_id}"

    def spawn(self, request: SpawnRequest) -> ProcessStatus:
        """Spawn a worker process inside an isolated herdr workspace and pane."""
        if not self.detect():
            return ProcessStatus(
                identity=request.identity,
                backend_name=self.name,
                state=ProcessState.FAILED,
                pid=None,
                alive=False,
                metadata={"error": "herdr binary not available"},
            )

        ws_name = self._workspace_name(request.identity)
        pane_name = self._pane_name(request.identity)

        try:
            # 1. Create workspace
            subprocess.run(
                [self._binary_path, "workspace", "create", ws_name, "--path", request.cwd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # 2. Create pane and launch command
            cmd_args = [
                self._binary_path,
                "pane",
                "create",
                "--workspace",
                ws_name,
                "--name",
                pane_name,
                "--",
            ] + request.command

            res = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if res.returncode != 0:
                return ProcessStatus(
                    identity=request.identity,
                    backend_name=self.name,
                    state=ProcessState.FAILED,
                    pid=None,
                    alive=False,
                    metadata={"error": res.stderr.strip() or f"exit code {res.returncode}"},
                )

            return ProcessStatus(
                identity=request.identity,
                backend_name=self.name,
                state=ProcessState.RUNNING,
                pid=None,
                alive=True,
                metadata={"workspace": ws_name, "pane": pane_name},
            )
        except Exception as exc:
            return ProcessStatus(
                identity=request.identity,
                backend_name=self.name,
                state=ProcessState.FAILED,
                pid=None,
                alive=False,
                metadata={"error": str(exc)},
            )

    def attach(self, identity: ExecutionIdentity) -> ProcessStatus:
        """Attach to existing herdr pane."""
        return self.status(identity)

    def send(self, identity: ExecutionIdentity, input_data: str) -> None:
        """Send input keystrokes to herdr pane."""
        if not self.detect():
            return
        ws_name = self._workspace_name(identity)
        pane_name = self._pane_name(identity)
        subprocess.run(
            [
                self._binary_path,
                "pane",
                "send",
                "--workspace",
                ws_name,
                "--name",
                pane_name,
                input_data,
            ],
            capture_output=True,
            timeout=5,
            check=False,
        )

    def read(self, identity: ExecutionIdentity, lines: int = 30) -> str:
        """Read bounded output (last N lines) from herdr pane."""
        if not self.detect():
            return ""
        ws_name = self._workspace_name(identity)
        pane_name = self._pane_name(identity)
        res = subprocess.run(
            [
                self._binary_path,
                "pane",
                "read",
                "--workspace",
                ws_name,
                "--name",
                pane_name,
                "--lines",
                str(lines),
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return res.stdout if res.returncode == 0 else ""

    def status(self, identity: ExecutionIdentity) -> ProcessStatus:
        """Get herdr pane status and agent state."""
        if not self.detect():
            return ProcessStatus(
                identity=identity,
                backend_name=self.name,
                state=ProcessState.UNKNOWN,
                pid=None,
                alive=False,
            )
        ws_name = self._workspace_name(identity)
        res = subprocess.run(
            [self._binary_path, "status", "--workspace", ws_name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if res.returncode != 0:
            return ProcessStatus(
                identity=identity,
                backend_name=self.name,
                state=ProcessState.FAILED,
                pid=None,
                alive=False,
                metadata={"detail": res.stderr.strip()},
            )

        output = res.stdout.lower()
        if "working" in output:
            state = ProcessState.WORKING
            alive = True
        elif "idle" in output:
            state = ProcessState.IDLE
            alive = True
        elif "blocked" in output:
            state = ProcessState.BLOCKED
            alive = True
        elif "completed" in output or "exited" in output:
            state = ProcessState.COMPLETED
            alive = False
        else:
            state = ProcessState.RUNNING
            alive = True

        return ProcessStatus(
            identity=identity,
            backend_name=self.name,
            state=state,
            pid=None,
            alive=alive,
            metadata={"raw_status": res.stdout.strip()},
        )

    def terminate(self, identity: ExecutionIdentity, grace_seconds: float = 2.0) -> bool:
        """Terminate herdr pane and remove workspace."""
        if not self.detect():
            return False
        ws_name = self._workspace_name(identity)
        pane_name = self._pane_name(identity)

        # Kill pane
        subprocess.run(
            [self._binary_path, "pane", "kill", "--workspace", ws_name, "--name", pane_name],
            capture_output=True,
            timeout=5,
            check=False,
        )
        # Delete workspace
        res = subprocess.run(
            [self._binary_path, "workspace", "delete", ws_name],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return res.returncode == 0

    def collect_metadata(self, identity: ExecutionIdentity) -> Dict[str, Any]:
        """Collect herdr metadata."""
        return {
            "backend": self.name,
            "workspace": self._workspace_name(identity),
            "pane": self._pane_name(identity),
        }
