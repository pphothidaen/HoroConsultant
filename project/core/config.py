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

import hashlib
import json
import logging
import os
import subprocess
import urllib.request
from functools import lru_cache
from pathlib import Path
import re

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

_RELEASE_SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
_RELEASE_SOURCE_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_RELEASE_SOURCE_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_RELEASE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.([0-9a-f]{7,40})$")

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


def get_release_source_identity() -> dict[str, str]:
    """Return the immutable source identity declared by static release metadata.

    A release can be packaged or evidenced in a later commit. Consequently,
    the current repository ``HEAD`` is not release provenance and must never be
    used as a fallback here. The source identity is deliberately explicit: the
    abbreviated commit, resolved full revision, and digest of the canonical
    source-metadata payload must all agree. Legacy ``commit`` and deployment
    ``packaging_commit`` fields are rejected rather than silently interpreted.

    Raises:
        ValueError: If local metadata is missing, malformed, ambiguous, or does
            not bind its version suffix to exactly one valid source commit.
    """
    metadata_path = BASE_DIR / "project" / "static" / "version.json"

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        metadata: dict[str, object] = {}
        for key, value in pairs:
            if key in metadata:
                raise ValueError(f"duplicate local release metadata key: {key}")
            metadata[key] = value
        return metadata

    try:
        raw_metadata = json.loads(
            metadata_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"local release metadata unavailable: {exc}") from exc

    if not isinstance(raw_metadata, dict):
        raise ValueError("local release metadata must contain a JSON object")

    required_fields = (
        "version",
        "release_source_commit",
        "release_source_revision",
        "release_source_metadata_path",
        "release_source_metadata_sha256",
    )
    missing_fields = [key for key in required_fields if key not in raw_metadata]
    if missing_fields:
        raise ValueError(f"local release metadata missing required fields: {missing_fields}")
    forbidden_fields = [key for key in ("commit", "packaging_commit") if key in raw_metadata]
    if forbidden_fields:
        raise ValueError(f"local release metadata contains forbidden fields: {forbidden_fields}")

    version = raw_metadata["version"]
    if not isinstance(version, str):
        raise ValueError("local release metadata requires one string version")
    version_match = _RELEASE_VERSION_RE.fullmatch(version)
    if version_match is None:
        raise ValueError("local release version must end with one lowercase source commit")

    source_commit = raw_metadata["release_source_commit"]
    source_revision = raw_metadata["release_source_revision"]
    source_metadata_path = raw_metadata["release_source_metadata_path"]
    source_metadata_digest = raw_metadata["release_source_metadata_sha256"]
    if not isinstance(source_commit, str) or _RELEASE_SOURCE_COMMIT_RE.fullmatch(source_commit) is None:
        raise ValueError("local release source commit must be lowercase hexadecimal")
    if not isinstance(source_revision, str) or _RELEASE_SOURCE_REVISION_RE.fullmatch(source_revision) is None:
        raise ValueError("local release source revision must be a full lowercase Git revision")
    if not isinstance(source_metadata_path, str) or source_metadata_path != "project/static/version.json":
        raise ValueError("local release source metadata path must be project/static/version.json")
    if not isinstance(source_metadata_digest, str) or _RELEASE_SOURCE_DIGEST_RE.fullmatch(source_metadata_digest) is None:
        raise ValueError("local release source metadata digest must be lowercase SHA-256")
    if version_match.group(1) != source_commit:
        raise ValueError("local release version suffix must equal release source commit")

    canonical_source_metadata = json.dumps(
        {
            "release_source_commit": source_commit,
            "release_source_metadata_path": source_metadata_path,
            "release_source_revision": source_revision,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_digest = hashlib.sha256(canonical_source_metadata).hexdigest()
    if source_metadata_digest != expected_digest:
        raise ValueError("local release source metadata digest does not match canonical source metadata")

    try:
        resolved_revision = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{source_commit}^{{commit}}"],
            cwd=str(BASE_DIR),
            stderr=subprocess.DEVNULL,
            timeout=2,
            text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("local release source commit cannot be resolved in Git") from exc
    if resolved_revision != source_revision:
        raise ValueError("local release source revision conflicts with release source commit")

    return {
        "version": version,
        "release_source_commit": source_commit,
        "release_source_revision": source_revision,
        "release_source_metadata_path": source_metadata_path,
        "release_source_metadata_sha256": source_metadata_digest,
        "metadata_path": str(metadata_path),
    }


_DOPPLER_CACHE: dict[str, str] = {}
_DOPPLER_FETCHED: bool = False


def fetch_all_doppler_secrets_via_api() -> dict[str, str]:
    """Fetch all secrets from Doppler REST API in a single HTTP request if DOPPLER_TOKEN is available."""
    global _DOPPLER_CACHE, _DOPPLER_FETCHED
    if _DOPPLER_FETCHED:
        return _DOPPLER_CACHE

    _DOPPLER_FETCHED = True
    doppler_token = os.getenv("DOPPLER_TOKEN") or os.getenv("DOPPLER_KEY") or os.getenv("DOPPLER_SERVICE_TOKEN")
    
    # Check Kaggle UserSecretsClient if running on Kaggle
    if not doppler_token:
        try:
            from kaggle_secrets import UserSecretsClient
            user_secrets = UserSecretsClient()
            for dk in ("DOPPLER_TOKEN", "doppler_token", "DOPPLER_KEY", "DOPPLER_SERVICE_TOKEN"):
                try:
                    dval = user_secrets.get_secret(dk)
                    if dval:
                        doppler_token = str(dval).strip()
                        os.environ["DOPPLER_TOKEN"] = doppler_token
                        logger.info(f"[DOPPLER] Found DOPPLER_TOKEN in Kaggle Secrets Store ({dk}).")
                        break
                except Exception:
                    pass
        except Exception:
            pass

    # Check Google Colab userdata if running on Colab
    if not doppler_token:
        try:
            from google.colab import userdata
            dval = userdata.get("DOPPLER_TOKEN")
            if dval:
                doppler_token = str(dval).strip()
                os.environ["DOPPLER_TOKEN"] = doppler_token
        except Exception:
            pass

    if not doppler_token:
        return _DOPPLER_CACHE

    try:
        url = "https://api.doppler.com/v3/configs/config/secrets"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {doppler_token}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            secrets_map = data.get("secrets", {})
            for k, sec_obj in secrets_map.items():
                if isinstance(sec_obj, dict):
                    val = sec_obj.get("computed") or sec_obj.get("raw") or ""
                    if val:
                        val = str(val).strip()
                        _DOPPLER_CACHE[k] = val
                        os.environ[k] = val
            logger.info(f"[DOPPLER] [OK] Successfully hydrated {len(_DOPPLER_CACHE)} centralized secrets from Doppler API (1st Priority).")
    except Exception as dop_err:
        logger.warning(f"[DOPPLER] Note fetching centralized secrets via API: {dop_err}")

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
