"""TDD tests for MCP transport hardening (KAN-308 P0)."""

from __future__ import annotations

import pytest

from project.mcp_transport_hardening import (
    BoundedBuffer,
    BufferFullError,
    ColdStartTracker,
    CollectionTooLarge,
    FdBudget,
    FdBudgetExhausted,
    MAX_COLLECTION_SIZE,
    MAX_IN_FLIGHT,
    MAX_MESSAGE_SIZE,
    MAX_NESTING_DEPTH,
    MessageTooLarge,
    NestingTooDeep,
    OriginNotAllowed,
    SessionManager,
    SessionNotFound,
    redact_headers,
    validate_message,
    validate_nesting,
    validate_origin,
)

def test_constants():
    assert MAX_MESSAGE_SIZE == 4 * 1024 * 1024
    assert MAX_IN_FLIGHT == 64 * 1024 * 1024
    assert MAX_NESTING_DEPTH == 32
    assert MAX_COLLECTION_SIZE == 10000


def test_validate_message_accepts_within_cap():
    payload = b"x" * (4 * 1024 * 1024)
    validate_message(payload)  # no raise


def test_validate_message_rejects_oversized():
    payload = b"x" * (4 * 1024 * 1024 + 1)
    with pytest.raises(MessageTooLarge):
        validate_message(payload)


def test_validate_nesting_accepts_normal():
    obj = {"a": [1, 2, {"b": 3}], "c": "text"}
    validate_nesting(obj)


def test_validate_nesting_rejects_deep():
    obj = 1
    for _ in range(33):
        obj = [obj]
    with pytest.raises(NestingTooDeep):
        validate_nesting(obj)


def test_validate_nesting_rejects_huge_array():
    obj = [0] * 10001
    with pytest.raises(CollectionTooLarge):
        validate_nesting(obj)


def test_validate_nesting_rejects_huge_dict():
    obj = {str(i): i for i in range(10001)}
    with pytest.raises(CollectionTooLarge):
        validate_nesting(obj)


def test_buffer_per_message_cap():
    buf = BoundedBuffer()
    with pytest.raises(MessageTooLarge):
        buf.write(b"x" * (4 * 1024 * 1024 + 1))


