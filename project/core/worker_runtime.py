"""Unified Worker Runtime Backend Interface (ABC).

Defines the contract for decoupled execution runtimes (herdr, tmux, mock).
Strict rule: Zero Jira knowledge or business workflow logic in this layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from project.core.execution_identity import ExecutionIdentity


class ProcessState(str, Enum):
    """Normalized process lifecycle state."""

    STARTING = "starting"
    RUNNING = "running"
    WORKING = "working"
    IDLE = "idle"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuntimeHealth:
    """Health check result for a runtime backend."""

    backend_name: str
    available: bool
    healthy: bool
    version: Optional[str] = None
    detail: Optional[str] = None


@dataclass(frozen=True)
class ProcessStatus:
    """Status snapshot of an active worker process."""

    identity: ExecutionIdentity
    backend_name: str
    state: ProcessState
    pid: Optional[int]
    exit_code: Optional[int] = None
    alive: bool = True
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SpawnRequest:
    """Request payload to spawn a decoupled worker process."""

    identity: ExecutionIdentity
    command: List[str]
    cwd: str
    env: Optional[Dict[str, str]] = None
    bounded_lines_limit: int = 30


class RuntimeBackend(ABC):
    """Abstract Base Class for all Worker Runtime Backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the runtime backend (e.g. 'herdr', 'tmux', 'mock')."""
        pass

    @abstractmethod
    def detect(self) -> bool:
        """Check if the backend binary/daemon is installed and available on host."""
        pass

    @abstractmethod
    def health(self) -> RuntimeHealth:
        """Probe the runtime health status."""
        pass

    @abstractmethod
    def spawn(self, request: SpawnRequest) -> ProcessStatus:
        """Spawn a new isolated worker process bound to the execution identity."""
        pass

    @abstractmethod
    def attach(self, identity: ExecutionIdentity) -> ProcessStatus:
        """Attach to an existing worker process by execution identity."""
        pass

    @abstractmethod
    def send(self, identity: ExecutionIdentity, input_data: str) -> None:
        """Send input text / keystrokes to the worker process."""
        pass

    @abstractmethod
    def read(self, identity: ExecutionIdentity, lines: int = 30) -> str:
        """Read bounded output (last N lines) from the worker process buffer."""
        pass

    @abstractmethod
    def status(self, identity: ExecutionIdentity) -> ProcessStatus:
        """Get the current process lifecycle status."""
        pass

    @abstractmethod
    def terminate(self, identity: ExecutionIdentity, grace_seconds: float = 2.0) -> bool:
        """Terminate the worker process and clean up pane/workspace resources."""
        pass

    @abstractmethod
    def collect_metadata(self, identity: ExecutionIdentity) -> Dict[str, Any]:
        """Collect runtime-specific telemetry and resource usage."""
        pass
