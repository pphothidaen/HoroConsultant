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
AGY_ROUTING_CONFIG="${HERMES_AGY_ROUTING_CONFIG:-$ROOT_DIR/.agents/config/gemini_parity.yaml}"
HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-analysis}"
HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-high}"

# ── ASCII Logging Helpers (Pure ASCII per .agents/AGENTS.md Rule #3) ──────────
log_info()    { echo "[INFO]    $*"; }
log_ok()      { echo "[OK]      $*"; }
log_warn()    { echo "[WARNING] $*"; }
log_error()   { echo "[ERROR]   $*"; exit 1; }
log_section() { echo ""; echo "======================================================================"; echo "  $*"; echo "======================================================================"; }
HERMES_START_NOTIFY_ENABLED="${HERMES_START_NOTIFY_ENABLED:-true}"

hermes_escape_json() {
    local value="${1:-}"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/\\r}"
    value="${value//$'\t'/\\t}"
    printf '%s' "$value"
}

send_hermes_webhook() {
    local url="$1"
    local payload="$2"

    if [ -z "$url" ] || [ -z "$payload" ]; then
        return 1
    fi

    if ! command -v curl >/dev/null 2>&1; then
        log_warn "curl is unavailable — skipping HTTP notification"
        return 1
    fi

    if curl -sS --max-time 10 -H "Content-Type: application/json" -d "$payload" "$url" >/dev/null; then
        return 0
    else
        return 1
    fi
}

