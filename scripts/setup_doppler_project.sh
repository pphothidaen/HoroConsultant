#!/usr/bin/env bash
# ============================================================
# scripts/setup_doppler_project.sh
# ============================================================
# Automated Setup & Secret Push Script for Doppler Project
# ============================================================
# Dashboard: https://dashboard.doppler.com/workplace/4e65e3d95e9f71174b4e/projects/horo-consultant/configs/prd

set -e

PROJECT_NAME="horo-consultant"
ENV_FILE=".env.production"

echo "🔐 --- Doppler Setup & Initialization for HoroConsultant ---"

# 1. Check Doppler CLI
DOPPLER_BIN=$(which doppler || echo "/opt/homebrew/bin/doppler")
if [ ! -f "$DOPPLER_BIN" ]; then
    echo "❌ Doppler CLI not found. Installing via Homebrew..."
    brew install dopplerhq/cli/doppler
fi

# 2. Check Login Status
if ! $DOPPLER_BIN me >/dev/null 2>&1; then
    echo "⚠️ Doppler CLI is not logged in."
    echo "👉 Please run 'doppler login' or set DOPPLER_TOKEN first."
    echo ""
    echo "Terminal Command to Login:"
    echo "  doppler login"
    exit 1
fi

echo "✅ Authenticated with Doppler!"

# 3. Create Project
echo "📦 Creating Doppler Project '$PROJECT_NAME'..."
$DOPPLER_BIN projects create "$PROJECT_NAME" --description "Computational Metaphysics Engine" || true

# 4. Setup Local Directory Binding
echo "🔗 Setting up local directory binding to project '$PROJECT_NAME' (config: dev)..."
$DOPPLER_BIN setup --project "$PROJECT_NAME" --config dev --no-prompt

# 5. Push Production Secrets
echo "🚀 Uploading all 46 Production secrets to Doppler project '$PROJECT_NAME' (config: prd)..."
python3 scripts/sync_doppler_secrets.py --env-file "$ENV_FILE" --project "$PROJECT_NAME" --config prd

echo ""
echo "🎉 Doppler setup and secret initialization completed successfully!"
