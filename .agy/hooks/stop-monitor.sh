#!/usr/bin/env bash
set -euo pipefail

# AGY CLI Stop Monitor & Anti-Cognitive Decay Guard
# Detects context accumulation > 45% threshold and alerts operator for Snapshot & Clear

THRESHOLD_KB=450 # ~45% context budget indicator for transcript accumulation

INPUT_JSON=""
TRANSCRIPT_PATH="${1:-}"

# Read stdin only if argument not provided and stdin is piped
if [ -z "$TRANSCRIPT_PATH" ] && [ ! -t 0 ]; then
  if read -r -t 1 first_line; then
    rest_lines=$(cat || true)
    INPUT_JSON="${first_line}"$'\n'"${rest_lines}"
    if [ -n "$INPUT_JSON" ]; then
      TRANSCRIPT_PATH=$(echo "$INPUT_JSON" | grep -o '"transcriptPath": *"[^"]*"' | head -n1 | cut -d'"' -f4 || echo "")
    fi
  fi
fi

# Check transcript size if path found
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  SIZE_KB=$(du -k "$TRANSCRIPT_PATH" | cut -f1)
  if [ "$SIZE_KB" -gt "$THRESHOLD_KB" ]; then
    printf "\033[0;33m[AGY MONITOR] Context accumulation warning: Transcript is %d KB (>45%% threshold).\033[0m\n" "$SIZE_KB" >&2
    printf "\033[0;33mAction: Run /handoff and execute /clear to prevent cognitive decay.\033[0m\n" >&2
    if [ -n "$INPUT_JSON" ]; then
      printf '{"decision": "continue", "reason": "Context consumption has crossed 45%% threshold. Please generate HANDOFF.md and reset session context."}\n'
      exit 0
    fi
  fi
fi

if [ -n "$INPUT_JSON" ]; then
  printf '{"decision": "stop"}\n'
fi
exit 0
