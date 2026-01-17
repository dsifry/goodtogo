"""Unit tests for the GoodToMerge container module.

This module tests the Container class and its factory methods,
including cache creation for different backends.
"""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest

from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
from goodtogo.adapters.cache_sqlite import SqliteCacheAdapter
from goodtogo.container import (
    Container,
    MockGitHubAdapter,
    _create_cache,
    _create_default_parsers,
)
from goodtogo.core.models import ReviewerType

# ============================================================================
# Test: MockGitHubAdapter String Representations
# ============================================================================


class TestMockGitHubAdapterRepr:
    """Tests for MockGitHubAdapter __repr__ and __str__ methods."""

    def test_repr_returns_expected_string(self):
        """MockGitHubAdapter.__repr__ should return descriptive string."""
        adapter = MockGitHubAdapter()
        assert repr(adapter) == "MockGitHubAdapter()"

    def test_str_returns_same_as_repr(self):
        """MockGitHubAdapter.__str__ should return the same as __repr__."""
        adapter = MockGitHubAdapter()
        assert str(adapter) == "MockGitHubAdapter()"
        assert str(adapter) == repr(adapter)

    def test_str_is_useful_for_debugging(self):
        """String representation should be useful for debugging."""
        adapter = MockGitHubAdapter()
        # Should contain the class name
        assert "MockGitHubAdapter" in str(adapter)


