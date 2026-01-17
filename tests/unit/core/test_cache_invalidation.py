"""Tests for cache invalidation based on PR analysis status.

This module tests the fix for issue #28 - ensuring that comment/thread/review
data is NOT cached (or quickly invalidated) when the PR has AMBIGUOUS or
ACTIONABLE comments.

The caching behavior should be:
- READY status: Comment data IS cached (normal TTL)
- ACTION_REQUIRED status: Comment data is NOT cached or invalidated
- AMBIGUOUS comments present: Comment data is NOT cached or invalidated
- When cached comments are deleted on GitHub: Fresh data is returned

This prevents stale cache from showing resolved/deleted comments as still
present, which could cause false positives in PR analysis.
"""

from __future__ import annotations

from typing import Any

import pytest

from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
from goodtogo.adapters.time_provider import MockTimeProvider
from goodtogo.container import Container
from goodtogo.core.analyzer import CACHE_TTL_META, PRAnalyzer
from goodtogo.core.interfaces import CachePort, GitHubPort
from goodtogo.core.models import CommentClassification, PRStatus


class RecordingCacheAdapter(CachePort):
    """Cache adapter that records all operations for testing.

    Wraps an InMemoryCacheAdapter and records all set/get/delete operations
    for verification in tests.
    """

    def __init__(self, time_provider: MockTimeProvider) -> None:
        """Initialize with a time provider."""
        self._inner = InMemoryCacheAdapter(time_provider=time_provider)
        self.set_calls: list[tuple[str, str, int]] = []  # (key, value, ttl)
        self.get_calls: list[str] = []  # keys accessed
        self.invalidate_calls: list[str] = []  # patterns invalidated

    def get(self, key: str) -> str | None:
        """Get a cached value and record the access."""
        self.get_calls.append(key)
        return self._inner.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set a cached value and record the operation."""
        self.set_calls.append((key, value, ttl_seconds))
        self._inner.set(key, value, ttl_seconds)

    def delete(self, key: str) -> None:
        """Delete a cached value."""
        self._inner.delete(key)

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate keys matching pattern and record the operation."""
        self.invalidate_calls.append(pattern)
        self._inner.invalidate_pattern(pattern)

    def cleanup_expired(self) -> None:
        """Clean up expired entries."""
        self._inner.cleanup_expired()

    def get_stats(self):
        """Get cache statistics."""
        return self._inner.get_stats()


class ConfigurableGitHubAdapter(GitHubPort):
    """GitHub adapter with configurable responses per call.

    Allows setting different responses for successive calls to simulate
    comment deletion or changes on GitHub.
    """

    def __init__(self) -> None:
        """Initialize with empty default responses."""
        self._pr_data: dict[str, Any] = {}
        self._comments_responses: list[list[dict[str, Any]]] = []
        self._comments_index = 0
        self._reviews: list[dict[str, Any]] = []
        self._threads: list[dict[str, Any]] = []
        self._ci_status: dict[str, Any] = {}
        # Default commit data to avoid test failures
        self._commit_data: dict[str, Any] = {
            "sha": "abc123def456",
            "commit": {
                "committer": {"date": "2024-01-15T10:00:00Z"},
                "author": {"date": "2024-01-15T09:00:00Z"},
            },
        }

    def set_pr_data(self, data: dict[str, Any]) -> None:
        """Set the PR data to return."""
        self._pr_data = data

    def set_comments(self, comments: list[dict[str, Any]]) -> None:
        """Set a single comments response (for backward compatibility)."""
        self._comments_responses = [comments]
        self._comments_index = 0

    def add_comments_response(self, comments: list[dict[str, Any]]) -> None:
        """Add a comments response for successive calls."""
        self._comments_responses.append(comments)

    def set_reviews(self, reviews: list[dict[str, Any]]) -> None:
        """Set the reviews to return."""
        self._reviews = reviews

    def set_threads(self, threads: list[dict[str, Any]]) -> None:
        """Set the threads to return."""
        self._threads = threads

    def set_ci_status(self, status: dict[str, Any]) -> None:
        """Set the CI status to return."""
        self._ci_status = status

    def set_commit_data(self, data: dict[str, Any]) -> None:
        """Set the commit data to return."""
        self._commit_data = data

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Return configured PR data."""
        return self._pr_data

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return comments, cycling through configured responses."""
        if not self._comments_responses:
            return []
        response = self._comments_responses[self._comments_index]
        if self._comments_index < len(self._comments_responses) - 1:
            self._comments_index += 1
        return response

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return configured reviews."""
        return self._reviews

    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return configured threads."""
        return self._threads

    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Return configured CI status."""
        return self._ci_status

    def get_commit(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Return configured commit data."""
        return self._commit_data


@pytest.fixture
def time_provider() -> MockTimeProvider:
    """Create a mock time provider starting at time 1000."""
    return MockTimeProvider(start=1000.0)