notify_hermes_start() {
    local phase="$1"
    local status="$2"
    local router="${RESOLVED_ROUTER_URL:-${OPENAI_BASE_URL:-<direct LLM backend>}}"
    local account_alias="${HERMES_ACCOUNT_ALIAS_RESOLVED:-agy1}"
    local model="${HERMES_ROUTER_MODEL:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}}"
    local message
    local sent_count=0
    local escaped

    if [ "${HERMES_START_NOTIFY_ENABLED:-true}" != "true" ]; then
        return 0
    fi

    message="Hermes started [$phase] status=$status account=$account_alias model=$model router=$router complexity=${HERMES_TASK_COMPLEXITY:-medium} ts=$TIMESTAMP"
    escaped="$(hermes_escape_json "$message")"

    if [ -n "${HERMES_NOTIFY_WEBHOOK_URL:-}" ] && send_hermes_webhook "$HERMES_NOTIFY_WEBHOOK_URL" "{\"text\":\"$escaped\"}"; then
        log_ok "Notification sent to HERMES_NOTIFY_WEBHOOK_URL"
        sent_count=$((sent_count+1))
    elif [ -n "${HERMES_NOTIFY_WEBHOOK_URL:-}" ]; then
        log_warn "Failed to send notification to HERMES_NOTIFY_WEBHOOK_URL"
    fi

    if [ -n "${DISCORD_WEBHOOK_URL:-}" ] && send_hermes_webhook "$DISCORD_WEBHOOK_URL" "{\"content\":\"$escaped\"}"; then
        log_ok "Notification sent to DISCORD_WEBHOOK_URL"
        sent_count=$((sent_count+1))
    elif [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
        log_warn "Failed to send notification to DISCORD_WEBHOOK_URL"
    fi

    if [ -n "${SLACK_WEBHOOK_URL:-}" ] && send_hermes_webhook "$SLACK_WEBHOOK_URL" "{\"text\":\"$escaped\"}"; then
        log_ok "Notification sent to SLACK_WEBHOOK_URL"
        sent_count=$((sent_count+1))
    elif [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        log_warn "Failed to send notification to SLACK_WEBHOOK_URL"
    fi

    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        if send_hermes_webhook "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" "{\"chat_id\":\"$TELEGRAM_CHAT_ID\",\"text\":\"$escaped\"}"; then
            log_ok "Notification sent to Telegram"
            sent_count=$((sent_count+1))
        else
            log_warn "Failed to send Telegram notification"
        fi
    elif [ -n "${TELEGRAM_BOT_TOKEN:-}${TELEGRAM_CHAT_ID:-}" ]; then
        log_warn "Telegram notify requested but token or chat id is missing"
    fi

    if [ "$sent_count" -eq 0 ]; then
        log_warn "No notification channel configured for Hermes start event"
    fi
}

resolve_hermes_route_profile() {
    local requested_alias="${HERMES_ACCOUNT_ALIAS:-${ROUTER_ACCOUNT_ALIAS:-${NINE_ROUTER_ACCOUNT_ALIAS:-agy1}}}"
    local requested_role="${HERMES_TASK_ROLE:-analysis}"
    local requested_complexity="${HERMES_TASK_COMPLEXITY:-high}"
    local route_line
    local model time alias chain

    if [ -f "$AGY_ROUTING_CONFIG" ] && command -v python3 >/dev/null 2>&1; then
        if route_line="$(python3 "$SCRIPT_DIR/hermes_agy_router.py" \
            --alias "$requested_alias" \
            --role "$requested_role" \
            --complexity "$requested_complexity" \
            --config "$AGY_ROUTING_CONFIG")"; then

            if [ -n "$route_line" ]; then
                IFS='|' read -r model time alias chain _role _complexity codex_fallback_model <<< "$route_line"
                export HERMES_ROUTER_MODEL="${model:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}}"
                export HERMES_ROUTER_TIME="${time:-medium}"
                export HERMES_ACCOUNT_ALIAS_RESOLVED="${alias:-$requested_alias}"
                export NINE_ROUTER_DEVELOPER_MODEL="${HERMES_ROUTER_MODEL}"
                export AGY_FALLBACK_CHAIN="${chain:-agy1,agy2,codex_subagent}"
                export HERMES_RESOLVED_ROLE="${_role:-$requested_role}"
                export HERMES_RESOLVED_COMPLEXITY="${_complexity:-$requested_complexity}"
                export HERMES_CODEX_FALLBACK_MODEL="${codex_fallback_model:-gpt-5.3-codex-spark high}"
                return 0
            fi
        fi
    fi

    log_warn "AGY routing config not available; using legacy env/model defaults."
    export HERMES_ROUTER_MODEL="${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}"
    export HERMES_ROUTER_TIME="medium"
    export HERMES_ACCOUNT_ALIAS_RESOLVED="${requested_alias}"
    export NINE_ROUTER_DEVELOPER_MODEL="${HERMES_ROUTER_MODEL}"
    export AGY_FALLBACK_CHAIN="agy1,agy2,codex_subagent"
    export HERMES_RESOLVED_ROLE="${requested_role}"
    export HERMES_RESOLVED_COMPLEXITY="${requested_complexity}"
    export HERMES_CODEX_FALLBACK_MODEL="gpt-5.3-codex-spark high"
}

# ── 9router Health Check & Routing Resolution ─────────────────────────────────
resolve_router() {
    resolve_hermes_route_profile

    HERMES_TASK_ROLE="${HERMES_RESOLVED_ROLE:-implementation}"
    HERMES_TASK_COMPLEXITY="${HERMES_RESOLVED_COMPLEXITY:-medium}"
    ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS_RESOLVED:-agy1}"

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
    export HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-implementation}"
    export HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-medium}"
    resolve_router
    log_info "Router resolved. Developer agent now active via $OPENAI_BASE_URL"
    log_info "Routing profile: role=${HERMES_RESOLVED_ROLE:-implementation}, complexity=${HERMES_RESOLVED_COMPLEXITY:-medium}"
    log_info "Model: ${HERMES_ROUTER_MODEL:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}} (via ${ACCOUNT_ALIAS}, time=${HERMES_ROUTER_TIME:-medium})"
    log_info "Fallback chain: ${AGY_FALLBACK_CHAIN:-agy1,agy2,codex_subagent}"
    log_info "Codex fallback model: ${HERMES_CODEX_FALLBACK_MODEL:-gpt-5.3-codex-spark high}"
    notify_hermes_start "dev" "routing_ready"
    log_ok "Environment ready. Run: agy --agent developer '<task>'"
}

phase_qa() {
    log_section "PHASE 3: QA Testing (Hermes Headless — qa_tester agent)"
    export HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-review}"
    export HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-medium}"
    resolve_router
    notify_hermes_start "qa" "execution"
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
    export HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-implementation}"
    export HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-medium}"
    resolve_router
    notify_hermes_start "deploy" "execution"

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
    notify_hermes_start "sync" "execution"
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
    export HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-implementation}"
    export HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-medium}"
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
