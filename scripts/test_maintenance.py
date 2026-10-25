#!/usr/bin/env python3
"""
Test Maintenance Automation (KAN-308 4C)
- Flaky test detection & quarantine
- Snapshot auto-update
- Coverage regression gate (>5% drop = fail)
- AI-assisted test generation for uncovered code paths
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import bridge clients
try:
    import requests
    HAS_REQUESTS = True
    RequestsModule = requests
except ImportError:
    HAS_REQUESTS = False
    RequestsModule = None  # type: ignore


class BridgeClient:
    """Client for communicating with AI bridges (gemini-web-bridge / aipass-web-bridge)"""

    def __init__(self, bridge_name: str, base_url: str):
        self.bridge_name = bridge_name
        self.base_url = base_url.rstrip("/")
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        if not HAS_REQUESTS or RequestsModule is None:
            return False
        try:
            if "gemini" in self.bridge_name:
                resp = RequestsModule.get(f"{self.base_url}/healthz", timeout=5)
                return resp.status_code == 200 and "gemini-web-bridge" in resp.text
            elif "aipass" in self.bridge_name:
                resp = RequestsModule.get(f"{self.base_url}/registry", timeout=5)
                return resp.status_code == 200 and "aipass-web-bridge" in resp.text
        except Exception:
            return False
        return False

    def generate(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        if not self.available or RequestsModule is None:
            return None
        try:
            payload = {"prompt": prompt}
            if model:
                payload["model"] = model
            resp = RequestsModule.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json().get("text", "")
        except Exception:
            pass
        return None


class FlakyDetector:
    """Detects and tracks flaky tests"""

    HISTORY_FILE = Path(".hermes/flaky_history.json")
    QUARANTINE_THRESHOLD = 3  # Quarantine after N consecutive failures
    FLAKY_THRESHOLD = 0.3  # Consider flaky if fail rate > 30%

    def __init__(self):
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"tests": {}, "runs": []}

    def _save_history(self):
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=2)

    def record_run(self, test_results: List[Dict]):
        """Record a test run result"""
        run_id = f"run_{int(time.time())}"
        run_data = {
            "id": run_id,
            "timestamp": time.time(),
            "results": test_results,
        }
        self.history["runs"].append(run_data)
        # Keep last 100 runs
        self.history["runs"] = self.history["runs"][-100:]

        # Update per-test stats
        for result in test_results:
            test_name = result["name"]
            if test_name not in self.history["tests"]:
                self.history["tests"][test_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "consecutive_failures": 0,
                    "quarantined": False,
                }
            stats = self.history["tests"][test_name]
            stats["total"] += 1
            if result["passed"]:
                stats["passed"] += 1
                stats["consecutive_failures"] = 0
            else:
                stats["failed"] += 1
                stats["consecutive_failures"] += 1
                if stats["consecutive_failures"] >= self.QUARANTINE_THRESHOLD:
                    stats["quarantined"] = True

        self._save_history()

    def get_flaky_tests(self) -> List[Dict]:
        """Get list of flaky tests"""
        flaky = []
        for name, stats in self.history["tests"].items():
            if stats["total"] >= 3:  # Need minimum runs
                fail_rate = stats["failed"] / stats["total"]
                if fail_rate > self.FLAKY_THRESHOLD and not stats.get("quarantined", False):
                    flaky.append({
                        "name": name,
                        "fail_rate": fail_rate,
                        "total_runs": stats["total"],
                        "consecutive_failures": stats["consecutive_failures"],
                    })
        return sorted(flaky, key=lambda x: x["fail_rate"], reverse=True)

    def get_quarantined_tests(self) -> List[str]:
        """Get list of quarantined test names"""
        return [
            name for name, stats in self.history["tests"].items()
            if stats.get("quarantined", False)
        ]

    def run_detection(self, test_path: str = "tests") -> Dict:
        """Run flaky detection by executing tests multiple times"""
        print(f"Running flaky detection on {test_path}...")
        all_results = []

        # Run tests 3 times to detect flakiness
        for i in range(3):
            print(f"  Run {i+1}/3...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            # Parse results (simplified)
            passed = result.returncode == 0
            all_results.append({
                "run": i,
                "passed": passed,
                "output": result.stdout[-2000:] if result.stdout else "",
            })

        # For now, return summary
        return {
            "runs": all_results,
            "flaky_detected": any(not r["passed"] for r in all_results) and any(r["passed"] for r in all_results),
        }


class SnapshotManager:
    """Manages snapshot testing and auto-updates"""

    SNAPSHOTS_DIR = Path("tests/snapshots")

    def __init__(self):
        self.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def get_snapshot_path(self, test_name: str) -> Path:
        safe_name = test_name.replace("/", "_").replace("::", "_")
        return self.SNAPSHOTS_DIR / f"{safe_name}.snap"

    def snapshot_exists(self, test_name: str) -> bool:
        return self.get_snapshot_path(test_name).exists()

    def load_snapshot(self, test_name: str) -> Optional[str]:
        path = self.get_snapshot_path(test_name)
        if path.exists():
            return path.read_text()
        return None

    def save_snapshot(self, test_name: str, content: str):
        path = self.get_snapshot_path(test_name)
        path.write_text(content)

    def compare_and_update(self, test_name: str, actual_output: str, auto_update: bool = False) -> Dict:
        """Compare output with snapshot, optionally update"""
        expected = self.load_snapshot(test_name)
        if expected is None:
            if auto_update:
                self.save_snapshot(test_name, actual_output)
                return {"status": "created", "updated": True}
            return {"status": "missing", "updated": False, "expected": None, "actual": actual_output}

        if expected == actual_output:
            return {"status": "match", "updated": False}
        else:
            if auto_update:
                self.save_snapshot(test_name, actual_output)
                return {"status": "updated", "updated": True, "expected": expected, "actual": actual_output}
            return {"status": "mismatch", "updated": False, "expected": expected, "actual": actual_output}


class CoverageGate:
    """Coverage regression gate - fails if coverage drops >5%"""

    BASELINE_FILE = Path(".hermes/coverage_baseline.json")
    THRESHOLD = 5.0  # percent

    def __init__(self):
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict:
        if self.BASELINE_FILE.exists():
            try:
                with open(self.BASELINE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"total": 0.0, "files": {}, "timestamp": 0}

    def _save_baseline(self, data: Dict):
        self.BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.BASELINE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def run_coverage(self, test_path: str = "tests") -> Dict:
        """Run pytest with coverage and return results"""
        print(f"Running coverage on {test_path}...")
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest", test_path,
                "--cov=.", "--cov-report=json:.hermes/coverage.json",
                "-q", "--tb=short"
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        coverage_file = Path(".hermes/coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                cov_data = json.load(f)
            total = cov_data.get("totals", {}).get("percent_covered", 0.0)
            files = cov_data.get("files", {})
            return {
                "total": total,
                "files": {k: v.get("summary", {}).get("percent_covered", 0) for k, v in files.items()},
                "raw": cov_data,
            }
        return {"total": 0.0, "files": {}, "raw": {}}

    def check_regression(self, current: Dict, update_baseline: bool = False) -> Dict:
        """Check for coverage regression"""
        baseline_total = self.baseline.get("total", 0.0)
        current_total = current.get("total", 0.0)

        if baseline_total == 0.0:
            # First run, establish baseline
            if update_baseline:
                self._save_baseline({**current, "timestamp": time.time()})
            return {
                "passed": True,
                "baseline": baseline_total,
                "current": current_total,
                "delta": 0.0,
                "message": "No baseline established",
            }

        delta = baseline_total - current_total
        passed = delta <= self.THRESHOLD

        result = {
            "passed": passed,
            "baseline": baseline_total,
            "current": current_total,
            "delta": delta,
            "threshold": self.THRESHOLD,
            "message": f"Coverage: {current_total:.1f}% (baseline: {baseline_total:.1f}%, delta: {delta:.1f}%)",
        }

        if update_baseline and passed:
            self._save_baseline({**current, "timestamp": time.time()})

        return result


class AITestGenerator:
    """AI-assisted test generation for uncovered code paths"""

    def __init__(self):
        self.gemini_bridge = BridgeClient("gemini-web-bridge", "http://127.0.0.1:8765")
        self.aipass_bridge = BridgeClient("aipass-web-bridge", "http://127.0.0.1:8766")
        self.active_bridge = self.gemini_bridge if self.gemini_bridge.available else self.aipass_bridge

    def get_uncovered_paths(self, coverage_data: Dict) -> List[Dict]:
        """Identify uncovered code paths from coverage data"""
        uncovered = []
        for file_path, file_data in coverage_data.get("files", {}).items():
            if isinstance(file_data, dict):
                missing_lines = file_data.get("missing_lines", [])
                if missing_lines:
                    uncovered.append({
                        "file": file_path,
                        "missing_lines": missing_lines,
                        "coverage": file_data.get("summary", {}).get("percent_covered", 0),
                    })
        return uncovered

    def generate_test_stub(self, uncovered_item: Dict) -> Optional[str]:
        """Generate a test stub for uncovered code"""
        if not self.active_bridge:
            return None

        file_path = uncovered_item["file"]
        missing = uncovered_item["missing_lines"][:10]  # Limit to first 10

        prompt = f"""Generate a pytest test stub for the following uncovered code in {file_path}:

