#!/usr/bin/env bash
# AGY adapter for atomic TDD lifecycle governance
# Transforms AGY event format to core format, runs the canonical guard,
# then transforms output (reason_code -> reason) and exits appropriately.

set -uo pipefail

# Parse arguments
REPO=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)
            REPO="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [[ -z "$REPO" ]]; then
    echo '{"decision":"deny","reason":"MISSING_REPO_ARGUMENT"}' >&2
    exit 1
fi

# Read stdin (event JSON)
EVENT=$(cat)

# Transform AGY event format to core format
# AGY format: {"toolCall": {"name": "...", "args": {...}}, "repo": "..."}
# Core format: {"hook_event_name": "PreToolUse", "tool_name": "...", "tool_input": {...}, ...}
TRANSFORMED=$(echo "$EVENT" | python3 -c "
import json, sys
agy = json.load(sys.stdin)
tool_call = agy.get('toolCall', {})
args = tool_call.get('args', {})
event = {
    'hook_event_name': 'PreToolUse',
    'tool_name': tool_call.get('name', ''),
    'tool_input': {'file_path': args.get('file_path', '')},
    'ticket_id': args.get('ticket_id', ''),
    'baseline_verified': args.get('baseline_verified', False),
    'review_pass': args.get('review_pass', False),
    'qa_pass': args.get('qa_pass', False),
    'repo': '$REPO',
}
# Pass through optional fields
for key in ('lane_id', 'orchestrator_effort', 'model', 'ambiguity_detected'):
    if key in args:
        event[key] = args[key]
    if key in agy:
        event[key] = agy[key]
print(json.dumps(event))
")

# Run the canonical guard with core adapter and capture output + exit code
GUARD_OUTPUT_FILE=$(mktemp)
echo "$TRANSFORMED" | python3 .agents/hooks/atomic_tdd_guard.py --repo "$REPO" --adapter core > "$GUARD_OUTPUT_FILE" 2>/dev/null
GUARD_EXIT=$?
RESULT=$(cat "$GUARD_OUTPUT_FILE")
rm -f "$GUARD_OUTPUT_FILE"

# Transform output: reason_code -> reason
OUTPUT=$(echo "$RESULT" | python3 -c "
import json, sys
result = json.load(sys.stdin)
output = {
    'decision': result.get('decision', 'deny'),
    'reason': result.get('reason_code', 'UNKNOWN'),
}
print(json.dumps(output))
")

echo "$OUTPUT"

# Exit with code 2 on deny, 0 on allow
DECISION=$(echo "$OUTPUT" | python3 -c "import json, sys; print(json.load(sys.stdin).get('decision', 'deny'))")
if [[ "$DECISION" == "deny" ]]; then
    exit 2
fi
exit 0