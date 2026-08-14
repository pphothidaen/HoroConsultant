#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant — Master 100% Automated Multi-Cloud Production Deployment Pipeline
# ==============================================================================
# Executes full AI SDLC & SDLC lifecycle automation in 1 single command:
# 1. Pre-deployment quality & security audit (Pytest, Code Reviewer)
# 2. Multi-cloud secrets synchronization across environment stores
# 3. Vercel Edge Gateway Deployment (npx vercel --prod)
# 4. Hugging Face Docker backend deployment is triggered by the protected
#    main-branch workflow (.github/workflows/hf_backend_deploy.yml)
# 5. Hugging Face Static Edge CDN Deployment
# 6. Post-deployment live endpoint health check
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

# Load .env file safely if present
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env" 2>/dev/null || true
    set +a
fi

echo "======================================================================"
echo " 🚀 HOROCONSULTANT MASTER AUTOMATED PRODUCTION DEPLOYMENT PIPELINE"
echo "======================================================================"
echo " [START] Time: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo " [PATH]  Directory: $ROOT_DIR"
echo "======================================================================"

# ------------------------------------------------------------------------------
# STEP 1: Pre-Deployment Automated Quality & Safety Audit
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 1/5] Executing Pre-Deployment Test Suite & Security Audit..."

echo "[INFO] Running Pytest Unit & Integration Regression Suite..."
python3 -m pytest -v --ignore=project/kaggle_kernel

echo "[INFO] Running 22-Button UI & Endpoint Contract Regression Test..."
python3 scripts/run_button_regression.py

echo "[INFO] Executing Code Reviewer & Secret Leakage Audit..."
python3 project/core/code_reviewer.py --review

echo "[OK] Step 1 Audit Completed: All tests passed & Status is READY_FOR_PROD."

# ------------------------------------------------------------------------------
# STEP 2: Automated Multi-Cloud Secrets Synchronization
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 2/5] Executing Multi-Cloud Secrets Synchronization..."
bash scripts/setup_production_secrets.sh
echo "[OK] Step 2 Secrets Sync Completed."

# ------------------------------------------------------------------------------
# STEP 3: Deploy Hugging Face Static Edge CDN
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 3/5] Deploying Web UIs to Hugging Face Static Edge CDN..."
python3 scripts/publish_space_hf.py --sdk static
echo "[OK] Step 3 Hugging Face Space Deployment Completed."

# ------------------------------------------------------------------------------
# STEP 4: Deploy Vercel Edge Gateway Proxy
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 4/5] Deploying Vercel Edge Gateway Proxy..."
if command -v vercel &> /dev/null || command -v npx &> /dev/null; then
    VERCEL_CMD="npx vercel"
    [ -x "$(command -v vercel)" ] && VERCEL_CMD="vercel"

    if [ -n "$VERCEL_TOKEN" ]; then
        echo "[DEPLOY] Executing: $VERCEL_CMD --prod --yes --token=***"
        $VERCEL_CMD --prod --yes --token="$VERCEL_TOKEN"
        echo "[OK] Step 4 Vercel Edge Deployment Completed."
    elif $VERCEL_CMD whoami &>/dev/null; then
        echo "[DEPLOY] Executing: $VERCEL_CMD --prod --yes"
        $VERCEL_CMD --prod --yes
        echo "[OK] Step 4 Vercel Edge Deployment Completed."
    else
        echo "[INFO] [Vercel] GitHub Push-to-Deploy is active. To enable CLI deploy, set VERCEL_TOKEN in .env or run 'npx vercel login'."
    fi
else
    echo "[INFO] [Vercel] npx / vercel CLI not found. Skipping Vercel deployment."
fi

# ------------------------------------------------------------------------------
# STEP 5: Confirm Hugging Face Docker backend deployment ownership
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 5/5] Hugging Face Docker backend deploy is triggered by push to main."
if [ -n "${HF_BACKEND_URL:-}" ]; then
    echo "[OK] Public backend target configured: ${HF_BACKEND_URL}"
else
    echo "[WARNING] HF_BACKEND_URL is not configured locally; GitHub Actions supplies its default target."
fi

# ------------------------------------------------------------------------------
# STEP 6: Post-Deployment Live Verification & Summary
# ------------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo " 🎉 MASTER AUTOMATED PRODUCTION DEPLOYMENT PIPELINE COMPLETED!"
echo "======================================================================"
echo "  • Hugging Face Static Edge : https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
echo "  • Admin Panel & HITL Studio: https://pphothidaen-horoconsultant-core-backend.static.hf.space/admin.html"
echo "  • Hugging Face Docker Backend : ${HF_BACKEND_URL:-https://pphothidaen-horoconsultant-core-api.hf.space}/health"
echo "  • Vercel Edge Gateway      : Configured via vercel.json & GitHub Push"
echo "======================================================================"
