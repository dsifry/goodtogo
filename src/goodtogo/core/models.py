"""Data models for GoodToMerge PR analysis.

This module defines all the Pydantic models and enums used throughout
the GoodToMerge library for representing PR analysis results, comments,
CI status, and thread information.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PRStatus(str, Enum):
    """Final PR status - maps to exit codes.

    Exit code mapping:
        READY: 0 - All clear, ready to merge
        ACTION_REQUIRED: 1 - Actionable comments exist
        UNRESOLVED_THREADS: 2 - Unresolved threads exist
        CI_FAILING: 3 - CI/CD checks failing
        ERROR: 4 - Error fetching data
    """

    READY = "READY"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    UNRESOLVED_THREADS = "UNRESOLVED"
    CI_FAILING = "CI_FAILING"
    ERROR = "ERROR"


class CommentClassification(str, Enum):
    """Comment classification result.

    Used to categorize comments from automated reviewers and humans
    to determine what action (if any) is required.
    """

    ACTIONABLE = "ACTIONABLE"
    """Comment that must be addressed before merge."""

    NON_ACTIONABLE = "NON_ACTIONABLE"
    """Comment that can be safely ignored (informational, nitpick, etc.)."""

    AMBIGUOUS = "AMBIGUOUS"
    """Comment that needs agent investigation - cannot determine classification."""


class Priority(str, Enum):
    """Comment priority level.

    Used to sort and prioritize actionable comments. Maps to severity
    indicators from various automated reviewers.
    """

    CRITICAL = "CRITICAL"
    """Must fix immediately - blocking issue."""

    MAJOR = "MAJOR"
    """Must fix before merge - significant issue."""

    MINOR = "MINOR"
    """Should fix - notable but not blocking."""

    TRIVIAL = "TRIVIAL"
    """Nice to fix - minor improvement."""

    UNKNOWN = "UNKNOWN"
    """Could not determine priority."""


class ReviewerType(str, Enum):
    """Automated reviewer identification.

    Used to select the appropriate parser for processing comments
    from different automated code review tools.
    """

    CODERABBIT = "coderabbit"
    """CodeRabbit AI code reviewer."""

    GREPTILE = "greptile"
    """Greptile code reviewer."""

    CLAUDE = "claude"
    """Claude Code reviewer."""

    CURSOR = "cursor"
    """Cursor/Bugbot code reviewer."""

    HUMAN = "human"
    """Human reviewer (not automated)."""

    UNKNOWN = "unknown"
    """Unknown reviewer type."""


class Comment(BaseModel):
    """Individual comment with classification.

    Represents a single comment from a PR review, including its
    classification result and metadata for addressing it.
    """

    id: str
    """Unique identifier for the comment."""

    author: str
    """Username of the comment author."""

    reviewer_type: ReviewerType
    """Type of reviewer that posted this comment."""

    body: str
    """Full text content of the comment."""

    classification: CommentClassification
    """Classification result (ACTIONABLE, NON_ACTIONABLE, AMBIGUOUS)."""

    priority: Priority
    """Priority level for actionable comments."""

    requires_investigation: bool
    """True if AMBIGUOUS and needs agent investigation."""

    thread_id: Optional[str]
    """ID of the review thread this comment belongs to, if any."""

    is_resolved: bool
    """Whether the thread containing this comment is resolved."""

    is_outdated: bool
    """Whether this comment is outdated (code has changed)."""

    file_path: Optional[str]
    """Path to the file this comment references, if any."""

    line_number: Optional[int]
    """Line number in the file this comment references, if any."""

    created_at: str
    """ISO 8601 timestamp when the comment was created."""

    addressed_in_commit: Optional[str]
    """SHA of commit that addressed this comment, if known."""

    url: Optional[str] = None
    """URL to view this comment on GitHub, for agent workflows."""


class CICheck(BaseModel):
    """Individual CI check status.

    Represents a single CI/CD check run (e.g., build, test, lint).
    """

    name: str
    """Name of the CI check."""

    status: str
    """Current status: 'success', 'failure', or 'pending'."""

    conclusion: Optional[str]
    """Final conclusion of the check, if completed."""

    url: Optional[str]
    """URL to the check details/logs."""


class CIStatus(BaseModel):
    """Aggregate CI status.

    Provides summary statistics and individual check details
    for all CI/CD checks on a PR.
    """

    state: str
    """Overall state: 'success', 'failure', or 'pending'."""

    total_checks: int
    """Total number of CI checks."""

    passed: int
    """Number of checks that passed."""

    failed: int
    """Number of checks that failed."""

    pending: int
    """Number of checks still running or pending."""

    checks: list[CICheck]
    """List of individual CI check results."""


class UnresolvedThread(BaseModel):
    """Detailed information about an unresolved review thread.

    Contains all data an agent needs to resolve a thread without
    additional API calls, including the GraphQL node ID for the
    resolution mutation.
    """

    id: str
    """GraphQL node ID for resolution mutation."""

    url: Optional[str]
    """Link to thread in GitHub UI (if available)."""

    path: str
    """File path the thread is attached to."""

    line: Optional[int]
    """Line number in the diff."""

    author: str
    """Username of the first comment author."""

    body_preview: str
    """First 200 characters of the first comment body."""


class ThreadSummary(BaseModel):
    """Thread resolution summary.

    Provides counts of review thread states for determining
    if unresolved discussions remain.
    """

    total: int
    """Total number of review threads."""

    resolved: int
    """Number of resolved threads."""

    unresolved: int
    """Number of unresolved threads."""

    outdated: int
    """Number of outdated threads (code changed since comment)."""

    unresolved_threads: list[UnresolvedThread]
    """Detailed information about each unresolved thread for agent workflows."""


class CacheStats(BaseModel):
    """Cache performance metrics.

    Used to report cache effectiveness for performance tuning.
    """

    hits: int
    """Number of cache hits."""

    misses: int
    """Number of cache misses."""

    hit_rate: float
    """Cache hit rate as a decimal (0.0 to 1.0)."""


class PRAnalysisResult(BaseModel):
    """Complete PR analysis result - main output.

    This is the primary output model returned by PRAnalyzer.analyze().
    It contains all information needed for an AI agent to determine
    the next action for a PR.
    """

    status: PRStatus
    """Final PR status determining readiness to merge."""

    pr_number: int
    """PR number being analyzed."""

    repo_owner: str
    """Repository owner (organization or user)."""

    repo_name: str
    """Repository name."""

    latest_commit_sha: str
    """SHA of the latest commit on the PR branch."""

    latest_commit_timestamp: str
    """ISO 8601 timestamp of the latest commit."""

    ci_status: CIStatus
    """Aggregate CI/CD check status."""

    threads: ThreadSummary
    """Summary of review thread resolution status."""

    comments: list[Comment]
    """All comments on the PR with classifications."""

    actionable_comments: list[Comment]
    """Filtered list of comments requiring action."""

    ambiguous_comments: list[Comment]
    """Filtered list of comments requiring investigation."""

    action_items: list[str]
    """Human-readable list of actions needed."""

    needs_action: bool
    """True if any action is required before merge."""

    cache_stats: Optional[CacheStats]
    """Cache performance metrics, if caching is enabled."""
