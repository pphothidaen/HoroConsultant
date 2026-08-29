#!/usr/bin/env bash
set -euo pipefail

# AGY CLI Post-Tool Lifecycle Hook
# Targeted Fast Formatting, Hygiene & Auto-Parity Trigger strictly on touched files

MODIFIED_FILE="${1:-}"
INPUT_JSON=""

# Read stdin only if argument not provided and stdin is piped
if [ -z "$MODIFIED_FILE" ] && [ ! -t 0 ]; then
  if read -r -t 1 first_line; then
    rest_lines=$(cat || true)
    INPUT_JSON="${first_line}"$'\n'"${rest_lines}"
    if [ -n "$INPUT_JSON" ]; then
      PARSED_FILE=$(echo "$INPUT_JSON" | grep -o '"TargetFile": *"[^"]*"' | head -n1 | cut -d'"' -f4 || echo "")
      if [ -n "$PARSED_FILE" ]; then
        MODIFIED_FILE="$PARSED_FILE"
      fi
    fi
  fi
fi

if [[ -z "$MODIFIED_FILE" || ! -f "$MODIFIED_FILE" ]]; then
  if [ -n "${INPUT_JSON:-}" ]; then
    printf '{}\n'
  fi
  exit 0
fi

# Auto-Trigger Parity Synchronization if agent ecosystem files are touched
case "$MODIFIED_FILE" in
  *.claude*|*.agy*|*rules/*|*skills/*|*agents/*|*CLAUDE.md|*AGY.md|*.claudeignore|*.agyignore)
    if command -v python3 &>/dev/null && [ -f "scripts/sync_claude_agy_parity.py" ]; then
      python3 scripts/sync_claude_agy_parity.py --sync >/dev/null 2>&1 || true
    fi
    ;;
esac

# Apply lightweight formatter based on file extension
case "$MODIFIED_FILE" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.html)
    if command -v prettier &>/dev/null; then
      prettier --write "$MODIFIED_FILE" 2>/dev/null || true
    elif command -v npx &>/dev/null; then
      npx prettier --write "$MODIFIED_FILE" 2>/dev/null || true
    fi
    ;;
  *.py)
    if command -v ruff &>/dev/null; then
      ruff format --quiet "$MODIFIED_FILE" 2>/dev/null || true
    elif command -v black &>/dev/null; then
      black --quiet "$MODIFIED_FILE" 2>/dev/null || true
    fi
    ;;
  *.go)
    if command -v gofmt &>/dev/null; then
      gofmt -w "$MODIFIED_FILE" 2>/dev/null || true
    fi
    ;;
  *.rs)
    if command -v rustfmt &>/dev/null; then
      rustfmt --quiet "$MODIFIED_FILE" 2>/dev/null || true
    fi
    ;;
esac

if [ -n "${INPUT_JSON:-}" ]; then
  printf '{}\n'
fi
exit 0
