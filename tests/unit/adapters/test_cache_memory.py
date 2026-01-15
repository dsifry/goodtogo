"""Tests for InMemoryCacheAdapter.

This module tests the in-memory cache adapter including:
- Basic get/set/delete operations
- TTL expiration handling
- Pattern-based invalidation
- Statistics tracking
- clear(), __len__(), and __repr__()

Coverage target: 100% coverage on cache_memory.py
"""

from __future__ import annotations

import time
from unittest.mock import patch

from goodtogo.adapters.cache_memory import CacheEntry, InMemoryCacheAdapter
from goodtogo.core.models import CacheStats


class TestCacheEntry:
    """Tests for the CacheEntry dataclass."""

    def test_cache_entry_creation(self) -> None:
        """CacheEntry should store value and expiration time."""
        entry = CacheEntry(value="test_value", expires_at=12345.0)
        assert entry.value == "test_value"
        assert entry.expires_at == 12345.0


class TestInMemoryCacheAdapterBasics:
    """Tests for basic cache operations."""

    def test_init_creates_empty_cache(self) -> None:
        """Initializing cache should create empty store with zero stats."""
        cache = InMemoryCacheAdapter()
        assert len(cache) == 0
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0

    def test_set_and_get_value(self) -> None:
        """Setting a value should allow retrieval via get."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key_returns_none(self) -> None:
        """Getting a nonexistent key should return None and increment misses."""
        cache = InMemoryCacheAdapter()
        result = cache.get("nonexistent")
        assert result is None
        stats = cache.get_stats()
        assert stats.misses == 1
        assert stats.hits == 0

    def test_get_increments_hits(self) -> None:
        """Getting an existing value should increment hits counter."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.get("key1")
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 0

    def test_set_overwrites_existing_value(self) -> None:
        """Setting a key that already exists should overwrite the value."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.set("key1", "value2", ttl_seconds=300)
        assert cache.get("key1") == "value2"


class TestInMemoryCacheAdapterExpiration:
    """Tests for TTL expiration handling (lines 88-90)."""

    def test_expired_entry_returns_none(self) -> None:
        """Getting an expired entry should return None and remove it."""
        cache = InMemoryCacheAdapter()

        # Set with a very short TTL
        cache.set("key1", "value1", ttl_seconds=1)

        # Verify it's there initially
        assert cache.get("key1") == "value1"

        # Wait for expiration (or mock time)
        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            # First call is during set, second is during get
            mock_time.time.return_value = time.time() + 2  # 2 seconds in future
            result = cache.get("key1")

        assert result is None

    def test_expired_entry_increments_misses(self) -> None:
        """Getting an expired entry should increment the miss counter."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=1)

        # First get (should be a hit)
        cache.get("key1")
        stats_before = cache.get_stats()
        assert stats_before.hits == 1
        assert stats_before.misses == 0

        # Expire the entry using mock
        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            cache.get("key1")

        stats_after = cache.get_stats()
        assert stats_after.misses == 1  # Now incremented

    def test_expired_entry_is_deleted(self) -> None:
        """Accessing an expired entry should remove it from the store."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=1)
        assert len(cache) == 1

        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            cache.get("key1")

        # Entry should be removed after expired get
        assert len(cache) == 0


class TestInMemoryCacheAdapterDelete:
    """Tests for delete() method (line 119)."""

    def test_delete_existing_key(self) -> None:
        """Deleting an existing key should remove it from cache."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        assert len(cache) == 1

        cache.delete("key1")
        assert len(cache) == 0
        assert cache.get("key1") is None

    def test_delete_nonexistent_key_no_error(self) -> None:
        """Deleting a nonexistent key should be a no-op (no error)."""
        cache = InMemoryCacheAdapter()
        # Should not raise
        cache.delete("nonexistent")
        assert len(cache) == 0

    def test_delete_only_removes_specified_key(self) -> None:
        """Delete should only remove the specified key."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.set("key2", "value2", ttl_seconds=300)

        cache.delete("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestInMemoryCacheAdapterInvalidatePattern:
    """Tests for invalidate_pattern() method (lines 137-140)."""

    def test_invalidate_pattern_removes_matching_keys(self) -> None:
        """invalidate_pattern should remove all keys matching glob pattern."""
        cache = InMemoryCacheAdapter()
        cache.set("pr:owner:repo:123:meta", "meta_value", ttl_seconds=300)
        cache.set("pr:owner:repo:123:comments", "comments_value", ttl_seconds=300)
        cache.set("pr:owner:repo:456:meta", "other_meta", ttl_seconds=300)

        cache.invalidate_pattern("pr:owner:repo:123:*")

        assert cache.get("pr:owner:repo:123:meta") is None
        assert cache.get("pr:owner:repo:123:comments") is None
        assert cache.get("pr:owner:repo:456:meta") == "other_meta"

    def test_invalidate_pattern_no_matches(self) -> None:
        """invalidate_pattern with no matches should not affect cache."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)

        cache.invalidate_pattern("nonexistent:*")

        assert cache.get("key1") == "value1"
        assert len(cache) == 1

    def test_invalidate_pattern_wildcard_in_middle(self) -> None:
        """invalidate_pattern should work with wildcards in middle of pattern."""
        cache = InMemoryCacheAdapter()
        cache.set("pr:owner:repo:123:meta", "value1", ttl_seconds=300)
        cache.set("pr:owner:other:123:meta", "value2", ttl_seconds=300)

        cache.invalidate_pattern("pr:owner:*:123:meta")

        assert cache.get("pr:owner:repo:123:meta") is None
        assert cache.get("pr:owner:other:123:meta") is None

    def test_invalidate_pattern_question_mark_wildcard(self) -> None:
        """invalidate_pattern should support ? for single character match."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.set("key2", "value2", ttl_seconds=300)
        cache.set("key10", "value10", ttl_seconds=300)

        cache.invalidate_pattern("key?")

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key10") == "value10"  # ? matches single char only


class TestInMemoryCacheAdapterCleanupExpired:
    """Tests for cleanup_expired() method (lines 149-157)."""

    def test_cleanup_expired_removes_expired_entries(self) -> None:
        """cleanup_expired should remove all expired entries."""
        cache = InMemoryCacheAdapter()

        # Add entries with different TTLs
        current_time = time.time()
        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            mock_time.time.return_value = current_time
            cache.set("expired1", "value1", ttl_seconds=1)
            cache.set("expired2", "value2", ttl_seconds=2)
            cache.set("valid", "value3", ttl_seconds=3600)

        assert len(cache) == 3

        # Advance time by 3 seconds
        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            mock_time.time.return_value = current_time + 3
            cache.cleanup_expired()

        # Only valid entry should remain
        assert len(cache) == 1

    def test_cleanup_expired_preserves_valid_entries(self) -> None:
        """cleanup_expired should not remove entries that haven't expired."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=3600)
        cache.set("key2", "value2", ttl_seconds=3600)

        cache.cleanup_expired()

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_cleanup_expired_on_empty_cache(self) -> None:
        """cleanup_expired on empty cache should not error."""
        cache = InMemoryCacheAdapter()
        cache.cleanup_expired()
        assert len(cache) == 0


