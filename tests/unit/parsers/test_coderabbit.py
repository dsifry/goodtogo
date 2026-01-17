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

from goodtogo.core.models import CommentClassification, OutsideDiffComment, Priority, ReviewerType
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

    def test_inline_comment_with_walkthrough_is_non_actionable(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test inline comment with walkthrough content is NON_ACTIONABLE.

        Even inline comments (with path set) that contain walkthrough/summary
        content should be NON_ACTIONABLE - this tests the body-level check.
        """
        body = "## Walkthrough\n\nThis summarizes the changes."
        comment = {"body": body, "path": "src/file.py", "line": 42}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False


class TestCodeRabbitParserPRLevelSummaryComments:
    """Tests for PR-level summary comment detection.

    PR-level summary comments are posted by CodeRabbit at the PR level (not inline)
    and contain overview information. These should be classified as NON_ACTIONABLE
    because the actual actionable items are in inline comments.
    """

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_pr_summary_with_actionable_comments_count(self, parser: CodeRabbitParser) -> None:
        """Test PR-level summary with 'Actionable comments posted: N' is NON_ACTIONABLE.

        This is the main summary comment posted by CodeRabbit. Even when it says
        'Actionable comments posted: 1', the summary itself is not actionable -
        the inline comments are.
        """
        body = """<!-- This is an auto-generated comment by CodeRabbit -->

## Summary

Actionable comments posted: 1

## Walkthrough

This PR adds feature X.

| File | Changes |
|------|---------|
| foo.py | Added function |
"""
        comment = {"body": body, "path": None, "line": None}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_pr_summary_with_zero_actionable_comments(self, parser: CodeRabbitParser) -> None:
        """Test PR-level summary with 'Actionable comments posted: 0' is NON_ACTIONABLE."""
        body = """<!-- This is an auto-generated comment by CodeRabbit -->

Actionable comments posted: 0

## Walkthrough

No issues found in this PR.
"""
        comment = {"body": body, "path": None, "line": None}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_pr_summary_with_details_sections(self, parser: CodeRabbitParser) -> None:
        """Test PR-level summary with <details> sections is NON_ACTIONABLE."""
        body = """<!-- This is an auto-generated comment by CodeRabbit -->

<details>
<summary>Summary by CodeRabbit</summary>

- Added new feature
- Fixed bug
</details>

Actionable comments posted: 2
"""
        comment = {"body": body, "path": None, "line": None}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_inline_comment_with_actionable_pattern_not_filtered(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test inline comment containing 'Actionable comments' pattern is NOT filtered.

        Inline comments (with path/line) should never be filtered by summary detection,
        even if they happen to contain similar text patterns.
        """
        body = """The previous summary said "Actionable comments posted: 1" but this
inline comment is addressing the actual issue."""
        comment = {"body": body, "path": "src/file.py", "line": 42}
        classification, priority, requires_investigation = parser.parse(comment)

        # Should NOT be filtered - this is an inline comment
        # Without severity markers, it should be AMBIGUOUS
        assert classification == CommentClassification.AMBIGUOUS
        assert requires_investigation is True

    def test_pr_summary_walkthrough_only(self, parser: CodeRabbitParser) -> None:
        """Test PR-level summary with only Walkthrough section is NON_ACTIONABLE."""
        body = """## Walkthrough

The changes introduce a new parser module for handling Greptile comments.

## Changes

| File | Summary |
|------|---------|
| parser.py | New parser implementation |
"""
        comment = {"body": body, "path": None, "line": None}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_pr_summary_with_coderabbit_signature(self, parser: CodeRabbitParser) -> None:
        """Test PR-level summary with CodeRabbit signature HTML comment."""
        body = """<!-- This is an auto-generated comment by CodeRabbit -->

## Summary

This PR looks good overall.
"""
        comment = {"body": body, "path": None, "line": None}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_is_pr_summary_comment_returns_false_for_inline(self, parser: CodeRabbitParser) -> None:
        """Test _is_pr_summary_comment returns False when path is set."""
        body = (
            "<!-- This is an auto-generated comment by CodeRabbit -->\n\n"
            "Actionable comments posted: 1"
        )
        comment = {"body": body, "path": "src/file.py", "line": 10}
        assert parser._is_pr_summary_comment(comment) is False

    def test_is_pr_summary_comment_returns_true_for_pr_level(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test _is_pr_summary_comment returns True for PR-level summary."""
        body = (
            "<!-- This is an auto-generated comment by CodeRabbit -->\n\n"
            "Actionable comments posted: 1"
        )
        comment = {"body": body, "path": None, "line": None}
        assert parser._is_pr_summary_comment(comment) is True

    def test_is_pr_summary_comment_with_actionable_count_pattern(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test _is_pr_summary_comment detects 'Actionable comments posted:' pattern."""
        comment = {
            "body": "Actionable comments posted: 3\n\n## Walkthrough",
            "path": None,
            "line": None,
        }
        assert parser._is_pr_summary_comment(comment) is True

    def test_pr_summary_not_filtered_when_has_severity_marker_inline(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test inline comment with severity marker is still classified correctly.

        Even though the comment might quote summary text, if it has a severity
        marker and is inline, it should be classified by the severity.
        """
        body = "_\u26a0\ufe0f Potential issue_ | _\U0001f534 Critical_\n\nThis is critical."
        comment = {"body": body, "path": "src/file.py", "line": 42}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.ACTIONABLE
        assert priority == Priority.CRITICAL
        assert requires_investigation is False


class TestCodeRabbitParserAcknowledgments:
    """Tests for CodeRabbit acknowledgment/thank-you pattern detection."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_thank_you_for_fix(self, parser: CodeRabbitParser) -> None:
        """Test thank-you acknowledgment for fix is NON_ACTIONABLE."""
        body = "`@dsifry` Thank you for the fix!"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_parse_thank_you_for_addressing(self, parser: CodeRabbitParser) -> None:
        """Test thank-you for addressing is NON_ACTIONABLE."""
        body = "`@dsifry` Thank you for addressing this!"
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_parse_thank_you_for_catch(self, parser: CodeRabbitParser) -> None:
        """Test thank-you for catch is NON_ACTIONABLE."""
        body = "@username Thank you for the catch! The fix looks good."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_parse_thank_you_for_suggestion(self, parser: CodeRabbitParser) -> None:
        """Test thank-you for suggestion is NON_ACTIONABLE."""
        body = "`@user`, thank you for the suggestion. We'll incorporate it."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_parse_thank_you_updated_correctly(self, parser: CodeRabbitParser) -> None:
        """Test thank-you mentioning 'updated correctly' is NON_ACTIONABLE."""
        body = (
            "`@dsifry`, thank you for the fix! The example output "
            "now correctly reflects the recommended secure defaults."
        )
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_parse_thank_you_addressed(self, parser: CodeRabbitParser) -> None:
        """Test thank-you saying issue was addressed is NON_ACTIONABLE."""
        body = "`@dsifry` Thank you for addressing this! " "The updated defaults look much safer."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_is_acknowledgment_returns_true(self, parser: CodeRabbitParser) -> None:
        """Test _is_acknowledgment helper returns True for valid patterns."""
        assert parser._is_acknowledgment("`@user` Thank you for the fix!") is True
        assert parser._is_acknowledgment("Thank you for addressing this") is True

    def test_is_acknowledgment_returns_false_for_non_acknowledgment(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test _is_acknowledgment returns False for non-acknowledgment content."""
        assert parser._is_acknowledgment("This needs to be fixed") is False
        assert parser._is_acknowledgment("Please address this issue") is False

    def test_parse_thank_you_hyphenated_username(self, parser: CodeRabbitParser) -> None:
        """Test thank-you with hyphenated username is NON_ACTIONABLE.

        GitHub usernames can contain hyphens (e.g., 'foo-bar'), and the pattern
        must match these correctly.
        """
        body = "`@foo-bar` Thank you for the fix! The changes look great."
        comment = {"body": body}
        classification, priority, requires_investigation = parser.parse(comment)

        assert classification == CommentClassification.NON_ACTIONABLE
        assert requires_investigation is False

    def test_is_acknowledgment_hyphenated_username(self, parser: CodeRabbitParser) -> None:
        """Test _is_acknowledgment works with hyphenated usernames."""
        assert parser._is_acknowledgment("@foo-bar Thank you for the fix!") is True
        assert parser._is_acknowledgment("`@my-user-name` Thank you for the catch!") is True


class TestCodeRabbitParserOutsideDiffComments:
    """Tests for parsing 'Outside diff range comments' from review bodies."""

    @pytest.fixture
    def parser(self) -> CodeRabbitParser:
        """Create a CodeRabbitParser instance."""
        return CodeRabbitParser()

    def test_parse_outside_diff_comments_single_item(self, parser: CodeRabbitParser) -> None:
        """Test parsing a single outside diff comment from review body."""
        review_body = """
## Summary

Some review content here.

<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/config.py:42-45**: Consider adding validation for the config values.

</details>

Other content.
"""
        results = parser.parse_outside_diff_comments(
            review_body,
            review_id="123",
            author="coderabbitai[bot]",
            review_url="https://github.com/org/repo/pull/1#pullrequestreview-123",
        )

        assert len(results) == 1
        assert results[0].source == "coderabbitai[bot]"
        assert results[0].review_id == "123"
        assert results[0].file_path == "src/config.py"
        assert results[0].line_range == "42-45"
        assert "validation" in results[0].body
        assert results[0].review_url == "https://github.com/org/repo/pull/1#pullrequestreview-123"

    def test_parse_outside_diff_comments_multiple_items(self, parser: CodeRabbitParser) -> None:
        """Test parsing multiple outside diff comments from review body."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (3)</summary>

**src/config.py:42-45**: Consider adding validation for the config values.

**src/utils.py:100**: This function could use memoization for performance.

**tests/test_main.py:15-20**: These tests should use fixtures.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="456", author="coderabbitai[bot]"
        )

        assert len(results) == 3

        assert results[0].file_path == "src/config.py"
        assert results[0].line_range == "42-45"
        assert "validation" in results[0].body

        assert results[1].file_path == "src/utils.py"
        assert results[1].line_range == "100"
        assert "memoization" in results[1].body

        assert results[2].file_path == "tests/test_main.py"
        assert results[2].line_range == "15-20"
        assert "fixtures" in results[2].body

    def test_parse_outside_diff_comments_no_section(self, parser: CodeRabbitParser) -> None:
        """Test returns empty list when no outside diff section exists."""
        review_body = """
## Summary

This is a regular review without outside diff comments.

Everything looks good!
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="789", author="coderabbitai[bot]"
        )

        assert len(results) == 0

    def test_parse_outside_diff_comments_empty_body(self, parser: CodeRabbitParser) -> None:
        """Test returns empty list for empty review body."""
        results = parser.parse_outside_diff_comments(
            "", review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 0

    def test_parse_outside_diff_comments_empty_section(self, parser: CodeRabbitParser) -> None:
        """Test returns empty list when section exists but has no items."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (0)</summary>

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 0

    def test_parse_outside_diff_comments_multiline_body(self, parser: CodeRabbitParser) -> None:
        """Test parsing comment with multiline body text."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/handler.py:50-55**: This error handling could be improved.
You should consider catching specific exceptions rather than using a bare except.
Also, logging the error would help with debugging.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 1
        assert results[0].file_path == "src/handler.py"
        assert results[0].line_range == "50-55"
        assert "error handling" in results[0].body
        assert "logging" in results[0].body

    def test_parse_outside_diff_comments_case_insensitive(self, parser: CodeRabbitParser) -> None:
        """Test parsing is case insensitive for section header."""
        review_body = """
<details>
<summary>\u26a0\ufe0f OUTSIDE DIFF RANGE COMMENTS (1)</summary>

**src/config.py:10**: Add a docstring here.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 1
        assert results[0].file_path == "src/config.py"

    def test_parse_outside_diff_comments_with_singular_comment(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test parsing with singular 'comment' in header."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comment (1)</summary>

**src/main.py:5**: Initialize this variable.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 1
        assert results[0].file_path == "src/main.py"

    def test_parse_outside_diff_comments_preserves_review_url(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test that review_url is preserved correctly."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/config.py:1**: Add header.

</details>
"""
        url = "https://github.com/org/repo/pull/42#pullrequestreview-999"
        results = parser.parse_outside_diff_comments(
            review_body, review_id="999", author="coderabbitai[bot]", review_url=url
        )

        assert len(results) == 1
        assert results[0].review_url == url

    def test_parse_outside_diff_comments_no_review_url(self, parser: CodeRabbitParser) -> None:
        """Test that review_url can be None."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/config.py:1**: Add header.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]", review_url=None
        )

        assert len(results) == 1
        assert results[0].review_url is None

    def test_parse_outside_diff_comments_returns_outside_diff_comment_type(
        self, parser: CodeRabbitParser
    ) -> None:
        """Test that returned objects are OutsideDiffComment instances."""
        review_body = """
<details>
<summary>\u26a0\ufe0f Outside diff range comments (1)</summary>

**src/config.py:42**: Check this.

</details>
"""
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        assert len(results) == 1
        assert isinstance(results[0], OutsideDiffComment)

    def test_parse_outside_diff_comments_skips_empty_body(self, parser: CodeRabbitParser) -> None:
        """Test that items with empty body are skipped."""
        # First item has no body text after the colon, second has content
        # Note: items must be separated by blank lines (double newline)
        review_body = (
            "<details>\n"
            "<summary>\u26a0\ufe0f Outside diff range comments (2)</summary>\n\n"
            "**src/config.py:42**:\n\n"
            "**src/utils.py:10**: This has content.\n\n"
            "</details>"
        )
        results = parser.parse_outside_diff_comments(
            review_body, review_id="123", author="coderabbitai[bot]"
        )

        # Only the second item should be included (first has empty body)
        assert len(results) == 1
        assert results[0].file_path == "src/utils.py"
        assert results[0].body == "This has content."
