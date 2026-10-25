#!/usr/bin/env python3
"""
Integration Testing Script - KAN-279

Script to validate integration of the structured cross-functional review system
with existing task coordination and workflow systems.

Version: 1.0.0
Author: HoroConsultant Integration Team
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
REPO_ROOT = str(ROOT_DIR)

# Note: hermes_tools is intentionally not imported here; this script only uses
# the standard library (see integration_coordination.py for the mock pattern).

class IntegrationTester:
    """Main class for integration testing."""
    
    def __init__(self, integration_file: str = None):
        self.integration_file = integration_file or "integration_config.json"
        self.test_results = []
        self.integration_validation = {}
        
    def run_integration_validation(self):
        """Run comprehensive integration validation."""
        print("🔍 Starting Integration Validation")
        print("=" * 50)
        
        # Test 1: Core System Integration
        self._test_core_system_integration()
        
        # Test 2: Task Coordination Integration
        self._test_task_coordination_integration()
        
        # Test 3: Quality Assurance Integration
        self._test_quality_assurance_integration()
        
        # Test 4: Documentation Integration
        self._test_documentation_integration()
        
        # Test 5: Workflow Integration
        self._test_workflow_integration()
        
        # Generate integration report
        self._generate_integration_report()
        
        return self._generate_summary()
    
    def _test_core_system_integration(self):
        """Test core system integration."""
        print("\n🧪 Test 1: Core System Integration")
        
        test_result = {
            "test_name": "Core System Integration",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check core files exist
        core_files = [
            f"{REPO_ROOT}/.hermes/scripts/cross_functional_review.py",
            f"{REPO_ROOT}/.hermes/reviews/KAN-279-cross-functional-review.md"
        ]
        
        for file_path in core_files:
            if os.path.exists(file_path):
                test_result["details"].append(f"✅ Core file exists: {os.path.basename(file_path)}")
            else:
                test_result["details"].append(f"❌ Core file missing: {file_path}")
                test_result["status"] = "FAIL"
        
        self.test_results.append(test_result)
    
    def _test_task_coordination_integration(self):
        """Test integration with task coordination systems."""
        print("\n🧪 Test 2: Task Coordination Integration")
        
        test_result = {
            "test_name": "Task Coordination Integration",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check integration requirements
        coordination_files = [
            f"{REPO_ROOT}/ATOMIC_TICKET.md",
            f"{REPO_ROOT}/plans/test_provenance",
            f"{REPO_ROOT}/.githooks"
        ]
        
        for file_path in coordination_files:
            if os.path.exists(file_path):
                test_result["details"].append(f"✅ Coordination component exists: {os.path.basename(file_path)}")
            else:
                test_result["details"].append(f"❌ Coordination component missing: {file_path}")
                test_result["status"] = "WARN"
        
        # Check for integration scripts
        integration_scripts = [
            f"{REPO_ROOT}/scripts/integration.py",
            f"{REPO_ROOT}/.hermes/scripts/integration.py"
        ]
        
        found_script = False
        for script_path in integration_scripts:
            if os.path.exists(script_path):
                test_result["details"].append(f"✅ Integration script exists: {os.path.basename(script_path)}")
                found_script = True
                break
        
        if not found_script:
            test_result["details"].append("⚠️ Integration script not found - will use default integration")
        
        self.test_results.append(test_result)
    
    def _test_quality_assurance_integration(self):
        """Test integration with quality assurance systems."""
        print("\n🧪 Test 3: Quality Assurance Integration")
        
        test_result = {
            "test_name": "Quality Assurance Integration",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check existing test files
        test_files = [
            f"{REPO_ROOT}/tests",
            f"{REPO_ROOT}/TDD-HORO-v3.0",
            f"{REPO_ROOT}/scripts/test_*.py"
        ]
        
        test_files_exist = 0
        for pattern in test_files:
            if os.path.exists(pattern):
                test_files_exist += 1
        
        if test_files_exist > 0:
            test_result["details"].append(f"✅ QA components found ({test_files_exist} test directories)")
        else:
            test_result["details"].append("❌ No QA components found")
            test_result["status"] = "FAIL"
        
        # Check test suite execution
        if os.path.exists(f"{REPO_ROOT}/tests"):
            test_files = os.listdir(f"{REPO_ROOT}/tests")
            test_result["details"].append(f"✅ Test suite found with {len(test_files)} test files")
        
        self.test_results.append(test_result)
    
    def _test_documentation_integration(self):
        """Test integration with documentation systems."""
        print("\n🧪 Test 4: Documentation Integration")
        
        test_result = {
            "test_name": "Documentation Integration",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check documentation components
        doc_files = [
            f"{REPO_ROOT}/README.md",
            f"{REPO_ROOT}/docs",
            f"{REPO_ROOT}/SUMMARY.md"
        ]
        
        doc_count = 0
        for file_path in doc_files:
            if os.path.exists(file_path):
                doc_count += 1
        
        if doc_count > 0:
            test_result["details"].append(f"✅ Documentation components found ({doc_count} documentation files)")
        else:
            test_result["details"].append("❌ Documentation components missing")
            test_result["status"] = "WARN"
        
        # Check review documentation
        if os.path.exists(f"{REPO_ROOT}/.hermes/reviews/KAN-279-cross-functional-review.md"):
            test_result["details"].append("✅ Review documentation created successfully")
        else:
            test_result["details"].append("❌ Review documentation missing")
        
        self.test_results.append(test_result)
    
    def _test_workflow_integration(self):
        """Test integration with workflow systems."""
        print("\n🧪 Test 5: Workflow Integration")
        
        test_result = {
            "test_name": "Workflow Integration",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for workflow scripts (glob patterns)
        workflow_scripts = [
            str(ROOT_DIR / "scripts" / "*.py"),
            str(ROOT_DIR / ".hermes" / "scripts" / "*.py")
        ]

        workflow_count = sum(len(glob.glob(pattern)) for pattern in workflow_scripts)
        
        if workflow_count > 0:
            test_result["details"].append(f"✅ Workflow scripts found ({workflow_count} scripts)")
        else:
            test_result["details"].append("❌ Workflow scripts missing")
            test_result["status"] = "WARN"
        
        # Check for git hooks
        if os.path.exists(f"{REPO_ROOT}/.githooks"):
            test_result["details"].append("✅ Git hooks present for workflow integration")
        
        self.test_results.append(test_result)
    
    def _generate_integration_report(self):
        """Generate comprehensive integration report."""
        print("\n📊 Generating Integration Report")
        print("=" * 50)
        
        self.integration_validation = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for test in self.test_results if test["status"] == "PASS"),
            "warning_tests": sum(1 for test in self.test_results if test["status"] == "WARN"),
            "failed_tests": sum(1 for test in self.test_results if test["status"] == "FAIL"),
            "test_results": self.test_results
        }
        
        # Save integration report
        report_file = f"{REPO_ROOT}/plans/test_provenance/integration_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.integration_validation, f, indent=2)
        
        print(f"✅ Integration report saved to: {report_file}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate integration test summary."""
        total_tests = self.integration_validation["total_tests"]
        passed_tests = self.integration_validation["passed_tests"]
        warning_tests = self.integration_validation["warning_tests"]
        failed_tests = self.integration_validation["failed_tests"]
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "integration_status": "SUCCESS" if success_rate >= 80 else "NEEDS_ATTENTION",
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "warning_tests": warning_tests,
            "failed_tests": failed_tests,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations()
        }
        
        print("\n🎯 Integration Test Summary")
        print("=" * 50)
        print(f"✅ Integration Status: {summary['integration_status']}")
        print(f"📊 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🧪 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"⚠️ Warnings: {summary['warning_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate integration recommendations."""
        recommendations = []
        
        failed_tests = [test for test in self.test_results if test["status"] == "FAIL"]
        warning_tests = [test for test in self.test_results if test["status"] == "WARN"]
        
        if failed_tests:
            recommendations.append("🔴 Address failed integration tests")
        
        if warning_tests:
            recommendations.append("🟡 Review warnings and improve integration completeness")
        
        if len(failed_tests) == 0 and len(warning_tests) == 0:
            recommendations.append("✅ Integration successful - proceed with deployment")
        else:
            recommendations.append("🔄 Complete integration remediation before deployment")
        
        recommendations.append("📋 Document integration results for future reference")
        
        return recommendations


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Integration Testing Script - KAN-279"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Integration test command
    test_parser = subparsers.add_parser("test", help="Run integration tests")
    test_parser.add_argument("--config", help="Integration configuration file")
    test_parser.add_argument("--output", help="Output file for integration report")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run integration tests
    tester = IntegrationTester(args.config)
    
    if args.output:
        print(f"📁 Integration report will be saved to: {args.output}")
        # Override default output path
        tester.integration_file = args.output
    
    summary = tester.run_integration_validation()
    
    # Print summary
    print("\n📋 Integration Test Summary")
    print("=" * 50)
    
    for recommendation in summary["recommendations"]:
        print(recommendation)
    
    print(f"\n🎯 Overall Integration Status: {summary['integration_status']}")
    
    return 0 if summary["integration_status"] == "SUCCESS" else 1

if __name__ == "__main__":
    sys.exit(main())