class TestInMemoryCacheAdapterClear:
    """Tests for clear() method (lines 180-182)."""

    def test_clear_removes_all_entries(self) -> None:
        """clear() should remove all entries from the cache."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.set("key2", "value2", ttl_seconds=300)
        assert len(cache) == 2

        cache.clear()

        assert len(cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_clear_resets_statistics(self) -> None:
        """clear() should reset hit/miss counters to zero."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats_before = cache.get_stats()
        assert stats_before.hits == 1
        assert stats_before.misses == 1

        cache.clear()

        stats_after = cache.get_stats()
        assert stats_after.hits == 0
        assert stats_after.misses == 0

    def test_clear_on_empty_cache(self) -> None:
        """clear() on empty cache should not error."""
        cache = InMemoryCacheAdapter()
        cache.clear()
        assert len(cache) == 0


class TestInMemoryCacheAdapterLen:
    """Tests for __len__() method (line 193)."""

    def test_len_empty_cache(self) -> None:
        """len() on empty cache should return 0."""
        cache = InMemoryCacheAdapter()
        assert len(cache) == 0

    def test_len_with_entries(self) -> None:
        """len() should return number of entries in cache."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        assert len(cache) == 1

        cache.set("key2", "value2", ttl_seconds=300)
        assert len(cache) == 2

    def test_len_includes_potentially_expired(self) -> None:
        """len() should include expired entries that haven't been cleaned."""
        cache = InMemoryCacheAdapter()
        current_time = time.time()

        with patch("goodtogo.adapters.cache_memory.time") as mock_time:
            mock_time.time.return_value = current_time
            cache.set("expired", "value", ttl_seconds=1)

        # Entry is expired but not yet cleaned
        # len() still counts it
        assert len(cache) == 1


class TestInMemoryCacheAdapterRepr:
    """Tests for __repr__() method (line 201)."""

    def test_repr_empty_cache(self) -> None:
        """repr() should show entry count of 0 for empty cache."""
        cache = InMemoryCacheAdapter()
        result = repr(cache)
        assert result == "InMemoryCacheAdapter(entries=0)"

    def test_repr_with_entries(self) -> None:
        """repr() should show correct entry count."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.set("key2", "value2", ttl_seconds=300)
        result = repr(cache)
        assert result == "InMemoryCacheAdapter(entries=2)"

    def test_repr_format(self) -> None:
        """repr() should follow standard format."""
        cache = InMemoryCacheAdapter()
        cache.set("key", "value", ttl_seconds=300)
        result = repr(cache)
        assert "InMemoryCacheAdapter" in result
        assert "entries=" in result


class TestInMemoryCacheAdapterGetStats:
    """Tests for get_stats() method and hit rate calculation."""

    def test_get_stats_returns_cache_stats(self) -> None:
        """get_stats() should return CacheStats object."""
        cache = InMemoryCacheAdapter()
        stats = cache.get_stats()
        assert isinstance(stats, CacheStats)

    def test_get_stats_hit_rate_calculation(self) -> None:
        """get_stats() should calculate correct hit rate."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)

        # 2 hits
        cache.get("key1")
        cache.get("key1")

        # 2 misses
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 2
        assert stats.hit_rate == 0.5  # 2 / 4

    def test_get_stats_zero_operations(self) -> None:
        """get_stats() with no operations should return 0.0 hit rate."""
        cache = InMemoryCacheAdapter()
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

    def test_get_stats_all_hits(self) -> None:
        """get_stats() with all hits should return 1.0 hit rate."""
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1", ttl_seconds=300)
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")

        stats = cache.get_stats()
        assert stats.hit_rate == 1.0

    def test_get_stats_all_misses(self) -> None:
        """get_stats() with all misses should return 0.0 hit rate."""
        cache = InMemoryCacheAdapter()
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.get_stats()
        assert stats.hit_rate == 0.0
