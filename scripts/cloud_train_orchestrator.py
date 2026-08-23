"""
scripts/cloud_train_orchestrator.py
===================================
Production Fine-Tuning Orchestrator for Cloud Platforms (Kaggle / Lightning AI / SageMaker / Colab).

Workflow:
1. Fetches latest verified training dataset from Supabase DB (with fallback to local `train.jsonl`).
2. Loads base model (`Qwen/Qwen2.5-7B-Instruct` or `typhoon-v1.5-8b-instruct`) in 4-bit quantization (BitsAndBytes).
3. Configures PEFT / LoRA adapter.
4. Executes SFTTrainer loop with checkpoint saving.
5. Pushes trained LoRA adapter to Hugging Face Hub repository (`pphothidaen/qwen2.5-7b-bazi-instruct-4bit`).
6. Logs completion metadata and loss back to Supabase `model_checkpoints`.

Usage (On Kaggle / Lightning AI Notebook or Terminal):
---------------------------------------------------
    python3 scripts/cloud_train_orchestrator.py [--platform KAGGLE_T4] [--epochs 3] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config
from project.core.supabase_db import SupabaseDB

# Force UTF-8 and replace invalid unicode surrogates to prevent ipykernel UnicodeEncodeError
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "600"
os.environ["HF_HUB_MAX_RETRIES"] = "20"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TQDM_DISABLE"] = "1"
os.environ["BITSANDBYTES_NOWELCOME"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Root Cause Fix: Suppress dataset fingerprint hashing warning for inner tokenization closures
import warnings

warnings.filterwarnings("ignore", message=".*couldn't be hashed properly.*")
warnings.filterwarnings("ignore", category=UserWarning, module="datasets.*")

# Triton 3.x compatibility shim for bitsandbytes (prevents ModuleNotFoundError: No module named 'triton.ops.matmul_perf_model')
import types

try:
    import triton
except (ImportError, ModuleNotFoundError):
    triton = types.ModuleType("triton")
    triton.__path__ = []
    sys.modules["triton"] = triton

if not hasattr(triton, "ops") or "triton.ops" not in sys.modules:
    triton_ops = types.ModuleType("triton.ops")
    triton_ops.__path__ = []
    setattr(triton, "ops", triton_ops)
    sys.modules["triton.ops"] = triton_ops

triton_ops = sys.modules["triton.ops"]
if not hasattr(triton_ops, "__path__"):
    triton_ops.__path__ = []

if not hasattr(triton_ops, "matmul_perf_model") or "triton.ops.matmul_perf_model" not in sys.modules:
    triton_ops_matmul = types.ModuleType("triton.ops.matmul_perf_model")
    triton_ops_matmul.early_config_prune = lambda *a, **k: None
    triton_ops_matmul.estimate_matmul_time = lambda *a, **k: 0
    setattr(triton_ops, "matmul_perf_model", triton_ops_matmul)
    sys.modules["triton.ops.matmul_perf_model"] = triton_ops_matmul
# Global PyTorch Embedding Guard: Prevents RuntimeError on FloatTensor input_ids during mixed-precision / accelerate training
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    _orig_nn_embedding_forward = nn.Embedding.forward
    def _safe_nn_embedding_forward(self, input):
        if isinstance(input, torch.Tensor) and input.dtype not in (torch.long, torch.int, torch.int32, torch.int64):
            input = input.long()
        return _orig_nn_embedding_forward(self, input)
    nn.Embedding.forward = _safe_nn_embedding_forward

    _orig_f_embedding = F.embedding
    def _safe_f_embedding(input, weight, *args, **kwargs):
        if isinstance(input, torch.Tensor) and input.dtype not in (torch.long, torch.int, torch.int32, torch.int64):
            input = input.long()
        return _orig_f_embedding(input, weight, *args, **kwargs)
    F.embedding = _safe_f_embedding
except Exception:
    pass


def _ensure_bitsandbytes_cuda_binary() -> bool:
    """
    Root Cause Fix for bitsandbytes CUDA binary mismatch on Kaggle / CUDA 12.x environments:
    If PyTorch reports CUDA 12.x (e.g. 12.8) and libbitsandbytes_cuda128.so is requested
    but missing, dynamically symlink/copy the highest available CUDA binary
    (e.g. libbitsandbytes_cuda124.so) to libbitsandbytes_cuda128.so inside bitsandbytes folder.
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return False

        import bitsandbytes as bnb
        bnb_dir = Path(bnb.__file__).parent

        cuda_ver_str = getattr(torch.version, "cuda", "") or ""
        cuda_clean = cuda_ver_str.replace(".", "")
        if cuda_clean:
            target_so = bnb_dir / f"libbitsandbytes_cuda{cuda_clean}.so"
            if not target_so.exists():
                available = sorted(list(bnb_dir.glob("libbitsandbytes_cuda*.so")), reverse=True)
                if available:
                    best = available[0]
                    try:
                        os.symlink(best, target_so)
                        sys.stdout.write(f"[OK] BNB CUDA Fix: Symlinked {best.name} -> {target_so.name}\n")
                    except Exception:
                        import shutil
                        shutil.copy(best, target_so)
                        sys.stdout.write(f"[OK] BNB CUDA Fix: Copied {best.name} -> {target_so.name}\n")
                    return True
        return True
    except Exception:
        return False


