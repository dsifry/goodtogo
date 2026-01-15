"""Tests for Cursor/Bugbot parser.

This module tests the CursorBugbotParser implementation, verifying:
- Author and body detection patterns (can_parse)
- Severity patterns (Critical, High, Medium, Low)
- Correct priority and requires_investigation values
"""

import pytest

from goodtogo.core.models import CommentClassification, Priority, ReviewerType
from goodtogo.parsers.cursor import CursorBugbotParser


class TestCursorBugbotParserCanParse:
    """Tests for CursorBugbotParser.can_parse() method."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_can_parse_by_author_cursor_bot(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test detection by cursor[bot] author."""
        assert parser.can_parse("cursor[bot]", "") is True

    def test_can_parse_by_author_cursor_dash_bot(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test detection by cursor-bot author."""
        assert parser.can_parse("cursor-bot", "") is True

    def test_can_parse_by_author_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test that author matching is case-insensitive."""
        assert parser.can_parse("CURSOR[BOT]", "") is True
        assert parser.can_parse("Cursor[bot]", "") is True
        assert parser.can_parse("CURSOR-BOT", "") is True

    def test_can_parse_by_body_cursor_link(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test detection by cursor.com link in body."""
        body = "Review powered by https://cursor.com"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test that body signature detection is case-insensitive."""
        assert parser.can_parse("other", "Check out CURSOR.COM") is True
        assert parser.can_parse("other", "Visit Cursor.Com for more") is True

    def test_can_parse_non_matching_author(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test that non-matching authors are rejected."""
        assert parser.can_parse("random-user", "") is False
        assert parser.can_parse("github-bot", "") is False
        assert parser.can_parse("coderabbitai[bot]", "") is False
        assert parser.can_parse("", "") is False

    def test_can_parse_non_matching_body(self, parser: CursorBugbotParser) -> None:
        """Test that non-matching bodies are rejected."""
        assert parser.can_parse("random-user", "Regular comment body") is False
        assert parser.can_parse("random-user", "Some other review tool") is False


class TestCursorBugbotParserReviewerType:
    """Tests for CursorBugbotParser.reviewer_type property."""

    def test_reviewer_type_returns_cursor(self) -> None:
        """Test that reviewer_type returns CURSOR."""
        parser = CursorBugbotParser()
        assert parser.reviewer_type == ReviewerType.CURSOR


class TestCursorBugbotParserCriticalSeverity:
    """Tests for Critical Severity classification."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_parse_critical_severity(self, parser: CursorBugbotParser) -> None:
        """Test Critical Severity detection."""
        body = "Critical Severity: This issue must be fixed immediately."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL
        assert requires_investigation is False

    def test_parse_critical_severity_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test Critical Severity is case-insensitive."""
        body = "CRITICAL SEVERITY: Security vulnerability detected."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL

    def test_parse_critical_severity_with_whitespace(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test Critical Severity with extra whitespace."""
        body = "Critical   Severity: Issue found."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL


class TestCursorBugbotParserHighSeverity:
    """Tests for High Severity classification."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_parse_high_severity(self, parser: CursorBugbotParser) -> None:
        """Test High Severity detection."""
        body = "High Severity: Must fix before merge."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR
        assert requires_investigation is False

    def test_parse_high_severity_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test High Severity is case-insensitive."""
        body = "HIGH SEVERITY: Data validation missing."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR


class TestCursorBugbotParserMediumSeverity:
    """Tests for Medium Severity classification."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_parse_medium_severity(self, parser: CursorBugbotParser) -> None:
        """Test Medium Severity detection."""
        body = "Medium Severity: Should fix this issue."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR
        assert requires_investigation is False

    def test_parse_medium_severity_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test Medium Severity is case-insensitive."""
        body = "MEDIUM SEVERITY: Consider refactoring."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR


class TestCursorBugbotParserLowSeverity:
    """Tests for Low Severity classification."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_parse_low_severity(self, parser: CursorBugbotParser) -> None:
        """Test Low Severity detection."""
        body = "Low Severity: Nice to fix but not required."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False

    def test_parse_low_severity_case_insensitive(
        self, parser: CursorBugbotParser
    ) -> None:
        """Test Low Severity is case-insensitive."""
        body = "LOW SEVERITY: Minor style improvement."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL


class TestCursorBugbotParserAmbiguous:
    """Tests for ambiguous comment handling."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_parse_empty_body(self, parser: CursorBugbotParser) -> None:
        """Test empty body results in AMBIGUOUS."""
        comment = {"body": ""}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_missing_body(self, parser: CursorBugbotParser) -> None:
        """Test missing body key results in AMBIGUOUS."""
        comment = {}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_unrecognized_pattern(self, parser: CursorBugbotParser) -> None:
        """Test unrecognized body pattern results in AMBIGUOUS."""
        comment = {"body": "Consider adding error handling here."}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_no_severity_indicator(self, parser: CursorBugbotParser) -> None:
        """Test body without severity indicator results in AMBIGUOUS."""
        comment = {"body": "This code could be improved."}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True


class TestCursorBugbotParserPrecedence:
    """Tests for severity pattern precedence rules."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_critical_over_high(self, parser: CursorBugbotParser) -> None:
        """Test Critical severity takes precedence over High."""
        body = "Critical Severity: Fix this.\nHigh Severity: Also this."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL

    def test_high_over_medium(self, parser: CursorBugbotParser) -> None:
        """Test High severity takes precedence over Medium."""
        body = "High Severity: Important fix.\nMedium Severity: Less important."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR

    def test_medium_over_low(self, parser: CursorBugbotParser) -> None:
        """Test Medium severity takes precedence over Low."""
        body = "Medium Severity: Should fix.\nLow Severity: Nice to fix."
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR

    def test_highest_severity_wins(self, parser: CursorBugbotParser) -> None:
        """Test the highest severity pattern wins when multiple are present."""
        body = """
        Low Severity: Minor formatting issue.
        Medium Severity: Should add validation.
        High Severity: Missing null check.
        Critical Severity: Security vulnerability.
        """
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        # Critical is checked first in _SEVERITY_PATTERNS
        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL


class TestCursorBugbotParserEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.fixture
    def parser(self) -> CursorBugbotParser:
        """Create a CursorBugbotParser instance."""
        return CursorBugbotParser()

    def test_severity_in_larger_body(self, parser: CursorBugbotParser) -> None:
        """Test severity pattern embedded in larger body."""
        body = """
        ## Bugbot Review

        I found an issue in your code.

        Medium Severity: The validation logic is incomplete.

        Please address this before merging.
        """
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR

    def test_severity_with_colon_in_message(self, parser: CursorBugbotParser) -> None:
        """Test severity detection when message also contains colons."""
        body = "Critical Severity: Error in file: config.py: line 42"
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL

    def test_partial_severity_not_matched(self, parser: CursorBugbotParser) -> None:
        """Test that partial severity text is not matched."""
        body = "The severity of this is unclear."
        comment = {"body": body}
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True

    def test_severity_without_space(self, parser: CursorBugbotParser) -> None:
        """Test severity patterns require whitespace between words."""
        # Pattern is r"Critical\s+Severity" - requires whitespace
        body = "CriticalSeverity: No space issue."
        comment = {"body": body}
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True
