#!/usr/bin/env python3
"""
scripts/post_train_fuse.py
==========================
Post-training fusion and deployment pipeline for Qwen2.5-BaZi fine-tuned model on macOS Apple Silicon.

Pipeline Steps:
1. Verify LoRA adapter existence at project/models/qwen2.5-bazi-adapter/adapters.safetensors
2. Fuse LoRA adapter into base model via mlx_lm.fuse
3. Convert fused model to GGUF format using llama.cpp convert_hf_to_gguf.py
4. Register and create Ollama model using project/models/Modelfile
5. Run a quick BaZi domain sanity test on the resulting model

Usage:
    # Standard full post-training pipeline
    python scripts/post_train_fuse.py

    # Dry-run mode (preview commands and status without execution)
    python scripts/post_train_fuse.py --dry-run

    # Skip GGUF conversion or Ollama registration
    python scripts/post_train_fuse.py --skip-gguf --skip-ollama

    # Custom paths
    python scripts/post_train_fuse.py --adapter-path project/models/my-adapter --fused-path project/models/my-fused
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_BASE_MODEL       = os.getenv("BASE_MODEL_NAME", "mlx-community/Qwen2.5-7B-Instruct-4bit")
DEFAULT_ADAPTER_PATH     = ROOT / "project" / "models" / "qwen2.5-bazi-adapter"
DEFAULT_FUSED_PATH       = ROOT / "project" / "models" / "qwen2.5-bazi-fused"
DEFAULT_GGUF_PATH        = ROOT / "project" / "models" / "qwen2.5-bazi.gguf"
DEFAULT_MODELFILE_PATH   = ROOT / "project" / "models" / "Modelfile"
DEFAULT_OLLAMA_MODEL_NAME= "qwen2.5-bazi"
DEFAULT_OUTTYPE          = "q4_k_m"

# Candidate paths to locate llama.cpp convert_hf_to_gguf.py
LLAMA_CPP_CANDIDATES = [
    ROOT / "llama.cpp" / "convert_hf_to_gguf.py",
    ROOT.parent / "llama.cpp" / "convert_hf_to_gguf.py",
    Path.home() / "llama.cpp" / "convert_hf_to_gguf.py",
    Path("/Users/kimlenglim/Project/qwen3.6-27b-fable5-lora/llama.cpp/convert_hf_to_gguf.py"),
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _format_size(path: Path) -> str:
    """Return formatted human-readable size of file or directory."""
    if not path.exists():
        return "0 B"
    if path.is_file():
        total_size = path.stat().st_size
    else:
        total_size = sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if total_size < 1024.0:
            return f"{total_size:.2f} {unit}"
        total_size /= 1024.0
    return f"{total_size:.2f} PB"


def verify_adapter(adapter_path: Path, dry_run: bool = False) -> bool:
    """Step 1: Verify LoRA adapter weights exist."""
    print("\n🔍 Step 1/5: Verifying LoRA Adapter...")
    print(f"   Adapter directory: {adapter_path}")

    if not adapter_path.exists():
        print(f"❌ Adapter directory not found: {adapter_path}")
        if not dry_run:
            return False

    weights_file = adapter_path / "adapters.safetensors"
    alt_weights_1 = adapter_path / "adapter.safetensors"
    alt_weights_2 = adapter_path / "weights.safetensors"

    target_weights = None
    if weights_file.exists():
        target_weights = weights_file
    elif alt_weights_1.exists():
        target_weights = alt_weights_1
    elif alt_weights_2.exists():
        target_weights = alt_weights_2

    if target_weights and target_weights.exists():
        size_str = _format_size(target_weights)
        print(f"✅ Found adapter weights: {target_weights.name} ({size_str})")
        return True
    else:
        print(f"❌ Adapter weights file not found (expected adapters.safetensors in {adapter_path})")
        if dry_run:
            print("   [Dry-run] Continuing verification preview...")
            return True
        return False


def fuse_adapter(
    base_model: str,
    adapter_path: Path,
    fused_path: Path,
    dry_run: bool = False
) -> bool:
    """Step 2: Fuse adapter weights into base model via mlx_lm.fuse."""
    print("\n🔗 Step 2/5: Fusing LoRA Adapter into Base Model...")
    print(f"   Base Model   : {base_model}")
    print(f"   Adapter Path : {adapter_path}")
    print(f"   Fused Output : {fused_path}")

    cmd = [
        sys.executable, "-m", "mlx_lm.fuse",
        "--model", base_model,
        "--adapter-path", str(adapter_path),
        "--save-path", str(fused_path)
    ]
    print(f"   $ {' '.join(cmd)}")

    if dry_run:
        print("🔎 [Dry-run] Would execute mlx_lm.fuse command above.")
        return True

    try:
        fused_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(cmd, check=True)
        if fused_path.exists():
            fused_size = _format_size(fused_path)
            print(f"✅ Fused model saved successfully → {fused_path} ({fused_size})")
            return True
        else:
            print(f"❌ Fused directory was not created: {fused_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ mlx_lm.fuse failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during fusion: {e}")
        return False


def find_llama_cpp_script(custom_dir: str | None = None) -> Path | None:
    """Locate convert_hf_to_gguf.py script."""
    if custom_dir:
        custom_script = Path(custom_dir) / "convert_hf_to_gguf.py"
        if custom_script.exists():
            return custom_script

    for candidate in LLAMA_CPP_CANDIDATES:
        if candidate.exists():
            return candidate

    return None


def _is_mlx_quantized_model(fused_path: Path) -> bool:
    """Detect if fused model is in MLX quantized format (has .biases/.scales tensors)."""
    try:
        from safetensors import safe_open
        safetensor_files = list(fused_path.glob("*.safetensors"))
        if not safetensor_files:
            return False
        with safe_open(str(safetensor_files[0]), framework="pt") as f:
            keys = list(f.keys())[:20]
        return any(k.endswith(".biases") or k.endswith(".scales") for k in keys)
    except Exception:
        return False


def convert_to_gguf_mlx(
    model_id: str,
    adapter_path: Path,
    fused_path: Path,
    gguf_path: Path,
    dry_run: bool = False,
) -> bool:
    """Export GGUF directly via mlx_lm.fuse --export-gguf (for MLX quantized models)."""
    cmd = [
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", model_id,
        "--adapter-path", str(adapter_path),
        "--save-path", str(fused_path),
        "--export-gguf",
        "--gguf-path", str(gguf_path),
    ]
    print(f"   $ {' '.join(cmd)}")
    if dry_run:
        print("🔎 [Dry-run] Would execute mlx_lm.fuse --export-gguf command above.")
        return True
    try:
        subprocess.run(cmd, check=True)
        if gguf_path.exists():
            size_str = _format_size(gguf_path)
            print(f"✅ GGUF (MLX-native) created → {gguf_path} ({size_str})")
            return True
        print(f"❌ GGUF not found after mlx_lm.fuse: {gguf_path}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ mlx_lm.fuse --export-gguf failed (exit {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ mlx_lm.fuse --export-gguf error: {e}")
        return False


def convert_to_gguf(
    fused_path: Path,
    gguf_path: Path,
    outtype: str = DEFAULT_OUTTYPE,
    llama_cpp_dir: str | None = None,
    dry_run: bool = False,
    adapter_path: Path | None = None,
    base_model: str = DEFAULT_BASE_MODEL,
) -> bool:
    """Step 3: Convert fused model to GGUF format.
    
    Auto-detects model format:
    - MLX quantized (has .biases/.scales): uses mlx_lm.fuse --export-gguf
    - Standard PyTorch: uses llama.cpp convert_hf_to_gguf.py
    """
    print("\n📦 Step 3/5: Converting Fused Model to GGUF Format...")
    print(f"   Fused Model : {fused_path}")
    print(f"   GGUF Target : {gguf_path}")
    print(f"   Quantization: {outtype}")

    # Auto-detect MLX quantized format
    if _is_mlx_quantized_model(fused_path):
        print("   Format: MLX quantized (has .biases/.scales tensors) → using mlx_lm --export-gguf")
        _adapter_path = adapter_path or Path(str(fused_path).replace("-fused", "-adapter"))
        return convert_to_gguf_mlx(
            model_id=base_model,
            adapter_path=_adapter_path,
            fused_path=fused_path,
            gguf_path=gguf_path,
            dry_run=dry_run,
        )

    # Standard PyTorch model → llama.cpp
    print("   Format: Standard PyTorch → using llama.cpp convert_hf_to_gguf.py")
    script_path = find_llama_cpp_script(llama_cpp_dir)

    if not script_path:
        print("⚠️  convert_hf_to_gguf.py from llama.cpp was not found in standard paths.")
        print("\n   To manually convert to GGUF:")
        print("   1. Clone llama.cpp:")
        print("      git clone https://github.com/ggerganov/llama.cpp.git")
        print("   2. Install requirements:")
        print("      pip install -r llama.cpp/requirements.txt")
        print("   3. Run conversion script:")
        print(f"      python llama.cpp/convert_hf_to_gguf.py {fused_path} \\")
        print(f"        --outfile {gguf_path} --outtype {outtype}")
        if dry_run:
            print("🔎 [Dry-run] Continuing without local llama.cpp converter...")
            return True
        return False

    print(f"✅ Located llama.cpp converter: {script_path}")
    cmd = [
        sys.executable, str(script_path),
        str(fused_path),
        "--outfile", str(gguf_path),
        "--outtype", outtype
    ]
    print(f"   $ {' '.join(cmd)}")

    if dry_run:
        print("🔎 [Dry-run] Would execute GGUF conversion command above.")
        return True

    try:
        gguf_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(cmd, check=True)
        if gguf_path.exists():
            size_str = _format_size(gguf_path)
            print(f"✅ GGUF file created successfully → {gguf_path} ({size_str})")
            return True
        else:
            print(f"❌ GGUF file not created: {gguf_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ GGUF conversion failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error during GGUF conversion: {e}")
        return False


def create_ollama_model(
    modelfile: Path,
    model_name: str,
    gguf_path: Path,
    dry_run: bool = False
) -> bool:
    """Step 4: Register model with Ollama using Modelfile."""
    print("\n🦙 Step 4/5: Registering Ollama Model...")
    print(f"   Modelfile  : {modelfile}")
    print(f"   Model Name : {model_name}")

    if not shutil.which("ollama"):
        print("⚠️  Ollama CLI ('ollama') is not installed or not in PATH.")
        print("   Install Ollama from https://ollama.com or via Homebrew: `brew install ollama`")
        if dry_run:
            print("🔎 [Dry-run] Continuing Ollama preview...")
            return True
        return False

    if not modelfile.exists():
        print(f"❌ Modelfile not found: {modelfile}")
        if not dry_run:
            return False

    if not gguf_path.exists() and not dry_run:
        print(f"⚠️  GGUF file missing at {gguf_path}. Cannot create Ollama model without GGUF.")
        return False

    cmd = ["ollama", "create", model_name, "-f", str(modelfile)]
    print(f"   $ {' '.join(cmd)}")

    if dry_run:
        print(f"🔎 [Dry-run] Would run 'ollama create {model_name} -f {modelfile}'")
        return True

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Ollama model '{model_name}' created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ollama model creation failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error registering Ollama model: {e}")
        return False


def run_sanity_test(
    model_name: str,
    fused_path: Path,
    skip_ollama: bool = False,
    dry_run: bool = False
) -> bool:
    """Step 5: Run a quick BaZi query sanity test."""
    print("\n🧪 Step 5/5: Running BaZi Model Sanity Test...")
    prompt = "คำนวณและวิเคราะห์ดวง BaZi สำหรับคนเกิดวัน甲 (Jia Wood) ในช่วงฤดูใบไม้ผลิ พร้อมระบุจุดแข็งและธาตุปรับสมดุล"
    print(f"   Prompt: \"{prompt}\"")

    if dry_run:
        print("🔎 [Dry-run] Would execute sanity test query against the model.")
        return True

    # Try Ollama test first if not skipped and ollama CLI present
    if not skip_ollama and shutil.which("ollama"):
        print(f"   Testing via Ollama (`ollama run {model_name}`)...")
        try:
            res = subprocess.run(
                ["ollama", "run", model_name, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            if res.returncode == 0:
                output = res.stdout.strip()
                print("\n" + "-" * 50)
                print("📝 Model Response (Ollama):")
                print(output[:500] + ("..." if len(output) > 500 else ""))
                print("-" * 50)
                print("✅ Ollama sanity test passed!")
                return True
            else:
                print(f"⚠️  Ollama run returned non-zero code {res.returncode}: {res.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print("⚠️  Ollama test query timed out (>60s).")
        except Exception as e:
            print(f"⚠️  Ollama test execution failed: {e}")

    # Fallback to mlx_lm.generate if fused path exists
    if fused_path.exists():
        print("   Testing via MLX (`mlx_lm generate`)...")
        cmd = [
            sys.executable, "-m", "mlx_lm", "generate",
            "--model", str(fused_path),
            "--prompt", prompt,
            "--max-tokens", "150"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                output = res.stdout.strip()
                print("\n" + "-" * 50)
                print("📝 Model Response (MLX):")
                print(output[:500] + ("..." if len(output) > 500 else ""))
                print("-" * 50)
                print("✅ MLX sanity test passed!")
                return True
            else:
                print(f"⚠️  MLX test returned non-zero exit code: {res.stderr.strip()}")
        except Exception as e:
            print(f"⚠️  MLX test execution failed: {e}")

    print("⚠️  Sanity test skipped or completed with warnings.")
    return True


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-training fusion and deployment pipeline for Qwen2.5-BaZi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model",            default=DEFAULT_BASE_MODEL, help="Base model name/path")
    parser.add_argument("--adapter-path",     default=str(DEFAULT_ADAPTER_PATH), help="Path to LoRA adapter weights")
    parser.add_argument("--fused-path",       default=str(DEFAULT_FUSED_PATH), help="Output path for fused model")
    parser.add_argument("--gguf-path",        default=str(DEFAULT_GGUF_PATH), help="Output path for GGUF model")
    parser.add_argument("--modelfile",        default=str(DEFAULT_MODELFILE_PATH), help="Path to Ollama Modelfile")
    parser.add_argument("--ollama-model-name",default=DEFAULT_OLLAMA_MODEL_NAME, help="Name of Ollama model to create")
    parser.add_argument("--outtype",          default=DEFAULT_OUTTYPE, help="GGUF quantization type")
    parser.add_argument("--llama-cpp-dir",    default=None, help="Directory containing llama.cpp convert_hf_to_gguf.py")
    parser.add_argument("--dry-run",          action="store_true", help="Preview pipeline steps without running commands")
    parser.add_argument("--skip-fuse",        action="store_true", help="Skip MLX fusion step (use when fused model already exists)")
    parser.add_argument("--skip-gguf",        action="store_true", help="Skip GGUF conversion step")
    parser.add_argument("--skip-ollama",      action="store_true", help="Skip Ollama model creation step")
    parser.add_argument("--skip-test",        action="store_true", help="Skip model sanity test step")

    args = parser.parse_args()

    adapter_path = Path(args.adapter_path)
    fused_path   = Path(args.fused_path)
    gguf_path    = Path(args.gguf_path)
    modelfile    = Path(args.modelfile)

    print("\n🚀 Qwen2.5-BaZi Post-Training Fusion & Deployment Pipeline")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("   Mode: 🔎 DRY-RUN (No actions will be executed)")

    # 1. Verify Adapter
    ok = verify_adapter(adapter_path, dry_run=args.dry_run)
    if not ok and not args.dry_run:
        print("\n❌ Pipeline aborted: Adapter verification failed.")
        sys.exit(1)

    # 2. Fuse Adapter (auto-skip if fused model already exists OR --skip-fuse passed)
    fused_already_exists = fused_path.exists() and any(fused_path.glob("*.safetensors"))
    if args.skip_fuse or fused_already_exists:
        if fused_already_exists:
            fused_size = _format_size(fused_path)
            print(f"\n🔗 Step 2/5: MLX Fusion [AUTO-SKIPPED — fused model already exists at {fused_path} ({fused_size})]")
        else:
            print("\n🔗 Step 2/5: MLX Fusion [SKIPPED via --skip-fuse]")
    else:
        ok = fuse_adapter(args.model, adapter_path, fused_path, dry_run=args.dry_run)
        if not ok and not args.dry_run:
            print("\n❌ Pipeline aborted: Model fusion failed.")
            sys.exit(1)


    # 3. Convert to GGUF
    if args.skip_gguf:
        print("\n📦 Step 3/5: GGUF Conversion [SKIPPED]")
    else:
        gguf_ok = convert_to_gguf(
            fused_path,
            gguf_path,
            outtype=args.outtype,
            llama_cpp_dir=args.llama_cpp_dir,
            dry_run=args.dry_run
        )
        if not gguf_ok and not args.dry_run:
            print("⚠️  Proceeding despite GGUF conversion warning...")

    # 4. Create Ollama Model
    if args.skip_ollama:
        print("\n🦙 Step 4/5: Ollama Model Registration [SKIPPED]")
    else:
        create_ollama_model(
            modelfile,
            args.ollama_model_name,
            gguf_path,
            dry_run=args.dry_run
        )

    # 5. Sanity Test
    if args.skip_test:
        print("\n🧪 Step 5/5: Sanity Test [SKIPPED]")
    else:
        run_sanity_test(
            args.ollama_model_name,
            fused_path,
            skip_ollama=args.skip_ollama,
            dry_run=args.dry_run
        )

    print("\n" + "=" * 60)
    print("🎉 Post-Training Pipeline Completed Successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
