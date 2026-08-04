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
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": []
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
                    "\n",
                    "# Suppress PyDev / frozen modules debugger warnings on Kaggle\n",
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
                    "# 2. Safe Git Clone / Pull\n",
                    "if not os.path.exists('/kaggle/working/HoroConsultant'):\n",
                    "    !git clone https://github.com/pphothidaen/HoroConsultant.git /kaggle/working/HoroConsultant\n",
                    "\n",
                    "%cd /kaggle/working/HoroConsultant\n",
                    "!git pull\n",
                    "\n",
                    "# 3. Install Dependencies\n",
                    "!pip install -q -r requirements.txt\n",
                    "!pip install -q torch transformers peft bitsandbytes datasets trl huggingface_hub\n",
                    "\n",
                    "# 4. Run Cloud Training Orchestrator\n",
                    "!python3 /kaggle/working/HoroConsultant/scripts/cloud_train_orchestrator.py --platform KAGGLE_T4 --epochs 3\n"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    NOTEBOOK_FILE.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    logger.info(f"📓 Created Jupyter Notebook file at '{NOTEBOOK_FILE}'")


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
    parser.add_argument("--pull", action="store_true", help="Pull latest notebook and metadata down from Kaggle")

    args = parser.parse_args()

    if not any([args.setup, args.push, args.status, args.pull]):
        args.setup = True

    if args.setup:
        setup_kaggle_credentials()
        create_kernel_files()

    if args.push:
        setup_kaggle_credentials()
        if not METADATA_FILE.exists():
            create_kernel_files()
        run_kaggle_cmd(["kernels", "push", "-p", str(KERNEL_DIR)])

    if args.status:
        setup_kaggle_credentials()
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        run_kaggle_cmd(["kernels", "status", kernel_id])

    if args.pull:
        setup_kaggle_credentials()
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        run_kaggle_cmd(["kernels", "pull", kernel_id, "-p", str(KERNEL_DIR), "-m"])


if __name__ == "__main__":
    main()
