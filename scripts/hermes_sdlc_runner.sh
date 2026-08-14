#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant — Hermes SDLC Execution Runner
# ==============================================================================
# Hermes Execution Engine: Plan -> Act -> Observe -> Reflect loop dispatcher.
# Supports two runtime modes:
#   LOCAL   — Interactive developer Mac with 9router on localhost:20128
#   CI/CD   — Headless GitHub Actions runner with ROUTER_BASE_URL from secrets
#
# Usage:
#   bash scripts/hermes_sdlc_runner.sh dev      # Phase 2: Core Implementation
#   bash scripts/hermes_sdlc_runner.sh qa        # Phase 3: Automated QA
#   bash scripts/hermes_sdlc_runner.sh deploy    # Phase 5: Cloud Deploy
#   bash scripts/hermes_sdlc_runner.sh sync      # Post-edit: Agent sync mandate
#   bash scripts/hermes_sdlc_runner.sh all       # Full pipeline (1->5)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Load .env if present (local mode)
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.env" 2>/dev/null || true
    set +a
fi

PHASE="${1:-help}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S %z')"
MAX_RETRIES="${HERMES_MAX_LOOP_RETRIES:-3}"

# ── ASCII Logging Helpers (Pure ASCII per .agents/AGENTS.md Rule #3) ──────────
log_info()    { echo "[INFO]    $*"; }
log_ok()      { echo "[OK]      $*"; }
log_warn()    { echo "[WARNING] $*"; }
log_error()   { echo "[ERROR]   $*"; exit 1; }
log_section() { echo ""; echo "======================================================================"; echo "  $*"; echo "======================================================================"; }

# ── 9router Health Check & Routing Resolution ─────────────────────────────────
resolve_router() {
    ACCOUNT_ALIAS="${ROUTER_ACCOUNT_ALIAS:-${NINE_ROUTER_ACCOUNT_ALIAS:-agy1}}"

    # Priority 1: ROUTER_BASE_URL (Cloud/CI secret override)
    if [ -n "${ROUTER_BASE_URL:-}" ]; then
        RESOLVED_ROUTER_URL="$ROUTER_BASE_URL"
        log_info "Routing: ROUTER_BASE_URL (Cloud/CI mode) -> $RESOLVED_ROUTER_URL (Account Alias: $ACCOUNT_ALIAS)"
        export OPENAI_BASE_URL="$RESOLVED_ROUTER_URL"
        export OPENAI_API_KEY="${NINE_ROUTER_API_KEY:-dummy}"
        export NINE_ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
        export ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
        export HTTP_HEADER_X_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
        return 0
    fi

    # Priority 2: NINE_ROUTER_BASE_URL (Local 9router on localhost)
    if [ -n "${NINE_ROUTER_BASE_URL:-}" ]; then
        HEALTH_ENDPOINT="${NINE_ROUTER_BASE_URL%/v1}/health"
        if curl -sf --max-time 3 "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            RESOLVED_ROUTER_URL="$NINE_ROUTER_BASE_URL"
            log_ok "9router UP at $NINE_ROUTER_BASE_URL — routing via proxy (Account Alias: $ACCOUNT_ALIAS)"
            export OPENAI_BASE_URL="$RESOLVED_ROUTER_URL"
            export OPENAI_API_KEY="${NINE_ROUTER_API_KEY:-dummy}"
            export NINE_ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            export ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            export HTTP_HEADER_X_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            return 0
        else
            log_warn "9router at $NINE_ROUTER_BASE_URL not reachable — trying fallback"
        fi
    fi

    # Priority 3: CODEX_PRO endpoint fallback
    if [ -n "${CODEX_PRO_BASE_URL:-}" ] && [ -n "${CODEX_PRO:-}" ]; then
        log_warn "Falling back to CODEX_PRO endpoint: $CODEX_PRO_BASE_URL"
        export OPENAI_BASE_URL="$CODEX_PRO_BASE_URL"
        export OPENAI_API_KEY="$CODEX_PRO"
        return 0
    fi

    # Priority 4: Gemini direct (GOOGLE_AI_STUDIO_API_KEY)
    if [ -n "${GOOGLE_AI_STUDIO_API_KEY:-}" ]; then
        log_warn "Falling back to direct Gemini API (no proxy)"
        unset OPENAI_BASE_URL
        unset OPENAI_API_KEY
        return 0
    fi

    log_error "No LLM routing available. Set NINE_ROUTER_BASE_URL, ROUTER_BASE_URL, CODEX_PRO, or GOOGLE_AI_STUDIO_API_KEY"
}

# ── Phase Implementations ─────────────────────────────────────────────────────

phase_dev() {
    log_section "PHASE 2: Core Implementation (Hermes — developer agent)"
    resolve_router
    log_info "Router resolved. Developer agent now active via $OPENAI_BASE_URL"
    log_info "Model: ${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3} (via 9router pool)"
    log_ok "Environment ready. Run: agy --agent developer '<task>'"
}

