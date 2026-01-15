"""Generic fallback parser for unknown reviewers.

This module provides the GenericParser class, which serves as a fallback
parser for comments that don't match any specific automated reviewer pattern.
It handles human comments and unknown reviewer types.

Per the design specification, the Generic Parser classification rules are:
- Thread is resolved -> NON_ACTIONABLE
- Thread is outdated -> NON_ACTIONABLE
- Contains reply from PR author -> NON_ACTIONABLE (future enhancement)
- All other -> AMBIGUOUS with requires_investigation=True
"""

from __future__ import annotations

from goodtomerge.core.interfaces import ReviewerParser
from goodtomerge.core.models import (
    CommentClassification,
    Priority,
    ReviewerType,
)


class GenericParser(ReviewerParser):
    """Fallback parser for unknown reviewers and human comments.

    This parser is used when no specific reviewer parser matches the comment.
    It applies conservative classification rules, marking most comments as
    AMBIGUOUS to ensure nothing is silently skipped.

    The GenericParser serves two purposes:
    1. Handle comments from human reviewers (ReviewerType.HUMAN)
    2. Act as a fallback for any unrecognized automated reviewers

    Classification logic:
    - Resolved threads -> NON_ACTIONABLE (already addressed)
    - Outdated threads -> NON_ACTIONABLE (code has changed)
    - All other comments -> AMBIGUOUS with requires_investigation=True

    This conservative approach ensures that AI agents never miss potentially
    important feedback by automatically dismissing it.
    """

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return ReviewerType.HUMAN.

        The generic parser is used for human reviewers and as a fallback
        for unknown reviewer types. HUMAN is returned as it's the most
        appropriate classification for non-automated reviews.

        Returns:
            ReviewerType.HUMAN
        """
        return ReviewerType.HUMAN

    def can_parse(self, author: str, body: str) -> bool:
        """Always returns True - this is the fallback parser.

        The GenericParser accepts any comment, serving as the last resort
        when no specific reviewer parser matches. It should be registered
        last in the parser chain.

        Args:
            author: Comment author's username/login (unused).
            body: Comment body text (unused).

        Returns:
            Always True - this parser accepts all comments.
        """
        return True

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment using conservative classification rules.

        Applies the Generic Parser rules from the design specification:
        1. If thread is resolved -> NON_ACTIONABLE
        2. If thread is outdated -> NON_ACTIONABLE
        3. All other cases -> AMBIGUOUS with requires_investigation=True

        Args:
            comment: Dictionary containing comment data with optional keys:
                - 'is_resolved': Boolean indicating if thread is resolved
                - 'is_outdated': Boolean indicating if thread is outdated
                - 'body': Comment text content
                - Other keys as needed

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - For resolved/outdated: (NON_ACTIONABLE, UNKNOWN, False)
            - For all others: (AMBIGUOUS, UNKNOWN, True)

        Note:
            AMBIGUOUS comments always have requires_investigation=True.
            This ensures AI agents escalate uncertain cases to humans
            rather than making potentially incorrect assumptions.
        """
        # Check if thread is resolved
        if comment.get("is_resolved", False):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check if thread is outdated
        if comment.get("is_outdated", False):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Future enhancement: Check for reply from PR author
        # This would require access to PR author information and
        # checking if the comment is part of a conversation where
        # the PR author has responded. For now, treat as AMBIGUOUS.

        # All other cases: AMBIGUOUS with requires_investigation=True
        # Critical: AMBIGUOUS comments MUST always have requires_investigation=True
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)
