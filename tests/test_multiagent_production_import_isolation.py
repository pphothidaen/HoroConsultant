"""Dispatch must work in a fresh interpreter without test collection patches."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_clean_process_qobs_validation_and_collection_preserve_production():
    # Importing tests must never supply or replace dispatch runtime functions.
    result = subprocess.run(
        [sys.executable, "-c", """
import runpy
from types import SimpleNamespace
import scripts.multiagent_prompt_command as command
names = (
    '_qobs_admission_binding', '_validate_qobs_invocation_binding',
    '_consume_spawn_capacity', '_release_spawn_capacity',
    '_execute_invocation_locked',
)
before = {name: getattr(command, name, None) for name in names}
assert all(callable(value) for value in before.values()), 'production dispatch helpers missing'
assert command._validate_qobs_invocation_binding(SimpleNamespace(qobs_admission=None)) is None
runpy.run_path('tests/test_multiagent_prompt_command.py')
assert all(getattr(command, name) is value for name, value in before.items()), 'test import replaced production dispatch'
"""],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
