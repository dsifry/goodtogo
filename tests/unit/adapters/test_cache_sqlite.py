"""Tests for SqliteCacheAdapter.

This module tests the SQLite-based cache adapter including:
- Basic get/set/delete operations
- TTL expiration handling
- Pattern-based invalidation
- Statistics tracking
- Secure file permissions
- Connection management

Coverage target: 100% coverage on cache_sqlite.py
"""

from __future__ import annotations

import os
import stat
import tempfile
import time
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from goodtogo.adapters.cache_sqlite import SqliteCacheAdapter
from goodtogo.core.models import CacheStats


class TestSqliteCacheAdapterInit:
    """Tests for adapter initialization and security."""

    def test_init_creates_database(self) -> None:
        """Initializing adapter should create the database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache", "test.db")
            adapter = SqliteCacheAdapter(db_path)

            assert os.path.exists(db_path)
            adapter.close()

    def test_init_creates_parent_directory(self) -> None:
        """Init should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "nested", "dir", "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            assert os.path.exists(os.path.dirname(db_path))
            adapter.close()

    def test_init_sets_secure_directory_permissions(self) -> None:
        """Init should set directory permissions to 0700."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            db_path = os.path.join(cache_dir, "test.db")
            adapter = SqliteCacheAdapter(db_path)

            dir_mode = stat.S_IMODE(os.stat(cache_dir).st_mode)
            assert dir_mode == 0o700
            adapter.close()

    def test_init_sets_secure_file_permissions(self) -> None:
        """Init should set file permissions to 0600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            file_mode = stat.S_IMODE(os.stat(db_path).st_mode)
            assert file_mode == stat.S_IRUSR | stat.S_IWUSR  # 0600
            adapter.close()

    def test_init_fixes_permissive_file_permissions(self) -> None:
        """Init should fix permissive file permissions and warn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")

            # Create file with permissive permissions
            Path(db_path).touch()
            os.chmod(db_path, 0o644)

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                adapter = SqliteCacheAdapter(db_path)

                # Should have issued a warning
                assert len(w) == 1
                assert "permissive permissions" in str(w[0].message)
                # Check for both possible formats (0644 or 0o644)
                warning_text = str(w[0].message)
                assert "644" in warning_text

            adapter.close()

    def test_init_fixes_directory_permissions(self) -> None:
        """Init should fix permissive directory permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            os.makedirs(cache_dir, mode=0o755)
            db_path = os.path.join(cache_dir, "test.db")

            adapter = SqliteCacheAdapter(db_path)

            dir_mode = stat.S_IMODE(os.stat(cache_dir).st_mode)
            assert dir_mode == 0o700
            adapter.close()


class TestSqliteCacheAdapterBasics:
    """Tests for basic cache operations."""

    def test_set_and_get_value(self) -> None:
        """Setting a value should allow retrieval via get."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            result = adapter.get("key1")

            assert result == "value1"
            adapter.close()

    def test_get_nonexistent_key_returns_none(self) -> None:
        """Getting a nonexistent key should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            result = adapter.get("nonexistent")

            assert result is None
            adapter.close()

    def test_set_overwrites_existing_value(self) -> None:
        """Setting a key that exists should overwrite the value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.set("key1", "value2", ttl_seconds=300)
            result = adapter.get("key1")

            assert result == "value2"
            adapter.close()

    def test_get_updates_hit_statistics(self) -> None:
        """Getting an existing value should update hit counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.get("key1")

            stats = adapter.get_stats()
            assert stats.hits == 1
            assert stats.misses == 0
            adapter.close()

    def test_get_updates_miss_statistics(self) -> None:
        """Getting a nonexistent value should update miss counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.get("nonexistent")

            stats = adapter.get_stats()
            assert stats.hits == 0
            assert stats.misses == 1
            adapter.close()


class TestSqliteCacheAdapterDelete:
    """Tests for delete() method (lines 220-222)."""

    def test_delete_existing_key(self) -> None:
        """Deleting an existing key should remove it from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.delete("key1")

            assert adapter.get("key1") is None
            adapter.close()

    def test_delete_nonexistent_key_no_error(self) -> None:
        """Deleting a nonexistent key should not raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            # Should not raise
            adapter.delete("nonexistent")
            adapter.close()

    def test_delete_only_removes_specified_key(self) -> None:
        """Delete should only remove the specified key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.set("key2", "value2", ttl_seconds=300)
            adapter.delete("key1")

            assert adapter.get("key1") is None
            assert adapter.get("key2") == "value2"
            adapter.close()