def _format_conversation_example(example: dict) -> dict:
    """Top-level dataset formatting function to enable pickling & fingerprint hashing in Hugging Face datasets."""
    items = example.get("conversations") or example.get("messages") or []
    formatted_convs = []
    if isinstance(items, list):
        for msg in items:
            if isinstance(msg, dict):
                role = msg.get("role", "")
                if role in ("human", "user"):
                    role = "user"
                elif role in ("gpt", "assistant"):
                    role = "assistant"
                elif role == "system":
                    role = "system"
                content = msg.get("value") or msg.get("content", "")
                if content:
                    formatted_convs.append({"role": role, "content": content})
    if formatted_convs:
        text = "\n".join([f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>" for m in formatted_convs])
    else:
        raw_text = example.get("text", "")
        text = raw_text if isinstance(raw_text, str) else str(raw_text)

    return {"text": text}

class SafeAsciiLogFormatter(logging.Formatter):
    """Logging formatter that automatically strips emojis and surrogate characters."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return original.encode('ascii', errors='ignore').decode('ascii')

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(SafeAsciiLogFormatter("%(asctime)s [%(levelname)s] %(message)s"))
logger = logging.getLogger("cloud_train")
logger.setLevel(logging.INFO)
logger.handlers = [_handler]


def prepare_dataset(output_jsonl: Path, dataset_path: str | None = None) -> Path:
    """
    Fetch and compile the complete training corpus using Hybrid Ingestion:
    1. Explicit path (if provided)
    2. Supabase verified QA exports (if configured)
    3. Kaggle mounted input datasets (/kaggle/input/**)
    4. Curated local Hugging Face corpus (project/data/bazi_hf_curated_corpus.jsonl)
    5. Dynamic Hugging Face Liked Datasets sync (@pphothidaen)
    6. Local fallback (project/rag/datasets/train.jsonl)
    """
    if dataset_path:
        explicit_path = Path(dataset_path).expanduser()
        if explicit_path.exists():
            logger.info(f"[INFO] Using explicit dataset path '{explicit_path}'")
            return explicit_path
        logger.warning(
            f"[WARN] Explicit dataset path '{explicit_path}' not found. Falling back to automated dataset source."
        )

    logger.info("[DATA] Initializing Hybrid Metaphysics Data Ingestion...")
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    all_records = []
    seen_hashes = set()

    def _add_jsonl_file(fpath: Path, tag: str):
        count = 0
        try:
            for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        all_records.append(s)
                        count += 1
                except Exception:
                    pass
            if count > 0:
                logger.info(f"[{tag}] Ingested {count} records from {fpath.name}")
        except Exception as e:
            logger.warning(f"[{tag}] Note reading {fpath}: {e}")

    # 1. Check Supabase DB
    db = SupabaseDB()
    if db.is_configured():
        temp_sb = output_jsonl.parent / "temp_supabase.jsonl"
        sb_count = db.export_verified_qa_to_jsonl(temp_sb)
        if sb_count > 0:
            _add_jsonl_file(temp_sb, "SUPABASE")
            if temp_sb.exists():
                temp_sb.unlink()

    # 2. Check Kaggle mounted datasets in /kaggle/input (e.g. horoconsultant-distilled-dataset)
    kaggle_input = Path("/kaggle/input")
    if kaggle_input.exists():
        kaggle_files = list(kaggle_input.glob("**/*.jsonl")) + list(kaggle_input.glob("**/*.json"))
        if kaggle_files:
            logger.info(f"[KAGGLE DATA] Discovered {len(kaggle_files)} dataset file(s) in /kaggle/input...")
            for kf in kaggle_files:
                _add_jsonl_file(kf, "KAGGLE DATA")

    # 3. Dynamic Hugging Face Liked Datasets Ingestion Layer
    hf_token = os.getenv("HF_TOKEN") or Config.HF_TOKEN
    try:
        from scripts.harvest_hf_liked_datasets import fetch_liked_dataset_names, harvest_dataset_repo
        liked_repos = fetch_liked_dataset_names(hf_token)
        if liked_repos:
            logger.info(f"[DYNAMIC HF] Discovered {len(liked_repos)} liked datasets on Hugging Face. Verifying live fresh records...")
            dynamic_added = 0
            for repo_name in liked_repos:
                recs = harvest_dataset_repo(repo_name, hf_token)
                for r in recs:
                    try:
                        s = json.dumps(r, ensure_ascii=False)
                        h = hashlib.sha256(s.encode("utf-8")).hexdigest()
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            all_records.append(s)
                            dynamic_added += 1
                    except Exception:
                        pass
            if dynamic_added > 0:
                logger.info(f"[DYNAMIC HF] Added {dynamic_added} fresh unique records dynamically from Hugging Face liked datasets!")
            else:
                logger.info("[DYNAMIC HF] Liked dataset records already synchronized (0 duplicates added).")
    except Exception as hf_err:
        logger.warning(f"[DYNAMIC HF] Dynamic HF ingestion bypassed or offline: {hf_err}")

    # 4. Check curated local Hugging Face corpus
    curated_hf_corpus = ROOT_DIR / "project" / "data" / "bazi_hf_curated_corpus.jsonl"
    if curated_hf_corpus.exists():
        _add_jsonl_file(curated_hf_corpus, "HF CURATED CORPUS")

    # 4. Check base train.jsonl
    base_train = ROOT_DIR / "project" / "rag" / "datasets" / "train.jsonl"
    if base_train.exists():
        _add_jsonl_file(base_train, "BASE DATASET")

    # 5. Check hitl_approved.jsonl
    hitl_train = ROOT_DIR / "project" / "rag" / "datasets" / "hitl_approved.jsonl"
    if hitl_train.exists():
        _add_jsonl_file(hitl_train, "HITL APPROVED")

    if all_records:
        output_jsonl.write_text("\n".join(all_records) + "\n", encoding="utf-8")
        logger.info(f"[OK] Hybrid Ingestion compiled {len(all_records)} unique records into '{output_jsonl}'")
        return output_jsonl

    raise FileNotFoundError("[ERROR] No valid dataset records found from any hybrid sources!")


def _setup_cuda_environment_for_device() -> dict:
    """
    Detect GPU compute capability and set environment variables for stable CUDA execution.
    Returns a dict with keys: 'is_sm75' (T4), 'compute_cap', 'device_name'.
    Must be called before any CUDA operations or library imports that trigger CUDA kernels.
    """
    import torch
    info = {"is_sm75": False, "compute_cap": (0, 0), "device_name": "CPU"}
    if not torch.cuda.is_available():
        return info

    device_name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)  # e.g. (7, 5) for T4, (8, 0) for A100
    info["device_name"] = device_name
    info["compute_cap"] = cap

    # Tesla T4 is sm_75 (7.5). bfloat16 requires sm_80+.
    is_sm75 = (cap[0] == 7 and cap[1] == 5)
    info["is_sm75"] = is_sm75

    # Inspect PyTorch binary compiled CUDA arch list
    arch_list = torch.cuda.get_arch_list() if hasattr(torch.cuda, "get_arch_list") else []
    target_sm = f"sm_{cap[0]}{cap[1]}"
    arch_match = any(target_sm in a or f"{cap[0]}.{cap[1]}" in a for a in arch_list) if arch_list else True
    info["arch_list"] = arch_list
    info["arch_match"] = arch_match

    if arch_list:
        logger.info(f"   [AUDIT] PyTorch Compiled Arch List: {arch_list}")
        if not arch_match:
            logger.warning(f"   [WARNING] WARNING: PyTorch wheel does NOT contain compiled binary for {target_sm} ({device_name})!")

    # Unset any forced BNB_CUDA_VERSION override to let bitsandbytes load native CUDA library cleanly
    os.environ.pop("BNB_CUDA_VERSION", None)

    if is_sm75:
        logger.info(f"   [TARGET] GPU Architecture: sm_75 ({device_name}) — Applying T4-specific stability settings.")
        os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "7.5")
        os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")
        logger.info("   [OK] Set TORCH_CUDA_ARCH_LIST=7.5, CUDA_MODULE_LOADING=LAZY")
    else:
        sm_str = f"{cap[0]}{cap[1]}"
        logger.info(f"   [TARGET] GPU Architecture: sm_{sm_str} ({device_name})")
        os.environ.setdefault("TORCH_CUDA_ARCH_LIST", f"{cap[0]}.{cap[1]}")
        os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")

    return info


def run_preflight_environment_audit() -> dict:
    """
    Executes instant (<0.5s) pre-flight diagnostic tests to catch CUDA driver mismatches,
    broken PyTorch kernel images, or library signature incompatibilities BEFORE starting
    heavy model downloads or cloud training.
    """
    logger.info("[CHECK] Running Instant Pre-Flight Environment Audit...")
    results = {"cuda_ok": False, "peft_ok": False, "trl_ok": False, "warnings": [], "gpu_info": {}}

    try:
        import torch
        if torch.cuda.is_available():
            # First: setup env vars for stable CUDA execution
            gpu_info = _setup_cuda_environment_for_device()
            results["gpu_info"] = gpu_info
            device_name = gpu_info["device_name"]
            logger.info(f"   [CUDA] CUDA Device: {device_name} (Total GPUs: {torch.cuda.device_count()})")

            # Run pure PyTorch CUDA kernel execution tests (avoids bitsandbytes)
            try:
                # 1. Test float32 CUDA arithmetic (universal support across all CUDA drivers)
                t32 = torch.ones((4, 4), device="cuda:0", dtype=torch.float32)
                res32 = (t32 + t32).cpu()
                assert res32[0, 0].item() == 2.0
                results["cuda_ok"] = True
                logger.info("   [OK] CUDA Kernel Execution Test (float32): PASSED")

                # 2. Test float16 CUDA arithmetic
                try:
                    t16 = torch.ones((4, 4), device="cuda:0", dtype=torch.float16)
                    res16 = (t16 + t16).cpu()
                    assert res16[0, 0].item() == 2.0
                    results["float16_ok"] = True
                    logger.info("   [OK] CUDA Kernel Execution Test (float16): PASSED")
                except Exception as fp16_err:
                    results["float16_ok"] = False
                    logger.warning(f"   [WARNING] CUDA float16 kernel unavailable ({fp16_err}). Will use float32 fallback.")
            except Exception as cuda_err:
                logger.error(f"   [ERROR] CUDA Kernel Execution Test FAILED: {cuda_err}")
                results["warnings"].append(f"CUDA Kernel Failure: {cuda_err}")
                results["cuda_ok"] = False
        else:
            logger.info("   [INFO] CPU Mode (No CUDA GPU detected)")
            results["cuda_ok"] = True
    except Exception as e:
        logger.error(f"   [ERROR] PyTorch Import Error: {e}")

    try:
        import inspect

        from peft import LoraConfig
        peft_config = LoraConfig(r=8, lora_alpha=16, task_type="CAUSAL_LM")
        results["peft_ok"] = True
        logger.info("   [OK] PEFT Adapter Configuration Test: PASSED")
    except Exception as peft_err:
        logger.error(f"   [ERROR] PEFT Config Error: {peft_err}")

    try:
        import inspect

        from trl import SFTConfig
        sig = inspect.signature(SFTConfig.__init__)
        has_max_seq = "max_seq_length" in sig.parameters
        results["trl_ok"] = True
        logger.info(f"   [OK] TRL SFTConfig Test: PASSED (accepts max_seq_length in __init__: {has_max_seq})")
    except Exception as trl_err:
        logger.info(f"   [INFO] TRL SFTConfig Check Note: {trl_err}")

    return results


def create_sft_trainer(
    model,
    tokenizer,
    train_dataset,
    peft_config,
    training_args,
    dataset_text_field: str = None,
    formatting_func = None,
    max_seq_length: int = 512,
    hf_repo_id: str | None = None,
):
    """
    Instantiates training pipeline using standard Hugging Face Trainer
    with pre-tokenized dataset, PEFT LoRA adapter (with continual checkpoint warm-start),
    and dynamic DataCollator.
    """
    from transformers import Trainer, DataCollatorForLanguageModeling
    from peft import get_peft_model, PeftModel

    # Wrap model with PEFT LoRA if not already wrapped
    if peft_config is not None and not isinstance(model, PeftModel):
        adapter_loaded = False
        if hf_repo_id and Config.is_hf_configured():
            try:
                from huggingface_hub import HfApi
                api = HfApi(token=Config.HF_TOKEN)
                if api.repo_exists(hf_repo_id):
                    logger.info(f"   [RESUME] Found existing LoRA checkpoint on Hugging Face: '{hf_repo_id}'. Continual learning enabled!")
                    model = PeftModel.from_pretrained(model, hf_repo_id, is_trainable=True)
                    adapter_loaded = True
                    logger.info(f"   [OK] Resumed trainable LoRA adapter from latest checkpoint '{hf_repo_id}'.")
            except Exception as resume_err:
                logger.warning(f"   [INFO] Checkpoint warm-start note: {resume_err}")

        if not adapter_loaded:
            try:
                model = get_peft_model(model, peft_config)
                logger.info("   [OK] Attached fresh PEFT LoRA adapter to base causal LM.")
            except Exception as peft_wrap_err:
                logger.warning(f"   [WARNING] PEFT wrapping skipped/failed ({peft_wrap_err})")

        if hasattr(model, "print_trainable_parameters"):
            model.print_trainable_parameters()

    class SafeDataCollator(DataCollatorForLanguageModeling):
        def torch_call(self, examples):
            batch = super().torch_call(examples)
            if "labels" in batch and hasattr(batch["labels"], "to"):
                batch["labels"] = batch["labels"].to(torch.long)
            if "input_ids" in batch and hasattr(batch["input_ids"], "to"):
                batch["input_ids"] = batch["input_ids"].to(torch.long)
            return batch

    collator = SafeDataCollator(tokenizer=tokenizer, mlm=False)

    # Safe Trainer patch to prevent NotImplementedError on meta/offloaded tensors and float labels
    try:
        _orig_move = getattr(Trainer, "_move_model_to_device", None)
        def _safe_move(self, m, dev):
            if getattr(self, "is_model_parallel", False) or hasattr(m, "hf_device_map") or hasattr(m, "device_map"):
                return
            try:
                has_meta = any(p.is_meta for p in m.parameters()) if hasattr(m, "parameters") else False
                if has_meta:
                    logger.info("   [OK] Model contains meta/offloaded parameters. Skipping Trainer._move_model_to_device.")
                    return
            except Exception:
                pass
            try:
                if _orig_move is not None:
                    _orig_move(self, m, dev)
                else:
                    m.to(dev)
            except Exception as move_err:
                logger.warning(f"   [WARNING] Trainer._move_model_to_device bypassed ({move_err})")
        Trainer._move_model_to_device = _safe_move
        Trainer._remove_unused_columns = lambda self, dataset, description=None: dataset

        _orig_compute_loss = getattr(Trainer, "compute_loss", None)
        if _orig_compute_loss is not None:
            def _safe_compute_loss(self, m, inputs, return_outputs=False, num_items_in_batch=None):
                if isinstance(inputs, dict):
                    if "labels" in inputs and hasattr(inputs["labels"], "long"):
                        inputs["labels"] = inputs["labels"].long()
                    if "input_ids" in inputs and hasattr(inputs["input_ids"], "long"):
                        inputs["input_ids"] = inputs["input_ids"].long()
                if num_items_in_batch is not None:
                    try:
                        return _orig_compute_loss(self, m, inputs, return_outputs=return_outputs, num_items_in_batch=num_items_in_batch)
                    except TypeError:
                        return _orig_compute_loss(self, m, inputs, return_outputs=return_outputs)
                return _orig_compute_loss(self, m, inputs, return_outputs=return_outputs)
            Trainer.compute_loss = _safe_compute_loss
            logger.info("   [OK] Registered long-dtype compute_loss guard on Transformers Trainer.")
    except Exception:
        pass

    # Ensure max_seq_length / remove_unused_columns configured on training_args
    if hasattr(training_args, "remove_unused_columns"):
        try:
            training_args.remove_unused_columns = False
        except Exception:
            pass

    logger.info("[OK] Initializing standard Hugging Face Trainer with pre-tokenized dataset and DataCollator.")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        data_collator=collator,
    )

    if hasattr(trainer, "_remove_unused_columns"):
        try:
            trainer._remove_unused_columns = lambda dataset, description=None: dataset
        except Exception:
            pass
    if hasattr(trainer, "args") and hasattr(trainer.args, "remove_unused_columns"):
        try:
            trainer.args.remove_unused_columns = False
        except Exception:
            pass

    return trainer


def run_training_pipeline(
    dataset_path: Path,
    platform: str,
    base_model: str,
    output_dir: Path,
    hf_repo_id: str,
    epochs: int = 3,
    dry_run: bool = False,
) -> bool:
    """Execute PyTorch / PEFT fine-tuning and upload to Hugging Face Hub."""
    logger.info(f"[START] Starting Cloud Fine-Tuning Pipeline on platform [{platform}]...")
    logger.info(f"   Base Model: {base_model}")
    logger.info(f"   Dataset: {dataset_path}")
    logger.info(f"   HF Repo ID: {hf_repo_id}")

    # Run instant pre-flight diagnostic check
    audit_results = run_preflight_environment_audit()
    if audit_results.get("warnings"):
        logger.warning(f"[WARNING] Pre-flight audit notice: {', '.join(audit_results['warnings'])}")

    # Graceful Fallback Guard: If CUDA kernel execution fails (e.g. sm_60 P100 lacking PyTorch binary), fall back to CPU
    cuda_hardware_ok = audit_results.get("cuda_ok", True)
    if not cuda_hardware_ok:
        logger.warning("[WARNING] CUDA pre-flight kernel execution test failed on this device (e.g. sm_60/P100 unsupported by PyTorch wheel). Gracefully falling back to CPU execution mode.")

    if "mlx-community" in base_model:
        logger.warning(f"[WARNING] Base model '{base_model}' is an MLX format model. Automatically switching to PyTorch base model 'Qwen/Qwen2.5-7B-Instruct' for Cloud training.")
        base_model = "Qwen/Qwen2.5-7B-Instruct"

    if base_model == Config.HF_REPO_ID or base_model.endswith("-4bit") or "bazi-instruct" in base_model:
        logger.warning(f"[WARNING] Base model '{base_model}' appears to be an adapter or quantized repository. Automatically switching to base model 'Qwen/Qwen2.5-7B-Instruct' for Cloud training.")
        base_model = "Qwen/Qwen2.5-7B-Instruct"

    if dry_run:
        logger.info(" DRY RUN MODE: Validated dataset & setup cleanly. Skipping heavy GPU training.")
        return True

    try:
        import torch
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from trl import SFTTrainer
    except ImportError as e:
        logger.error(f"[ERROR] Missing required PyTorch/Transformers packages: {e}")
        logger.error("Run: pip install transformers peft bitsandbytes datasets trl huggingface_hub accelerate")
        return False

    # 1. Quantization / Model Loading Config
    use_cuda = torch.cuda.is_available() and cuda_hardware_ok

    # --- GPU Architecture Detection (MUST run before any CUDA library imports) ---
    # This sets BNB_CUDA_VERSION, TORCH_CUDA_ARCH_LIST, CUDA_MODULE_LOADING env vars.
    gpu_info = _setup_cuda_environment_for_device() if use_cuda else {}
    is_sm75 = gpu_info.get("is_sm75", False)  # Tesla T4 = sm_75

    # Detect Kaggle / cloud environment
    is_kaggle = (
        os.path.exists("/kaggle")
        or "KAGGLE" in platform.upper()
        or os.getenv("KAGGLE_DATA_PROXY_TOKEN") is not None
    )

    # Force float16 on sm_75 (T4): T4 does NOT support bfloat16 natively (requires sm_80+).
    # Using bfloat16 on T4 triggers silent CUDA errors during dtype casting in PEFT.
    cap = (0, 0)
    if use_cuda:
        cap = gpu_info.get("compute_cap", (0, 0))
        if is_sm75 or "T4" in gpu_info.get("device_name", "") or is_kaggle or cap < (8, 0):
            compute_dtype = torch.float16
            logger.info("   [INFO] Kaggle/T4/sm_60-75 platform detected: Forcing float16 compute dtype (sm_75 has no native bfloat16).")
        elif cap >= (8, 0) and torch.cuda.is_bf16_supported():
            compute_dtype = torch.bfloat16
            logger.info(f"   [OK] sm_{cap[0]}{cap[1]} detected: Using bfloat16 compute dtype.")
        else:
            compute_dtype = torch.float16
            logger.info("   [INFO] Defaulting to float16 compute dtype.")
    else:
        compute_dtype = torch.float32

    # Quantization check (BitsAndBytes 4-bit)
    bnb_available = False
    if use_cuda:
        try:
            _ensure_bitsandbytes_cuda_binary()
            import bitsandbytes as bnb
            bnb_available = True
            logger.info("   [OK] BitsAndBytes 4-bit quantization initialized successfully.")
        except Exception as bnb_err:
            logger.warning(f"BitsAndBytes CUDA check failed ({bnb_err}). 4-bit quantization will be bypassed.")

    bnb_config = None
    if bnb_available:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )

    logger.info(f"[MODEL] Loading tokenizer and base model '{base_model}'...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if use_cuda:
        num_gpus = torch.cuda.device_count()
        if num_gpus > 1:
            logger.info(f"[CUDA] Multi-GPU detected ({num_gpus} GPUs available). Distributing model with device_map='auto'.")
            device_map = "auto"
        else:
            device_map = {"": 0}
    else:
        device_map = None

    model = None
    max_download_retries = 5
    if use_cuda and bnb_config is not None:
        for attempt in range(1, max_download_retries + 1):
            try:
                logger.info(f"[CUDA] Attempting 4-bit BitsAndBytes quantization model load (Attempt {attempt}/{max_download_retries})...")
                model = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    quantization_config=bnb_config,
                    torch_dtype=compute_dtype,
                    device_map=device_map,
                    low_cpu_mem_usage=(device_map is not None),
                    trust_remote_code=True,
                    attn_implementation="sdpa",
                )
                model = prepare_model_for_kbit_training(model)
                logger.info("[OK] Successfully loaded 4-bit quantized model.")
                break
            except Exception as e:
                logger.warning(f"[WARNING] 4-bit BitsAndBytes quantization load attempt {attempt} failed ({e}).")
                if attempt < max_download_retries:
                    import time
                    time.sleep(5 * attempt)
                    continue
                else:
                    logger.warning("[WARNING] All 4-bit quantization load attempts exhausted. Falling back to standard precision loading...")
                    model = None

    if model is None:
        for attempt in range(1, max_download_retries + 1):
            try:
                logger.info(f"[MODEL] Loading base model in standard precision ({compute_dtype}) (Attempt {attempt}/{max_download_retries})...")
                model = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    torch_dtype=compute_dtype,
                    device_map=device_map,
                    low_cpu_mem_usage=(device_map is not None),
                    trust_remote_code=True,
                    attn_implementation="sdpa" if use_cuda else None,
                )
                logger.info(f"[OK] Successfully loaded model with precision {compute_dtype}.")
                break
            except Exception as e:
                logger.warning(f"[WARNING] Standard precision load attempt {attempt} failed ({e}).")
                if attempt < max_download_retries:
                    import time
                    time.sleep(5 * attempt)
                    continue
                else:
                    raise e

    if use_cuda and (is_kaggle or is_sm75 or cap < (8, 0)):
        compute_dtype = torch.float16
        if device_map is None and hasattr(model, "to") and getattr(model, "dtype", None) != torch.float16:
            logger.info(f"[CAST] Converting base model weights from {getattr(model, 'dtype', 'unknown')} to {compute_dtype} for T4/sm_75 compatibility...")
            try:
                model = model.to(torch.float16)
            except Exception as cast_err:
                logger.warning(f"Weight cast skipped ({cast_err}).")

    # Ensure input embeddings and model forward strictly enforce LongTensor input_ids
    try:
        def _ensure_long_indices_hook(module, args):
            if args and len(args) > 0:
                idx = args[0]
                if hasattr(idx, "dtype") and getattr(idx, "dtype", None) not in (torch.long, torch.int, torch.int32, torch.int64):
                    return (idx.long(),) + args[1:]
            return args

        input_embeddings = getattr(model, "get_input_embeddings", lambda: None)()
        if input_embeddings is not None and hasattr(input_embeddings, "register_forward_pre_hook"):
            input_embeddings.register_forward_pre_hook(_ensure_long_indices_hook)
            logger.info("   [OK] Registered long-dtype pre-hook on input embeddings.")
    except Exception as hook_err:
        logger.info(f"   [INFO] Embedding long-dtype hook note: {hook_err}")




    # 2. LoRA Config
    # On sm_75/T4 (Kaggle), PEFT's `cast_adapter_dtype` calls `param.data.to(torch.float32)`
    # which triggers `cudaErrorNoKernelImageForDevice` because bitsandbytes CUDA kernels
    # compiled for cu128 lack sm_75 device code. We monkey-patch the function to a no-op
    # on sm_75 devices BEFORE calling get_peft_model() / SFTTrainer().
    if use_cuda and (is_sm75 or is_kaggle):
        try:
            import peft.tuners.tuners_utils as _peft_utils
            if hasattr(_peft_utils, "cast_adapter_dtype"):
                def _safe_cast_adapter_dtype(model, adapter_name=None, autocast_adapter_dtype=True, **kwargs):
                    logger.info("   [INFO] [sm_75 patch] Skipping cast_adapter_dtype to prevent CUDA kernel mismatch.")
                _peft_utils.cast_adapter_dtype = _safe_cast_adapter_dtype
                logger.info("   [OK] Applied sm_75/T4 PEFT cast_adapter_dtype no-op patch.")
        except Exception:
            pass

    # Patch Transformers Trainer._get_num_items_in_batch to perform label mask calculation on CPU
    try:
        import transformers.trainer as _tf_trainer
        def _safe_get_num_items_in_batch(self, batch_samples, device=None):
            total = 0
            for batch in batch_samples:
                if isinstance(batch, dict) and "labels" in batch:
                    try:
                        labels = batch["labels"]
                        if hasattr(labels, "detach"):
                            labels = labels.detach().cpu()
                        total += int((labels != -100).sum().item())
                    except Exception:
                        if "input_ids" in batch:
                            total += len(batch["input_ids"])
                elif isinstance(batch, dict) and "input_ids" in batch:
                    total += len(batch["input_ids"])
            return max(total, 1)

        _tf_trainer.Trainer._get_num_items_in_batch = _safe_get_num_items_in_batch
        logger.info("   [OK] Applied Transformers Trainer._get_num_items_in_batch CPU-safe patch.")
    except Exception as tr_patch_err:
        logger.info(f"   [INFO] Trainer._get_num_items_in_batch patch note: {tr_patch_err}")

    try:
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            autocast_adapter_dtype=False,
        )
    except TypeError:
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )


    max_seq_length = 1024

    # 3. Load & Pre-format Dataset into a single string 'text' column
    logger.info(f" Pre-formatting dataset from '{dataset_path}'...")
    raw_data = load_dataset("json", data_files=str(dataset_path))

    formatted_ds = raw_data["train"].map(
        _format_conversation_example,
        remove_columns=raw_data["train"].column_names,
        desc="Formatting dataset rows into single string 'text' column",
    )

    logger.info(" Pre-tokenizing dataset into input_ids and attention_mask...")
    def _tokenize_batch(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_seq_length,
            padding=False,
        )

    train_ds = formatted_ds.map(
        _tokenize_batch,
        batched=True,
        remove_columns=formatted_ds.column_names,
        desc="Tokenizing dataset into input_ids and attention_mask",
    )

    # Disable incompatible pre-installed torchao (<0.16.0) on Kaggle/cloud to prevent PEFT ImportError
    try:
        import torchao
        v_str = getattr(torchao, "__version__", "0.0.0")
        v_parts = [int(x) for x in v_str.split(".") if x.isdigit()]
        if v_parts and tuple(v_parts[:2]) < (0, 16):
            logger.info(f"[INFO] Pre-installed torchao version ({v_str}) is < 0.16.0. Disabling torchao integration safely.")
            sys.modules["torchao"] = None
    except Exception:
        pass

    # Check WANDB_KEY for Weights & Biases live tracking
    report_to_target = "none"
    wandb_key = os.getenv("WANDB_KEY")
    if wandb_key and wandb_key.strip():
        try:
            import wandb
            wandb.login(key=wandb_key.strip())
            os.environ["WANDB_PROJECT"] = os.getenv("WANDB_PROJECT", "HoroConsultant")
            os.environ["WANDB_ENTITY"] = os.getenv("WANDB_ENTITY", "pphothidaen-")
            report_to_target = "wandb"
            logger.info("[OK] W&B authentication successful. Live metrics logging enabled (Project: HoroConsultant, Entity: pphothidaen-).")
        except Exception as e:
            logger.warning(f"[WARNING] W&B login/initialization failed ({e}). Defaulting report_to to 'none'.")

    sft_kwargs = {
        "output_dir": str(output_dir),
        "num_train_epochs": epochs,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "warmup_steps": 10,
        "logging_steps": 10,
        "save_strategy": "epoch",
        "learning_rate": 2e-4,
        "fp16": use_cuda,
        "report_to": report_to_target,
        "gradient_checkpointing": True,
        "remove_unused_columns": False,
    }

    from transformers import TrainingArguments
    training_args = TrainingArguments(**sft_kwargs)

    if hasattr(training_args, "max_seq_length") and getattr(training_args, "max_seq_length", None) is None:
        try:
            training_args.max_seq_length = max_seq_length
        except Exception:
            pass

    trainer = create_sft_trainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        peft_config=peft_config,
        training_args=training_args,
        dataset_text_field=None,
        max_seq_length=max_seq_length,
        hf_repo_id=hf_repo_id,
    )




    logger.info("️ Training model...")
    train_result = trainer.train()
    final_loss = float(train_result.training_loss)
    logger.info(f"[OK] Training completed with Final Loss: {final_loss:.4f}")

    # 4. Save Adapter locally
    adapter_path = output_dir / "final_adapter"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    logger.info(f" Saved adapter to '{adapter_path}'")

    # 5. Push to Hugging Face Hub
    if Config.is_hf_configured():
        # Pre-flight: verify token actually works before burning time on push
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=Config.HF_TOKEN)
            api.whoami()
            logger.info(f"[OK] HF_TOKEN verified (Hugging Face login OK).")
        except Exception as hf_auth_err:
            logger.error(f"[ERROR] HF_TOKEN pre-flight check failed: {hf_auth_err}. Push will be skipped.")
            logger.warning("[WARNING] HF_TOKEN not found or invalid (must start with 'hf_'). Skipping Hugging Face upload.")
            hf_push_skipped = True
        else:
            hf_push_skipped = False

        if not hf_push_skipped:
            logger.info(f" Pushing LoRA Adapter to Hugging Face Hub ({hf_repo_id})...")
            try:
                model.push_to_hub(hf_repo_id, token=Config.HF_TOKEN)
                tokenizer.push_to_hub(hf_repo_id, token=Config.HF_TOKEN)
                logger.info(f"[SUCCESS] Successfully uploaded to Hugging Face: https://huggingface.co/{hf_repo_id}")
            except Exception as e:
                logger.error(f"[WARNING] Failed to push to Hugging Face Hub: {e}")
    else:
        logger.warning("[WARNING] HF_TOKEN not found or invalid (must start with 'hf_'). Skipping Hugging Face upload.")

    # 6. Log to Supabase DB
    db = SupabaseDB()
    if db.is_configured():
        db.log_training_run(
            platform=platform,
            model_name=base_model,
            step_count=train_result.global_step,
            final_loss=final_loss,
            hf_repo_id=hf_repo_id,
            notes=f"Cloud training run on {platform}",
        )

    # 7. Auto-Save summary & Git push back to GitHub Repository
    sync_back_to_github_repo(platform, base_model, train_result.global_step, final_loss, hf_repo_id)

    return True


def sync_back_to_github_repo(
    platform: str,
    model_name: str,
    step_count: int,
    final_loss: float,
    hf_repo_id: str,
) -> bool:
    """Save post-training summary and push updated files back to GitHub repository."""
    import datetime
    import subprocess

    summary_file = ROOT_DIR / "project" / "data" / "latest_cloud_train_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    summary_data = {
        "completed_at": datetime.datetime.now().isoformat(),
        "platform": platform,
        "model_name": model_name,
        "step_count": step_count,
        "final_loss": final_loss,
        "hf_repo_id": hf_repo_id,
        "status": "COMPLETED",
    }
    summary_file.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[FILE] Saved training summary to '{summary_file}'")

    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        logger.warning("[WARNING] GH_TOKEN not found. Skipping auto git push to GitHub repository.")
        return False

    repo_url = f"https://{gh_token}@github.com/pphothidaen/HoroConsultant.git"

    logger.info(f"[GIT] Auto-committing and pushing training artifacts back to GitHub repository [{platform}]...")
    try:
        subprocess.run(["git", "config", "user.name", "HoroConsultant-Bot"], check=False)
        subprocess.run(["git", "config", "user.email", "bot@horoconsultant.local"], check=False)
        subprocess.run(["git", "add", "project/data/latest_cloud_train_summary.json"], check=False)
        subprocess.run(["git", "commit", "-m", f"auto({platform.lower()}): save post-train summary (loss: {final_loss:.4f})"], check=False)
        # Pull with rebase first to absorb any concurrent Kaggle pushes before pushing.
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], capture_output=True, text=True, check=False)
        res = subprocess.run(["git", "push", repo_url, "HEAD:main"], capture_output=True, text=True)

        if res.returncode == 0:
            logger.info("[SUCCESS] Successfully pushed post-training artifacts back to GitHub repository!")
            return True
        else:
            logger.warning(f"[WARNING] Git push note: {res.stderr}")
            return False
    except Exception as e:
        logger.warning(f"[WARNING] Git auto-sync exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="HoroConsultant Cloud Fine-Tuning Orchestrator")
    parser.add_argument(
        "--platform",
        default="KAGGLE_T4X2",
        type=str,
        help="Cloud platform name (e.g. KAGGLE_T4X2, KAGGLE_T4, KAGGLE_P100, LIGHTNING_L4, SAGEMAKER, COLAB)",
    )
    parser.add_argument("--base-model", default=Config.BASE_MODEL_NAME, help="Base model identifier")
    parser.add_argument("--hf-repo", default=Config.HF_REPO_ID, help="Hugging Face Repository ID")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--dataset-path", default=None, help="Explicit dataset JSONL path")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without running GPU training")

    args = parser.parse_args()

    temp_dataset = ROOT_DIR / "project" / "rag" / "datasets" / "cloud_train_temp.jsonl"
    output_dir = ROOT_DIR / "project" / "models" / "cloud_checkpoint"

    dataset_path = prepare_dataset(temp_dataset, dataset_path=args.dataset_path)

    success = run_training_pipeline(
        dataset_path=dataset_path,
        platform=args.platform,
        base_model=args.base_model,
        output_dir=output_dir,
        hf_repo_id=args.hf_repo,
        epochs=args.epochs,
        dry_run=args.dry_run,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
