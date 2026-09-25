"""Unit tests for RuntimeSelector and Pre-spawn Immutable Locking (AT-04)."""

from unittest.mock import MagicMock
import pytest

from project.core.execution_identity import ExecutionIdentity
from project.core.runtime_selector import (
    RuntimeImmutableLockError,
    RuntimeSelector,
    RuntimeUnavailableError,
)
from project.core.worker_runtime import RuntimeHealth


@pytest.fixture
def sample_identity():
    return ExecutionIdentity(
        execution_id="exec-lock-001",
        ticket_id="KAN-300",
        attempt=1,
        lease_id="L-300",
        fencing_token="fence-300",
        session_id="session-300",
        worker_id="worker-300",
    )


def test_selector_macos_prefers_herdr():
    mock_herdr = MagicMock()
    mock_herdr.name = "herdr"
    mock_herdr.detect.return_value = True
    mock_herdr.health.return_value = RuntimeHealth("herdr", True, True, "0.6.9")

    mock_tmux = MagicMock()
    mock_tmux.name = "tmux"
    mock_tmux.detect.return_value = True
    mock_tmux.health.return_value = RuntimeHealth("tmux", True, True, "3.4")

    selector = RuntimeSelector(
        herdr_adapter=mock_herdr,
        tmux_adapter=mock_tmux,
        target_platform="darwin",
    )
    backend = selector.select_backend()
    assert backend.name == "herdr"


def test_selector_macos_fallback_to_tmux_when_herdr_unhealthy():
    mock_herdr = MagicMock()
    mock_herdr.name = "herdr"
    mock_herdr.detect.return_value = True
    mock_herdr.health.return_value = RuntimeHealth("herdr", True, False, detail="crashed")

    mock_tmux = MagicMock()
    mock_tmux.name = "tmux"
    mock_tmux.detect.return_value = True
    mock_tmux.health.return_value = RuntimeHealth("tmux", True, True, "3.4")

    selector = RuntimeSelector(
        herdr_adapter=mock_herdr,
        tmux_adapter=mock_tmux,
        target_platform="darwin",
    )
    backend = selector.select_backend()
    assert backend.name == "tmux"


def test_selector_linux_prefers_tmux():
    mock_herdr = MagicMock()
    mock_herdr.name = "herdr"
    mock_herdr.detect.return_value = True
    mock_herdr.health.return_value = RuntimeHealth("herdr", True, True)

    mock_tmux = MagicMock()
    mock_tmux.name = "tmux"
    mock_tmux.detect.return_value = True
    mock_tmux.health.return_value = RuntimeHealth("tmux", True, True)

    selector = RuntimeSelector(
        herdr_adapter=mock_herdr,
        tmux_adapter=mock_tmux,
        target_platform="linux",
    )
    backend = selector.select_backend()
    assert backend.name == "tmux"


def test_selector_immutable_lock_enforcement(sample_identity):
    mock_herdr = MagicMock()
    mock_herdr.name = "herdr"
    mock_herdr.detect.return_value = True
    mock_herdr.health.return_value = RuntimeHealth("herdr", True, True)

    mock_tmux = MagicMock()
    mock_tmux.name = "tmux"
    mock_tmux.detect.return_value = True
    mock_tmux.health.return_value = RuntimeHealth("tmux", True, True)

    selector = RuntimeSelector(
        herdr_adapter=mock_herdr,
        tmux_adapter=mock_tmux,
        target_platform="darwin",
    )

    # Initial lock binds to herdr
    locked = selector.lock_for_execution(sample_identity, backend=mock_herdr)
    assert locked.name == "herdr"

    # Repeated lock with same backend returns existing
    locked_again = selector.lock_for_execution(sample_identity, backend=mock_herdr)
    assert locked_again.name == "herdr"

    # Attempt to swap to tmux mid-lifecycle raises RuntimeImmutableLockError (INVARIANT-06)
    with pytest.raises(RuntimeImmutableLockError, match="INVARIANT-06 violated"):
        selector.lock_for_execution(sample_identity, backend=mock_tmux)


def test_selector_release_lock(sample_identity):
    mock_tmux = MagicMock()
    mock_tmux.name = "tmux"
    mock_tmux.detect.return_value = True
    mock_tmux.health.return_value = RuntimeHealth("tmux", True, True)

    selector = RuntimeSelector(tmux_adapter=mock_tmux, target_platform="linux")
    selector.lock_for_execution(sample_identity)
    assert selector.get_locked_backend(sample_identity) is not None

    selector.release_lock(sample_identity)
    assert selector.get_locked_backend(sample_identity) is None
