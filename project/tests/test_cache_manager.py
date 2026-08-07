"""
project/tests/test_cache_manager.py
===================================
Unit tests for RuntimeCacheManager (Track B Caching Layer).
"""

from __future__ import annotations

from project.core.cache_manager import RuntimeCacheManager


def test_cache_set_and_get():
    cache = RuntimeCacheManager(ttl_seconds=60)
    key_input = {"birth_datetime": "1990-05-15 14:30:00", "longitude": 100.4930}
    val = {"status": "ok", "day_master": "Bing Fire"}

    cache.set(key_input, val)
    retrieved = cache.get(key_input)

    assert retrieved is not None
    assert retrieved["day_master"] == "Bing Fire"


def test_cache_miss():
    cache = RuntimeCacheManager(ttl_seconds=60)
    key_input = {"non_existent_key": 12345}
    assert cache.get(key_input) is None


def test_cache_clear():
    cache = RuntimeCacheManager(ttl_seconds=60)
    key_input = {"test_key": "clear_me"}
    cache.set(key_input, {"data": "test"})
    cache.clear()

    assert cache.get(key_input) is None
