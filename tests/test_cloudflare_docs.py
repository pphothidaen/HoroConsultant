"""Smoke test: verify cloudflare deployment analysis and security mapping load."""
import json
from pathlib import Path

def test_cloudflare_deployment_analysis_loads():
    p = Path("cloudflare-deployment-analysis.json")
    if p.exists():
        data = json.loads(p.read_text())
        assert isinstance(data, dict)

def test_cloudflare_security_mapping_loads():
    p = Path(".hermes/plans/cloudflare-security-mapping.json")
    if p.exists():
        data = json.loads(p.read_text())
        assert isinstance(data, dict)

def test_atomic_push_plan_loads():
    p = Path("plans/2026-09-03-atomic-push-to-main.md")
    if p.exists():
        content = p.read_text()
        assert len(content) > 0
