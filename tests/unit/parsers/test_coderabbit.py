"""Tests for CodeRabbit parser.

This module tests the CodeRabbitParser implementation, verifying:
- Author and body detection patterns (can_parse)
- Classification of severity indicators (Critical, Major, Minor, Trivial, Nitpick)
- Fingerprinting comment detection
- Addressed marker detection
- Outside diff range detection
- Correct priority and requires_investigation values
"""

import pytest

from goodtogo.core.models import CommentClassification, Priority, ReviewerType
from goodtogo.parsers.coderabbit import CodeRabbitParser


class TestCodeRabbitParserCanParse:
    """Tests for CodeRabbitParser.can_parse() method."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_can_parse_by_author_exact_match(self, parser: CodeRabbitParser) -> None:
        """Test detection by exact author match."""
        assert parser.can_parse("coderabbitai[bot]", "") is True

    def test_can_parse_by_author_case_sensitive(self, parser: CodeRabbitParser) -> None:
        """Test that author matching is case-sensitive."""
        # The parser uses exact match, so these should not match
        assert parser.can_parse("CODERABBITAI[bot]", "") is False
        assert parser.can_parse("CodeRabbitAI[bot]", "") is False

    def test_can_parse_by_body_signature(self, parser: CodeRabbitParser) -> None:
        """Test detection by body signature pattern."""
        body = "<!-- This is an auto-generated comment by coderabbit.ai -->"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_by_body_signature_case_insensitive(self, parser: CodeRabbitParser) -> None:
        """Test that body signature detection is case-insensitive."""
        body = "<!-- This is an auto-generated comment by CodeRabbit.AI -->"
        assert parser.can_parse("other-user", body) is True

    def test_can_parse_non_matching_author(self, parser: CodeRabbitParser) -> None:
        """Test that non-matching authors are rejected."""
        assert parser.can_parse("random-user", "") is False
        assert parser.can_parse("github-bot", "") is False
        assert parser.can_parse("", "") is False

    def test_can_parse_non_matching_body(self, parser: CodeRabbitParser) -> None:
        """Test that non-matching bodies are rejected."""
        assert parser.can_parse("random-user", "Regular comment body") is False
        assert parser.can_parse("random-user", "Some other review tool") is False


class TestCodeRabbitParserReviewerType:
    """Tests for CodeRabbitParser.reviewer_type property."""

    def test_reviewer_type_returns_coderabbit(self) -> None:
        """Test that reviewer_type returns CODERABBIT."""
        parser = CodeRabbitParser()
        assert parser.reviewer_type == ReviewerType.CODERABBIT


class TestCodeRabbitParserCritical:
    """Tests for Critical severity classification."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_critical_severity(self, parser: CodeRabbitParser) -> None:
        """Test Critical severity detection with emoji pattern."""
        # Using the exact Unicode characters from the parser
        body = "_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_\n\nThis is critical."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL
        assert requires_investigation is False

    def test_parse_critical_severity_case_insensitive(self, parser: CodeRabbitParser) -> None:
        """Test Critical severity with different case."""
        body = "_\u26a0\ufe0f potential issue_ | _\U0001f534 critical_"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL
        assert requires_investigation is False


class TestCodeRabbitParserMajor:
    """Tests for Major severity classification."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_major_severity(self, parser: CodeRabbitParser) -> None:
        """Test Major severity detection with emoji pattern."""
        # Using the exact Unicode characters from the parser
        body = "_\u26a0\ufe0f Potential issue_ | _\U0001f7e0 Major_\n\nThis is a major issue."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR
        assert requires_investigation is False

    def test_parse_major_severity_case_insensitive(self, parser: CodeRabbitParser) -> None:
        """Test Major severity with different case."""
        body = "_\u26a0\ufe0f POTENTIAL ISSUE_ | _\U0001f7e0 MAJOR_"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR
        assert requires_investigation is False


class TestCodeRabbitParserMinor:
    """Tests for Minor severity classification."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_minor_severity(self, parser: CodeRabbitParser) -> None:
        """Test Minor severity detection with emoji pattern."""
        # Using the exact Unicode characters from the parser
        body = "_\u26a0\ufe0f Potential issue_ | _\U0001f7e1 Minor_\n\nThis is a minor issue."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR
        assert requires_investigation is False


class TestCodeRabbitParserTrivial:
    """Tests for Trivial severity classification."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_trivial_severity(self, parser: CodeRabbitParser) -> None:
        """Test Trivial severity detection."""
        body = "_\U0001f535 Trivial_\n\nThis is a trivial comment."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False


class TestCodeRabbitParserNitpick:
    """Tests for Nitpick classification."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_nitpick(self, parser: CodeRabbitParser) -> None:
        """Test Nitpick detection."""
        body = "_\U0001f9f9 Nitpick_\n\nThis is a nitpick comment."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.TRIVIAL
        assert requires_investigation is False


