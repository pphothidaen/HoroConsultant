"""Tmux Runtime Adapter Implementation for Linux/CI and reliable fallback (AT-03).

Implements RuntimeBackend ABC using standard `tmux` multiplexer.
Provides isolated session lifecycle, bounded capture (<= 30 lines), and clean termination.
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


class TmuxRuntimeAdapter(RuntimeBackend):
    """Tmux-based reliable process execution backend."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        self._binary_path = binary_path or shutil.which("tmux") or "tmux"

    @property
    def name(self) -> str:
        return "tmux"

    def detect(self) -> bool:
        """Check if tmux binary is installed and executable."""
        return shutil.which(self._binary_path) is not None or os.path.exists(self._binary_path)

    def health(self) -> RuntimeHealth:
        """Probe tmux version and health."""
        if not self.detect():
            return RuntimeHealth(
                backend_name=self.name,
                available=False,
                healthy=False,
                detail="tmux executable not found in PATH",
            )
        try:
            res = subprocess.run(
                [self._binary_path, "-V"],
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
                    detail="tmux binary operational",
                )
            return RuntimeHealth(
                backend_name=self.name,
                available=True,
                healthy=False,
                detail=f"tmux -V returned exit code {res.returncode}",
            )
        except Exception as exc:
            return RuntimeHealth(
                backend_name=self.name,
                available=True,
                healthy=False,
                detail=f"tmux probe failed: {exc}",
            )

    def _session_name(self, identity: ExecutionIdentity) -> str:
        """Generate safe tmux session name from execution identity."""
        safe_exec = identity.execution_id.replace("-", "_").replace(".", "_")
        safe_worker = identity.worker_id.replace("-", "_").replace(".", "_")
        return f"tmux_{safe_exec}_{safe_worker}"

    def spawn(self, request: SpawnRequest) -> ProcessStatus:
        """Spawn a detached tmux session running the command."""
        if not self.detect():
            return ProcessStatus(
                identity=request.identity,
                backend_name=self.name,
                state=ProcessState.FAILED,
                pid=None,
                alive=False,
                metadata={"error": "tmux binary not available"},
            )

        sess_name = self._session_name(request.identity)
        cmd_str = " ".join(f"'{arg}'" if " " in arg else arg for arg in request.command)

        try:
            # Kill any existing session with same name to prevent collisions
            subprocess.run(
                [self._binary_path, "kill-session", "-t", sess_name],
                capture_output=True,
                timeout=3,
                check=False,
            )

            # Create new detached session
            spawn_args = [
                self._binary_path,
                "new-session",
                "-d",
                "-s",
                sess_name,
                "-c",
                request.cwd,
                cmd_str,
            ]
            res = subprocess.run(
                spawn_args,
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
                metadata={"tmux_session": sess_name},
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
        """Attach to tmux session status."""
        return self.status(identity)

    def send(self, identity: ExecutionIdentity, input_data: str) -> None:
        """Send input text / keystrokes to tmux session."""
        if not self.detect():
            return
        sess_name = self._session_name(identity)
        subprocess.run(
            [self._binary_path, "send-keys", "-t", sess_name, input_data, "Enter"],
            capture_output=True,
            timeout=5,
            check=False,
        )

    def read(self, identity: ExecutionIdentity, lines: int = 30) -> str:
        """Read bounded output (last N lines) from tmux pane buffer."""
        if not self.detect():
            return ""
        sess_name = self._session_name(identity)
        res = subprocess.run(
            [
                self._binary_path,
                "capture-pane",
                "-pt",
                sess_name,
                "-S",
                f"-{lines}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if res.returncode != 0:
            return ""
        # Return only the last N lines
        raw_lines = res.stdout.splitlines()
        return "\n".join(raw_lines[-lines:])

    def status(self, identity: ExecutionIdentity) -> ProcessStatus:
        """Check if tmux session is still alive."""
        if not self.detect():
            return ProcessStatus(
                identity=identity,
                backend_name=self.name,
                state=ProcessState.UNKNOWN,
                pid=None,
                alive=False,
            )
        sess_name = self._session_name(identity)
        res = subprocess.run(
            [self._binary_path, "has-session", "-t", sess_name],
            capture_output=True,
            timeout=3,
            check=False,
        )
        if res.returncode == 0:
            return ProcessStatus(
                identity=identity,
                backend_name=self.name,
                state=ProcessState.RUNNING,
                pid=None,
                alive=True,
                metadata={"tmux_session": sess_name},
            )
        return ProcessStatus(
            identity=identity,
            backend_name=self.name,
            state=ProcessState.COMPLETED,
            pid=None,
            alive=False,
            metadata={"tmux_session": sess_name},
        )

    def terminate(self, identity: ExecutionIdentity, grace_seconds: float = 2.0) -> bool:
        """Kill tmux session."""
        if not self.detect():
            return False
        sess_name = self._session_name(identity)
        res = subprocess.run(
            [self._binary_path, "kill-session", "-t", sess_name],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return res.returncode == 0

    def collect_metadata(self, identity: ExecutionIdentity) -> Dict[str, Any]:
        """Collect tmux metadata."""
        return {
            "backend": self.name,
            "session": self._session_name(identity),
        }
