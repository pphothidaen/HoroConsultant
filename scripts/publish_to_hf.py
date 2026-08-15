"""
scripts/publish_to_hf.py
========================
Automated Hugging Face Model Publisher for HoroConsultant Project.

Uploads fused MLX model (`project/models/qwen2.5-bazi-fused`) or
LoRA adapter (`project/models/qwen2.5-bazi-adapter`) to Hugging Face Hub.

Usage
-----
    python3 scripts/publish_to_hf.py [--repo-id REPO_ID] [--private]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from huggingface_hub import HfApi, create_repo
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


def publish_model(
    model_dir: Path,
    repo_id: str,
    private: bool = False,
) -> bool:
    """Upload model directory to Hugging Face Hub repository."""
    if not HF_AVAILABLE:
        print("❌ huggingface_hub package not found. Run 'pip install huggingface_hub'")
        return False

    token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or os.getenv("HF_API_TOKEN")
        or os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HUGGING_FACE_TOKEN")
    )
    if not token:
        print("❌ HF token environment variable not found in .env")
        return False

    api = HfApi(token=token)

    try:
        user_info = api.whoami()
        print(f"🔐 Authenticated as Hugging Face user: {user_info['name']}")
    except Exception as e:
        print(f"❌ HF Token authentication failed: {e}")
        return False

    if not model_dir.exists():
        print(f"❌ Target model directory does not exist: {model_dir}")
        return False

    print(f"📦 Creating/verifying Hugging Face repository '{repo_id}'...")
    try:
        create_repo(
            repo_id=repo_id,
            token=token,
            private=private,
            exist_ok=True,
            repo_type="model",
        )
        print(f"✅ Repository ready: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"⚠️ Repo creation note: {e}")

    print(f"🚀 Uploading model contents from '{model_dir}' to '{repo_id}'...")
    try:
        api.upload_folder(
            folder_path=str(model_dir),
            repo_id=repo_id,
            repo_type="model",
        )
        print("\n🎉 Model successfully published to Hugging Face Hub!")
        print(f"🔗 View Repository: https://huggingface.co/{repo_id}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Publish HoroConsultant model to Hugging Face Hub")
    username = os.getenv("HF_USERNAME", "pphothidaen")
    default_repo = f"{username}/qwen2.5-7b-bazi-instruct-4bit"
    default_dir  = Path("project/models/qwen2.5-bazi-fused")

    parser.add_argument("--repo-id", default=default_repo, help=f"HF Repository ID (default: {default_repo})")
    parser.add_argument("--model-dir", type=Path, default=default_dir, help="Model directory to upload")
    parser.add_argument("--private", action="store_true", help="Create private repository")

    args = parser.parse_args()

    # Fallback to adapter if fused model directory does not exist yet
    target_dir = args.model_dir
    if not target_dir.exists():
        adapter_dir = Path("project/models/qwen2.5-bazi-adapter")
        if adapter_dir.exists():
            print(f"ℹ️ Fused model not found at '{target_dir}'. Using adapter directory '{adapter_dir}' instead.")
            target_dir = adapter_dir

    success = publish_model(target_dir, args.repo_id, args.private)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