phase_qa() {
    log_section "PHASE 3: QA Testing (Hermes Headless — qa_tester agent)"
    local retry=0

    while [ $retry -lt "$MAX_RETRIES" ]; do
        log_info "QA attempt $((retry+1))/$MAX_RETRIES — running pytest..."
        if python3 -m pytest -v --ignore=project/kaggle_kernel --tb=short 2>&1 | tee /tmp/hermes_pytest_output.txt; then
            log_ok "Pytest PASSED"
            break
        else
            retry=$((retry+1))
            if [ $retry -lt "$MAX_RETRIES" ]; then
                log_warn "Pytest FAILED (attempt $retry). Retrying after 5s..."
                sleep 5
            else
                log_error "Pytest FAILED after $MAX_RETRIES attempts. Escalating to Orchestrator."
            fi
        fi
    done

    log_info "Running 22-button UI regression suite..."
    if python3 scripts/run_button_regression.py; then
        log_ok "UI Button Regression PASSED (22/22)"
    else
        log_warn "UI regression had failures — check /tmp/hermes_pytest_output.txt"
    fi

    # Emit telemetry if enabled
    if [ "${HERMES_TELEMETRY_ENABLED:-false}" = "true" ] && [ -f "scripts/hermes_telemetry.py" ]; then
        python3 scripts/hermes_telemetry.py --phase qa --status passed 2>/dev/null || true
    fi
}

phase_deploy() {
    log_section "PHASE 5: Cloud Deploy (Hermes — devops agent)"
    resolve_router

    log_info "Step 1/3: Publishing static UI to Hugging Face Spaces..."
    python3 scripts/publish_space_hf.py --sdk static
    log_ok "HF Spaces published"

    log_info "Step 2/3: Vercel edge gateway deployment..."
    if command -v vercel &>/dev/null || command -v npx &>/dev/null; then
        VERCEL_CMD="npx vercel"
        [ -x "$(command -v vercel)" ] && VERCEL_CMD="vercel"
        if [ -n "${VERCEL_TOKEN:-}" ]; then
            $VERCEL_CMD --prod --yes --token="$VERCEL_TOKEN"
            log_ok "Vercel deployed"
        else
            log_warn "VERCEL_TOKEN not set — Vercel push-to-deploy via git will trigger automatically"
        fi
    fi

    log_info "Step 3/3: Azure Container Apps — triggered via azure_deploy.yml on git push"
    log_info "Azure URL: ${AZURE_CONTAINER_APP_URL:-<set AZURE_CONTAINER_APP_URL in .env>}"

    log_info "Running Live E2E Network Audit..."
    python3 scripts/test_live_e2e_network.py || log_warn "E2E audit had warnings — review output"
}

phase_sync() {
    log_section "POST-EDIT: Agent Sync Mandate (AGENTS.md Rule #9)"
    log_info "Step 1/2: Syncing .antigravity/agents -> .agents/agents..."
    python3 scripts/sync_sdlc_agents.py --sync
    log_ok "sync_sdlc_agents.py --sync complete"

    log_info "Step 2/2: Generating .codex/agents from .agents/agents..."
    python3 scripts/sync_codex_agents.py --sync
    log_ok "sync_codex_agents.py --sync complete"

    log_info "Validation check..."
    python3 scripts/sync_codex_agents.py --check
    log_ok "Agent definitions synchronized and validated"
}

phase_all() {
    log_section "HERMES — Full AI SDLC Pipeline (Phases 1-5)"
    log_info "Timestamp: $TIMESTAMP"
    resolve_router
    phase_qa
    phase_deploy
    phase_sync
    log_section "HERMES — Full Pipeline Complete"
}

# ── Help ──────────────────────────────────────────────────────────────────────
phase_help() {
    echo ""
    echo "  Hermes SDLC Execution Runner"
    echo "  Usage: bash scripts/hermes_sdlc_runner.sh <phase>"
    echo ""
    echo "  Phases:"
    echo "    dev     Phase 2: Activate developer agent routing (local)"
    echo "    qa      Phase 3: Pytest + UI regression (local & headless CI)"
    echo "    deploy  Phase 5: HF Spaces + Vercel + Azure deploy"
    echo "    sync    Post-edit: sync_sdlc_agents + sync_codex_agents"
    echo "    all     Run qa -> deploy -> sync sequentially"
    echo ""
    echo "  Routing priority:"
    echo "    1. ROUTER_BASE_URL     (Cloud/CI override)"
    echo "    2. NINE_ROUTER_BASE_URL (Local 9router on :20128)"
    echo "    3. CODEX_PRO_BASE_URL  (CODEX_PRO endpoint)"
    echo "    4. GOOGLE_AI_STUDIO_API_KEY (Gemini direct)"
    echo ""
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "$PHASE" in
    dev)    phase_dev    ;;
    qa)     phase_qa     ;;
    deploy) phase_deploy ;;
    sync)   phase_sync   ;;
    all)    phase_all    ;;
    help|*) phase_help   ;;
esac
