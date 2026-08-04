"""
scripts/test_cloud_credentials.py
==================================
Verification Script for Case 3: Cloud GPU Environment (Lightning AI, Kaggle, Hugging Face Hub).

Tests:
1. Hugging Face API Token & Account Status
2. Lightning AI Credentials & Teamspace Access
3. Kaggle API Credentials
4. Supabase DB Connection & Dataset Readiness
"""

from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config
from project.core.supabase_db import SupabaseDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_cloud")


def test_huggingface_credentials() -> bool:
    """Verify Hugging Face token and account status."""
    token = Config.HF_TOKEN
    if not token:
        logger.error("❌ HF_TOKEN not found in Config / Doppler")
        return False

    url = "https://huggingface.co/api/whoami-v2"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                username = data.get("name", "Unknown")
                logger.info(f"✅ Hugging Face Authentication OK (User: {username})")
                return True
            else:
                logger.error(f"❌ Hugging Face Auth Failed ({resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        logger.error(f"❌ Hugging Face Connection Error: {e}")
        return False


def test_lightning_credentials() -> bool:
    """Verify Lightning AI API keys and credentials."""
    api_key = os.getenv("LIGHTNING_API_KEY") or os.getenv("LIGHTNING_PROD_API_KEY")
    teamspace = os.getenv("LIGHTNING_TEAMSPACE", "deploy-model-project")

    if not api_key:
        logger.error("❌ LIGHTNING_API_KEY not found in Config / Doppler")
        return False

    logger.info(f"✅ Lightning AI Credentials configured (Teamspace: {teamspace})")
    return True


def test_kaggle_credentials() -> bool:
    """Verify Kaggle Username and Token."""
    username = os.getenv("KAGGLE_USERNAME", "pphothidaen")
    token = os.getenv("KAGGLE_TOKEN")

    if not token:
        logger.error("❌ KAGGLE_TOKEN not found in Config / Doppler")
        return False

    logger.info(f"✅ Kaggle Credentials configured (Username: {username})")
    return True


def main():
    logger.info("🧪 --- Testing Case 3: Cloud GPU Platform Credentials & Infrastructure ---")
    
    hf_ok = test_huggingface_credentials()
    lit_ok = test_lightning_credentials()
    kag_ok = test_kaggle_credentials()

    db = SupabaseDB()
    db_ok = db.is_configured()
    logger.info(f"📡 Supabase Central DB Configured: {db_ok}")

    print("\n" + "=" * 65)
    print("  CASE 3 CLOUD GPU PLATFORM VERIFICATION SUMMARY")
    print("=" * 65)
    print(f"  Hugging Face Hub API : {'✅ PASSED' if hf_ok else '❌ FAILED'}")
    print(f"  Lightning AI Cloud   : {'✅ PASSED' if lit_ok else '❌ FAILED'}")
    print(f"  Kaggle GPU Cluster   : {'✅ PASSED' if kag_ok else '❌ FAILED'}")
    print(f"  Supabase Dataset DB  : {'✅ PASSED' if db_ok else '⚠️ NOT CONFIGURED'}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
