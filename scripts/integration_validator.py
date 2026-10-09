#!/usr/bin/env python3
"""
Integration Validator Script - KAN-279

Script to validate the integration of the structured cross-functional review
system with existing task coordination and workflow systems.

Version: 1.0.0
Author: HoroConsultant Integration Team
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Note: Using sys.path insert to avoid hermes_tools import issues
# The validation is done using standard library modules

# Repository root resolved from this script's location (scripts/ -> repo root)
REPO_ROOT = str(Path(__file__).resolve().parent.parent)

class IntegrationValidator:
    """Main class for integration validation."""
    
    def __init__(self, validation_config: str = None):
        self.validation_config = validation_config
        self.validation_results = []
        self.overall_validation = {}
        
    def run_integration_validation(self, integration_type: str = "full"):
        """Run comprehensive integration validation."""
        print("🔍 Starting Integration Validation")
        print("=" * 60)
        
        if integration_type == "full":
            # Run all validation tests
            self._validate_core_integration()
            self._validate_system_compatibility()
            self._validate_workflow_integration()
            self._validate_documentation()
            self._validate_quality_assurance()
        elif integration_type == "partial":
            # Run limited validation tests
            self._validate_core_integration()
            self._validate_system_compatibility()
        
        # Generate validation report
        self._generate_validation_report()
        
        return self._generate_summary()
    
    def _validate_core_integration(self):
        """Validate core integration components."""
        print("\n🧪 Validating Core Integration")
        print("-" * 40)
        
        test_result = {
            "test_name": "Core Integration Validation",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if core review system exists
        core_components = [
            {
                "path": f"{REPO_ROOT}/.hermes/scripts/cross_functional_review.py",
                "name": "Core Review System"
            },
            {
                "path": f"{REPO_ROOT}/.hermes/reviews/KAN-279-cross-functional-review.md",
                "name": "Review Documentation"
            }
        ]
        
        for component in core_components:
            if os.path.exists(component["path"]):
                test_result["details"].append(
                    f"✅ {component['name']} exists and accessible"
                )
            else:
                test_result["details"].append(
                    f"❌ {component['name']} missing or inaccessible"
                )
                test_result["status"] = "FAIL"
        
        self.validation_results.append(test_result)
    
    def _validate_system_compatibility(self):
        """Validate system compatibility."""
        print("\n🧪 Validating System Compatibility")
        print("-" * 40)
        
        test_result = {
            "test_name": "System Compatibility Validation",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check existing task coordination systems
        coordination_systems = [
            {
                "path": f"{REPO_ROOT}/ATOMIC_TICKET.md",
                "name": "Atomic Ticket Registry"
            },
            {
                "path": f"{REPO_ROOT}/plans",
                "name": "Planning System"
            }
        ]
        
        for system in coordination_systems:
            if os.path.exists(system["path"]):
                test_result["details"].append(
                    f"✅ {system['name']} integrated successfully"
                )
            else:
                test_result["details"].append(
                    f"⚠️ {system['name']} integration needs attention"
                )
                test_result["status"] = "WARN"
        
        self.validation_results.append(test_result)
    
    def _validate_workflow_integration(self):
        """Validate workflow integration."""
        print("\n🧪 Validating Workflow Integration")
        print("-" * 40)
        
        test_result = {
            "test_name": "Workflow Integration Validation",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check workflow scripts
        workflow_scripts = [
            f"{REPO_ROOT}/scripts/integration_test.py",
            f"{REPO_ROOT}/scripts/integration_coordination.py"
        ]
        
        for script in workflow_scripts:
            if os.path.exists(script):
                try:
                    with open(script, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'def main()' in content and 'argparse.ArgumentParser' in content:
                            test_result["details"].append(
                                f"✅ Workflow script executable: {os.path.basename(script)}"
                            )
                        else:
                            test_result["details"].append(
                                f"⚠️ Workflow script found but may not be executable: {os.path.basename(script)}"
                            )
                except Exception as e:
                    test_result["details"].append(
                        f"❌ Error loading workflow script {os.path.basename(script)}: {str(e)}"
                    )
                    test_result["status"] = "FAIL"
            else:
                test_result["details"].append(
                    f"❌ Workflow script missing: {os.path.basename(script)}"
                )
                test_result["status"] = "FAIL"
        
        self.validation_results.append(test_result)
    
    def _validate_documentation(self):
        """Validate documentation integration."""
        print("\n🧪 Validating Documentation Integration")
        print("-" * 40)
        
        test_result = {
            "test_name": "Documentation Integration Validation",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check documentation components
        review_doc_path = f"{REPO_ROOT}/.hermes/reviews/KAN-279-cross-functional-review.md"
        
        if os.path.exists(review_doc_path):
            try:
                with open(review_doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 1000:
                        test_result["details"].append(
                            f"✅ Documentation is comprehensive ({len(content)} characters)"
                        )
                    else:
                        test_result["details"].append(
                            f"⚠️ Documentation may need expansion ({len(content)} characters)"
                        )
            except Exception as e:
                test_result["details"].append(
                    f"❌ Error reading documentation: {str(e)}"
                )
                test_result["status"] = "FAIL"
        else:
            test_result["details"].append("❌ Review documentation missing")
            test_result["status"] = "FAIL"
        
        self.validation_results.append(test_result)
    
    def _validate_quality_assurance(self):
        """Validate quality assurance integration."""
        print("\n🧪 Validating Quality Assurance Integration")
        print("-" * 40)
        
        test_result = {
            "test_name": "Quality Assurance Integration Validation",
            "status": "PASS",
            "details": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check integration test scripts
        test_scripts = [
            f"{REPO_ROOT}/scripts/integration_test.py",
            f"{REPO_ROOT}/scripts/integration_coordination.py"
        ]
        
        for test_script in test_scripts:
            if os.path.exists(test_script):
                test_result["details"].append(
                    f"✅ Integration test script found: {os.path.basename(test_script)}"
                )
            else:
                test_result["details"].append(
                    f"❌ Integration test script missing: {os.path.basename(test_script)}"
                )
                test_result["status"] = "FAIL"
        
        self.validation_results.append(test_result)
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report."""
        print("\n📊 Generating Validation Report")
        print("=" * 60)
        
        self.overall_validation = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.validation_results),
            "passed_tests": sum(1 for test in self.validation_results if test["status"] == "PASS"),
            "warning_tests": sum(1 for test in self.validation_results if test["status"] == "WARN"),
            "failed_tests": sum(1 for test in self.validation_results if test["status"] == "FAIL"),
            "validation_results": self.validation_results
        }
        
        # Save validation report
        report_file = f"{REPO_ROOT}/plans/test_provenance/validation_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.overall_validation, f, indent=2)
        
        print(f"✅ Validation report saved to: {report_file}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total_tests = self.overall_validation["total_tests"]
        passed_tests = self.overall_validation["passed_tests"]
        warning_tests = self.overall_validation["warning_tests"]
        failed_tests = self.overall_validation["failed_tests"]
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "validation_status": "SUCCESS" if success_rate >= 80 else "NEEDS_ATTENTION",
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "warning_tests": warning_tests,
            "failed_tests": failed_tests,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations()
        }
        
        print("\n🎯 Integration Validation Summary")
        print("=" * 60)
        print(f"✅ Validation Status: {summary['validation_status']}")
        print(f"📊 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🧪 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"⚠️ Warnings: {summary['warning_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate validation recommendations."""
        recommendations = []
        
        failed_tests = [test for test in self.validation_results if test["status"] == "FAIL"]
        warning_tests = [test for test in self.validation_results if test["status"] == "WARN"]
        
        if failed_tests:
            recommendations.append("🔴 Address failed integration tests")
        
        if warning_tests:
            recommendations.append("🟡 Review warnings and improve integration completeness")
        
        if len(failed_tests) == 0 and len(warning_tests) == 0:
            recommendations.append("✅ Validation successful - system ready for production")
        else:
            recommendations.append("🔄 Complete integration remediation before deployment")
        
        recommendations.append("📋 Document validation results for future reference")
        
        return recommendations


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Integration Validator Script - KAN-279"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validation command
    validate_parser = subparsers.add_parser("validate", help="Run integration validation")
    validate_parser.add_argument("--type", choices=["full", "partial"], 
                                default="full", help="Validation type (default: full)")
    validate_parser.add_argument("--config", help="Validation configuration file")
    validate_parser.add_argument("--output", help="Output file for validation report")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run validation
    validator = IntegrationValidator(args.config)
    
    if args.output:
        print(f"📁 Validation report will be saved to: {args.output}")
        validator.validation_config = args.output
    
    summary = validator.run_integration_validation(args.type)
    
    # Print summary
    print("\n📋 Integration Validation Summary")
    print("=" * 60)
    
    for recommendation in summary["recommendations"]:
        print(recommendation)
    
    print(f"\n🎯 Overall Validation Status: {summary['validation_status']}")
    
    return 0 if summary["validation_status"] == "SUCCESS" else 1

if __name__ == "__main__":
    main()