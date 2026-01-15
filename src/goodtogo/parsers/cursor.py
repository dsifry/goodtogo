"""Cursor/Bugbot comment parser.

This module implements the ReviewerParser interface for parsing comments
from Cursor's Bugbot automated code reviewer.

Cursor/Bugbot uses severity-based classification:
- Critical Severity: Must fix immediately
- High Severity: Must fix before merge
- Medium Severity: Should fix
- Low Severity: Nice to fix (non-actionable)
"""

from __future__ import annotations

import re

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType


class CursorBugbotParser(ReviewerParser):
    """Parser for Cursor/Bugbot automated code review comments.

    Detects comments from Cursor's Bugbot based on author patterns and
    body content signatures. Classifies based on severity indicators
    in the comment body.

    Author patterns:
        - "cursor[bot]"
        - "cursor-bot"

    Body signatures:
        - cursor.com links
        - Cursor-specific formatting

    Severity mapping:
        - Critical Severity -> ACTIONABLE, CRITICAL
        - High Severity -> ACTIONABLE, MAJOR
        - Medium Severity -> ACTIONABLE, MINOR
        - Low Severity -> NON_ACTIONABLE, TRIVIAL
        - No severity indicator -> AMBIGUOUS, UNKNOWN
    """

    # Author patterns that identify Cursor/Bugbot comments
    _AUTHOR_PATTERNS = frozenset({"cursor[bot]", "cursor-bot"})

    # Patterns in body that indicate Cursor/Bugbot origin
    _CURSOR_BODY_SIGNATURES = (re.compile(r"cursor\.com", re.IGNORECASE),)

    # Severity patterns and their classifications
    _SEVERITY_PATTERNS = (
        (
            re.compile(r"Critical\s+Severity", re.IGNORECASE),
            CommentClassification.ACTIONABLE,
            Priority.CRITICAL,
        ),
        (
            re.compile(r"High\s+Severity", re.IGNORECASE),
            CommentClassification.ACTIONABLE,
            Priority.MAJOR,
        ),
        (
            re.compile(r"Medium\s+Severity", re.IGNORECASE),
            CommentClassification.ACTIONABLE,
            Priority.MINOR,
        ),
        (
            re.compile(r"Low\s+Severity", re.IGNORECASE),
            CommentClassification.NON_ACTIONABLE,
            Priority.TRIVIAL,
        ),
    )

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType.CURSOR
        """
        return ReviewerType.CURSOR

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        A comment can be parsed by this parser if:
        1. The author matches known Cursor/Bugbot patterns, OR
        2. The body contains Cursor-specific signatures

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if this parser can handle the comment, False otherwise.
        """
        # Check author patterns (case-insensitive)
        author_lower = author.lower()
        if author_lower in self._AUTHOR_PATTERNS:
            return True

        # Check body signatures
        for pattern in self._CURSOR_BODY_SIGNATURES:
            if pattern.search(body):
                return True

        return False

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment and return classification.

        Analyzes the comment body for severity indicators to determine
        classification and priority. Comments without a recognized
        severity pattern are classified as AMBIGUOUS.

        Args:
            comment: Dictionary containing comment data with at least:
                - 'body': Comment text content

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority enum value
            - requires_investigation: True if AMBIGUOUS, False otherwise
        """
        body = comment.get("body", "")

        # Check each severity pattern in order of priority
        for pattern, classification, priority in self._SEVERITY_PATTERNS:
            if pattern.search(body):
                return classification, priority, False

        # No recognized severity pattern - classify as ambiguous
        # This requires investigation by the agent
        return CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True
