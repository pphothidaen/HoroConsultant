"""
scripts/sync_doppler_secrets.py
================================
Automated Production Secret Sync Script for Doppler Secrets Management.

Reads secrets from `.env` in local/dev contexts, and falls back to
`.env.production` for CI/CD/prod-style runs.
Syncs all keys into Doppler Secrets Manager for `horo-consultant` project
(config: `prd` or `dev`), then syncs platform secrets.
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
import shutil
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
    return shutil.which("doppler") or "doppler"


def sync_github_secrets(valid_secrets: dict[str, str], dry_run: bool = False) -> None:
    """Sync the allowlisted CI/CD values to GitHub Repository Secrets."""
    gh_bin = "gh"
    if not dry_run and shutil.which("gh") is None:
        logger.info("[INFO] GitHub CLI is not installed; skipping GitHub secret sync.")
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
        "GEMINI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    for key in target_secrets:
        val = valid_secrets.get(key)
        if val:
            if dry_run:
                logger.info("[DRY RUN] Would sync GitHub secret: %s", key)
            else:
                try:
                    res = subprocess.run(
                        [gh_bin, "secret", "set", key],
                        input=val,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0:
                        logger.info("[OK] Synced GitHub repository secret: %s", key)
                    else:
                        logger.warning(
                            "[WARN] GitHub rejected secret %s; details redacted.", key
                        )
                except OSError:
                    logger.warning(
                        "[WARN] GitHub secret sync failed locally for %s; details redacted.",
                        key,
                    )


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
            logger.info(
                "[INFO] Requested file '%s' not found; using '%s'.",
                env_file.name,
                fallback.name,
            )
            env_file = fallback
        else:
            logger.error("[ERROR] Secret environment file not found: %s", env_file)
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

    logger.info(
        "[INFO] Categorized %d production secrets from %s.",
        len(valid_secrets),
        env_file.name,
    )
    categories = {
        "Cloud AI Fallback (Gemini)": ["GOOGLE_AI_STUDIO_API_KEY", "GOOGLE_AI_STUDIO_API_KEY2", "GOOGLE_APPLICATION_CREDENTIALS", "PRIMARY_MODEL"],
        "Production Database (Supabase)": ["APP_SUPABASE_URL", "APP_SUPABASE_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"],
        "Model Repository (Hugging Face)": ["HF_TOKEN", "HF_USERNAME", "HF_REPO_ID"],
        "Cloud & Edge Deployments (Azure, Fly.io & Vercel)": ["AZURE_RESOURCE_GROUP", "AZURE_CONTAINER_APP", "AZURE_CREDENTIALS", "AZURE_CONTAINER_APP_URL", "FLY_API_TOKEN", "VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"],
        "Cloud GPU Training (Lightning AI & Kaggle)": ["LIGHTNING_API_KEY", "LIGHTNING_PROD_API_KEY", "KAGGLE_USERNAME", "KAGGLE_TOKEN"],
        "MLOps & GitHub": ["WANDB_KEY", "GH_TOKEN", "GH_TOTP_SECRET"],
        "Incident Notifications": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DISCORD_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "HEALTH_ALERT_WEBHOOK_URL"],
        "Infrastructure & Security": ["APP_ENV", "SECRET_KEY", "REDIS_URL", "AUTO_SYNC_ENABLED"],
    }

    for cat_name, keys in categories.items():
        matched = [k for k in keys if k in valid_secrets]
        logger.info(
            "[INFO] %s: %d keys (%s)",
            cat_name,
            len(matched),
            ", ".join(matched[:3]),
        )

    if dry_run:
        logger.info("[OK] Dry run: production secret names validated.")
        for k in sorted(valid_secrets.keys()):
            logger.info("[DRY RUN] Would sync Secret: %s", k)
        sync_github_secrets(valid_secrets, dry_run=dry_run)
        return True

    doppler_bin = get_doppler_cli_path()
    
    # Execute setup & creation
    cmd = [doppler_bin, "secrets", "set", "--project", project, "--config", config]
    for k, v in valid_secrets.items():
        cmd.append(f"{k}={v}")

    logger.info(
        "[INFO] Syncing secret values to Doppler project [%s], config [%s].",
        project,
        config,
    )
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            logger.info("[OK] Synced production secrets to Doppler.")
            sync_github_secrets(valid_secrets, dry_run=dry_run)
            return True
        else:
            if "must provide a token" in res.stderr or "auth login" in res.stderr:
                logger.warning(
                    "[WARN] Doppler authentication is required; no values were printed."
                )
                logger.info(
                    "[INFO] Authenticate with 'doppler login' or DOPPLER_TOKEN, then rerun."
                )
                return False
            else:
                logger.error("[ERROR] Doppler rejected the sync; details redacted.")
                return False
    except OSError:
        logger.error("[ERROR] Doppler sync execution failed; details redacted.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sync HoroConsultant Production Secrets to Doppler & GitHub Secrets")
    default_env_file = ROOT_DIR / (".env" if os.getenv("GITHUB_ACTIONS") != "true" else ".env.production")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=default_env_file,
        help="Path to local/prod env file (defaults to .env locally, .env.production in CI)",
    )
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