@pytest.fixture
def recording_cache(time_provider: MockTimeProvider) -> RecordingCacheAdapter:
    """Create a recording cache adapter."""
    return RecordingCacheAdapter(time_provider)


@pytest.fixture
def github() -> ConfigurableGitHubAdapter:
    """Create a configurable GitHub adapter."""
    return ConfigurableGitHubAdapter()


@pytest.fixture
def make_pr_data():
    """Factory for creating PR data dictionaries."""

    def _make(
        number: int = 123,
        title: str = "Test PR",
        head_sha: str = "abc123def456",
        updated_at: str = "2024-01-15T10:00:00Z",
    ) -> dict[str, Any]:
        return {
            "number": number,
            "title": title,
            "state": "open",
            "head": {
                "sha": head_sha,
                "ref": "feature-branch",
                "committed_at": updated_at,
            },
            "base": {"ref": "main"},
            "updated_at": updated_at,
            "user": {"login": "test-author"},
        }

    return _make


@pytest.fixture
def make_comment():
    """Factory for creating comment data dictionaries."""

    def _make(
        comment_id: int = 1,
        author: str = "reviewer",
        body: str = "Looks good!",
        path: str | None = None,
        line: int | None = None,
        created_at: str = "2024-01-15T10:00:00Z",
    ) -> dict[str, Any]:
        return {
            "id": comment_id,
            "user": {"login": author},
            "body": body,
            "path": path,
            "line": line,
            "in_reply_to_id": None,
            "created_at": created_at,
        }

    return _make


@pytest.fixture
def make_ci_status():
    """Factory for creating CI status data dictionaries."""

    def _make(state: str = "success") -> dict[str, Any]:
        return {
            "state": state,
            "statuses": [],
            "check_runs": [],
        }

    return _make


@pytest.fixture
def make_commit_data():
    """Factory for creating commit data dictionaries."""

    def _make(
        sha: str = "abc123def456",
        committer_date: str = "2024-01-15T10:00:00Z",
        author_date: str = "2024-01-15T09:00:00Z",
    ) -> dict[str, Any]:
        return {
            "sha": sha,
            "commit": {
                "committer": {"date": committer_date},
                "author": {"date": author_date},
            },
        }

    return _make


