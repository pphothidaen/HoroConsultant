#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# herdr-ops.sh — Agent-Native Terminal Session Manager (Primary)
# Part of: terminal-session-management skill
# Requires: herdr (https://herdr.dev) installed via `brew install herdr`
# =============================================================================

SCRIPT_NAME="herdr-ops"
ACTION="${1:-help}"
WORKSPACE="${2:-horoconsultant}"
PANE_NAME="${3:-}"
MAX_LINES="${4:-30}"

# --- Helpers -----------------------------------------------------------------

log_ok()      { echo "[OK] $*"; }
log_error()   { echo "[ERROR] $*" >&2; }
log_warning() { echo "[WARNING] $*"; }
log_info()    { echo "[INFO] $*"; }

check_herdr() {
  if ! command -v herdr &>/dev/null; then
    log_error "herdr not found. Install: brew install herdr"
    log_info "Falling back to tmux-ops.sh"
    exit 127
  fi
}

# --- Actions -----------------------------------------------------------------

action_create_workspace() {
  local project_path="${3:-$(pwd)}"
  check_herdr
  herdr workspace create "$WORKSPACE" --path "$project_path" 2>/dev/null \
    && log_ok "Workspace created: $WORKSPACE (path: $project_path)" \
    || log_warning "Workspace '$WORKSPACE' may already exist"
}

action_create_pane() {
  local command_str="${5:-bash}"
  check_herdr
  if [[ -z "$PANE_NAME" ]]; then
    log_error "Pane name required. Usage: $0 create-pane <workspace> <pane-name> [max_lines] [command]"
    exit 1
  fi
  herdr pane create --workspace "$WORKSPACE" --name "$PANE_NAME" -- $command_str \
    && log_ok "Pane created: $WORKSPACE/$PANE_NAME (cmd: $command_str)" \
    || { log_error "Failed to create pane: $WORKSPACE/$PANE_NAME"; exit 1; }
}

action_status() {
  check_herdr
  if [[ -n "$PANE_NAME" ]]; then
    herdr status --workspace "$WORKSPACE" 2>/dev/null | grep -i "$PANE_NAME" || true
  else
    herdr status 2>/dev/null
  fi
  log_ok "Status retrieved for workspace: $WORKSPACE"
}

action_read_output() {
  check_herdr
  if [[ -z "$PANE_NAME" ]]; then
    log_error "Pane name required. Usage: $0 read <workspace> <pane-name> [max_lines]"
    exit 1
  fi
  herdr pane read --workspace "$WORKSPACE" --name "$PANE_NAME" --lines "$MAX_LINES" 2>/dev/null \
    || { log_warning "Could not read pane output: $WORKSPACE/$PANE_NAME"; }
  log_info "Output captured: $MAX_LINES lines from $WORKSPACE/$PANE_NAME"
}

action_send_input() {
  local input_text="${5:-}"
  check_herdr
  if [[ -z "$PANE_NAME" || -z "$input_text" ]]; then
    log_error "Usage: $0 send <workspace> <pane-name> <max_lines> <input_text>"
    exit 1
  fi
  herdr pane send --workspace "$WORKSPACE" --name "$PANE_NAME" "$input_text" \
    && log_ok "Input sent to $WORKSPACE/$PANE_NAME" \
    || { log_error "Failed to send input to $WORKSPACE/$PANE_NAME"; exit 1; }
}

action_kill_pane() {
  check_herdr
  if [[ -z "$PANE_NAME" ]]; then
    log_error "Pane name required. Usage: $0 kill-pane <workspace> <pane-name>"
    exit 1
  fi
  herdr pane kill --workspace "$WORKSPACE" --name "$PANE_NAME" 2>/dev/null \
    && log_ok "Pane killed: $WORKSPACE/$PANE_NAME" \
    || log_warning "Pane may not exist: $WORKSPACE/$PANE_NAME"
}

action_delete_workspace() {
  check_herdr
  herdr workspace delete "$WORKSPACE" 2>/dev/null \
    && log_ok "Workspace deleted: $WORKSPACE" \
    || log_warning "Workspace may not exist: $WORKSPACE"
}

action_setup_6lane() {
  local project_path="${3:-$(pwd)}"
  check_herdr

  log_info "Setting up 6-lane architecture for: $WORKSPACE"

  # Create workspace
  herdr workspace create "$WORKSPACE" --path "$project_path" 2>/dev/null || true

  # Management Tier (3 lanes)
  herdr pane create --workspace "$WORKSPACE" --name "mgmt-lead-ba"   -- bash 2>/dev/null || true
  herdr pane create --workspace "$WORKSPACE" --name "mgmt-intake"    -- bash 2>/dev/null || true
  herdr pane create --workspace "$WORKSPACE" --name "mgmt-auditor"   -- bash 2>/dev/null || true

  # Execution Tier (3 lanes)
  herdr pane create --workspace "$WORKSPACE" --name "exec-dev-api"   -- bash 2>/dev/null || true
  herdr pane create --workspace "$WORKSPACE" --name "exec-dev-core"  -- bash 2>/dev/null || true
  herdr pane create --workspace "$WORKSPACE" --name "exec-qa"        -- bash 2>/dev/null || true

  log_ok "6-lane workspace ready: $WORKSPACE (6 panes created)"
  herdr status --workspace "$WORKSPACE" 2>/dev/null || true
}

action_teardown() {
  check_herdr
  log_info "Tearing down workspace: $WORKSPACE"
  herdr workspace delete "$WORKSPACE" --force 2>/dev/null \
    && log_ok "Workspace teardown complete: $WORKSPACE" \
    || log_warning "Workspace may not exist: $WORKSPACE"
}

# --- Help / Dispatch ---------------------------------------------------------

action_help() {
  cat <<'USAGE'
herdr-ops.sh — Agent-Native Terminal Session Manager

Usage: herdr-ops.sh <action> <workspace> [pane-name] [max_lines] [extra]

Actions:
  create-workspace <workspace> [project-path]    Create a herdr workspace
  create-pane <workspace> <pane> [lines] [cmd]   Create a pane in workspace
  status [workspace] [pane]                       Show agent status
  read <workspace> <pane> [max_lines]             Read bounded output
  send <workspace> <pane> <lines> <input>         Send input to pane
  kill-pane <workspace> <pane>                    Kill a single pane
  delete-workspace <workspace>                    Delete entire workspace
  setup-6lane <workspace> [project-path]          Create full 6-lane workspace
  teardown <workspace>                            Force-delete workspace
  help                                            Show this help

Defaults: workspace=horoconsultant, max_lines=30
USAGE
}

case "$ACTION" in
  create-workspace)  action_create_workspace "$@" ;;
  create-pane)       action_create_pane "$@" ;;
  status)            action_status ;;
  read)              action_read_output ;;
  send)              action_send_input "$@" ;;
  kill-pane)         action_kill_pane ;;
  delete-workspace)  action_delete_workspace ;;
  setup-6lane)       action_setup_6lane "$@" ;;
  teardown)          action_teardown ;;
  help|--help|-h)    action_help ;;
  *)
    log_error "Unknown action: $ACTION"
    action_help
    exit 1
    ;;
esac
