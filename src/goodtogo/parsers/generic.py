"""Generic fallback parser for unknown reviewers.

This module provides the GenericParser class, which serves as a fallback
parser for comments that don't match any specific automated reviewer pattern.
It handles human comments and unknown reviewer types.

Per the design specification, the Generic Parser classification rules are:
- Thread is resolved -> NON_ACTIONABLE
- Thread is outdated -> NON_ACTIONABLE
- Reply confirmation patterns -> NON_ACTIONABLE (acknowledging fixes)
- Approval patterns (LGTM, etc.) -> NON_ACTIONABLE
- All other -> AMBIGUOUS with requires_investigation=True
"""

from __future__ import annotations

import re

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import (
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
    - Reply confirmation patterns -> NON_ACTIONABLE (acknowledging fixes)
    - Approval patterns -> NON_ACTIONABLE (LGTM, looks good, etc.)
    - All other comments -> AMBIGUOUS with requires_investigation=True

    This conservative approach ensures that AI agents never miss potentially
    important feedback by automatically dismissing it.
    """

    # Patterns indicating a reply that confirms something was addressed
    # These are typically non-actionable acknowledgments
    REPLY_CONFIRMATION_PATTERNS = [
        # Explicit fix confirmations
        re.compile(r"^(good\s+catch|great\s+catch|nice\s+catch)", re.IGNORECASE),
        re.compile(r"^fixed\s+(in\s+)?(commit|[a-f0-9]{7})", re.IGNORECASE),
        re.compile(r"^done[.!]?\s*$", re.IGNORECASE),
        re.compile(r"^addressed[.!]?\s*$", re.IGNORECASE),
        re.compile(r"^resolved[.!]?\s*$", re.IGNORECASE),
        # Acknowledgments and thanks
        re.compile(r"^thanks[!.,]?\s*$", re.IGNORECASE),
        re.compile(r"^thank\s+you[!.,]?\s*$", re.IGNORECASE),
        re.compile(r"^will\s+(fix|do|address|update)", re.IGNORECASE),
        re.compile(r"^updated[.!]?\s*$", re.IGNORECASE),
        re.compile(r"^applied[.!]?\s*$", re.IGNORECASE),
        # Agreement patterns - must be complete confirmations, not prefixes
        re.compile(r"^(yep|yeah|yes)[,.]?\s+(fixed|done|updated|addressed)", re.IGNORECASE),
        re.compile(r"^agreed[,.]?\s*(fixed|done|updated)?[.!]?\s*$", re.IGNORECASE),
        re.compile(r"^makes\s+sense[.!]?\s*$", re.IGNORECASE),
    ]

    # Patterns indicating approval or positive feedback (non-actionable)
    APPROVAL_PATTERNS = [
        re.compile(r"^lgtm[!.]?\s*$", re.IGNORECASE),
        re.compile(r"^looks\s+good(\s+to\s+me)?[!.]?\s*$", re.IGNORECASE),
        re.compile(r"^ship\s+it[!.]?\s*$", re.IGNORECASE),
        re.compile(r"^\+1\s*$"),
        re.compile(r"^:?\+1:?\s*$"),  # emoji format
        re.compile(r"^approved[!.]?\s*$", re.IGNORECASE),
    ]

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
        """Return True for all comments.

        As the fallback parser, GenericParser accepts all comments that
        weren't matched by more specific parsers. This ensures no comments
        are dropped or unhandled.

        Args:
            author: Comment author's username/login (ignored).
            body: Comment body text (ignored).

        Returns:
            Always True - this is the catch-all parser.
        """
        return True

    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parse comment and return classification.

        Classification logic:
        1. Resolved threads -> NON_ACTIONABLE
        2. Outdated threads -> NON_ACTIONABLE
        3. Reply confirmation patterns -> NON_ACTIONABLE
        4. Approval patterns -> NON_ACTIONABLE
        5. All other -> AMBIGUOUS with requires_investigation=True

        Note: This parser intentionally does NOT try to interpret comment
        content for actionability. That would be unreliable for human comments.
        Instead, it relies on metadata (resolved/outdated status) and simple
        patterns that indicate the comment has been addressed.

        Args:
            comment: Dictionary containing comment data with:
                - 'body': Comment text content (optional)
                - 'is_resolved': Boolean indicating if thread is resolved
                - 'is_outdated': Boolean indicating if comment is outdated

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority.UNKNOWN (generic parser doesn't assess priority)
            - requires_investigation: True for AMBIGUOUS, False otherwise
        """
        # Check if thread is resolved
        if comment.get("is_resolved", False):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check if thread is outdated
        if comment.get("is_outdated", False):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        body = comment.get("body", "")

        # Check for reply confirmation patterns (acknowledging fixes)
        if self._is_reply_confirmation(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check for approval patterns (LGTM, looks good, etc.)
        if self._is_approval(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # All other cases: AMBIGUOUS with requires_investigation=True
        # Critical: AMBIGUOUS comments MUST always have requires_investigation=True
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)

    def _is_reply_confirmation(self, body: str) -> bool:
        """Check if the body is a reply confirmation.

        Reply confirmations are comments that acknowledge something was
        addressed or fixed, such as "Good catch!", "Fixed in commit abc123", etc.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be a reply confirmation.
        """
        body_stripped = body.strip()
        for pattern in self.REPLY_CONFIRMATION_PATTERNS:
            if pattern.search(body_stripped):
                return True
        return False

    def _is_approval(self, body: str) -> bool:
        """Check if the body is an approval comment.

        Approval comments are positive feedback that indicate the code
        is acceptable, such as "LGTM", "Looks good", "+1", etc.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be an approval.
        """
        body_stripped = body.strip()
        for pattern in self.APPROVAL_PATTERNS:
            if pattern.search(body_stripped):
                return True
        return False