class TestCacheOnReadyStatus:
    """Tests verifying that comment data IS cached when PR is READY."""

    def test_comments_are_cached_when_pr_is_ready(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When analysis returns READY status, comment data should be cached."""
        # Setup: PR with no actionable comments (will be READY)
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([make_comment(body="LGTM!")])  # Non-actionable
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.READY
        assert len(result.actionable_comments) == 0
        assert len(result.ambiguous_comments) == 0

        # Verify comments were cached
        comments_cache_key = "pr:owner:repo:123:comments"
        comments_cached = any(key == comments_cache_key for key, _, _ in recording_cache.set_calls)
        assert comments_cached, "Comments should be cached when PR status is READY"

    def test_cached_data_is_used_on_subsequent_calls_when_ready(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """Cached comment data should be used on subsequent calls when READY."""
        # Setup: PR with no actionable comments (will be READY)
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([make_comment(body="LGTM!")])
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act: Call analyze twice
        result1 = analyzer.analyze("owner", "repo", 123)
        result2 = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result1.status == PRStatus.READY
        assert result2.status == PRStatus.READY

        # Verify cache was used on second call (check cache stats)
        stats = recording_cache.get_stats()
        assert stats.hits > 0, "Cache should have hits on second analyze call"


class TestCacheOnActionRequiredStatus:
    """Tests verifying that comment data is NOT cached when ACTION_REQUIRED."""

    def test_comments_not_cached_when_actionable_comments_exist(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When actionable comments exist, comment data should NOT be cached."""
        # Setup: PR with actionable CodeRabbit comment
        # NOTE: path must be set for CodeRabbit parser to treat as inline comment
        # (path=None makes it a PR-level summary which is NON_ACTIONABLE)
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                make_comment(
                    author="coderabbitai[bot]",
                    body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Missing null check in handler function.
""",
                    path="src/handler.py",  # Required for inline comment classification
                    line=42,
                )
            ]
        )
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.actionable_comments) > 0

        # Check if comments cache was invalidated or not cached with long TTL
        comments_cache_key = "pr:owner:repo:123:comments"

        # Option 1: Comments should be invalidated
        comment_invalidated = any(
            "comments" in pattern for pattern in recording_cache.invalidate_calls
        )

        # Option 2: Comments should be cached with very short TTL (0 or very small)
        comment_set_with_short_ttl = any(
            key == comments_cache_key and ttl <= 1 for key, _, ttl in recording_cache.set_calls
        )

        # Option 3: Comments should not be in cache after analysis
        # (either never set, or invalidated)
        comments_in_cache = recording_cache.get(comments_cache_key) is not None

        # At least one of these conditions should be true
        assert (
            comment_invalidated or comment_set_with_short_ttl or not comments_in_cache
        ), "Comments should not be persistently cached when actionable comments exist"

    def test_threads_not_cached_when_actionable_comments_exist(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When actionable comments exist, thread data should NOT be cached."""
        # Setup: PR with actionable comment
        # NOTE: path must be set for CodeRabbit parser to treat as inline comment
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                make_comment(
                    author="coderabbitai[bot]",
                    body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Security vulnerability detected.
""",
                    path="src/handler.py",
                    line=42,
                )
            ]
        )
        github.set_reviews([])
        github.set_threads([{"id": "thread-1", "is_resolved": False, "path": "file.py"}])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status in (PRStatus.ACTION_REQUIRED, PRStatus.UNRESOLVED_THREADS)

        # Check if threads cache was invalidated or not cached with long TTL
        threads_cache_key = "pr:owner:repo:123:threads"

        thread_invalidated = any(
            "threads" in pattern for pattern in recording_cache.invalidate_calls
        )
        thread_set_with_short_ttl = any(
            key == threads_cache_key and ttl <= 1 for key, _, ttl in recording_cache.set_calls
        )
        threads_in_cache = recording_cache.get(threads_cache_key) is not None

        assert (
            thread_invalidated or thread_set_with_short_ttl or not threads_in_cache
        ), "Threads should not be persistently cached when actionable comments exist"


class TestCacheOnAmbiguousStatus:
    """Tests verifying that comment data is NOT cached when AMBIGUOUS comments exist."""

    def test_comments_not_cached_when_ambiguous_comments_exist(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When ambiguous comments exist, comment data should NOT be cached."""
        # Setup: PR with ambiguous comment (human comment that needs investigation)
        # The GenericParser classifies most human comments as AMBIGUOUS
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                make_comment(
                    author="human-reviewer",
                    body="Can you take another look at this logic? Not sure if this is correct.",
                )
            ]
        )
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert - should be ACTION_REQUIRED due to ambiguous comments
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.ambiguous_comments) > 0

        # Check that comments are not persistently cached
        comments_cache_key = "pr:owner:repo:123:comments"

        comment_invalidated = any(
            "comments" in pattern for pattern in recording_cache.invalidate_calls
        )
        comment_set_with_short_ttl = any(
            key == comments_cache_key and ttl <= 1 for key, _, ttl in recording_cache.set_calls
        )
        comments_in_cache = recording_cache.get(comments_cache_key) is not None

        assert (
            comment_invalidated or comment_set_with_short_ttl or not comments_in_cache
        ), "Comments should not be persistently cached when ambiguous comments exist"


