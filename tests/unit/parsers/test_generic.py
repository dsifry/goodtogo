"""Tests for Generic/Fallback parser.

This module tests the GenericParser implementation, verifying:
- Always-true can_parse behavior (fallback parser)
- Resolved thread detection
- Outdated thread detection
- Default AMBIGUOUS behavior with requires_investigation=True
"""

import pytest

from goodtogo.core.models import CommentClassification, Priority, ReviewerType
from goodtogo.parsers.generic import GenericParser


class TestGenericParserCanParse:
    """Tests for GenericParser.can_parse() method."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_can_parse_always_returns_true(self, parser: GenericParser) -> None:
        """Test that can_parse always returns True."""
        assert parser.can_parse("any-user", "") is True
        assert parser.can_parse("", "") is True
        assert parser.can_parse("random-bot", "any body") is True

    def test_can_parse_any_author(self, parser: GenericParser) -> None:
        """Test can_parse accepts any author."""
        assert parser.can_parse("user123", "") is True
        assert parser.can_parse("github-bot", "") is True
        assert parser.can_parse("coderabbitai[bot]", "") is True
        assert parser.can_parse("greptile[bot]", "") is True

    def test_can_parse_any_body(self, parser: GenericParser) -> None:
        """Test can_parse accepts any body content."""
        assert parser.can_parse("user", "Regular comment") is True
        assert parser.can_parse("user", "<!-- HTML comment -->") is True
        assert parser.can_parse("user", "LGTM!") is True
        assert parser.can_parse("user", "") is True

    def test_can_parse_is_fallback(self, parser: GenericParser) -> None:
        """Test that parser is intended as fallback for unrecognized comments."""
        # This is the defining characteristic of the generic parser
        # It should accept anything because it's the last resort
        assert parser.can_parse("unknown-reviewer[bot]", "Unknown format") is True


class TestGenericParserReviewerType:
    """Tests for GenericParser.reviewer_type property."""

    def test_reviewer_type_returns_human(self) -> None:
        """Test that reviewer_type returns HUMAN."""
        parser = GenericParser()
        assert parser.reviewer_type == ReviewerType.HUMAN


class TestGenericParserResolved:
    """Tests for resolved thread detection."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_parse_resolved_thread(self, parser: GenericParser) -> None:
        """Test resolved thread results in NON_ACTIONABLE."""
        comment = {"body": "This is a comment.", "is_resolved": True}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_parse_resolved_with_body(self, parser: GenericParser) -> None:
        """Test resolved thread with body content."""
        comment = {
            "body": "Please fix this issue!",
            "is_resolved": True,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_parse_not_resolved(self, parser: GenericParser) -> None:
        """Test is_resolved=False doesn't trigger NON_ACTIONABLE."""
        comment = {"body": "Please fix this.", "is_resolved": False}
        classification, _, requires_investigation = parser.parse(comment)

        # Not resolved, not outdated -> AMBIGUOUS
        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True


class TestGenericParserOutdated:
    """Tests for outdated thread detection."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_parse_outdated_thread(self, parser: GenericParser) -> None:
        """Test outdated thread results in NON_ACTIONABLE."""
        comment = {"body": "This is a comment.", "is_outdated": True}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_parse_outdated_with_body(self, parser: GenericParser) -> None:
        """Test outdated thread with body content."""
        comment = {
            "body": "The function signature is wrong.",
            "is_outdated": True,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_parse_not_outdated(self, parser: GenericParser) -> None:
        """Test is_outdated=False doesn't trigger NON_ACTIONABLE."""
        comment = {"body": "Please fix this.", "is_outdated": False}
        classification, _, requires_investigation = parser.parse(comment)

        # Not resolved, not outdated -> AMBIGUOUS
        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True


class TestGenericParserAmbiguous:
    """Tests for default AMBIGUOUS behavior."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_parse_default_ambiguous(self, parser: GenericParser) -> None:
        """Test default case results in AMBIGUOUS."""
        comment = {"body": "This is a regular comment."}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_empty_body_ambiguous(self, parser: GenericParser) -> None:
        """Test empty body results in AMBIGUOUS."""
        comment = {"body": ""}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_missing_body_ambiguous(self, parser: GenericParser) -> None:
        """Test missing body key results in AMBIGUOUS."""
        comment = {}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_empty_comment_dict(self, parser: GenericParser) -> None:
        """Test empty comment dictionary results in AMBIGUOUS."""
        comment: dict = {}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_ambiguous_always_requires_investigation(self, parser: GenericParser) -> None:
        """Test that AMBIGUOUS classification always has requires_investigation=True."""
        # Test multiple scenarios that should result in AMBIGUOUS
        test_cases = [
            {"body": "Random comment"},
            {"body": "Please fix this!", "is_resolved": False, "is_outdated": False},
            {"body": "LGTM"},  # Generic parser doesn't understand LGTM
            {"body": "Consider refactoring"},  # Generic parser doesn't understand this
        ]

        for comment in test_cases:
            classification, _, requires_investigation = parser.parse(comment)
            if classification == CommentClassification.AMBIGUOUS:
                assert requires_investigation is True, (
                    f"AMBIGUOUS comment should have requires_investigation=True: " f"{comment}"
                )


class TestGenericParserPrecedence:
    """Tests for precedence rules."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_resolved_takes_precedence_over_outdated(self, parser: GenericParser) -> None:
        """Test resolved check comes before outdated check."""
        # Both resolved and outdated = NON_ACTIONABLE (resolved checked first)
        comment = {
            "body": "Comment content",
            "is_resolved": True,
            "is_outdated": True,
        }
        classification, _, _ = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE

    def test_outdated_when_not_resolved(self, parser: GenericParser) -> None:
        """Test outdated is checked when not resolved."""
        comment = {
            "body": "Comment content",
            "is_resolved": False,
            "is_outdated": True,
        }
        classification, _, _ = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE


class TestGenericParserEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.fixture
    def parser(self) -> GenericParser:
        """Create a GenericParser instance."""
        return GenericParser()

    def test_parse_with_extra_fields(self, parser: GenericParser) -> None:
        """Test parsing with extra fields in comment dict."""
        comment = {
            "body": "A comment",
            "is_resolved": False,
            "is_outdated": False,
            "author": "test-user",
            "extra_field": "ignored",
            "another_field": 123,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_resolved_with_false_like_values(self, parser: GenericParser) -> None:
        """Test that only explicit False is not-resolved, falsy values vary."""
        # None is treated as False by .get() default
        comment = {"body": "Comment", "is_resolved": None}
        classification, _, _ = parser.parse(comment)

        # None evaluates to False in boolean context
        assert classification == CommentClassification.AMBIGUOUS

    def test_parse_human_review_comment(self, parser: GenericParser) -> None:
        """Test typical human review comment is AMBIGUOUS."""
        comment = {
            "body": "Can you add a test for this edge case?",
            "is_resolved": False,
            "is_outdated": False,
        }
        classification, priority, requires_investigation = parser.parse(comment)

        # Human comments should require investigation
        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_human_approval_still_ambiguous(self, parser: GenericParser) -> None:
        """Test that human approval comments are still AMBIGUOUS."""
        # GenericParser doesn't understand approval patterns
        comment = {"body": "LGTM! Ship it."}
        classification, _, requires_investigation = parser.parse(comment)

        # Generic parser treats all unresolved/not-outdated as AMBIGUOUS
        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True

    def test_resolved_overrides_body_content(self, parser: GenericParser) -> None:
        """Test that resolved status overrides body content analysis."""
        # Even if body suggests action needed, resolved means NON_ACTIONABLE
        comment = {
            "body": "CRITICAL BUG: Fix immediately!",
            "is_resolved": True,
        }
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False
