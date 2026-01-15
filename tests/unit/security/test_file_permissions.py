"""Tests for SQLite cache file permissions.

This module tests that cache files and directories are created with secure
permissions to prevent unauthorized access to cached data.

Coverage target: 100% branch coverage on permission handling.
"""

from __future__ import annotations

import os
import stat
import tempfile

import pytest

from goodtomerge.adapters.cache_sqlite import SqliteCacheAdapter


class TestSQLiteCacheFilePermissions:
    """Verify cache files have secure permissions (0600)."""

    def test_new_cache_file_has_0600_permissions(self) -> None:
        """New cache file must be created with 0600 (owner rw only)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check permissions
            mode = os.stat(cache_path).st_mode
            # Extract permission bits
            perms = stat.S_IMODE(mode)
            assert perms == 0o600, f"Expected 0600, got {oct(perms)}"

            cache.close()

    def test_cache_file_permissions_after_get(self) -> None:
        """Cache file should maintain 0600 permissions after read operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("key", "value", ttl_seconds=300)
            cache.get("key")
            cache.get("nonexistent")

            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600, f"Expected 0600, got {oct(perms)}"

            cache.close()


class TestSQLiteCacheDirectoryPermissions:
    """Verify cache directories have secure permissions (0700)."""

    def test_cache_directory_has_0700_permissions(self) -> None:
        """Cache directory must be created with 0700."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "subdir", "cache")
            cache_path = os.path.join(cache_dir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check directory permissions
            mode = os.stat(cache_dir).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o700, f"Expected 0700, got {oct(perms)}"

            cache.close()

    def test_nested_directory_creation_permissions(self) -> None:
        """Nested directories should all be created with secure permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create deeply nested path
            cache_path = os.path.join(tmpdir, "a", "b", "c", "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check the immediate parent directory (where cache.db lives)
            immediate_parent = os.path.dirname(cache_path)
            mode = os.stat(immediate_parent).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o700, f"Expected 0700, got {oct(perms)}"

            cache.close()


class TestExistingPermissiveCacheFile:
    """Verify permissive existing files get fixed."""

    def test_existing_permissive_file_gets_restricted(self) -> None:
        """If file exists with loose perms, must be tightened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            # Create file with permissive permissions
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o666)

            # Verify it's permissive before
            mode_before = os.stat(cache_path).st_mode
            assert stat.S_IMODE(mode_before) == 0o666

            # Open cache - should fix permissions
            cache = SqliteCacheAdapter(cache_path)

            # Verify permissions were fixed
            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600, f"Expected 0600, got {oct(perms)}"

            cache.close()

    def test_group_readable_file_gets_restricted(self) -> None:
        """File with group read permission should be restricted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o640)  # Group readable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)

            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600

            cache.close()

    def test_world_readable_file_gets_restricted(self) -> None:
        """File with world read permission should be restricted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o644)  # World readable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)

            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600

            cache.close()

    def test_world_writable_file_gets_restricted(self) -> None:
        """File with world write permission should be restricted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o622)  # World writable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)

            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600

            cache.close()


class TestPermissionWarnings:
    """Verify warnings are issued for world-readable files."""

    def test_permission_warning_logged_for_world_readable(self) -> None:
        """Log warning if file was world-readable before fix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o644)  # World readable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)
                cache.close()

    def test_permission_warning_includes_old_permissions(self) -> None:
        """Warning message should include the old permission value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o777)  # Very permissive

            with pytest.warns(UserWarning, match=r"0o777"):
                cache = SqliteCacheAdapter(cache_path)
                cache.close()

    def test_no_warning_for_secure_existing_file(self) -> None:
        """No warning should be issued if existing file already has 0600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o600)  # Already secure

            # Should not warn
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("error")
                cache = SqliteCacheAdapter(cache_path)
                cache.close()

    def test_warning_for_group_writable(self) -> None:
        """Warning should be issued for group-writable files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o660)  # Group writable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)
                cache.close()


class TestDirectoryPermissionFixes:
    """Verify existing directories with wrong permissions get fixed."""

    def test_existing_permissive_directory_gets_fixed(self) -> None:
        """If directory exists with loose perms, should be tightened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache_subdir")
            os.makedirs(cache_dir, mode=0o755)  # World readable/executable

            cache_path = os.path.join(cache_dir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check directory permissions were fixed
            mode = os.stat(cache_dir).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o700, f"Expected 0700, got {oct(perms)}"

            cache.close()
