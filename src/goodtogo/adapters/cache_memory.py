"""In-memory cache adapter for testing.

This module provides a simple dict-based cache implementation that implements
the CachePort interface. It is primarily intended for testing and development
scenarios where persistence is not required.

The cache stores entries with expiration timestamps and tracks hit/miss
statistics for performance monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Optional

from goodtogo.adapters.time_provider import SystemTimeProvider
from goodtogo.core.interfaces import CachePort, TimeProvider
from goodtogo.core.models import CacheStats


@dataclass
class CacheEntry:
    """A single cache entry with value and expiration.

    Attributes:
        value: The cached string value.
        expires_at: Unix timestamp when this entry expires.
    """

    value: str
    expires_at: float


class InMemoryCacheAdapter(CachePort):
    """Simple dict-based cache implementation for testing.

    This adapter provides an in-memory cache that:
    - Stores entries with expiration timestamps
    - Tracks cache hit/miss statistics
    - Supports glob-style pattern matching for invalidation
    - Automatically excludes expired entries from get operations

    The cache is not thread-safe and is intended for single-threaded
    test scenarios. For production use, consider SqliteCacheAdapter
    or RedisCacheAdapter.

    Example:
        cache = InMemoryCacheAdapter()
        cache.set("key", "value", ttl_seconds=300)
        value = cache.get("key")  # Returns "value"
        cache.invalidate_pattern("key:*")  # Invalidate matching keys

    Attributes:
        _store: Internal dictionary storing CacheEntry objects.
        _hits: Counter for cache hits.
        _misses: Counter for cache misses.
    """

    def __init__(self, time_provider: Optional[TimeProvider] = None) -> None:
        """Initialize an empty in-memory cache.

        Args:
            time_provider: TimeProvider for getting current time.
                          Defaults to SystemTimeProvider if not provided.
        """
        self._store: dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._time_provider: TimeProvider = time_provider or SystemTimeProvider()

    def get(self, key: str) -> Optional[str]:
        """Get cached value if it exists and has not expired.

        Retrieves a value from the cache. If the entry exists but has
        expired, it is treated as a cache miss and the entry is removed.

        This method updates hit/miss statistics.

        Args:
            key: Cache key to retrieve.

        Returns:
            The cached string value if found and not expired, None otherwise.
        """
        entry = self._store.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check if entry has expired
        if entry.expires_at <= self._time_provider.now():
            # Remove expired entry
            del self._store[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set cached value with TTL.

        Stores a value in the cache with an expiration time. If an entry
        with the same key already exists, it is overwritten.

        Args:
            key: Cache key to store under.
            value: String value to cache.
            ttl_seconds: Time to live in seconds. The entry will be
                        considered expired after this duration.
        """
        expires_at = self._time_provider.now() + ttl_seconds
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> None:
        """Delete cached value.

        Removes a specific entry from the cache. If the key does not
        exist, this is a no-op.

        Args:
            key: Cache key to delete.
        """
        self._store.pop(key, None)

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern.

        Removes all cache entries whose keys match the given glob-style
        pattern. Uses fnmatch for pattern matching, which supports:
        - * matches everything
        - ? matches any single character
        - [seq] matches any character in seq
        - [!seq] matches any character not in seq

        Args:
            pattern: Glob-style pattern to match keys against.
                    Example: 'pr:myorg:myrepo:123:*' matches all keys
                    starting with 'pr:myorg:myrepo:123:'.
        """
        # Collect keys to delete (avoid modifying dict during iteration)
        keys_to_delete = [key for key in self._store if fnmatch(key, pattern)]

        for key in keys_to_delete:
            del self._store[key]

    def cleanup_expired(self) -> None:
        """Remove all expired entries.

        Scans the entire cache and removes any entries whose TTL has
        expired. This should be called periodically to prevent unbounded
        memory growth from accumulated expired entries.
        """
        current_time = self._time_provider.now()

        # Collect expired keys (avoid modifying dict during iteration)
        expired_keys = [
            key for key, entry in self._store.items() if entry.expires_at <= current_time
        ]

        for key in expired_keys:
            del self._store[key]

    def get_stats(self) -> CacheStats:
        """Get cache hit/miss statistics.

        Returns metrics about cache performance. The hit rate is calculated
        as hits / (hits + misses). If no operations have been performed,
        the hit rate is 0.0.

        Returns:
            CacheStats object containing hits, misses, and hit_rate.
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return CacheStats(hits=self._hits, misses=self._misses, hit_rate=hit_rate)

    def clear(self) -> None:
        """Clear all entries and reset statistics.

        Removes all cached entries and resets hit/miss counters to zero.
        This is useful for test setup/teardown.
        """
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def __len__(self) -> int:
        """Return the number of entries in the cache.

        Note that this includes potentially expired entries that have
        not yet been cleaned up.

        Returns:
            Number of entries currently in the cache.
        """
        return len(self._store)

    def __repr__(self) -> str:
        """Return a string representation of the cache.

        Returns:
            String showing cache type and entry count.
        """
        return f"InMemoryCacheAdapter(entries={len(self._store)})"