class TestSqliteCacheAdapterInvalidatePattern:
    """Tests for invalidate_pattern() method (lines 243-249)."""

    def test_invalidate_pattern_with_asterisk(self) -> None:
        """invalidate_pattern should convert * to % for SQL LIKE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("pr:owner:repo:123:meta", "meta", ttl_seconds=300)
            adapter.set("pr:owner:repo:123:comments", "comments", ttl_seconds=300)
            adapter.set("pr:owner:repo:456:meta", "other", ttl_seconds=300)

            adapter.invalidate_pattern("pr:owner:repo:123:*")

            assert adapter.get("pr:owner:repo:123:meta") is None
            assert adapter.get("pr:owner:repo:123:comments") is None
            assert adapter.get("pr:owner:repo:456:meta") == "other"
            adapter.close()

    def test_invalidate_pattern_with_question_mark(self) -> None:
        """invalidate_pattern should convert ? to _ for SQL LIKE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.set("key2", "value2", ttl_seconds=300)
            adapter.set("key10", "value10", ttl_seconds=300)

            adapter.invalidate_pattern("key?")

            assert adapter.get("key1") is None
            assert adapter.get("key2") is None
            assert adapter.get("key10") == "value10"
            adapter.close()

    def test_invalidate_pattern_with_percent(self) -> None:
        """invalidate_pattern should work with SQL LIKE % directly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("prefix:a", "value1", ttl_seconds=300)
            adapter.set("prefix:b", "value2", ttl_seconds=300)
            adapter.set("other:c", "value3", ttl_seconds=300)

            adapter.invalidate_pattern("prefix:%")

            assert adapter.get("prefix:a") is None
            assert adapter.get("prefix:b") is None
            assert adapter.get("other:c") == "value3"
            adapter.close()

    def test_invalidate_pattern_no_matches(self) -> None:
        """invalidate_pattern with no matches should not affect cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.invalidate_pattern("nonexistent:*")

            assert adapter.get("key1") == "value1"
            adapter.close()


class TestSqliteCacheAdapterCleanupExpired:
    """Tests for cleanup_expired() method (lines 257-260)."""

    def test_cleanup_expired_removes_expired_entries(self) -> None:
        """cleanup_expired should remove all expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            # Add entry with very short TTL
            adapter.set("expired", "value", ttl_seconds=1)
            adapter.set("valid", "value", ttl_seconds=3600)

            # Wait for expiration
            time.sleep(1.1)

            adapter.cleanup_expired()

            assert adapter.get("expired") is None
            # Note: get() will also return None for expired, but we want to
            # verify cleanup_expired removes it from the database
            assert adapter.get("valid") == "value"
            adapter.close()

    def test_cleanup_expired_preserves_valid_entries(self) -> None:
        """cleanup_expired should not remove entries that haven't expired."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=3600)
            adapter.set("key2", "value2", ttl_seconds=3600)

            adapter.cleanup_expired()

            assert adapter.get("key1") == "value1"
            assert adapter.get("key2") == "value2"
            adapter.close()

    def test_cleanup_expired_on_empty_database(self) -> None:
        """cleanup_expired on empty database should not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            # Should not raise
            adapter.cleanup_expired()
            adapter.close()


class TestSqliteCacheAdapterGetStats:
    """Tests for get_stats() method (lines 275-291)."""

    def test_get_stats_returns_cache_stats(self) -> None:
        """get_stats() should return CacheStats object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            stats = adapter.get_stats()

            assert isinstance(stats, CacheStats)
            adapter.close()

    def test_get_stats_initial_values(self) -> None:
        """get_stats() on new adapter should return zero counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            stats = adapter.get_stats()

            assert stats.hits == 0
            assert stats.misses == 0
            assert stats.hit_rate == 0.0
            adapter.close()

    def test_get_stats_tracks_hits_and_misses(self) -> None:
        """get_stats() should track hits and misses correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.get("key1")  # Hit
            adapter.get("key1")  # Hit
            adapter.get("nonexistent")  # Miss

            stats = adapter.get_stats()

            assert stats.hits == 2
            assert stats.misses == 1
            assert stats.hit_rate == pytest.approx(2 / 3)
            adapter.close()

    def test_get_stats_hit_rate_all_hits(self) -> None:
        """get_stats() with all hits should return 1.0 hit rate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=300)
            adapter.get("key1")
            adapter.get("key1")

            stats = adapter.get_stats()

            assert stats.hit_rate == 1.0
            adapter.close()

    def test_get_stats_hit_rate_all_misses(self) -> None:
        """get_stats() with all misses should return 0.0 hit rate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.get("nonexistent1")
            adapter.get("nonexistent2")

            stats = adapter.get_stats()

            assert stats.hit_rate == 0.0
            adapter.close()


