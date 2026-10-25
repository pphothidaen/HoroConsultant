#!/usr/bin/env python3
"""
AI Governance Observability (KAN-308 4E)
LangSmith/MLflow tracing, CI/CD anomaly detection, SDLC health dashboard (alerting only), quality gate telemetry
"""
import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional dependencies - graceful degradation
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


class BridgeClient:
    """Minimal bridge client for gemini/aipass web bridges"""

    def __init__(self):
        self.gemini_url = os.environ.get("GEMINI_WEB_BRIDGE_URL", "http://127.0.0.1:8765")
        self.aipass_url = os.environ.get("AIPASS_WEB_BRIDGE_URL", "http://127.0.0.1:8766")

    def health_check(self) -> Dict[str, bool]:
        """Check bridge health via semantic signature"""
        import urllib.request
        import urllib.error

        results = {}
        for name, url in [("gemini", self.gemini_url), ("aipass", self.aipass_url)]:
            try:
                req = urllib.request.Request(f"{url}/healthz" if name == "gemini" else f"{url}/registry")
                req.add_header("User-Agent", "hermes-observability/1.0")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode())
                    expected = "gemini-web-bridge" if name == "gemini" else "aipass-web-bridge"
                    results[name] = data.get("service") == expected
            except Exception:
                results[name] = False
        return results


class TracingManager:
    """LangSmith/MLflow tracing for AI SDLC pipeline"""

    def __init__(self):
        self.langsmith_client = None
        self.mlflow_active = False
        self._init_langsmith()
        self._init_mlflow()

    def _init_langsmith(self):
        if not LANGSMITH_AVAILABLE:
            return
        api_key = os.environ.get("LANGSMITH_API_KEY")
        if api_key:
            try:
                self.langsmith_client = LangSmithClient(api_key=api_key)
            except Exception:
                self.langsmith_client = None

    def _init_mlflow(self):
        if not MLFLOW_AVAILABLE:
            return
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("hermes-sdlc")
            self.mlflow_active = True
        except Exception:
            pass

    def trace_ai_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trace AI code review execution"""
        trace_id = f"review-{int(time.time() * 1000)}"
        result = {"trace_id": trace_id, "status": "traced", "langsmith": "false", "mlflow": "false"}

        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name="ai_code_review",
                    run_type="chain",
                    inputs={"files_changed": review_data.get("files_changed", [])},
                    outputs={"findings_count": len(review_data.get("findings", []))},
                )
                result["langsmith"] = "true"
            except Exception:
                result["langsmith"] = "false"

        if self.mlflow_active:
            try:
                with mlflow.start_run(run_name=trace_id):
                    mlflow.log_params({
                        "files_changed": len(review_data.get("files_changed", [])),
                        "model": review_data.get("model", "unknown"),
                    })
                    mlflow.log_metrics({
                        "critical_findings": len([f for f in review_data.get("findings", []) if f.get("severity") == "critical"]),
                        "high_findings": len([f for f in review_data.get("findings", []) if f.get("severity") == "high"]),
                        "total_findings": len(review_data.get("findings", [])),
                    })
                result["mlflow"] = "true"
            except Exception:
                result["mlflow"] = "false"

        return result

    def trace_quality_gate(self, gate_result: Dict[str, Any]) -> Dict[str, Any]:
        """Trace quality gate evaluation"""
        trace_id = f"gate-{int(time.time() * 1000)}"
        result = {"trace_id": trace_id, "status": "traced", "langsmith": "false", "mlflow": "false"}

        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name="quality_gate",
                    run_type="chain",
                    inputs={"thresholds": gate_result.get("thresholds", {})},
                    outputs={"passed": gate_result.get("passed", False)},
                )
                result["langsmith"] = "true"
            except Exception:
                result["langsmith"] = "false"

        if self.mlflow_active:
            try:
                with mlflow.start_run(run_name=trace_id):
                    mlflow.log_metric("gate_passed", 1 if gate_result.get("passed") else 0)
                    mlflow.log_metric("violations", gate_result.get("violations", 0))
                result["mlflow"] = "true"
            except Exception:
                result["mlflow"] = "false"

        return result

    def trace_refactoring(self, refactor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trace refactoring agent runs"""
        trace_id = f"refactor-{int(time.time() * 1000)}"
        result = {"trace_id": trace_id, "status": "traced", "langsmith": "false", "mlflow": "false"}

        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name="ai_refactoring",
                    run_type="chain",
                    inputs={"target_files": refactor_data.get("target_files", [])},
                    outputs={"suggestions": len(refactor_data.get("suggestions", []))},
                )
                result["langsmith"] = "true"
            except Exception:
                result["langsmith"] = "false"

        if self.mlflow_active:
            try:
                with mlflow.start_run(run_name=trace_id):
                    mlflow.log_metric("files_analyzed", len(refactor_data.get("target_files", [])))
                    mlflow.log_metric("suggestions_count", len(refactor_data.get("suggestions", [])))
                result["mlflow"] = "true"
            except Exception:
                result["mlflow"] = "false"

        return result


