"""Collector for AI agent quota observations.

Spawns observation probe subprocess in its own process group, enforces a 64 KB
stream limit, enforces timeout with clean process group termination, detects
auth failures (401 / authentication_failed), and returns parsed observation dict
or structured error dictionaries.

Pure ASCII formatting enforced.
"""

from __future__ import annotations

import fcntl
import json
import os
import select
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Union


class QuotaCollector:
    """Collects quota observation from CLI / stdio probe in a fail-closed manner."""

    def __init__(self, default_command: Optional[List[str]] = None) -> None:
        self.default_command = default_command or ["codex", "app-server", "--stdio"]

    def collect_quota_observation(
        self,
        timeout_seconds: Union[int, float] = 10,
        command: Optional[List[str]] = None,
        max_stream_bytes: int = 65536,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute quota collection probe with strict timeout and stream limits."""
        cmd = command or self.default_command
        if not isinstance(cmd, list):
            cmd = list(cmd)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except (FileNotFoundError, PermissionError) as exc:
            return {
                "reason_code": "COLLECTOR_PROCESS_SPAWN_ERROR",
                "exit_code": 3,
                "error": f"Failed to spawn process: {exc}",
            }
        except OSError as exc:
            return {
                "reason_code": "COLLECTOR_PROCESS_SPAWN_ERROR",
                "exit_code": 3,
                "error": f"OS error spawning process: {exc}",
            }
        except Exception as exc:
            return {
                "reason_code": "COLLECTOR_TRANSPORT_ERROR",
                "exit_code": 3,
                "error": f"Transport error: {exc}",
            }

        stdout_chunks: List[bytes] = []
        stderr_chunks: List[bytes] = []
        total_stdout_bytes = 0
        total_stderr_bytes = 0
        start_time = time.monotonic()

        def _kill_pg() -> None:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                proc.wait(timeout=1.0)
            except Exception:
                pass

        try:
            for pipe in (proc.stdout, proc.stderr):
                if pipe is not None:
                    fl = fcntl.fcntl(pipe.fileno(), fcntl.F_GETFL)
                    fcntl.fcntl(pipe.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

            pipes = [p for p in (proc.stdout, proc.stderr) if p is not None]

            while True:
                elapsed = time.monotonic() - start_time
                remaining = timeout_seconds - elapsed
                if remaining <= 0:
                    _kill_pg()
                    return {
                        "reason_code": "COLLECTOR_TIMEOUT",
                        "exit_code": 3,
                        "error": "Collector timed out",
                    }

                if not pipes:
                    break

                ready, _, _ = select.select(pipes, [], [], min(max(remaining, 0.01), 0.1))
                for r in ready:
                    try:
                        chunk = r.read(4096)
                    except (BlockingIOError, OSError):
                        continue

                    if not chunk:
                        pipes.remove(r)
                        continue

                    if r is proc.stdout:
                        total_stdout_bytes += len(chunk)
                        stdout_chunks.append(chunk)
                        if total_stdout_bytes > max_stream_bytes:
                            _kill_pg()
                            return {
                                "reason_code": "COLLECTOR_OVERSIZED_RESPONSE",
                                "exit_code": 3,
                                "error": f"Stream limit {max_stream_bytes} exceeded",
                            }
                    elif r is proc.stderr:
                        total_stderr_bytes += len(chunk)
                        stderr_chunks.append(chunk)
                        if total_stderr_bytes > max_stream_bytes:
                            _kill_pg()
                            return {
                                "reason_code": "COLLECTOR_OVERSIZED_RESPONSE",
                                "exit_code": 3,
                                "error": f"Stream limit {max_stream_bytes} exceeded",
                            }

                if proc.poll() is not None:
                    for p in list(pipes):
                        try:
                            while True:
                                chunk = p.read(4096)
                                if not chunk:
                                    break
                                if p is proc.stdout:
                                    total_stdout_bytes += len(chunk)
                                    stdout_chunks.append(chunk)
                                    if total_stdout_bytes > max_stream_bytes:
                                        _kill_pg()
                                        return {
                                            "reason_code": "COLLECTOR_OVERSIZED_RESPONSE",
                                            "exit_code": 3,
                                            "error": f"Stream limit {max_stream_bytes} exceeded",
                                        }
                                elif p is proc.stderr:
                                    total_stderr_bytes += len(chunk)
                                    stderr_chunks.append(chunk)
                                    if total_stderr_bytes > max_stream_bytes:
                                        _kill_pg()
                                        return {
                                            "reason_code": "COLLECTOR_OVERSIZED_RESPONSE",
                                            "exit_code": 3,
                                            "error": f"Stream limit {max_stream_bytes} exceeded",
                                        }
                        except (BlockingIOError, OSError):
                            pass
                    break

        except Exception as exc:
            _kill_pg()
            return {
                "reason_code": "COLLECTOR_TRANSPORT_ERROR",
                "exit_code": 3,
                "error": f"Transport error: {exc}",
            }
        finally:
            if proc.poll() is None:
                _kill_pg()

        stdout_bytes = b"".join(stdout_chunks)
        stderr_bytes = b"".join(stderr_chunks)
        stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()
        combined_str = (stdout_str + "\n" + stderr_str).strip()

        if (
            "authentication_failed" in combined_str
            or "HTTP 401" in combined_str
            or "status\": 401" in combined_str
            or "status: 401" in combined_str
        ):
            return {
                "reason_code": "COLLECTOR_AUTH_FAILURE",
                "exit_code": 3,
                "error": "Authentication failed",
            }

        try:
            payload = json.loads(stdout_str)
        except Exception as exc:
            return {
                "reason_code": "PAYLOAD_DECODE_ERROR",
                "exit_code": 3,
                "error": f"Failed to decode JSON payload: {exc}",
            }

        if not isinstance(payload, dict):
            return {
                "reason_code": "PAYLOAD_NOT_OBJECT",
                "exit_code": 3,
                "error": "Payload is not a JSON object",
            }

        if (
            payload.get("error") == "authentication_failed"
            or payload.get("status") == 401
            or payload.get("statusCode") == 401
        ):
            return {
                "reason_code": "COLLECTOR_AUTH_FAILURE",
                "exit_code": 3,
                "error": "Authentication failed",
            }

        return payload
