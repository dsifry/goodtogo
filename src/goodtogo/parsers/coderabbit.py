"""CodeRabbit comment parser for GoodToMerge.

This module implements the ReviewerParser interface for parsing comments
from CodeRabbit, an AI-powered automated code review tool.

CodeRabbit uses specific patterns to indicate comment severity and type:
- Severity indicators with emojis and labels
- Fingerprinting comments (internal metadata)
- Resolution status markers
- Outside diff range notifications
- Summary/walkthrough sections (non-actionable)
"""

from __future__ import annotations

import re

from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import (
    CommentClassification,
    OutsideDiffComment,
    Priority,
    ReviewerType,
)


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
        - Summary/walkthrough sections: NON_ACTIONABLE
        - Tip/info boxes: NON_ACTIONABLE
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

    # Acknowledgment patterns (thank-you replies indicating issue was addressed)
    # These are reply comments from CodeRabbit confirming a fix was applied
    # Note: GitHub usernames can contain hyphens, so we use [\w-] instead of \w
    ACKNOWLEDGMENT_PATTERNS = [
        # "@username Thank you for the fix/catch/suggestion/addressing"
        re.compile(
            r"`?@[\w-]+`?\s+Thank\s+you\s+for\s+(the\s+)?(fix|catch|suggestion|addressing)",
            re.IGNORECASE,
        ),
        # "Thank you for addressing this"
        re.compile(r"Thank\s+you\s+for\s+addressing\s+this", re.IGNORECASE),
        # Starts with "Thank you" and contains keywords like fix, addressed, suggestion
        re.compile(
            r"^`?@?[\w-]*`?\s*,?\s*[Tt]hank\s+you.*?(fix|addressed|updated|resolved|correct|suggestion)",
            re.IGNORECASE,
        ),
    ]

    # Outside diff range (in review body)
    OUTSIDE_DIFF_PATTERN = re.compile(r"Outside diff range", re.IGNORECASE)

    # Summary/walkthrough patterns (non-actionable informational content)
    # These are overview sections that don't require action
    SUMMARY_PATTERNS = [
        # Walkthrough header
        re.compile(r"^##\s*Walkthrough", re.MULTILINE),
        # Changes summary header
        re.compile(r"^##\s*Changes", re.MULTILINE),
        # Summary header
        re.compile(r"^##\s*Summary", re.MULTILINE),
        # PR summary pattern
        re.compile(r"^##\s*PR\s+Summary", re.MULTILINE | re.IGNORECASE),
        # Review summary
        re.compile(r"^##\s*Review\s+Summary", re.MULTILINE | re.IGNORECASE),
        # File summary table pattern (CodeRabbit specific)
        re.compile(r"\|\s*File\s*\|\s*Changes\s*\|", re.IGNORECASE),
        # Sequence diagram indicators
        re.compile(r"```mermaid", re.IGNORECASE),
        # PR Objectives section
        re.compile(r"^##\s*Objectives", re.MULTILINE | re.IGNORECASE),
    ]

    # Tip/info box patterns (non-actionable)
    TIP_PATTERNS = [
        re.compile(r"^>\s*\[!TIP\]", re.MULTILINE),
        re.compile(r"^>\s*\[!NOTE\]", re.MULTILINE),
        re.compile(r"^>\s*\[!INFO\]", re.MULTILINE),
    ]

    # PR-level summary comment patterns (non-actionable)
    # These are posted at the PR level (path=None, line=None) and contain
    # overview information. The actual actionable items are in inline comments.
    PR_SUMMARY_PATTERNS = [
        # "Actionable comments posted: N" pattern
        re.compile(r"Actionable comments posted:\s*\d+", re.IGNORECASE),
        # <details> sections with summaries
        re.compile(r"<details>.*?<summary>.*?</summary>", re.IGNORECASE | re.DOTALL),
        # CodeRabbit auto-generated comment signature
        re.compile(
            r"<!-- This is an auto-generated comment.*?by coderabbit",
            re.IGNORECASE | re.DOTALL,
        ),
    ]

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
            1. PR-level summary comments -> NON_ACTIONABLE
            2. Fingerprinting comments -> NON_ACTIONABLE
            3. Addressed marker -> NON_ACTIONABLE
            4. Critical severity -> ACTIONABLE, CRITICAL
            5. Major severity -> ACTIONABLE, MAJOR
            6. Minor severity -> ACTIONABLE, MINOR
            7. Trivial severity -> NON_ACTIONABLE, TRIVIAL
            8. Nitpick marker -> NON_ACTIONABLE, TRIVIAL
            9. Outside diff range -> ACTIONABLE, MINOR
            10. Summary/walkthrough sections -> NON_ACTIONABLE
            11. Tip/info boxes -> NON_ACTIONABLE
            12. All other -> AMBIGUOUS, UNKNOWN, requires_investigation=True

        Args:
            comment: Dictionary containing comment data with 'body' key,
                and optionally 'path' and 'line' keys for inline comments.

        Returns:
            Tuple of (classification, priority, requires_investigation):
            - classification: CommentClassification enum value
            - priority: Priority enum value
            - requires_investigation: Boolean, True for AMBIGUOUS comments
        """
        # Check for PR-level summary comments first (highest precedence)
        # These are posted at the PR level and contain overview information
        if self._is_pr_summary_comment(comment):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

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

        # Check acknowledgment patterns (thank-you replies)
        if self._is_acknowledgment(body):
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

        # Check for summary/walkthrough sections (non-actionable informational)
        if self._is_summary_content(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Check for tip/info boxes (non-actionable)
        if self._is_tip_content(body):
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Default: AMBIGUOUS - requires investigation
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)

    def _is_summary_content(self, body: str) -> bool:
        """Check if the body is a summary/walkthrough section.

        Summary sections are informational overviews that don't require
        specific action. They include walkthroughs, change summaries,
        and file tables.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be a summary section.
        """
        for pattern in self.SUMMARY_PATTERNS:
            if pattern.search(body):
                return True
        return False

    def _is_tip_content(self, body: str) -> bool:
        """Check if the body is a tip/info box.

        Tip boxes are informational callouts that provide helpful
        context but don't require action.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be a tip/info box.
        """
        for pattern in self.TIP_PATTERNS:
            if pattern.search(body):
                return True
        return False

    def _is_acknowledgment(self, body: str) -> bool:
        """Check if the body is an acknowledgment/thank-you reply.

        Acknowledgment comments are replies from CodeRabbit confirming
        that a fix or suggestion was addressed. These don't require action.

        Args:
            body: Comment body text.

        Returns:
            True if the body appears to be an acknowledgment.
        """
        for pattern in self.ACKNOWLEDGMENT_PATTERNS:
            if pattern.search(body):
                return True
        return False

    def _has_actionable_severity_markers(self, body: str) -> bool:
        """Check if body contains actionable severity markers.

        This is used to prevent filtering PR-level comments that contain
        actual actionable issues with severity markers, even if they also
        contain summary patterns.

        Args:
            body: Comment body text.

        Returns:
            True if the body contains Critical or Major severity markers.
        """
        return bool(self.CRITICAL_PATTERN.search(body) or self.MAJOR_PATTERN.search(body))

    def _is_pr_summary_comment(self, comment: dict) -> bool:
        """Check if this is a PR-level summary comment.

        PR-level summary comments are posted at the PR level (not inline)
        and contain overview information like "Actionable comments posted: N",
        walkthrough sections, or CodeRabbit signatures. These should be
        classified as NON_ACTIONABLE because the actual actionable items
        are in inline comments.

        Key criteria:
        1. Must be a PR-level comment (path=None or missing)
        2. Must match one of the PR summary patterns
        3. Must NOT contain actionable severity markers (Critical/Major)

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

        # Safety check: if the comment contains actionable severity markers,
        # do NOT filter it as a summary - let it be classified by severity
        if self._has_actionable_severity_markers(body):
            return False

        # Check for PR summary patterns
        for pattern in self.PR_SUMMARY_PATTERNS:
            if pattern.search(body):
                return True

        # Also check for summary/walkthrough content at PR level
        if self._is_summary_content(body):
            return True

        return False

    # Pattern to match the "Outside diff range comments" details section
    # Matches: <details>\n<summary>... Outside diff range comments (N)</summary>
    OUTSIDE_DIFF_SECTION_PATTERN = re.compile(
        r"<details>\s*\n\s*<summary>.*?"
        r"Outside diff range comments?\s*\(\d+\)\s*"
        r"</summary>(.*?)</details>",
        re.IGNORECASE | re.DOTALL,
    )

    # Pattern to extract individual file path and line references
    # Matches: **src/config.py:42-45**: or **src/utils.py:100**:
    # Uses [ \t]* instead of \s* to avoid consuming newlines (needed for lookahead)
    OUTSIDE_DIFF_ITEM_PATTERN = re.compile(
        r"\*\*([^:*]+):(\d+(?:-\d+)?)\*\*:[ \t]*(.*?)(?=(?:\n\n\*\*[^:*]+:\d)|$)",
        re.DOTALL,
    )

    def parse_outside_diff_comments(
        self,
        review_body: str,
        review_id: str,
        author: str,
        review_url: str | None = None,
    ) -> list[OutsideDiffComment]:
        """Parse "Outside diff range comments" section from a review body.

        CodeRabbit embeds actionable feedback in review bodies under
        a `<details>` section with summary containing "Outside diff range comments".
        These are NOT individual comment threads and cannot be replied to inline,
        but often contain valuable feedback that should be surfaced.

        Example input:
            <details>
            <summary>... Outside diff range comments (3)</summary>

            **src/config.py:42-45**: Consider adding validation for the config values.

            **src/utils.py:100**: This function could use memoization for performance.

            </details>

        Args:
            review_body: The full body text of a review.
            review_id: The ID of the review (for reference).
            author: The author of the review (e.g., "coderabbitai[bot]").
            review_url: Optional URL to the review on GitHub.

        Returns:
            List of OutsideDiffComment objects extracted from the review body.
            Returns empty list if no "Outside diff range comments" section is found.
        """
        if not review_body:
            return []

        results: list[OutsideDiffComment] = []

        # Find the outside diff section
        section_match = self.OUTSIDE_DIFF_SECTION_PATTERN.search(review_body)
        if not section_match:
            return []

        section_content = section_match.group(1)

        # Extract individual items from the section
        for item_match in self.OUTSIDE_DIFF_ITEM_PATTERN.finditer(section_content):
            file_path = item_match.group(1).strip()
            line_range = item_match.group(2).strip()
            body = item_match.group(3).strip()

            # Clean up the body - remove trailing whitespace and empty lines
            body = body.strip()

            if file_path and body:
                results.append(
                    OutsideDiffComment(
                        source=author,
                        review_id=review_id,
                        file_path=file_path,
                        line_range=line_range if line_range else None,
                        body=body,
                        review_url=review_url,
                    )
                )

        return results