class TestCodeRabbitParserFingerprint:
    """Tests for fingerprinting comment detection."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_fingerprint_comment(self, parser: CodeRabbitParser) -> None:
        """Test fingerprinting comment detection."""
        body = "<!-- fingerprinting: some-metadata -->"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_fingerprint_takes_precedence_over_severity(self, parser: CodeRabbitParser) -> None:
        """Test that fingerprinting comments override severity patterns."""
        # A comment that has both fingerprint and critical should be NON_ACTIONABLE
        body = (
            "<!-- fingerprinting: metadata -->"
            "_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_"
        )
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN


class TestCodeRabbitParserAddressed:
    """Tests for Addressed marker detection."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_addressed_marker(self, parser: CodeRabbitParser) -> None:
        """Test Addressed marker detection."""
        body = "\u2705 Addressed\n\nThe issue has been resolved."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert priority == Priority.UNKNOWN
        assert requires_investigation is False

    def test_addressed_takes_precedence_over_severity(self, parser: CodeRabbitParser) -> None:
        """Test that Addressed marker overrides severity patterns."""
        body = "\u2705 Addressed\n_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE


class TestCodeRabbitParserOutsideDiffRange:
    """Tests for Outside diff range detection."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_outside_diff_range(self, parser: CodeRabbitParser) -> None:
        """Test Outside diff range detection."""
        body = "Outside diff range: This comment refers to code not in this PR."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR
        assert requires_investigation is False

    def test_outside_diff_range_case_insensitive(self, parser: CodeRabbitParser) -> None:
        """Test Outside diff range with different case."""
        body = "OUTSIDE DIFF RANGE: some comment"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR


class TestCodeRabbitParserAmbiguous:
    """Tests for ambiguous comment handling."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_empty_body(self, parser: CodeRabbitParser) -> None:
        """Test empty body results in AMBIGUOUS."""
        comment = {"body": ""}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_missing_body(self, parser: CodeRabbitParser) -> None:
        """Test missing body key results in AMBIGUOUS."""
        comment = {}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True

    def test_parse_unrecognized_pattern(self, parser: CodeRabbitParser) -> None:
        """Test unrecognized body pattern results in AMBIGUOUS."""
        comment = {"body": "This is a regular comment without any markers."}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.AMBIGUOUS
        assert priority == Priority.UNKNOWN
        assert requires_investigation is True


class TestCodeRabbitParserPrecedence:
    """Tests for pattern precedence rules."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_critical_over_major(self, parser: CodeRabbitParser) -> None:
        """Test Critical severity takes precedence over Major."""
        body = (
            "_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_\n"
            "_\u26a0\ufe0f Potential issue_ | _\U0001f7e0 Major_"
        )
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL

    def test_major_over_minor(self, parser: CodeRabbitParser) -> None:
        """Test Major severity takes precedence over Minor when first."""
        body = (
            "_\u26a0\ufe0f Potential issue_ | _\U0001f7e0 Major_\n"
            "_\u26a0\ufe0f Potential issue_ | _\U0001f7e1 Minor_"
        )
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MAJOR

    def test_severity_over_trivial(self, parser: CodeRabbitParser) -> None:
        """Test severity patterns take precedence over trivial."""
        body = "_\u26a0\ufe0f Potential issue_ | _\U0001f7e1 Minor_\n" "_\U0001f535 Trivial_"
        comment = {"body": body}
        classification, priority, _ = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.MINOR


class TestCodeRabbitParserSummaryPatterns:
    """Tests for summary/walkthrough and tip content detection."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_walkthrough_header_is_non_actionable(self, parser: CodeRabbitParser) -> None:
        """Test ## Walkthrough header is classified as NON_ACTIONABLE."""
        body = "## Walkthrough\n\nThis PR adds a feature."
        comment = {"body": body}
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_tip_callout_is_non_actionable(self, parser: CodeRabbitParser) -> None:
        """Test > [!TIP] is classified as NON_ACTIONABLE."""
        body = "> [!TIP]\n> Use this method."
        comment = {"body": body}
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_mermaid_is_non_actionable(self, parser: CodeRabbitParser) -> None:
        """Test mermaid diagrams are NON_ACTIONABLE."""
        body = "```mermaid\ndiagram\n```"
        comment = {"body": body}
        classification, _, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_is_summary_content_no_match(self, parser: CodeRabbitParser) -> None:
        """Test _is_summary_content returns False for non-matching text."""
        assert parser._is_summary_content("Regular text") is False

    def test_is_tip_content_no_match(self, parser: CodeRabbitParser) -> None:
        """Test _is_tip_content returns False for non-matching text."""
        assert parser._is_tip_content("> Quote") is False
