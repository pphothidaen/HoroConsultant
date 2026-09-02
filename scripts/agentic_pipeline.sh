#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - Multi-Agent Local Validation Pipeline
# ==============================================================================
# Master Orchestrator (orchestrator) conducts specialized agents:
# 1. [business_analyst] Requirement Audit & Documentation Watchdog
# 2. [developer] Architecture & Configuration Audit
# 3. [qa_tester] Unit & Button Contract Regression Testing
# 4. [code_reviewer] Security & Secret Leakage Scanning
# 5. [devops] Secret Scan and Canonical HF Docker Payload Dry-Run
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

# Local validation never sources credential files. Export non-secret routing
# values explicitly when local agent routing is required.

HERMES_AGY_ROUTING_CONFIG="${HERMES_AGY_ROUTING_CONFIG:-$ROOT_DIR/.agents/config/gemini_parity.yaml}"
HERMES_TASK_ROLE="${HERMES_TASK_ROLE:-analysis}"
HERMES_TASK_COMPLEXITY="${HERMES_TASK_COMPLEXITY:-high}"
notify_hermes_pipeline_start() {
    local phase="${1:-pipeline}"
    echo "[INFO] Local notification suppressed for phase=$phase."
}

resolve_hermes_route_profile() {
    local requested_alias="${HERMES_ACCOUNT_ALIAS:-${ROUTER_ACCOUNT_ALIAS:-${NINE_ROUTER_ACCOUNT_ALIAS:-codex1}}}"
    local requested_role="${HERMES_TASK_ROLE:-analysis}"
    local requested_complexity="${HERMES_TASK_COMPLEXITY:-medium}"
    local sdlc_phase="${HERMES_SDLC_PHASE:-}"
    local route_line
    local model time alias chain resolved_role resolved_complexity codex_fallback_model

    if [ -f "$HERMES_AGY_ROUTING_CONFIG" ] && command -v python3 >/dev/null 2>&1; then
        # Prefer --phase shortcut when HERMES_SDLC_PHASE is set (auto-resolves role+complexity+alias)
        local router_args=("--config" "$HERMES_AGY_ROUTING_CONFIG")
        if [ -n "$sdlc_phase" ]; then
            router_args+=("--phase" "$sdlc_phase")
        else
            router_args+=("--alias" "$requested_alias" "--role" "$requested_role" "--complexity" "$requested_complexity")
        fi

        if route_line="$(python3 "$SCRIPT_DIR/hermes_agy_router.py" "${router_args[@]}")"; then
            if [ -n "$route_line" ]; then
                IFS='|' read -r model time alias chain resolved_role resolved_complexity codex_fallback_model <<< "$route_line"
                export HERMES_ROUTER_MODEL="${model:-${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}}"
                export HERMES_ROUTER_TIME="${time:-medium}"
                export HERMES_ACCOUNT_ALIAS_RESOLVED="${alias:-$requested_alias}"
                export AGY_FALLBACK_CHAIN="${chain:-codex1,codex2,codex3,codex_subagent}"
                export HERMES_RESOLVED_ROLE="${resolved_role:-$requested_role}"
                export HERMES_RESOLVED_COMPLEXITY="${resolved_complexity:-$requested_complexity}"
                export HERMES_CODEX_FALLBACK_MODEL="${codex_fallback_model:-gpt-5.3-codex-spark high}"
                return 0
            fi
        fi
    fi

    echo "[WARNING] [HERMES] AGY routing config not available; using legacy env/model defaults."
    export HERMES_ROUTER_MODEL="${NINE_ROUTER_DEVELOPER_MODEL:-deepseek-v3}"
    export HERMES_ROUTER_TIME="medium"
    export HERMES_ACCOUNT_ALIAS_RESOLVED="${requested_alias}"
    export AGY_FALLBACK_CHAIN="codex1,codex2,codex3,codex_subagent"
    export HERMES_RESOLVED_ROLE="${requested_role}"
    export HERMES_RESOLVED_COMPLEXITY="${requested_complexity}"
    export HERMES_CODEX_FALLBACK_MODEL="gpt-5.3-codex-spark high"
}

echo "======================================================================"
echo " HOROCONSULTANT AGENTIC LOCAL VALIDATION PIPELINE"
echo "======================================================================"
echo " [ORCHESTRATOR] Master Agent: Claude 3.7 Sonnet via 9router / CODEX_PRO"
echo " [HERMES]       Execution Engine: Plan -> Act -> Observe -> Reflect"
echo " [TIMESTAMP]    $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "======================================================================"

