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

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kaggle_manager")

KERNEL_DIR = ROOT_DIR / "project" / "kaggle_kernel"
METADATA_FILE = KERNEL_DIR / "kernel-metadata.json"
NOTEBOOK_FILE = KERNEL_DIR / "notebook.ipynb"


def setup_kaggle_credentials(*, write_file: bool = True) -> bool:
    """Load Kaggle credentials and optionally write the CLI configuration file.

    Read-only operations such as ``--status`` must not mutate a developer's
    home directory.  The Kaggle CLI accepts credentials through environment
    variables, so writing ``~/.kaggle/kaggle.json`` is reserved for explicit
    ``--setup`` calls.
    """
    username = os.getenv("KAGGLE_USERNAME") or Config.get_summary().get("KAGGLE_USERNAME", "pphothidaen")
    token = os.getenv("KAGGLE_TOKEN") or os.getenv("KAGGLE_KEY")

    if not token or token.startswith("REPLACE"):
        # Fallback to check .env or .env.production directly
        from dotenv import dotenv_values
        env_secrets = dotenv_values(ROOT_DIR / ".env.production") or dotenv_values(ROOT_DIR / ".env")
        username = env_secrets.get("KAGGLE_USERNAME", username)
        token = env_secrets.get("KAGGLE_TOKEN") or env_secrets.get("KAGGLE_KEY") or token

    if not token or token.startswith("REPLACE"):
        logger.error("[ERROR] KAGGLE_TOKEN environment variable or Doppler secret not set!")
        return False

    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_TOKEN"] = token
    os.environ["KAGGLE_KEY"] = token
    os.environ["KAGGLE_API_TOKEN"] = token
    if not write_file:
        logger.info(f"[AUTH] Kaggle credentials loaded for process execution (User: {username})")
        return True

    kaggle_dir = Path.home() / ".kaggle"
    json_file = kaggle_dir / "kaggle.json"
    cred_data = {"username": username, "key": token}
    try:
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        json_file.write_text(json.dumps(cred_data, indent=2), encoding="utf-8")
        os.chmod(json_file, 0o600)
    except OSError as error:
        logger.error(f"[ERROR] Could not write Kaggle credentials at '{json_file}': {error}")
        return False
    logger.info(f"[AUTH] Kaggle credentials configured at '{json_file}' (User: {username})")
    return True


