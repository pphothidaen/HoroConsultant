"""Unit tests for code_reviewer.py Layered Review (Phase 2.1)."""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project.core.code_reviewer import LayeredCodeReviewer, run_layered_review


class TestLayeredReview:
    """Tests for Layer 1 Deterministic Surface Analysis."""

    def _write_temp(self, content: str) -> str:
        """Write temp file and return relative path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=ROOT) as f:
            f.write(content)
            return str(Path(f.name).relative_to(ROOT))

    def _cleanup(self, rel_path: str):
        abs_path = ROOT / rel_path
        if abs_path.exists():
            abs_path.unlink()

    def test_radon_cc_flags_high_complexity(self):
        """Test that radon detects functions with Cyclomatic Complexity >= 11."""
        rel_path = self._write_temp("""
def high_cc_func(a, b, c, d, e, f, g, h, i, j, k):  # CC = 12
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            if g:
                                if h:
                                    if i:
                                        if j:
                                            if k:
                                                return 1
    return 0
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-CC", mode="observation")
            exit_code, findings = reviewer.evaluate()

            cc_findings = [f for f in findings if f["tool"] == "radon_cc"]
            assert len(cc_findings) >= 1, f"Expected radon_cc finding, got: {findings}"
            assert cc_findings[0]["score"] >= 11, f"CC score should be >= 11, got {cc_findings[0]['score']}"
            assert cc_findings[0]["rank"] in ("C", "D", "E", "F"), f"Rank should be C+, got {cc_findings[0]['rank']}"
            print(f"✅ test_radon_cc_flags_high_complexity: Found CC={cc_findings[0]['score']}, Rank={cc_findings[0]['rank']}")
        finally:
            self._cleanup(rel_path)

    def test_bandit_flags_unsafe_subprocess(self):
        """Test that bandit detects unsafe subprocess with shell=True."""
        rel_path = self._write_temp("""
import subprocess

def unsafe_cmd(user_input):
    subprocess.run(user_input, shell=True)  # Bandit B602
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-BANDIT", mode="observation")
            exit_code, findings = reviewer.evaluate()

            bandit_findings = [f for f in findings if f["tool"] == "bandit"]
            # B602 varies by bandit version/context: can be LOW, MEDIUM, or HIGH
            assert len(bandit_findings) >= 1, f"Expected bandit finding, got: {findings}"
            assert bandit_findings[0]["severity"] in ("LOW", "MEDIUM", "HIGH"), f"Severity should be LOW/MEDIUM/HIGH, got {bandit_findings[0]['severity']}"
            assert "B602" in bandit_findings[0]["name"], f"Should be B602, got {bandit_findings[0]['name']}"
            print(f"✅ test_bandit_flags_unsafe_subprocess: Found {bandit_findings[0]['name']} severity={bandit_findings[0]['severity']}")
        finally:
            self._cleanup(rel_path)

    def test_bandit_flags_unsafe_eval(self):
        """Test that bandit detects unsafe eval()."""
        rel_path = self._write_temp("""
def unsafe_eval(user_input):
    return eval(user_input)  # Bandit B307
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-EVAL", mode="observation")
            exit_code, findings = reviewer.evaluate()

            bandit_findings = [f for f in findings if f["tool"] == "bandit"]
            assert len(bandit_findings) >= 1, f"Expected bandit finding for eval, got: {findings}"
            assert "B307" in bandit_findings[0]["name"], f"Should be B307, got {bandit_findings[0]['name']}"
            print(f"✅ test_bandit_flags_unsafe_eval: Found {bandit_findings[0]['name']} severity={bandit_findings[0]['severity']}")
        finally:
            self._cleanup(rel_path)

    def test_clean_code_passes(self):
        """Test that clean code passes without findings."""
        rel_path = self._write_temp("""
def clean_function(x: int) -> int:
    '''A simple clean function.'''
    return x * 2

class CleanClass:
    def method(self) -> str:
        return "hello"
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-CLEAN", mode="observation")
            exit_code, findings = reviewer.evaluate()

            assert exit_code == 0, f"Clean code should pass, got exit_code={exit_code}"
            assert len(findings) == 0, f"Clean code should have no findings, got: {findings}"
            print("✅ test_clean_code_passes: No findings for clean code")
        finally:
            self._cleanup(rel_path)

    def test_bandit_flags_pickle_medium(self):
        """Test that bandit detects unsafe pickle (MEDIUM severity)."""
        rel_path = self._write_temp("""
import pickle

def unsafe_pickle(data):
    return pickle.loads(data)  # Bandit B301 - MEDIUM
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-PICKLE", mode="observation")
            exit_code, findings = reviewer.evaluate()

            bandit_findings = [f for f in findings if f["tool"] == "bandit"]
            assert len(bandit_findings) >= 1, f"Expected bandit finding for pickle, got: {findings}"
            assert bandit_findings[0]["severity"] == "MEDIUM", f"Severity should be MEDIUM, got {bandit_findings[0]['severity']}"
            assert "B301" in bandit_findings[0]["name"], f"Should be B301, got {bandit_findings[0]['name']}"
            print(f"✅ test_bandit_flags_pickle_medium: Found {bandit_findings[0]['name']} severity={bandit_findings[0]['severity']}")
        finally:
            self._cleanup(rel_path)

    def test_enforce_mode_blocks_on_medium(self):
        """Test that enforce mode returns exit_code=1 on MEDIUM/HIGH findings."""
        rel_path = self._write_temp("""
import pickle

def unsafe_pickle(data):
    return pickle.loads(data)  # Bandit B301 - MEDIUM severity
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-ENFORCE", mode="enforce")
            exit_code, findings = reviewer.evaluate()

            assert exit_code == 1, f"Enforce mode should block on MEDIUM, got exit_code={exit_code}"
            print("✅ test_enforce_mode_blocks_on_medium: Enforce mode correctly blocks")
        finally:
            self._cleanup(rel_path)

    def test_observation_mode_allows_medium(self):
        """Test that observation mode returns exit_code=0 even with MEDIUM findings."""
        rel_path = self._write_temp("""
import pickle

def unsafe_pickle(data):
    return pickle.loads(data)  # Bandit B301 - MEDIUM severity
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-OBS", mode="observation")
            exit_code, findings = reviewer.evaluate()

            assert exit_code == 0, f"Observation mode should not block, got exit_code={exit_code}"
            assert len(findings) >= 1, "Should still report findings in observation mode"
            print("✅ test_observation_mode_allows_medium: Observation mode allows with warning")
        finally:
            self._cleanup(rel_path)

    def test_findings_cap(self):
        """Test that findings are capped at MAX_FINDINGS_CAP (8)."""
        # Create file with many bandit MEDIUM issues (pickle)
        issues = "\n".join([f"        pickle.loads(b'data{i}')" for i in range(15)])
        rel_path = self._write_temp(f"""
import pickle

def many_issues():
{issues}
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-CAP", mode="observation")
            exit_code, findings = reviewer.evaluate()

            # Should cap at 8
            assert len(findings) <= 8, f"Findings should be capped at 8, got {len(findings)}"
            print(f"✅ test_findings_cap: Capped at {len(findings)} findings (max 8)")
        finally:
            self._cleanup(rel_path)

    def test_telemetry_recording(self):
        """Test that findings are recorded to telemetry."""
        rel_path = self._write_temp("""
import pickle
pickle.loads(b'test')
""")
        try:
            reviewer = LayeredCodeReviewer([rel_path], ticket_id="TEST-TELEMETRY", mode="observation")
            exit_code, findings = reviewer.evaluate()

            # Verify in database
            import sqlite3
            conn = sqlite3.connect(ROOT / "metrics" / "ai_sdlc_metrics.db")
            cur = conn.cursor()
            cur.execute("""
                SELECT ticket_id, finding_type, severity, file_path, line_number, message
                FROM ai_reviewer_signals
                WHERE ticket_id = 'TEST-TELEMETRY'
                ORDER BY id DESC LIMIT 1
            """)
            row = cur.fetchone()
            conn.close()

            assert row is not None, "Telemetry should be recorded"
            assert row[0] == "TEST-TELEMETRY", f"Ticket ID mismatch: {row[0]}"
            assert row[1] == "security", f"Finding type should be security: {row[1]}"
            assert row[2] == "medium", f"Severity should be medium: {row[2]}"
            assert row[3] is not None, f"File path should be recorded: {row[3]}"
            print(f"✅ test_telemetry_recording: Recorded in DB - {row}")
        finally:
            self._cleanup(rel_path)


if __name__ == "__main__":
    test = TestLayeredReview()
    test.test_radon_cc_flags_high_complexity()
    test.test_bandit_flags_unsafe_subprocess()
    test.test_bandit_flags_unsafe_eval()
    test.test_bandit_flags_pickle_medium()
    test.test_clean_code_passes()
    test.test_enforce_mode_blocks_on_medium()
    test.test_observation_mode_allows_medium()
    test.test_findings_cap()
    test.test_telemetry_recording()
    print("\n✅ All Layered Review tests passed!")