class TestMockGitHubAdapterMethods:
    """Tests for MockGitHubAdapter method stubs."""

    def test_get_pr_raises_not_implemented(self):
        """get_pr should raise NotImplementedError with helpful message."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_pr("owner", "repo", 123)
        assert "not implemented" in str(exc_info.value).lower()
        assert "Replace with a mock" in str(exc_info.value)

    def test_get_pr_comments_raises_not_implemented(self):
        """get_pr_comments should raise NotImplementedError."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_pr_comments("owner", "repo", 123)
        assert "not implemented" in str(exc_info.value).lower()

    def test_get_pr_reviews_raises_not_implemented(self):
        """get_pr_reviews should raise NotImplementedError."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_pr_reviews("owner", "repo", 123)
        assert "not implemented" in str(exc_info.value).lower()

    def test_get_pr_threads_raises_not_implemented(self):
        """get_pr_threads should raise NotImplementedError."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_pr_threads("owner", "repo", 123)
        assert "not implemented" in str(exc_info.value).lower()

    def test_get_ci_status_raises_not_implemented(self):
        """get_ci_status should raise NotImplementedError."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_ci_status("owner", "repo", "abc123")
        assert "not implemented" in str(exc_info.value).lower()

    def test_get_commit_raises_not_implemented(self):
        """get_commit should raise NotImplementedError."""
        adapter = MockGitHubAdapter()
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.get_commit("owner", "repo", "abc123")
        assert "not implemented" in str(exc_info.value).lower()


# ============================================================================
# Test: Container.create_default Factory Method
# ============================================================================


class TestContainerCreateDefault:
    """Tests for Container.create_default() factory method."""

    def test_create_default_with_sqlite_cache(self, tmp_path):
        """create_default should create container with SQLite cache."""
        cache_path = str(tmp_path / "cache.db")

        with patch("goodtogo.container.GitHubAdapter") as mock_github:
            mock_github.return_value = MagicMock()

            container = Container.create_default(
                github_token="ghp_test_token",
                cache_type="sqlite",
                cache_path=cache_path,
            )

        assert container.github is not None
        assert isinstance(container.cache, SqliteCacheAdapter)
        assert container.parsers is not None

    def test_create_default_with_redis_cache(self):
        """create_default should create container with Redis cache when configured."""
        # Create a mock Redis cache adapter
        mock_redis_adapter = MagicMock()

        with patch("goodtogo.container.GitHubAdapter") as mock_github:
            mock_github.return_value = MagicMock()

            # Mock the Redis import and class
            with patch.dict(
                "sys.modules",
                {"goodtogo.adapters.cache_redis": MagicMock()},
            ):
                with patch("goodtogo.container._create_cache") as mock_create_cache:
                    mock_create_cache.return_value = mock_redis_adapter

                    container = Container.create_default(
                        github_token="ghp_test_token",
                        cache_type="redis",
                        redis_url="redis://localhost:6379",
                    )

        assert container is not None
        mock_create_cache.assert_called_once_with(
            "redis",
            ".goodtogo/cache.db",
            "redis://localhost:6379",
            ANY,  # time_provider
        )

    def test_create_default_with_none_cache(self):
        """create_default should create container with no-op cache."""
        with patch("goodtogo.container.GitHubAdapter") as mock_github:
            mock_github.return_value = MagicMock()

            container = Container.create_default(
                github_token="ghp_test_token",
                cache_type="none",
            )

        assert container.github is not None
        # "none" cache type uses InMemoryCacheAdapter as no-op
        assert isinstance(container.cache, InMemoryCacheAdapter)

    def test_create_default_passes_token_to_github_adapter(self, tmp_path):
        """create_default should pass token to GitHubAdapter."""
        cache_path = str(tmp_path / "cache.db")

        with patch("goodtogo.container.GitHubAdapter") as mock_github:
            mock_github.return_value = MagicMock()

            Container.create_default(
                github_token="ghp_my_secret_token",
                cache_type="sqlite",
                cache_path=cache_path,
            )

        mock_github.assert_called_once_with(
            token="ghp_my_secret_token",
            time_provider=ANY,
        )


# ============================================================================
# Test: _create_cache Internal Function
# ============================================================================


class TestCreateCacheFunction:
    """Tests for the _create_cache() helper function."""

    def test_create_cache_sqlite(self, tmp_path):
        """_create_cache should create SqliteCacheAdapter for 'sqlite' type."""
        cache_path = str(tmp_path / "test_cache.db")
        cache = _create_cache("sqlite", cache_path, None)

        assert isinstance(cache, SqliteCacheAdapter)

    def test_create_cache_none_type(self):
        """_create_cache should create InMemoryCacheAdapter for 'none' type."""
        cache = _create_cache("none", "/unused/path", None)

        # "none" type uses InMemoryCacheAdapter as a no-op cache
        assert isinstance(cache, InMemoryCacheAdapter)

    def test_create_cache_redis_requires_url(self):
        """_create_cache should raise ValueError if redis_url missing for redis type."""
        with pytest.raises(ValueError) as exc_info:
            _create_cache("redis", "/unused/path", None)

        assert "redis_url required" in str(exc_info.value)

    def test_create_cache_redis_with_url(self):
        """_create_cache should import and create RedisCacheAdapter when redis_url provided."""
        import sys

        # Create a mock RedisCacheAdapter class
        mock_redis_instance = MagicMock()
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        # Create a mock module with RedisCacheAdapter
        mock_module = MagicMock()
        mock_module.RedisCacheAdapter = mock_redis_class

        # Inject the mock module before calling _create_cache
        sys.modules["goodtogo.adapters.cache_redis"] = mock_module

        try:
            # Now call _create_cache which will import from the mocked module
            result = _create_cache("redis", "/unused/path", "redis://localhost:6379")

            # Verify the mock was called with the redis URL
            mock_redis_class.assert_called_once_with("redis://localhost:6379")
            assert result is mock_redis_instance
        finally:
            # Restore original modules
            if "goodtogo.adapters.cache_redis" in sys.modules:
                del sys.modules["goodtogo.adapters.cache_redis"]
            # Also clear from the import cache
            for key in list(sys.modules.keys()):
                if "cache_redis" in key:
                    del sys.modules[key]

    def test_create_cache_invalid_type_raises_error(self):
        """_create_cache should raise ValueError for unknown cache types."""
        with pytest.raises(ValueError) as exc_info:
            _create_cache("invalid_cache_type", "/path", None)

        assert "Unknown cache type" in str(exc_info.value)
        assert "invalid_cache_type" in str(exc_info.value)

    def test_create_cache_empty_type_raises_error(self):
        """_create_cache should raise ValueError for empty cache type string."""
        with pytest.raises(ValueError) as exc_info:
            _create_cache("", "/path", None)

        assert "Unknown cache type" in str(exc_info.value)


# ============================================================================
# Test: Container.create_for_testing Factory Method
# ============================================================================


class TestContainerCreateForTesting:
    """Tests for Container.create_for_testing() factory method."""

    def test_create_for_testing_uses_mock_github(self):
        """create_for_testing should use MockGitHubAdapter by default."""
        container = Container.create_for_testing()

        assert isinstance(container.github, MockGitHubAdapter)

    def test_create_for_testing_uses_memory_cache(self):
        """create_for_testing should use InMemoryCacheAdapter by default."""
        container = Container.create_for_testing()

        assert isinstance(container.cache, InMemoryCacheAdapter)

    def test_create_for_testing_accepts_custom_github(self):
        """create_for_testing should accept custom GitHub adapter."""
        custom_github = MagicMock()

        container = Container.create_for_testing(github=custom_github)

        assert container.github is custom_github

    def test_create_for_testing_accepts_custom_cache(self):
        """create_for_testing should accept custom cache adapter."""
        custom_cache = MagicMock()

        container = Container.create_for_testing(cache=custom_cache)

        assert container.cache is custom_cache

    def test_create_for_testing_has_all_parsers(self):
        """create_for_testing should include all default parsers."""
        container = Container.create_for_testing()

        assert ReviewerType.CODERABBIT in container.parsers
        assert ReviewerType.GREPTILE in container.parsers
        assert ReviewerType.CLAUDE in container.parsers
        assert ReviewerType.CURSOR in container.parsers
        assert ReviewerType.HUMAN in container.parsers
        assert ReviewerType.UNKNOWN in container.parsers


# ============================================================================
# Test: _create_default_parsers Function
# ============================================================================


class TestCreateDefaultParsers:
    """Tests for the _create_default_parsers() helper function."""

    def test_creates_all_reviewer_parsers(self):
        """_create_default_parsers should create parsers for all reviewer types."""
        parsers = _create_default_parsers()

        # Should have entries for all known reviewer types
        expected_types = [
            ReviewerType.CODERABBIT,
            ReviewerType.GREPTILE,
            ReviewerType.CLAUDE,
            ReviewerType.CURSOR,
            ReviewerType.HUMAN,
            ReviewerType.UNKNOWN,
        ]

        for reviewer_type in expected_types:
            assert reviewer_type in parsers
            assert parsers[reviewer_type] is not None

    def test_parsers_have_can_parse_method(self):
        """All parsers should have a can_parse method."""
        parsers = _create_default_parsers()

        for reviewer_type, parser in parsers.items():
            assert hasattr(parser, "can_parse")
            assert callable(parser.can_parse)

    def test_parsers_have_parse_method(self):
        """All parsers should have a parse method."""
        parsers = _create_default_parsers()

        for reviewer_type, parser in parsers.items():
            assert hasattr(parser, "parse")
            assert callable(parser.parse)
