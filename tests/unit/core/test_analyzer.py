"""Tests for PRAnalyzer with classification persistence.

This module tests the integration of AgentState's dismissal persistence
with the PRAnalyzer's comment classification flow, and thread resolution
mapping behavior.
"""

import os
import tempfile

import pytest

from goodtogo.adapters.agent_state import AgentState
from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import CommentClassification, Priority, PRStatus


class TestAnalyzerDismissalIntegration:
    """Tests for analyzer integration with comment dismissal persistence."""

    @pytest.fixture
    def test_container(self, mock_github, make_pr_data, make_ci_status):
        """Create a test container with mock GitHub adapter."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        return Container.create_for_testing(github=mock_github)

    @pytest.fixture
    def agent_state(self):
        """Create a temporary AgentState for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)
            yield state
            state.close()

    def test_classify_comment_returns_non_actionable_for_dismissed(
        self, test_container, agent_state, make_comment
    ):
        """Test that dismissed comments return NON_ACTIONABLE classification."""
        pr_key = "owner/repo:123"
        # Note: comment_id is stored as string in analyzer, so use "1" to match
        comment_id = "1"

        # Pre-dismiss the comment
        agent_state.dismiss_comment(pr_key, comment_id, reason="Not actionable")

        # Create analyzer with agent state
        analyzer = PRAnalyzer(test_container, agent_state=agent_state, pr_key=pr_key)

        # Create a comment that would normally be ACTIONABLE
        # The comment_id=1 (int) becomes "1" (str) in the analyzer
        comment_data = make_comment(
            comment_id=1,
            author="coderabbitai[bot]",
            body="""_⚠️ Potential issue_ | _🔴 Critical_

Missing null check in handler function.
""",
        )

        # Classify the comment
        result = analyzer._classify_comment(comment_data, {}, {})

        # Should return NON_ACTIONABLE because it was dismissed
        assert result.classification == CommentClassification.NON_ACTIONABLE
        assert result.requires_investigation is False

    def test_classify_comment_runs_parser_for_non_dismissed(
        self, test_container, agent_state, make_comment
    ):
        """Test that non-dismissed comments are processed normally by parser."""
        pr_key = "owner/repo:123"

        # Create analyzer with agent state
        analyzer = PRAnalyzer(test_container, agent_state=agent_state, pr_key=pr_key)

        # Create a comment that would be ACTIONABLE
        comment_data = make_comment(
            comment_id=1,
            author="coderabbitai[bot]",
            body="""_⚠️ Potential issue_ | _🔴 Critical_

Missing null check in handler function.
""",
        )

        # Classify the comment (comment_1 is not dismissed)
        result = analyzer._classify_comment(comment_data, {}, {})

        # Should be processed normally and classified as ACTIONABLE
        assert result.classification == CommentClassification.ACTIONABLE

    def test_dismiss_comment_method_persists_dismissal(
        self, test_container, agent_state, make_comment
    ):
        """Test that analyzer's dismiss_comment method persists the dismissal."""
        pr_key = "owner/repo:123"
        comment_id = "comment_1"

        # Create analyzer with agent state
        analyzer = PRAnalyzer(test_container, agent_state=agent_state, pr_key=pr_key)

        # Dismiss a comment via the analyzer
        analyzer.dismiss_comment(comment_id, reason="Informational only")

        # Verify the dismissal is persisted
        assert agent_state.is_comment_dismissed(pr_key, comment_id)
        dismissed = agent_state.get_dismissed_comments(pr_key)
        assert comment_id in dismissed

    def test_analyzer_without_agent_state_works_normally(self, test_container, make_comment):
        """Test that analyzer works without AgentState (backward compatible)."""
        # Create analyzer WITHOUT agent state
        analyzer = PRAnalyzer(test_container)

        # Create a comment that would be ACTIONABLE
        comment_data = make_comment(
            comment_id=1,
            author="coderabbitai[bot]",
            body="""_⚠️ Potential issue_ | _🔴 Critical_

Missing null check in handler function.
""",
        )

        # Classify the comment - should work normally
        result = analyzer._classify_comment(comment_data, {}, {})

        # Should be processed normally and classified as ACTIONABLE
        assert result.classification == CommentClassification.ACTIONABLE

    def test_dismissed_comment_has_priority_unknown(
        self, test_container, agent_state, make_comment
    ):
        """Test that dismissed comments have UNKNOWN priority."""
        pr_key = "owner/repo:123"
        comment_id = "comment_1"

        # Pre-dismiss the comment
        agent_state.dismiss_comment(pr_key, comment_id)

        # Create analyzer with agent state
        analyzer = PRAnalyzer(test_container, agent_state=agent_state, pr_key=pr_key)

        # Create a comment
        comment_data = make_comment(comment_id=1, author="reviewer", body="Fix this!")

        # Classify the comment
        result = analyzer._classify_comment(comment_data, {}, {})

        # Dismissed comments should have UNKNOWN priority (not evaluated)
        assert result.priority == Priority.UNKNOWN

    def test_dismiss_comment_requires_pr_key(self, test_container, agent_state):
        """Test that dismiss_comment requires pr_key to be set."""
        # Create analyzer with agent state but no pr_key
        analyzer = PRAnalyzer(test_container, agent_state=agent_state)

        # Should raise an error when trying to dismiss without pr_key
        with pytest.raises(ValueError, match="pr_key"):
            analyzer.dismiss_comment("comment_1")

    def test_dismiss_comment_requires_agent_state(self, test_container):
        """Test that dismiss_comment requires agent_state to be configured."""
        # Create analyzer with pr_key but no agent_state
        analyzer = PRAnalyzer(test_container, pr_key="owner/repo:123")

        # Should raise an error when trying to dismiss without agent_state
        with pytest.raises(RuntimeError, match="agent_state"):
            analyzer.dismiss_comment("comment_1")


