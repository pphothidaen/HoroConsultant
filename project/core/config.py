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

import json
import logging
import os
import subprocess
import urllib.request
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("config_manager")

# Load local .env if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)


@lru_cache(maxsize=1)
def get_git_commit_hash() -> str:
    """
    Retrieve short 7-character Git commit hash dynamically.
    Checks environment variables (GIT_COMMIT_HASH, VERCEL_GIT_COMMIT_SHA, HF_COMMIT_SHA, COMMIT_REF),
    `git_commit.txt` file, or executes `git rev-parse --short HEAD`.
    """
    env_hash = (
        os.getenv("GIT_COMMIT_HASH")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("HF_COMMIT_SHA")
        or os.getenv("COMMIT_REF")
    )
    if env_hash:
        return env_hash[:7]

    commit_file = BASE_DIR / "git_commit.txt"
    if commit_file.exists():
        try:
            val = commit_file.read_text().strip()
            if val:
                return val[:7]
        except Exception:
            pass

    try:
        cmd_out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(BASE_DIR),
            stderr=subprocess.DEVNULL,
            timeout=2,
            text=True,
        ).strip()
        if cmd_out:
            return cmd_out
    except Exception:
        pass

    return "unknown"


def get_app_version() -> str:
    """Return full application version string with dynamic Git commit hash, e.g. 1.0.0.fe6a2aa."""
    return f"1.0.0.{get_git_commit_hash()}"


_DOPPLER_CACHE: dict[str, str] = {}
_DOPPLER_FETCHED: bool = False


def fetch_all_doppler_secrets_via_api() -> dict[str, str]:
    """Fetch all secrets from Doppler REST API in a single HTTP request if DOPPLER_TOKEN is available."""
    global _DOPPLER_CACHE, _DOPPLER_FETCHED
    if _DOPPLER_FETCHED:
        return _DOPPLER_CACHE

    _DOPPLER_FETCHED = True
    doppler_token = os.getenv("DOPPLER_TOKEN")
    if not doppler_token:
        return _DOPPLER_CACHE

    try:
        url = "https://api.doppler.com/v3/configs/config/secrets"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {doppler_token}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            secrets_map = data.get("secrets", {})
            for k, sec_obj in secrets_map.items():
                if isinstance(sec_obj, dict):
                    val = sec_obj.get("computed") or sec_obj.get("raw") or ""
                    if val:
                        val = str(val).strip()
                        _DOPPLER_CACHE[k] = val
                        os.environ[k] = val
    except Exception:
        pass

    return _DOPPLER_CACHE


def fetch_doppler_secret_via_api(key_name: str) -> str | None:
    """Attempt fetching secret directly from Doppler API if DOPPLER_TOKEN is available."""
    cached = fetch_all_doppler_secrets_via_api()
    if key_name in cached:
        return cached[key_name]

    doppler_token = os.getenv("DOPPLER_TOKEN")
    if not doppler_token:
        return None

    try:
        url = f"https://api.doppler.com/v3/configs/config/secret?name={key_name}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {doppler_token.strip()}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            val = data.get("value", {}).get("computed")
            if val:
                val = str(val).strip()
                os.environ[key_name] = val
            return val
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
    is_doppler_env = bool(os.getenv("DOPPLER_ENVIRONMENT") or os.getenv("DOPPLER_CONFIG") or os.getenv("DOPPLER_TOKEN"))
    if is_doppler_env:
        for k in all_keys:
            val_api = fetch_doppler_secret_via_api(k)
            if val_api:
                return str(val_api).strip()
            val = os.getenv(k)
            if val:
                return str(val).strip()

    # --- Warning Notice if 1st Priority Doppler miss ---
    platform_name = "KAGGLE SECRETS STORE" if (os.path.exists("/kaggle") or "KAGGLE" in os.environ) else "PLATFORM SECRETS (.env / System)"
    logger.warning(f"Secret '{key_name}' not found in 1st Priority (DOPPLER). Falling back to 2nd Priority ({platform_name})...")

    # --- 2nd Priority: PLATFORM SECRETS (Kaggle / GitHub / Local) ---
    # 1. Try Kaggle Secrets Client if running on Kaggle
    try:
        from kaggle_secrets import UserSecretsClient
        user_secrets = UserSecretsClient()
        for k in all_keys:
            try:
                val = user_secrets.get_secret(k)
                if val:
                    val = str(val).strip()
                    logger.info(f"[OK] Secret '{k}' loaded from 2nd Priority (KAGGLE SECRETS STORE)")
                    os.environ[k] = val
                    os.environ[key_name] = val
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
            os.environ[k] = val
            os.environ[key_name] = val
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
    OLLAMA_PRIMARY_MODEL: str = os.getenv("OLLAMA_PRIMARY_MODEL", "qwen2.5-bazi")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

    # AI Provider Routing Configuration
    AI_PRIMARY_PROVIDER: str = os.getenv("AI_PRIMARY_PROVIDER", "codex_chatgpt").lower()
    AI_FALLBACK_PROVIDER: str = os.getenv("AI_FALLBACK_PROVIDER", "gemini").lower()
    CODEX_COMMAND: str = os.getenv("CODEX_COMMAND", "codex")
    CODEX_USE_CHATGPT_AUTH: bool = os.getenv("CODEX_USE_CHATGPT_AUTH", "true").lower() == "true"

    # Fine-Tuning Settings
    BASE_MODEL_NAME: str = os.getenv("BASE_MODEL_NAME", "pphothidaen/qwen2.5-7b-bazi-instruct-4bit")
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
