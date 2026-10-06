#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - Cloudflare Workers Local Deploy Helper
# ==============================================================================
# Local mirror of the account-scoped GitHub Actions workflows
# (.github/workflows/workers-hermes.yml, workers-gemini.yml, workers-aipass.yml).
#   preview mode    -> wrangler dry-run bundle (no network, no token needed)
#   production mode -> real deploy; requires CLOUDFLARE_API_TOKEN in the env
# Tokens are never hardcoded here. GitHub Actions uses the per-account secrets
# documented in docs/GITHUB_SECRETS_WORKERS.md (CF_API_TOKEN_HERMES/_GEMINI/_AIPASS).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

usage() {
    echo "Usage: ./scripts/deploy-worker.sh {hermes|gemini|aipass} [preview|production]"
    echo ""
    echo "Account -> config mapping (repo root):"
    echo "  hermes  -> wrangler.hermes.toml  (CF_API_TOKEN_HERMES)"
    echo "  gemini  -> wrangler.gemini.toml  (CF_API_TOKEN_GEMINI)"
    echo "  aipass  -> wrangler.aipass.toml  (CF_API_TOKEN_AIPASS)"
    echo ""
    echo "Environments (default: production):"
    echo "  preview     npx wrangler deploy --dry-run --outdir=dist-<account> (offline, no token)"
    echo "  production  npx wrangler deploy (requires CLOUDFLARE_API_TOKEN)"
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "[ERROR] Invalid argument count: $# (expected 1 or 2)."
    usage
    exit 2
fi

ACCOUNT="$1"
ENVIRONMENT="${2:-production}"

case "$ACCOUNT" in
    hermes|gemini|aipass)
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        echo "[ERROR] Unknown account: $ACCOUNT (expected hermes, gemini, or aipass)."
        usage
        exit 2
        ;;
esac

case "$ENVIRONMENT" in
    preview|production)
        ;;
    *)
        echo "[ERROR] Unknown environment: $ENVIRONMENT (expected preview or production)."
        usage
        exit 2
        ;;
esac

CONFIG="wrangler.${ACCOUNT}.toml"
OUTDIR="dist-${ACCOUNT}"

if [ ! -f "$CONFIG" ]; then
    echo "[ERROR] Config not found: $CONFIG (expected in repo root: $ROOT_DIR)."
    exit 2
fi

echo "======================================================================"
echo " HOROCONSULTANT WORKERS DEPLOY"
echo "======================================================================"
echo " [INFO] Account:     $ACCOUNT"
echo " [INFO] Config:      $CONFIG"
echo " [INFO] Environment: $ENVIRONMENT"
echo "======================================================================"

if [ "$ENVIRONMENT" = "preview" ]; then
    echo "[INFO] Running offline dry-run bundle (no deploy, no token required)."
    npx wrangler deploy --config "$CONFIG" --dry-run --outdir="$OUTDIR"
    echo "[OK] Dry-run bundle written to $OUTDIR/ (nothing was deployed)."
    exit 0
fi

# ------------------------------------------------------------------------------
# Production deploy: token gate, identity check, then real deploy
# ------------------------------------------------------------------------------
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
    echo "[ERROR] CLOUDFLARE_API_TOKEN is not set; refusing production deploy."
    echo "[INFO] Export the target account token first, e.g.:"
    echo "       export CLOUDFLARE_API_TOKEN=<token for the $ACCOUNT account>"
    echo "[INFO] GitHub Actions uses the per-account secrets documented in"
    echo "       docs/GITHUB_SECRETS_WORKERS.md (CF_API_TOKEN_HERMES/_GEMINI/_AIPASS)."
    exit 1
fi

echo "[INFO] Verifying token identity with 'npx wrangler whoami'."
npx wrangler whoami --config "$CONFIG"

echo "[INFO] Deploying $CONFIG to Cloudflare Workers (production)."
npx wrangler deploy --config "$CONFIG"
echo "[OK] Production deploy completed for account $ACCOUNT."
