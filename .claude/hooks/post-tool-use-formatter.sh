#!/usr/bin/env bash
# Read-only, targeted post-edit lint & auto-parity synchronization trigger.
set -euo pipefail

event="$(cat)"
while IFS= read -r file; do
  [[ -n "$file" && -f "$file" ]] || continue

  # Auto-Trigger Parity Synchronization if agent ecosystem files are touched
  case "$file" in
    *.claude*|*.agy*|*rules/*|*skills/*|*agents/*|*CLAUDE.md|*AGY.md|*.claudeignore|*.agyignore)
      if command -v python3 &>/dev/null && [ -f "scripts/sync_claude_agy_parity.py" ]; then
        python3 scripts/sync_claude_agy_parity.py --sync >/dev/null 2>&1 || true
      fi
      ;;
  esac

  if [[ "$file" == *.py ]]; then
    if ! ruff check --isolated "$file" 2>/dev/null; then
      printf '[WARNING] Targeted lint reported findings in %s; local hooks do not modify files.\n' "$file" >&2
    fi
  fi
done < <(python3 -c '
import json, sys

event = json.load(sys.stdin)
payload = event.get("tool_input", {})

def paths(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [path for item in value for path in paths(item)]
    if isinstance(value, dict):
        return [path for key in ("file_path", "path", "notebook_path", "TargetFile") for path in paths(value.get(key))]
    return []

for path in dict.fromkeys(paths(payload)):
    print(path)
' <<<"$event")
