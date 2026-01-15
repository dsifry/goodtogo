"""PR Analyzer - main orchestrator for GoodToMerge.

This module contains the PRAnalyzer class, which orchestrates the analysis
of pull requests to determine their readiness for merge. It coordinates
between GitHub API access, caching, and comment parsing to produce a
comprehensive analysis result.

The analyzer follows the decision tree from the design specification:
1. CI checks pending/failing -> CI_FAILING
2. Unresolved threads exist -> UNRESOLVED_THREADS
3. Actionable comments exist -> ACTION_REQUIRED
4. Ambiguous comments exist -> ACTION_REQUIRED (with requires_investigation)
5. All clear -> READY
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from goodtogo.core.errors import redact_error
from goodtogo.core.models import (
    CICheck,
    CIStatus,
    Comment,
    CommentClassification,
    PRAnalysisResult,
    Priority,
    PRStatus,
    ReviewerType,
    ThreadSummary,
)
from goodtogo.core.validation import (
    build_cache_key,
    validate_github_identifier,
    validate_pr_number,
)

if TYPE_CHECKING:
    from goodtogo.container import Container


# Cache TTL values in seconds
CACHE_TTL_META = 300  # 5 minutes for PR metadata
CACHE_TTL_CI_PENDING = 300  # 5 minutes while CI pending
CACHE_TTL_CI_COMPLETE = 86400  # 24 hours after CI complete
CACHE_TTL_COMMENT = 86400  # 24 hours for immutable comments


class PRAnalyzer:
    """Main orchestrator for PR analysis.

    PRAnalyzer coordinates the analysis of pull requests by:
    1. Validating inputs
    2. Fetching PR data from GitHub (with caching)
    3. Identifying reviewer types for each comment
    4. Classifying comments using appropriate parsers
    5. Determining overall PR status

    The analyzer uses dependency injection for all external dependencies
    (GitHub API, cache, parsers) to enable testing and flexibility.

    Example:
        >>> from goodtogo.container import Container
        >>> container = Container.create_default(github_token="ghp_...")
        >>> analyzer = PRAnalyzer(container)
        >>> result = analyzer.analyze("myorg", "myrepo", 123)
        >>> print(result.status)
        PRStatus.READY
    """

    def __init__(self, container: Container) -> None:
        """Initialize the PRAnalyzer with a DI container.

        Args:
            container: Dependency injection container providing:
                - github: GitHubPort implementation for API access
                - cache: CachePort implementation for caching
                - parsers: Dict mapping ReviewerType to ReviewerParser
        """
        self._container = container

    def analyze(self, owner: str, repo: str, pr_number: int) -> PRAnalysisResult:
        """Analyze a PR and determine its readiness for merge.

        This method orchestrates the complete PR analysis workflow:
        1. Validate inputs (owner, repo, pr_number)
        2. Fetch PR metadata (with cache)
        3. Check for new commits (invalidate cache if needed)
        4. Fetch comments, reviews, threads, CI status
        5. Identify reviewer type for each comment
        6. Parse and classify all comments
        7. Build actionable and ambiguous comment lists
        8. Generate human-readable action items
        9. Determine final PR status

        Args:
            owner: Repository owner (organization or username).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            PRAnalysisResult containing complete analysis with:
            - status: Final PR status (READY, ACTION_REQUIRED, etc.)
            - ci_status: CI/CD check results
            - threads: Thread resolution summary
            - comments: All classified comments
            - actionable_comments: Comments requiring action
            - ambiguous_comments: Comments needing investigation
            - action_items: Human-readable action list
            - needs_action: Boolean indicating if action is required

        Raises:
            ValueError: If inputs fail validation.
            RedactedError: If an error occurs during analysis (with
                sensitive data redacted from the message).
        """
        try:
            # Step 1: Validate inputs
            owner = validate_github_identifier(owner, "owner")
            repo = validate_github_identifier(repo, "repo")
            pr_number = validate_pr_number(pr_number)

            # Step 2: Fetch PR metadata (with cache)
            pr_data = self._get_pr_data(owner, repo, pr_number)

            # Extract commit info
            head_sha = pr_data.get("head", {}).get("sha", "")
            head_timestamp = pr_data.get("head", {}).get("committed_at", "")
            if not head_timestamp:
                # Fallback to updated_at if committed_at not available
                head_timestamp = pr_data.get("updated_at", "")

            # Step 3: Check for new commits and invalidate cache if needed
            self._check_and_invalidate_cache(owner, repo, pr_number, head_sha)

            # Step 4: Fetch PR data (comments, reviews, threads, CI)
            comments_data = self._get_comments(owner, repo, pr_number)
            reviews_data = self._get_reviews(owner, repo, pr_number)
            threads_data = self._get_threads(owner, repo, pr_number)
            ci_data = self._get_ci_status(owner, repo, head_sha)

            # Step 5-6: Process comments with reviewer identification and parsing
            all_comments = self._process_comments(comments_data, reviews_data, threads_data)

            # Step 7: Build filtered lists
            actionable_comments = [
                c for c in all_comments if c.classification == CommentClassification.ACTIONABLE
            ]
            ambiguous_comments = [
                c for c in all_comments if c.classification == CommentClassification.AMBIGUOUS
            ]

            # Sort actionable comments by priority
            priority_order = {
                Priority.CRITICAL: 0,
                Priority.MAJOR: 1,
                Priority.MINOR: 2,
                Priority.TRIVIAL: 3,
                Priority.UNKNOWN: 4,
            }
            actionable_comments.sort(key=lambda c: priority_order[c.priority])

            # Step 8: Generate action items
            action_items = self._generate_action_items(
                actionable_comments, ambiguous_comments, threads_data, ci_data
            )

            # Build CI status model
            ci_status = self._build_ci_status(ci_data)

            # Build thread summary
            threads = self._build_thread_summary(threads_data)

            # Step 9: Determine final status using decision tree
            status = self._determine_status(
                ci_status, threads, actionable_comments, ambiguous_comments
            )

            # Get cache stats
            cache_stats = self._container.cache.get_stats()

            # Determine if action is needed
            needs_action = status != PRStatus.READY

            return PRAnalysisResult(
                status=status,
                pr_number=pr_number,
                repo_owner=owner,
                repo_name=repo,
                latest_commit_sha=head_sha,
                latest_commit_timestamp=head_timestamp,
                ci_status=ci_status,
                threads=threads,
                comments=all_comments,
                actionable_comments=actionable_comments,
                ambiguous_comments=ambiguous_comments,
                action_items=action_items,
                needs_action=needs_action,
                cache_stats=cache_stats,
            )

        except ValueError:
            # Validation errors don't need redaction, re-raise as-is
            raise
        except Exception as e:
            # Wrap all other exceptions with redacted messages
            raise redact_error(e) from e

    def _get_pr_data(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata with caching.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.

        Returns:
            Dictionary containing PR metadata.
        """
        cache_key = build_cache_key("pr", owner, repo, str(pr_number), "meta")

        # Try cache first
        cached = self._container.cache.get(cache_key)
        if cached:
            return cast(dict[str, Any], json.loads(cached))

        # Fetch from GitHub
        pr_data = self._container.github.get_pr(owner, repo, pr_number)

        # Cache the result
        self._container.cache.set(cache_key, json.dumps(pr_data), CACHE_TTL_META)

        return pr_data

    def _check_and_invalidate_cache(
        self, owner: str, repo: str, pr_number: int, current_sha: str
    ) -> None:
        """Check for new commits and invalidate cache if needed.

        If the latest commit SHA has changed since the last analysis,
        invalidate all cached data for this PR.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.
            current_sha: Current head commit SHA.
        """
        cache_key = build_cache_key("pr", owner, repo, str(pr_number), "commit", "latest")

        cached_sha = self._container.cache.get(cache_key)
        if cached_sha and cached_sha != current_sha:
            # New commit detected, invalidate all cached data for this PR
            pattern = f"pr:{owner}:{repo}:{pr_number}:*"
            self._container.cache.invalidate_pattern(pattern)

        # Store current SHA
        self._container.cache.set(cache_key, current_sha, CACHE_TTL_META)

    def _get_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch PR comments with caching.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.

        Returns:
            List of comment dictionaries.
        """
        cache_key = build_cache_key("pr", owner, repo, str(pr_number), "comments")

        cached = self._container.cache.get(cache_key)
        if cached:
            return cast(list[dict[str, Any]], json.loads(cached))

        comments = self._container.github.get_pr_comments(owner, repo, pr_number)
        self._container.cache.set(cache_key, json.dumps(comments), CACHE_TTL_META)

        return comments

    def _get_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch PR reviews with caching.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.

        Returns:
            List of review dictionaries.
        """
        cache_key = build_cache_key("pr", owner, repo, str(pr_number), "reviews")

        cached = self._container.cache.get(cache_key)
        if cached:
            return cast(list[dict[str, Any]], json.loads(cached))

        reviews = self._container.github.get_pr_reviews(owner, repo, pr_number)
        self._container.cache.set(cache_key, json.dumps(reviews), CACHE_TTL_META)

        return reviews

    def _get_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch PR threads with caching.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.

        Returns:
            List of thread dictionaries.
        """
        cache_key = build_cache_key("pr", owner, repo, str(pr_number), "threads")

        cached = self._container.cache.get(cache_key)
        if cached:
            return cast(list[dict[str, Any]], json.loads(cached))

        threads = self._container.github.get_pr_threads(owner, repo, pr_number)
        self._container.cache.set(cache_key, json.dumps(threads), CACHE_TTL_META)

        return threads

    def _get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Fetch CI status with caching.

        Uses different TTL based on whether CI is complete or still pending.

        Args:
            owner: Repository owner.
            repo: Repository name.
            ref: Git reference (commit SHA).

        Returns:
            Dictionary containing CI status.
        """
        cache_key = build_cache_key("pr", owner, repo, ref, "ci", "status")

        cached = self._container.cache.get(cache_key)
        if cached:
            return cast(dict[str, Any], json.loads(cached))

        ci_data = self._container.github.get_ci_status(owner, repo, ref)

        # Use longer TTL if CI is complete
        state = ci_data.get("state", "pending")
        ttl = CACHE_TTL_CI_COMPLETE if state in ("success", "failure") else CACHE_TTL_CI_PENDING

        self._container.cache.set(cache_key, json.dumps(ci_data), ttl)

        return ci_data

    def _identify_reviewer_type(self, author: str, body: str) -> ReviewerType:
        """Identify the reviewer type for a comment.

        Iterates through parsers in priority order to find one that
        can handle the comment.

        Args:
            author: Comment author username.
            body: Comment body text.

        Returns:
            ReviewerType for the identified reviewer.
        """
        # Check parsers in order (CODERABBIT, GREPTILE, CLAUDE, CURSOR, then fallback)
        parser_order = [
            ReviewerType.CODERABBIT,
            ReviewerType.GREPTILE,
            ReviewerType.CLAUDE,
            ReviewerType.CURSOR,
        ]

        for reviewer_type in parser_order:
            if reviewer_type in self._container.parsers:
                parser = self._container.parsers[reviewer_type]
                if parser.can_parse(author, body):
                    return reviewer_type

        # Fallback to HUMAN/UNKNOWN
        return ReviewerType.HUMAN

    def _process_comments(
        self,
        comments_data: list[dict[str, Any]],
        reviews_data: list[dict[str, Any]],
        threads_data: list[dict[str, Any]],
    ) -> list[Comment]:
        """Process all comments and classify them.

        Combines comments from inline comments, reviews, and threads,
        identifies the reviewer type, and classifies each comment.

        Args:
            comments_data: List of inline comments from GitHub.
            reviews_data: List of reviews from GitHub.
            threads_data: List of threads from GitHub.

        Returns:
            List of Comment objects with classifications.
        """
        all_comments: list[Comment] = []

        # Build thread resolution map
        thread_resolution = {}
        thread_outdated = {}
        for thread in threads_data:
            thread_id = thread.get("id", "")
            thread_resolution[thread_id] = thread.get("is_resolved", False)
            thread_outdated[thread_id] = thread.get("is_outdated", False)

        # Process inline comments
        for comment_data in comments_data:
            comment = self._classify_comment(comment_data, thread_resolution, thread_outdated)
            all_comments.append(comment)

        # Process review body comments
        for review_data in reviews_data:
            # Skip reviews with empty bodies
            body = review_data.get("body", "")
            if not body or not body.strip():
                continue

            # Create a comment-like dict from review
            review_comment = {
                "id": f"review_{review_data.get('id', '')}",
                "user": review_data.get("user", {}),
                "body": body,
                "created_at": review_data.get("submitted_at", ""),
                "path": None,
                "line": None,
            }
            comment = self._classify_comment(review_comment, thread_resolution, thread_outdated)
            all_comments.append(comment)

        return all_comments

    def _classify_comment(
        self,
        comment_data: dict[str, Any],
        thread_resolution: dict[str, bool],
        thread_outdated: dict[str, bool],
    ) -> Comment:
        """Classify a single comment using the appropriate parser.

        Args:
            comment_data: Dictionary containing comment data.
            thread_resolution: Map of thread ID to resolution status.
            thread_outdated: Map of thread ID to outdated status.

        Returns:
            Classified Comment object.
        """
        author = comment_data.get("user", {}).get("login", "")
        body = comment_data.get("body", "")
        comment_id = str(comment_data.get("id", ""))
        thread_id = comment_data.get("in_reply_to_id")
        if thread_id:
            thread_id = str(thread_id)

        # Determine thread status
        is_resolved = thread_resolution.get(thread_id, False) if thread_id else False
        is_outdated = thread_outdated.get(thread_id, False) if thread_id else False

        # Identify reviewer type
        reviewer_type = self._identify_reviewer_type(author, body)

        # Get the appropriate parser (fallback to HUMAN parser if not found)
        parser = self._container.parsers.get(reviewer_type)
        if parser is None:
            parser = self._container.parsers.get(ReviewerType.HUMAN)
        if parser is None:
            # Last resort fallback - use the first available parser
            parser = next(iter(self._container.parsers.values()))

        # Add resolution status to comment data for parser use
        comment_with_status = {
            **comment_data,
            "is_resolved": is_resolved,
            "is_outdated": is_outdated,
        }

        # Parse the comment
        classification, priority, requires_investigation = parser.parse(comment_with_status)

        return Comment(
            id=comment_id,
            author=author,
            reviewer_type=reviewer_type,
            body=body,
            classification=classification,
            priority=priority,
            requires_investigation=requires_investigation,
            thread_id=thread_id,
            is_resolved=is_resolved,
            is_outdated=is_outdated,
            file_path=comment_data.get("path"),
            line_number=comment_data.get("line"),
            created_at=comment_data.get("created_at", ""),
            addressed_in_commit=None,
        )

    def _build_ci_status(self, ci_data: dict[str, Any]) -> CIStatus:
        """Build CIStatus model from GitHub API response.

        Args:
            ci_data: Dictionary from GitHub CI status API.

        Returns:
            CIStatus model with aggregated check information.
        """
        state = ci_data.get("state", "pending")
        statuses = ci_data.get("statuses", [])
        check_runs = ci_data.get("check_runs", [])

        checks: list[CICheck] = []

        # Process status checks
        for status in statuses:
            checks.append(
                CICheck(
                    name=status.get("context", "unknown"),
                    status=status.get("state", "pending"),
                    conclusion=status.get("state"),
                    url=status.get("target_url"),
                )
            )

        # Process check runs (GitHub Actions, etc.)
        for run in check_runs:
            run_status = run.get("status", "queued")
            run_conclusion = run.get("conclusion")

            # Map GitHub status to our status
            if run_status == "completed":
                status_value = run_conclusion or "unknown"
            elif run_status in ("queued", "in_progress"):
                status_value = "pending"
            else:
                status_value = run_status

            checks.append(
                CICheck(
                    name=run.get("name", "unknown"),
                    status=status_value,
                    conclusion=run_conclusion,
                    url=run.get("html_url"),
                )
            )

        # Calculate counts
        total = len(checks)
        passed = sum(1 for c in checks if c.status == "success")
        failed = sum(1 for c in checks if c.status in ("failure", "error"))
        pending = sum(1 for c in checks if c.status == "pending")

        return CIStatus(
            state=state,
            total_checks=total,
            passed=passed,
            failed=failed,
            pending=pending,
            checks=checks,
        )

    def _build_thread_summary(self, threads_data: list[dict[str, Any]]) -> ThreadSummary:
        """Build ThreadSummary from thread data.

        Args:
            threads_data: List of thread dictionaries.

        Returns:
            ThreadSummary with resolution counts.
        """
        total = len(threads_data)
        resolved = sum(1 for t in threads_data if t.get("is_resolved", False))
        outdated = sum(1 for t in threads_data if t.get("is_outdated", False))
        unresolved = total - resolved

        return ThreadSummary(
            total=total,
            resolved=resolved,
            unresolved=unresolved,
            outdated=outdated,
        )

    def _generate_action_items(
        self,
        actionable_comments: list[Comment],
        ambiguous_comments: list[Comment],
        threads_data: list[dict[str, Any]],
        ci_data: dict[str, Any],
    ) -> list[str]:
        """Generate human-readable action items.

        Args:
            actionable_comments: List of actionable comments.
            ambiguous_comments: List of ambiguous comments.
            threads_data: List of thread data.
            ci_data: CI status data.

        Returns:
            List of human-readable action item strings.
        """
        action_items: list[str] = []

        # CI status items
        state = ci_data.get("state", "pending")
        if state == "pending":
            action_items.append("CI checks are still running - wait for completion")
        elif state == "failure":
            action_items.append("CI checks are failing - fix build/test errors")

        # Thread items
        unresolved = sum(1 for t in threads_data if not t.get("is_resolved", False))
        if unresolved > 0:
            action_items.append(
                f"{unresolved} unresolved review thread{'s' if unresolved != 1 else ''}"
            )

        # Actionable comment items
        if actionable_comments:
            # Group by priority
            critical = sum(1 for c in actionable_comments if c.priority == Priority.CRITICAL)
            major = sum(1 for c in actionable_comments if c.priority == Priority.MAJOR)
            minor = sum(1 for c in actionable_comments if c.priority == Priority.MINOR)
            other = len(actionable_comments) - critical - major - minor

            if critical > 0:
                issues = "issue" if critical == 1 else "issues"
                needs = "needs" if critical == 1 else "need"
                action_items.append(f"{critical} critical {issues} {needs} immediate attention")
            if major > 0:
                issues = "issue" if major == 1 else "issues"
                action_items.append(f"{major} major {issues} must be fixed before merge")
            if minor > 0:
                issues = "issue" if minor == 1 else "issues"
                action_items.append(f"{minor} minor {issues} should be addressed")
            if other > 0:
                comments = "comment" if other == 1 else "comments"
                needs = "needs" if other == 1 else "need"
                action_items.append(f"{other} actionable {comments} {needs} addressing")

        # Ambiguous comment items
        if ambiguous_comments:
            action_items.append(
                f"{len(ambiguous_comments)} comment{'s' if len(ambiguous_comments) != 1 else ''} "
                f"require{'s' if len(ambiguous_comments) == 1 else ''} investigation (ambiguous)"
            )

        return action_items

    def _determine_status(
        self,
        ci_status: CIStatus,
        threads: ThreadSummary,
        actionable_comments: list[Comment],
        ambiguous_comments: list[Comment],
    ) -> PRStatus:
        """Determine final PR status using the decision tree.

        Decision tree (in order):
        1. CI pending/failing -> CI_FAILING
        2. Unresolved threads -> UNRESOLVED_THREADS
        3. Actionable/ambiguous comments -> ACTION_REQUIRED
        4. All clear -> READY

        Args:
            ci_status: CI check status.
            threads: Thread summary.
            actionable_comments: List of actionable comments.
            ambiguous_comments: List of ambiguous comments.

        Returns:
            Final PRStatus enum value.
        """
        # Check CI status first
        if ci_status.state in ("pending", "failure", "error"):
            return PRStatus.CI_FAILING

        # Check for unresolved threads
        if threads.unresolved > 0:
            return PRStatus.UNRESOLVED_THREADS

        # Check for actionable or ambiguous comments
        if actionable_comments or ambiguous_comments:
            return PRStatus.ACTION_REQUIRED

        # All clear!
        return PRStatus.READY
