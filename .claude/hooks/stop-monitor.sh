#!/usr/bin/env bash
set -euo pipefail
python3 "$(git rev-parse --show-toplevel)/scripts/context_handoff.py" hook --runtime claude --event Stop --native --state-file "${CONTEXT_HANDOFF_STATE_FILE:-}"
