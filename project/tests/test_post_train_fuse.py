"""
project/tests/test_post_train_fuse.py
====================================
Unit tests for the post-training fusion + deployment script pipeline.
"""

from pathlib import Path
from unittest.mock import MagicMock

from scripts import post_train_fuse


def test_verify_adapter_accepts_expected_filenames(tmp_path):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()

    # canonical
    (adapter_dir / "adapters.safetensors").write_text("weights", encoding="utf-8")
    assert post_train_fuse.verify_adapter(adapter_dir, dry_run=False) is True

    # alternate names should also work
    alt_dir = tmp_path / "adapter_alt"
    alt_dir.mkdir()
    (alt_dir / "adapter.safetensors").write_text("weights", encoding="utf-8")
    assert post_train_fuse.verify_adapter(alt_dir, dry_run=False) is True


def test_verify_adapter_dry_run_keeps_going_when_missing(tmp_path):
    missing = tmp_path / "missing"
    assert post_train_fuse.verify_adapter(missing, dry_run=True) is True
    assert post_train_fuse.verify_adapter(missing, dry_run=False) is False


def test_fuse_adapter_dry_run_only(tmp_path):
    fused = tmp_path / "fused"
    assert post_train_fuse.fuse_adapter("base/model", tmp_path / "nope", fused, dry_run=True) is True


def test_convert_to_gguf_dry_run_when_converter_absent(tmp_path):
    fused = tmp_path / "fused"
    gguf = tmp_path / "model.gguf"
    # No converter on disk in this test; dry-run should continue.
    assert post_train_fuse.convert_to_gguf(fused, gguf, dry_run=True) is True


def test_convert_to_gguf_with_stubbed_converter_calls_subprocess(monkeypatch, tmp_path):
    fused = tmp_path / "fused"
    gguf = tmp_path / "model.gguf"
    converter = tmp_path / "convert_hf_to_gguf.py"
    converter.write_text("", encoding="utf-8")

    monkeypatch.setattr(post_train_fuse, "LLAMA_CPP_CANDIDATES", [converter])

    ran = {}

    def fake_run(cmd, check=True):
        ran["called"] = True
        ran["cmd"] = cmd
        gguf.write_bytes(b"fake gguf payload")
        return MagicMock(returncode=0)

    monkeypatch.setattr(post_train_fuse.subprocess, "run", fake_run)

    assert post_train_fuse.convert_to_gguf(fused, gguf, dry_run=False) is True
    assert ran["called"] is True
    assert any(str(fused) in part for part in ran["cmd"])


def test_create_ollama_model_dry_run(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text("FROM test", encoding="utf-8")
    assert post_train_fuse.create_ollama_model(modelfile, "qwen2.5-bazi", tmp_path / "model.gguf", dry_run=True) is True


def test_create_ollama_model_fails_without_ollama_or_gguf(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text("FROM test", encoding="utf-8")

    gguf = tmp_path / "model.gguf"
    # File absent and non-dry-run path should fail when Ollama CLI is unavailable.
    assert post_train_fuse.create_ollama_model(modelfile, "qwen2.5-bazi", gguf, dry_run=False) is False

    # Ensure missing Modelfile also fails.
    gguf.write_text("", encoding="utf-8")
    assert post_train_fuse.create_ollama_model(tmp_path / "missing", "qwen2.5-bazi", gguf, dry_run=False) is False
