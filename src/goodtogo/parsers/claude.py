"""Claude Code parser for GoodToMerge.

This module implements the ReviewerParser interface for parsing comments
from Claude Code (Anthropic's AI coding assistant). It classifies comments
based on pattern matching to determine actionability and priority.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType

if TYPE_CHECKING:
    pass


class ClaudeCodeParser(ReviewerParser):
    """Parser for Claude Code automated reviewer comments.

    Identifies and classifies comments from Claude Code based on author
    patterns and body content. Uses keyword-based heuristics to determine
    comment classification and priority.

    Author patterns:
        - claude-code[bot]
        - anthropic-claude[bot]

    Body signature fallback:
        - Contains Claude Code signature patterns

    Classification rules:
        - ACTIONABLE: Contains "must", "should fix", "error", "bug"
        - NON_ACTIONABLE: LGTM / approval keywords
        - AMBIGUOUS: Contains "consider", "suggestion", "might" or unclassified
    """

    # Author patterns that identify Claude Code comments
    _AUTHOR_PATTERNS: tuple[str, ...] = (
        "claude[bot]",
        "claude-code[bot]",
        "anthropic-claude[bot]",
    )

    # Body patterns that identify Claude Code comments (fallback)
    _BODY_SIGNATURE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"Generated with Claude Code", re.IGNORECASE),
        re.compile(r"Claude Code", re.IGNORECASE),
    )

    # Patterns indicating actionable comments (case-insensitive)
    _ACTIONABLE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bmust\b", re.IGNORECASE),
        re.compile(r"\bshould\s+fix\b", re.IGNORECASE),
        re.compile(r"\berror\b", re.IGNORECASE),
        re.compile(r"\bbug\b", re.IGNORECASE),
    )

    # Patterns indicating non-actionable approval comments (case-insensitive)
    _APPROVAL_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bLGTM\b", re.IGNORECASE),
        re.compile(r"\blooks\s+good\b", re.IGNORECASE),
        re.compile(r"\bapproved?\b", re.IGNORECASE),
        re.compile(r"\bship\s+it\b", re.IGNORECASE),
    )

    # Patterns indicating task completion summaries (non-actionable)
    # These are automated review summaries, not actionable comments
    _SUMMARY_PATTERNS: tuple[re.Pattern[str], ...] = (
        # "**Claude finished @username's task**" header (username can have hyphens)
        re.compile(r"\*\*Claude finished @[\w-]+'s task\*\*", re.IGNORECASE),
        # "Claude finished reviewing" pattern
        re.compile(r"Claude finished reviewing", re.IGNORECASE),
        # Review summary headers
        re.compile(r"^###?\s*(?:PR\s+)?Review(?:\s+Summary)?:", re.MULTILINE | re.IGNORECASE),
        # Recommendation line at end of reviews
        re.compile(r"^##?\s*Recommendation\s*$", re.MULTILINE | re.IGNORECASE),
        # "Overall Assessment" sections
        re.compile(r"^##?\s*Overall Assessment\s*$", re.MULTILINE | re.IGNORECASE),
    )

    # Patterns indicating ambiguous/suggestion comments (case-insensitive)
    _SUGGESTION_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bconsider\b", re.IGNORECASE),
        re.compile(r"\bsuggestion\b", re.IGNORECASE),
        re.compile(r"\bmight\b", re.IGNORECASE),
    )

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType.CLAUDE for Claude Code comments.
        """
        return ReviewerType.CLAUDE

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        Identifies Claude Code comments by:
        1. Matching author name against known bot patterns
        2. Checking body for Claude Code signature patterns (fallback)

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if the comment appears to be from Claude Code.
        """
        # Check author patterns first (most reliable)
        author_lower = author.lower()
        for author_pattern in self._AUTHOR_PATTERNS:
            if author_pattern.lower() == author_lower:
                return True

        # Fallback: check body for Claude signature
        for body_pattern in self._BODY_SIGNATURE_PATTERNS:
            if body_pattern.search(body):
                return True

        return False

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment and return classification.

        Classifies Claude Code comments based on keyword patterns:
        - Actionable: Contains "must", "should fix", "error", "bug"
        - Non-actionable: LGTM / approval keywords
        - Ambiguous: Contains "consider", "suggestion", "might" or unclassified

        Args:
            comment: Dictionary containing comment data with 'body' key.

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: ACTIONABLE, NON_ACTIONABLE, or AMBIGUOUS
            - priority: MINOR for actionable, UNKNOWN otherwise
            - requires_investigation: True for AMBIGUOUS classification
        """
        body = comment.get("body", "")

        # Check for task completion summaries first (these are informational)
        for pattern in self._SUMMARY_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.NON_ACTIONABLE,
                    Priority.UNKNOWN,
                    False,
                )

        # Check for actionable patterns (highest priority for non-summary comments)
        for pattern in self._ACTIONABLE_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.ACTIONABLE,
                    Priority.MINOR,
                    False,
                )

        # Check for approval/LGTM patterns (non-actionable)
        for pattern in self._APPROVAL_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.NON_ACTIONABLE,
                    Priority.UNKNOWN,
                    False,
                )

        # Check for suggestion patterns (ambiguous, needs investigation)
        for pattern in self._SUGGESTION_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.AMBIGUOUS,
                    Priority.UNKNOWN,
                    True,
                )

        # Default: ambiguous, requires investigation
        # Per design spec: "Never silently skip ambiguous comments"
        return (
            CommentClassification.AMBIGUOUS,
            Priority.UNKNOWN,
            True,
        )
