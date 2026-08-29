#!/usr/bin/env bash
set -euo pipefail

# AGY CLI Pre-Tool Guard Hook
# Hard safety boundary: Prevents file modification tools on protected branches (main/master)

TOOL_NAME="${1:-}"
FILE_TARGET="${2:-}"
INPUT_JSON=""

# Read stdin only if arguments are not provided and stdin is piped
if [ -z "$TOOL_NAME" ] && [ ! -t 0 ]; then
  if read -r -t 1 first_line; then
    rest_lines=$(cat || true)
    INPUT_JSON="${first_line}"$'\n'"${rest_lines}"
    if [ -n "$INPUT_JSON" ]; then
      PARSED_TOOL=$(echo "$INPUT_JSON" | grep -o '"name": *"[^"]*"' | head -n1 | cut -d'"' -f4 || echo "")
      if [ -n "$PARSED_TOOL" ]; then
        TOOL_NAME="$PARSED_TOOL"
      fi
    fi
  fi
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "detached")

# Intercept modification tools on protected branches
if [[ "$CURRENT_BRANCH" =~ ^(main|master)$ ]]; then
  if [[ "$TOOL_NAME" =~ ^(Edit|Write|Bash|replace_file_content|write_to_file|run_command|MultiEdit)$ ]]; then
    printf "\033[0;31m[AGY GUARD] ABORTED: Direct modifications to '%s' are forbidden.\033[0m\n" "$CURRENT_BRANCH" >&2
    printf "\033[0;33mAction: Create a dedicated feature branch first: git checkout -b feat/<name>\033[0m\n" >&2
    # Output AGY JSON decision if running inside AGY hook lifecycle
    if [ -n "${INPUT_JSON:-}" ]; then
      printf '{"decision": "deny", "reason": "Direct modifications to protected branch (%s) are forbidden. Checkout a feature branch first."}\n' "$CURRENT_BRANCH"
    fi
    exit 2
  fi
fi

# Allow execution
if [ -n "${INPUT_JSON:-}" ]; then
  printf '{"decision": "allow"}\n'
fi
exit 0
