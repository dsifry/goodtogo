"""Abstract base classes (ports) for the GoodToMerge hexagonal architecture.

This module defines the abstract interfaces (ports) that the core domain
depends on. Concrete implementations (adapters) must implement these
interfaces to integrate with external systems like GitHub API and caching.

Following the Ports & Adapters (Hexagonal) architecture pattern, these
interfaces ensure the core domain has no external dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from goodtogo.core.models import (
        CacheStats,
        CommentClassification,
        Priority,
        ReviewerType,
    )


class GitHubPort(ABC):
    """Abstract interface for GitHub API access.

    This port defines the contract for fetching PR-related data from GitHub.
    Implementations may use REST API, GraphQL, or any other mechanism to
    fulfill these requirements.

    All methods accept validated inputs (owner, repo, pr_number) and return
    raw dictionary data that will be processed by the analyzer.
    """

    @abstractmethod
    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch PR metadata.

        Retrieves basic PR information including title, state, head SHA,
        base branch, and timestamps.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Dictionary containing PR metadata with keys like:
            - 'number': PR number
            - 'title': PR title
            - 'state': PR state ('open', 'closed', 'merged')
            - 'head': Dictionary with 'sha' key for latest commit
            - 'base': Dictionary with 'ref' key for base branch
            - 'created_at': ISO timestamp
            - 'updated_at': ISO timestamp

        Raises:
            Exception: If the API request fails or PR is not found.
        """
        pass

    @abstractmethod
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all PR comments (inline + review + issue).

        Retrieves all types of comments associated with a PR:
        - Inline review comments on specific code lines
        - Review body comments
        - Issue-style comments on the PR itself

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Unique comment identifier
            - 'user': Dictionary with 'login' key for author
            - 'body': Comment text content
            - 'created_at': ISO timestamp
            - 'path': File path (for inline comments, None otherwise)
            - 'line': Line number (for inline comments, None otherwise)
            - 'in_reply_to_id': Parent comment ID if reply (None otherwise)

        Raises:
            Exception: If the API request fails.
        """
        pass

    @abstractmethod
    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all PR reviews.

        Retrieves all reviews submitted on a PR, including approvals,
        change requests, and comment-only reviews.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Unique review identifier
            - 'user': Dictionary with 'login' key for reviewer
            - 'body': Review body text (may be empty)
            - 'state': Review state ('APPROVED', 'CHANGES_REQUESTED',
                      'COMMENTED', 'DISMISSED', 'PENDING')
            - 'submitted_at': ISO timestamp

        Raises:
            Exception: If the API request fails.
        """
        pass

    @abstractmethod
    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all review threads with resolution status.

        Retrieves all review threads on a PR using GitHub's GraphQL API,
        which provides thread resolution status not available in REST API.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Thread node ID
            - 'is_resolved': Boolean indicating if thread is resolved
            - 'is_outdated': Boolean indicating if thread is outdated
                            (code has changed since comment)
            - 'path': File path the thread is attached to
            - 'line': Line number in the diff
            - 'comments': List of comments in the thread

        Raises:
            Exception: If the API request fails.
        """
        pass

    @abstractmethod
    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict:
        """Fetch CI/CD check status for a commit.

        Retrieves the combined status of all CI checks for a specific
        commit reference (usually the head SHA of the PR).

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            ref: Git reference (commit SHA, branch name, or tag).

        Returns:
            Dictionary containing:
            - 'state': Overall state ('success', 'failure', 'pending')
            - 'total_count': Total number of checks
            - 'statuses': List of individual status checks
            - 'check_runs': List of check runs (GitHub Actions, etc.)

            Each status/check_run contains:
            - 'name': Check name
            - 'state' or 'status': Individual check state
            - 'conclusion': Final conclusion (for completed checks)
            - 'target_url' or 'html_url': Link to check details

        Raises:
            Exception: If the API request fails.
        """
        pass


class CachePort(ABC):
    """Abstract interface for caching.

    This port defines the contract for caching PR analysis data to reduce
    API calls and improve response times. Implementations may use SQLite,
    Redis, or in-memory storage.

    All keys are strings constructed from validated inputs. Values are
    serialized as strings (typically JSON). TTL (Time To Live) controls
    automatic expiration.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get cached value.

        Retrieves a value from the cache if it exists and has not expired.

        Args:
            key: Cache key (e.g., 'pr:myorg:myrepo:123:meta').

        Returns:
            Cached value as string if found and not expired, None otherwise.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set cached value with TTL.

        Stores a value in the cache with an expiration time.

        Args:
            key: Cache key (e.g., 'pr:myorg:myrepo:123:meta').
            value: Value to cache (typically JSON string).
            ttl_seconds: Time to live in seconds. After this duration,
                        the entry is considered expired.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete cached value.

        Removes a specific entry from the cache.

        Args:
            key: Cache key to delete.
        """
        pass

    @abstractmethod
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern.

        Removes all cache entries whose keys match the given pattern.
        Pattern syntax depends on the implementation but typically
        supports glob-style wildcards (e.g., 'pr:myorg:myrepo:123:*').

        This is used to invalidate all cached data for a PR when
        a new commit is detected.

        Args:
            pattern: Pattern to match keys against (e.g., 'pr:*:*:123:*').
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> None:
        """Remove expired entries.

        Deletes all entries whose TTL has expired. This should be called
        periodically to prevent unbounded cache growth.

        For some implementations (like Redis), this may be a no-op as
        expiration is handled automatically.
        """
        pass

    @abstractmethod
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
        pass


class TimeProvider(ABC):
    """Abstract interface for time operations.

    This port defines the contract for time-related operations, enabling
    dependency injection of time for deterministic testing. Production
    code uses real system time; tests use a controllable mock.

    This pattern eliminates flaky tests caused by real time.sleep() calls
    and non-deterministic time.time() values.
    """

    @abstractmethod
    def now(self) -> float:
        """Get current time as Unix timestamp.

        Returns:
            Current time as seconds since epoch (float).
        """
        pass

    @abstractmethod
    def now_int(self) -> int:
        """Get current time as Unix timestamp (integer).

        Returns:
            Current time as seconds since epoch (int).
        """
        pass

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Sleep for the specified duration.

        In production, this calls time.sleep().
        In tests, this can advance simulated time instantly.

        Args:
            seconds: Duration to sleep in seconds.
        """
        pass


