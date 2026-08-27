#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - Local Release Readiness Runner
# ==============================================================================
# Local execution is limited to QA, secret scanning, and an HF Docker payload
# dry-run. Production mutation belongs to a READY, target-bound release ticket
# executed through governed CI.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

usage() {
    echo "Usage: bash scripts/auto_deploy_all.sh --dry-run"
    echo ""
    echo "Local production deployment is disabled."
    echo "Use --dry-run for QA and HF Docker package validation only."
}

if [ "$#" -ne 1 ]; then
    echo "[ERROR] BLOCKED: local production release is disabled."
    echo "[INFO] Use a READY, target-bound release ticket in PROJECT_TASKS.md through governed CI."
    usage
    exit 2
fi

case "$1" in
    --dry-run)
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        echo "[ERROR] BLOCKED: unsupported local release action: $1"
        echo "[INFO] Use a READY, target-bound release ticket in PROJECT_TASKS.md through governed CI."
        usage
        exit 2
        ;;
esac

echo "======================================================================"
echo " HOROCONSULTANT LOCAL RELEASE READINESS DRY-RUN"
echo "======================================================================"
echo " [START] Time: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo " [PATH]  Directory: $ROOT_DIR"
echo "======================================================================"

# ------------------------------------------------------------------------------
# STEP 1: Local QA
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 1/3] Running local QA checks."

echo "[INFO] Running pytest unit and integration regression suite."
python3 -m pytest -v --ignore=project/kaggle_kernel

echo "[INFO] Running UI and endpoint contract regression."
python3 scripts/run_button_regression.py

echo "[OK] Step 1 local QA completed."

# ------------------------------------------------------------------------------
# STEP 2: Read-only secret scan
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 2/3] Running secret leakage scan."
python3 project/core/code_reviewer.py --scan-secrets
echo "[OK] Step 2 secret scan completed."

# ------------------------------------------------------------------------------
# STEP 3: Canonical HF Docker payload dry-run
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [STEP 3/3] Validating the canonical HF Docker backend payload without upload."
python3 scripts/publish_space_hf.py \
    --space-id pphothidaen/horoconsultant-core-backend \
    --sdk docker \
    --dry-run
echo "[OK] Step 3 HF Docker payload dry-run completed."

echo "======================================================================"
echo " [OK] LOCAL PLAN, QA, AND DRY-RUN CHECKS COMPLETED"
echo "======================================================================"
echo " [WARNING] No deploy, publish, push, or secret synchronization was performed."
echo " [INFO] Production release requires a READY, target-bound ticket in PROJECT_TASKS.md through governed CI."
echo "======================================================================"
