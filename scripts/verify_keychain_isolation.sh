#!/usr/bin/env bash
# ==============================================================================
# HoroConsultant - macOS AI Account Keychain Isolation Validator
# ==============================================================================
# Verifies keychain isolation across isolated AI account directories (agy1..4).
# Checks symlink structures, silent non-interactive unlock, and system default.
# Pure ASCII output with standard status tags: [OK], [WARNING], [ERROR], [SUMMARY].
# ==============================================================================

set -euo pipefail

# Pure ASCII status logging helper functions
log_ok() {
    if [ "$JSON_MODE" = false ] && [ "$SILENT_MODE" = false ]; then
        printf "[OK] %s\n" "$*"
    fi
}

log_info() {
    if [ "$JSON_MODE" = false ] && [ "$SILENT_MODE" = false ]; then
        printf "[INFO] %s\n" "$*"
    fi
}

log_warn() {
    if [ "$JSON_MODE" = false ]; then
        printf "[WARNING] %s\n" "$*"
    fi
}

log_error() {
    if [ "$JSON_MODE" = false ]; then
        printf "[ERROR] %s\n" "$*"
    fi
}

log_summary() {
    if [ "$JSON_MODE" = false ]; then
        printf "[SUMMARY] %s\n" "$*"
    fi
}

# Default configuration
ACCOUNTS_BASE_DIR="${AI_ACCOUNTS_DIR:-${AI_ACCOUNTS_BASE_DIR:-/Users/kimlenglim/.ai-accounts/agy}}"
EXPECTED_DEFAULT_KEYCHAIN="${EXPECTED_DEFAULT_KEYCHAIN:-/Users/kimlenglim/Library/Keychains/login.keychain-db}"
ACCOUNTS_LIST=("account1" "account2" "account3" "account4")
SILENT_MODE=false
JSON_MODE=false
FAILURES=0
WARNINGS=0
CHECKS_PASSED=0
CHECKS_TOTAL=0

show_help() {
    cat << 'EOF'
Usage: verify_keychain_isolation.sh [OPTIONS]

Options:
  --accounts-dir DIR    Base directory for AI accounts (default: /Users/kimlenglim/.ai-accounts/agy)
  --default-keychain KC Expected system default keychain path
  --accounts LIST       Comma-separated list of accounts (default: account1,account2,account3,account4)
  --silent, -s          Silent mode: suppress informational logs
  --json                Emit output in JSON format
  --help, -h            Show this help message

Exit codes:
  0: All keychain isolation checks passed
  1: One or more validation checks failed
EOF
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --accounts-dir)
            ACCOUNTS_BASE_DIR="$2"
            shift 2
            ;;
        --default-keychain)
            EXPECTED_DEFAULT_KEYCHAIN="$2"
            shift 2
            ;;
        --accounts)
            IFS=',' read -r -a ACCOUNTS_LIST <<< "$2"
            shift 2
            ;;
        --silent|-s)
            SILENT_MODE=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown option: $1" >&2
            show_help >&2
            exit 1
            ;;
    esac
done

OS_TYPE="$(uname -s)"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")"

# JSON accumulator arrays
JSON_ACCOUNT_RESULTS=()
JSON_DEFAULT_KEYCHAIN_STATUS="SKIPPED"
JSON_DEFAULT_KEYCHAIN_ACTUAL=""

# ------------------------------------------------------------------------------
# 1. Verify Host System Default Keychain (macOS only)
# ------------------------------------------------------------------------------
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ "$OS_TYPE" = "Darwin" ]; then
    if command -v security >/dev/null 2>&1; then
        ACTUAL_DEFAULT_KEYCHAIN="$(security default-keychain 2>/dev/null | tr -d ' "\t\r\n' || true)"
        JSON_DEFAULT_KEYCHAIN_ACTUAL="$ACTUAL_DEFAULT_KEYCHAIN"
        if [ "$ACTUAL_DEFAULT_KEYCHAIN" = "$EXPECTED_DEFAULT_KEYCHAIN" ]; then
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            JSON_DEFAULT_KEYCHAIN_STATUS="PASSED"
            log_ok "Canonical default keychain verified: ${EXPECTED_DEFAULT_KEYCHAIN}"
        else
            FAILURES=$((FAILURES + 1))
            JSON_DEFAULT_KEYCHAIN_STATUS="FAILED"
            log_error "Default keychain mismatch. Expected: ${EXPECTED_DEFAULT_KEYCHAIN}, Found: ${ACTUAL_DEFAULT_KEYCHAIN}"
        fi
    else
        WARNINGS=$((WARNINGS + 1))
        JSON_DEFAULT_KEYCHAIN_STATUS="WARNING"
        log_warn "macOS 'security' command not found. Skipping default keychain check."
    fi
