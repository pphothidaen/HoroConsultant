"""
Atomic file operations with advisory locks for shared manifests.
Prevents race conditions when multiple subagents update provenance files.
"""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from typing import Any


@contextmanager
def file_lock(filepath: str, exclusive: bool = True, timeout: float = 10.0):
    """
    Advisory file lock context manager.
    Prevents concurrent writes to shared manifest files.

    Usage:
        with file_lock("plans/test_provenance/manifest.json"):
            atomic_write_json("plans/test_provenance/manifest.json", data)
    """
    start = time.time()
    lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH

    with open(filepath, "a+") as f:
        while True:
            try:
                fcntl.flock(f.fileno(), lock_type | fcntl.LOCK_NB)
                break
            except (IOError, OSError):
                if time.time() - start > timeout:
                    raise TimeoutError(f"Could not acquire lock on {filepath}")
                time.sleep(0.1)

        try:
            yield f
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Atomically write JSON to file with locking.
    Used for provenance manifests and test results.
    """
    with file_lock(filepath, exclusive=True):
        # Write to temp file first
        tmp_path = f"{filepath}.tmp.{os.getpid()}"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename
        os.replace(tmp_path, filepath)


def atomic_write_text(filepath: str, content: str) -> None:
    """
    Atomically write text to file with locking.
    """
    with file_lock(filepath, exclusive=True):
        tmp_path = f"{filepath}.tmp.{os.getpid()}"
        with open(tmp_path, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)


def safe_read_json(filepath: str) -> Any:
    """
    Safely read JSON from a locked file.
    Returns None if file doesn't exist.
    """
    if not os.path.exists(filepath):
        return None

    with file_lock(filepath, exclusive=False):
        with open(filepath, "r") as f:
            return json.load(f)
