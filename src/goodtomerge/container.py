"""Dependency injection container for GoodToMerge.

This module provides the Container class that manages all dependencies
for the GoodToMerge library, following the Ports & Adapters (Hexagonal)
architecture pattern.

The Container provides factory methods for creating production and test
configurations, ensuring all dependencies are properly initialized with
appropriate adapters.

Example:
    # Production usage
    container = Container.create_default(
        github_token="ghp_...",
        cache_type="sqlite",
        cache_path=".goodtomerge/cache.db",
    )

    # Test usage
    container = Container.create_for_testing()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from goodtomerge.adapters.cache_memory import InMemoryCacheAdapter
from goodtomerge.adapters.cache_sqlite import SqliteCacheAdapter
from goodtomerge.adapters.github import GitHubAdapter
from goodtomerge.core.interfaces import CachePort, GitHubPort, ReviewerParser
from goodtomerge.core.models import ReviewerType
from goodtomerge.parsers.claude import ClaudeCodeParser
from goodtomerge.parsers.coderabbit import CodeRabbitParser
from goodtomerge.parsers.cursor import CursorBugbotParser
from goodtomerge.parsers.generic import GenericParser
from goodtomerge.parsers.greptile import GreptileParser


class MockGitHubAdapter(GitHubPort):
    """Mock GitHub adapter for testing.

    This adapter raises NotImplementedError for all methods by default.
    Test code should replace individual methods with mock implementations
    as needed.

    Example:
        container = Container.create_for_testing()
        container.github.get_pr = MagicMock(return_value={"number": 123})
    """

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return "MockGitHubAdapter()"

    def __str__(self) -> str:
        """Return string representation."""
        return self.__repr__()

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata.

        Raises:
            NotImplementedError: Always raised - override in tests.
        """
        raise NotImplementedError(
            "MockGitHubAdapter.get_pr() not implemented. " "Replace with a mock in your test."
        )

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all PR comments.

        Raises:
            NotImplementedError: Always raised - override in tests.
        """
        raise NotImplementedError(
            "MockGitHubAdapter.get_pr_comments() not implemented. "
            "Replace with a mock in your test."
        )

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all PR reviews.

        Raises:
            NotImplementedError: Always raised - override in tests.
        """
        raise NotImplementedError(
            "MockGitHubAdapter.get_pr_reviews() not implemented. "
            "Replace with a mock in your test."
        )

    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all review threads.

        Raises:
            NotImplementedError: Always raised - override in tests.
        """
        raise NotImplementedError(
            "MockGitHubAdapter.get_pr_threads() not implemented. "
            "Replace with a mock in your test."
        )

    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Fetch CI/CD check status.

        Raises:
            NotImplementedError: Always raised - override in tests.
        """
        raise NotImplementedError(
            "MockGitHubAdapter.get_ci_status() not implemented. "
            "Replace with a mock in your test."
        )


