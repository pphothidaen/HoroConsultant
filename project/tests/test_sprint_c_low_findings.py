"""TDD tests for Sprint C — LOW severity findings (C1-C4)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (ROOT / "project/validator.py").read_text()
API_ROUTER = (ROOT / "project/api_router.py").read_text()
README_TEXT = (ROOT / "README.md").read_text(encoding="utf-8")
SOLAR_TIME = (ROOT / "project/core/solar_time.py").read_text()


class TestValidatorModelSpecificity:
    """C1 — D1.6: validator.py default model too vague."""
    def test_default_model_is_specific(self):
        assert 'gemini-2.0-flash' not in VALIDATOR, (
            "validator.py uses 'gemini-2.0-flash' — must match current rotation (gemini-2.5-flash)."
        )

    def test_model_candidates_are_current(self):
        match = re.search(r'for alt in \[(.*?)\]', VALIDATOR, re.DOTALL)
        assert match, "Could not find model candidates list in validator.py"
        cands = match.group(0)
        assert 'gemini-2.0' not in cands, (
            "validator.py model candidates should not include 'gemini-2.0'."
        )


class TestNoDeadCode:
    """C2 — D3.4: AI_ZERO_COST_ONLY dead code."""
    def test_no_dead_ai_zero_cost_only(self):
        matches = re.findall(r'AI_ZERO_COST_ONLY', API_ROUTER)
        assert len(matches) < 2, (
            "AI_ZERO_COST_ONLY appears 2+ times — extract to constant."
        )
        if matches:
            assert 'os.environ[' in API_ROUTER, (
                "AI_ZERO_COST_ONLY referenced but os.environ[ not used for access."
            )


class TestHITLDiagramZodiac:
    """C3 — D4.8: README HITL diagram omits zodiac wheel SVG."""
    def test_hitl_diagram_includes_zodiac(self):
        hitl_start = README_TEXT.find('participant HITLUI')
        hitl_section = README_TEXT[hitl_start:] if hitl_start >= 0 else ""
        assert 'zodiac' in hitl_section.lower(), (
            "HITL sequence diagram should include zodiac wheel SVG step."
        )


class TestTSTDecimalPrecision:
    """C4 — D4.9: TST uses float arithmetic → sub-second errors."""
    def test_uses_decimal_for_lmt(self):
        assert 'from decimal import' in SOLAR_TIME or 'Decimal(' in SOLAR_TIME, (
            "solar_time.py should use Decimal for LMT computation."
        )

    def test_lmt_rounds_before_timedelta(self):
        lmt_section = re.search(
            r'def calculate_true_solar_time.*?timedelta.*?timedelta',
            SOLAR_TIME,
            re.DOTALL,
        )
        assert lmt_section, "Could not find LMT computation section"
        assert 'round(' in lmt_section.group(0), (
            "LMT should round before passing to timedelta."
        )
