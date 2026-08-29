#!/usr/bin/env bash
# Block application-file mutations from Claude Code while on a protected branch.
set -euo pipefail

root_dir="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
branch="$(git -C "$root_dir" branch --show-current 2>/dev/null || true)"
event="$(cat)"

if [[ "$branch" != "main" && "$branch" != "master" ]]; then
  exit 0
fi

if python3 -c '
import json, re, sys

event = json.load(sys.stdin)
tool = str(event.get("tool_name", ""))
payload = event.get("tool_input", {})
app_path = re.compile(r"(^|/)(project|src|app|backend|frontend|scripts)/|^(pyproject\.toml|package\.json)$")
mutation = re.compile(r"(^|[;|&\s])(apply_patch|tee|touch|mkdir|rm|mv|cp|install)\b|\b(sed|perl)\s+-\S*i|>|git\s+(add|commit|reset|restore|checkout|clean)\b")

def paths(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [part for item in value for part in paths(item)]
    if isinstance(value, dict):
        return [part for key in ("file_path", "path", "notebook_path") for part in paths(value.get(key))]
    return []

if tool in {"Edit", "Write", "MultiEdit"} and any(app_path.search(path.lstrip("./")) for path in paths(payload)):
    sys.exit(2)
if tool == "Bash":
    command = str(payload.get("command", ""))
    if mutation.search(command) and app_path.search(command):
        sys.exit(2)
' <<<"$event"; then
  exit 0
fi

printf '\033[31m[BLOCKED] Protected branch %s: create a feature branch before modifying application files.\033[0m\n' "$branch" >&2
exit 2
