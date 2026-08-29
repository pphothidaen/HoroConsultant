#!/usr/bin/env bash
set -euo pipefail

# AGY CLI Background tmux & Subshell Runner
# Executes verbose commands in isolation to prevent agent context pollution

COMMAND="${1:-}"
SESSION_NAME="${2:-agy-bg-task}"
MAX_LINES="${3:-30}"

if [[ -z "$COMMAND" ]]; then
  echo "Usage: $0 \"<command>\" [session_name] [max_lines]"
  exit 1
fi

# Check if tmux is available
if command -v tmux &>/dev/null; then
  # Kill previous session if exists
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  
  # Start detached session
  tmux new-session -d -s "$SESSION_NAME" "$COMMAND"
  
  # Wait briefly for execution or completion
  sleep 1
  
  # Capture output pane
  echo "[TMUX RUNNER] Executing '$COMMAND' in session '$SESSION_NAME'..."
  tmux capture-pane -pt "$SESSION_NAME" 2>/dev/null | tail -n "$MAX_LINES" || true
else
  # Fallback to background process redirection
  LOG_FILE="/tmp/${SESSION_NAME}.log"
  eval "$COMMAND" > "$LOG_FILE" 2>&1 &
  PID=$!
  wait $PID 2>/dev/null || true
  tail -n "$MAX_LINES" "$LOG_FILE"
fi
