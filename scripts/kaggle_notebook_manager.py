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
        logger.error("❌ KAGGLE_TOKEN environment variable or Doppler secret not set!")
        return False

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    json_file = kaggle_dir / "kaggle.json"

    cred_data = {"username": username, "key": token}
    json_file.write_text(json.dumps(cred_data, indent=2), encoding="utf-8")
    os.chmod(json_file, 0o600)
    logger.info(f"🔑 Kaggle credentials configured at '{json_file}' (User: {username})")
    return True


def create_kernel_files() -> None:
    """Generate project/kaggle_kernel/ metadata and notebook.ipynb."""
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)

    username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
    slug = "horoconsultant-finetune-pipeline"
    kernel_id = f"{username}/{slug}"

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
        "accelerator": "nvidiaTeslaT4",
        "machine_shape": "NvidiaTeslaT4"
    }


    METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info(f"📄 Created metadata file at '{METADATA_FILE}'")

    # Generate notebook structure with clean execution code
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 🌌 HoroConsultant - Production Cloud Fine-Tuning Pipeline\n",
                    "import os\n",
                    "import sys\n",
                    "import subprocess\n",
                    "\n",
                    "# Suppress PyDev / frozen modules debugger warnings\n",
                    "os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'\n",
                    "os.environ['PYTHONWARNINGS'] = 'ignore'\n",

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
                    "                print(f'✅ Kaggle Secret loaded: {secret_key}')\n",
                    "        except Exception as e:\n",
                    "            print(f'ℹ️ Kaggle Secret note ({secret_key}): {e}')\n",
                    "except Exception as e:\n",
                    "    print(f'ℹ️ Kaggle Secrets Client not available: {e}')\n",
                    "\n",
                    "# 2. Safe Git Clone / Pull with pure Python subprocess\n",
                    "target_dir = '/kaggle/working/HoroConsultant'\n",
                    "if not os.path.exists(target_dir):\n",
                    "    print('📦 Cloning HoroConsultant repository...')\n",
                    "    subprocess.run(['git', 'clone', 'https://github.com/pphothidaen/HoroConsultant.git', target_dir], check=True)\n",
                    "else:\n",
                    "    print('🔄 Resetting and pulling latest updates...')\n",
                    "    subprocess.run(['git', '-C', target_dir, 'fetch', 'origin', 'main'], check=True)\n",
                    "    subprocess.run(['git', '-C', target_dir, 'reset', '--hard', 'origin/main'], check=True)\n",
                    "\n",
                    "os.chdir(target_dir)\n",
                    "if target_dir not in sys.path:\n",
                    "    sys.path.insert(0, target_dir)\n",
                    "\n",
                    "# 3. Install Fine-Tuning Dependencies safely without overwriting pre-installed Kaggle CUDA PyTorch\n",
                    "print('📦 Installing dependencies...')\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torchao'], check=False)\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--prefer-binary', '-r', 'requirements.txt'], check=True)\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--prefer-binary', 'torchao>=0.16.0', 'transformers>=4.40.0', 'peft>=0.10.0', 'bitsandbytes>=0.43.3', 'datasets>=2.18.0', 'trl>=0.12.0', 'huggingface_hub', 'accelerate'], check=True)\n",


                    "\n",
                    "# 4. Run Cloud Training Orchestrator with execution logging\n",
                    "print('🚀 Launching Cloud Training Orchestrator...')\n",
                    "log_path = '/kaggle/working/train_execution.log'\n",
                    "proc = subprocess.Popen([sys.executable, 'scripts/cloud_train_orchestrator.py', '--platform', 'KAGGLE_T4', '--base-model', 'Qwen/Qwen2.5-7B-Instruct', '--epochs', '3'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)\n",
                    "with open(log_path, 'w', encoding='utf-8') as log_f:\n",
                    "    for line in iter(proc.stdout.readline, ''):\n",
                    "        sys.stdout.write(line)\n",
                    "        log_f.write(line)\n",
                    "proc.wait()\n",
                    "if proc.returncode != 0:\n",
                    "    raise RuntimeError(f'❌ Training orchestrator failed with exit code {proc.returncode}')\n",
                    "print('🎉 Training pipeline completed successfully!')\n"
                ]
            }
        ],
        "metadata": {
            "accelerator": "nvidiaTeslaT4",
            "gpuType": "nvidiaTeslaT4",
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

    logger.info(f"📓 Created Jupyter Notebook file at '{NOTEBOOK_FILE}'")


def git_auto_commit_and_push(message: str) -> bool:
    """Auto-stage, commit, and push updated repository files to GitHub."""
    logger.info(f"🐙 Auto-syncing repository changes to GitHub: '{message}'...")
    try:
        subprocess.run(["git", "add", "."], cwd=ROOT_DIR, check=False)
        res = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT_DIR, capture_output=True, text=True)
        if not res.stdout.strip():
            logger.info("ℹ️ No uncommitted git changes detected.")
            return True
        
        subprocess.run(["git", "commit", "-m", message], cwd=ROOT_DIR, check=False)
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT_DIR, capture_output=True, text=True)
        if push_res.returncode == 0:
            logger.info("🎉 Successfully pushed latest changes to GitHub repository!")
            return True
        else:
            logger.warning(f"⚠️ Git push notice: {push_res.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"❌ Git auto-push failed: {e}")
        return False


def run_kaggle_cmd(args_list: list[str]) -> bool:
    """Run kaggle CLI command."""
    cmd = ["kaggle"] + args_list
    logger.info(f"🚀 Running command: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(res.stdout)
            return True
        else:
            logger.error(f"❌ Kaggle CLI Error ({res.returncode}): {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Command execution error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="HoroConsultant Kaggle Notebook Automation CLI")
    parser.add_argument("--setup", action="store_true", help="Setup credentials and generate kernel metadata & notebook")
    parser.add_argument("--push", action="store_true", help="Push & trigger notebook execution on Kaggle GPU")
    parser.add_argument("--status", action="store_true", help="Check notebook execution status on Kaggle")
    parser.add_argument("--pull", action="store_true", help="Pull latest notebook, outputs, and metadata down from Kaggle")
    parser.add_argument("--output", action="store_true", help="Pull kernel output files specifically via 'kaggle kernels output'")
    parser.add_argument("--dest", default=str(KERNEL_DIR), help="Destination directory for output files (default: project/kaggle_kernel)")
    parser.add_argument("--accelerator", default="nvidiaTeslaT4", help="Specify Kaggle GPU accelerator (e.g. nvidiaTeslaT4, gpu, nvidiaTeslaP100)")

    args = parser.parse_args()

    if not any([args.setup, args.push, args.status, args.pull, args.output]):
        args.setup = True

    if args.setup:
        setup_kaggle_credentials()
        create_kernel_files()

    if args.push:
        setup_kaggle_credentials()
        if not METADATA_FILE.exists():
            create_kernel_files()
        # Auto-commit and push code updates to GitHub first so Kaggle git clone gets latest code
        git_auto_commit_and_push("feat(kaggle): auto-commit updated notebook & scripts before pushing to Kaggle")
        push_args = ["kernels", "push", "-p", str(KERNEL_DIR)]
        if args.accelerator:
            push_args.extend(["--accelerator", args.accelerator])
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
