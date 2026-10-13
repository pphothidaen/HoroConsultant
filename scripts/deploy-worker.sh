#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - Cloudflare Workers Local Deploy Helper
# ==============================================================================
# Local mirror of the account-scoped GitHub Actions workflows
# (.github/workflows/workers-builds.yml, workers-hermes.yml, workers-gemini.yml, workers-aipass.yml).
#   preview mode    -> wrangler dry-run bundle (no network, no token needed)
#   production mode -> real deploy; requires CLOUDFLARE_API_TOKEN or account secret in env
#   check mode      -> validate all configs and scripts without deploying (--check)
# Tokens are never hardcoded here. GitHub Actions uses the per-account secrets
# documented in docs/GITHUB_SECRETS_WORKERS.md (CF_API_TOKEN, CF_API_TOKEN_HERMES/_GEMINI/_AIPASS).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

usage() {
    echo "Usage: ./scripts/deploy-worker.sh {horo|root|hermes|gemini|aipass} [preview|production]"
    echo "       ./scripts/deploy-worker.sh --check"
    echo ""
    echo "Account -> config mapping (repo root):"
    echo "  horo|root -> wrangler.toml         (CF_API_TOKEN)"
    echo "  hermes    -> wrangler.hermes.toml  (CF_API_TOKEN_HERMES)"
    echo "  gemini    -> wrangler.gemini.toml  (CF_API_TOKEN_GEMINI)"
    echo "  aipass    -> wrangler.aipass.toml  (CF_API_TOKEN_AIPASS)"
    echo ""
    echo "Flags:"
    echo "  --check     Validate all configs and scripts without deploying"
    echo "  --help, -h  Show this help message"
    echo ""
    echo "Environments (default: production):"
    echo "  preview     npx wrangler deploy --dry-run --outdir=dist-<account> (offline, no token)"
    echo "  production  npx wrangler deploy (requires CLOUDFLARE_API_TOKEN or account secret)"
}

check_script_syntax() {
    local script_file="$SCRIPT_DIR/deploy-worker.sh"
    echo "[INFO] Validating script syntax: $script_file"
    if bash -n "$script_file"; then
        echo "[OK] Shell script syntax valid: $script_file"
        return 0
    else
        echo "[ERROR] Shell script syntax error: $script_file"
        return 1
    fi
}

validate_account_config() {
    local target_account="$1"
    local config_file="$2"
    local expected_token_var="$3"
    local errors=0

    echo "[INFO] Validating account: $target_account (config: $config_file, token: $expected_token_var)"

    # 1. Config file existence
    if [ ! -f "$config_file" ]; then
        echo "[ERROR] Missing config file: $config_file"
        return 1
    fi
    echo "[OK] Config file exists: $config_file"

    # 2. TOML syntax verification
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import sys
try:
    import tomllib as toml
except ImportError:
    try:
        import tomli as toml
    except ImportError:
        sys.exit(0)
toml.loads(open('$config_file').read())" 2>/dev/null; then
            echo "[OK] TOML syntax valid: $config_file"
        else
            echo "[ERROR] Invalid TOML syntax in $config_file"
            errors=$((errors + 1))
        fi
    fi

    # 3. Required fields validation
    if ! grep -Eq '^[[:space:]]*name[[:space:]]*=' "$config_file"; then
        echo "[ERROR] Missing 'name' in $config_file"
        errors=$((errors + 1))
    fi

    if ! grep -Eq '^[[:space:]]*account_id[[:space:]]*=' "$config_file"; then
        echo "[ERROR] Missing 'account_id' in $config_file"
        errors=$((errors + 1))
    else
        local acct_id
        acct_id=$(grep -E '^[[:space:]]*account_id[[:space:]]*=' "$config_file" | head -n 1 | sed -E 's/.*=[[:space:]]*"([a-f0-9]+)".*/\1/')
        if [ ${#acct_id} -ne 32 ]; then
            echo "[ERROR] Invalid account_id length in $config_file (expected 32 hex chars, got ${#acct_id})"
            errors=$((errors + 1))
        fi
    fi

    if ! grep -Eq '^[[:space:]]*main[[:space:]]*=' "$config_file"; then
        echo "[ERROR] Missing 'main' entrypoint in $config_file"
        errors=$((errors + 1))
    else
        local entrypoint
        entrypoint=$(grep -E '^[[:space:]]*main[[:space:]]*=' "$config_file" | head -n 1 | sed -E 's/.*main[[:space:]]*=[[:space:]]*["'"'"']([^"'"'"']+)["'"'"'].*/\1/')
        if [ -f "$entrypoint" ]; then
            echo "[OK] Entrypoint file found: $entrypoint"
        else
            echo "[WARNING] Entrypoint file '$entrypoint' not found locally (required before deploying)."
        fi
    fi

    if [ "$errors" -ne 0 ]; then
        echo "[ERROR] Account $target_account validation failed with $errors error(s)."
        return 1
    fi

    echo "[OK] Account $target_account configuration verified."
    return 0
}

run_check_all() {
    echo "======================================================================"
    echo " HOROCONSULTANT WORKERS PREFLIGHT CHECK"
    echo "======================================================================"
    local check_errors=0

    # 1. Self syntax check
    if ! check_script_syntax; then
        check_errors=$((check_errors + 1))
    fi

    # 2. Check all account configs
    validate_account_config "horo" "wrangler.toml" "CF_API_TOKEN" || check_errors=$((check_errors + 1))
    validate_account_config "hermes" "wrangler.hermes.toml" "CF_API_TOKEN_HERMES" || check_errors=$((check_errors + 1))
    validate_account_config "gemini" "wrangler.gemini.toml" "CF_API_TOKEN_GEMINI" || check_errors=$((check_errors + 1))
    validate_account_config "aipass" "wrangler.aipass.toml" "CF_API_TOKEN_AIPASS" || check_errors=$((check_errors + 1))

    echo "======================================================================"
    if [ "$check_errors" -eq 0 ]; then
        echo "[OK] All configs and scripts passed preflight checks."
        return 0
    else
        echo "[ERROR] Preflight check failed with $check_errors error(s)."
        return 1
    fi
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "[ERROR] Invalid argument count: $# (expected 1 or 2)."
    usage
    exit 2
fi

ACCOUNT="$1"
ENVIRONMENT="${2:-production}"

case "$ACCOUNT" in
    --help|-h)
        usage
        exit 0
        ;;
    --check)
        run_check_all
        exit $?
        ;;
    horo|root)
        CONFIG="wrangler.toml"
        TOKEN_VAR="CF_API_TOKEN"
        OUTDIR="dist-${ACCOUNT}"
        ;;
    hermes)
        CONFIG="wrangler.hermes.toml"
        TOKEN_VAR="CF_API_TOKEN_HERMES"
        OUTDIR="dist-hermes"
        ;;
    gemini)
        CONFIG="wrangler.gemini.toml"
        TOKEN_VAR="CF_API_TOKEN_GEMINI"
        OUTDIR="dist-gemini"
        ;;
    aipass)
        CONFIG="wrangler.aipass.toml"
        TOKEN_VAR="CF_API_TOKEN_AIPASS"
        OUTDIR="dist-aipass"
        ;;
    *)
        echo "[ERROR] Unknown account: $ACCOUNT (expected horo, root, hermes, gemini, or aipass)."
        usage
        exit 2
        ;;