class TestAnalyzerDismissalInFullAnalysis:
    """Tests for dismissal persistence in full PR analysis flow."""

    def test_dismissed_comments_excluded_from_actionable(
        self, mock_github, make_pr_data, make_ci_status, make_comment
    ):
        """Test that dismissed comments don't appear in actionable_comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            agent_state = AgentState(db_path)

            pr_key = "owner/repo:123"

            # Pre-dismiss comment with id "1"
            agent_state.dismiss_comment(pr_key, "1", reason="Not actionable")

            # Setup mock GitHub with an actionable comment
            mock_github.set_pr_data(make_pr_data(number=123))
            mock_github.set_comments(
                [
                    make_comment(
                        comment_id=1,
                        author="coderabbitai[bot]",
                        body="""_⚠️ Potential issue_ | _🔴 Critical_

Missing null check.
""",
                    ),
                    make_comment(
                        comment_id=2,
                        author="coderabbitai[bot]",
                        body="""_⚠️ Potential issue_ | _🟡 Minor_

Consider adding a comment.
""",
                    ),
                ]
            )
            mock_github.set_reviews([])
            mock_github.set_threads([])
            mock_github.set_ci_status(make_ci_status(state="success"))

            container = Container.create_for_testing(github=mock_github)
            analyzer = PRAnalyzer(container, agent_state=agent_state, pr_key=pr_key)

            # Run full analysis
            result = analyzer.analyze("owner", "repo", 123)

            # Comment 1 should be NON_ACTIONABLE (dismissed)
            # Comment 2 should be ACTIONABLE
            dismissed_comment = next((c for c in result.comments if c.id == "1"), None)
            active_comment = next((c for c in result.comments if c.id == "2"), None)

            assert dismissed_comment is not None
            assert dismissed_comment.classification == CommentClassification.NON_ACTIONABLE

            assert active_comment is not None
            assert active_comment.classification == CommentClassification.ACTIONABLE

            # Only comment 2 should be in actionable_comments
            assert len(result.actionable_comments) == 1
            assert result.actionable_comments[0].id == "2"

            agent_state.close()


class TestAnalyzerOutsideDiffComments:
    """Tests for parsing 'Outside diff range' comments from review bodies."""

    def test_outside_diff_comments_extracted_from_coderabbit_reviews(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """Test that outside diff comments are extracted from CodeRabbit review bodies."""
        # Setup mock GitHub with a CodeRabbit review containing outside diff comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=456,
                    author="coderabbitai[bot]",
                    body="""## Summary

