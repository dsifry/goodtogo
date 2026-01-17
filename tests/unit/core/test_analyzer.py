"""Tests for PRAnalyzer with classification persistence.

This module tests the integration of AgentState's dismissal persistence
with the PRAnalyzer's comment classification flow.
"""

import os
import tempfile

import pytest

from goodtogo.adapters.agent_state import AgentState
from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import CommentClassification, Priority


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

    def test_analyzer_without_agent_state_works_normally(
        self, test_container, make_comment
    ):
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
            mock_github.set_comments([
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
            ])
            mock_github.set_reviews([])
            mock_github.set_threads([])
            mock_github.set_ci_status(make_ci_status(state="success"))

            container = Container.create_for_testing(github=mock_github)
            analyzer = PRAnalyzer(container, agent_state=agent_state, pr_key=pr_key)

            # Run full analysis
            result = analyzer.analyze("owner", "repo", 123)

            # Comment 1 should be NON_ACTIONABLE (dismissed)
            # Comment 2 should be ACTIONABLE
            dismissed_comment = next(
                (c for c in result.comments if c.id == "1"), None
            )
            active_comment = next(
                (c for c in result.comments if c.id == "2"), None
            )

            assert dismissed_comment is not None
            assert dismissed_comment.classification == CommentClassification.NON_ACTIONABLE

            assert active_comment is not None
            assert active_comment.classification == CommentClassification.ACTIONABLE

            # Only comment 2 should be in actionable_comments
            assert len(result.actionable_comments) == 1
            assert result.actionable_comments[0].id == "2"

            agent_state.close()
