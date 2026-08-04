"""
scripts/kaggle_notebook_manager.py
==================================
Kaggle Notebook (Kernels) Automation & Management Tool for HoroConsultant.

Allows creating, updating, pushing, and monitoring Kaggle fine-tuning notebooks
directly from CLI / scripts using Kaggle API.

Usage:
------
    # 1. Setup ~/.kaggle/kaggle.json and project/kaggle_kernel/ directory
    python3 scripts/kaggle_notebook_manager.py --setup

    # 2. Push & trigger execution on Kaggle GPU
    python3 scripts/kaggle_notebook_manager.py --push

    # 3. Check execution status on Kaggle
    python3 scripts/kaggle_notebook_manager.py --status

    # 4. Pull notebook output & metadata down locally
    python3 scripts/kaggle_notebook_manager.py --pull
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import subprocess
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kaggle_manager")

KERNEL_DIR = ROOT_DIR / "project" / "kaggle_kernel"
METADATA_FILE = KERNEL_DIR / "kernel-metadata.json"
NOTEBOOK_FILE = KERNEL_DIR / "notebook.ipynb"


def setup_kaggle_credentials() -> bool:
    """Setup ~/.kaggle/kaggle.json from environment variables / Doppler Config."""
    username = os.getenv("KAGGLE_USERNAME") or Config.get_summary().get("KAGGLE_USERNAME", "pphothidaen")
    token = os.getenv("KAGGLE_TOKEN")

    if not token or token.startswith("REPLACE"):
        # Fallback to check .env or .env.production directly
        from dotenv import dotenv_values
        env_secrets = dotenv_values(ROOT_DIR / ".env.production") or dotenv_values(ROOT_DIR / ".env")
        username = env_secrets.get("KAGGLE_USERNAME", username)
        token = env_secrets.get("KAGGLE_TOKEN", token)

    if not token or token.startswith("REPLACE"):
        logger.error("[ERROR] KAGGLE_TOKEN environment variable or Doppler secret not set!")
        return False

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    json_file = kaggle_dir / "kaggle.json"

    cred_data = {"username": username, "key": token}
    json_file.write_text(json.dumps(cred_data, indent=2), encoding="utf-8")
    os.chmod(json_file, 0o600)
    logger.info(f"[AUTH] Kaggle credentials configured at '{json_file}' (User: {username})")
    return True


def create_kernel_files(accelerator_type: str = "nvidiaTeslaT4x2") -> None:
    """Generate project/kaggle_kernel/ metadata and notebook.ipynb for specified GPU type (default: Dual T4x2)."""
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)

    username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
    slug = "horoconsultant-finetune-pipeline"
    kernel_id = f"{username}/{slug}"

    acc_lower = accelerator_type.lower()
    if "p100" in acc_lower:
        machine_shape = "NvidiaTeslaP100"
        platform_arg = "KAGGLE_P100"
    else:
        machine_shape = "NvidiaTeslaT4x2"
        platform_arg = "KAGGLE_T4X2"

    metadata = {
        "id": kernel_id,
        "title": "HoroConsultant-FineTune-Pipeline",
        "code_file": "notebook.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "accelerator": "gpu",
        "machine_shape": machine_shape
    }


    METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info(f"[FILE] Created metadata file at '{METADATA_FILE}' for accelerator [gpu / {machine_shape}]")

    # Generate notebook structure with clean execution code
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "#  HoroConsultant - Production Cloud Fine-Tuning Pipeline\n",
                    "import os\n",
                    "import sys\n",
                    "import subprocess\n",
                    "\n",
                    "# Suppress PyDev / frozen modules debugger warnings & force UTF-8 encoding\n",
                    "os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'\n",
                    "os.environ['PYTHONWARNINGS'] = 'ignore'\n",
                    "os.environ['PYTHONIOENCODING'] = 'utf-8:surrogateescape'\n",
                    "os.environ['PYTHONUTF8'] = '1'\n",
                    "os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'\n",
                    "os.environ['TRANSFORMERS_VERBOSITY'] = 'error'\n",
                    "os.environ['TQDM_DISABLE'] = '1'\n",
                    "if hasattr(sys.stdout, 'reconfigure'):\n",
                    "    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n",
                    "    except Exception: pass\n",
                    "if hasattr(sys.stderr, 'reconfigure'):\n",
                    "    try: sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n",
                    "    except Exception: pass\n",
                    "\n",
                    "# 0. Set CUDA stability env vars FIRST (before any torch/bnb imports)\n",
                    "# Tesla T4 = sm_75 (Compute Capability 7.5) -- bfloat16 requires sm_80+\n",
                    "os.environ.setdefault('TORCH_CUDA_ARCH_LIST', '7.5')     # Target T4 arch\n",
                    "os.environ.pop('BNB_CUDA_VERSION', None)                   # Let BNB auto-detect native CUDA library\n",
                    "os.environ.setdefault('CUDA_MODULE_LOADING', 'LAZY')      # Lazy loading prevents JIT errors at import\n",
                    "os.environ['TOKENIZERS_PARALLELISM'] = 'false'\n",
                    "print('[OK] CUDA stability environment variables set (T4/sm_75 compatible)')\n",
                    "\n",
                    "# 1. Load Secrets safely from Kaggle Secrets (individual try-except per key)\n",
                    "try:\n",
                    "    from kaggle_secrets import UserSecretsClient\n",
                    "    user_secrets = UserSecretsClient()\n",
                    "    for secret_key in ['HF_TOKEN', 'APP_SUPABASE_URL', 'APP_SUPABASE_KEY', 'GH_TOKEN']:\n",
                    "        try:\n",
                    "            val = user_secrets.get_secret(secret_key)\n",
                    "            if val:\n",
                    "                os.environ[secret_key] = val\n",
                    "                print(f'[OK] Kaggle Secret loaded: {secret_key}')\n",
                    "        except Exception as e:\n",
                    "            print(f'[INFO] Kaggle Secret note ({secret_key}): {e}')\n",
                    "except Exception as e:\n",
                    "    print(f'[INFO] Kaggle Secrets Client not available: {e}')\n",
                    "\n",
                    "# 2. Safe Git Clone / Pull with pure Python subprocess\n",
                    "target_dir = '/kaggle/working/HoroConsultant'\n",
                    "if not os.path.exists(target_dir):\n",
                    "    print('[MODEL] Cloning HoroConsultant repository...')\n",
                    "    subprocess.run(['git', 'clone', 'https://github.com/pphothidaen/HoroConsultant.git', target_dir], check=True)\n",
                    "else:\n",
                    "    print('[SYNC] Resetting and pulling latest updates...')\n",
                    "    subprocess.run(['git', '-C', target_dir, 'fetch', 'origin', 'main'], check=True)\n",
                    "    subprocess.run(['git', '-C', target_dir, 'reset', '--hard', 'origin/main'], check=True)\n",
                    "\n",
                    "os.chdir(target_dir)\n",
                    "if target_dir not in sys.path:\n",
                    "    sys.path.insert(0, target_dir)\n",
                    "\n",
                    "# 3. Install Fine-Tuning Dependencies preserving Kaggle's pre-installed CUDA PyTorch\n",
                    "print('[CHECK] Checking pre-installed PyTorch & CUDA status...')\n",
                    "import torch\n",
                    "print(f'[CUDA] Kaggle PyTorch version: {torch.__version__}, CUDA available: {torch.cuda.is_available()}')\n",
                    "if torch.cuda.is_available():\n",
                    "    cap = torch.cuda.get_device_capability(0)\n",
                    "    dev_name = torch.cuda.get_device_name(0)\n",
                    "    target_sm = f'sm_{cap[0]}{cap[1]}'\n",
                    "    print(f'[CUDA] Detected GPU: {dev_name} ({target_sm})')\n",
                    "    if cap == (6, 0):\n",
                    "        print('[WARNING] Kaggle allocated Tesla P100 (sm_60). Installing PyTorch 2.2.0+cu121 compatibility wheel with native sm_60 Pascal support...')\n",
                    "        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--prefer-binary', '--no-deps', 'torch==2.2.0+cu121', 'torchvision==0.17.0+cu121', '--index-url', 'https://download.pytorch.org/whl/cu121'], check=True)\n",
                    "    else:\n",
                    "        print(f'[OK] {dev_name} ({target_sm}) fully supported by native PyTorch.')\n",
                    "print('[MODEL] Removing incompatible torchao/torchvision & installing fine-tuning packages...')\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torchao', 'torchvision'], check=False)\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--progress-bar', 'off', '--prefer-binary', '--no-deps', 'transformers==4.44.2', 'peft==0.12.0', 'trl==0.11.0', 'accelerate==0.33.0', 'bitsandbytes==0.43.3', 'datasets==2.18.0', 'huggingface_hub==0.25.1'], check=True)\n",
                    "try:\n",
                    "    import bitsandbytes\n",
                    "    bnb_ver = getattr(bitsandbytes, '__version__', 'unknown')\n",
                    "except Exception as bnb_e:\n",
                    "    bnb_ver = f'bypassed ({bnb_e})'\n",
                    "import transformers, peft, trl, datasets, accelerate\n",
                    "print(f'[OK] Fail-Fast Import Verified: transformers={transformers.__version__}, peft={peft.__version__}, trl={trl.__version__}, accelerate={accelerate.__version__}, bitsandbytes={bnb_ver}')\n",
                    "\n",
                    "# 4. Run Cloud Training Orchestrator with execution logging\n",
                    "# Pass the full environment (incl. CUDA stability vars) to subprocess\n",
                    "print('\\ud83d\\ude80 Launching Cloud Training Orchestrator...')\n",
                    "log_path = '/kaggle/working/train_execution.log'\n",
                    "train_env = os.environ.copy()\n",
                    "train_env['PYTHONIOENCODING'] = 'utf-8:surrogateescape'\n",
                    "train_env['PYTHONUTF8'] = '1'\n",
                    "proc = subprocess.Popen([sys.executable, 'scripts/cloud_train_orchestrator.py', '--platform', '" + platform_arg + "', '--base-model', 'Qwen/Qwen2.5-7B-Instruct', '--epochs', '3'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', env=train_env)\n",
                    "with open(log_path, 'w', encoding='utf-8', errors='replace') as log_f:\n",
                    "    for line in iter(proc.stdout.readline, ''):\n",
                    "        safe_line = line.encode('utf-8', errors='replace').decode('utf-8', errors='replace')\n",
                    "        sys.stdout.write(safe_line)\n",
                    "        log_f.write(safe_line)\n",
                    "proc.wait()\n",
                    "if proc.returncode != 0:\n",
                    "    log_tail = ''\n",
                    "    if os.path.exists(log_path):\n",
                    "        try:\n",
                    "            with open(log_path, 'r', encoding='utf-8') as f:\n",
                    "                log_tail = ''.join(f.readlines()[-30:])\n",
                    "        except Exception:\n",
                    "            pass\n",
                    "    raise RuntimeError(f'\\u274c Training orchestrator failed (exit code {proc.returncode}).\\n--- Tail of train_execution.log ---\\n{log_tail}')\n",
                    "print('\\ud83c\\udf89 Training pipeline completed successfully!')\n"
                ]
            }
        ],
        "metadata": {
            "accelerator": "gpu",
            "gpuType": "gpu",
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    NOTEBOOK_FILE.write_text(json.dumps(notebook, indent=2), encoding="utf-8")

    logger.info(f"[NOTEBOOK] Created Jupyter Notebook file at '{NOTEBOOK_FILE}'")


def git_auto_commit_and_push(message: str) -> bool:
    """Auto-stage, commit, and push updated repository files to GitHub."""
    logger.info(f"[GIT] Auto-syncing repository changes to GitHub: '{message}'...")
    try:
        subprocess.run(["git", "add", "."], cwd=ROOT_DIR, check=False)
        res = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT_DIR, capture_output=True, text=True)
        if not res.stdout.strip():
            logger.info("[INFO] No uncommitted git changes detected.")
            return True
        
        subprocess.run(["git", "commit", "-m", message], cwd=ROOT_DIR, check=False)
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT_DIR, capture_output=True, text=True)
        if push_res.returncode == 0:
            logger.info("[SUCCESS] Successfully pushed latest changes to GitHub repository!")
            return True
        else:
            logger.warning(f"[WARNING] Git push notice: {push_res.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Git auto-push failed: {e}")
        return False


def run_kaggle_cmd(args_list: list[str]) -> bool:
    """Run kaggle CLI command with credentials supplied via env vars."""
    cmd = ["kaggle"] + args_list
    logger.info(f"[START] Running command: {' '.join(cmd)}")
    env = os.environ.copy()
    try:
        json_file = Path.home() / ".kaggle" / "kaggle.json"
        if json_file.exists():
            creds = json.loads(json_file.read_text(encoding="utf-8"))
            env["KAGGLE_USERNAME"] = creds.get("username", "")
            env["KAGGLE_API_TOKEN"] = creds.get("key", "")
            env["KAGGLE_KEY"] = creds.get("key", "")
    except Exception as e:
        logger.warning(f"[WARNING] Could not load kaggle.json for env var setup: {e}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if res.returncode == 0:
            print(res.stdout)
            return True
        else:
            logger.error(f"[ERROR] Kaggle CLI Error ({res.returncode}): {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Command execution error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="HoroConsultant Kaggle Notebook Automation CLI")
    parser.add_argument("--setup", action="store_true", help="Setup credentials and generate kernel metadata & notebook")
    parser.add_argument("--push", action="store_true", help="Push & trigger notebook execution on Kaggle GPU")
    parser.add_argument("--status", action="store_true", help="Check notebook execution status on Kaggle")
    parser.add_argument("--pull", action="store_true", help="Pull latest notebook, outputs, and metadata down from Kaggle")
    parser.add_argument("--output", action="store_true", help="Pull kernel output files specifically via 'kaggle kernels output'")
    parser.add_argument("--dest", default=str(KERNEL_DIR), help="Destination directory for output files (default: project/kaggle_kernel)")
    parser.add_argument("--accelerator", default="nvidiaTeslaT4x2", help="Specify Kaggle GPU accelerator (default: nvidiaTeslaT4x2, optional: nvidiaTeslaP100)")

    args = parser.parse_args()

    if not any([args.setup, args.push, args.status, args.pull, args.output]):
        args.setup = True

    if args.setup:
        setup_kaggle_credentials()
        create_kernel_files(args.accelerator)

    if args.push:
        setup_kaggle_credentials()
        create_kernel_files(args.accelerator)
        # Auto-commit and push code updates to GitHub first so Kaggle git clone gets latest code
        git_auto_commit_and_push("feat(kaggle): auto-commit updated notebook & scripts before pushing to Kaggle")
        push_args = ["kernels", "push", "-p", str(KERNEL_DIR)]
        run_kaggle_cmd(push_args)


    if args.status:
        setup_kaggle_credentials()
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        run_kaggle_cmd(["kernels", "status", kernel_id])

    if args.output:
        setup_kaggle_credentials()
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        dest_dir = Path(args.dest)
        dest_dir.mkdir(parents=True, exist_ok=True)
        run_kaggle_cmd(["kernels", "output", kernel_id, "-p", str(dest_dir)])

    if args.pull:
        setup_kaggle_credentials()
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        dest_dir = Path(args.dest)
        dest_dir.mkdir(parents=True, exist_ok=True)
        # 1. Pull notebook & metadata
        pull_success = run_kaggle_cmd(["kernels", "pull", kernel_id, "-p", str(dest_dir), "-m"])
        # 2. Pull output files (train_execution.log, summaries, adapters)
        output_success = run_kaggle_cmd(["kernels", "output", kernel_id, "-p", str(dest_dir)])
        if pull_success or output_success:
            git_auto_commit_and_push("feat(kaggle): sync pulled notebook outputs & metadata from Kaggle")


if __name__ == "__main__":
    main()