class AnomalyDetector:
    """CI/CD metric anomaly detection"""

    def __init__(self, history_path: str = ".hermes/ci_history.json"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.thresholds = {
            "duration_multiplier": 2.0,      # 2x normal duration
            "failure_rate_threshold": 0.3,   # 30% failure rate
            "queue_time_multiplier": 3.0,    # 3x normal queue time
        }

    def load_history(self) -> List[Dict[str, Any]]:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text()).get("builds", [])
            except Exception:
                return []
        return []

    def save_history(self, builds: List[Dict[str, Any]]):
        self.history_path.write_text(json.dumps({"builds": builds}, indent=2))

    def record_build(self, duration_seconds: int, status: str, queue_seconds: int = 0):
        """Record a build for anomaly detection"""
        builds = self.load_history()
        builds.append({
            "duration_seconds": duration_seconds,
            "status": status,
            "queue_seconds": queue_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep last 100 builds
        self.save_history(builds[-100:])

    def detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in CI/CD metrics"""
        builds = self.load_history()
        if len(builds) < 5:
            return {"anomalies": [], "insufficient_data": True}

        durations = [b["duration_seconds"] for b in builds if b["status"] == "success"]
        failure_rate = sum(1 for b in builds if b["status"] != "success") / len(builds)
        queue_times = [b.get("queue_seconds", 0) for b in builds]

        anomalies = []

        # Duration anomaly
        if durations:
            median_duration = statistics.median(durations)
            latest_duration = durations[-1] if durations else 0
            if latest_duration > median_duration * self.thresholds["duration_multiplier"]:
                anomalies.append({
                    "type": "duration",
                    "severity": "high" if latest_duration > median_duration * 3 else "medium",
                    "message": f"Build duration {latest_duration}s exceeds {self.thresholds['duration_multiplier']}x median ({median_duration}s)",
                    "value": latest_duration,
                    "baseline": median_duration,
                })

        # Failure rate anomaly
        if failure_rate > self.thresholds["failure_rate_threshold"]:
            anomalies.append({
                "type": "failure_rate",
                "severity": "critical" if failure_rate > 0.5 else "high",
                "message": f"Failure rate {failure_rate:.1%} exceeds {self.thresholds['failure_rate_threshold']:.0%} threshold",
                "value": failure_rate,
                "baseline": self.thresholds["failure_rate_threshold"],
            })

        # Queue time anomaly
        if queue_times:
            median_queue = statistics.median(queue_times)
            latest_queue = queue_times[-1] if queue_times else 0
            if latest_queue > median_queue * self.thresholds["queue_time_multiplier"]:
                anomalies.append({
                    "type": "queue_time",
                    "severity": "medium",
                    "message": f"Queue time {latest_queue}s exceeds {self.thresholds['queue_time_multiplier']}x median ({median_queue}s)",
                    "value": latest_queue,
                    "baseline": median_queue,
                })

        return {"anomalies": anomalies, "insufficient_data": False}


class HealthDashboard:
    """SDLC health dashboard (alerting only - NO control authority)"""

    def __init__(self):
        self.metrics = {
            "code_quality": {},
            "test_health": {},
            "ci_health": {},
            "security": {},
        }

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect health metrics from various sources"""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
        }

        # Code quality metrics
        quality_path = Path(".hermes/tech_debt_history.json")
        if quality_path.exists():
            try:
                history = json.loads(quality_path.read_text())
                latest = history[-1] if history else {}
                metrics["code_quality"] = {
                    "maintainability_index": latest.get("maintainability_index"),
                    "debt_ratio": latest.get("debt_ratio"),
                    "complexity_avg": latest.get("complexity", {}).get("average"),
                }
            except Exception:
                pass

        # Test health
        test_artifacts = Path(".hermes/test_artifacts")
        if test_artifacts.exists():
            metrics["test_health"] = {
                "flaky_tests": len(list(test_artifacts.glob("flaky_*.json"))),
                "coverage_regressions": len(list(test_artifacts.glob("coverage_regression_*.json"))),
            }

        # CI health from anomaly detector
        detector = AnomalyDetector()
        anomaly_result = detector.detect_anomalies()
        metrics["ci_health"] = {
            "anomalies": anomaly_result.get("anomalies", []),
            "anomaly_count": len(anomaly_result.get("anomalies", [])),
        }

        # Security metrics
        sec_artifacts = Path(".hermes/security_artifacts")
        if sec_artifacts.exists():
            metrics["security"] = {
                "vulnerabilities": len(list(sec_artifacts.glob("vuln_*.json"))),
                "secrets_found": len(list(sec_artifacts.glob("secrets_*.json"))),
            }

        return metrics

    def generate_dashboard(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate dashboard data (JSON for UI consumption)"""
        metrics = self.collect_metrics()

        # Determine overall health status
        anomaly_count = metrics.get("ci_health", {}).get("anomaly_count", 0)
        vuln_count = metrics.get("security", {}).get("vulnerabilities", 0)
        flaky_count = metrics.get("test_health", {}).get("flaky_tests", 0)

        if anomaly_count > 0 or vuln_count > 0:
            health = "degraded"
        elif flaky_count > 3:
            health = "warning"
        else:
            health = "healthy"

        dashboard = {
            "status": health,
            "timestamp": metrics["timestamp"],
            "components": metrics,
            "alerts": self._generate_alerts(metrics),
            "summary": {
                "total_anomalies": anomaly_count,
                "total_vulnerabilities": vuln_count,
                "flaky_tests": flaky_count,
            },
        }

        if output_path:
            Path(output_path).write_text(json.dumps(dashboard, indent=2))

        return dashboard

    def _generate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts (NO control actions - alerting only)"""
        alerts = []

        for anomaly in metrics.get("ci_health", {}).get("anomalies", []):
            alerts.append({
                "type": "ci_anomaly",
                "severity": anomaly.get("severity", "medium"),
                "message": anomaly.get("message", ""),
                "action": "investigate",  # Only alert, never control
            })

        vuln_count = metrics.get("security", {}).get("vulnerabilities", 0)
        if vuln_count > 0:
            alerts.append({
                "type": "security_vulnerabilities",
                "severity": "high" if vuln_count > 5 else "medium",
                "message": f"{vuln_count} vulnerabilities detected",
                "action": "review_dependabot_prs",
            })

        flaky = metrics.get("test_health", {}).get("flaky_tests", 0)
        if flaky > 3:
            alerts.append({
                "type": "flaky_tests",
                "severity": "medium",
                "message": f"{flaky} flaky tests quarantined",
                "action": "review_quarantine",
            })

        return alerts

    def generate_weekly_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate weekly health report"""
        dashboard = self.generate_dashboard()
        report = {
            "report_type": "weekly_health",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dashboard": dashboard,
            "recommendations": self._generate_recommendations(dashboard),
        }
        if output_path:
            Path(output_path).write_text(json.dumps(report, indent=2))
        return report

    def _generate_recommendations(self, dashboard: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        summary = dashboard.get("summary", {})

        if summary.get("total_anomalies", 0) > 0:
            recs.append("Investigate CI anomalies - check build durations and failure patterns")
        if summary.get("total_vulnerabilities", 0) > 0:
            recs.append("Review and merge Dependabot PRs for vulnerability fixes")
        if summary.get("flaky_tests", 0) > 3:
            recs.append("Review quarantined flaky tests - fix or remove")

        if not recs:
            recs.append("All systems healthy - no action required")

        return recs


class TelemetryAggregator:
    """Quality gate telemetry aggregation"""

    def __init__(self, history_path: str = ".hermes/quality_gate_history.json"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def record_gate_result(self, result: Dict[str, Any]):
        """Record quality gate result"""
        history = self.load_history()
        history.append({
            **result,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })
        self.history_path.write_text(json.dumps(history[-500:], indent=2))

    def load_history(self) -> List[Dict[str, Any]]:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text())
            except Exception:
                return []
        return []

    def get_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze trends over specified days"""
        history = self.load_history()
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)

        recent = [
            h for h in history
            if datetime.fromisoformat(h.get("recorded_at", "").replace("Z", "+00:00")).timestamp() > cutoff
        ]

        if not recent:
            return {"insufficient_data": True}

        passed = sum(1 for r in recent if r.get("passed"))
        total = len(recent)
        violations = [r.get("violations", 0) for r in recent]

        return {
            "period_days": days,
            "total_runs": total,
            "pass_rate": passed / total if total > 0 else 0,
            "avg_violations": statistics.mean(violations) if violations else 0,
            "trend": "improving" if len(recent) > 10 and violations[-1] < violations[0] else "stable",
        }


def main():
    parser = argparse.ArgumentParser(description="AI Governance Observability")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Trace commands
    trace_parser = subparsers.add_parser("trace", help="Trace AI SDLC operations")
    trace_sub = trace_parser.add_subparsers(dest="trace_type")
    trace_sub.add_parser("review", help="Trace AI code review")
    trace_sub.add_parser("gate", help="Trace quality gate")
    trace_sub.add_parser("refactor", help="Trace refactoring")

    # Anomaly detection
    anomaly_parser = subparsers.add_parser("anomaly", help="CI/CD anomaly detection")
    anomaly_parser.add_argument("--record-build", nargs=3, metavar=("DURATION", "STATUS", "QUEUE"),
                                help="Record build: duration_seconds status queue_seconds")
    anomaly_parser.add_argument("--detect", action="store_true", help="Detect anomalies")

    # Dashboard
    dash_parser = subparsers.add_parser("dashboard", help="SDLC health dashboard")
    dash_parser.add_argument("--output", help="Output JSON file")
    dash_parser.add_argument("--weekly-report", help="Generate weekly report to file")

    # Telemetry
    tele_parser = subparsers.add_parser("telemetry", help="Quality gate telemetry")
    tele_parser.add_argument("--record", help="Record gate result (JSON string)")
    tele_parser.add_argument("--trends", type=int, default=30, help="Trend analysis days")

    # Bridge health
    subparsers.add_parser("bridge-health", help="Check bridge semantic signatures")

    args = parser.parse_args()

    if args.command == "trace":
        tm = TracingManager()
        if args.trace_type == "review":
            # Read review data from stdin or file
            data = json.loads(sys.stdin.read() or "{}")
            print(json.dumps(tm.trace_ai_review(data)))
        elif args.trace_type == "gate":
            data = json.loads(sys.stdin.read() or "{}")
            print(json.dumps(tm.trace_quality_gate(data)))
        elif args.trace_type == "refactor":
            data = json.loads(sys.stdin.read() or "{}")
            print(json.dumps(tm.trace_refactoring(data)))
        else:
            trace_parser.print_help()
            return 1

    elif args.command == "anomaly":
        det = AnomalyDetector()
        if args.record_build:
            duration, status, queue = args.record_build
            det.record_build(int(duration), status, int(queue))
            print(json.dumps({"status": "recorded"}))
        elif args.detect:
            print(json.dumps(det.detect_anomalies(), indent=2))
        else:
            anomaly_parser.print_help()
            return 1

    elif args.command == "dashboard":
        dash = HealthDashboard()
        if args.output:
            result = dash.generate_dashboard(args.output)
            print(json.dumps({"status": "generated", "file": args.output}))
        elif args.weekly_report:
            result = dash.generate_weekly_report(args.weekly_report)
            print(json.dumps({"status": "generated", "file": args.weekly_report}))
        else:
            print(json.dumps(dash.generate_dashboard(), indent=2))

    elif args.command == "telemetry":
        tel = TelemetryAggregator()
        if args.record:
            tel.record_gate_result(json.loads(args.record))
            print(json.dumps({"status": "recorded"}))
        else:
            print(json.dumps(tel.get_trends(args.trends), indent=2))

    elif args.command == "bridge-health":
        client = BridgeClient()
        print(json.dumps(client.health_check(), indent=2))

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())