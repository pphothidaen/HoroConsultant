#!/usr/bin/env python3
"""Contract test for CODEOWNERS file validation.

RED test - should fail initially, then pass after CODEOWNERS is added.
"""
import subprocess
import pytest


def test_codeowners_file_exists():
    """Assert CODEOWNERS file exists."""
    import os
    assert os.path.exists(".github/CODEOWNERS"), "CODEOWNERS file must exist at .github/CODEOWNERS"


def test_codeowners_has_valid_syntax():
    """Assert CODEOWNERS has valid syntax - at least one owner pattern."""
    with open(".github/CODEOWNERS", "r") as f:
        content = f.read().strip()
    
    # Should have at least one non-comment line with an owner
    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
    assert len(lines) > 0, "CODEOWNERS must have at least one pattern with owners"
    
    # Each line should have @ for owners
    for line in lines:
        assert '@' in line, f"CODEOWNERS line must have @ owners: {line}"


def test_codeowners_covers_critical_paths():
    """Assert CODEOWNERS covers critical paths."""
    with open(".github/CODEOWNERS", "r") as f:
        content = f.read()
    
    critical_paths = [
        ".github/",
        "scripts/",
        "tests/",
        "docs/",
        "packages/"
    ]
    
    for path in critical_paths:
        # Check if path or * is covered
        assert path in content or '*' in content, f"CODEOWNERS must cover {path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])