"""Unit tests for HerdrRuntimeAdapter (AT-02)."""

from unittest.mock import MagicMock, patch
import pytest

from project.core.execution_identity import ExecutionIdentity
from project.core.runtime_herdr import HerdrRuntimeAdapter
from project.core.worker_runtime import ProcessState, SpawnRequest


@pytest.fixture
def sample_identity():
    return ExecutionIdentity(
        execution_id="exec-100",
        ticket_id="KAN-100",
        attempt=1,
        lease_id="L-100",
        fencing_token="fence-100",
        session_id="session-100",
        worker_id="worker-01",
    )


def test_herdr_detect_and_health_missing():
    adapter = HerdrRuntimeAdapter(binary_path="/nonexistent/path/herdr")
    assert adapter.detect() is False
    health = adapter.health()
    assert health.available is False
    assert health.healthy is False


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/local/bin/herdr")
def test_herdr_health_success(mock_which, mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="herdr 0.6.9\n", stderr="")
    adapter = HerdrRuntimeAdapter()
    assert adapter.detect() is True
    health = adapter.health()
    assert health.available is True
    assert health.healthy is True
    assert health.version == "herdr 0.6.9"


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/local/bin/herdr")
def test_herdr_spawn_and_read(mock_which, mock_run, sample_identity):
    mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\n", stderr="")
    adapter = HerdrRuntimeAdapter()
    req = SpawnRequest(
        identity=sample_identity,
        command=["python3", "script.py"],
        cwd="/tmp",
    )
    status = adapter.spawn(req)
    assert status.state == ProcessState.RUNNING
    assert status.alive is True

    output = adapter.read(sample_identity, lines=10)
    assert "line1" in output


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/local/bin/herdr")
def test_herdr_status_state_mapping(mock_which, mock_run, sample_identity):
    adapter = HerdrRuntimeAdapter()

    # Working state
    mock_run.return_value = MagicMock(returncode=0, stdout="Agent is working on tests", stderr="")
    status = adapter.status(sample_identity)
    assert status.state == ProcessState.WORKING
    assert status.alive is True

    # Blocked state
    mock_run.return_value = MagicMock(returncode=0, stdout="Agent is blocked on input", stderr="")
    status = adapter.status(sample_identity)
    assert status.state == ProcessState.BLOCKED
    assert status.alive is True


@patch("subprocess.run")
@patch("shutil.which", return_value="/usr/local/bin/herdr")
def test_herdr_terminate(mock_which, mock_run, sample_identity):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    adapter = HerdrRuntimeAdapter()
    res = adapter.terminate(sample_identity)
    assert res is True