Uncovered lines: {missing}

Create a minimal test that exercises these code paths. Use pytest style.
Only output the test code, no explanation."""

        response = self.active_bridge.generate(prompt)
        if response:
            return f"# AI-generated test for {file_path}\n{response}"
        return None

    def generate_tests_for_uncovered(self, coverage_data: Dict, output_dir: str = "tests/generated") -> List[str]:
        """Generate tests for all uncovered paths"""
        uncovered = self.get_uncovered_paths(coverage_data)
        generated = []

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for item in uncovered[:5]:  # Limit to 5 files per run
            test_code = self.generate_test_stub(item)
            if test_code:
                file_name = Path(item["file"]).stem
                test_file = output_path / f"test_generated_{file_name}.py"
                test_file.write_text(test_code)
                generated.append(str(test_file))
                print(f"Generated: {test_file}")

        return generated


def cmd_flaky(args):
    """Flaky test detection command"""
    detector = FlakyDetector()
    if args.detect:
        result = detector.run_detection(args.path)
        print(json.dumps(result, indent=2))
    elif args.list:
        flaky = detector.get_flaky_tests()
        print(json.dumps(flaky, indent=2))
    elif args.quarantined:
        quarantined = detector.get_quarantined_tests()
        print(json.dumps(quarantined, indent=2))
    else:
        print("Use --detect, --list, or --quarantined")


def cmd_snapshot(args):
    """Snapshot management command"""
    manager = SnapshotManager()
    if args.update:
        # This would be called from actual test code
        print("Use from test code: manager.compare_and_update(name, output, auto_update=True)")
    elif args.list:
        snaps = list(manager.SNAPSHOTS_DIR.glob("*.snap"))
        print(json.dumps([str(s) for s in snaps], indent=2))
    else:
        print("Use --update or --list")


def cmd_coverage(args):
    """Coverage regression gate command"""
    gate = CoverageGate()
    if args.check:
        current = gate.run_coverage(args.path)
        result = gate.check_regression(current, update_baseline=args.update_baseline)
        print(json.dumps(result, indent=2))
        if not result["passed"]:
            sys.exit(1)
    elif args.baseline:
        current = gate.run_coverage(args.path)
        gate._save_baseline({**current, "timestamp": time.time()})
        print("Baseline established")
    else:
        print("Use --check or --baseline")


def cmd_generate_tests(args):
    """AI test generation command"""
    generator = AITestGenerator()
    if not generator.active_bridge:
        print("No AI bridge available. Start gemini-web-bridge (port 8765) or aipass-web-bridge (port 8766)")
        sys.exit(1)

    # Run coverage first
    gate = CoverageGate()
    current = gate.run_coverage(args.path)
    generated = generator.generate_tests_for_uncovered(current.get("raw", {}), args.output)
    print(json.dumps({"generated": generated}, indent=2))


def cmd_all(args):
    """Run all maintenance tasks"""
    print("=== Running Test Maintenance ===\n")

    # 1. Flaky detection
    print("1. Flaky Detection...")
    detector = FlakyDetector()
    flaky_result = detector.run_detection(args.path)
    flaky_tests = detector.get_flaky_tests()
    print(f"   Flaky tests detected: {len(flaky_tests)}")
    for ft in flaky_tests[:5]:
        print(f"   - {ft['name']}: {ft['fail_rate']:.1%} fail rate")

    # 2. Coverage regression
    print("\n2. Coverage Regression Gate...")
    gate = CoverageGate()
    current = gate.run_coverage(args.path)
    cov_result = gate.check_regression(current, update_baseline=args.update_baseline)
    print(f"   {cov_result['message']}")
    if not cov_result["passed"]:
        print("   ⚠️  COVERAGE REGRESSION DETECTED!")
        if not args.force:
            sys.exit(1)

    # 3. AI Test Generation
    print("\n3. AI Test Generation...")
    generator = AITestGenerator()
    if generator.active_bridge:
        generated = generator.generate_tests_for_uncovered(current.get("raw", {}), args.output)
        print(f"   Generated {len(generated)} test files")
    else:
        print("   Skipped (no AI bridge available)")

    print("\n=== Test Maintenance Complete ===")


def main():
    parser = argparse.ArgumentParser(description="Test Maintenance Automation (KAN-308 4C)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Flaky detection
    flaky_parser = subparsers.add_parser("flaky", help="Flaky test detection")
    flaky_parser.add_argument("--detect", action="store_true", help="Run detection")
    flaky_parser.add_argument("--list", action="store_true", help="List flaky tests")
    flaky_parser.add_argument("--quarantined", action="store_true", help="List quarantined tests")
    flaky_parser.add_argument("--path", default="tests", help="Test path")
    flaky_parser.set_defaults(func=cmd_flaky)

    # Snapshot management
    snap_parser = subparsers.add_parser("snapshot", help="Snapshot management")
    snap_parser.add_argument("--update", action="store_true", help="Update snapshots")
    snap_parser.add_argument("--list", action="store_true", help="List snapshots")
    snap_parser.set_defaults(func=cmd_snapshot)

    # Coverage gate
    cov_parser = subparsers.add_parser("coverage", help="Coverage regression gate")
    cov_parser.add_argument("--check", action="store_true", help="Check for regression")
    cov_parser.add_argument("--baseline", action="store_true", help="Establish baseline")
    cov_parser.add_argument("--update-baseline", action="store_true", help="Update baseline if passed")
    cov_parser.add_argument("--path", default="tests", help="Test path")
    cov_parser.set_defaults(func=cmd_coverage)

    # AI test generation
    gen_parser = subparsers.add_parser("generate", help="AI test generation")
    gen_parser.add_argument("--output", default="tests/generated", help="Output directory")
    gen_parser.add_argument("--path", default="tests", help="Test path")
    gen_parser.set_defaults(func=cmd_generate_tests)

    # All-in-one
    all_parser = subparsers.add_parser("all", help="Run all maintenance tasks")
    all_parser.add_argument("--path", default="tests", help="Test path")
    all_parser.add_argument("--output", default="tests/generated", help="Generated tests output")
    all_parser.add_argument("--update-baseline", action="store_true", help="Update coverage baseline")
    all_parser.add_argument("--force", action="store_true", help="Don't exit on regression")
    all_parser.set_defaults(func=cmd_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()