def test_buffer_inflight_cap():
    buf = BoundedBuffer()
    chunk = b"x" * MAX_MESSAGE_SIZE
    for _ in range(MAX_IN_FLIGHT // MAX_MESSAGE_SIZE):
        buf.write(chunk)
    with pytest.raises(BufferFullError):
        buf.write(b"x")


def test_buffer_accepts_within_inflight():
    buf = BoundedBuffer()
    buf.write(b"x" * 1024)
    assert buf.in_flight >= 1024


def test_redact_authorization_case_insensitive():
    h = {"Authorization": "Bearer secret", "authorization": "Bearer other"}
    # dict can't have both; test single
    out = redact_headers({"Authorization": "Bearer secret"})
    assert out["Authorization"] == "***REDACTED***"


def test_redact_each_header_case_insensitive():
    headers = {
        "authorization": "a",
        "X-API-KEY": "b",
        "Mcp-Session-Token": "c",
        "COOKIE": "d",
    }
    out = redact_headers(headers)
    assert out["authorization"] == "***REDACTED***"
    assert out["X-API-KEY"] == "***REDACTED***"
    assert out["Mcp-Session-Token"] == "***REDACTED***"
    assert out["COOKIE"] == "***REDACTED***"


def test_redact_non_redacted_pass_through():
    headers = {"Content-Type": "application/json", "X-Request-Id": "123"}
    out = redact_headers(headers)
    assert out == headers
    assert out is not headers


def test_redact_does_not_mutate_input():
    headers = {"Authorization": "secret"}
    redact_headers(headers)
    assert headers["Authorization"] == "secret"


def test_validate_origin_accepts_loopback_hosts():
    assert validate_origin("http://127.0.0.1:8080") is True
    assert validate_origin("http://localhost") is True
    assert validate_origin("https://[::1]:9000") is True
    assert validate_origin("http://localhost/path") is True


def test_validate_origin_rejects_missing_empty():
    for val in (None, "", "   "):
        with pytest.raises(OriginNotAllowed):
            validate_origin(val)


def test_validate_origin_rejects_non_loopback():
    with pytest.raises(OriginNotAllowed):
        validate_origin("http://example.com")
    with pytest.raises(OriginNotAllowed):
        validate_origin("https://attacker.com:443")


def test_validate_origin_rejects_dns_rebinding():
    # host is not in allowlist even if it resolves to 127.0.0.1
    with pytest.raises(OriginNotAllowed):
        validate_origin("http://attacker.com")


def test_validate_origin_rejects_wrong_port_host():
    with pytest.raises(OriginNotAllowed):
        validate_origin("http://127.0.0.1.evil.com")


def test_session_manager_create_and_validity():
    sm = SessionManager()
    sid = sm.create_session()
    assert isinstance(sid, str) and sid
    assert sm.is_valid(sid) is True
    assert sm.is_valid("nope") is False
    assert sm.is_valid(None) is False


def test_session_manager_rotate():
    sm = SessionManager()
    sid = sm.create_session()
    new = sm.rotate_on_auth_change(sid)
    assert new != sid
    assert sm.is_valid(new) is True
    assert sm.is_valid(sid) is False


def test_session_manager_rotate_unknown_raises():
    sm = SessionManager()
    with pytest.raises(SessionNotFound):
        sm.rotate_on_auth_change("missing")


def test_fd_budget_basic():
    b = FdBudget()
    for i in range(8):
        assert b.acquire(f"s{i}") is True
    assert b.count() == 8
    with pytest.raises(FdBudgetExhausted):
        b.acquire("s9")
    b.release("s0")
    assert b.count() == 7
    assert b.acquire("s9") is True
    assert b.count() == 8


def test_fd_budget_custom_max():
    b = FdBudget(max_servers=2)
    b.acquire("a")
    b.acquire("b")
    with pytest.raises(FdBudgetExhausted):
        b.acquire("c")


def test_cold_start_tracker_cold_path():
    t = ColdStartTracker()
    t.mark_start()
    assert t.is_cold() is True
    assert t.timeout_for() == 120
    assert t.elapsed() >= 0


def test_cold_start_tracker_warm_path():
    t = ColdStartTracker()
    t.mark_start(now=0)  # epoch; elapsed huge
    # force elapsed beyond threshold by marking old start
    import time
    t.mark_start(now=time.time() - 200)
    assert t.is_cold() is False
    assert t.timeout_for() == 15


def test_cold_start_tracker_no_start():
    t = ColdStartTracker()
    assert t.is_cold() is False
    assert t.timeout_for() == 15
    assert t.elapsed() == 0.0


def test_sanitize_doc_index_payload_strips_patterns():
    from project.mcp_transport_hardening import sanitize_doc_index_payload
    text = "hi<script>alert(1)</script> x javascript:foo onmouseover=bar onclick=\"baz\" \x01"
    out = sanitize_doc_index_payload(text)
    assert "<script>" not in out
    assert "alert" not in out
    assert "javascript:" not in out
    assert "onmouseover=" not in out
    assert "onclick=" not in out
    assert "\x01" not in out


def test_add_verify_provenance():
    from project.mcp_transport_hardening import add_provenance, verify_provenance
    rec = add_provenance({"a": 1}, "src")
    assert set(rec) == {"payload", "source", "sha256", "timestamp"}
    assert rec["source"] == "src"
    assert verify_provenance(rec) is True
    rec["payload"] = {"a": 2}
    assert verify_provenance(rec) is False


def test_circuit_breaker_registry_threshold():
    from project.mcp_transport_hardening import CircuitBreakerRegistry
    r = CircuitBreakerRegistry()
    assert r.is_open("gemini:sse") is False
    r.record_failure("gemini:sse")
    r.record_failure("gemini:sse")
    assert r.is_open("gemini:sse") is False
    r.record_failure("gemini:sse")
    assert r.is_open("gemini:sse") is True
    # reset
    r.reset("gemini:sse")
    assert r.is_open("gemini:sse") is False


def test_circuit_breaker_registry_window_expiry():
    import time as _t
    from project.mcp_transport_hardening import CircuitBreakerRegistry
    r = CircuitBreakerRegistry()
    base = 1000.0
    r.record_failure("k", now=base)
    r.record_failure("k", now=base + 10)
    r.record_failure("k", now=base + 70)  # first expired
    assert r.is_open("k", now=base + 70) is False


def test_circuit_breaker_registry_open_duration():
    from project.mcp_transport_hardening import CircuitBreakerRegistry
    r = CircuitBreakerRegistry(open_duration=30)
    base = 1000.0
    for _ in range(3):
        r.record_failure("k", now=base)
    assert r.is_open("k", now=base + 10) is True
    assert r.is_open("k", now=base + 31) is False


def test_degradation_manager():
    from project.mcp_transport_hardening import DegradationManager
    d = DegradationManager()
    assert d.is_degraded("t") is False
    d.mark_degraded("t", "reason")
    assert d.is_degraded("t") is True
    assert "t" in d.list_degraded()
    d.clear("t")
    assert d.is_degraded("t") is False
    assert d.list_degraded() == []


def test_failover_guard():
    from project.mcp_transport_hardening import FailoverGuard
    g = FailoverGuard({"sse": 2, "stdio": 1})
    assert g.allow_failover("stdio", "sse") is True
    assert g.allow_failover("sse", "stdio") is False
    assert g.allow_failover("sse", "sse") is True
