"""Unit tests for TmuxRuntimeAdapter (AT-03)."""

from unittest.mock import MagicMock, patch
import pytest

from project.core.execution_identity import ExecutionIdentity
from project.core.runtime_tmux import TmuxRuntimeAdapter
from project.core.worker_runtime import ProcessState, SpawnRequest


@pytest.fixture
def sample_identity():
    return ExecutionIdentity(
        execution_id="exec-200",
        ticket_id="KAN-200",
        attempt=1,
        lease_id="L-200",
        fencing_token="fence-200",
        session_id="session-200",
        worker_id="worker-tmux-01",
    )


def test_tmux_detect_and_health_missing():
    adapter = TmuxRuntimeAdapter(binary_path="/nonexistent/path/tmux")
    assert adapter.detect() is False
    health = adapter.health()
    assert health.available is False
    assert health.healthy is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/tmux")
def test_tmux_health_success(mock_which, mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="tmux 3.4\n", stderr="")
    adapter = TmuxRuntimeAdapter()
    assert adapter.detect() is True
    health = adapter.health()
    assert health.available is True
    assert health.healthy is True
    assert health.version == "tmux 3.4"


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/tmux")
def test_tmux_spawn_and_read(mock_which, mock_run, sample_identity):
    mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\nline3\n", stderr="")
    adapter = TmuxRuntimeAdapter()
    req = SpawnRequest(
        identity=sample_identity,
        command=["python3", "test.py"],
        cwd="/tmp",
    )
    status = adapter.spawn(req)
    assert status.state == ProcessState.RUNNING
    assert status.alive is True

    output = adapter.read(sample_identity, lines=2)
    assert output == "line2\nline3"


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/tmux")
def test_tmux_status_running_and_completed(mock_which, mock_run, sample_identity):
    adapter = TmuxRuntimeAdapter()

    # has-session succeeds -> RUNNING
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    status = adapter.status(sample_identity)
    assert status.state == ProcessState.RUNNING
    assert status.alive is True

    # has-session fails -> COMPLETED
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="can't find session")
    status = adapter.status(sample_identity)
    assert status.state == ProcessState.COMPLETED
    assert status.alive is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/bin/tmux")
def test_tmux_terminate(mock_which, mock_run, sample_identity):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    adapter = TmuxRuntimeAdapter()
    res = adapter.terminate(sample_identity)
    assert res is True
