"""Greptile parser for classifying comments from Greptile code reviewer.

This module provides the GreptileParser class that implements the ReviewerParser
interface for parsing and classifying comments from the Greptile automated
code review tool.

Greptile comments are identified by:
- Author: "greptile[bot]"
- Body patterns: Contains "greptile.com" links or "Greptile" branding

Classification rules (per design spec):
- "Actionable comments posted: 0" -> NON_ACTIONABLE
- "Actionable comments posted: N" (N > 0) -> ACTIONABLE, MINOR
- Review summary only -> NON_ACTIONABLE
- Other -> AMBIGUOUS, UNKNOWN, requires_investigation=True
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from goodtomerge.core.interfaces import ReviewerParser
from goodtomerge.core.models import CommentClassification, Priority, ReviewerType

if TYPE_CHECKING:
    pass


class GreptileParser(ReviewerParser):
    """Parser for Greptile automated code reviewer comments.

    Implements the ReviewerParser interface to classify comments from
    Greptile based on patterns defined in the GoodToMerge design specification.
    """

    # Pattern to detect "Actionable comments posted: N" where N is a number
    ACTIONABLE_PATTERN = re.compile(r"Actionable comments posted:\s*(\d+)", re.IGNORECASE)

    # Pattern to detect Greptile signature/branding in body
    GREPTILE_SIGNATURE_PATTERN = re.compile(r"greptile\.com|greptile|Greptile", re.IGNORECASE)

    # Patterns indicating a review summary (non-actionable)
    REVIEW_SUMMARY_PATTERNS = [
        re.compile(r"^#+\s*(Summary|Review Summary|PR Summary)", re.MULTILINE),
        re.compile(r"(reviewed|analyzed)\s+(this\s+)?(PR|pull\s+request)", re.IGNORECASE),
    ]

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType.GREPTILE
        """
        return ReviewerType.GREPTILE

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        Greptile comments are identified by:
        1. Author is "greptile[bot]"
        2. Body contains Greptile signature/links (fallback detection)

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if this appears to be a Greptile comment, False otherwise.
        """
        # Primary detection: author is greptile bot
        if author.lower() == "greptile[bot]":
            return True

        # Fallback detection: body contains Greptile signature
        if self.GREPTILE_SIGNATURE_PATTERN.search(body):
            return True

        return False

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment and return classification.

        Classification logic (per design spec):
        1. "Actionable comments posted: 0" -> NON_ACTIONABLE
        2. "Actionable comments posted: N" (N > 0) -> ACTIONABLE, MINOR
        3. Review summary only -> NON_ACTIONABLE
        4. Other -> AMBIGUOUS, UNKNOWN, requires_investigation=True

        Args:
            comment: Dictionary containing comment data with at least:
                - 'body': Comment text content
                - 'user': Dictionary with 'login' key

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority enum value
            - requires_investigation: Boolean, True for AMBIGUOUS comments
        """
        body = comment.get("body", "")

        # Check for "Actionable comments posted: N" pattern
        match = self.ACTIONABLE_PATTERN.search(body)
        if match:
            count = int(match.group(1))
            if count == 0:
                # No actionable comments
                return CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False
            else:
                # Has actionable comments - classify as ACTIONABLE with MINOR priority
                return CommentClassification.ACTIONABLE, Priority.MINOR, False

        # Check if this is a review summary (non-actionable)
        if self._is_review_summary(body):
            return CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False

        # Default: AMBIGUOUS - cannot determine classification
        # Per design spec: AMBIGUOUS comments MUST have requires_investigation=True
        return CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True

    def _is_review_summary(self, body: str) -> bool:
        """Check if the body is a review summary.

        Review summaries typically contain overview information about
        the PR without specific actionable items.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be a review summary.
        """
        for pattern in self.REVIEW_SUMMARY_PATTERNS:
            if pattern.search(body):
                return True
        return False
