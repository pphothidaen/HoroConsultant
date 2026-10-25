#!/bin/bash
# run_observability.sh - CI wrapper for AI Governance Observability
# Modes: weekly (health report), pr (dashboard), manual

set -euo pipefail

MODE="${1:-manual}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

case "$MODE" in
    weekly)
        echo "=== Weekly SDLC Health Report ==="
        python3 scripts/observability.py dashboard --weekly-report .hermes/weekly_health_report.json
        cat .hermes/weekly_health_report.json | jq -r '.recommendations[]' 2>/dev/null || true
        ;;

    pr)
        echo "=== PR Health Dashboard ==="
        python3 scripts/observability.py dashboard --output .hermes/pr_health_dashboard.json
        cat .hermes/pr_health_dashboard.json
        ;;

    record-build)
        # Called from CI after build completes
        DURATION="${2:-300}"
        STATUS="${3:-success}"
        QUEUE="${4:-0}"
        python3 scripts/observability.py anomaly --record-build "$DURATION" "$STATUS" "$QUEUE"
        ;;

    detect-anomalies)
        echo "=== CI/CD Anomaly Detection ==="
        python3 scripts/observability.py anomaly --detect
        ;;

    telemetry)
        echo "=== Quality Gate Telemetry ==="
        python3 scripts/observability.py telemetry --trends 30
        ;;

    trace-review)
        REVIEW_FILE="${2:-}"
        if [[ -f "$REVIEW_FILE" ]]; then
            python3 scripts/observability.py trace review < "$REVIEW_FILE"
        else
            echo '{}' | python3 scripts/observability.py trace review
        fi
        ;;

    trace-gate)
        GATE_FILE="${2:-}"
        if [[ -f "$GATE_FILE" ]]; then
            python3 scripts/observability.py trace gate < "$GATE_FILE"
        else
            echo '{}' | python3 scripts/observability.py trace gate
        fi
        ;;

    trace-refactor)
        REFACTOR_FILE="${2:-}"
        if [[ -f "$REFACTOR_FILE" ]]; then
            python3 scripts/observability.py trace refactor < "$REFACTOR_FILE"
        else
            echo '{}' | python3 scripts/observability.py trace refactor
        fi
        ;;

    bridge-health)
        python3 scripts/observability.py bridge-health
        ;;

    *)
        echo "Usage: $0 {weekly|pr|record-build|detect-anomalies|telemetry|trace-review|trace-gate|trace-refactor|bridge-health}"
        exit 1
        ;;
esac