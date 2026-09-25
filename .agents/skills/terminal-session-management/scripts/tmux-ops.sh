#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# tmux-ops.sh — Traditional Terminal Multiplexer Wrapper (Fallback)
# Part of: terminal-session-management skill
# Replaces legacy .agy/scripts/tmux-runner.sh with improved session management
# =============================================================================

SCRIPT_NAME="tmux-ops"
ACTION="${1:-help}"
SESSION_NAME="${2:-agy-session}"
PANE_OR_CMD="${3:-}"
MAX_LINES="${4:-30}"

LOG_DIR="/tmp/agy-sessions"
mkdir -p "$LOG_DIR"

# --- Helpers -----------------------------------------------------------------

log_ok()      { echo "[OK] $*"; }
log_error()   { echo "[ERROR] $*" >&2; }
log_warning() { echo "[WARNING] $*"; }
log_info()    { echo "[INFO] $*"; }

timestamp() { date +%Y%m%d-%H%M%S; }

check_tmux() {
  if ! command -v tmux &>/dev/null; then
    log_error "tmux not found. Install: brew install tmux"
    exit 127
  fi
}

session_exists() {
  tmux has-session -t "$1" 2>/dev/null
}

# --- Actions -----------------------------------------------------------------

action_create() {
  local command_str="${PANE_OR_CMD:-bash}"
  check_tmux

  # Generate unique session name with timestamp to prevent collisions
  local unique_name="${SESSION_NAME}-$(timestamp)"
  local log_file="${LOG_DIR}/${unique_name}.log"

  tmux new-session -d -s "$unique_name" \
    "{ $command_str; echo \"[EXIT_CODE=\$?]\"; } 2>&1 | tee '$log_file'" \
    && log_ok "Session created: $unique_name (log: $log_file)" \
    || { log_error "Failed to create session: $unique_name"; exit 1; }

  # Store session name mapping for later retrieval
  echo "$unique_name" > "${LOG_DIR}/${SESSION_NAME}.latest"
  log_info "Latest session pointer: ${LOG_DIR}/${SESSION_NAME}.latest"
}

action_run() {
  # Run a command in a session, wait briefly, and capture output (legacy compat)
  local command_str="${PANE_OR_CMD:-}"
  check_tmux

  if [[ -z "$command_str" ]]; then
    log_error "Usage: $0 run <session-name> <command> [max_lines]"
    exit 1
  fi

  local unique_name="${SESSION_NAME}-$(timestamp)"
  local log_file="${LOG_DIR}/${unique_name}.log"

  # Kill previous session with same base name if exists
  if [[ -f "${LOG_DIR}/${SESSION_NAME}.latest" ]]; then
    local prev_session
    prev_session=$(cat "${LOG_DIR}/${SESSION_NAME}.latest" 2>/dev/null || true)
    if [[ -n "$prev_session" ]] && session_exists "$prev_session"; then
      tmux kill-session -t "$prev_session" 2>/dev/null || true
      log_info "Killed previous session: $prev_session"
    fi
  fi

  tmux new-session -d -s "$unique_name" \
    "{ $command_str; } 2>&1 | tee '$log_file'"

  echo "$unique_name" > "${LOG_DIR}/${SESSION_NAME}.latest"

  # Wait briefly for output
  sleep 2

  # Capture bounded output
  log_info "Executing '$command_str' in session '$unique_name'..."
  tmux capture-pane -pt "$unique_name" 2>/dev/null | tail -n "$MAX_LINES" || true
}

action_status() {
  check_tmux
  if [[ -n "$PANE_OR_CMD" ]]; then
    tmux list-panes -t "$PANE_OR_CMD" -F "#{pane_index}: #{pane_current_command} (#{pane_pid})" 2>/dev/null \
      || log_warning "Session not found: $PANE_OR_CMD"
  else
    tmux list-sessions -F "#{session_name}: #{session_windows} windows, #{session_attached} attached" 2>/dev/null \
      || log_info "No tmux sessions running"
  fi
}

