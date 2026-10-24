#!/usr/bin/env python3
"""Tests for AI code review agent and quality gate."""

import json
import tempfile
import subprocess
import os
from pathlib import Path


def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def test_ai_code_review_script_exists():
    """Test that ai_code_review.py script exists and is executable."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/ai_code_review.py")
    assert script_path.exists(), "ai_code_review.py should exist"
    assert os.access(script_path, os.X_OK), "ai_code_review.py should be executable"
    print("✅ ai_code_review.py exists and is executable")


def test_ai_code_review_help():
    """Test that ai_code_review.py shows help."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/ai_code_review.py")
    result = run_cmd(["python3", str(script_path), "--help"])
    assert result.returncode == 0, "Should show help successfully"
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
    print("✅ ai_code_review.py --help works")


def test_ai_code_review_basic():
    """Test basic AI review with a simple diff."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/ai_code_review.py")
    
    # Simple test diff
    test_diff = """diff --git a/test.py b/test.py
+def unsafe_eval(user_input):
+    return eval(user_input)
+
+def good_function():
+    return "hello"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as f:
        f.write(test_diff)
        diff_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--diff-file", diff_file,
            "--output", "json"
        ])
        
        # Should succeed (even if AI unavailable, should handle gracefully)
        assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"
        
        # If successful, should output valid JSON
        if result.returncode == 0:
            review = json.loads(result.stdout)
            assert "reviews" in review or "issues" in review or "summary" in review
            print("✅ AI review basic test passed")
        else:
            # If AI unavailable, should still handle gracefully
            print(f"⚠️ AI review returned {result.returncode} (may be expected if bridge unavailable)")
            
    finally:
        os.unlink(diff_file)


def test_quality_gate_script_exists():
    """Test that quality_gate.py script exists and is executable."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/quality_gate.py")
    assert script_path.exists(), "quality_gate.py should exist"
    assert os.access(script_path, os.X_OK), "quality_gate.py should be executable"
    print("✅ quality_gate.py exists and is executable")


def test_quality_gate_help():
    """Test that quality_gate.py shows help."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/quality_gate.py")
    result = run_cmd(["python3", str(script_path), "--help"])
    assert result.returncode == 0, "Should show help successfully"
    print("✅ quality_gate.py --help works")


def test_quality_gate_pass():
    """Test quality gate passes clean review."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/quality_gate.py")
    
    # Clean review result (no critical issues)
    clean_review = {
        "summary": {"total_issues": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
        "issues": [],
        "fix_suggestions": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(clean_review, f)
        review_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--review-file", review_file
        ])
        
        assert result.returncode == 0, "Clean review should pass quality gate"
        print("✅ Quality gate passes clean review")
        
    finally:
        os.unlink(review_file)


def test_quality_gate_fail_critical():
    """Test quality gate fails on critical issues."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/quality_gate.py")
    
    # Review with critical issue
    critical_review = {
        "summary": {"total_issues": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
        "issues": [
            {"severity": "critical", "category": "security", "message": "SQL injection vulnerability", "file": "test.py", "line": 10}
        ],
        "fix_suggestions": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(critical_review, f)
        review_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--review-file", review_file
        ])
        
        assert result.returncode == 1, "Critical issue should fail quality gate"
        print("✅ Quality gate fails on critical issues")
        
    finally:
        os.unlink(review_file)


def test_quality_gate_override():
    """Test quality gate can be overridden."""
    script_path = Path("/Users/kimlenglim/Project/HoroConsultant/scripts/quality_gate.py")
    
    # Review with critical issue but override flag
    critical_review = {
        "summary": {"total_issues": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
        "issues": [
            {"severity": "critical", "category": "security", "message": "Known false positive", "file": "test.py", "line": 10}
        ],
        "fix_suggestions": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(critical_review, f)
        review_file = f.name
    
    try:
        result = run_cmd([
            "python3", str(script_path),
            "--review-file", review_file,
            "--override"
        ])
        
        assert result.returncode == 0, "Override should pass quality gate"
        print("✅ Quality gate allows override")
        
    finally:
        os.unlink(review_file)


if __name__ == "__main__":
    # These tests SHOULD FAIL initially (RED phase)
    print("🔴 TDD RED Phase - Tests expected to fail")
    print("=" * 50)
    
    try:
        test_ai_code_review_script_exists()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_ai_code_review_help()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_ai_code_review_basic()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_quality_gate_script_exists()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_quality_gate_help()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_quality_gate_pass()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_quality_gate_fail_critical()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    try:
        test_quality_gate_override()
    except AssertionError as e:
        print(f"🔴 Expected failure: {e}")
    
    print("\n🔴 RED phase complete - all tests failed as expected")
    print("Next: Implement scripts to make tests pass (GREEN phase)")