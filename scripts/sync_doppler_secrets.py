"""
scripts/sync_doppler_secrets.py
================================
Automated Production Secret Sync Script for Doppler Secrets Management.

Reads secrets from `.env.production` or `.env` and syncs them into Doppler
Secrets Manager for `horo-consultant` project (config: `prd` or `dev`),
as well as GitHub Repository Secrets for GitHub Actions CI/CD automation.

Usage:
------
    # Dry-run validation
    python3 scripts/sync_doppler_secrets.py --dry-run

    # Production Sync
    python3 scripts/sync_doppler_secrets.py --env-file .env.production --project horo-consultant --config prd
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("doppler_sync")


def get_doppler_cli_path() -> str:
    """Check if Doppler CLI is installed."""
    for path in ["/opt/homebrew/bin/doppler", "/usr/local/bin/doppler"]:
        if os.path.exists(path):
            return path
    try:
        res = subprocess.run(["which", "doppler"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "doppler"


def sync_github_secrets(valid_secrets: dict[str, str], dry_run: bool = False) -> None:
    """Sync key CI/CD deployment secrets (FLY_API_TOKEN, VERCEL_TOKEN) to GitHub Repository Secrets."""
    gh_bin = "gh"
    if not dry_run:
        try:
            subprocess.run(["which", "gh"], capture_output=True, check=True)
        except Exception:
            logger.info("ℹ️ GitHub CLI (`gh`) not installed. Skipping direct GitHub Secrets sync.")
            return

    target_secrets = [
        "AZURE_CREDENTIALS",
        "AZURE_CONTAINER_APP",
        "AZURE_RESOURCE_GROUP",
        "AZURE_CONTAINER_APP_URL",
        "DOCKER_USERNAME",
        "DOCKER_PASSWORD",
        "ROUTER_BASE_URL",
        "NINE_ROUTER_BASE_URL",
        "FLY_API_TOKEN",
        "VERCEL_TOKEN",
        "HF_TOKEN",
        "GOOGLE_AI_STUDIO_API_KEY",
        "GOOGLE_AI_STUDIO_API_KEY2",
    ]
    for key in target_secrets:
        val = valid_secrets.get(key)
        if val:
            if dry_run:
                logger.info(f"🧪 [DRY RUN] Would sync GitHub Secret: {key}")
            else:
                try:
                    res = subprocess.run(
                        [gh_bin, "secret", "set", key, "--body", val],
                        capture_output=True,
                        text=True,
                    )
                    if res.returncode == 0:
                        logger.info(f"✅ Synced GitHub Repository Secret: `{key}`")
                    else:
                        logger.warning(f"⚠️ Failed to set GitHub Secret `{key}`: {res.stderr.strip()}")
                except Exception as e:
                    logger.warning(f"⚠️ GitHub Secret sync note for {key}: {e}")


def sync_secrets_to_doppler(
    env_file: Path,
    project: str = "horo-consultant",
    config: str = "prd",
    dry_run: bool = False,
) -> bool:
    """Parse environment file and set secrets in Doppler via Doppler CLI / API."""
    if not env_file.exists():
        fallback = ROOT_DIR / ".env"
        if fallback.exists():
            logger.info(f"ℹ️ Requested file '{env_file.name}' not found. Falling back to '{fallback.name}'")
            env_file = fallback
        else:
            logger.error(f"❌ Secret environment file not found at: {env_file}")
            return False

    secrets = dotenv_values(env_file)
    ignored_keys = {k for k in secrets.keys() if isinstance(k, str) and k.startswith("DOPPLER_")}
    valid_secrets = {
        k: v
        for k, v in secrets.items()
        if (
            k
            and v
            and not k.startswith("#")
            and "REPLACE" not in str(v)
            and k not in ignored_keys
        )
    }

    logger.info(f"🔑 Categorized {len(valid_secrets)} Production Secrets from `{env_file.name}`:")
    categories = {
        "Cloud AI Fallback (Gemini)": ["GOOGLE_AI_STUDIO_API_KEY", "GOOGLE_AI_STUDIO_API_KEY2", "GOOGLE_APPLICATION_CREDENTIALS", "PRIMARY_MODEL"],
        "Production Database (Supabase)": ["APP_SUPABASE_URL", "APP_SUPABASE_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"],
        "Model Repository (Hugging Face)": ["HF_TOKEN", "HF_USERNAME", "HF_REPO_ID"],
        "Cloud & Edge Deployments (Azure, Fly.io & Vercel)": ["AZURE_RESOURCE_GROUP", "AZURE_CONTAINER_APP", "AZURE_CREDENTIALS", "AZURE_CONTAINER_APP_URL", "FLY_API_TOKEN", "VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"],
        "Cloud GPU Training (Lightning AI & Kaggle)": ["LIGHTNING_API_KEY", "LIGHTNING_PROD_API_KEY", "KAGGLE_USERNAME", "KAGGLE_TOKEN"],
        "MLOps & GitHub": ["WANDB_KEY", "GH_TOKEN", "GH_TOTP_SECRET"],
        "Infrastructure & Security": ["APP_ENV", "SECRET_KEY", "REDIS_URL", "AUTO_SYNC_ENABLED"],
    }

    for cat_name, keys in categories.items():
        matched = [k for k in keys if k in valid_secrets]
        logger.info(f"   📌 {cat_name}: {len(matched)} keys ({', '.join(matched[:3])}...)")

    if dry_run:
        logger.info("🧪 DRY RUN MODE: All Production secrets categorized and validated successfully!")
        logger.info(f"🧪 Would sync Doppler first (project: {project}, config: {config})")
        for k in sorted(valid_secrets.keys()):
            logger.info(f"🧪 [DRY RUN] Would sync Doppler Secret: {k}")
        sync_github_secrets(valid_secrets, dry_run=dry_run)
        return True

    doppler_bin = get_doppler_cli_path()
    
    # Execute setup & creation
    cmd = [doppler_bin, "secrets", "set", "--project", project, "--config", config]
    for k, v in valid_secrets.items():
        cmd.append(f"{k}={v}")

    logger.info(f"🚀 Executing Doppler Secret Sync to project [{project}] config [{config}]...")
    doppler_ok = False
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("🎉 Successfully synced all Production secrets to Doppler Secrets Manager!")
            doppler_ok = True
        else:
            if "must provide a token" in res.stderr or "auth login" in res.stderr:
                logger.warning("⚠️ Doppler CLI needs authentication (`doppler login` or `DOPPLER_TOKEN`).")
                logger.info("📋 Generated One-Line Doppler Push Command for Terminal:")
                cmd_str = f"{doppler_bin} secrets set --project {project} --config {config} " + " ".join([f'{k}="{v}"' for k, v in valid_secrets.items()])
                print("\n" + "=" * 80)
                print("RUN THIS COMMAND IN YOUR TERMINAL AFTER `doppler login`:")
                print("=" * 80)
                print(cmd_str)
                print("=" * 80 + "\n")
                doppler_ok = True
            else:
                logger.error(f"❌ Doppler CLI Error: {res.stderr}")
                return False
    except Exception as e:
        logger.error(f"❌ Execution error: {e}")
        return False

    sync_github_secrets(valid_secrets, dry_run=dry_run)
    return doppler_ok


def main():
    parser = argparse.ArgumentParser(description="Sync HoroConsultant Production Secrets to Doppler & GitHub Secrets")
    parser.add_argument("--env-file", type=Path, default=ROOT_DIR / ".env.production", help="Path to production .env file")
    parser.add_argument("--project", default="horo-consultant", help="Doppler project name")
    parser.add_argument("--config", default="prd", help="Doppler config name ('dev' or 'prd')")
    parser.add_argument("--dry-run", action="store_true", help="Validate without sending to Doppler")

    args = parser.parse_args()

    success = sync_secrets_to_doppler(
        env_file=args.env_file,
        project=args.project,
        config=args.config,
        dry_run=args.dry_run,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
