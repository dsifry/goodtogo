"""Vercel parser for classifying comments from Vercel deployment bot.

This module provides the VercelParser class that implements the ReviewerParser
interface for parsing and classifying comments from the Vercel deployment bot.

Vercel comments are identified by:
- Author: "vercel[bot]"
- Body patterns: Contains "[vc]:", "vercel.com", or deployment table with "Preview" links

Classification rules:
- ALL Vercel comments are NON_ACTIONABLE / TRIVIAL - they are deployment status
  notifications, never code review feedback.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType

if TYPE_CHECKING:
    pass


class VercelParser(ReviewerParser):
    """Parser for Vercel deployment bot comments.

    Implements the ReviewerParser interface to classify comments from
    the Vercel deployment bot. All Vercel comments are deployment status
    notifications and are always classified as NON_ACTIONABLE.
    """

    # Pattern to detect Vercel signature/branding in body
    VERCEL_SIGNATURE_PATTERN = re.compile(
        r"\[vc\]:|vercel\.com|" r"https?://[^\s]*\.vercel\.app|" r"\*\*Preview\*\*",
        re.IGNORECASE,
    )

    @property
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles.

        Returns:
            ReviewerType.VERCEL
        """
        return ReviewerType.VERCEL

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment.

        Vercel comments are identified by:
        1. Author is "vercel[bot]"
        2. Body contains Vercel signature/links (fallback detection)

        Args:
            author: Comment author's username/login.
            body: Comment body text.

        Returns:
            True if this appears to be a Vercel comment, False otherwise.
        """
        # Primary detection: author is vercel bot
        if author.lower() == "vercel[bot]":
            return True

        # Fallback detection: body contains Vercel signature
        if self.VERCEL_SIGNATURE_PATTERN.search(body):
            return True

        return False

    def _parse_impl(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parser-specific classification logic for Vercel comments.

        All Vercel comments are deployment status notifications and are
        always classified as NON_ACTIONABLE with TRIVIAL priority.

        Resolved/outdated thread checks are handled by the base class.

        Args:
            comment: Dictionary containing comment data with at least:
                - 'body': Comment text content
                - 'user': Dictionary with 'login' key

        Returns:
            Tuple of (NON_ACTIONABLE, TRIVIAL, False) - always.
        """
        return CommentClassification.NON_ACTIONABLE, Priority.TRIVIAL, False
