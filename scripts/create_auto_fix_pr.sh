#!/bin/bash
# Auto-fix PR creator script for KAN-307
# Called from CI workflow

set -euo pipefail

FIXES_COUNT=$(jq -r '.files_changed // 0' auto-fix-result.json)
if [ "$FIXES_COUNT" -eq 0 ]; then
    echo "No auto-fixes needed"
    exit 0
fi

echo "Auto-fix found $FIXES_COUNT files with changes. Creating fix branch..."

# Create fix branch
FIX_BRANCH="fix/auto-$(date +%s)"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git checkout -b "$FIX_BRANCH"

# Apply fixes
python3 scripts/auto_fix.py --dir . --apply

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m $'Auto-fix: formatting and import fixes (KAN-307)\n\nAuto-applied safe fixes from auto-fix engine:\n- Black formatting\n- isort import sorting\n- Whitespace cleanup\n\nThis is an automated fix PR for review.'

    git push origin "$FIX_BRANCH"

    # Create PR
    gh pr create --base "${GITHUB_BASE_REF}" --head "$FIX_BRANCH" \
        --title "Auto-fix: Formatting and import fixes" \
        --body $'Automated fixes from KAN-307 auto-fix engine (dry-run found '$FIXES_COUNT' files with changes).\n\n## Changes Applied\n- Black formatting\n- isort import sorting  \n- Whitespace cleanup\n\nPlease review and merge if changes look correct.'
else
    echo "No changes after applying fixes"
fi