@dataclass
class Container:
    """DI container - all dependencies injected, no global state.

    The Container holds all adapters and parsers needed by the PRAnalyzer.
    It provides factory methods for creating properly configured instances
    for production and testing scenarios.

    Attributes:
        github: GitHub API adapter implementing GitHubPort interface.
        cache: Cache adapter implementing CachePort interface.
        parsers: Dictionary mapping ReviewerType to parser implementations.

    Example:
        # Create production container
        container = Container.create_default(github_token="ghp_...")
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Create test container with mocks
        container = Container.create_for_testing()
        container.github.get_pr = MagicMock(return_value={...})
    """

    github: GitHubPort
    cache: CachePort
    parsers: dict[ReviewerType, ReviewerParser]

    @classmethod
    def create_default(
        cls,
        github_token: str,
        cache_type: str = "sqlite",
        cache_path: str = ".goodtomerge/cache.db",
        redis_url: str | None = None,
    ) -> Container:
        """Factory for standard production configuration.

        Creates a Container with production-ready adapters:
        - GitHubAdapter for real GitHub API access
        - SQLite or Redis cache based on cache_type
        - All default reviewer parsers

        Args:
            github_token: GitHub personal access token or OAuth token.
                         Must have 'repo' scope for private repositories.
            cache_type: Cache backend to use. One of:
                       - "sqlite": Local SQLite database (default)
                       - "redis": Redis server (requires redis_url)
                       - "none": No caching (NoCacheAdapter)
            cache_path: Path to SQLite database file. Only used when
                       cache_type is "sqlite". Default: ".goodtomerge/cache.db"
            redis_url: Redis connection URL. Required when cache_type is "redis".
                      Example: "redis://localhost:6379" or "rediss://..." for TLS.

        Returns:
            Configured Container instance ready for production use.

        Raises:
            ValueError: If cache_type is "redis" but redis_url is not provided,
                       or if cache_type is unknown.
        """
        cache = _create_cache(cache_type, cache_path, redis_url)
        return cls(
            github=GitHubAdapter(token=github_token),
            cache=cache,
            parsers=_create_default_parsers(),
        )

    @classmethod
    def create_for_testing(
        cls,
        github: GitHubPort | None = None,
        cache: CachePort | None = None,
    ) -> Container:
        """Factory for tests - all mocks by default.

        Creates a Container suitable for testing with mock adapters:
        - MockGitHubAdapter that raises NotImplementedError (override as needed)
        - InMemoryCacheAdapter for fast, ephemeral caching
        - All default reviewer parsers

        Args:
            github: Optional GitHubPort implementation to use instead of mock.
                   If None, uses MockGitHubAdapter.
            cache: Optional CachePort implementation to use instead of mock.
                  If None, uses InMemoryCacheAdapter.

        Returns:
            Container instance configured for testing.

        Example:
            # Basic test setup
            container = Container.create_for_testing()

            # With custom mock
            mock_github = MagicMock(spec=GitHubPort)
            mock_github.get_pr.return_value = {"number": 123, "title": "Test"}
            container = Container.create_for_testing(github=mock_github)
        """
        return cls(
            github=github if github is not None else MockGitHubAdapter(),
            cache=cache if cache is not None else InMemoryCacheAdapter(),
            parsers=_create_default_parsers(),
        )


def _create_cache(cache_type: str, path: str, redis_url: str | None) -> CachePort:
    """Create cache adapter based on type.

    Factory function that creates the appropriate cache adapter
    based on the specified cache type.

    Args:
        cache_type: Type of cache to create. One of:
                   - "sqlite": Local SQLite database
                   - "redis": Redis server
                   - "none": No-op cache adapter
        path: Path to SQLite database file (only used for "sqlite").
        redis_url: Redis connection URL (only used for "redis").

    Returns:
        CachePort implementation matching the requested type.

    Raises:
        ValueError: If cache_type is "redis" but redis_url is not provided,
                   or if cache_type is unknown.
    """
    if cache_type == "sqlite":
        return SqliteCacheAdapter(path)
    elif cache_type == "redis":
        if not redis_url:
            raise ValueError("redis_url required for redis cache")
        # Import Redis adapter only when needed to avoid requiring redis package
        from goodtomerge.adapters.cache_redis import (  # type: ignore[import-untyped]
            RedisCacheAdapter,
        )

        result: CachePort = RedisCacheAdapter(redis_url)
        return result
    elif cache_type == "none":
        # No-op cache - use in-memory with immediate expiration
        # For a true no-op, we could create a NoCacheAdapter, but
        # InMemoryCacheAdapter with TTL=0 effectively accomplishes this
        return InMemoryCacheAdapter()
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")


def _create_default_parsers() -> dict[ReviewerType, ReviewerParser]:
    """Create default parser registry.

    Creates a dictionary mapping each ReviewerType to its corresponding
    parser implementation. The GenericParser is used as a fallback for
    both HUMAN and UNKNOWN reviewer types.

    Returns:
        Dictionary with all default parsers registered:
        - CODERABBIT: CodeRabbitParser
        - GREPTILE: GreptileParser
        - CLAUDE: ClaudeCodeParser
        - CURSOR: CursorBugbotParser
        - HUMAN: GenericParser (fallback)
        - UNKNOWN: GenericParser (fallback)
    """
    return {
        ReviewerType.CODERABBIT: CodeRabbitParser(),
        ReviewerType.GREPTILE: GreptileParser(),
        ReviewerType.CLAUDE: ClaudeCodeParser(),
        ReviewerType.CURSOR: CursorBugbotParser(),
        ReviewerType.HUMAN: GenericParser(),
        ReviewerType.UNKNOWN: GenericParser(),
    }
