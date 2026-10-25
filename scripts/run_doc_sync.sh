#!/bin/bash
# Documentation Sync CI Job Script (M4 - KAN-308 4D)
# Runs on PR, weekly schedule, or workflow_dispatch

set -euo pipefail

echo "=== Documentation Sync (KAN-308 4D) ==="

# Determine run mode
if [[ "${GITHUB_EVENT_NAME}" == "schedule" ]]; then
    MODE="weekly"
    echo "Running weekly documentation sync"
elif [[ "${GITHUB_EVENT_NAME}" == "pull_request" ]]; then
    MODE="pr"
    echo "Running PR documentation sync"
else
    MODE="manual"
    echo "Running manual documentation sync"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e .[test] > /dev/null 2>&1

# Run documentation sync
echo "Running documentation sync..."
python3 scripts/doc_sync.py all --root . --allow-drift --allow-invalid --allow-failed > doc-sync-report.json 2>&1 || true

# Also run drift detection separately for reporting
python3 scripts/doc_sync.py drift --root . > drift-report.json 2>&1 || true

# Display results
echo "=== Drift Detection Results ==="
python3 -c "
import json
with open('drift-report.json') as f:
    data = json.load(f)
print(f\"Issues: {data.get('count', 0)}\")
for issue in data.get('issues', [])[:10]:
    print(f\"  - {issue['type']}: {issue['message']}\")
"

# Post results as PR comment if on PR
if [[ "${MODE}" == "pr" && -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_PR_NUMBER:-}" ]]; then
    echo "Posting documentation sync results as PR comment..."

    python3 -c "
import json
import os

drift_file = 'drift-report.json'
sync_file = 'doc-sync-report.json'

drift_count = 0
drift_issues = []
if os.path.exists(drift_file):
    with open(drift_file) as f:
        data = json.load(f)
    drift_count = data.get('count', 0)
    for issue in data.get('issues', [])[:10]:
        drift_issues.append(f'- **{issue[\"type\"]}**: {issue[\"message\"]}')

lines = [
    '## Documentation Sync Results (KAN-308 4D)',
    '',
    f'**Mode:** {os.environ.get(\"MODE\", \"pr\")}',
    f'**Drift Issues:** {drift_count}',
    '',
    '### Drift Issues Found'
]
if drift_issues:
    lines.extend(drift_issues)
else:
    lines.append('No drift issues found')

lines.append('')
lines.append(f'*Generated at {__import__(\"subprocess\").check_output([\"date\", \"-u\", \"+%Y-%m-%d %H:%M:%S UTC\"]).decode().strip()}*')

with open('doc-sync-comment.txt', 'w') as f:
    f.write('\n'.join(lines))
"

    COMMENT_BODY=$(cat doc-sync-comment.txt | sed ':a;N;s/\n/\\n/g;ta' | sed 's/"/\\"/g')
    gh api repos/${GITHUB_REPOSITORY}/issues/${GITHUB_PR_NUMBER}/comments -f body="${COMMENT_BODY}" || echo "Failed to post comment"
fi

echo "=== Documentation Sync Job Complete ==="