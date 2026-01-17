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
- Severity markers (**logic:**, **bug:**, **security:**) -> ACTIONABLE with priority
- Other -> AMBIGUOUS, UNKNOWN, requires_investigation=True
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType

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

    # Severity marker patterns for Greptile inline comments
    # Format: **category:** description (e.g., **logic:** The function...)
    # These patterns indicate specific issues found by Greptile
    SEVERITY_PATTERNS: list[tuple[re.Pattern[str], Priority]] = [
        # Critical severity markers (security, bug, error)
        (re.compile(r"\*\*security[:\s]", re.IGNORECASE), Priority.CRITICAL),
        (re.compile(r"\*\*bug[:\s]", re.IGNORECASE), Priority.MAJOR),
        (re.compile(r"\*\*error[:\s]", re.IGNORECASE), Priority.MAJOR),
        # Medium severity markers (logic, performance)
        (re.compile(r"\*\*logic[:\s]", re.IGNORECASE), Priority.MINOR),
        (re.compile(r"\*\*performance[:\s]", re.IGNORECASE), Priority.MINOR),
        # Lower severity markers (style, typo, suggestion)
        (re.compile(r"\*\*style[:\s]", re.IGNORECASE), Priority.TRIVIAL),
        (re.compile(r"\*\*typo[:\s]", re.IGNORECASE), Priority.TRIVIAL),
        (re.compile(r"\*\*nitpick[:\s]", re.IGNORECASE), Priority.TRIVIAL),
    ]

    # PR-level summary comment patterns (non-actionable)
    # These are posted at the PR level (path=None) and contain overview information.
    # The actual actionable items are in inline comments.
    PR_SUMMARY_PATTERNS = [
        # Greptile Summary HTML header
        re.compile(r"<h3>Greptile Summary</h3>", re.IGNORECASE),
        # "N files reviewed" pattern
        re.compile(r"\d+\s+files?\s+reviewed", re.IGNORECASE),
        # Edit Code Review Agent Settings link
        re.compile(r"Edit Code Review Agent Settings", re.IGNORECASE),
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
        1. PR-level summary comments -> NON_ACTIONABLE
        2. "Actionable comments posted: 0" -> NON_ACTIONABLE
        3. "Actionable comments posted: N" (N > 0) -> ACTIONABLE, MINOR
        4. Review summary only -> NON_ACTIONABLE
        5. Severity markers (**logic:**, **bug:**) -> ACTIONABLE with priority
        6. Other -> AMBIGUOUS, UNKNOWN, requires_investigation=True

        Args:
            comment: Dictionary containing comment data with at least:
                - 'body': Comment text content
                - 'user': Dictionary with 'login' key
                - Optionally 'path' and 'line' for inline comments

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority enum value
            - requires_investigation: Boolean, True for AMBIGUOUS comments
        """
        # Check for PR-level summary comments first (highest precedence)
        # These are posted at the PR level and contain overview information
        if self._is_pr_summary_comment(comment):
            return CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False

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

        # Check for severity markers (**logic:**, **bug:**, etc.)
        severity_result = self._check_severity_markers(body)
        if severity_result is not None:
            return severity_result

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

    def _check_severity_markers(
        self, body: str
    ) -> tuple[CommentClassification, Priority, bool] | None:
        """Check for Greptile severity markers in the comment body.

        Greptile uses **category:** format to indicate the type and
        severity of issues found. For example:
        - **logic:** indicates a logic error
        - **security:** indicates a security issue
        - **bug:** indicates a bug

        Args:
            body: Comment body text.

        Returns:
            Tuple of (classification, priority, requires_investigation) if a
            severity marker is found, None otherwise.
        """
        for pattern, priority in self.SEVERITY_PATTERNS:
            if pattern.search(body):
                # Trivial priority markers are non-actionable
                if priority == Priority.TRIVIAL:
                    return CommentClassification.NON_ACTIONABLE, priority, False
                return CommentClassification.ACTIONABLE, priority, False
        return None

    def _is_pr_summary_comment(self, comment: dict) -> bool:
        """Check if this is a PR-level summary comment.

        PR-level summary comments are posted at the PR level (not inline)
        and contain overview information like Greptile Summary headers,
        "N files reviewed" counts, or settings links. These should be
        classified as NON_ACTIONABLE because the actual actionable items
        are in inline comments.

        Key criteria:
        1. Must be a PR-level comment (path=None or missing)
        2. Must match one of the PR summary patterns

        Args:
            comment: Dictionary containing comment data with 'body' key,
                and optionally 'path' and 'line' keys.

        Returns:
            True if this is a PR-level summary comment that should be
            classified as NON_ACTIONABLE.
        """
        # Only filter PR-level comments (path=None or missing)
        # Never filter inline comments (they have path/line set)
        path = comment.get("path")
        if path is not None:
            return False

        body = comment.get("body", "")
        if not body:
            return False

        # Check for PR summary patterns
        for pattern in self.PR_SUMMARY_PATTERNS:
            if pattern.search(body):
                return True

        # Also check for review summary content at PR level
        if self._is_review_summary(body):
            return True

        return False