This PR looks good overall.

<details>
<summary>\u26a0\ufe0f Outside diff range comments (2)</summary>

**src/config.py:42-45**: Consider adding validation for the config values.

**src/utils.py:100**: This function could use memoization for performance.

</details>
""",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        # Run full analysis
        result = analyzer.analyze("owner", "repo", 123)

        # Verify outside diff comments were extracted
        assert len(result.outside_diff_comments) == 2

        assert result.outside_diff_comments[0].file_path == "src/config.py"
        assert result.outside_diff_comments[0].line_range == "42-45"
        assert "validation" in result.outside_diff_comments[0].body
        assert result.outside_diff_comments[0].source == "coderabbitai[bot]"

        assert result.outside_diff_comments[1].file_path == "src/utils.py"
        assert result.outside_diff_comments[1].line_range == "100"
        assert "memoization" in result.outside_diff_comments[1].body

    def test_outside_diff_comments_empty_when_no_coderabbit_reviews(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """Test that outside_diff_comments is empty when no CodeRabbit reviews exist."""
        # Setup mock GitHub with a non-CodeRabbit review
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=456,
                    author="regular-user",
                    body="LGTM!",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        # Run full analysis
        result = analyzer.analyze("owner", "repo", 123)

        # Verify outside_diff_comments is empty
        assert len(result.outside_diff_comments) == 0

    def test_outside_diff_comments_empty_when_review_has_no_section(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """Test that outside_diff_comments is empty when review has no outside diff section."""
        # Setup mock GitHub with a CodeRabbit review without outside diff comments
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=456,
                    author="coderabbitai[bot]",
                    body="## Summary\n\nThis PR looks good!",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        # Run full analysis
        result = analyzer.analyze("owner", "repo", 123)

        # Verify outside_diff_comments is empty
        assert len(result.outside_diff_comments) == 0

    def test_outside_diff_comments_from_multiple_reviews(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """Test that outside diff comments are collected from multiple reviews."""
        # Setup mock GitHub with multiple CodeRabbit reviews
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=456,
                    author="coderabbitai[bot]",
                    body="""
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/config.py:10**: First comment.

</details>
""",
                ),
                make_review(
                    review_id=789,
                    author="coderabbitai[bot]",
                    body="""
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/utils.py:20**: Second comment.

