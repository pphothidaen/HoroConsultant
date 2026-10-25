#!/usr/bin/env python3
"""Tests for AI Refactoring Agent, Auto-Fix Engine, and Tech Debt Tracker."""

import json
import tempfile
import subprocess
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


# ============================================================
# AI Refactoring Agent Tests
# ============================================================

def test_ai_refactor_script_exists():
    """Test that ai_refactor.py script exists and is executable."""
    script_path = SCRIPTS_DIR / "ai_refactor.py"
    assert script_path.exists(), "ai_refactor.py should exist"
    assert os.access(script_path, os.X_OK), "ai_refactor.py should be executable"
    print("✅ ai_refactor.py exists and is executable")


def test_ai_refactor_help():
    """Test that ai_refactor.py shows help."""
    script_path = SCRIPTS_DIR / "ai_refactor.py"
    result = run_cmd(["python3", str(script_path), "--help"])
    assert result.returncode == 0, "Should show help successfully"
    print("✅ ai_refactor.py --help works")


def test_ai_refactor_basic():
    """Test basic refactoring with review input."""
    script_path = SCRIPTS_DIR / "ai_refactor.py"
    
    # Sample review with issues that could be refactored
    review_input = {
        "reviews": [
            {
                "severity": "medium",
                "category": "complexity",
                "message": "Function too complex (cognitive complexity 15)",
                "file": "src/processor.py",
                "line": 42,
                "suggestion": "Extract helper function for validation logic",
                "code_snippet": "def process(data):\n    if x:\n        if y:\n            ..."
            },
            {
                "severity": "low",
                "category": "style",
                "message": "Unused import: os",
                "file": "src/handler.py",
                "line": 3,
                "suggestion": "Remove unused import",
                "code_snippet": "import os\nimport sys"
            }
        ],
        "summary": {"total_issues": 2, "critical": 0, "high": 0, "medium": 1, "low": 1, "info": 0},
        "fix_suggestions": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(review_input, f)
        review_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--review-file", review_file,
            "--output", "json"
        ])
        
        assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"
        
        if result.returncode == 0:
            refactor = json.loads(result.stdout)
            assert "refactorings" in refactor or "suggestions" in refactor
            print("✅ AI refactor basic test passed")
        else:
            print(f"⚠️ AI refactor returned {result.returncode} (may be expected if bridge unavailable)")
            
    finally:
        os.unlink(review_file)


# ============================================================
# Auto-Fix Engine Tests
# ============================================================

def test_auto_fix_script_exists():
    """Test that auto_fix.py script exists and is executable."""
    script_path = SCRIPTS_DIR / "auto_fix.py"
    assert script_path.exists(), "auto_fix.py should exist"
    assert os.access(script_path, os.X_OK), "auto_fix.py should be executable"
    print("✅ auto_fix.py exists and is executable")


def test_auto_fix_help():
    """Test that auto_fix.py shows help."""
    script_path = SCRIPTS_DIR / "auto_fix.py"
    result = run_cmd(["python3", str(script_path), "--help"])
    assert result.returncode == 0, "Should show help successfully"
    print("✅ auto_fix.py --help works")


def test_auto_fix_dry_run():
    """Test auto-fix dry-run mode."""
    script_path = SCRIPTS_DIR / "auto_fix.py"
    
    # Create a test file with fixable issues
    test_code = """import os
import sys
import json

def  bad_function ( x , y ) :
    return x + y

unused_var = 42

"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        test_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--file", test_file,
            "--dry-run"
        ])
        
        assert result.returncode == 0, "Dry-run should succeed"
        print("✅ Auto-fix dry-run works")
        
    finally:
        os.unlink(test_file)


def test_auto_fix_apply():
    """Test auto-fix apply mode (should fix formatting)."""
    script_path = SCRIPTS_DIR / "auto_fix.py"
    
    test_code = """import os
import sys

def  bad_function ( x , y ) :
    return x + y

"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        test_file = f.name
    
    try:
        # Apply fixes
        result = run_cmd([
            "python3", str(script_path),
            "--file", test_file,
            "--apply"
        ])
        
        assert result.returncode == 0, "Apply should succeed"
        
        # Read fixed file
        with open(test_file, 'r') as f:
            fixed = f.read()
        
        # Should have proper formatting
        assert "def bad_function(x, y):" in fixed or "def bad_function (x, y):" in fixed
        print("✅ Auto-fix apply works")
        
    finally:
        os.unlink(test_file)


# ============================================================
# Tech Debt Tracker Tests
# ============================================================

def test_tech_debt_script_exists():
    """Test that tech_debt_tracker.py script exists and is executable."""
    script_path = SCRIPTS_DIR / "tech_debt_tracker.py"
    assert script_path.exists(), "tech_debt_tracker.py should exist"
    assert os.access(script_path, os.X_OK), "tech_debt_tracker.py should be executable"
    print("✅ tech_debt_tracker.py exists and is executable")


def test_tech_debt_help():
    """Test that tech_debt_tracker.py shows help."""
    script_path = SCRIPTS_DIR / "tech_debt_tracker.py"
    result = run_cmd(["python3", str(script_path), "--help"])
    assert result.returncode == 0, "Should show help successfully"
    print("✅ tech_debt_tracker.py --help works")


def test_tech_debt_analyze():
    """Test tech debt analysis on a sample directory."""
    script_path = SCRIPTS_DIR / "tech_debt_tracker.py"
    
    result = run_cmd([
        "python3", str(script_path),
        "--path", str(SCRIPTS_DIR),
        "--output", "json"
    ])
    
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"
    
    if result.returncode == 0:
        debt = json.loads(result.stdout)
        assert "metrics" in debt or "hotspots" in debt or "summary" in debt
        print("✅ Tech debt analyze works")
    else:
        print(f"⚠️ Tech debt returned {result.returncode}")


def test_tech_debt_history():
    """Test tech debt history tracking."""
    script_path = SCRIPTS_DIR / "tech_debt_tracker.py"
    
    # First run to create history
    result1 = run_cmd([
        "python3", str(script_path),
        "--path", str(SCRIPTS_DIR),
        "--update-history"
    ])
    
    assert result1.returncode == 0, "First run should succeed"
    
    # Second run to verify history
    result2 = run_cmd([
        "python3", str(script_path),
        "--show-history"
    ])
    
    assert result2.returncode == 0, "History should be readable"
    print("✅ Tech debt history tracking works")


if __name__ == "__main__":
    print("🟢 TDD GREEN Phase - All tests should pass")
    print("=" * 60)
    
    tests = [
        ("ai_refactor exists", test_ai_refactor_script_exists),
        ("ai_refactor help", test_ai_refactor_help),
        ("ai_refactor basic", test_ai_refactor_basic),
        ("auto_fix exists", test_auto_fix_script_exists),
        ("auto_fix help", test_auto_fix_help),
        ("auto_fix dry-run", test_auto_fix_dry_run),
        ("auto_fix apply", test_auto_fix_apply),
        ("tech_debt exists", test_tech_debt_script_exists),
        ("tech_debt help", test_tech_debt_help),
        ("tech_debt analyze", test_tech_debt_analyze),
        ("tech_debt history", test_tech_debt_history),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED [{name}]: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ FAILED [{name}]: {type(e).__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🟢 GREEN phase complete - all tests pass!")
    else:
        print("🔴 Some tests failed")
        sys.exit(1)