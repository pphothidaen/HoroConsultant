#!/bin/bash
# Test Maintenance CI Job Script (M3 - KAN-308 4C)
# Runs on PR, weekly schedule, or workflow_dispatch

set -euo pipefail

echo "=== Test Maintenance (KAN-308 4C) ==="

# Determine run mode
if [[ "${GITHUB_EVENT_NAME}" == "schedule" ]]; then
    MODE="weekly"
    echo "Running weekly test maintenance"
elif [[ "${GITHUB_EVENT_NAME}" == "pull_request" ]]; then
    MODE="pr"
    echo "Running PR test maintenance"
else
    MODE="manual"
    echo "Running manual test maintenance"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e .[test] > /dev/null 2>&1
pip install pytest-cov > /dev/null 2>&1

# Run all maintenance tasks
echo "Running test maintenance..."
python3 scripts/test_maintenance.py all \
    --path tests \
    --output tests/generated \
    --update-baseline \
    --force

# Check results
if [[ -f ".hermes/flaky_history.json" ]]; then
    FLAKY_COUNT=$(python3 -c "
import json
with open('.hermes/flaky_history.json') as f:
    data = json.load(f)
flaky = [t for t in data.get('tests', {}).values() if t.get('quarantined', False)]
print(len(flaky))
")
    echo "Quarantined tests: ${FLAKY_COUNT}"
fi

if [[ -f ".hermes/coverage_baseline.json" ]]; then
    BASELINE=$(python3 -c "
import json
with open('.hermes/coverage_baseline.json') as f:
    data = json.load(f)
print(data.get('total', 0))
")
    echo "Coverage baseline: ${BASELINE}%"
fi

# Post results as PR comment if on PR
if [[ "${MODE}" == "pr" && -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_PR_NUMBER:-}" ]]; then
    echo "Posting test maintenance results as PR comment..."

    python3 -c "
import json
import os

flaky_file = '.hermes/flaky_history.json'
cov_file = '.hermes/coverage_baseline.json'

flaky_count = 0
flaky_tests = []
if os.path.exists(flaky_file):
    with open(flaky_file) as f:
        data = json.load(f)
    for name, stats in data.get('tests', {}).items():
        if stats.get('quarantined', False):
            flaky_count += 1
            flaky_tests.append(f'- **{name}**: {stats[\"consecutive_failures\"]} consecutive failures')

baseline_cov = 0
if os.path.exists(cov_file):
    with open(cov_file) as f:
        data = json.load(f)
    baseline_cov = data.get('total', 0)

lines = [
    '## Test Maintenance Results (KAN-308 4C)',
    '',
    f'**Mode:** {os.environ.get(\"MODE\", \"pr\")}',
    f'**Coverage Baseline:** {baseline_cov:.1f}%',
    f'**Quarantined Tests:** {flaky_count}',
    '',
    '### Quarantined Tests'
]
if flaky_tests:
    lines.extend(flaky_tests)
else:
    lines.append('No quarantined tests')

lines.append('')
lines.append(f'*Generated at {__import__(\"subprocess\").check_output([\"date\", \"-u\", \"+%Y-%m-%d %H:%M:%S UTC\"]).decode().strip()}*')

with open('maintenance-comment.txt', 'w') as f:
    f.write('\n'.join(lines))
"

    COMMENT_BODY=$(cat maintenance-comment.txt | sed ':a;N;s/\n/\\n/g;ta' | sed 's/"/\\"/g')
    gh api repos/${GITHUB_REPOSITORY}/issues/${GITHUB_PR_NUMBER}/comments -f body="${COMMENT_BODY}" || echo "Failed to post comment"
fi

echo "=== Test Maintenance Job Complete ==="