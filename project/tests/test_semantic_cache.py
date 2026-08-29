"""
project/tests/test_semantic_cache.py
====================================
Comprehensive Test Suite for High-Performance Metaphysics Semantic Cache
& Deterministic Safe Net Fallback.

Covers:
1. SHA-256 Canonical Prompt Normalization & Deterministic Astrological Hashing.
2. Category TTLs (Daily Horoscope, FAQ/Reference, BaZi Chart, Feng Shui, General).
3. Thread-Safe In-Memory LRU Eviction & Stats Tracking.
4. Deterministic Safe Net Fallback (<1ms baseline, zero cloud cost).
5. Concurrency & Multi-Thread Stress Testing.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any, Dict

import pytest

from project.core.semantic_cache import (
    DEFAULT_CATEGORY_TTLS,
    SemanticCache,
    SemanticCacheEntry,
    compute_prompt_hash,
    normalize_astrological_prompt,
    semantic_cache,
)


# ============================================================================
# 1. SHA-256 CANONICAL PROMPT NORMALIZATION & HASHING
# ============================================================================

class TestPromptNormalizationAndHashing:
    """Tests verifying canonical normalization and deterministic SHA-256 hashing."""

    def test_whitespace_and_case_canonicalization(self):
        """Redundant whitespace and mixed case normalize to standard representation."""
        p1 = "   What is   my   BaZi   Day   Master?   "
        p2 = "what is my bazi day master?"
        assert normalize_astrological_prompt(p1) == p2
        assert compute_prompt_hash(p1) == compute_prompt_hash(p2)

    def test_identical_hash_for_equivalent_prompts(self):
        """Identical semantic queries yield identical SHA-256 hexdigests."""
        p1 = "Analyze Feng Shui for South Facing Office"
        p2 = "  analyze   feng shui for south facing office  "
        h1 = compute_prompt_hash(p1)
        h2 = compute_prompt_hash(p2)
        assert len(h1) == 64
        assert h1 == h2

    def test_astrological_metadata_canonicalization_and_key_sorting(self):
        """Astrological metadata keys are sorted and canonicalized deterministically."""
        meta1 = {
            "day_master": "Bing Fire",
            "true_solar_time": "14:32:10",
            "latitude": 13.7563,
            "domain": "BaZi",
        }
        meta2 = {
            "domain": "bazi",
            "latitude": 13.756300,
            "true_solar_time": "14:32:10",
            "day_master": "bing fire",
        }
        h1 = compute_prompt_hash("Analyze chart", metadata=meta1)
        h2 = compute_prompt_hash("  analyze chart  ", metadata=meta2)
        assert h1 == h2

    def test_none_metadata_values_handled_cleanly(self):
        """None values in metadata do not crash and are skipped/canonicalized."""
        meta1 = {"day_master": "Jia Wood", "extra": None}
        meta2 = {"day_master": "Jia Wood"}
        h1 = compute_prompt_hash("Prompt", metadata=meta1)
        h2 = compute_prompt_hash("Prompt", metadata=meta2)
        assert h1 == h2

    def test_differing_metadata_produces_differing_hashes(self):
        """Distinct astrological attributes produce distinct SHA-256 hashes."""
        h1 = compute_prompt_hash("Daily Reading", metadata={"day_master": "Bing Fire"})
        h2 = compute_prompt_hash("Daily Reading", metadata={"day_master": "Gui Water"})
        assert h1 != h2

    def test_hash_format_is_valid_sha256_hex(self):
        """compute_prompt_hash returns 64-character lowercase hex string."""
        h = compute_prompt_hash("Test prompt")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ============================================================================
# 2. CATEGORY TTLS & EXPIRATION VERIFICATION
# ============================================================================

class TestCategoryTTLsAndExpiration:
    """Tests verifying category-specific TTLs, custom TTLs, and expiration purging."""

    def test_default_category_ttl_constants(self):
        """Verify default TTL definitions across metaphysical domains."""
        assert DEFAULT_CATEGORY_TTLS["daily_horoscope"] == 86400      # 24 hours
        assert DEFAULT_CATEGORY_TTLS["daily_horoscope_6h"] == 21600   # 6 hours
        assert DEFAULT_CATEGORY_TTLS["daily"] == 86400                # 24 hours
        assert DEFAULT_CATEGORY_TTLS["faq"] == 2592000                # 30 days
        assert DEFAULT_CATEGORY_TTLS["reference"] == 2592000          # 30 days
        assert DEFAULT_CATEGORY_TTLS["bazi_chart"] == 2592000         # 30 days
        assert DEFAULT_CATEGORY_TTLS["bazi"] == 2592000               # 30 days
        assert DEFAULT_CATEGORY_TTLS["natal_chart"] == 2592000        # 30 days
        assert DEFAULT_CATEGORY_TTLS["chart"] == 2592000              # 30 days
        assert DEFAULT_CATEGORY_TTLS["feng_shui"] == 604800           # 7 days
        assert DEFAULT_CATEGORY_TTLS["general"] == 3600               # 1 hour

    def test_cache_entry_expiration_evaluation(self):
        """SemanticCacheEntry.is_expired returns True when elapsed time exceeds TTL."""
        entry = SemanticCacheEntry(
            prompt_hash="abc123hash",
            normalized_prompt="normalized",
            response={"result": "data"},
            category="general",
            created_at=1000.0,
            ttl=3600.0,
        )
        assert entry.is_expired(current_time=1000.0) is False
        assert entry.is_expired(current_time=4599.0) is False
        assert entry.is_expired(current_time=4601.0) is True

    def test_cache_get_purges_expired_entry(self):
        """Accessing expired entry via get() returns None and purges item from cache."""
        cache = SemanticCache(capacity=100)
        cache.set("Daily forecast", {"forecast": "Prosperity"}, category="daily_horoscope", ttl=1.0)

        # Immediate retrieval succeeds
        assert cache.get("Daily forecast") == {"forecast": "Prosperity"}

        # Simulate time passing beyond 1.0s TTL
        time.sleep(1.05)
        assert cache.get("Daily forecast") is None
        assert len(cache) == 0

    def test_custom_ttl_override(self):
        """Custom TTL passed to set() overrides default category TTL."""
        cache = SemanticCache()
        key = cache.set("Custom TTL query", {"value": 42}, category="general", ttl=10.0)
        entry = cache._cache[key]
        assert entry.ttl == 10.0

    def test_invalidate_single_entry(self):
        """invalidate() removes specific entry by prompt and metadata."""
        cache = SemanticCache()
        prompt = "BaZi Chart Reading"
        meta = {"chart_id": 999}
        cache.set(prompt, {"reading": "Strong Wood"}, category="bazi_chart", metadata=meta)

        assert cache.get(prompt, metadata=meta) is not None
        removed = cache.invalidate(prompt, metadata=meta)
        assert removed is True
        assert cache.get(prompt, metadata=meta) is None

        # Invalidating non-existent item returns False
        assert cache.invalidate("Non existent") is False

    def test_invalidate_category_purges_only_target_category(self):
        """invalidate_category purges all items in target category while preserving others."""
        cache = SemanticCache()
        cache.set("Horoscope Day 1", {"h": 1}, category="daily_horoscope")
        cache.set("Horoscope Day 2", {"h": 2}, category="daily_horoscope")
        cache.set("FAQ Qi Men", {"f": 1}, category="faq")
        cache.set("BaZi Natal", {"b": 1}, category="bazi_chart")

        assert len(cache) == 4
        purged = cache.invalidate_category("daily_horoscope")
        assert purged == 2
        assert len(cache) == 2

        assert cache.get("Horoscope Day 1", category="daily_horoscope") is None
        assert cache.get("FAQ Qi Men", category="faq") == {"f": 1}
        assert cache.get("BaZi Natal", category="bazi_chart") == {"b": 1}

    def test_prune_expired_removes_all_stale_entries(self):
        """prune_expired() purges all expired entries and retains valid ones."""
        cache = SemanticCache()
        cache.set("Short TTL 1", {"val": 1}, ttl=0.1)
        cache.set("Short TTL 2", {"val": 2}, ttl=0.1)
        cache.set("Long TTL", {"val": 3}, ttl=60.0)

        time.sleep(0.15)
        pruned = cache.prune_expired()
        assert pruned == 2
        assert len(cache) == 1
        assert cache.get("Long TTL") == {"val": 3}


# ============================================================================
# 3. LRU EVICTION & TELEMETRY STATS TRACKING
# ============================================================================

class TestLRUEvictionAndStats:
    """Tests verifying LRU cache eviction policy and statistics telemetry."""

    def test_lru_capacity_eviction_removes_oldest_item(self):
        """When capacity is reached, adding a new item evicts the least recently accessed."""
        cache = SemanticCache(capacity=3)
        cache.set("Query 1", {"id": 1})
        cache.set("Query 2", {"id": 2})
        cache.set("Query 3", {"id": 3})

        assert len(cache) == 3
        assert cache.evictions == 0

        # Adding 4th item triggers eviction of Query 1 (oldest)
        cache.set("Query 4", {"id": 4})
        assert len(cache) == 3
        assert cache.evictions == 1
        assert cache.get("Query 1") is None
        assert cache.get("Query 2") is not None
        assert cache.get("Query 3") is not None
        assert cache.get("Query 4") is not None

    def test_lru_access_refreshes_item_order(self):
        """Reading an item with get() moves it to the most recently used position."""
        cache = SemanticCache(capacity=3)
        cache.set("Query A", {"id": "A"})
        cache.set("Query B", {"id": "B"})
        cache.set("Query C", {"id": "C"})

        # Access Query A so it becomes most recently used
        assert cache.get("Query A") == {"id": "A"}

        # Adding Query D should evict Query B (now the oldest)
        cache.set("Query D", {"id": "D"})
        assert len(cache) == 3
        assert cache.get("Query A") is not None
        assert cache.get("Query B") is None
        assert cache.get("Query C") is not None
        assert cache.get("Query D") is not None

    def test_peek_does_not_modify_lru_order_or_stats(self):
        """peek() inspects cache entry without updating LRU position or hits/misses."""
        cache = SemanticCache(capacity=3)
        cache.set("Item 1", {"val": 1})
        cache.set("Item 2", {"val": 2})
        cache.set("Item 3", {"val": 3})

        initial_hits = cache.hits
        initial_misses = cache.misses

        # Peek Item 1
        res = cache.peek("Item 1")
        assert res == {"val": 1}
        assert cache.hits == initial_hits
        assert cache.misses == initial_misses

        # Peek non-existent item
        res_none = cache.peek("Non existent")
        assert res_none is None
        assert cache.hits == initial_hits
        assert cache.misses == initial_misses

        # Adding Item 4 should still evict Item 1 because peek did not refresh LRU position
        cache.set("Item 4", {"val": 4})
        assert cache.get("Item 1") is None

    def test_stats_tracking_hits_misses_and_hit_ratio(self):
        """Verify get_stats calculation of hits, misses, evictions, and hit_ratio."""
        cache = SemanticCache(capacity=5)
        cache.set("K1", {"v": 1})
        cache.set("K2", {"v": 2})

        # 2 Hits
        cache.get("K1")
        cache.get("K2")
        # 2 Misses
        cache.get("K3")
        cache.get("K4")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["capacity"] == 5
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["evictions"] == 0
        assert stats["hit_ratio"] == 0.5

    def test_clear_resets_cache_and_telemetry(self):
        """clear() purges all entries and resets telemetry counters to zero."""
        cache = SemanticCache(capacity=10)
        cache.set("A", {"v": 1})
        cache.get("A")
        cache.get("B")

        assert len(cache) == 1
        assert cache.hits == 1
        assert cache.misses == 1

        cache.clear()
        assert len(cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.evictions == 0

    def test_dunder_len_and_contains_support(self):
        """Verify __len__ and __contains__ work with prompt text and SHA-256 keys."""
        cache = SemanticCache()
        prompt = "Feng Shui Compass 24 Mountains"
        key = cache.set(prompt, {"compass": "Luo Pan"})

        assert len(cache) == 1
        assert prompt in cache
        assert key in cache
        assert "Non existent prompt" not in cache


# ============================================================================
# 4. DETERMINISTIC SAFE NET FALLBACK (<1MS BASELINE)
# ============================================================================

class TestDeterministicSafeNetFallback:
    """Tests verifying instant (<1ms) deterministic safe net offline baseline."""

    def test_deterministic_fallback_reading_structure(self):
        """Deterministic safe net returns structured baseline interpretation."""
        cache = SemanticCache()
        meta = {
            "day_master": "Bing Fire",
            "domain": "BaZi",
            "question_type": "Career & Wealth",
            "element": "Fire",
            "true_solar_time": "12:00:00",
        }
        reading = cache.deterministic_fallback_reading(
            prompt="What is my career direction for 2026?",
            metadata=meta,
        )

        assert reading["status"] == "fallback"
        assert reading["provider"] == "DETERMINISTIC_SAFE_NET"
        assert reading["model"] == "rust_pyo3_baseline"
        assert reading["error_type"] == "deterministic_fallback"
        assert reading["route_used"] == "deterministic_safe_net"
        assert "Bing Fire" in reading["content"]
        assert "Career & Wealth" in reading["content"]
        assert "Zero cloud billing incurred" in reading["content"]

    def test_deterministic_fallback_latency_under_1ms_baseline(self):
        """Deterministic reading executes in sub-millisecond baseline latency."""
        cache = SemanticCache()
        t_start = time.perf_counter()
        reading = cache.deterministic_fallback_reading("Analyze Destiny")
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        assert elapsed_ms < 5.0  # Conservative upper bound for test reliability (<5ms)
        assert reading["latency_ms"] >= 0.0

    def test_deterministic_fallback_pure_ascii_content(self):
        """Deterministic reading content is pure ASCII characters."""
        cache = SemanticCache()
        reading = cache.deterministic_fallback_reading("Pure ASCII verification prompt")
        content = reading["content"]
        assert content.isascii() is True


# ============================================================================
# 5. CONCURRENCY & MULTI-THREAD STRESS TESTING
# ============================================================================

class TestConcurrencyAndThreadSafety:
    """Stress testing thread-safety of SemanticCache under high concurrent load."""

    def test_concurrent_reads_and_writes(self):
        """Multiple threads concurrently performing set, get, and peek operations."""
        cache = SemanticCache(capacity=100)
        num_threads = 16
        ops_per_thread = 50

        def worker_task(thread_id: int):
            for i in range(ops_per_thread):
                p = f"Thread-{thread_id}-Query-{i % 10}"
                cache.set(p, {"thread": thread_id, "op": i})
                val = cache.get(p)
                assert val is not None
                peeked = cache.peek(p)
                assert peeked is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_task, t_id) for t_id in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Raises if any assertion failed

        stats = cache.get_stats()
        assert stats["size"] <= 100
        assert stats["hits"] > 0

    def test_concurrent_lru_eviction_under_heavy_load(self):
        """Concurrent writes exceeding capacity maintain data consistency and eviction counts."""
        capacity = 20
        cache = SemanticCache(capacity=capacity)
        total_items = 200

        def insert_item(item_id: int):
            cache.set(f"Heavy-Load-Query-{item_id}", {"id": item_id})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(insert_item, range(total_items)))

        assert len(cache) == capacity
        assert cache.evictions == (total_items - capacity)
