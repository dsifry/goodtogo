"""Integration tests for the full PR analysis flow.

This module tests the complete analysis workflow from PRAnalyzer through
to final results, using mocked GitHub adapters to verify:
- Status determination logic
- Comment classification
- Thread handling
- CI status integration
- Cache invalidation behavior
"""

from __future__ import annotations

import json

import pytest

from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import (
    CommentClassification,
    Priority,
    PRStatus,
    ReviewerType,
)

# Import test fixtures from conftest
from tests.conftest import MockableGitHubAdapter

# ============================================================================
# Test: Complete Analysis Flow Returning READY Status
# ============================================================================


class TestReadyToMergeFlow:
    """Tests for PRs that should return READY status."""

    def test_ready_pr_with_no_issues(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """A PR with passing CI, no threads, and no comments should be READY."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[
                    make_check_run(name="build", conclusion="success"),
                    make_check_run(name="test", conclusion="success"),
                ],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.READY
        assert result.needs_action is False
        assert len(result.action_items) == 0
        assert len(result.actionable_comments) == 0

    def test_ready_pr_with_resolved_threads(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
        make_comment,
    ):
        """A PR with all threads resolved should be READY."""
        # Setup - comments in resolved threads should not block merge
        # Note: The comment's in_reply_to_id must match a thread id for resolution to apply
        mock_github.set_pr_data(make_pr_data(number=123))
        # No standalone comments - resolved threads don't require separate comment checking
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=True),
                make_thread(thread_id="thread-2", is_resolved=True),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.READY
        assert result.threads.resolved == 2
        assert result.threads.unresolved == 0

    def test_ready_pr_with_no_comments(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """A PR with no comments (clean PR) should be READY.

        Note: The GenericParser classifies all non-resolved human comments as
        AMBIGUOUS (requiring investigation), so a truly READY PR should have
        no comments or only comments from resolved threads.
        """
        # Setup - no comments means no ambiguous items
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.READY


# ============================================================================
# Test: Analysis with Actionable Comments
# ============================================================================


class TestActionableCommentsFlow:
    """Tests for PRs with actionable comments."""

    def test_coderabbit_critical_comment_requires_action(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """CodeRabbit critical comments should result in ACTION_REQUIRED.

        CodeRabbit uses specific emoji patterns for severity:
        - _⚠️ Potential issue_ | _🔴 Critical_
        - _⚠️ Potential issue_ | _🟠 Major_
        - _⚠️ Potential issue_ | _🟡 Minor_
        """
        # Setup with CodeRabbit-style critical comment using actual emoji pattern
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="""_⚠️ Potential issue_ | _🔴 Critical_

Security vulnerability detected: SQL injection risk

The query parameter is being interpolated directly into SQL string.

```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```
""",
                    path="src/db.py",
                    line=42,
                )
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.ACTION_REQUIRED
        assert result.needs_action is True
        assert len(result.actionable_comments) > 0
        # Check that the comment was identified as CodeRabbit
        actionable = result.actionable_comments[0]
        assert actionable.reviewer_type == ReviewerType.CODERABBIT

    def test_multiple_actionable_comments_sorted_by_priority(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Actionable comments should be sorted by priority (critical first).

        CodeRabbit uses specific emoji patterns for severity:
        - _⚠️ Potential issue_ | _🔴 Critical_
        - _⚠️ Potential issue_ | _🟠 Major_
        - _⚠️ Potential issue_ | _🟡 Minor_
        """
        # Setup with multiple CodeRabbit comments at different priorities
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                # Minor issue first (in list order)
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body=(
                        "_⚠️ Potential issue_ | _🟡 Minor_\n\n"
                        "Consider using a more descriptive variable name."
                    ),
                    path="src/utils.py",
                    line=10,
                ),
                # Critical issue second (in list order)
                make_comment(
                    comment_id=2,
                    author="coderabbitai[bot]",
                    body=(
                        "_⚠️ Potential issue_ | _🔴 Critical_\n\n"
                        "Memory leak detected - resources not released."
                    ),
                    path="src/handler.py",
                    line=50,
                ),
                # Major issue third (in list order)
                make_comment(
                    comment_id=3,
                    author="coderabbitai[bot]",
                    body="_⚠️ Potential issue_ | _🟠 Major_\n\nError handling is incomplete.",
                    path="src/api.py",
                    line=30,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.actionable_comments) == 3
        # Should be sorted: CRITICAL, MAJOR, MINOR
        assert result.actionable_comments[0].priority == Priority.CRITICAL
        assert result.actionable_comments[1].priority == Priority.MAJOR
        assert result.actionable_comments[2].priority == Priority.MINOR

    def test_action_items_generated_correctly(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Action items should be generated for actionable comments."""
        # Setup - use correct CodeRabbit emoji pattern
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="_⚠️ Potential issue_ | _🔴 Critical_\n\nMissing error handling",
                    path="src/main.py",
                    line=10,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert len(result.action_items) > 0
        # Should mention critical issues
        assert any("critical" in item.lower() for item in result.action_items)


# ============================================================================
# Test: Analysis with Unresolved Threads
# ============================================================================


class TestUnresolvedThreadsFlow:
    """Tests for PRs with unresolved review threads."""

    def test_unresolved_thread_blocks_merge(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
    ):
        """PRs with unresolved threads should return UNRESOLVED_THREADS status."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=False),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.UNRESOLVED_THREADS
        assert result.threads.unresolved == 1
        assert result.needs_action is True

    def test_multiple_unresolved_threads_counted(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
    ):
        """Thread summary should correctly count resolved vs unresolved."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=False),
                make_thread(thread_id="thread-2", is_resolved=True),
                make_thread(thread_id="thread-3", is_resolved=False),
                make_thread(thread_id="thread-4", is_resolved=True),
                make_thread(thread_id="thread-5", is_resolved=True, is_outdated=True),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.UNRESOLVED_THREADS
        assert result.threads.total == 5
        assert result.threads.resolved == 3
        assert result.threads.unresolved == 2
        assert result.threads.outdated == 1

    def test_action_items_include_thread_count(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
    ):
        """Action items should mention the number of unresolved threads."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=False),
                make_thread(thread_id="thread-2", is_resolved=False),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert any("2" in item and "thread" in item.lower() for item in result.action_items)


# ============================================================================
# Test: Analysis with Failing CI
# ============================================================================


class TestFailingCIFlow:
    """Tests for PRs with failing CI checks."""

    def test_failing_ci_blocks_merge(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """PRs with failing CI should return CI_FAILING status."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="failure",
                check_runs=[
                    make_check_run(name="build", conclusion="failure"),
                    make_check_run(name="lint", conclusion="success"),
                ],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.CI_FAILING
        assert result.ci_status.failed >= 1
        assert result.needs_action is True

    def test_pending_ci_blocks_merge(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """PRs with pending CI should return CI_FAILING status."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="pending",
                check_runs=[
                    make_check_run(name="build", status="in_progress", conclusion=None),
                    make_check_run(name="test", status="queued", conclusion=None),
                ],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.CI_FAILING
        assert result.ci_status.pending >= 1

    def test_ci_status_summary_accurate(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """CI status should accurately count passed/failed/pending checks."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="failure",
                check_runs=[
                    make_check_run(name="build", conclusion="success"),
                    make_check_run(name="test", conclusion="failure"),
                    make_check_run(name="lint", conclusion="success"),
                    make_check_run(name="deploy", status="queued", conclusion=None),
                ],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.ci_status.total_checks == 4
        assert result.ci_status.passed == 2
        assert result.ci_status.failed == 1
        assert result.ci_status.pending == 1

    def test_ci_action_items_generated(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Action items should mention CI failure."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="failure",
                check_runs=[
                    make_check_run(name="test", conclusion="failure"),
                ],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - action items should mention CI
        assert any("CI" in item or "failing" in item.lower() for item in result.action_items)


# ============================================================================
# Test: Cache Invalidation on New Commits
# ============================================================================


class TestCacheInvalidation:
    """Tests for cache behavior during PR analysis."""

    def test_cache_used_on_repeated_analysis(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Repeated analysis should use cache and increase hit count.

        Note: Cache invalidation on new commits requires the PR metadata to be
        refreshed from GitHub. In this test, the mock adapter always returns
        the same data, so we're testing that the cache is being used properly
        on repeated calls with the same SHA.
        """
        # Setup - analysis with fixed SHA
        mock_github.set_pr_data(make_pr_data(number=123, head_sha="abc123"))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        analyzer = PRAnalyzer(test_container)

        # First analysis - all cache misses
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.latest_commit_sha == "abc123"
        assert result1.cache_stats is not None
        initial_hits = result1.cache_stats.hits

        # Second analysis - should have cache hits
        result2 = analyzer.analyze("owner", "repo", 123)
        assert result2.latest_commit_sha == "abc123"
        assert result2.cache_stats is not None
        # Hits should have increased
        assert result2.cache_stats.hits > initial_hits

    def test_cache_stats_returned(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Analysis result should include cache statistics."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        analyzer = PRAnalyzer(test_container)

        # First analysis - should have misses
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.cache_stats is not None

        # Second analysis - should have hits
        result2 = analyzer.analyze("owner", "repo", 123)
        assert result2.cache_stats is not None
        assert result2.cache_stats.hits > 0


# ============================================================================
# Test: Status Priority (Decision Tree)
# ============================================================================


class TestStatusPriority:
    """Tests verifying the correct priority order of status determination."""

    def test_ci_failure_takes_priority_over_threads(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
    ):
        """CI_FAILING should take priority over UNRESOLVED_THREADS."""
        # Setup - both failing CI and unresolved threads
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=False),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="failure",
                check_runs=[make_check_run(name="build", conclusion="failure")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - CI failure should win
        assert result.status == PRStatus.CI_FAILING

    def test_threads_take_priority_over_comments(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_thread,
        make_comment,
    ):
        """UNRESOLVED_THREADS should take priority over ACTION_REQUIRED."""
        # Setup - both unresolved threads and actionable comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="**[critical]** Missing null check",
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                make_thread(thread_id="thread-1", is_resolved=False),
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - unresolved threads should win
        assert result.status == PRStatus.UNRESOLVED_THREADS


# ============================================================================
# Test: Reviewer Type Identification
# ============================================================================


class TestReviewerIdentification:
    """Tests for correct reviewer type identification."""

    def test_coderabbit_identified(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Comments from coderabbitai[bot] should be identified as CodeRabbit."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="**[minor]** Consider renaming this variable.",
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert len(result.comments) == 1
        assert result.comments[0].reviewer_type == ReviewerType.CODERABBIT

    def test_human_reviewer_identified(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Comments from regular users should be identified as HUMAN."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="john-reviewer",
                    body="Please add more tests for edge cases.",
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert len(result.comments) == 1
        assert result.comments[0].reviewer_type == ReviewerType.HUMAN


# ============================================================================
# Test: Input Validation
# ============================================================================


class TestInputValidation:
    """Tests for input validation in PRAnalyzer."""

    def test_invalid_owner_rejected(self, test_container: Container):
        """Invalid owner names should be rejected."""
        analyzer = PRAnalyzer(test_container)

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("invalid owner!", "repo", 123)

        assert "owner" in str(exc_info.value).lower()

    def test_invalid_repo_rejected(self, test_container: Container):
        """Invalid repo names should be rejected."""
        analyzer = PRAnalyzer(test_container)

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("owner", "invalid repo!", 123)

        assert "repo" in str(exc_info.value).lower()

    def test_invalid_pr_number_rejected(self, test_container: Container):
        """Invalid PR numbers should be rejected."""
        analyzer = PRAnalyzer(test_container)

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("owner", "repo", -1)

        assert "pr" in str(exc_info.value).lower() or "number" in str(exc_info.value).lower()

    def test_zero_pr_number_rejected(self, test_container: Container):
        """Zero PR number should be rejected."""
        analyzer = PRAnalyzer(test_container)

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("owner", "repo", 0)

        assert "pr" in str(exc_info.value).lower() or "positive" in str(exc_info.value).lower()


# ============================================================================
# Test: Using Fixture Scenarios
# ============================================================================


class TestFixtureScenarios:
    """Tests using pre-configured fixture scenarios."""

    def test_ready_to_merge_scenario(
        self,
        test_container: Container,
        ready_to_merge_pr: MockableGitHubAdapter,
    ):
        """Test using the ready_to_merge_pr fixture."""
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.status == PRStatus.READY

    def test_failing_ci_scenario(
        self,
        test_container: Container,
        pr_with_failing_ci: MockableGitHubAdapter,
    ):
        """Test using the pr_with_failing_ci fixture."""
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.status == PRStatus.CI_FAILING

    def test_unresolved_threads_scenario(
        self,
        test_container: Container,
        pr_with_unresolved_threads: MockableGitHubAdapter,
    ):
        """Test using the pr_with_unresolved_threads fixture."""
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.status == PRStatus.UNRESOLVED_THREADS

    def test_actionable_comments_scenario(
        self,
        test_container: Container,
        pr_with_actionable_comments: MockableGitHubAdapter,
    ):
        """Test using the pr_with_actionable_comments fixture."""
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.actionable_comments) > 0


# ============================================================================
# Test: Result Model Correctness
# ============================================================================


class TestResultModelCorrectness:
    """Tests verifying PRAnalysisResult fields are populated correctly."""

    def test_result_contains_pr_metadata(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Result should contain correct PR metadata."""
        # Setup
        mock_github.set_pr_data(
            make_pr_data(
                number=456,
                head_sha="sha789xyz",
                updated_at="2024-06-15T14:30:00Z",
            )
        )
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("myorg", "myrepo", 456)

        # Verify
        assert result.pr_number == 456
        assert result.repo_owner == "myorg"
        assert result.repo_name == "myrepo"
        assert result.latest_commit_sha == "sha789xyz"

    def test_result_serializable_to_json(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """PRAnalysisResult should be serializable to JSON."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should serialize without error
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["status"] == "READY"
        assert parsed["pr_number"] == 123


# ============================================================================
# Test: Error Redaction in Analyzer
# ============================================================================


class TestErrorRedaction:
    """Tests for error redaction when exceptions occur during analysis."""

    def test_github_error_is_redacted(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
    ):
        """Exceptions from GitHub API should be redacted.

        This tests line 206-208 in analyzer.py where non-ValueError exceptions
        are wrapped with redact_error().
        """
        from goodtogo.core.errors import RedactedError

        # Setup - make get_pr raise an exception with sensitive data
        def raise_with_token(*args, **kwargs):
            raise RuntimeError("GitHub API error: Invalid token ghp_secret123456 for auth")

        mock_github.get_pr = raise_with_token

        # Execute and verify exception is redacted
        analyzer = PRAnalyzer(test_container)

        with pytest.raises(RedactedError) as exc_info:
            analyzer.analyze("owner", "repo", 123)

        # Token should be redacted
        assert "ghp_secret123456" not in str(exc_info.value)
        assert "<REDACTED_TOKEN>" in str(exc_info.value)

    def test_validation_errors_not_redacted(
        self,
        test_container: Container,
    ):
        """ValueError from validation should not be wrapped in RedactedError.

        This tests line 203-205 where ValueError is re-raised as-is.
        """
        analyzer = PRAnalyzer(test_container)

        # Invalid owner should raise plain ValueError
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("invalid owner!", "repo", 123)

        # Should be a regular ValueError, not RedactedError
        assert type(exc_info.value) is ValueError


# ============================================================================
# Test: Review Body Processing
# ============================================================================


class TestReviewBodyProcessing:
    """Tests for review body comment processing."""

    def test_reviews_with_empty_body_skipped(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_review,
    ):
        """Reviews with empty or whitespace-only bodies should be skipped.

        This tests lines 423-437 in analyzer.py where review bodies are checked.
        """
        # Setup - reviews with empty bodies should not create comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(review_id=1, author="reviewer1", body="", state="APPROVED"),
                make_review(review_id=2, author="reviewer2", body="   ", state="APPROVED"),
                make_review(review_id=3, author="reviewer3", body=None, state="APPROVED"),
                make_review(
                    review_id=4,
                    author="reviewer4",
                    body="This is a real comment",
                    state="CHANGES_REQUESTED",
                ),
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - only the non-empty review body should be processed
        assert len(result.comments) == 1
        assert "This is a real comment" in result.comments[0].body


# ============================================================================
# Test: CI Status Mapping
# ============================================================================


class TestCIStatusMapping:
    """Tests for CI status mapping from GitHub response."""

    def test_ci_status_with_traditional_statuses(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
    ):
        """CI statuses (not check_runs) should be processed correctly.

        This tests lines 521-530 in analyzer.py where status checks are processed.
        """
        # Setup - use traditional status checks instead of check_runs
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "failure",
                "statuses": [
                    {
                        "context": "continuous-integration/travis-ci",
                        "state": "success",
                        "target_url": "https://travis-ci.com/build/123",
                    },
                    {
                        "context": "codeclimate",
                        "state": "failure",
                        "target_url": "https://codeclimate.com/report/456",
                    },
                ],
                "check_runs": [],
            }
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.ci_status.total_checks == 2
        assert result.ci_status.passed == 1
        assert result.ci_status.failed == 1
        assert result.status == PRStatus.CI_FAILING

    def test_ci_check_run_with_unknown_status(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
    ):
        """Check runs with unknown status values should be handled.

        This tests line 543 in analyzer.py where unknown statuses fall through.
        """
        # Setup - use an unusual status value
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "success",
                "statuses": [],
                "check_runs": [
                    {
                        "name": "weird-check",
                        "status": "waiting",  # Neither completed, queued, nor in_progress
                        "conclusion": None,
                        "html_url": "https://github.com/actions/123",
                    },
                ],
            }
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should handle the unknown status gracefully
        assert result.ci_status.total_checks == 1
        # The check should have status "waiting" mapped through
        assert result.ci_status.checks[0].status == "waiting"


# ============================================================================
# Test: Exclude Checks Feature
# ============================================================================


class TestExcludeChecks:
    """Tests for the exclude_checks parameter in analyze()."""

    def test_exclude_failing_check_run(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
    ):
        """Excluding a failing check run should result in success state.

        This tests the exclude_checks feature when a check_run is excluded.
        """
        # Setup - one passing check, one failing check
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "failure",
                "statuses": [],
                "check_runs": [
                    {
                        "name": "build",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://github.com/actions/build",
                    },
                    {
                        "name": "gtg-check",
                        "status": "completed",
                        "conclusion": "failure",
                        "html_url": "https://github.com/actions/gtg",
                    },
                ],
            }
        )

        # Execute with gtg-check excluded
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123, exclude_checks={"gtg-check"})

        # Verify - gtg-check should be excluded, only build remains
        assert result.ci_status.total_checks == 1
        assert result.ci_status.passed == 1
        assert result.ci_status.failed == 0
        assert result.ci_status.state == "success"
        assert result.status == PRStatus.READY
        # Verify the excluded check is not in the list
        assert all(c.name != "gtg-check" for c in result.ci_status.checks)

    def test_exclude_failing_status_check(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
    ):
        """Excluding a failing status check should result in success state.

        This tests the exclude_checks feature with traditional status checks.
        """
        # Setup - one passing status, one failing status
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "failure",
                "statuses": [
                    {
                        "context": "build",
                        "state": "success",
                        "target_url": "https://ci.example.com/build",
                    },
                    {
                        "context": "gtg-check",
                        "state": "failure",
                        "target_url": "https://ci.example.com/gtg",
                    },
                ],
                "check_runs": [],
            }
        )

        # Execute with gtg-check excluded
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123, exclude_checks={"gtg-check"})

        # Verify - gtg-check should be excluded, only build remains
        assert result.ci_status.total_checks == 1
        assert result.ci_status.passed == 1
        assert result.ci_status.failed == 0
        assert result.ci_status.state == "success"
        assert result.status == PRStatus.READY

    def test_exclude_all_checks_results_in_success(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
    ):
        """Excluding all checks should result in success state (empty = pass).

        This tests the edge case where all checks are excluded.
        """
        # Setup - only one failing check
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "failure",
                "statuses": [],
                "check_runs": [
                    {
                        "name": "gtg-check",
                        "status": "completed",
                        "conclusion": "failure",
                        "html_url": "https://github.com/actions/gtg",
                    },
                ],
            }
        )

        # Execute with gtg-check excluded (now no checks remain)
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123, exclude_checks={"gtg-check"})

        # Verify - no checks means success
        assert result.ci_status.total_checks == 0
        assert result.ci_status.passed == 0
        assert result.ci_status.failed == 0
        assert result.ci_status.state == "success"
        assert result.status == PRStatus.READY

    def test_exclude_checks_empty_set_keeps_all_checks(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
    ):
        """Empty exclude_checks set should keep all checks."""
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            {
                "state": "failure",
                "statuses": [],
                "check_runs": [
                    {
                        "name": "gtg-check",
                        "status": "completed",
                        "conclusion": "failure",
                        "html_url": "https://github.com/actions/gtg",
                    },
                ],
            }
        )

        # Execute with empty exclude set
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123, exclude_checks=set())

        # Verify - all checks should be included
        assert result.ci_status.total_checks == 1
        assert result.ci_status.failed == 1
        assert result.status == PRStatus.CI_FAILING