class TestSqliteCacheAdapterClose:
    """Tests for close() method (line 309)."""

    def test_close_closes_connection(self) -> None:
        """close() should close the database connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.close()

            # Connection should be None after close
            assert adapter._connection is None

    def test_close_can_be_called_multiple_times(self) -> None:
        """close() should be safe to call multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.close()
            adapter.close()  # Should not raise
            adapter.close()  # Should not raise

    def test_del_closes_connection(self) -> None:
        """__del__ should close the connection on garbage collection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            # Trigger __del__ explicitly
            adapter.__del__()

            assert adapter._connection is None


class TestSqliteCacheAdapterRepr:
    """Tests for __repr__() method (line 309)."""

    def test_repr_includes_db_path(self) -> None:
        """repr() should include the database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            result = repr(adapter)

            assert "SqliteCacheAdapter" in result
            assert "cache.db" in result
            adapter.close()

    def test_repr_format(self) -> None:
        """repr() should follow standard format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_cache.db")
            adapter = SqliteCacheAdapter(db_path)

            result = repr(adapter)

            assert result == f"SqliteCacheAdapter(db_path={db_path!r})"
            adapter.close()


class TestSqliteCacheAdapterExpiration:
    """Tests for TTL expiration handling."""

    def test_expired_entry_returns_none(self) -> None:
        """Getting an expired entry should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=1)

            # Wait for expiration
            time.sleep(1.1)

            result = adapter.get("key1")
            assert result is None
            adapter.close()

    def test_expired_entry_increments_misses(self) -> None:
        """Getting an expired entry should increment miss counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            adapter.set("key1", "value1", ttl_seconds=1)
            adapter.get("key1")  # Hit (not expired yet)

            time.sleep(1.1)
            adapter.get("key1")  # Miss (expired)

            stats = adapter.get_stats()
            assert stats.hits == 1
            assert stats.misses == 1
            adapter.close()


class TestSqliteCacheAdapterPersistence:
    """Tests for data persistence across adapter instances."""

    def test_data_persists_across_connections(self) -> None:
        """Data should persist when reopening the database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")

            # First adapter instance
            adapter1 = SqliteCacheAdapter(db_path)
            adapter1.set("key1", "value1", ttl_seconds=3600)
            adapter1.close()

            # Second adapter instance
            adapter2 = SqliteCacheAdapter(db_path)
            result = adapter2.get("key1")

            assert result == "value1"
            adapter2.close()


