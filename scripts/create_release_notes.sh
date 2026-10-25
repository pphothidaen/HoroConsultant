#!/bin/bash
# Release Notes CI Job Script (M2 - KAN-308 4A)
# Runs on push to main or tag push

set -euo pipefail

echo "=== Release Notes Automation (KAN-308 4A) ==="

# Determine trigger
if [[ "${GITHUB_EVENT_NAME}" == "push" && "${GITHUB_REF}" == "refs/heads/main" ]]; then
    MODE="main_merge"
    echo "Running on merge to main"
elif [[ "${GITHUB_EVENT_NAME}" == "push" && "${GITHUB_REF}" =~ ^refs/tags/ ]]; then
    MODE="tag_push"
    echo "Running on tag push: ${GITHUB_REF}"
elif [[ "${GITHUB_EVENT_NAME}" == "workflow_dispatch" ]]; then
    MODE="manual"
    echo "Running manual release notes generation"
else
    MODE="unknown"
    echo "Unknown trigger: ${GITHUB_EVENT_NAME} ${GITHUB_REF}"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -e .[test] > /dev/null 2>&1

# Generate release notes
echo "Generating release notes..."
python3 scripts/release_notes.py generate \
    --from-tag $(git describe --tags --abbrev=0 2>/dev/null || echo "") \
    --to-tag HEAD \
    --output RELEASE_NOTES.md \
    --format markdown

# Update CHANGELOG.md
echo "Updating CHANGELOG.md..."
python3 scripts/release_notes.py changelog \
    --release-notes RELEASE_NOTES.md \
    --changelog CHANGELOG.md

# Create GitHub Release (draft)
if [[ "${MODE}" == "tag_push" && -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" ]]; then
    echo "Creating GitHub Release..."
    TAG_NAME="${GITHUB_REF#refs/tags/}"
    RELEASE_BODY=$(cat RELEASE_NOTES.md | sed ':a;N;s/\n/\\n/g;ta' | sed 's/"/\\"/g')
    
    gh api repos/${GITHUB_REPOSITORY}/releases \
        -f tag_name="${TAG_NAME}" \
        -f name="Release ${TAG_NAME}" \
        -f body="${RELEASE_BODY}" \
        -f draft=true \
        -f prerelease=false || echo "Failed to create release (may already exist)"
fi

# Post as PR comment if on PR (for manual trigger on PR)
if [[ "${GITHUB_EVENT_NAME}" == "pull_request" && -n "${GITHUB_TOKEN:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_PR_NUMBER:-}" ]]; then
    echo "Posting release notes preview as PR comment..."
    RELEASE_BODY=$(cat RELEASE_NOTES.md | sed ':a;N;s/\n/\\n/g;ta' | sed 's/"/\\"/g')
    gh api repos/${GITHUB_REPOSITORY}/issues/${GITHUB_PR_NUMBER}/comments -f body="${RELEASE_BODY}" || echo "Failed to post comment"
fi

echo "=== Release Notes Job Complete ==="