class ReviewerParser(ABC):
    """Abstract interface for reviewer-specific parsing.

    This port defines the contract for parsing comments from different
    automated reviewers (CodeRabbit, Greptile, Claude Code, etc.).

    Each parser knows how to:
    1. Identify comments from its reviewer (via author or body patterns)
    2. Classify comments as ACTIONABLE, NON_ACTIONABLE, or AMBIGUOUS
    3. Determine comment priority (CRITICAL, MAJOR, MINOR, TRIVIAL)

    Parsers are registered in the container and selected based on
    can_parse() returning True for a given comment.
    """

    @property
    @abstractmethod
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType enum value (e.g., ReviewerType.CODERABBIT,
            ReviewerType.GREPTILE, ReviewerType.HUMAN).
        """
        pass

    @abstractmethod
    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        Determines whether this parser is appropriate for a given comment
        based on the author name and/or body content patterns.

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if this parser can handle the comment, False otherwise.

        Note:
            Multiple parsers may return True for the same comment.
            The analyzer should use the first matching parser based
            on parser priority.
        """
        pass

    @abstractmethod
    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment and return classification.

        Analyzes the comment content and determines its classification,
        priority, and whether it requires human investigation.

        Args:
            comment: Dictionary containing comment data with keys:
                - 'body': Comment text content
                - 'user': Dictionary with 'login' key
                - 'id': Comment identifier
                - Additional keys depending on comment type

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
              (ACTIONABLE, NON_ACTIONABLE, or AMBIGUOUS)
            - priority: Priority enum value
              (CRITICAL, MAJOR, MINOR, TRIVIAL, or UNKNOWN)
            - requires_investigation: Boolean, True if the comment
              could not be definitively classified and needs human
              review (always True for AMBIGUOUS classification)

        Note:
            If classification is AMBIGUOUS, requires_investigation MUST
            be True. Never silently skip ambiguous comments.
        """
        pass