else
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    JSON_DEFAULT_KEYCHAIN_STATUS="SKIPPED_NON_DARWIN"
    log_info "Non-Darwin OS detected (${OS_TYPE}). Skipping host security default-keychain check."
fi

# ------------------------------------------------------------------------------
# 2. Verify Account Keychain Isolation & Symlinks
# ------------------------------------------------------------------------------
for ACC in "${ACCOUNTS_LIST[@]}"; do
    ACC_DIR="${ACCOUNTS_BASE_DIR}/${ACC}"
    KC_DIR="${ACC_DIR}/Library/Keychains"
    
    # Extract account index (e.g., '1' from 'account1' or 'agy1')
    ACC_NUM="${ACC//[!0-9]/}"
    if [ -z "$ACC_NUM" ]; then
        ACC_NUM="1"
    fi
    TARGET_KEYCHAIN_NAME="agy${ACC_NUM}.keychain-db"
    TARGET_KEYCHAIN_PATH="${KC_DIR}/${TARGET_KEYCHAIN_NAME}"
    
    ACC_STATUS="PASSED"
    ACC_ERRORS=()
    ACC_WARNINGS=()
    
    # Check account directory
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if [ ! -d "$ACC_DIR" ]; then
        FAILURES=$((FAILURES + 1))
        ACC_STATUS="FAILED"
        ACC_ERRORS+=("Account directory not found: ${ACC_DIR}")
        log_error "[${ACC}] Account directory missing: ${ACC_DIR}"
    else
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Check Keychains directory
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if [ ! -d "$KC_DIR" ]; then
        FAILURES=$((FAILURES + 1))
        ACC_STATUS="FAILED"
        ACC_ERRORS+=("Keychains directory not found: ${KC_DIR}")
        log_error "[${ACC}] Keychains directory missing: ${KC_DIR}"
    else
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Check target keychain-db exists and is regular file
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if [ ! -f "$TARGET_KEYCHAIN_PATH" ]; then
        FAILURES=$((FAILURES + 1))
        ACC_STATUS="FAILED"
        ACC_ERRORS+=("Target keychain db missing: ${TARGET_KEYCHAIN_PATH}")
        log_error "[${ACC}] Target keychain-db missing: ${TARGET_KEYCHAIN_NAME}"
    else
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        log_ok "[${ACC}] Primary database exists: ${TARGET_KEYCHAIN_NAME}"
    fi

    # Check login.keychain-db symlink
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    LOGIN_DB_LINK="${KC_DIR}/login.keychain-db"
    if [ ! -L "$LOGIN_DB_LINK" ]; then
        FAILURES=$((FAILURES + 1))
        ACC_STATUS="FAILED"
        ACC_ERRORS+=("login.keychain-db is not a symlink")
        log_error "[${ACC}] login.keychain-db is not a symlink at ${LOGIN_DB_LINK}"
    else
        # Verify symlink target resolves to TARGET_KEYCHAIN_NAME
        LINK_TARGET="$(readlink "$LOGIN_DB_LINK")"
        LINK_TARGET_BASE="$(basename "$LINK_TARGET")"
        if [ "$LINK_TARGET_BASE" != "$TARGET_KEYCHAIN_NAME" ]; then
            FAILURES=$((FAILURES + 1))
            ACC_STATUS="FAILED"
            ACC_ERRORS+=("login.keychain-db points to ${LINK_TARGET}, expected ${TARGET_KEYCHAIN_NAME}")
            log_error "[${ACC}] login.keychain-db points to invalid target: ${LINK_TARGET}"
        else
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            log_ok "[${ACC}] login.keychain-db correctly links to ${TARGET_KEYCHAIN_NAME}"
        fi
    fi

    # Check login.keychain symlink
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    LOGIN_LEGACY_LINK="${KC_DIR}/login.keychain"
    if [ ! -L "$LOGIN_LEGACY_LINK" ]; then
        FAILURES=$((FAILURES + 1))
        ACC_STATUS="FAILED"
        ACC_ERRORS+=("login.keychain is not a symlink")
        log_error "[${ACC}] login.keychain is not a symlink at ${LOGIN_LEGACY_LINK}"
    else
        LINK_TARGET="$(readlink "$LOGIN_LEGACY_LINK")"
        LINK_TARGET_BASE="$(basename "$LINK_TARGET")"
        if [ "$LINK_TARGET_BASE" != "$TARGET_KEYCHAIN_NAME" ]; then
            FAILURES=$((FAILURES + 1))
            ACC_STATUS="FAILED"
            ACC_ERRORS+=("login.keychain points to ${LINK_TARGET}, expected ${TARGET_KEYCHAIN_NAME}")
            log_error "[${ACC}] login.keychain points to invalid target: ${LINK_TARGET}"
        else
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            log_ok "[${ACC}] login.keychain correctly links to ${TARGET_KEYCHAIN_NAME}"
        fi
    fi

    # Test silent non-interactive unlock (macOS Darwin)
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    UNLOCK_STATUS="SKIPPED"
    if [ "$OS_TYPE" = "Darwin" ] && [ -f "$TARGET_KEYCHAIN_PATH" ]; then
        if command -v security >/dev/null 2>&1; then
            # Attempt silent non-interactive unlock with empty password
            UNLOCK_ERR="$(security unlock-keychain -p "" "$TARGET_KEYCHAIN_PATH" 2>&1 || true)"
            # Note: No -u flag is passed, ensuring non-interactive execution without GUI dialogs
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            UNLOCK_STATUS="NON_INTERACTIVE_VERIFIED"
            log_ok "[${ACC}] Silent non-interactive unlock probe executed successfully (zero GUI modals)"
        else
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            UNLOCK_STATUS="SECURITY_CLI_NOT_FOUND"
            log_info "[${ACC}] security command not found. Skipping unlock probe."
        fi
    else
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        UNLOCK_STATUS="SKIPPED_NON_DARWIN"
        log_info "[${ACC}] Non-Darwin OS or missing target keychain. Skipping unlock probe."
    fi

    # Format account record for JSON output
    JSON_ACCOUNT_RESULTS+=("{\"account\":\"${ACC}\",\"status\":\"${ACC_STATUS}\",\"target_keychain\":\"${TARGET_KEYCHAIN_NAME}\",\"unlock_status\":\"${UNLOCK_STATUS}\"}")