esac

case "$ENVIRONMENT" in
    preview|production)
        ;;
    --check|check)
        echo "======================================================================"
        echo " HOROCONSULTANT WORKERS PREFLIGHT CHECK ($ACCOUNT)"
        echo "======================================================================"
        if ! check_script_syntax; then
            exit 1
        fi
        if ! validate_account_config "$ACCOUNT" "$CONFIG" "$TOKEN_VAR"; then
            exit 1
        fi
        echo "[OK] Preflight check passed for account $ACCOUNT."
        exit 0
        ;;
    *)
        echo "[ERROR] Unknown environment: $ENVIRONMENT (expected preview or production)."
        usage
        exit 2
        ;;
esac

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
echo " [INFO] Secret Var:  $TOKEN_VAR"
echo "======================================================================"

# ------------------------------------------------------------------------------
# Token mapping: resolve CLOUDFLARE_API_TOKEN from account-scoped variable if unset
# ------------------------------------------------------------------------------
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
    ACCOUNT_TOKEN_VAL=""
    case "$TOKEN_VAR" in
        CF_API_TOKEN)        ACCOUNT_TOKEN_VAL="${CF_API_TOKEN:-}" ;;
        CF_API_TOKEN_HERMES) ACCOUNT_TOKEN_VAL="${CF_API_TOKEN_HERMES:-}" ;;
        CF_API_TOKEN_GEMINI) ACCOUNT_TOKEN_VAL="${CF_API_TOKEN_GEMINI:-}" ;;
        CF_API_TOKEN_AIPASS) ACCOUNT_TOKEN_VAL="${CF_API_TOKEN_AIPASS:-}" ;;
    esac
    if [ -n "$ACCOUNT_TOKEN_VAL" ]; then
        echo "[INFO] Mapped $TOKEN_VAR to CLOUDFLARE_API_TOKEN for account $ACCOUNT."
        export CLOUDFLARE_API_TOKEN="$ACCOUNT_TOKEN_VAL"
    fi
fi

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
    echo "[ERROR] CLOUDFLARE_API_TOKEN (or $TOKEN_VAR) is not set; refusing production deploy."
    echo "[INFO] Export the target account token first, e.g.:"
    echo "       export $TOKEN_VAR=<token for the $ACCOUNT account>"
    echo "       or export CLOUDFLARE_API_TOKEN=<token>"
    echo "[INFO] GitHub Actions uses the per-account secrets documented in"
    echo "       docs/GITHUB_SECRETS_WORKERS.md ($TOKEN_VAR)."
    exit 1
fi

echo "[INFO] Verifying token identity with 'npx wrangler whoami'."
npx wrangler whoami --config "$CONFIG"

echo "[INFO] Deploying $CONFIG to Cloudflare Workers (production)."
npx wrangler deploy --config "$CONFIG"
echo "[OK] Production deploy completed for account $ACCOUNT."