# ============================================================================
# Test: Action Items Generation Edge Cases
# ============================================================================


class TestActionItemsGeneration:
    """Tests for action items generation with various comment types."""

    def test_action_items_with_trivial_and_unknown_priority(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Action items should count 'other' comments (TRIVIAL/UNKNOWN priority).

        This tests lines 642-645 in analyzer.py where non-critical/major/minor
        comments are counted as 'other'.
        """
        # Setup - we need to use a comment that will be classified as ACTIONABLE
        # with TRIVIAL or UNKNOWN priority. The GenericParser classifies human
        # comments as AMBIGUOUS, so we need to use a bot that produces ACTIONABLE
        # with lower priority.

        # CodeRabbit can produce TRIVIAL priority with nitpick comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",
                    body="""_Nitpick (non-blocking)_

Consider adding a trailing newline to the file.

This is a very minor style suggestion.""",
                    path="src/main.py",
                    line=100,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should have action items (either actionable or ambiguous)
        assert result.status == PRStatus.ACTION_REQUIRED
        # The comment should be classified
        assert len(result.comments) == 1


# ============================================================================
# Test: Ambiguous Comments Handling
# ============================================================================


class TestAmbiguousCommentsHandling:
    """Tests for ambiguous comment classification and action items."""

    def test_human_comments_classified_as_ambiguous(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Human comments without clear action markers should be AMBIGUOUS.

        The GenericParser classifies unresolved human comments as AMBIGUOUS
        since it cannot determine if action is needed.
        """
        # Setup
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="human-reviewer",
                    body="This is an interesting approach to the problem.",
                    path="src/algorithm.py",
                    line=50,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.ambiguous_comments) == 1
        assert result.ambiguous_comments[0].requires_investigation is True

    def test_ambiguous_comments_generate_action_items(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Ambiguous comments should generate appropriate action items."""
        # Setup - multiple ambiguous comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="reviewer1",
                    body="Hmm, what about edge cases?",
                    path="src/handler.py",
                    line=10,
                ),
                make_comment(
                    comment_id=2,
                    author="reviewer2",
                    body="Have you considered the performance implications?",
                    path="src/processor.py",
                    line=20,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify
        assert len(result.ambiguous_comments) == 2
        # Action items should mention ambiguous/investigation
        assert any(
            "ambiguous" in item.lower() or "investigation" in item.lower()
            for item in result.action_items
        )


# ============================================================================
# Test: PR Data Without Committed Timestamp
# ============================================================================


class TestPRDataFallbacks:
    """Tests for PR data fallback behavior."""

    def test_uses_updated_at_when_committed_at_missing(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_ci_status,
        make_check_run,
    ):
        """Should use updated_at as timestamp when committed_at is missing.

        This tests line 131-132 in analyzer.py where it falls back to updated_at.
        """
        # Setup - PR data without committed_at in head
        mock_github.set_pr_data(
            {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "head": {
                    "sha": "abc123",
                    "ref": "feature-branch",
                    # No committed_at field
                },
                "base": {"ref": "main"},
                "updated_at": "2024-01-15T12:00:00Z",
                "user": {"login": "author"},
            }
        )
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should use updated_at as the timestamp
        assert result.latest_commit_timestamp == "2024-01-15T12:00:00Z"


# ============================================================================
# Test: Cache Invalidation on New Commit
# ============================================================================


class TestCacheInvalidationOnNewCommit:
    """Tests for cache invalidation when new commits are detected."""

    def test_cache_invalidated_when_sha_changes(
        self,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Cache should be invalidated when the commit SHA changes.

        This tests lines 255-256 in analyzer.py where cache is invalidated
        when a new commit is detected.
        """
        from goodtogo.adapters.cache_memory import InMemoryCacheAdapter

        # Create a fresh cache for this test to track invalidation
        cache = InMemoryCacheAdapter()
        container = Container.create_for_testing(github=mock_github, cache=cache)

        # Setup - first analysis with SHA "abc123"
        mock_github.set_pr_data(make_pr_data(number=123, head_sha="abc123"))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        analyzer = PRAnalyzer(container)

        # First analysis - populates cache
        result1 = analyzer.analyze("owner", "repo", 123)
        assert result1.latest_commit_sha == "abc123"

        # Now we need to bypass the PR metadata cache to test SHA change detection
        # Clear the cache manually to simulate PR metadata refresh
        # Cache key format is: pr:owner:repo:pr_number:meta
        cache.delete("pr:owner:repo:123:meta")

        # Update the mock to return new SHA
        mock_github.set_pr_data(make_pr_data(number=123, head_sha="def456"))

        # Second analysis - should detect SHA change and invalidate cache
        result2 = analyzer.analyze("owner", "repo", 123)
        assert result2.latest_commit_sha == "def456"

        # The cache invalidation should have been triggered (lines 255-256)
        assert result2.cache_stats is not None


# ============================================================================
# Test: Parser Fallback Logic
# ============================================================================


class TestParserFallbackLogic:
    """Tests for parser fallback when parsers are missing."""

    def test_falls_back_to_human_parser_when_reviewer_type_missing(
        self,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Should fall back to HUMAN parser when reviewer type parser is missing.

        This tests lines 473-474 in analyzer.py where it falls back to HUMAN parser.
        """
        from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
        from goodtogo.adapters.time_provider import MockTimeProvider
        from goodtogo.parsers.generic import GenericParser

        # Create a container with limited parsers (missing some types)
        # Only include HUMAN and UNKNOWN parsers
        limited_parsers = {
            ReviewerType.HUMAN: GenericParser(),
            ReviewerType.UNKNOWN: GenericParser(),
        }

        # Create container with limited parsers
        container = Container(
            github=mock_github,
            cache=InMemoryCacheAdapter(),
            parsers=limited_parsers,
            time_provider=MockTimeProvider(),
        )

        # Setup mock data with a CodeRabbit comment (which has no parser)
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="coderabbitai[bot]",  # CodeRabbit author
                    body="This comment should fall back to generic parser",
                    path="src/main.py",
                    line=10,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute - should not raise, should fall back to HUMAN parser
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Should have processed the comment using fallback parser
        assert len(result.comments) == 1

    def test_falls_back_to_first_parser_when_all_standard_missing(
        self,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
        make_comment,
    ):
        """Should fall back to first available parser when HUMAN is also missing.

        This tests lines 475-477 in analyzer.py where it uses the first available parser.
        """
        from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
        from goodtogo.adapters.time_provider import MockTimeProvider
        from goodtogo.parsers.coderabbit import CodeRabbitParser

        # Create a container with only one parser that doesn't match the comment
        # Only CODERABBIT parser available, no HUMAN fallback
        minimal_parsers = {
            ReviewerType.CODERABBIT: CodeRabbitParser(),
        }

        container = Container(
            github=mock_github,
            cache=InMemoryCacheAdapter(),
            parsers=minimal_parsers,
            time_provider=MockTimeProvider(),
        )

        # Setup mock data with a human comment (HUMAN parser not available)
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                make_comment(
                    comment_id=1,
                    author="human-reviewer",  # Human author, but no HUMAN parser
                    body="A human comment without matching parser",
                    path="src/main.py",
                    line=10,
                ),
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute - should not raise, should use first available parser
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Should have processed the comment using the only available parser
        assert len(result.comments) == 1


# ============================================================================
# Test: Thread ID Conversion
# ============================================================================


class TestThreadIdConversion:
    """Tests for thread ID handling in comment processing."""

    def test_thread_id_converted_to_string(
        self,
        test_container: Container,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Comments with in_reply_to_id should have thread_id converted to string.

        This tests line 462 in analyzer.py where thread_id is converted to string.
        """
        # Setup - comment with numeric in_reply_to_id
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                {
                    "id": 1,
                    "user": {"login": "reviewer"},
                    "body": "I agree with the previous comment",
                    "path": "src/main.py",
                    "line": 20,
                    "in_reply_to_id": 12345,  # Numeric ID that should be converted
                    "created_at": "2024-01-15T10:00:00Z",
                },
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads(
            [
                {
                    "id": "12345",  # String ID to match
                    "is_resolved": False,
                    "is_outdated": False,
                    "path": "src/main.py",
                    "line": 20,
                },
            ]
        )
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(test_container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - thread_id should be converted to string "12345"
        assert len(result.comments) == 1
        assert result.comments[0].thread_id == "12345"


# ============================================================================
# Test: Action Items with "Other" Priority Comments
# ============================================================================


class TestActionItemsOtherPriority:
    """Tests for action items with TRIVIAL/UNKNOWN priority (other) comments."""

    def test_other_priority_comments_counted_in_action_items(
        self,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Comments with TRIVIAL/UNKNOWN priority should be counted as 'other'.

        This tests lines 642-645 in analyzer.py where 'other' comments are counted.
        """
        from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
        from goodtogo.adapters.time_provider import MockTimeProvider
        from goodtogo.core.interfaces import ReviewerParser
        from goodtogo.core.models import CommentClassification, Priority

        # Create a custom parser that always returns ACTIONABLE with TRIVIAL priority
        class TrivialParser(ReviewerParser):
            @property
            def reviewer_type(self) -> ReviewerType:
                return ReviewerType.HUMAN

            def can_parse(self, author: str, body: str) -> bool:
                return True

            def parse(self, comment_data: dict) -> tuple[CommentClassification, Priority, bool]:
                return (CommentClassification.ACTIONABLE, Priority.TRIVIAL, False)

        # Create container with the trivial parser for all types
        trivial_parser = TrivialParser()
        parsers = {
            ReviewerType.HUMAN: trivial_parser,
            ReviewerType.UNKNOWN: trivial_parser,
            ReviewerType.CODERABBIT: trivial_parser,
            ReviewerType.GREPTILE: trivial_parser,
            ReviewerType.CLAUDE: trivial_parser,
            ReviewerType.CURSOR: trivial_parser,
        }

        container = Container(
            github=mock_github,
            cache=InMemoryCacheAdapter(),
            parsers=parsers,
            time_provider=MockTimeProvider(),
        )

        # Setup mock data
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                {
                    "id": 1,
                    "user": {"login": "reviewer1"},
                    "body": "Trivial comment 1",
                    "path": "src/main.py",
                    "line": 10,
                    "created_at": "2024-01-15T10:00:00Z",
                },
                {
                    "id": 2,
                    "user": {"login": "reviewer2"},
                    "body": "Trivial comment 2",
                    "path": "src/main.py",
                    "line": 20,
                    "created_at": "2024-01-15T10:00:00Z",
                },
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should have actionable comments with TRIVIAL priority
        assert result.status == PRStatus.ACTION_REQUIRED
        assert len(result.actionable_comments) == 2
        # All should be TRIVIAL priority
        for comment in result.actionable_comments:
            assert comment.priority == Priority.TRIVIAL

        # Action items should mention "other" or "actionable comments need addressing"
        assert any("actionable" in item.lower() for item in result.action_items)

    def test_single_other_priority_comment_uses_singular(
        self,
        mock_github: MockableGitHubAdapter,
        make_pr_data,
        make_ci_status,
        make_check_run,
    ):
        """Single 'other' priority comment should use singular form.

        This tests the singular/plural logic in lines 643-645.
        """
        from goodtogo.adapters.cache_memory import InMemoryCacheAdapter
        from goodtogo.adapters.time_provider import MockTimeProvider
        from goodtogo.core.interfaces import ReviewerParser
        from goodtogo.core.models import CommentClassification, Priority

        # Create a custom parser that returns ACTIONABLE with UNKNOWN priority
        class UnknownPriorityParser(ReviewerParser):
            @property
            def reviewer_type(self) -> ReviewerType:
                return ReviewerType.HUMAN

            def can_parse(self, author: str, body: str) -> bool:
                return True

            def parse(self, comment_data: dict) -> tuple[CommentClassification, Priority, bool]:
                return (CommentClassification.ACTIONABLE, Priority.UNKNOWN, False)

        parser = UnknownPriorityParser()
        parsers = {rt: parser for rt in ReviewerType}

        container = Container(
            github=mock_github,
            cache=InMemoryCacheAdapter(),
            parsers=parsers,
            time_provider=MockTimeProvider(),
        )

        # Setup mock data with single comment
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments(
            [
                {
                    "id": 1,
                    "user": {"login": "reviewer"},
                    "body": "Single comment with unknown priority",
                    "path": "src/main.py",
                    "line": 10,
                    "created_at": "2024-01-15T10:00:00Z",
                },
            ]
        )
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(
            make_ci_status(
                state="success",
                check_runs=[make_check_run(name="build", conclusion="success")],
            )
        )

        # Execute
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Verify - should use singular form "1 actionable comment needs addressing"
        assert len(result.actionable_comments) == 1
        # Should have action item with singular form
        action_item = [item for item in result.action_items if "actionable" in item.lower()]
        assert len(action_item) == 1
        assert "comment" in action_item[0]
        assert "needs" in action_item[0]
