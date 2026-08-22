"""
tests/test_publish_space_hf.py
================================
Unit & Integration Tests for Hugging Face Spaces Deployment Publisher.

Tests:
1. Static payload audit validation (Dockerfile.hf, requirements.txt, project/)
2. File filter logic (ignoring models/*, kaggle_kernel/*, *.safetensors)
3. Dry-run function execution without errors
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.publish_space_hf import audit_payload, publish_space, should_ignore


def test_should_ignore_patterns():
    """Verify that heavy model files and cache directories are properly ignored."""
    assert should_ignore("project/models/qwen2.5-bazi-fused/model.safetensors") is True
    assert should_ignore("project/kaggle_kernel/notebook.ipynb") is True
    assert should_ignore("project/__pycache__/main.cpython-311.pyc") is True
    assert should_ignore("project/core/multi_agent_debate.py") is False
    assert should_ignore("project/main.py") is False


def test_audit_payload_integrity():
    """Verify payload audit structure and required files check."""
    is_valid, summary = audit_payload()
    assert is_valid is True
    assert summary["dockerfile_valid"] is True
    assert summary["requirements_valid"] is True
    assert summary["project_valid"] is True
    assert summary["total_files"] > 0
    assert summary["total_bytes"] > 0


def test_docker_build_context_dependencies_exist():
    """Dockerfile COPY sources must be present in the published repository payload."""
    dockerfile = (ROOT / "Dockerfile.hf").read_text(encoding="utf-8")
    assert (ROOT / ".env.example").is_file()
    assert (ROOT / "scripts").is_dir()
    assert (ROOT / "tests").is_dir()
    assert (ROOT / "rust_core" / "Cargo.toml").is_file()
    assert (ROOT / "rust_core" / "tests").is_dir()
    assert "COPY --chown=user:user scripts/" in dockerfile
    assert "COPY --chown=user:user tests/" in dockerfile
    assert "COPY --chown=user:user .env.example" in dockerfile
    assert "maturin build --locked --release" in dockerfile
    assert "COPY rust_core/Cargo.toml" in dockerfile
    assert "COPY rust_core/tests" in dockerfile
    assert "python3-venv patchelf" in dockerfile


def test_publish_space_dry_run():
    """Verify dry-run mode returns True without throwing exception."""
    result = publish_space("pphothidaen/test-horoconsultant-backend", dry_run=True)
    assert result is True
