#!/usr/bin/env bash
# local_ci.sh — Run CI-equivalent tests for the current commit/PR locally.
# Targets the same TIER_LITE/MEDIUM/STRICT split as .github/workflows/ci.yml.
#
# Usage:
#   scripts/local_ci.sh                          # Auto-detect mode
#   scripts/local_ci.sh --base origin/main        # PR diff vs base
#   scripts/local_ci.sh --files f1.py f2.py ...    # Explicit file list
#   scripts/local_ci.sh --only targeted           # Only targeted tests (TIER_MEDIUM)
#   scripts/local_ci.sh --full                    # Force full suite regardless of tier

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

ONLY_TARGETED=0
FULL=0
EXTRA_ARGS=()
BASE=""
HEAD=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --only-targeted)
      ONLY_TARGETED=1
      shift
      ;;
    --full)
      FULL=1
      shift
      ;;
    --base)
      BASE="$2"
      shift 2
      ;;
    --head)
      HEAD="$2"
      shift 2
      ;;
    --files)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

# Resolve file list
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  FILES=("${EXTRA_ARGS[@]}")
elif [[ -n "$BASE" ]]; then
  if [[ -z "$HEAD" ]]; then
    HEAD="HEAD"
  fi
  IFS=$'\n' read -r -d '' -a FILES < <(git diff --name-only "${BASE}...${HEAD}" && printf '\0')
else
  # Default: diff against origin/main or HEAD if no upstream
  if git rev-parse origin/main &>/dev/null; then
    IFS=$'\n' read -r -d '' -a FILES < <(git diff --name-only origin/main...HEAD && printf '\0')
  else
    IFS=$'\n' read -r -d '' -a FILES < <(git diff --name-only HEAD && printf '\0')
  fi
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No changed files detected. Nothing to test."
  exit 0
fi

echo "Changed files: ${#FILES[@]}"
for f in "${FILES[@]}"; do
  echo "  $f"
done
echo ""

# Run classifier (JSON for reliable parsing)
JSON_OUT=$(python3 scripts/path_ruleset_classifier.py --files "${FILES[@]}" --show-affected-tests --json)
echo "$JSON_OUT" | python3 -m json.tool
echo ""

TIER=$(echo "$JSON_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier'])")

case "$TIER" in
  LIGHT)
    echo "⚡ TIER_LIGHT: Skipping PyTest. Running security + provenance only."
    echo "  Commands to run manually:"
    echo "    python3 scripts/test_provenance_guard.py --files ..."
    ;;
  MEDIUM)
    echo "🎯 TIER_MEDIUM: Running targeted tests only."

    # Extract resolved test files from JSON
    RESOLVED=$(echo "$JSON_OUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
files=d.get('resolved_test_files',[])
globs=d.get('affected_test_globs',[])
if files: print('\n'.join(files))
elif globs: print('\n'.join(globs))
")

    if [[ -n "$RESOLVED" ]]; then
      TEST_FILES=()
      while IFS= read -r line; do
        [[ -n "$line" ]] && TEST_FILES+=("$line")
      done <<< "$RESOLVED"

      if [[ ${#TEST_FILES[@]} -gt 0 ]]; then
        echo "  Running pytest on ${#TEST_FILES[@]} files:"
        for t in "${TEST_FILES[@]}"; do
          echo "    $t"
        done
        echo ""
        python3 -m pytest "${TEST_FILES[@]}" -v -m "not network"
      fi
    else
      echo "  No test files matched."
    fi
    ;;
  STRICT)
    if [[ "$ONLY_TARGETED" == "1" ]]; then
      echo "🎯 TIER_MEDIUM override: Running targeted tests only."
      # MEDIUM path would have been taken; this branch is for --only-targeted with STRICT inputs
      echo "  Cannot run targeted tests for unmapped STRICT files. Use --full or add SOURCE_TEST_MAP entry."
      exit 1
    fi
    echo "🔒 TIER_STRICT: Running full pytest suite."
    python3 -m pytest -v -m "not network"
    ;;
  *)
    echo "⚠️ Unknown tier: $TIER — defaulting to full suite."
    python3 -m pytest -v -m "not network"
    ;;
esac
