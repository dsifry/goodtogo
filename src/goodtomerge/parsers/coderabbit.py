"""CodeRabbit comment parser for GoodToMerge.

This module implements the ReviewerParser interface for parsing comments
from CodeRabbit, an AI-powered automated code review tool.

CodeRabbit uses specific patterns to indicate comment severity and type:
- Severity indicators with emojis and labels
- Fingerprinting comments (internal metadata)
- Resolution status markers
- Outside diff range notifications
"""

from __future__ import annotations

import re

from goodtomerge.core.interfaces import ReviewerParser
from goodtomerge.core.models import CommentClassification, Priority, ReviewerType


class CodeRabbitParser(ReviewerParser):
    """Parser for CodeRabbit automated code review comments.

    CodeRabbit posts comments with structured severity indicators that
    can be deterministically parsed to classify comment actionability.

    Patterns recognized:
        - _Potential issue_ | _Critical/Major/Minor_: ACTIONABLE
        - _Trivial_: NON_ACTIONABLE
        - _Nitpick_: NON_ACTIONABLE
        - Fingerprinting HTML comments: NON_ACTIONABLE
        - Addressed checkmarks: NON_ACTIONABLE
        - Outside diff range mentions: ACTIONABLE (MINOR)
        - All other: AMBIGUOUS

    Author detection:
        - Primary: author == "coderabbitai[bot]"
        - Fallback: body contains CodeRabbit signature comment
    """

    # Author pattern for CodeRabbit bot
    CODERABBIT_AUTHOR = "coderabbitai[bot]"

    # Body pattern for CodeRabbit signature (fallback detection)
    CODERABBIT_SIGNATURE_PATTERN = re.compile(
        r"<!-- This is an auto-generated comment.*by coderabbit\.ai -->",
        re.IGNORECASE | re.DOTALL,
    )

    # Severity patterns - using re.escape for literal characters
    # Pattern: _Potential issue_ | _Critical/Major/Minor_
    CRITICAL_PATTERN = re.compile(
        r"_\u26a0\ufe0f\s*Potential issue_\s*\|\s*_\U0001f534\s*Critical_",
        re.IGNORECASE,
    )
    MAJOR_PATTERN = re.compile(
        r"_\u26a0\ufe0f\s*Potential issue_\s*\|\s*_\U0001f7e0\s*Major_",
        re.IGNORECASE,
    )
    MINOR_PATTERN = re.compile(
        r"_\u26a0\ufe0f\s*Potential issue_\s*\|\s*_\U0001f7e1\s*Minor_",
        re.IGNORECASE,
    )

    # Non-actionable patterns
    TRIVIAL_PATTERN = re.compile(r"_\U0001f535\s*Trivial_", re.IGNORECASE)
    NITPICK_PATTERN = re.compile(r"_\U0001f9f9\s*Nitpick_", re.IGNORECASE)

    # Fingerprinting comments (internal CodeRabbit metadata)
    FINGERPRINT_PATTERN = re.compile(r"<!--\s*fingerprinting:", re.IGNORECASE)

    # Addressed status marker
    ADDRESSED_PATTERN = re.compile(r"\u2705\s*Addressed", re.IGNORECASE)

    # Outside diff range (in review body)
    OUTSIDE_DIFF_PATTERN = re.compile(r"Outside diff range", re.IGNORECASE)

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType.CODERABBIT
        """
        return ReviewerType.CODERABBIT

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        Identifies CodeRabbit comments by:
        1. Author being "coderabbitai[bot]" (primary method)
        2. Body containing CodeRabbit signature HTML comment (fallback)

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if this is a CodeRabbit comment, False otherwise.
        """
        # Primary detection: check author
        if author == self.CODERABBIT_AUTHOR:
            return True

        # Fallback detection: check body for signature
        if body and self.CODERABBIT_SIGNATURE_PATTERN.search(body):
            return True

        return False

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse CodeRabbit comment and return classification.

        Analyzes the comment body to determine classification and priority
        based on CodeRabbit's severity indicators.

        Classification rules (in order of precedence):
            1. Fingerprinting comments -> NON_ACTIONABLE
            2. Addressed marker -> NON_ACTIONABLE
            3. Critical severity -> ACTIONABLE, CRITICAL
            4. Major severity -> ACTIONABLE, MAJOR
            5. Minor severity -> ACTIONABLE, MINOR
            6. Trivial severity -> NON_ACTIONABLE, TRIVIAL
            7. Nitpick marker -> NON_ACTIONABLE, TRIVIAL
            8. Outside diff range -> ACTIONABLE, MINOR
            9. All other -> AMBIGUOUS, UNKNOWN, requires_investigation=True

        Args:
            comment: Dictionary containing comment data with 'body' key.

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority enum value
            - requires_investigation: Boolean, True for AMBIGUOUS comments
        """
        body = comment.get("body", "")

        # Early exit for empty body
        if not body:
            return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)

        # Check fingerprinting comments first (internal metadata, ignore)
        if self.FINGERPRINT_PATTERN.search(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check addressed marker
        if self.ADDRESSED_PATTERN.search(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check severity patterns (most specific first)
        if self.CRITICAL_PATTERN.search(body):
            return (CommentClassification.ACTIONABLE, Priority.CRITICAL, False)

        if self.MAJOR_PATTERN.search(body):
            return (CommentClassification.ACTIONABLE, Priority.MAJOR, False)

        if self.MINOR_PATTERN.search(body):
            return (CommentClassification.ACTIONABLE, Priority.MINOR, False)

        # Check non-actionable patterns
        if self.TRIVIAL_PATTERN.search(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.TRIVIAL, False)

        if self.NITPICK_PATTERN.search(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.TRIVIAL, False)

        # Check outside diff range (actionable but lower priority)
        if self.OUTSIDE_DIFF_PATTERN.search(body):
            return (CommentClassification.ACTIONABLE, Priority.MINOR, False)

        # Default: AMBIGUOUS - requires investigation
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)
