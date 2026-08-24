"""Regression tests for Horo v3.0 consensus and audit metrics."""

from __future__ import annotations

from project.core import observability


def test_v3_metrics_update_internal_registries(monkeypatch):
    monkeypatch.setattr(observability, "PROMETHEUS_CLIENT_AVAILABLE", False)
    collector = observability.MetricsCollector()

    collector.record_v3_emission_metric("BaZi", count=3)
    collector.record_v3_arbitration_metric("STRATEGIC_TIMING_ACTION", 0.25, veto_count=1)
    collector.record_v3_audit_metric("AUDIT_PASS", lciw=0.91, rniw=0.04)

    assert collector._v3_emissions == {"BaZi": 3}
    assert collector._v3_arbitrations == {("STRATEGIC_TIMING_ACTION", "true"): 1}
    assert collector._v3_arbitration_count == 1
    assert collector._v3_arbitration_seconds_sum == 0.25
    assert collector._v3_lciw_latest == 0.91
    assert collector._v3_rniw_latest == 0.04
    assert collector._v3_audit_verdicts == {"AUDIT_PASS": 1}


def test_v3_metrics_are_exported(monkeypatch):
    monkeypatch.setattr(observability, "PROMETHEUS_CLIENT_AVAILABLE", False)
    collector = observability.MetricsCollector()
    collector.record_v3_emission_metric("QiMen")
    collector.record_v3_arbitration_metric("RISK_MITIGATION", 1.5)
    collector.record_v3_audit_metric("AUDIT_FAIL_RECOMPUTE", 0.62, 0.31)

    text = collector.generate_metrics_text()
    assert 'horo_v3_emissions_total{domain="QiMen"} 1' in text
    assert 'horo_v3_arbitrations_total{intent="RISK_MITIGATION",veto_applied="false"} 1' in text
    assert "horo_v3_arbitration_seconds_count 1" in text
    assert "horo_v3_arbitration_seconds_sum 1.500000" in text
    assert "horo_v3_lciw_latest 0.62" in text
    assert "horo_v3_rniw_latest 0.31" in text
    assert 'horo_v3_audit_verdicts_total{verdict="AUDIT_FAIL_RECOMPUTE"} 1' in text


def test_module_prometheus_generation_alias(monkeypatch):
    monkeypatch.setattr(observability, "PROMETHEUS_CLIENT_AVAILABLE", False)
    observability.observability_manager.clear_metrics()
    observability.observability_manager.record_v3_emission_metric("TaiYi")

    assert "horo_v3_emissions_total" in observability.generate_prometheus_metrics()