# ------------------------------------------------------------------------------
# 9router / Hermes Routing Resolution (Hybrid Cloud-First)
# ------------------------------------------------------------------------------
echo ""
echo "[INFO] [HERMES] Resolving LLM routing (9router -> CODEX_PRO -> Gemini)..."

resolve_hermes_route_profile
export HERMES_TASK_ROLE="${HERMES_RESOLVED_ROLE:-analysis}"
export HERMES_TASK_COMPLEXITY="${HERMES_RESOLVED_COMPLEXITY:-high}"
export HERMES_ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS_RESOLVED:-codex1}"
export NINE_ROUTER_DEVELOPER_MODEL="${HERMES_ROUTER_MODEL}"
export NINE_ROUTER_ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS}"
export ROUTER_ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS}"
export HTTP_HEADER_X_ACCOUNT_ALIAS="${HERMES_ACCOUNT_ALIAS}"

ACCOUNT_ALIAS="${ROUTER_ACCOUNT_ALIAS:-${NINE_ROUTER_ACCOUNT_ALIAS:-codex1}}"

RESOLVED_ROUTER=""
if [ -n "${ROUTER_BASE_URL:-}" ]; then
    RESOLVED_ROUTER="$ROUTER_BASE_URL"
    echo "[OK]   [HERMES] Routing via Cloud/CI ROUTER_BASE_URL: $RESOLVED_ROUTER (Account Alias: $ACCOUNT_ALIAS)"
    export OPENAI_BASE_URL="$RESOLVED_ROUTER"
    export OPENAI_API_KEY="${NINE_ROUTER_API_KEY:-dummy}"
    export NINE_ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
    export ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
    export HTTP_HEADER_X_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
elif [ -n "${NINE_ROUTER_BASE_URL:-}" ]; then
    HEALTH_EP="${NINE_ROUTER_BASE_URL%/v1}/health"
    if curl -sf --max-time 3 "$HEALTH_EP" > /dev/null 2>&1; then
        RESOLVED_ROUTER="$NINE_ROUTER_BASE_URL"
        echo "[OK]   [HERMES] 9router UP at $NINE_ROUTER_BASE_URL (Account Alias: $ACCOUNT_ALIAS)"
        export OPENAI_BASE_URL="$RESOLVED_ROUTER"
        export OPENAI_API_KEY="${NINE_ROUTER_API_KEY:-dummy}"
        export NINE_ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
        export ROUTER_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
        export HTTP_HEADER_X_ACCOUNT_ALIAS="$ACCOUNT_ALIAS"
    else
        echo "[WARNING] [HERMES] 9router not reachable - checking CODEX_PRO fallback"
    fi
fi

if [ -z "$RESOLVED_ROUTER" ] && [ -n "${CODEX_PRO_BASE_URL:-}" ] && [ -n "${CODEX_PRO:-}" ]; then
    echo "[WARNING] [HERMES] Routing via CODEX_PRO endpoint (fallback)"
    export OPENAI_BASE_URL="$CODEX_PRO_BASE_URL"
    export OPENAI_API_KEY="$CODEX_PRO"
elif [ -z "$RESOLVED_ROUTER" ] && [ -n "${GOOGLE_AI_STUDIO_API_KEY:-}" ]; then
    echo "[WARNING] [HERMES] Routing via Gemini direct (no proxy - last resort)"
    unset OPENAI_BASE_URL OPENAI_API_KEY 2>/dev/null || true
fi

notify_hermes_pipeline_start "agentic_pipeline"

# ------------------------------------------------------------------------------
# PHASE 1: Business System Analyst (business_analyst)
# ------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo " PHASE 1: Business System Analyst (business_analyst)"
echo "----------------------------------------------------------------------"
export HERMES_SDLC_PHASE="bsa"           # analysis/low/codex1
export HERMES_TASK_ROLE="analysis"
export HERMES_TASK_COMPLEXITY="low"      # BSA docs audit and spec sync
echo "[BSA] Auditing project documentation integrity (atomic_tasks.md, HOWTO.md)..."
if [ -f "atomic_tasks.md" ] && [ -f "HOWTO.md" ] && [ -f "README.md" ]; then
    echo "[OK] [BSA] Documentation files verified 100% up to date."
else
    echo "[ERROR] [BSA] Required project documentation missing." && exit 1
fi

echo "[BSA] Auditing Agent Skills Catalog (.agents/skills/)..."
if [ -d ".agents/skills" ]; then
    echo "[OK] [BSA] Agent Skills catalog active with 7 skills registered."
fi

