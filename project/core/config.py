"""
project/core/config.py
======================
Centralized 2-Tier Priority Secrets & Configuration Manager for HoroConsultant.

Priority Order:
1st Priority: DOPPLER SECRETS STORE (Centralized Cloud Vault)
   If not found: Logs explicit warning [WARNING] Secret 'KEY' not found in 1st Priority (DOPPLER).
2nd Priority: PLATFORM SECRETS STORE (Kaggle Secrets / GitHub Secrets / Local .env)
"""

from __future__ import annotations

import os
import sys
import json
import logging
import urllib.request
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("config_manager")

# Load local .env if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)


def fetch_doppler_secret_via_api(key_name: str) -> Optional[str]:
    """Attempt fetching secret directly from Doppler API if DOPPLER_TOKEN is available."""
    doppler_token = os.getenv("DOPPLER_TOKEN")
    if not doppler_token:
        return None
    try:
        url = f"https://api.doppler.com/v3/configs/config/secret?secret={key_name}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {doppler_token}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("value", {}).get("computed")
    except Exception:
        return None


def get_priority_secret(key_name: str, fallback_keys: tuple[str, ...] = (), default: str = "") -> str:
    """
    Fetch secret enforcing 2-Tier Priority Policy:
    1st Priority: DOPPLER SECRETS STORE
    2nd Priority: PLATFORM SECRETS STORE (Kaggle / GitHub / Local .env)
    """
    all_keys = (key_name,) + fallback_keys

    # --- 1st Priority: DOPPLER SECRETS ---
    # Check if Doppler CLI is running or DOPPLER_ENVIRONMENT is set
    is_doppler_env = bool(os.getenv("DOPPLER_ENVIRONMENT") or os.getenv("DOPPLER_CONFIG") or os.getenv("DOPPLER_TOKEN"))
    if is_doppler_env:
        for k in all_keys:
            val = os.getenv(k)
            if val:
                return val
            val_api = fetch_doppler_secret_via_api(k)
            if val_api:
                return val_api

    # --- Warning Notice if 1st Priority Doppler miss ---
    platform_name = "KAGGLE SECRETS STORE" if (os.path.exists("/kaggle") or "KAGGLE" in os.environ) else "PLATFORM SECRETS (.env / System)"
    logger.warning(f"[WARNING] Secret '{key_name}' not found in 1st Priority (DOPPLER). Falling back to 2nd Priority ({platform_name})...")

    # --- 2nd Priority: PLATFORM SECRETS (Kaggle / GitHub / Local) ---
    # 1. Try Kaggle Secrets Client if running on Kaggle
    try:
        from kaggle_secrets import UserSecretsClient
        user_secrets = UserSecretsClient()
        for k in all_keys:
            try:
                val = user_secrets.get_secret(k)
                if val:
                    logger.info(f"[OK] Secret '{k}' loaded from 2nd Priority (KAGGLE SECRETS STORE)")
                    return val
            except Exception:
                pass
    except Exception:
        pass

    # 2. Try System Environment & Local .env
    for k in all_keys:
        val = os.getenv(k)
        if val:
            logger.info(f"[OK] Secret '{k}' loaded from 2nd Priority (System Env / .env)")
            return val

    return default


class Config:
    """Application configuration provider with 2-Tier Priority Secrets Policy."""

    # Supabase Configuration
    SUPABASE_URL: str = get_priority_secret("APP_SUPABASE_URL", ("SUPABASE_URL",))
    SUPABASE_KEY: str = get_priority_secret("APP_SUPABASE_KEY", ("SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"))

    # Hugging Face Hub & GitHub
    HF_TOKEN: str = get_priority_secret("HF_TOKEN")
    GH_TOKEN: str = get_priority_secret("GH_TOKEN")
    HF_USERNAME: str = os.getenv("HF_USERNAME", "pphothidaen")
    HF_REPO_ID: str = os.getenv("HF_REPO_ID", f"{HF_USERNAME}/qwen2.5-7b-bazi-instruct-4bit")

    # Cloud AI & Analytics
    GOOGLE_AI_STUDIO_API_KEY: str = get_priority_secret("GOOGLE_AI_STUDIO_API_KEY")
    GOOGLE_AI_STUDIO_API_KEY2: str = get_priority_secret("GOOGLE_AI_STUDIO_API_KEY2")
    WANDB_KEY: str = get_priority_secret("WANDB_KEY")
    KAGGLE_TOKEN: str = get_priority_secret("KAGGLE_TOKEN")

    # Local Ollama Inference
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_PRIMARY_MODEL: str = os.getenv("OLLAMA_PRIMARY_MODEL", "qwen2.5:7b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

    # Fine-Tuning Settings
    BASE_MODEL_NAME: str = os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
    ADAPTER_PATH: str = os.getenv("ADAPTER_PATH", str(BASE_DIR / "project" / "models" / "qwen2.5-bazi-adapter"))

    @classmethod
    def is_supabase_configured(cls) -> bool:
        """Check if Supabase credentials are validly set."""
        return bool(cls.SUPABASE_URL and cls.SUPABASE_KEY and cls.SUPABASE_URL.startswith("http"))

    @classmethod
    def is_hf_configured(cls) -> bool:
        """Check if Hugging Face token is provided."""
        return bool(cls.HF_TOKEN and cls.HF_TOKEN.startswith("hf_"))

    @classmethod
    def get_summary(cls) -> dict[str, str]:
        """Return masked status summary of active configurations."""
        return {
            "SUPABASE": "✅ Configured" if cls.is_supabase_configured() else "⚠️ Not Configured",
            "HUGGING_FACE": "✅ Configured" if cls.is_hf_configured() else "⚠️ Missing HF_TOKEN",
            "GEMINI_KEY_1": "✅ Active" if bool(cls.GOOGLE_AI_STUDIO_API_KEY) else "❌ Missing",
            "GEMINI_KEY_2": "✅ Active" if bool(cls.GOOGLE_AI_STUDIO_API_KEY2) else "❌ Missing",
            "OLLAMA_URL": cls.OLLAMA_BASE_URL,
            "HF_REPO_ID": cls.HF_REPO_ID,
        }


if __name__ == "__main__":
    print("🔐 2-Tier Priority Config Status Summary:")
    print(json.dumps(Config.get_summary(), indent=2, ensure_ascii=False))
