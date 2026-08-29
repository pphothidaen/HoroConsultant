#!/usr/bin/env bash
# Warn on an optional launcher-provided context percentage; never alters state.
set -euo pipefail

usage_percent="${CLAUDE_CONTEXT_USAGE_PERCENT:-${CODEX_CONTEXT_USAGE_PERCENT:-}}"
if [[ -z "$usage_percent" ]]; then
  exit 0
fi

if [[ "$usage_percent" =~ ^[0-9]+$ ]] && (( usage_percent >= 80 )); then
  printf '[WARNING] Context usage is %s%%. Document progress in HANDOFF.md, then use /clear before continuing.\n' "$usage_percent" >&2
fi
