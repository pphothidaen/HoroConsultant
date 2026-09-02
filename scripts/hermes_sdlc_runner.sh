#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - Hermes SDLC Execution Runner
# ==============================================================================
# Hermes Execution Engine: Plan -> Act -> Observe -> Reflect loop dispatcher.
# Supports two runtime modes:
#   LOCAL   - Interactive developer Mac with 9router on localhost:20128
#   CI/CD   - Headless GitHub Actions runner with ROUTER_BASE_URL from secrets
#
# Usage:
#   bash scripts/hermes_sdlc_runner.sh dev      # Phase 2: Core Implementation
#   bash scripts/hermes_sdlc_runner.sh qa        # Phase 3: Automated QA
#   bash scripts/hermes_sdlc_runner.sh release-plan # Local release dry-run
#   bash scripts/hermes_sdlc_runner.sh deploy    # BLOCKED: governed CI only
#   bash scripts/hermes_sdlc_runner.sh sync      # Post-edit: Agent sync mandate
#   bash scripts/hermes_sdlc_runner.sh all       # Full pipeline (1->5)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Local runners never source credential files. Export non-secret routing values
# explicitly when using dev or QA orchestration.

PHASE="${1:-help}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S %z')"
MAX_RETRIES="${HERMES_MAX_LOOP_RETRIES:-3}"
AGY_ROUTING_CONFIG="${HERMES_AGY_ROUTING_CONFIG:-$ROOT_DIR/.agents/config/gemini_parity.yaml}"
HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-analysis}"
HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-high}"

# ASCII logging helpers (Pure ASCII per .agents/AGENTS.md Rule #3)
log_info()    { echo "[INFO]    $*"; }
log_ok()      { echo "[OK]      $*"; }
log_warn()    { echo "[WARNING] $*"; }
log_error()   { echo "[ERROR]   $*"; exit 1; }
log_section() { echo ""; echo "======================================================================"; echo "  $*"; echo "======================================================================"; }
notify_hermes_start() {
    local phase="$1"
    local status="$2"
    log_info "Local notification suppressed: phase=$phase status=$status."
}

resolve_hermes_route_profile() {
    local requested_alias="${HERMES_ACCOUNT_ALIAS:-${ROUTER_ACCOUNT_ALIAS:-${NINE_ROUTER_ACCOUNT_ALIAS:-codex1}}}"
    local requested_role="${HERMES_TASK_ROLE:-analysis}"
    local requested_complexity="${HERMES_TASK_COMPLEXITY:-medium}"
    local sdlc_phase="${HERMES_SDLC_PHASE:-}"
    local route_line
    local model time alias chain

    if [ -f "$AGY_ROUTING_CONFIG" ] && command -v python3 >/dev/null 2>&1; then
        # Build router args; prefer --phase when set.
        local router_args=("--config" "$AGY_ROUTING_CONFIG")
        if [ -n "$sdlc_phase" ]; then
            router_args+=("--phase" "$sdlc_phase")
        else
            router_args+=("--alias" "$requested_alias" "--role" "$requested_role" "--complexity" "$requested_complexity")
        fi

        if route_line="$(python3 "$SCRIPT_DIR/hermes_agy_router.py" "${router_args[@]}")"; then
            if [ -n "$route_line" ]; then
                IFS='|' read -r model time alias chain _role _complexity codex_fallback_model <<< "$route_line"
                export HERMES_ROUTER_MODEL="${model:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}}"
                export HERMES_ROUTER_TIME="${time:-medium}"
                export HERMES_ACCOUNT_ALIAS_RESOLVED="${alias:-$requested_alias}"
                export NINE_ROUTER_DEVELOPER_MODEL="${HERMES_ROUTER_MODEL}"
                export AGY_FALLBACK_CHAIN="${chain:-codex1,codex2,codex3}"
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
    export AGY_FALLBACK_CHAIN="codex1,codex2,codex3"
    export HERMES_RESOLVED_ROLE="${requested_role}"
    export HERMES_RESOLVED_COMPLEXITY="${requested_complexity}"
    export HERMES_CODEX_FALLBACK_MODEL="gpt-5.3-codex-spark high"
}

# 9router health check and routing resolution
resolve_router() {
    resolve_hermes_route_profile

    HERMES_TASK_ROLE="${HERMES_RESOLVED_ROLE:-implementation}"
    HERMES_TASK_COMPLEXITY="${HERMES_RESOLVED_COMPLEXITY:-medium}"
    ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS_RESOLVED:-codex1}"

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
            log_ok "9router UP at $NINE_ROUTER_BASE_URL - routing via proxy (Account Alias: $ACCOUNT_ALIAS)"
            export OPENAI_BASE_URL="$RESOLVED_ROUTER_URL"
            export OPENAI_API_KEY="${NINE_ROUTER_API_KEY:-dummy}"
            export NINE_ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            export ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            export HTTP_HEADER_X_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
            return 0
        else
            log_warn "9router at $NINE_ROUTER_BASE_URL not reachable - trying fallback"
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