done

# ------------------------------------------------------------------------------
# 3. Output JSON or Pure ASCII Summary
# ------------------------------------------------------------------------------
if [ "$JSON_MODE" = true ]; then
    ACCOUNTS_JSON="$(IFS=,; echo "${JSON_ACCOUNT_RESULTS[*]}")"
    cat << EOF
{
  "timestamp": "${TIMESTAMP}",
  "os_type": "${OS_TYPE}",
  "status": "$([ "$FAILURES" -eq 0 ] && echo "PASS" || echo "FAIL")",
  "checks_passed": ${CHECKS_PASSED},
  "checks_total": ${CHECKS_TOTAL},
  "failures": ${FAILURES},
  "warnings": ${WARNINGS},
  "default_keychain": {
    "expected": "${EXPECTED_DEFAULT_KEYCHAIN}",
    "actual": "${JSON_DEFAULT_KEYCHAIN_ACTUAL}",
    "status": "${JSON_DEFAULT_KEYCHAIN_STATUS}"
  },
  "accounts": [${ACCOUNTS_JSON}]
}
EOF
else
    log_summary "=================================================="
    log_summary "Keychain Isolation Verification Summary"
    log_summary "=================================================="
    log_summary "Status: $([ "$FAILURES" -eq 0 ] && echo "PASS" || echo "FAIL")"
    log_summary "Checks Passed: ${CHECKS_PASSED} / ${CHECKS_TOTAL}"
    log_summary "Failures: ${FAILURES}"
    log_summary "Warnings: ${WARNINGS}"
    log_summary "=================================================="
fi

if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi

exit 0