</details>
""",
                ),
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        # Run full analysis
        result = analyzer.analyze("owner", "repo", 123)

        # Verify outside diff comments from both reviews were collected
        assert len(result.outside_diff_comments) == 2
        file_paths = {c.file_path for c in result.outside_diff_comments}
        assert file_paths == {"src/config.py", "src/utils.py"}


class TestThreadResolutionMapping:
    """Tests for thread resolution status affecting comment classification.

    When a comment belongs to a resolved thread on GitHub, the comment should
    be classified as NON_ACTIONABLE regardless of severity markers in the text.
    This mapping uses the comment's database ID to match against thread comments.
    """

    def test_resolved_thread_comment_classified_as_non_actionable(
        self, mock_github, make_pr_data, make_ci_status, make_comment, make_thread
    ):
        """Test that a comment in a resolved thread is classified as NON_ACTIONABLE.

        This tests the mapping between REST API comments (with database IDs) and
        GraphQL thread resolution status.
        """
        # Comment with High Severity marker that would normally be ACTIONABLE
        comment = make_comment(
            comment_id=12345,  # Database ID from REST API
            author="cursor[bot]",
            body="High Severity: This is a critical issue!",
            path="src/main.py",
            line=10,
        )

        # Thread containing this comment, marked as resolved
        # The thread comment's database_id matches the comment's id
        thread = make_thread(
            thread_id="PRRT_kwDOTest123",
            is_resolved=True,
            path="src/main.py",
            line=10,
            comments=[
                {
                    "id": "PRRC_kwDOComment123",
                    "database_id": 12345,  # Matches comment_id above
                    "body": "High Severity: This is a critical issue!",
                    "author": "cursor[bot]",
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        )

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([comment])
        mock_github.set_reviews([])
        mock_github.set_threads([thread])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # The comment should be classified as NON_ACTIONABLE because
        # its thread is resolved, even though it has "High Severity" marker
        assert len(result.actionable_comments) == 0
        assert result.status == PRStatus.READY

    def test_unresolved_thread_comment_respects_severity(
        self, mock_github, make_pr_data, make_ci_status, make_comment, make_thread
    ):
        """Test that a comment in an unresolved thread respects severity markers."""
        comment = make_comment(
            comment_id=12345,
            author="cursor[bot]",
            body="High Severity: This is a critical issue!",
            path="src/main.py",
            line=10,
        )

        thread = make_thread(
            thread_id="PRRT_kwDOTest123",
            is_resolved=False,  # NOT resolved
            path="src/main.py",
            line=10,
            comments=[
                {
                    "id": "PRRC_kwDOComment123",
                    "database_id": 12345,
                    "body": "High Severity: This is a critical issue!",
                    "author": "cursor[bot]",
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        )

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([comment])
        mock_github.set_reviews([])
        mock_github.set_threads([thread])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # The comment should be ACTIONABLE since thread is not resolved
        assert len(result.actionable_comments) == 1
        assert result.actionable_comments[0].id == "12345"

    def test_outdated_thread_comment_classified_as_non_actionable(
        self, mock_github, make_pr_data, make_ci_status, make_comment, make_thread
    ):
        """Test that a comment in an outdated thread is classified as NON_ACTIONABLE."""
        comment = make_comment(
            comment_id=12345,
            author="cursor[bot]",
            body="Medium Severity: Should fix this.",
            path="src/main.py",
            line=10,
        )

        thread = make_thread(
            thread_id="PRRT_kwDOTest123",
            is_resolved=False,
            is_outdated=True,  # Outdated (code changed)
            path="src/main.py",
            line=10,
            comments=[
                {
                    "id": "PRRC_kwDOComment123",
                    "database_id": 12345,
                    "body": "Medium Severity: Should fix this.",
                    "author": "cursor[bot]",
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        )

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([comment])
        mock_github.set_reviews([])
        mock_github.set_threads([thread])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # The comment should be NON_ACTIONABLE since thread is outdated
        assert len(result.actionable_comments) == 0

    def test_multiple_comments_in_mixed_threads(
        self, mock_github, make_pr_data, make_ci_status, make_comment, make_thread
    ):
        """Test handling of multiple comments with some in resolved threads."""
        # Two comments - one in resolved thread, one in unresolved
        resolved_comment = make_comment(
            comment_id=111,
            author="cursor[bot]",
            body="High Severity: Resolved issue.",
            path="src/resolved.py",
            line=10,
        )
        unresolved_comment = make_comment(
            comment_id=222,
            author="cursor[bot]",
            body="High Severity: Unresolved issue.",
            path="src/unresolved.py",
            line=20,
        )

        resolved_thread = make_thread(
            thread_id="PRRT_resolved",
            is_resolved=True,
            path="src/resolved.py",
            line=10,
            comments=[
                {
                    "id": "PRRC_111",
                    "database_id": 111,
                    "body": "High Severity: Resolved issue.",
                    "author": "cursor[bot]",
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        )
        unresolved_thread = make_thread(
            thread_id="PRRT_unresolved",
            is_resolved=False,
            path="src/unresolved.py",
            line=20,
            comments=[
                {
                    "id": "PRRC_222",
                    "database_id": 222,
                    "body": "High Severity: Unresolved issue.",
                    "author": "cursor[bot]",
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        )

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([resolved_comment, unresolved_comment])
        mock_github.set_reviews([])
        mock_github.set_threads([resolved_thread, unresolved_thread])
        mock_github.set_ci_status(make_ci_status(state="success"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)

        result = analyzer.analyze("owner", "repo", 123)

        # Only the unresolved comment should be actionable
        assert len(result.actionable_comments) == 1
        assert result.actionable_comments[0].id == "222"