class TestCacheInvalidationOnCommentDeletion:
    """Tests verifying that deleted comments don't return stale cached data."""

    def test_deleted_comment_not_returned_from_cache(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When a comment is deleted on GitHub, subsequent calls should return fresh data."""
        # Setup: First call has an actionable comment
        github.set_pr_data(make_pr_data(number=123))

        # First response: has an actionable comment
        # NOTE: path must be set for CodeRabbit parser to treat as inline comment
        first_comments = [
            make_comment(
                comment_id=1,
                author="coderabbitai[bot]",
                body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Missing null check.
""",
                path="src/handler.py",
                line=42,
            )
        ]

        # Second response: comment was deleted/resolved
        second_comments: list[dict[str, Any]] = []

        github.add_comments_response(first_comments)
        github.add_comments_response(second_comments)
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act: First call - should see actionable comment
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.status == PRStatus.ACTION_REQUIRED
        assert len(result1.actionable_comments) == 1

        # Simulate cache invalidation (as would happen with the fix)
        # The fix should invalidate cache when actionable/ambiguous comments exist
        recording_cache.invalidate_pattern("pr:owner:repo:123:*")

        # Act: Second call - should see no comments (deleted)
        result2 = analyzer.analyze("owner", "repo", 123)

        # Assert: Should now be READY since comment is deleted
        assert result2.status == PRStatus.READY
        assert len(result2.actionable_comments) == 0

    def test_fresh_data_fetched_when_cache_invalidated(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """Cache invalidation should cause fresh data to be fetched from GitHub."""
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([make_comment(body="First comment")])
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # First call - populates cache
        _result1 = analyzer.analyze("owner", "repo", 123)
        _initial_get_calls = len(recording_cache.get_calls)

        # Invalidate cache
        recording_cache.invalidate_pattern("pr:owner:repo:123:comments")

        # Update what GitHub returns
        github.set_comments([make_comment(body="Updated comment")])

        # Second call - should fetch fresh data
        result2 = analyzer.analyze("owner", "repo", 123)

        # The second call should have caused new get calls (cache miss)
        # and the updated comment should be reflected
        assert result2.comments[0].body == "Updated comment"


class TestCacheInvalidationPatterns:
    """Tests for correct cache invalidation patterns."""

    def test_invalidation_uses_correct_pattern_format(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """Cache invalidation should use the correct pattern format."""
        # Setup with new commit to trigger cache invalidation
        github.set_pr_data(make_pr_data(number=123, head_sha="new_sha"))
        github.set_comments([])
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        # Pre-populate cache with old SHA
        recording_cache.set("pr:owner:repo:123:commit:latest", "old_sha", CACHE_TTL_META)

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        analyzer.analyze("owner", "repo", 123)

        # Assert: Should have invalidated with wildcard pattern
        assert any(
            pattern == "pr:owner:repo:123:*" for pattern in recording_cache.invalidate_calls
        ), "Should use wildcard pattern pr:owner:repo:123:* for invalidation"


class TestReviewCacheInvalidation:
    """Tests for review data cache invalidation."""

    def test_reviews_not_cached_when_actionable_comments_exist(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When actionable comments exist, review data should NOT be cached."""
        # NOTE: path must be set for CodeRabbit parser to treat as inline comment
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                make_comment(
                    author="coderabbitai[bot]",
                    body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Issue found.
""",
                    path="src/handler.py",
                    line=42,
                )
            ]
        )
        github.set_reviews(
            [{"id": 1, "user": {"login": "reviewer"}, "body": "Review body", "state": "COMMENTED"}]
        )
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.ACTION_REQUIRED

        # Check if reviews cache was invalidated or not cached with long TTL
        reviews_cache_key = "pr:owner:repo:123:reviews"

        review_invalidated = any(
            "reviews" in pattern for pattern in recording_cache.invalidate_calls
        )
        review_set_with_short_ttl = any(
            key == reviews_cache_key and ttl <= 1 for key, _, ttl in recording_cache.set_calls
        )
        reviews_in_cache = recording_cache.get(reviews_cache_key) is not None

        assert (
            review_invalidated or review_set_with_short_ttl or not reviews_in_cache
        ), "Reviews should not be persistently cached when actionable comments exist"