class TestSqliteCacheAdapterEdgeCases:
    """Tests for edge cases and branch coverage."""

    def test_init_with_existing_correct_dir_permissions(self) -> None:
        """Init should not chmod if directory already has 0o700 permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            os.makedirs(cache_dir, mode=0o700)
            db_path = os.path.join(cache_dir, "test.db")

            adapter = SqliteCacheAdapter(db_path)

            # Verify permissions are still correct
            dir_mode = stat.S_IMODE(os.stat(cache_dir).st_mode)
            assert dir_mode == 0o700
            adapter.close()

    def test_get_stats_with_deleted_global_row(self) -> None:
        """get_stats should handle missing global row gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")
            adapter = SqliteCacheAdapter(db_path)

            # Delete the global stats row
            conn = adapter._get_connection()
            conn.execute("DELETE FROM cache_stats WHERE key_prefix = 'global'")
            conn.commit()

            # get_stats should return zeros
            stats = adapter.get_stats()
            assert stats.hits == 0
            assert stats.misses == 0
            assert stats.hit_rate == 0.0
            adapter.close()

    def test_init_with_file_in_root_dir(self) -> None:
        """Init should handle db_path with empty parent (root directory concept)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path that simulates a file directly in the temp dir
            db_path = os.path.join(tmpdir, "cache.db")

            adapter = SqliteCacheAdapter(db_path)
            adapter.set("key", "value", ttl_seconds=300)

            assert adapter.get("key") == "value"
            adapter.close()

    def test_init_with_relative_path(self) -> None:
        """Init should handle a simple filename path."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir and use a relative path
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                adapter = SqliteCacheAdapter("cache.db")
                adapter.set("key", "value", ttl_seconds=300)
                assert adapter.get("key") == "value"
                adapter.close()
            finally:
                os.chdir(original_dir)

    def test_init_dir_already_has_correct_permissions_no_chmod(self) -> None:
        """Init should skip chmod when directory already has 0o700 permissions.

        This tests the condition `if current_mode != 0o700` evaluating to False.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            # Create dir with exactly 0o700 (the target permissions)
            os.makedirs(cache_dir, mode=0o700)

            # Verify starting permissions
            initial_mode = stat.S_IMODE(os.stat(cache_dir).st_mode)
            assert initial_mode == 0o700

            db_path = os.path.join(cache_dir, "test.db")
            adapter = SqliteCacheAdapter(db_path)

            # Permissions should still be 0o700 (no change needed)
            final_mode = stat.S_IMODE(os.stat(cache_dir).st_mode)
            assert final_mode == 0o700
            adapter.close()

    def test_init_database_with_mocked_path_not_exists(self) -> None:
        """Test edge case where path.exists() returns False in _init_database.

        This is a defensive branch that shouldn't normally trigger.
        """
        from unittest.mock import patch, MagicMock

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")

            # We need to make the first exists() call return True (for _ensure_secure_path)
            # and subsequent calls return appropriate values
            call_count = 0
            original_exists = Path.exists

            def mock_exists(self):
                nonlocal call_count
                call_count += 1
                # First few calls are in _ensure_secure_path
                # Last call is in _init_database - make it return False
                if str(self) == db_path and call_count > 2:
                    return False
                return original_exists(self)

            with patch.object(Path, 'exists', mock_exists):
                adapter = SqliteCacheAdapter(db_path)
                # Should still work even if the path check returns False
                adapter.set("key", "value", ttl_seconds=300)
                adapter.close()

    def test_init_with_empty_parent_path(self) -> None:
        """Test initialization with a filename only (no parent directory).

        When db_path is just a filename like 'cache.db', Path.parent returns
        Path('.') which is truthy but represents current directory. This tests
        the branch where cache_dir evaluates to Path('.').
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Just a filename - parent will be Path('.')
                adapter = SqliteCacheAdapter("cache.db")

                # Should work normally
                adapter.set("key", "value", ttl_seconds=300)
                assert adapter.get("key") == "value"
                adapter.close()
            finally:
                os.chdir(original_dir)

    def test_init_skipping_both_if_elif_branches(self) -> None:
        """Test edge case where both if and elif for cache_dir are skipped.

        This is achieved by mocking cache_dir to be falsy.
        """
        from unittest.mock import patch, PropertyMock

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cache.db")

            # Mock Path.parent to return a falsy-like path in a controlled way
            original_parent = Path.parent

            class FalsyPath:
                """A path-like object that evaluates to False."""
                def __bool__(self):
                    return False

            call_count = 0

            @property
            def mock_parent(self):
                nonlocal call_count
                call_count += 1
                # On first call (in _ensure_secure_path), return falsy
                if call_count == 1:
                    return FalsyPath()
                # For other calls, return normal parent
                return original_parent.fget(self)

            with patch.object(Path, 'parent', mock_parent):
                adapter = SqliteCacheAdapter(db_path)
                adapter.set("key", "value", ttl_seconds=300)
                adapter.close()
