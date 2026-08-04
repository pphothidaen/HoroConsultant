"""
project/core/config.py
======================
Centralized Secrets & Configuration Manager for HoroConsultant.

Supports loading secrets from:
1. Doppler CLI environment (when executed with `doppler run -- ...`)
2. System environment variables (Kaggle / Lightning AI Secrets)
3. Local `.env` file (fallback for local development)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load local .env if present (Doppler environment variables take precedence)
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)


class Config:
    """Application configuration provider with safe fallbacks."""

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("APP_SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("APP_SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Hugging Face Hub
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_USERNAME: str = os.getenv("HF_USERNAME", "pphothidaen")
    HF_REPO_ID: str = os.getenv("HF_REPO_ID", f"{HF_USERNAME}/qwen2.5-7b-bazi-instruct-4bit")

    # Cloud AI Fallbacks
    GOOGLE_AI_STUDIO_API_KEY: str = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
    GOOGLE_AI_STUDIO_API_KEY2: str = os.getenv("GOOGLE_AI_STUDIO_API_KEY2", "")

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
    import json
    print("🔐 Config Status Summary:")
    print(json.dumps(Config.get_summary(), indent=2, ensure_ascii=False))
