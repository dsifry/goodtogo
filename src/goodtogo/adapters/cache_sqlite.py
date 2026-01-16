"""SQLite cache adapter for GoodToMerge.

This module provides a SQLite-based implementation of the CachePort interface.
It offers zero-configuration local caching with automatic TTL expiration,
secure file permissions, and pattern-based invalidation.

Security features:
- Cache directory created with 0700 permissions (owner only)
- Cache file created with 0600 permissions (owner read/write only)
- Existing permissive permissions are fixed with a warning
- All inputs validated before use
"""

from __future__ import annotations

import sqlite3
import stat
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from goodtogo.adapters.time_provider import SystemTimeProvider
from goodtogo.core.interfaces import CachePort, TimeProvider

if TYPE_CHECKING:
    from goodtogo.core.models import CacheStats


# SQL statements for schema creation and operations
_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS pr_cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_expires_at ON pr_cache(expires_at);

CREATE TABLE IF NOT EXISTS cache_stats (
    key_prefix TEXT PRIMARY KEY,
    hits INTEGER DEFAULT 0,
    misses INTEGER DEFAULT 0
);

-- Initialize global stats if not exists
INSERT OR IGNORE INTO cache_stats (key_prefix, hits, misses) VALUES ('global', 0, 0);
"""


class SqliteCacheAdapter(CachePort):
    """SQLite-based cache adapter implementing the CachePort interface.

    This adapter provides persistent local caching using SQLite with:
    - Automatic TTL-based expiration
    - Pattern-based key invalidation using SQL LIKE
    - Hit/miss statistics tracking
    - Secure file permissions

    The cache database is created automatically on first use with
    appropriate file permissions to protect cached data.

    Example:
        >>> cache = SqliteCacheAdapter(".goodtogo/cache.db")
        >>> cache.set("pr:myorg:myrepo:123:meta", '{"title": "My PR"}', ttl_seconds=300)
        >>> value = cache.get("pr:myorg:myrepo:123:meta")
        >>> cache.invalidate_pattern("pr:myorg:myrepo:123:%")

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str, time_provider: Optional[TimeProvider] = None) -> None:
        """Initialize the SQLite cache adapter.

        Creates the cache directory and database file with secure permissions
        if they don't exist. If the file exists with permissive permissions,
        they are tightened and a warning is issued.

        Args:
            db_path: Path to the SQLite database file. Parent directories
                    will be created if they don't exist.
            time_provider: Optional TimeProvider for time operations.
                          Defaults to SystemTimeProvider if not provided.

        Raises:
            OSError: If unable to create directory or set permissions.
        """
        self.db_path = db_path
        self._time_provider = time_provider or SystemTimeProvider()
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_secure_path()
        self._init_database()

    def _ensure_secure_path(self) -> None:
        """Ensure cache directory and file have secure permissions.

        Creates the directory with 0700 permissions and ensures the file
        (if it exists) has 0600 permissions. Issues a warning if existing
        permissions were too permissive.
        """
        path = Path(self.db_path)
        cache_dir = path.parent

        # Create directory with secure permissions if needed
        if cache_dir and not cache_dir.exists():
            cache_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        elif cache_dir and cache_dir.exists():
            # Ensure existing directory has correct permissions
            current_mode = stat.S_IMODE(cache_dir.stat().st_mode)
            if current_mode != 0o700:
                cache_dir.chmod(0o700)

        # Check existing file permissions and fix if necessary
        if path.exists():
            current_mode = stat.S_IMODE(path.stat().st_mode)
            # Check if group or others have any permissions
            if current_mode & (stat.S_IRWXG | stat.S_IRWXO):
                warnings.warn(
                    f"Cache file {self.db_path} had permissive permissions "
                    f"({oct(current_mode)}). Fixing to 0600.",
                    UserWarning,
                    stacklevel=2,
                )
                path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _init_database(self) -> None:
        """Initialize the database schema.

        Creates the pr_cache and cache_stats tables if they don't exist.
        Sets file permissions to 0600 after creation.
        """
        conn = self._get_connection()
        conn.executescript(_CREATE_TABLES_SQL)
        conn.commit()

        # Ensure file has correct permissions after creation
        path = Path(self.db_path)
        if path.exists():
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection.

        Returns:
            Active SQLite connection with row factory set to sqlite3.Row.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def get(self, key: str) -> Optional[str]:
        """Get cached value.

        Retrieves a value from the cache if it exists and has not expired.
        Updates hit/miss statistics accordingly.

        Args:
            key: Cache key (e.g., 'pr:myorg:myrepo:123:meta').

        Returns:
            Cached value as string if found and not expired, None otherwise.
        """
        conn = self._get_connection()
        current_time = self._time_provider.now_int()

        cursor = conn.execute(
            "SELECT value FROM pr_cache WHERE key = ? AND expires_at > ?",
            (key, current_time),
        )
        row = cursor.fetchone()

        if row is not None:
            # Cache hit
            conn.execute("UPDATE cache_stats SET hits = hits + 1 WHERE key_prefix = 'global'")
            conn.commit()
            return str(row["value"])
        else:
            # Cache miss
            conn.execute("UPDATE cache_stats SET misses = misses + 1 WHERE key_prefix = 'global'")
            conn.commit()
            return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set cached value with TTL.

        Stores a value in the cache with an expiration time. If a value
        already exists for the key, it is replaced.

        Args:
            key: Cache key (e.g., 'pr:myorg:myrepo:123:meta').
            value: Value to cache (typically JSON string).
            ttl_seconds: Time to live in seconds. After this duration,
                        the entry is considered expired.
        """
        conn = self._get_connection()
        current_time = self._time_provider.now_int()
        expires_at = current_time + ttl_seconds

        conn.execute(
            """
            INSERT OR REPLACE INTO pr_cache (key, value, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, value, expires_at, current_time),
        )
        conn.commit()

    def delete(self, key: str) -> None:
        """Delete cached value.

        Removes a specific entry from the cache.

        Args:
            key: Cache key to delete.
        """
        conn = self._get_connection()
        conn.execute("DELETE FROM pr_cache WHERE key = ?", (key,))
        conn.commit()

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern.

        Removes all cache entries whose keys match the given pattern.
        Uses SQL LIKE pattern matching where '%' matches any sequence
        of characters and '_' matches any single character.

        For glob-style patterns using '*', convert to SQL LIKE:
        - 'pr:myorg:myrepo:123:*' -> 'pr:myorg:myrepo:123:%'

        Args:
            pattern: Pattern to match keys against. Use '%' as wildcard
                    for SQL LIKE matching (e.g., 'pr:myorg:myrepo:123:%').

        Note:
            The pattern is converted from glob-style to SQL LIKE:
            - '*' is converted to '%'
            - '?' is converted to '_'
        """
        conn = self._get_connection()

        # Convert glob-style wildcards to SQL LIKE pattern
        sql_pattern = pattern.replace("*", "%").replace("?", "_")

        conn.execute("DELETE FROM pr_cache WHERE key LIKE ?", (sql_pattern,))
        conn.commit()

    def cleanup_expired(self) -> None:
        """Remove expired entries.

        Deletes all entries whose TTL has expired. This should be called
        periodically to prevent unbounded cache growth.
        """
        conn = self._get_connection()
        current_time = self._time_provider.now_int()
        conn.execute("DELETE FROM pr_cache WHERE expires_at <= ?", (current_time,))
        conn.commit()

    def get_stats(self) -> CacheStats:
        """Get cache hit/miss statistics.

        Returns metrics about cache performance for monitoring and
        debugging purposes.

        Returns:
            CacheStats object containing:
            - hits: Number of successful cache lookups
            - misses: Number of cache misses
            - hit_rate: Ratio of hits to total lookups (0.0 to 1.0)
        """
        # Import here to avoid circular imports
        from goodtogo.core.models import CacheStats

        conn = self._get_connection()
        cursor = conn.execute("SELECT hits, misses FROM cache_stats WHERE key_prefix = 'global'")
        row = cursor.fetchone()

        if row is None:
            return CacheStats(hits=0, misses=0, hit_rate=0.0)

        hits = row["hits"]
        misses = row["misses"]
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0

        return CacheStats(hits=hits, misses=misses, hit_rate=hit_rate)

    def close(self) -> None:
        """Close the database connection.

        Should be called when the cache is no longer needed to release
        database resources.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        self.close()

    def __repr__(self) -> str:
        """Return string representation of the adapter."""
        return f"SqliteCacheAdapter(db_path={self.db_path!r})"