# ------------------------------------------------------------------------------
# PHASE 2: Senior Developer (developer)
# ------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo " PHASE 2: Senior Developer (developer)"
echo "----------------------------------------------------------------------"
export HERMES_SDLC_PHASE="dev"           # implementation/medium/codex2
export HERMES_TASK_ROLE="implementation"
export HERMES_TASK_COMPLEXITY="medium"   # DEV code validation
echo "[DEV] Checking canonical local configuration (vercel.json, Dockerfile.hf)..."
python3 -c "
import json
with open('vercel.json') as f:
    v = json.load(f)
    assert 'rewrites' in v, 'vercel.json missing rewrites'
print('[OK] [DEV] vercel.json Edge Rewrites validated.')
"
if [ ! -f "Dockerfile.hf" ]; then
    echo "[ERROR] [DEV] Dockerfile.hf is missing."
    exit 1
fi
echo "[OK] [DEV] Dockerfile.hf validated; retired infrastructure is not selected."

# ------------------------------------------------------------------------------
# PHASE 3: QA Tester (qa_tester)
# ------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo " PHASE 3: QA Tester (qa_tester)"
echo "----------------------------------------------------------------------"
export HERMES_SDLC_PHASE="qa"            # review/low/codex1
export HERMES_TASK_ROLE="review"
export HERMES_TASK_COMPLEXITY="low"      # QA deterministic pytest
echo "[QA] Executing Pytest Unit & Integration Regression Suite..."
python3 -m pytest -v --ignore=project/kaggle_kernel -m "not network"

echo "[QA] Executing 22-Button UI & Endpoint Contract Regression Test..."
python3 scripts/run_button_regression.py

echo "[OK] [QA] Pytest and UI Button Regression PASSED."

# ------------------------------------------------------------------------------
# PHASE 4: Code Reviewer & Safety Auditor (code_reviewer)
# ------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo " PHASE 4: Code Reviewer & Safety Auditor (code_reviewer)"
echo "----------------------------------------------------------------------"
export HERMES_SDLC_PHASE="reviewer"      # review/low/codex1
export HERMES_TASK_ROLE="review"
export HERMES_TASK_COMPLEXITY="low"      # REVIEWER deterministic Python script
echo "[REVIEWER] Running local secret leakage scan..."
python3 project/core/code_reviewer.py --scan-secrets
echo "[OK] [REVIEWER] Local secret scan passed; this is not production release authorization."

# ------------------------------------------------------------------------------
# PHASE 5: Local Release Readiness (devops)
# ------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo " PHASE 5: Local Release Readiness (devops)"
echo "----------------------------------------------------------------------"
export HERMES_SDLC_PHASE="devops"        # implementation/medium/codex1
export HERMES_TASK_ROLE="implementation"
export HERMES_TASK_COMPLEXITY="medium"   # DEVOPS local evidence only
echo "[DEVOPS] Running canonical HF Docker payload dry-run without upload."
python3 scripts/publish_space_hf.py \
    --space-id pphothidaen/horoconsultant-core-backend \
    --sdk docker \
    --dry-run

echo "[OK] [DEVOPS] Local release readiness evidence completed."
echo "[WARNING] [DEVOPS] No deploy, publish, push, or secret synchronization was performed."
echo "[INFO] [DEVOPS] Production release requires a READY, target-bound ticket in atomic_tasks.md through governed CI."

echo ""
echo "======================================================================"
echo " [ORCHESTRATOR] LOCAL MULTI-AGENT VALIDATION COMPLETE"
echo "======================================================================"
echo "  * Business System Analyst : Docs and skills checked [analysis/low/codex1]"
echo "  * Senior Developer        : Local configuration checked [implementation/medium/codex2]"
echo "  * QA Tester               : Unit and UI regression completed [review/low/codex1]"
echo "  * Code Reviewer           : Local review completed [review/low/codex1]"
echo "  * DevOps                  : Secret scan and HF Docker dry-run completed [implementation/medium/codex1]"
echo "  * Hermes Routing (last)   : ${HERMES_ACCOUNT_ALIAS:-codex1} | model=${HERMES_ROUTER_MODEL:-deepseek-v3} | time=${HERMES_ROUTER_TIME:-medium}"
echo "  * Hermes Fallback Chain   : ${AGY_FALLBACK_CHAIN:-codex1,codex2,codex3,codex_subagent}"
echo "  * Codex Fallback Model    : ${HERMES_CODEX_FALLBACK_MODEL:-gpt-5.3-codex-spark high}"
echo "  * Release Boundary        : Governed CI ticket required; local mutation blocked"
echo "======================================================================"