# Phase implementations

phase_dev() {
    log_section "PHASE 2: Core Implementation (Hermes - developer agent)"
    export HERMES_SDLC_PHASE="dev"                   # implementation/medium/codex2
    export HERMES_TASK_ROLE="implementation"
    export HERMES_TASK_COMPLEXITY="medium"
    resolve_router
    log_info "Router resolved. Developer agent now active via $OPENAI_BASE_URL"
    log_info "Routing profile: role=${HERMES_RESOLVED_ROLE:-implementation}, complexity=${HERMES_RESOLVED_COMPLEXITY:-medium}"
    log_info "Model: ${HERMES_ROUTER_MODEL:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}} (via ${ACCOUNT_ALIAS}, time=${HERMES_ROUTER_TIME:-medium})"
    log_info "Fallback chain: ${AGY_FALLBACK_CHAIN:-codex1,codex2,codex3}"
    log_info "Codex fallback model: ${HERMES_CODEX_FALLBACK_MODEL:-gpt-5.3-codex-spark high}"
    notify_hermes_start "dev" "routing_ready"
    log_ok "Environment ready. Run: agy --agent developer '<task>'"
}

phase_qa() {
    log_section "PHASE 3: QA Testing (Hermes Headless - qa_tester agent)"
    export HERMES_SDLC_PHASE="qa"                    # review/low/codex1
    export HERMES_TASK_ROLE="review"
    export HERMES_TASK_COMPLEXITY="low"              # QA is deterministic pytest, not LLM
    resolve_router
    notify_hermes_start "qa" "execution"
    local retry=0

    while [ $retry -lt "$MAX_RETRIES" ]; do
        log_info "QA attempt $((retry+1))/$MAX_RETRIES - running pytest..."
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
        log_warn "UI regression had failures - check /tmp/hermes_pytest_output.txt"
    fi

    log_info "Local telemetry emission is disabled; governed CI owns external evidence publication."
}

phase_deploy() {
    log_section "PHASE 5: Local production mutation is blocked"
    log_error "BLOCKED: deploy/publish/push must run from a READY, target-bound release ticket through governed CI."
}

phase_release_plan() {
    log_section "LOCAL RELEASE READINESS: QA evidence and HF Docker dry-run"
    log_info "Running secret leakage scan."
    python3 project/core/code_reviewer.py --scan-secrets
    log_info "Running canonical HF Docker payload dry-run without upload."
    python3 scripts/publish_space_hf.py \
        --space-id pphothidaen/horoconsultant-core-backend \
        --sdk docker \
        --dry-run
    log_ok "Local release readiness dry-run completed."
    log_warn "No deploy, publish, push, or secret synchronization was performed."
    log_info "Production release requires a READY, target-bound ticket in atomic_tasks.md through governed CI."
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
    log_section "HERMES - Local AI SDLC Validation Pipeline"
    log_info "Timestamp: $TIMESTAMP"
    export HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-implementation}"
    export HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-medium}"
    resolve_router
    phase_qa
    phase_release_plan
    phase_sync
    log_section "HERMES - Local Validation Pipeline Complete"
}

# Help
phase_help() {
    echo ""
    echo "  Hermes SDLC Execution Runner"
    echo "  Usage: bash scripts/hermes_sdlc_runner.sh <phase>"
    echo ""
    echo "  Phases:"
    echo "    dev     Phase 2: Activate developer agent routing (local)"
    echo "    qa      Phase 3: Pytest + UI regression (local & headless CI)"
    echo "    release-plan  Secret scan + canonical HF Docker payload dry-run"
    echo "    deploy        BLOCKED: production release belongs to governed CI"
    echo "    sync    Post-edit: sync_sdlc_agents + sync_codex_agents"
    echo "    all     Run qa -> release-plan -> sync sequentially"
    echo ""
    echo "  Routing priority:"
    echo "    1. ROUTER_BASE_URL     (Cloud/CI override)"
    echo "    2. NINE_ROUTER_BASE_URL (Local 9router on :20128)"
    echo "    3. CODEX_PRO_BASE_URL  (CODEX_PRO endpoint)"
    echo "    4. GOOGLE_AI_STUDIO_API_KEY (Gemini direct)"
    echo ""
}

# Dispatch
case "$PHASE" in
    dev)          phase_dev          ;;
    qa)           phase_qa           ;;
    release-plan) phase_release_plan ;;
    deploy)       phase_deploy       ;;
    sync)         phase_sync         ;;
    all)          phase_all          ;;
    help|-h|--help) phase_help       ;;
    *) log_error "BLOCKED: unsupported local phase '$PHASE'. Use help or a governed CI release ticket." ;;
esac
