"""Tests for Vercel parser.

This module tests the VercelParser implementation, verifying:
- Author and body detection patterns (can_parse)
- All comments classified as NON_ACTIONABLE
- Deployment success/failure/pending messages all non-actionable
"""

import pytest

from goodtogo.core.models import CommentClassification, Priority, ReviewerType
from goodtogo.parsers.vercel import VercelParser


class TestVercelParserCanParse:
    """Tests for VercelParser.can_parse() method."""

    @pytest.fixture
    def parser(self) -> VercelParser:
        """Create a VercelParser instance."""
        return VercelParser()

    def test_can_parse_by_author_exact_match(self, parser: VercelParser) -> None:
        """Test detection by exact author match."""
        assert parser.can_parse("vercel[bot]", "") is True

    def test_can_parse_by_author_case_insensitive(self, parser: VercelParser) -> None:
        """Test that author matching is case-insensitive."""
        assert parser.can_parse("Vercel[bot]", "") is True
        assert parser.can_parse("VERCEL[BOT]", "") is True

    def test_can_parse_by_body_vc_marker(self, parser: VercelParser) -> None:
        """Test detection by [vc]: marker in body."""
        body = "[vc]: # (deployment-status)"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_vercel_com(self, parser: VercelParser) -> None:
        """Test detection by vercel.com link in body."""
        body = "Visit https://vercel.com/dashboard for details"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_vercel_app_url(self, parser: VercelParser) -> None:
        """Test detection by .vercel.app deployment URL."""
        body = "Preview: https://my-app-abc123.vercel.app"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_preview_bold(self, parser: VercelParser) -> None:
        """Test detection by **Preview** marker in deployment table."""
        body = "| **Preview** | https://my-app.vercel.app |"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_case_insensitive(self, parser: VercelParser) -> None:
        """Test that body signature detection is case-insensitive."""
        assert parser.can_parse("other", "Check VERCEL.COM") is True
        assert parser.can_parse("other", "[VC]: # marker") is True

    def test_can_parse_non_matching_author(self, parser: VercelParser) -> None:
        """Test that non-matching authors are rejected."""
        assert parser.can_parse("random-user", "") is False
        assert parser.can_parse("github-bot", "") is False
        assert parser.can_parse("", "") is False

    def test_can_parse_non_matching_body(self, parser: VercelParser) -> None:
        """Test that non-matching bodies are rejected."""
        assert parser.can_parse("random-user", "Regular comment body") is False
        assert parser.can_parse("random-user", "Some other deployment tool") is False


class TestVercelParserReviewerType:
    """Tests for VercelParser.reviewer_type property."""

    def test_reviewer_type_returns_vercel(self) -> None:
        """Test that reviewer_type returns VERCEL."""
        parser = VercelParser()
        assert parser.reviewer_type == ReviewerType.VERCEL


class TestVercelParserClassification:
    """Tests for Vercel comment classification.

    All Vercel comments should be NON_ACTIONABLE since they are
    deployment status notifications, not code review feedback.
    """

    @pytest.fixture
    def parser(self) -> VercelParser:
        """Create a VercelParser instance."""
        return VercelParser()

    def test_deployment_success_is_non_actionable(self, parser: VercelParser) -> None:
        """Test deployment success comment is NON_ACTIONABLE."""
        body = (
            "The latest updates on your projects. "
            "Learn more about Vercel for Git.\n\n"
            "| Name | Status | Preview |\n"
            "| :--- | :----- | :------ |\n"
            "| **my-app** | Ready ([Inspect](https://vercel.com/...)) "
            "| [Visit Preview](https://my-app-abc123.vercel.app) |"
        )
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_deployment_failure_is_non_actionable(self, parser: VercelParser) -> None:
        """Test deployment failure comment is NON_ACTIONABLE."""
        body = (
            "The latest updates on your projects.\n\n"
            "| Name | Status | Preview |\n"
            "| :--- | :----- | :------ |\n"
            "| **my-app** | Failed ([Inspect](https://vercel.com/...)) | |"
        )
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_deployment_pending_is_non_actionable(self, parser: VercelParser) -> None:
        """Test deployment pending/building comment is NON_ACTIONABLE."""
        body = (
            "The latest updates on your projects.\n\n"
            "| Name | Status | Preview |\n"
            "| :--- | :----- | :------ |\n"
            "| **my-app** | Building ([Inspect](https://vercel.com/...)) | |"
        )
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_deployment_cancelled_is_non_actionable(self, parser: VercelParser) -> None:
        """Test deployment cancelled comment is NON_ACTIONABLE."""
        body = "[vc]: # (deployment-cancelled)\n" "This deployment was cancelled."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_empty_body_is_non_actionable(self, parser: VercelParser) -> None:
        """Test empty body is still NON_ACTIONABLE for Vercel."""
        comment = {"body": ""}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_missing_body_is_non_actionable(self, parser: VercelParser) -> None:
        """Test missing body key is still NON_ACTIONABLE for Vercel."""
        comment = {}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_arbitrary_text_is_non_actionable(self, parser: VercelParser) -> None:
        """Test any arbitrary text from Vercel is NON_ACTIONABLE."""
        comment = {"body": "Some unexpected Vercel message format."}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False


class TestVercelParserThreadResolution:
    """Tests for thread resolution handling (base class template method)."""

    @pytest.fixture
    def parser(self) -> VercelParser:
        """Create a VercelParser instance."""
        return VercelParser()

    def test_resolved_thread_is_non_actionable(self, parser: VercelParser) -> None:
        """Test that resolved threads return NON_ACTIONABLE."""
        comment = {
            "body": "Deployment ready: https://my-app.vercel.app",
            "is_resolved": True,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_outdated_thread_is_non_actionable(self, parser: VercelParser) -> None:
        """Test that outdated threads return NON_ACTIONABLE."""
        comment = {
            "body": "Deployment ready: https://my-app.vercel.app",
            "is_outdated": True,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_unresolved_thread_is_non_actionable(self, parser: VercelParser) -> None:
        """Test that even unresolved Vercel threads are NON_ACTIONABLE."""
        comment = {
            "body": "Deployment ready: https://my-app.vercel.app",
            "is_resolved": False,
            "is_outdated": False,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False
