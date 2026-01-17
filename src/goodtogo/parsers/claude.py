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
        - claude[bot] (GitHub Actions Claude bot)
        - claude-code[bot]
        - anthropic-claude[bot]

    Body signature fallback:
        - Contains Claude Code signature patterns
        - Contains "**Claude finished" task completion marker

    Classification rules (in order of precedence):
        1. NON_ACTIONABLE: Task completion summaries (automated review headers)
        2. ACTIONABLE/CRITICAL: Explicit blocking markers (❌ Blocking, must fix before merge)
        3. NON_ACTIONABLE: Explicit approval markers (APPROVE, LGTM, ready to merge)
        4. AMBIGUOUS: Contains suggestions or unclassified
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
        re.compile(r"\*\*Claude finished", re.IGNORECASE),  # Task completion marker
    )

    # Patterns indicating BLOCKING issues that must be addressed (highest priority)
    _BLOCKING_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"❌\s*Blocking", re.IGNORECASE),
        re.compile(r"🔴\s*Critical", re.IGNORECASE),
        re.compile(r"\bmust\s+fix\s+before\s+merge\b", re.IGNORECASE),
        re.compile(r"\brequired\s+change\b", re.IGNORECASE),
        re.compile(r"\bblocking\s+issue\b", re.IGNORECASE),
        re.compile(r"\brequest\s+changes\b", re.IGNORECASE),
    )

    # Patterns indicating explicit approval (non-actionable)
    _APPROVAL_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bLGTM\b", re.IGNORECASE),
        re.compile(r"\blooks\s+good\b", re.IGNORECASE),
        re.compile(r"\bAPPROVE\b"),  # Case-sensitive for explicit APPROVE
        re.compile(r"\bship\s+it\b", re.IGNORECASE),
        re.compile(r"\bready\s+to\s+merge\b", re.IGNORECASE),
        re.compile(r"\bready\s+for\s+production\b", re.IGNORECASE),
        re.compile(r"✅\s*\*\*Overall", re.IGNORECASE),  # "✅ **Overall Assessment"
        re.compile(r"\bstrong\s+implementation\b", re.IGNORECASE),
        re.compile(r"\bwell-implemented\b", re.IGNORECASE),
        re.compile(r"\bproduction-ready\b", re.IGNORECASE),
        re.compile(r"\brecommend\s+merging\b", re.IGNORECASE),
    )

    # Patterns indicating task completion summaries (non-actionable)
    # These are automated review summaries, not actionable comments
    _SUMMARY_PATTERNS: tuple[re.Pattern[str], ...] = (
        # "**Claude finished @username's task**" header (username can have hyphens)
        re.compile(r"\*\*Claude finished @[\w-]+'s task\*\*", re.IGNORECASE),
        # "Claude finished reviewing" pattern
        re.compile(r"Claude finished reviewing", re.IGNORECASE),
        # "Claude Code Review Skipped" - PR too large or other skip reasons
        re.compile(r"Claude Code Review Skipped", re.IGNORECASE),
        # Review summary headers
        re.compile(r"^###?\s*(?:PR\s+)?Review(?:\s+Summary)?:", re.MULTILINE | re.IGNORECASE),
        # Recommendation line at end of reviews
        re.compile(r"^##?\s*Recommendation\s*$", re.MULTILINE | re.IGNORECASE),
        # "Overall Assessment" sections
        re.compile(r"^##?\s*Overall Assessment\s*$", re.MULTILINE | re.IGNORECASE),
    )

    # Patterns indicating suggestions/recommendations (ambiguous, not blocking)
    _SUGGESTION_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bconsider\b", re.IGNORECASE),
        re.compile(r"\bsuggestion\b", re.IGNORECASE),
        re.compile(r"\bmight\b", re.IGNORECASE),
        re.compile(r"\brecommendation\b", re.IGNORECASE),
        re.compile(r"\bcould\s+be\s+improved\b", re.IGNORECASE),
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

    def _parse_impl(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parser-specific classification logic for Claude Code comments.

        Classifies Claude Code comments based on keyword patterns with the
        following precedence:
        1. Blocking issues (❌, must fix) → ACTIONABLE/CRITICAL
        2. Task completion summaries → NON_ACTIONABLE
        3. Explicit approval (APPROVE, LGTM) → NON_ACTIONABLE
        4. Suggestions/recommendations → AMBIGUOUS
        5. Default → AMBIGUOUS

        This order ensures that blocking issues are always classified as
        ACTIONABLE even if they appear in task completion summaries, and that
        reviews with explicit approval markers are classified as NON_ACTIONABLE
        even if they contain words like "bug" or "error" in a positive context.

        Resolved/outdated thread checks are handled by the base class.

        Args:
            comment: Dictionary containing comment data with 'body' key.

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: ACTIONABLE, NON_ACTIONABLE, or AMBIGUOUS
            - priority: CRITICAL for blocking, UNKNOWN otherwise
            - requires_investigation: True for AMBIGUOUS classification
        """
        body = comment.get("body", "")

        # Check for blocking issues FIRST (highest priority)
        # These are explicit markers that require action before merge
        # and should take precedence even in task completion summaries
        for pattern in self._BLOCKING_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.ACTIONABLE,
                    Priority.CRITICAL,
                    False,
                )

        # Check for task completion summaries (informational, non-actionable)
        # Only checked after blocking issues, so blocking issues in summaries
        # are still classified as ACTIONABLE
        for pattern in self._SUMMARY_PATTERNS:
            if pattern.search(body):
                return (
                    CommentClassification.NON_ACTIONABLE,
                    Priority.UNKNOWN,
                    False,
                )

        # Check for explicit approval markers (non-actionable)
        # This takes precedence over suggestion patterns because a review
        # can say "APPROVE" while also containing recommendations
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
