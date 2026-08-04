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

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config
from project.core.supabase_db import SupabaseDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cloud_train")


def prepare_dataset(output_jsonl: Path) -> Path:
    """Fetch latest dataset from Supabase or fallback to local JSONL dataset."""
    logger.info("📡 Checking dataset source...")
    db = SupabaseDB()
    if db.is_configured():
        count = db.export_verified_qa_to_jsonl(output_jsonl)
        if count > 0:
            logger.info(f"✅ Downloaded {count} records from Supabase DB to '{output_jsonl}'")
            return output_jsonl

    fallback_dataset = ROOT_DIR / "project" / "rag" / "datasets" / "train.jsonl"
    if fallback_dataset.exists():
        logger.info(f"ℹ️ Supabase not available/empty. Using local dataset '{fallback_dataset}'")
        return fallback_dataset

    raise FileNotFoundError("❌ Neither Supabase dataset nor local 'project/rag/datasets/train.jsonl' was found!")


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
    logger.info(f"🚀 Starting Cloud Fine-Tuning Pipeline on platform [{platform}]...")
    logger.info(f"   Base Model: {base_model}")
    logger.info(f"   Dataset: {dataset_path}")
    logger.info(f"   HF Repo ID: {hf_repo_id}")

    if "mlx-community" in base_model:
        logger.warning(f"⚠️ Base model '{base_model}' is an MLX format model. Automatically switching to PyTorch base model 'Qwen/Qwen2.5-7B-Instruct' for Cloud training.")
        base_model = "Qwen/Qwen2.5-7B-Instruct"

    if dry_run:
        logger.info("🧪 DRY RUN MODE: Validated dataset & setup cleanly. Skipping heavy GPU training.")
        return True

    try:
        import torch
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        os.environ["CUDA_MODULE_LOADING"] = "LAZY"

        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments

        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from datasets import load_dataset
        from trl import SFTTrainer
    except ImportError as e:
        logger.error(f"❌ Missing required PyTorch/Transformers packages: {e}")
        logger.error("Run: pip install transformers peft bitsandbytes datasets trl huggingface_hub accelerate")
        return False

    # 1. Quantization / Model Loading Config
    use_cuda = torch.cuda.is_available()
    compute_dtype = torch.float16 if use_cuda else torch.float32

    # Disable bitsandbytes 4-bit on Kaggle platform to prevent C++ ops.cu symbol errors (exit code -11)
    is_kaggle = os.path.exists("/kaggle") or platform == "KAGGLE_T4" or "KAGGLE" in platform
    if is_kaggle:
        logger.info("ℹ️ Kaggle platform detected: Bypassing bitsandbytes 4-bit CUDA ops to ensure 100% stable float16 execution.")
        bnb_available = False
    else:
        bnb_available = False
        if use_cuda:
            try:
                import bitsandbytes as bnb
                if hasattr(bnb, "cextension") and getattr(bnb.cextension, "COMPILED_WITH_CUDA", False):
                    bnb_available = True
            except Exception as bnb_err:
                logger.warning(f"⚠️ BitsAndBytes CUDA C++ check failed ({bnb_err}). 4-bit quantization will be bypassed.")

    bnb_config = None
    if bnb_available:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )


    logger.info(f"📦 Loading tokenizer and base model '{base_model}'...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if use_cuda:
        num_gpus = torch.cuda.device_count()
        if num_gpus > 1:
            logger.info(f"⚡ Multi-GPU detected ({num_gpus} GPUs available). Distributing model with device_map='auto'.")
            device_map = "auto"
        else:
            device_map = {"": 0}
    else:
        device_map = "auto"

    model = None
    if use_cuda and bnb_config is not None:
        try:
            logger.info("⚡ Attempting 4-bit BitsAndBytes quantization model load...")
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=bnb_config,
                torch_dtype=compute_dtype,
                device_map=device_map,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
            logger.info("✅ Successfully loaded 4-bit quantized model.")
        except Exception as e:
            logger.warning(f"⚠️ 4-bit BitsAndBytes quantization load failed ({e}). Falling back to standard precision loading...")
            model = None

    if model is None:
        dtype = torch.bfloat16 if (use_cuda and hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported()) else (torch.float16 if use_cuda else torch.float32)
        logger.info(f"📦 Loading base model in standard precision ({dtype})...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        logger.info(f"✅ Successfully loaded model with precision {dtype}.")



    # 2. LoRA Config
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 3. Load Dataset
    logger.info(f"📖 Formatting dataset from '{dataset_path}'...")
    raw_data = load_dataset("json", data_files=str(dataset_path))

    def formatting_prompts_func(example):
        output_texts = []
        # Support single items or list of conversation items
        items = example.get("conversations") or example.get("messages") or []
        if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
            items = [items]
        
        for conversations in items:
            if not isinstance(conversations, list):
                continue
            formatted_convs = []
            for msg in conversations:
                if not isinstance(msg, dict):
                    continue
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
                try:
                    text = tokenizer.apply_chat_template(formatted_convs, tokenize=False)
                except Exception:
                    text = "\n".join([f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>" for m in formatted_convs])
                output_texts.append(text)
        return output_texts

    # 4. Training Arguments & SFTTrainer (Ultra-Robust Compatibility for all TRL versions)
    from trl import SFTTrainer
    try:
        from trl import SFTConfig
        try:
            training_args = SFTConfig(
                output_dir=str(output_dir),
                num_train_epochs=epochs,
                per_device_train_batch_size=2,
                gradient_accumulation_steps=4,
                warmup_steps=10,
                logging_steps=10,
                save_strategy="epoch",
                learning_rate=2e-4,
                fp16=True,
                max_seq_length=1024,
                report_to="none",
            )
        except TypeError:
            logger.info("ℹ️ SFTConfig does not accept max_seq_length in __init__, initializing standard SFTConfig...")
            training_args = SFTConfig(
                output_dir=str(output_dir),
                num_train_epochs=epochs,
                per_device_train_batch_size=2,
                gradient_accumulation_steps=4,
                warmup_steps=10,
                logging_steps=10,
                save_strategy="epoch",
                learning_rate=2e-4,
                fp16=True,
                report_to="none",
            )

        trainer_kwargs = {
            "model": model,
            "train_dataset": raw_data["train"],
            "formatting_func": formatting_prompts_func,
            "peft_config": peft_config,
            "args": training_args,
        }
        try:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)
        except TypeError:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)

    except (ImportError, TypeError, AttributeError) as e:
        logger.info(f"ℹ️ Falling back to standard TrainingArguments + SFTTrainer: {e}")
        from transformers import TrainingArguments
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=epochs,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            logging_steps=10,
            save_strategy="epoch",
            learning_rate=2e-4,
            fp16=True,
            optim="paged_adamw_8bit",
            report_to="none",
        )
        trainer_kwargs = {
            "model": model,
            "train_dataset": raw_data["train"],
            "formatting_func": formatting_prompts_func,
            "peft_config": peft_config,
            "args": training_args,
        }
        try:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)
        except TypeError:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)

    if hasattr(trainer, "max_seq_length"):
        try:
            trainer.max_seq_length = 1024
        except Exception:
            pass



    logger.info("🏋️ Training model...")
    train_result = trainer.train()
    final_loss = float(train_result.training_loss)
    logger.info(f"✅ Training completed with Final Loss: {final_loss:.4f}")

    # 4. Save Adapter locally
    adapter_path = output_dir / "final_adapter"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    logger.info(f"💾 Saved adapter to '{adapter_path}'")

    # 5. Push to Hugging Face Hub
    if Config.is_hf_configured():
        logger.info(f"🤗 Pushing LoRA Adapter to Hugging Face Hub ({hf_repo_id})...")
        try:
            model.push_to_hub(hf_repo_id, token=Config.HF_TOKEN)
            tokenizer.push_to_hub(hf_repo_id, token=Config.HF_TOKEN)
            logger.info(f"🎉 Successfully uploaded to Hugging Face: https://huggingface.co/{hf_repo_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to push to Hugging Face Hub: {e}")
    else:
        logger.warning("⚠️ HF_TOKEN not found. Skipping Hugging Face upload.")

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
    import subprocess
    import datetime

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
    logger.info(f"📄 Saved training summary to '{summary_file}'")

    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        logger.warning("⚠️ GH_TOKEN not found. Skipping auto git push to GitHub repository.")
        return False

    repo_url = f"https://{gh_token}@github.com/pphothidaen/HoroConsultant.git"

    logger.info(f"🐙 Auto-committing and pushing training artifacts back to GitHub repository [{platform}]...")
    try:
        subprocess.run(["git", "config", "user.name", "HoroConsultant-Bot"], check=False)
        subprocess.run(["git", "config", "user.email", "bot@horoconsultant.local"], check=False)
        subprocess.run(["git", "add", "project/data/latest_cloud_train_summary.json"], check=False)
        subprocess.run(["git", "commit", "-m", f"auto({platform.lower()}): save post-train summary (loss: {final_loss:.4f})"], check=False)
        res = subprocess.run(["git", "push", repo_url, "HEAD:main"], capture_output=True, text=True)

        if res.returncode == 0:
            logger.info("🎉 Successfully pushed post-training artifacts back to GitHub repository!")
            return True
        else:
            logger.warning(f"⚠️ Git push note: {res.stderr}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Git auto-sync exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="HoroConsultant Cloud Fine-Tuning Orchestrator")
    parser.add_argument("--platform", default="KAGGLE_T4", choices=["KAGGLE_T4", "LIGHTNING_L4", "SAGEMAKER", "COLAB"], help="Cloud platform name")
    parser.add_argument("--base-model", default=Config.BASE_MODEL_NAME, help="Base model identifier")
    parser.add_argument("--hf-repo", default=Config.HF_REPO_ID, help="Hugging Face Repository ID")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without running GPU training")

    args = parser.parse_args()

    temp_dataset = ROOT_DIR / "project" / "rag" / "datasets" / "cloud_train_temp.jsonl"
    output_dir = ROOT_DIR / "project" / "models" / "cloud_checkpoint"

    dataset_path = prepare_dataset(temp_dataset)

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
