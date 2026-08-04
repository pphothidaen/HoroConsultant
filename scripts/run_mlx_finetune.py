#!/usr/bin/env python3
"""
scripts/run_mlx_finetune.py
============================
MLX LoRA Fine-Tune Runner for Qwen2.5-7B on macOS Apple Silicon.

Wraps mlx_lm.lora with sane defaults for BaZi domain adaptation.
Handles dataset path resolution, progress logging, and post-fuse steps.

Usage
-----
    # Basic run (uses project/rag/datasets/ or project/data/mlx_finetune/)
    python scripts/run_mlx_finetune.py

    # Custom dataset
    python scripts/run_mlx_finetune.py --dataset project/rag/datasets/train.jsonl

    # Resume from checkpoint
    python scripts/run_mlx_finetune.py --resume --adapter-path project/models/qwen2.5-bazi-adapter

    # Dry-run (show config only)
    python scripts/run_mlx_finetune.py --dry-run

Requirements (macOS Apple Silicon only)
-----------------------------------------
    pip install mlx mlx-lm huggingface_hub
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Defaults (from .env or fallback)
# ---------------------------------------------------------------------------

# QLoRA in mlx_lm works by loading a pre-quantized model (4-bit) and applying
# LoRA adapters on top. Using the FP16 base model (14GB) will OOM on 16GB RAM.
DEFAULT_MODEL        = os.getenv("BASE_MODEL_NAME", "mlx-community/Qwen2.5-7B-Instruct-4bit")
DEFAULT_ADAPTER_PATH = Path(os.getenv("ADAPTER_PATH", str(ROOT / "project" / "models" / "qwen2.5-bazi-adapter")))
DEFAULT_ITERS        = 600
DEFAULT_BATCH        = 1
DEFAULT_LORA_LAYERS  = 8
DEFAULT_LR           = 2e-5
DEFAULT_SAVE_EVERY   = 100
DEFAULT_VAL_BATCHES  = 25
DEFAULT_GRAD_ACCUM   = 4
DEFAULT_MAX_SEQ_LEN  = 1024
DEFAULT_LORA_CONFIG  = ROOT / "project" / "models" / "lora_config.yaml"

# Dataset resolution order
DATASET_CANDIDATES = [
    ROOT / "project" / "rag"  / "datasets",          # plan path (preferred)
    ROOT / "project" / "data" / "mlx_finetune",       # current path
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_dataset(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p.parent
        if p.is_dir():
            return p
        raise FileNotFoundError(f"Dataset not found: {explicit}")

    for candidate in DATASET_CANDIDATES:
        train = candidate / "train.jsonl"
        if train.exists():
            return candidate

    raise FileNotFoundError(
        "No dataset found. Run one of:\n"
        "  python scripts/extract_dataset_mlx.py\n"
        "  python project/rag/ingest_vault.py --export-finetune"
    )


def _check_mlx() -> bool:
    try:
        import mlx         # type: ignore  # noqa
        import mlx_lm      # type: ignore  # noqa
        return True
    except ImportError:
        return False


def _print_config(cfg: dict) -> None:
    print("\n" + "=" * 60)
    print("  MLX LoRA Fine-Tune Configuration")
    print("=" * 60)
    for k, v in cfg.items():
        print(f"  {k:<22}: {v}")
    print("=" * 60 + "\n")


def _count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in open(path, encoding="utf-8"))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MLX LoRA Fine-Tune Runner for Qwen2.5-BaZi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset",       default=None,  help="Path to dataset dir or train.jsonl")
    parser.add_argument("--model",         default=DEFAULT_MODEL)
    parser.add_argument("--adapter-path",  default=str(DEFAULT_ADAPTER_PATH))
    parser.add_argument("--iters",         default=DEFAULT_ITERS, type=int)
    parser.add_argument("--batch-size",    default=DEFAULT_BATCH, type=int)
    parser.add_argument("--lora-layers",   default=DEFAULT_LORA_LAYERS, type=int)
    parser.add_argument("--lr",            default=DEFAULT_LR, type=float)
    parser.add_argument("--save-every",    default=DEFAULT_SAVE_EVERY, type=int)
    parser.add_argument("--val-batches",   default=DEFAULT_VAL_BATCHES, type=int)
    parser.add_argument("--grad-accum",    default=DEFAULT_GRAD_ACCUM, type=int, help="Gradient accumulation steps")
    parser.add_argument("--max-seq-length",default=DEFAULT_MAX_SEQ_LEN, type=int, help="Max sequence length")
    parser.add_argument("--lora-config",   default=str(DEFAULT_LORA_CONFIG), help="YAML config for lora_parameters (rank, scale, dropout)")
    parser.add_argument("--grad-checkpoint", action="store_true", default=True, help="Enable gradient checkpointing")
    parser.add_argument("--no-grad-checkpoint", action="store_false", dest="grad_checkpoint", help="Disable gradient checkpointing")
    parser.add_argument("--resume",        action="store_true", help="Resume from existing adapter")
    parser.add_argument("--dry-run",       action="store_true", help="Show config without running")
    parser.add_argument("--fuse-after",    action="store_true", help="Auto-fuse adapter after training")
    parser.add_argument("--test",          action="store_true", help="Run evaluation on test set after training")
    args = parser.parse_args()

    print("\n🚀 Qwen2.5-BaZi MLX Fine-Tuning Pipeline")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Check MLX
    mlx_available = _check_mlx()
    if not mlx_available:
        print("⚠️  MLX package not installed in current environment.")
        print("   (Install with `pip install mlx mlx-lm` on macOS Apple Silicon)")
        if not args.dry_run:
            sys.exit(1)
    else:
        print("✅ MLX available")

    # 2. Resolve dataset
    dataset_dir = _resolve_dataset(args.dataset)
    train_path  = dataset_dir / "train.jsonl"
    valid_path  = dataset_dir / "valid.jsonl"

    n_train = _count_lines(train_path)
    n_valid = _count_lines(valid_path) if valid_path.exists() else 0
    print(f"✅ Dataset: {dataset_dir}")
    print(f"   Train: {n_train} entries | Valid: {n_valid} entries")

    if n_train == 0:
        print("\n❌ train.jsonl is empty. Run dataset extraction first.")
        sys.exit(1)

    # 3. Build config
    adapter_path = Path(args.adapter_path)
    adapter_path.mkdir(parents=True, exist_ok=True)

    config = {
        "model":           args.model,
        "train_data":      str(train_path),
        "valid_data":      str(valid_path),
        "adapter_path":    str(adapter_path),
        "iters":           args.iters,
        "batch_size":      args.batch_size,
        "lora_layers":     args.lora_layers,
        "learning_rate":   args.lr,
        "save_every":      args.save_every,
        "val_batches":     args.val_batches,
        "grad_accum":      args.grad_accum,
        "max_seq_length":  args.max_seq_length,
        "lora_config":     args.lora_config,
        "grad_checkpoint": args.grad_checkpoint,
        "resume":          args.resume,
        "test":            args.test,
    }
    _print_config(config)

    # Save config snapshot
    config_snap = adapter_path / "run_config.json"
    config_snap.write_text(
        json.dumps({**config, "started_at": datetime.now().isoformat()}, indent=2),
        encoding="utf-8"
    )

    if args.dry_run:
        print("🔎 Dry-run mode — command that would execute:")
        _print_lora_command(config)
        return

    # 4. Run mlx_lm.lora
    print("▶️  Starting LoRA fine-tuning…")
    cmd = _build_lora_command(config)
    print(f"   $ {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fine-tuning failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user — checkpoint saved in adapter_path")
        sys.exit(0)

    print(f"\n✅ Fine-tuning complete → {adapter_path}")

    # 5. Optional: fuse adapter
    if args.fuse_after:
        _fuse_adapter(args.model, str(adapter_path))


def _build_lora_command(cfg: dict) -> list[str]:
    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model",                cfg["model"],
        "--train",
        "--data",                 str(Path(cfg["train_data"]).parent),
        "--iters",                str(cfg["iters"]),
        "--batch-size",           str(cfg["batch_size"]),
        "--num-layers",           str(cfg["lora_layers"]),
        "--learning-rate",        str(cfg["learning_rate"]),
        "--adapter-path",         cfg["adapter_path"],
        "--val-batches",          str(cfg["val_batches"]),
        "--save-every",           str(cfg["save_every"]),
        "--grad-accumulation-steps", str(cfg["grad_accum"]),
        "--max-seq-length",       str(cfg["max_seq_length"]),
    ]
    # Pass lora_parameters (rank, scale, dropout) via YAML config file
    lora_config = cfg.get("lora_config")
    if lora_config and Path(lora_config).exists():
        cmd.extend(["-c", str(lora_config)])
    if cfg.get("grad_checkpoint"):
        cmd.append("--grad-checkpoint")
    if cfg.get("resume"):
        cmd.append("--resume-adapter-file")
        cmd.append(str(Path(cfg["adapter_path"]) / "adapters.safetensors"))
    if cfg.get("test"):
        cmd.append("--test")
    return cmd


def _print_lora_command(cfg: dict) -> None:
    cmd = _build_lora_command(cfg)
    print("   " + " \\\n     ".join(cmd))


def _fuse_adapter(model: str, adapter_path: str) -> None:
    fused_path = str(Path(adapter_path).parent / "qwen2.5-bazi-fused")
    print(f"\n🔗 Fusing adapter → {fused_path}")
    cmd = [
        sys.executable, "-m", "mlx_lm.fuse",
        "--model",        model,
        "--adapter-path", adapter_path,
        "--save-path",    fused_path,
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Fused model saved → {fused_path}")
        print("\nNext: Convert to GGUF for Ollama:")
        print(f"  cd llama.cpp && python convert_hf_to_gguf.py {fused_path} \\")
        print(f"    --outfile project/models/qwen2.5-bazi.gguf --outtype q4_k_m")
        print(f"  ollama create qwen2.5-bazi -f project/models/Modelfile")
    except subprocess.CalledProcessError as e:
        print(f"❌ Fuse failed: {e.returncode}")


if __name__ == "__main__":
    main()
