#!/bin/bash
# Post refactoring suggestions as PR comment for KAN-307

set -euo pipefail

PR_NUMBER="${1:-${GITHUB_PR_NUMBER}}"
if [ -z "$PR_NUMBER" ]; then
    echo "PR number not provided"
    exit 1
fi

# Combine refactoring and auto-fix comments
{
    echo "## AI Refactoring Suggestions (KAN-307)"
    echo ""
    cat ai-refactor-comment.txt 2>/dev/null || echo "No refactoring suggestions available"
    echo ""
    echo "---"
    echo ""
    echo "## Auto-Fix Dry Run Results"
    echo ""
    cat auto-fix-comment.txt 2>/dev/null || echo "No auto-fix results available"
} > combined-refactor-comment.txt

# Escape for GH API
COMMENT=$(cat combined-refactor-comment.txt)
# Simple escaping - replace special chars
COMMENT_ESCAPED=$(printf '%s' "$COMMENT" | sed ':a;N;$!ba;s/%/%25/g;s/\n/%0A/g;s/\r/%0D/g')

gh api repos/${GITHUB_REPOSITORY}/issues/$PR_NUMBER/comments -f body="$COMMENT_ESCAPED"