"""Platform-Aware Runtime Selector and Pre-Spawn Immutable Lock (AT-04).

Implements:
- Hybrid Runtime Policy:
    macOS: herdr (agent-aware) primary -> tmux fallback
    Linux/CI: tmux primary
- Pre-spawn immutable lock (INVARIANT-06):
    Runtime backend is locked before spawn and cannot be swapped mid-lifecycle.
"""

from __future__ import annotations

import platform
import sys
from typing import Dict, Optional

from project.core.execution_identity import ExecutionIdentity
from project.core.runtime_herdr import HerdrRuntimeAdapter
from project.core.runtime_tmux import TmuxRuntimeAdapter
from project.core.worker_runtime import RuntimeBackend


class RuntimeErrorBase(Exception):
    """Base exception for runtime selector."""

    pass


class RuntimeUnavailableError(RuntimeErrorBase):
    """Raised when no suitable runtime backend is available."""

    pass


class RuntimeImmutableLockError(RuntimeErrorBase):
    """Raised when an illegal backend swap is attempted for a locked execution."""

    pass


class RuntimeSelector:
    """Selects and locks runtime backends according to platform policy."""

    def __init__(
        self,
        herdr_adapter: Optional[HerdrRuntimeAdapter] = None,
        tmux_adapter: Optional[TmuxRuntimeAdapter] = None,
        target_platform: Optional[str] = None,
    ) -> None:
        self._herdr = herdr_adapter or HerdrRuntimeAdapter()
        self._tmux = tmux_adapter or TmuxRuntimeAdapter()
        self._platform = target_platform or sys.platform
        # Maps execution_id -> RuntimeBackend
        self._locks: Dict[str, RuntimeBackend] = {}

    def select_backend(self) -> RuntimeBackend:
        """Select preferred backend based on platform and availability."""
        is_macos = self._platform == "darwin" or self._platform.startswith("mac")

        if is_macos:
            # macOS: Prefer herdr if available and healthy
            if self._herdr.detect():
                health = self._herdr.health()
                if health.healthy:
                    return self._herdr

            # Fallback to tmux
            if self._tmux.detect():
                health = self._tmux.health()
                if health.healthy:
                    return self._tmux

            raise RuntimeUnavailableError(
                "Neither herdr nor tmux is available and healthy on macOS."
            )

        # Linux / CI / other
        if self._tmux.detect():
            health = self._tmux.health()
            if health.healthy:
                return self._tmux

        # Fallback to herdr if available on Linux
        if self._herdr.detect() and self._herdr.health().healthy:
            return self._herdr

        raise RuntimeUnavailableError(
            f"No healthy runtime backend available for platform '{self._platform}'."
        )

    def lock_for_execution(
        self,
        identity: ExecutionIdentity,
        backend: Optional[RuntimeBackend] = None,
    ) -> RuntimeBackend:
        """Lock an execution identity to a backend before spawn (INVARIANT-06)."""
        exec_id = identity.execution_id

        if exec_id in self._locks:
            existing = self._locks[exec_id]
            if backend is not None and backend.name != existing.name:
                raise RuntimeImmutableLockError(
                    f"Execution '{exec_id}' is already locked to backend '{existing.name}'. "
                    f"Cannot swap to '{backend.name}' mid-lifecycle (INVARIANT-06 violated)."
                )
            return existing

        chosen_backend = backend or self.select_backend()
        self._locks[exec_id] = chosen_backend
        return chosen_backend

    def get_locked_backend(self, identity: ExecutionIdentity) -> Optional[RuntimeBackend]:
        """Retrieve previously locked backend for an execution."""
        return self._locks.get(identity.execution_id)

    def release_lock(self, identity: ExecutionIdentity) -> None:
        """Release execution lock upon termination."""
        self._locks.pop(identity.execution_id, None)
