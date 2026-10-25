#!/bin/bash
# Security Scan CI Job Script (M1/M2 - KAN-308 4B)
# Runs on PR, weekly schedule, or workflow_dispatch

set -euo pipefail

echo "=== Security Scan (KAN-308 4B) ==="

# Determine run mode
if [[ "${GITHUB_EVENT_NAME}" == "schedule" ]]; then
    MODE="weekly"
    echo "Running weekly security scan"
elif [[ "${GITHUB_EVENT_NAME}" == "pull_request" ]]; then
    MODE="pr"
    echo "Running PR security scan"
else
    MODE="manual"
    echo "Running manual security scan"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e .[test] > /dev/null 2>&1

# Run SAST scan
echo "Running SAST scan (gitleaks + Semgrep)..."
python3 scripts/sast_scan.py scan --output sast-result.json --format sarif > /dev/null 2>&1 || true

# Run dependency scan
echo "Running dependency vulnerability scan (OSV)..."
python3 scripts/dependency_scan.py scan --output dependency-result.json > /dev/null 2>&1 || true

# Combine results for PR comment
echo "Generating security scan summary..."

python3 -c "
import json
import os

sast_file = 'sast-result.json'
dep_file = 'dependency-result.json'

sast_findings = 0
dep_findings = 0
critical_count = 0
high_count = 0

if os.path.exists(sast_file):
    with open(sast_file) as f:
        sast_data = json.load(f)
    if 'runs' in sast_data:
        for run in sast_data['runs']:
            if 'results' in run:
                sast_findings += len(run['results'])
                for result in run['results']:
                    level = result.get('level', 'note')
                    if level == 'error':
                        critical_count += 1
                    elif level == 'warning':
                        high_count += 1

if os.path.exists(dep_file):
    with open(dep_file) as f:
        dep_data = json.load(f)
    if 'vulnerabilities' in dep_data:
        dep_findings = len(dep_data['vulnerabilities'])
        for vuln in dep_data['vulnerabilities']:
            severity = vuln.get('severity', '').lower()
            if severity == 'critical':
                critical_count += 1
            elif severity == 'high':
                high_count += 1

lines = [
    '## Security Scan Results (KAN-308 4B)',
    '',
    f'**Mode:** {os.environ.get(\"MODE\", \"pr\")}',
    f'**SAST Findings:** {sast_findings}',
    f'**Dependency Vulnerabilities:** {dep_findings}',
    f'**Critical:** {critical_count}',
    f'**High:** {high_count}',
    ''
]

# Add top SAST findings
if os.path.exists(sast_file):
    with open(sast_file) as f:
        sast_data = json.load(f)
    lines.append('### Top SAST Findings')
    count = 0
    if 'runs' in sast_data:
        for run in sast_data['runs']:
            if 'results' in run:
                for result in run['results'][:5]:
                    rule_id = result.get('ruleId', 'unknown')
                    msg = result.get('message', {}).get('text', 'No message')
                    level = result.get('level', 'note')
                    lines.append(f'- **[{level.upper()}]** {rule_id}: {msg}')
                    count += 1
                    if count >= 5:
                        break
                if count >= 5:
                    break

# Add top dependency vulnerabilities
if os.path.exists(dep_file):
    with open(dep_file) as f:
        dep_data = json.load(f)
    lines.append('')
    lines.append('### Top Dependency Vulnerabilities')
    count = 0
    if 'vulnerabilities' in dep_data:
        for vuln in dep_data['vulnerabilities'][:5]:
            pkg = vuln.get('package', 'unknown')
            severity = vuln.get('severity', 'unknown')
            vuln_id = vuln.get('id', 'unknown')
            lines.append(f'- **[{severity.upper()}]** {pkg}: {vuln_id}')
            count += 1
            if count >= 5:
                break

lines.append('')
lines.append(f'*Generated at {__import__(\"subprocess\").check_output([\"date\", \"-u\", \"+%Y-%m-%d %H:%M:%S UTC\"]).decode().strip()}*')

with open('security-comment.txt', 'w') as f:
    f.write('\n'.join(lines))
"

# Post results as PR comment if on PR
if [[ "${MODE}" == "pr" && -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_PR_NUMBER:-}" ]]; then
    echo "Posting security scan results as PR comment..."
    COMMENT_BODY=$(cat security-comment.txt | sed ':a;N;s/\n/\\n/g;ta' | sed 's/"/\\"/g')
    gh api repos/${GITHUB_REPOSITORY}/issues/${GITHUB_PR_NUMBER}/comments -f body="${COMMENT_BODY}" || echo "Failed to post comment"
fi

# Check for critical findings
if [[ ${critical_count:-0} -gt 0 ]]; then
    echo "⚠️  CRITICAL SECURITY FINDINGS DETECTED!"
    exit 1
fi

echo "=== Security Scan Job Complete ==="