def create_kernel_files(
    accelerator_type: str = "gpu",
    force_metadata: bool = False,
    dataset_path: str | None = None,
) -> None:
    """Generate project/kaggle_kernel/ metadata and notebook.ipynb preserving user's default Kaggle GPU settings."""
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)
    dataset_cmd_path = str(Path(dataset_path).expanduser()) if dataset_path else ""

    username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
    slug = "horoconsultant-finetune-pipeline"
    kernel_id = f"{username}/{slug}"

    if METADATA_FILE.exists() and not force_metadata:
        logger.info(f"[PRESERVE] Using existing metadata file at '{METADATA_FILE}' without modifying accelerator settings.")
    else:
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
            "accelerator": "gpu"
        }
        METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        logger.info(f"[FILE] Created metadata file at '{METADATA_FILE}' (Accelerator locked to default: [gpu])")

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
                    "import shutil\n",
                    "import sys\n",
                    "import types\n",
                    "import subprocess\n",
                    "\n",
                    "# Suppress PyDev / frozen modules debugger warnings & force UTF-8 encoding\n",
                    "os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'\n",
                    "os.environ['PYTHONWARNINGS'] = 'ignore'\n",
                    "os.environ['PYTHONIOENCODING'] = 'utf-8'\n",
                    "os.environ['PYTHONUTF8'] = '1'\n",
                    "os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'\n",
                    "os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'\n",
                    "os.environ['HF_HUB_MAX_RETRIES'] = '10'\n",
                    "os.environ['TRANSFORMERS_VERBOSITY'] = 'error'\n",
                    "os.environ['TQDM_DISABLE'] = '1'\n",
                    "if hasattr(sys.stdout, 'reconfigure'):\n",
                    "    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n",
                    "    except Exception: pass\n",
                    "if hasattr(sys.stderr, 'reconfigure'):\n",
                    "    try: sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n",
                    "    except Exception: pass\n",
                    "\n",
                    "# 0. Set CUDA stability env vars FIRST & Triton 3.x compatibility shim\n",
                    "os.environ.setdefault('TORCH_CUDA_ARCH_LIST', '7.5')\n",
                    "os.environ.setdefault('BNB_CUDA_VERSION', '124')\n",
                    "os.environ.setdefault('CUDA_MODULE_LOADING', 'LAZY')\n",
                    "os.environ['TOKENIZERS_PARALLELISM'] = 'false'\n",
                    "\n",
                    "# Triton 3.x compatibility shim for bitsandbytes (prevents ModuleNotFoundError: No module named 'triton.ops')\n",
                    "try:\n",
                    "    import triton.ops\n",
                    "except (ImportError, ModuleNotFoundError):\n",
                    "    triton_ops = types.ModuleType('triton.ops')\n",
                    "    triton_ops_matmul = types.ModuleType('triton.ops.matmul_perf_model')\n",
                    "    triton_ops_matmul.early_config_prune = lambda *a, **k: None\n",
                    "    triton_ops_matmul.estimate_matmul_time = lambda *a, **k: 0\n",
                    "    sys.modules['triton.ops'] = triton_ops\n",
                    "    sys.modules['triton.ops.matmul_perf_model'] = triton_ops_matmul\n",
                    "print('[OK] CUDA stability & Triton compatibility shim applied.')\n",
                    "\n",
                    "# 1. Load Secrets using 2-Tier Priority Policy (1st Priority: DOPPLER, 2nd Priority: KAGGLE SECRETS STORE)\n",
                    "# Only load DOPPLER_TOKEN here — other secrets are handled by the orchestrator's Config class,\n",
                    "# which calls the Doppler API first (using this token), then falls back to Kaggle Secrets.\n",
                    "all_secrets = ['DOPPLER_TOKEN']\n",
                    "try:\n",
                    "    from kaggle_secrets import UserSecretsClient\n",
                    "    user_secrets = UserSecretsClient()\n",
                    "    for secret_key in all_secrets:\n",
                    "        # 1st Priority: Check if available via Doppler environment\n",
                    "        if os.getenv(secret_key):\n",
                    "            print(f'[OK] Secret {secret_key} loaded from 1st Priority (DOPPLER)')\n",
                    "            continue\n",
                    "        # Notice for Doppler Miss\n",
                    "        print(f'[INFO] Secret {secret_key} not in Doppler. Checking 2nd Priority (KAGGLE SECRETS STORE)...')\n",
                    "        try:\n",
                    "            val = user_secrets.get_secret(secret_key)\n",
                    "            if val:\n",
                    "                os.environ[secret_key] = val\n",
                    "                print(f'[OK] Secret {secret_key} loaded from 2nd Priority (KAGGLE SECRETS STORE)')\n",
                    "        except Exception as e:\n",
                    "            print(f'[INFO] Kaggle Secret note ({secret_key}): {e}')\n",
                    "except Exception as e:\n",
                    "    print(f'[INFO] Kaggle Secrets Client note: {e}')\n",
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
                    "    print(f'[OK] Detected GPU {dev_name} ({target_sm}) using native Kaggle PyTorch environment.')\n",
                    "print('[MODEL] Removing incompatible torchao/torchvision & installing fine-tuning packages...')\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torchao', 'torchvision'], check=False)\n",
                    "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--progress-bar', 'off', '--prefer-binary', 'transformers==4.44.2', 'tokenizers==0.19.1', 'peft==0.12.0', 'trl==0.11.0', 'accelerate==0.33.0', 'bitsandbytes==0.43.3', 'datasets==2.18.0', 'huggingface_hub==0.25.1', 'pyarrow_hotfix', 'python-docx', 'gdown'], check=True)\n",
                    "import docx, gdown, glob, zipfile\n",
                    "try:\n",
                    "    import bitsandbytes as bnb\n",
                    "    from pathlib import Path\n",
                    "    bnb_dir = Path(bnb.__file__).parent\n",
                    "    cuda_ver_str = getattr(torch.version, 'cuda', '') or ''\n",
                    "    cuda_clean = cuda_ver_str.replace('.', '')\n",
                    "    if cuda_clean:\n",
                    "        target_so = bnb_dir / f'libbitsandbytes_cuda{cuda_clean}.so'\n",
                    "        if not target_so.exists():\n",
                    "            available = sorted(list(bnb_dir.glob('libbitsandbytes_cuda*.so')), reverse=True)\n",
                    "            if available:\n",
                    "                try: os.symlink(available[0], target_so)\n",
                    "                except Exception: shutil.copy(available[0], target_so)\n",
                    "                print(f'[OK] BNB CUDA Fix: Symlinked {available[0].name} -> {target_so.name}')\n",
                    "    bnb_ver = getattr(bnb, '__version__', 'unknown')\n",
                    "except Exception as bnb_e:\n",
                    "    bnb_ver = f'bypassed ({bnb_e})'\n",
                    "import transformers, peft, trl, datasets, accelerate\n",
                    "print(f'[OK] Fail-Fast Import Verified: transformers={transformers.__version__}, peft={peft.__version__}, trl={trl.__version__}, accelerate={accelerate.__version__}, bitsandbytes={bnb_ver}')\n",
                    "\n",
                    "# 4. Google Drive Dataset Ingestion & Deduplication\n",
                    "print('[INFO] กำลังดาวน์โหลด Dataset จาก Google Drive...')\n",
                    "gdrive_url = 'https://drive.google.com/drive/folders/1e8nX-h3cKpcifUv6G2EjuJDey9DBm5b2'\n",
                    "gdrive_data_dir = '/kaggle/working/my_dataset'\n",
                    "os.makedirs(gdrive_data_dir, exist_ok=True)\n",
                    "try:\n",
                    "    gdown.download_folder(gdrive_url, output=gdrive_data_dir, quiet=False, use_cookies=False)\n",
                    "except Exception as gdown_err:\n",
                    "    print(f'[WARNING] Google Drive download note: {gdown_err}')\n",
                    "\n",
                    "local_dataset_target = os.path.join(target_dir, 'project/rag/datasets/train.jsonl')\n",
                    "os.makedirs(os.path.dirname(local_dataset_target), exist_ok=True)\n",
                    "valid_total_lines = 0\n",
                    "seen_data = set()\n",
                    "print('[INFO] กำลังตรวจสอบ รวบรวม และคัดกรองข้อมูลซ้ำจากไฟล์ทั้งหมด...')\n",
                    "if os.path.exists(local_dataset_target):\n",
                    "    try:\n",
                    "        with open(local_dataset_target, 'r', encoding='utf-8') as f_ex:\n",
                    "            for line in f_ex:\n",
                    "                s = line.strip()\n",
                    "                if s:\n",
                    "                    seen_data.add(s)\n",
                    "    except Exception:\n",
                    "        pass\n",
                    "\n",
                    "with open(local_dataset_target, 'w', encoding='utf-8') as f_out:\n",
                    "    for item in seen_data:\n",
                    "        f_out.write(item + '\\n')\n",
                    "        valid_total_lines += 1\n",
                    "    if os.path.exists(gdrive_data_dir):\n",
                    "        downloaded_files = glob.glob(os.path.join(gdrive_data_dir, '**/*.*'), recursive=True)\n",
                    "        for fpath in downloaded_files:\n",
                    "            file_ext = fpath.lower()\n",
                    "            valid_file_lines = 0\n",
                    "            duplicate_lines = 0\n",
                    "            if file_ext.endswith('.jsonl') or file_ext.endswith('.json') or file_ext.endswith('.docx'):\n",
                    "                print(f'[PROCESS] กำลังประมวลผลไฟล์: {os.path.basename(fpath)}')\n",
                    "                if zipfile.is_zipfile(fpath) or file_ext.endswith('.docx'):\n",
                    "                    try:\n",
                    "                        doc = docx.Document(fpath)\n",
                    "                        for para in doc.paragraphs:\n",
                    "                            text = para.text.strip()\n",
                    "                            if text:\n",
                    "                                text = text.replace('“', '\"').replace('”', '\"').replace('‘', \"'\").replace('’', \"'\")\n",
                    "                                try:\n",
                    "                                    json.loads(text)\n",
                    "                                    if text not in seen_data:\n",
                    "                                        seen_data.add(text)\n",
                    "                                        f_out.write(text + '\\n')\n",
                    "                                        valid_file_lines += 1\n",
                    "                                    else:\n",
                    "                                        duplicate_lines += 1\n",
                    "                                except json.JSONDecodeError:\n",
                    "                                    pass\n",
                    "                        print(f'  -> [OK] ได้ข้อมูลใหม่ {valid_file_lines} บรรทัด (ตัดข้อมูลซ้ำออก {duplicate_lines} บรรทัด)')\n",
                    "                    except Exception as e:\n",
                    "                        print(f'  -> [ERROR] สกัดข้อมูลล้มเหลว: {e}')\n",
                    "                else:\n",
                    "                    try:\n",
                    "                        with open(fpath, 'r', encoding='utf-8') as f_in:\n",
                    "                            for line in f_in:\n",
                    "                                text = line.strip()\n",
                    "                                if text:\n",
                    "                                    try:\n",
                    "                                        json.loads(text)\n",
                    "                                        if text not in seen_data:\n",
                    "                                            seen_data.add(text)\n",
                    "                                            f_out.write(text + '\\n')\n",
                    "                                            valid_file_lines += 1\n",
                    "                                        else:\n",
                    "                                            duplicate_lines += 1\n",
                    "                                    except json.JSONDecodeError:\n",
                    "                                        pass\n",
                    "                        print(f'  -> [OK] ได้ข้อมูลใหม่ {valid_file_lines} บรรทัด (ตัดข้อมูลซ้ำออก {duplicate_lines} บรรทัด)')\n",
                    "                    except Exception as e:\n",
                    "                        print(f'  -> [ERROR] อ่านไฟล์ล้มเหลว: {e}')\n",
                    "                valid_total_lines += valid_file_lines\n",
                    "print(f'[OK] รวบรวม Dataset สำเร็จ! มีข้อมูลที่ไม่ซ้ำกันพร้อมเทรนรวมทั้งสิ้น {valid_total_lines} บรรทัด')\n",
                    "\n",
                    "# 5. Run Cloud Training Orchestrator with execution logging\n",
                    "print('[START] Launching Cloud Training Orchestrator สำหรับการเทรนต่อเนื่อง...')\n",
                    "log_path = '/kaggle/working/train_execution.log'\n",
                    "train_env = os.environ.copy()\n",
                    "train_env['PYTHONIOENCODING'] = 'utf-8'\n",
                    "train_env['PYTHONUTF8'] = '1'\n",
                    "train_cmd = [\n",
                    "    sys.executable,\n",
                    "    'scripts/cloud_train_orchestrator.py',\n",
                    "    '--platform', 'KAGGLE',\n",
                    "    '--base-model', 'Qwen/Qwen2.5-7B-Instruct',\n",
                    "    '--hf-repo', 'pphothidaen/qwen2.5-7b-bazi-instruct-4bit',\n",
                    "    '--dataset-path', local_dataset_target,\n",
                    "    '--epochs', '3',\n",
                    "]\n",
                    "if 'HITL_EXPORT_PATH' in os.environ:\n",
                    "    train_cmd.extend(['--dataset-path', os.environ['HITL_EXPORT_PATH']])\n",
                    "elif dataset_cmd_path:\n",
                    "    train_cmd.extend(['--dataset-path', dataset_cmd_path])\n",
                    "proc = subprocess.Popen(train_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', env=train_env)\n",
                    "with open(log_path, 'w', encoding='utf-8', errors='replace') as log_f:\n",
                    "    for line in iter(proc.stdout.readline, ''):\n",
                    "        safe_line = line.encode('utf-8', errors='replace').decode('utf-8', errors='replace')\n",
                    "        sys.stdout.write(safe_line)\n",
                    "        sys.stdout.flush()\n",
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
                    "    raise RuntimeError(f'[ERROR] Training orchestrator failed (exit code {proc.returncode}).\\n--- Tail of train_execution.log ---\\n{log_tail}')\n",
                    "print('[OK] Training pipeline completed successfully! โมเดลถูกอัปโหลดขึ้น Hugging Face เรียบร้อยแล้ว!')\n"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="HoroConsultant Kaggle Notebook Automation CLI")
    parser.add_argument("--setup", action="store_true", help="Setup credentials and generate kernel metadata & notebook")
    parser.add_argument("--push", action="store_true", help="Push & trigger notebook execution on Kaggle GPU")
    parser.add_argument("--status", action="store_true", help="Check notebook execution status on Kaggle")
    parser.add_argument("--pull", action="store_true", help="Pull latest notebook, outputs, and metadata down from Kaggle")
    parser.add_argument("--output", action="store_true", help="Pull kernel output files specifically via 'kaggle kernels output'")
    parser.add_argument("--dataset-path", default=None, help="Explicit dataset JSONL path for training run")
    parser.add_argument("--dest", default=str(KERNEL_DIR), help="Destination directory for output files (default: project/kaggle_kernel)")
    parser.add_argument("--accelerator", default="nvidiaTeslaT4x2", help="Specify Kaggle GPU accelerator (default: nvidiaTeslaT4x2, optional: nvidiaTeslaP100)")

    args = parser.parse_args()

    if not any([args.setup, args.push, args.status, args.pull, args.output]):
        args.setup = True

    if args.setup:
        if not setup_kaggle_credentials(write_file=True):
            return 1
        create_kernel_files(args.accelerator, dataset_path=args.dataset_path)

    elif args.push and args.dataset_path:
        create_kernel_files(args.accelerator, dataset_path=args.dataset_path)

    success = True
    if args.push:
        if not setup_kaggle_credentials(write_file=False):
            return 1
        if not METADATA_FILE.exists() or not NOTEBOOK_FILE.exists():
            logger.error("[ERROR] Kaggle kernel files are missing; run --setup before --push.")
            return 1
        push_args = ["kernels", "push", "-p", str(KERNEL_DIR)]
        success = run_kaggle_cmd(push_args) and success

    if args.status:
        if not setup_kaggle_credentials(write_file=False):
            return 1
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        success = run_kaggle_cmd(["kernels", "status", kernel_id]) and success

    if args.output:
        if not setup_kaggle_credentials(write_file=False):
            return 1
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        dest_dir = Path(args.dest)
        dest_dir.mkdir(parents=True, exist_ok=True)
        success = run_kaggle_cmd(["kernels", "output", kernel_id, "-p", str(dest_dir)]) and success

    if args.pull:
        if not setup_kaggle_credentials(write_file=False):
            return 1
        username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
        kernel_id = f"{username}/horoconsultant-finetune-pipeline"
        dest_dir = Path(args.dest)
        dest_dir.mkdir(parents=True, exist_ok=True)
        # 1. Pull notebook & metadata
        pull_success = run_kaggle_cmd(["kernels", "pull", kernel_id, "-p", str(dest_dir), "-m"])
        # 2. Pull output files (train_execution.log, summaries, adapters)
        output_success = run_kaggle_cmd(["kernels", "output", kernel_id, "-p", str(dest_dir)])
        success = (pull_success or output_success) and success
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