action_read() {
  check_tmux
  if [[ -z "$SESSION_NAME" ]]; then
    log_error "Usage: $0 read <session-name> [window] [max_lines]"
    exit 1
  fi

  # Resolve latest session if pointer exists
  local target="$SESSION_NAME"
  if [[ -f "${LOG_DIR}/${SESSION_NAME}.latest" ]]; then
    target=$(cat "${LOG_DIR}/${SESSION_NAME}.latest" 2>/dev/null || echo "$SESSION_NAME")
  fi

  if session_exists "$target"; then
    tmux capture-pane -pt "$target" 2>/dev/null | tail -n "$MAX_LINES"
    log_info "Output captured: $MAX_LINES lines from $target"
  elif [[ -f "${LOG_DIR}/${target}.log" ]]; then
    tail -n "$MAX_LINES" "${LOG_DIR}/${target}.log"
    log_info "Output from log file: ${LOG_DIR}/${target}.log"
  else
    log_warning "No active session or log found for: $SESSION_NAME"
  fi
}

action_send() {
  local input_text="${4:-}"
  check_tmux
  if [[ -z "$input_text" ]]; then
    log_error "Usage: $0 send <session-name> <window> <input_text>"
    exit 1
  fi

  local target="$SESSION_NAME"
  if [[ -f "${LOG_DIR}/${SESSION_NAME}.latest" ]]; then
    target=$(cat "${LOG_DIR}/${SESSION_NAME}.latest" 2>/dev/null || echo "$SESSION_NAME")
  fi

  tmux send-keys -t "$target" "$input_text" Enter \
    && log_ok "Input sent to $target" \
    || { log_error "Failed to send input to $target"; exit 1; }
}

action_kill() {
  check_tmux
  local target="$SESSION_NAME"
  if [[ -f "${LOG_DIR}/${SESSION_NAME}.latest" ]]; then
    target=$(cat "${LOG_DIR}/${SESSION_NAME}.latest" 2>/dev/null || echo "$SESSION_NAME")
  fi

  tmux kill-session -t "$target" 2>/dev/null \
    && log_ok "Session killed: $target" \
    || log_warning "Session may not exist: $target"

  # Clean up pointer
  rm -f "${LOG_DIR}/${SESSION_NAME}.latest" 2>/dev/null || true
}

action_cleanup() {
  check_tmux
  local count=0
  for pointer_file in "${LOG_DIR}"/*.latest; do
    [[ -f "$pointer_file" ]] || continue
    local session_name
    session_name=$(cat "$pointer_file" 2>/dev/null || true)
    if [[ -n "$session_name" ]] && session_exists "$session_name"; then
      tmux kill-session -t "$session_name" 2>/dev/null || true
      ((count++))
    fi
    rm -f "$pointer_file"
  done
  log_ok "Cleaned up $count sessions and pointer files"
}

# --- Fallback: background process (no tmux) ----------------------------------

action_bg_fallback() {
  local command_str="${PANE_OR_CMD:-}"
  if [[ -z "$command_str" ]]; then
    log_error "Usage: $0 bg <name> <command> [max_lines]"
    exit 1
  fi

  local log_file="${LOG_DIR}/${SESSION_NAME}-$(timestamp).log"
  eval "$command_str" > "$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "${LOG_DIR}/${SESSION_NAME}.pid"

  log_ok "Background process started: PID=$pid (log: $log_file)"
  log_info "Check output: tail -n $MAX_LINES $log_file"
}

# --- Help / Dispatch ---------------------------------------------------------

action_help() {
  cat <<'USAGE'
tmux-ops.sh — Traditional Terminal Multiplexer Wrapper (Fallback)

Usage: tmux-ops.sh <action> <session-name> [command/window] [max_lines]

Actions:
  create <session> [command]          Create detached session
  run <session> <command> [lines]     Run command, wait, capture output
  status [session]                    List sessions or session panes
  read <session> [window] [lines]     Read bounded output
  send <session> <window> <input>     Send input to session
  kill <session>                      Kill session
  cleanup                             Kill all managed sessions
  bg <name> <command> [lines]         Fallback: background process
  help                                Show this help

Defaults: session=agy-session, max_lines=30
Logs: /tmp/agy-sessions/
USAGE
}

case "$ACTION" in
  create)   action_create ;;
  run)      action_run ;;
  status)   action_status ;;
  read)     action_read ;;
  send)     action_send "$@" ;;
  kill)     action_kill ;;
  cleanup)  action_cleanup ;;
  bg)       action_bg_fallback ;;
  help|--help|-h) action_help ;;
  *)
    log_error "Unknown action: $ACTION"
    action_help
    exit 1
    ;;
esac