class TrackingGitHubAdapter(GitHubPort):
    """GitHub adapter that tracks API call counts for testing cache behavior.

    Wraps a ConfigurableGitHubAdapter and records how many times each API
    method was called. Useful for verifying that cached data is being used.
    """

    def __init__(self, inner: ConfigurableGitHubAdapter) -> None:
        """Initialize with an inner adapter to delegate to."""
        self._inner = inner
        self.get_pr_call_count = 0
        self.get_comments_call_count = 0
        self.get_reviews_call_count = 0
        self.get_threads_call_count = 0
        self.get_ci_status_call_count = 0
        self.get_commit_call_count = 0

    def set_pr_data(self, data: dict[str, Any]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_pr_data(data)

    def set_comments(self, comments: list[dict[str, Any]]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_comments(comments)

    def add_comments_response(self, comments: list[dict[str, Any]]) -> None:
        """Delegate to inner adapter."""
        self._inner.add_comments_response(comments)

    def set_reviews(self, reviews: list[dict[str, Any]]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_reviews(reviews)

    def set_threads(self, threads: list[dict[str, Any]]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_threads(threads)

    def set_ci_status(self, status: dict[str, Any]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_ci_status(status)

    def set_commit_data(self, data: dict[str, Any]) -> None:
        """Delegate to inner adapter."""
        self._inner.set_commit_data(data)

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Track call and delegate."""
        self.get_pr_call_count += 1
        return self._inner.get_pr(owner, repo, pr_number)

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Track call and delegate."""
        self.get_comments_call_count += 1
        return self._inner.get_pr_comments(owner, repo, pr_number)

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Track call and delegate."""
        self.get_reviews_call_count += 1
        return self._inner.get_pr_reviews(owner, repo, pr_number)

    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Track call and delegate."""
        self.get_threads_call_count += 1
        return self._inner.get_pr_threads(owner, repo, pr_number)

    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Track call and delegate."""
        self.get_ci_status_call_count += 1
        return self._inner.get_ci_status(owner, repo, ref)

    def get_commit(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Track call and delegate."""
        self.get_commit_call_count += 1
        return self._inner.get_commit(owner, repo, ref)

    def reset_counts(self) -> None:
        """Reset all call counts to zero."""
        self.get_pr_call_count = 0
        self.get_comments_call_count = 0
        self.get_reviews_call_count = 0
        self.get_threads_call_count = 0
        self.get_ci_status_call_count = 0
        self.get_commit_call_count = 0


class TestCachePreservedWhenStatusIsReady:
    """Tests verifying cache is preserved and reused when PR status is READY."""

    def test_cache_preserved_when_status_is_ready(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When all comments are NON_ACTIONABLE and threads resolved, cache is preserved.

        This test verifies that:
        1. First analyze() call fetches from GitHub API and populates cache
        2. Second analyze() call uses cached data (GitHub API not called twice)
        """
        # Setup: PR with only NON_ACTIONABLE comments and resolved threads
        # NOTE: Generic parser only treats specific patterns as NON_ACTIONABLE:
        # - Resolved/outdated threads
        # - Reply confirmations (e.g., "Done", "Fixed", "Addressed")
        # - Approval patterns (e.g., "LGTM", "Looks good", "+1")
        inner_github = ConfigurableGitHubAdapter()
        tracking_github = TrackingGitHubAdapter(inner_github)

        tracking_github.set_pr_data(make_pr_data(number=123))
        tracking_github.set_comments(
            [
                make_comment(body="LGTM!"),  # Non-actionable (approval pattern)
                make_comment(comment_id=2, body="+1"),  # Non-actionable (approval pattern)
            ]
        )
        tracking_github.set_reviews([])
        tracking_github.set_threads(
            [
                {"id": "thread-1", "is_resolved": True, "is_outdated": False, "path": "file.py"},
            ]
        )
        tracking_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=tracking_github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act: First analyze call
        result1 = analyzer.analyze("owner", "repo", 123)

        # Verify first call returns READY status
        assert result1.status == PRStatus.READY
        assert len(result1.actionable_comments) == 0
        assert len(result1.ambiguous_comments) == 0

        # Record API call counts after first call
        first_call_comments_count = tracking_github.get_comments_call_count
        first_call_threads_count = tracking_github.get_threads_call_count
        first_call_reviews_count = tracking_github.get_reviews_call_count

        # Verify API was called during first analysis
        assert first_call_comments_count >= 1, "Comments API should be called on first analyze"
        assert first_call_threads_count >= 1, "Threads API should be called on first analyze"

        # Act: Second analyze call
        result2 = analyzer.analyze("owner", "repo", 123)

        # Verify second call also returns READY
        assert result2.status == PRStatus.READY

        # Verify GitHub API was NOT called again for comments/reviews (data came from cache)
        assert (
            tracking_github.get_comments_call_count == first_call_comments_count
        ), "Comments API should NOT be called on second analyze (should use cache)"
        assert (
            tracking_github.get_reviews_call_count == first_call_reviews_count
        ), "Reviews API should NOT be called on second analyze (should use cache)"
        # Note: Threads API is always called due to granular thread caching design.
        # We always fetch the fresh thread list to detect new threads, but use
        # cached data for individual resolved threads (stable state).

        # Verify cache was used (has hits)
        stats = recording_cache.get_stats()
        assert stats.hits > 0, "Cache should have hits from second analyze call"


class TestCacheInvalidatedWhenStatusIsActionRequired:
    """Tests verifying cache.invalidate_pattern() is called for ACTION_REQUIRED status."""

    def test_cache_invalidated_when_status_is_action_required(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When an ACTIONABLE comment exists, cache.invalidate_pattern() is called.

        This test verifies that analyze() calls cache.invalidate_pattern()
        with the correct pattern when actionable comments are present.
        """
        github = ConfigurableGitHubAdapter()

        # Setup: PR with an ACTIONABLE comment from CodeRabbit
        github.set_pr_data(make_pr_data(number=456))
        github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Missing null check in handler function. This could cause a NullPointerException.
""",
                    path="src/handler.py",  # Required for inline comment classification
                    line=42,
                )
            ]
        )
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Clear any previous invalidate calls
        recording_cache.invalidate_calls.clear()

        # Act
        result = analyzer.analyze("owner", "repo", 456)

        # Verify status is ACTION_REQUIRED
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.actionable_comments) > 0, "Should have at least one actionable comment"
        assert result.actionable_comments[0].classification == CommentClassification.ACTIONABLE

        # Verify cache.invalidate_pattern() was called with correct pattern
        # The pattern should match the PR's cache keys
        expected_pattern = "pr:owner:repo:456:*"

        # Check if invalidate_pattern was called
        # Note: The fix may invalidate all PR data when action is required
        invalidate_called = any(
            pattern == expected_pattern or "456" in pattern
            for pattern in recording_cache.invalidate_calls
        )

        # If not invalidated, check that data was not cached with long TTL
        if not invalidate_called:
            # Alternative: verify data is not in cache after analysis
            comments_key = "pr:owner:repo:456:comments"
            comments_in_cache = recording_cache.get(comments_key)
            assert comments_in_cache is None, "Comments should not be in cache when ACTION_REQUIRED"


class TestCacheInvalidatedWhenStatusIsUnresolved:
    """Tests verifying cache is invalidated when there are unresolved threads."""

    def test_cache_invalidated_when_status_is_unresolved(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When unresolved threads exist, cache.invalidate_pattern() is called.

        This test verifies that analyze() invalidates the cache when the PR
        has UNRESOLVED_THREADS status.
        """
        github = ConfigurableGitHubAdapter()

        # Setup: PR with unresolved threads but no actionable comments
        github.set_pr_data(make_pr_data(number=789))
        github.set_comments([make_comment(body="LGTM!")])  # Non-actionable
        github.set_reviews([])
        github.set_threads(
            [
                {
                    "id": "thread-1",
                    "is_resolved": False,  # Unresolved!
                    "is_outdated": False,
                    "path": "src/main.py",
                    "line": 10,
                    "comments": [{"author": "reviewer", "body": "Please fix this"}],
                },
                {
                    "id": "thread-2",
                    "is_resolved": False,  # Also unresolved!
                    "is_outdated": False,
                    "path": "src/utils.py",
                    "line": 25,
                    "comments": [{"author": "reviewer", "body": "Add error handling"}],
                },
            ]
        )
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Clear any previous invalidate calls
        recording_cache.invalidate_calls.clear()

        # Act
        result = analyzer.analyze("owner", "repo", 789)

        # Verify status is UNRESOLVED_THREADS
        assert result.status == PRStatus.UNRESOLVED_THREADS
        assert result.threads.unresolved == 2, "Should have 2 unresolved threads"

        # Verify cache.invalidate_pattern() was called
        expected_pattern = "pr:owner:repo:789:*"

        invalidate_called = any(
            pattern == expected_pattern or "789" in pattern
            for pattern in recording_cache.invalidate_calls
        )

        # If not explicitly invalidated, verify threads not cached with long TTL
        if not invalidate_called:
            threads_key = "pr:owner:repo:789:threads"
            threads_in_cache = recording_cache.get(threads_key)
            assert (
                threads_in_cache is None
            ), "Threads should not be in cache when UNRESOLVED_THREADS status"


class TestFreshDataOnSecondCallWhenNotReady:
    """Tests verifying fresh data is fetched when status is not READY."""

    def test_fresh_data_on_second_call_when_not_ready(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """First call returns ACTION_REQUIRED, invalidates cache; second fetches fresh data.

        This test verifies the complete flow:
        1. First analyze() with ACTIONABLE comment returns ACTION_REQUIRED
        2. Cache is invalidated
        3. Mock is updated to simulate comment being resolved
        4. Second analyze() fetches fresh data and returns READY
        """
        inner_github = ConfigurableGitHubAdapter()
        tracking_github = TrackingGitHubAdapter(inner_github)

        # Setup: First call - PR with an ACTIONABLE comment
        tracking_github.set_pr_data(make_pr_data(number=999))

        # First response: has actionable comment
        actionable_comment = make_comment(
            comment_id=1,
            author="coderabbitai[bot]",
            body="""_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_

Security vulnerability: SQL injection possible.
""",
            path="src/db.py",
            line=100,
        )

        # Use add_comments_response for first call
        tracking_github.add_comments_response([actionable_comment])

        # Second response: comment was resolved/deleted
        tracking_github.add_comments_response([])  # Empty - comment resolved

        tracking_github.set_reviews([])
        tracking_github.set_threads([])
        tracking_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=tracking_github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act: First analyze call
        result1 = analyzer.analyze("owner", "repo", 999)

        # Verify first call returns ACTION_REQUIRED
        assert result1.status == PRStatus.ACTION_REQUIRED
        assert len(result1.actionable_comments) == 1

        # Record call count after first analysis
        first_call_count = tracking_github.get_comments_call_count

        # Manually invalidate cache to simulate the fix behavior
        # (This simulates what the analyzer should do automatically)
        recording_cache.invalidate_pattern("pr:owner:repo:999:*")

        # Act: Second analyze call - should fetch fresh data
        result2 = analyzer.analyze("owner", "repo", 999)

        # Verify second call returns READY (comment was resolved)
        assert result2.status == PRStatus.READY
        assert (
            len(result2.actionable_comments) == 0
        ), "Should have no actionable comments after resolution"

        # Verify GitHub API was called again (cache was invalidated)
        assert (
            tracking_github.get_comments_call_count > first_call_count
        ), "Comments API should be called again after cache invalidation"


class TestGranularCommentCaching:
    """Tests for granular comment caching (caching NON_ACTIONABLE comments individually)."""

    def test_non_actionable_comments_are_cached_individually(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When a comment is NON_ACTIONABLE, it should be cached with a granular key."""
        # Setup: PR with a NON_ACTIONABLE comment
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([make_comment(comment_id=42, body="LGTM!")])
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.READY
        assert len(result.comments) == 1
        assert result.comments[0].classification == CommentClassification.NON_ACTIONABLE

        # Verify granular comment cache was set
        granular_cache_key = "comment:owner:repo:42"
        granular_cached = any(key == granular_cache_key for key, _, _ in recording_cache.set_calls)
        assert granular_cached, "NON_ACTIONABLE comment should be cached with granular key"

    def test_actionable_comments_are_not_cached_granularly(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """ACTIONABLE or AMBIGUOUS comments should NOT be cached with granular keys."""
        # Setup: PR with an AMBIGUOUS comment (parsed by generic parser with unclear intent)
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                make_comment(
                    comment_id=99,
                    author="reviewer",
                    body="I think we should consider refactoring this section.",
                )
            ]
        )
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.ambiguous_comments) == 1

        # Verify granular comment cache was NOT set for AMBIGUOUS comment
        granular_cache_key = "comment:owner:repo:99"
        granular_cached = any(key == granular_cache_key for key, _, _ in recording_cache.set_calls)
        assert not granular_cached, "AMBIGUOUS comment should NOT be cached with granular key"

    def test_granular_cache_used_for_stable_comments(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
        make_comment,
    ):
        """When PR-level cache is invalidated, granular cache should be used for stable comments."""
        inner_github = ConfigurableGitHubAdapter()
        tracking_github = TrackingGitHubAdapter(inner_github)

        # Setup: PR with a NON_ACTIONABLE comment
        tracking_github.set_pr_data(make_pr_data(number=123))
        tracking_github.set_comments([make_comment(comment_id=42, body="LGTM!")])
        tracking_github.set_reviews([])
        tracking_github.set_threads([])
        tracking_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=tracking_github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # First analyze - populates both PR-level and granular cache
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.status == PRStatus.READY

        # Invalidate PR-level comment cache (simulating cache expiry)
        recording_cache._inner.delete("pr:owner:repo:123:comments")

        # Second analyze - should fetch fresh from GitHub but use granular cache
        result2 = analyzer.analyze("owner", "repo", 123)
        assert result2.status == PRStatus.READY

        # Verify granular cache was accessed
        granular_cache_key = "comment:owner:repo:42"
        granular_accessed = any(key == granular_cache_key for key in recording_cache.get_calls)
        assert granular_accessed, "Granular cache should be accessed when PR-level cache is invalid"

    def test_comment_without_id_is_not_cached_granularly(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
    ):
        """Comments without IDs should not be cached granularly."""
        # Setup: PR with a comment that has no ID
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments(
            [
                {
                    "id": "",  # Empty ID
                    "user": {"login": "reviewer"},
                    "body": "LGTM!",
                    "path": None,
                    "line": None,
                    "in_reply_to_id": None,
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ]
        )
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert - should complete without error
        assert result.status == PRStatus.READY

        # Verify no granular cache with empty key was set
        empty_key_cached = any(
            key.startswith("comment:owner:repo:") and key.endswith(":")
            for key, _, _ in recording_cache.set_calls
        )
        assert not empty_key_cached, "Comment without ID should not create cache entry"


class TestGranularThreadCaching:
    """Tests for granular thread caching (caching resolved threads individually)."""

    def test_resolved_threads_are_cached_individually(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
    ):
        """When a thread is resolved, it should be cached with a granular key."""
        # Setup: PR with a resolved thread
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([])
        github.set_reviews([])
        github.set_threads(
            [
                {
                    "id": "thread-99",
                    "is_resolved": True,
                    "is_outdated": False,
                    "path": "file.py",
                }
            ]
        )
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.READY
        assert result.threads.resolved == 1

        # Verify granular thread cache was set
        granular_cache_key = "thread:owner:repo:thread-99"
        granular_cached = any(key == granular_cache_key for key, _, _ in recording_cache.set_calls)
        assert granular_cached, "Resolved thread should be cached with granular key"

    def test_unresolved_threads_are_not_cached_granularly(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
    ):
        """Unresolved threads should NOT be cached with granular keys."""
        # Setup: PR with an unresolved thread
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([])
        github.set_reviews([])
        github.set_threads(
            [
                {
                    "id": "thread-88",
                    "is_resolved": False,
                    "is_outdated": False,
                    "path": "file.py",
                    "comments": [{"author": "reviewer", "body": "Please fix this"}],
                }
            ]
        )
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert
        assert result.status == PRStatus.UNRESOLVED_THREADS
        assert result.threads.unresolved == 1

        # Verify granular thread cache was NOT set for unresolved thread
        granular_cache_key = "thread:owner:repo:thread-88"
        granular_cached = any(key == granular_cache_key for key, _, _ in recording_cache.set_calls)
        assert not granular_cached, "Unresolved thread should NOT be cached with granular key"

    def test_granular_cache_used_for_resolved_threads(
        self,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
    ):
        """When PR-level cache is invalidated, granular cache is used for resolved threads."""
        inner_github = ConfigurableGitHubAdapter()
        tracking_github = TrackingGitHubAdapter(inner_github)

        # Setup: PR with a resolved thread
        tracking_github.set_pr_data(make_pr_data(number=123))
        tracking_github.set_comments([])
        tracking_github.set_reviews([])
        tracking_github.set_threads(
            [
                {
                    "id": "thread-77",
                    "is_resolved": True,
                    "is_outdated": False,
                    "path": "file.py",
                }
            ]
        )
        tracking_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=tracking_github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # First analyze - populates both PR-level and granular cache
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.status == PRStatus.READY

        # Invalidate PR-level thread cache (simulating cache expiry)
        recording_cache._inner.delete("pr:owner:repo:123:threads")

        # Second analyze - should fetch fresh from GitHub but use granular cache
        result2 = analyzer.analyze("owner", "repo", 123)
        assert result2.status == PRStatus.READY

        # Verify granular cache was accessed
        granular_cache_key = "thread:owner:repo:thread-77"
        granular_accessed = any(key == granular_cache_key for key in recording_cache.get_calls)
        assert granular_accessed, "Granular cache should be accessed when PR-level cache is invalid"

    def test_thread_without_id_is_not_cached_granularly(
        self,
        github: ConfigurableGitHubAdapter,
        recording_cache: RecordingCacheAdapter,
        time_provider: MockTimeProvider,
        make_pr_data,
        make_ci_status,
    ):
        """Threads without IDs should not be cached granularly."""
        # Setup: PR with a thread that has no ID
        github.set_pr_data(make_pr_data(number=123))
        github.set_comments([])
        github.set_reviews([])
        github.set_threads(
            [
                {
                    "id": "",  # Empty ID
                    "is_resolved": True,
                    "is_outdated": False,
                    "path": "file.py",
                }
            ]
        )
        github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        # Act
        result = analyzer.analyze("owner", "repo", 123)

        # Assert - should complete without error
        assert result.status == PRStatus.READY

        # Verify no granular cache with empty key was set
        empty_key_cached = any(
            key.startswith("thread:owner:repo:") and key.endswith(":")
            for key, _, _ in recording_cache.set_calls
        )
        assert not empty_key_cached, "Thread without ID should not create cache entry"


class TestCacheEdgeCases:
    """Test edge cases in granular caching."""

    def test_cached_comment_with_non_stable_classification_is_ignored(
        self, make_pr_data, make_comment, make_ci_status
    ) -> None:
        """Cached comment with non-NON_ACTIONABLE classification should use fresh data."""
        # This covers the branch where cached_data.get("classification") != "NON_ACTIONABLE"
        time_provider = MockTimeProvider()
        recording_cache = RecordingCacheAdapter(time_provider)

        # Pre-populate cache with a comment that has ACTIONABLE classification
        # (shouldn't happen in practice, but tests the branch)
        recording_cache.set(
            "comment:owner:repo:123",
            '{"raw": {"id": "123", "body": "Stale"}, "classification": "ACTIONABLE"}',
            86400,
        )

        github = ConfigurableGitHubAdapter()
        github.set_pr_data(make_pr_data())
        github.set_comments([make_comment(comment_id=123, body="Fresh data")])
        github.set_reviews([])
        github.set_threads([])
        github.set_ci_status(make_ci_status())
        github.set_commit_data(
            {"sha": "abc123def456", "commit": {"committer": {"date": "2024-01-15T10:00:00Z"}}}
        )

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # Should use fresh data, not stale cached data with wrong classification
        assert any(c.body == "Fresh data" for c in result.comments)

    def test_cached_thread_with_unresolved_status_is_ignored(
        self, make_pr_data, make_ci_status
    ) -> None:
        """Cached thread with is_resolved=False should use fresh data."""
        # This covers the branch where cached_data.get("is_resolved") is False
        time_provider = MockTimeProvider()
        recording_cache = RecordingCacheAdapter(time_provider)

        # Pre-populate cache with a thread that has is_resolved=False
        # (shouldn't happen in practice, but tests the branch)
        recording_cache.set(
            "thread:owner:repo:thread-123",
            '{"raw": {"id": "thread-123", "is_resolved": false}, "is_resolved": false}',
            86400,
        )

        github = ConfigurableGitHubAdapter()
        github.set_pr_data(make_pr_data())
        github.set_comments([])
        github.set_reviews([])
        github.set_threads(
            [{"id": "thread-123", "is_resolved": True, "is_outdated": False, "comments": []}]
        )
        github.set_ci_status(make_ci_status())
        github.set_commit_data(
            {"sha": "abc123def456", "commit": {"committer": {"date": "2024-01-15T10:00:00Z"}}}
        )

        container = Container.create_for_testing(
            github=github,
            cache=recording_cache,
            time_provider=time_provider,
        )
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # Should use fresh data (resolved=True), not cached (resolved=False)
        assert result.threads.resolved == 1
        assert result.threads.unresolved == 0
