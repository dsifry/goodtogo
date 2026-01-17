"""GitHub API adapter implementing the GitHubPort interface.

This module provides a concrete implementation of the GitHubPort interface
using httpx for HTTP requests to the GitHub REST API. It handles authentication,
rate limiting, and error handling.

Security features:
- Token stored in private `_token` attribute
- Token never appears in __repr__, __str__, or error messages
- All errors are redacted before propagation
"""

from __future__ import annotations

from typing import Any, Optional, cast

import httpx

from goodtogo.adapters.time_provider import SystemTimeProvider
from goodtogo.core.interfaces import GitHubPort, TimeProvider


class GitHubRateLimitError(Exception):
    """Raised when GitHub API rate limit is exceeded.

    Attributes:
        reset_at: Unix timestamp when the rate limit resets.
        retry_after: Seconds until the rate limit resets.
    """

    def __init__(self, message: str, reset_at: int, retry_after: int) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error description.
            reset_at: Unix timestamp when rate limit resets.
            retry_after: Seconds until rate limit resets.
        """
        super().__init__(message)
        self.reset_at = reset_at
        self.retry_after = retry_after


class GitHubAPIError(Exception):
    """Raised when a GitHub API request fails.

    Attributes:
        status_code: HTTP status code from the response.
        message: Error description (with sensitive data redacted).
    """

    def __init__(self, message: str, status_code: int) -> None:
        """Initialize the API error.

        Args:
            message: Error description.
            status_code: HTTP status code.
        """
        super().__init__(message)
        self.status_code = status_code


class GitHubAdapter(GitHubPort):
    """GitHub API adapter with secure token handling.

    This adapter implements the GitHubPort interface using httpx to make
    HTTP requests to the GitHub REST API and GraphQL API.

    The authentication token is stored in a private attribute and is never
    exposed through string representations or error messages.

    Attributes:
        BASE_URL: GitHub REST API base URL.
        GRAPHQL_URL: GitHub GraphQL API URL.

    Example:
        >>> adapter = GitHubAdapter(token="ghp_...")
        >>> pr = adapter.get_pr("owner", "repo", 123)
        >>> print(pr["title"])
    """

    BASE_URL = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, time_provider: Optional[TimeProvider] = None) -> None:
        """Initialize the GitHub adapter.

        Args:
            token: GitHub personal access token or OAuth token.
                   Must have 'repo' scope for private repositories.
            time_provider: Optional TimeProvider for time operations.
                           Defaults to SystemTimeProvider if not provided.
        """
        # Token stored in private attribute - never log, cache, or serialize
        self._token = token
        self._time_provider = time_provider or SystemTimeProvider()
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    def __repr__(self) -> str:
        """Return string representation with redacted token.

        Returns:
            String with token redacted for safe logging.
        """
        return "GitHubAdapter(token=<redacted>)"

    def __str__(self) -> str:
        """Return string representation with redacted token.

        Returns:
            String with token redacted for safe logging.
        """
        return self.__repr__()

    def __del__(self) -> None:
        """Clean up the HTTP client on deletion."""
        if hasattr(self, "_client"):
            self._client.close()

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response, checking for errors and rate limits.

        Args:
            response: The httpx response object.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails for other reasons.
        """
        # Check for rate limiting
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            if remaining == "0":
                reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
                retry_after = max(0, reset_at - self._time_provider.now_int())
                raise GitHubRateLimitError(
                    f"GitHub API rate limit exceeded. Resets in {retry_after} seconds.",
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

        # Check for secondary rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            reset_at = self._time_provider.now_int() + retry_after
            raise GitHubRateLimitError(
                f"GitHub API secondary rate limit. Retry after {retry_after} seconds.",
                reset_at=reset_at,
                retry_after=retry_after,
            )

        # Handle other errors
        if response.status_code >= 400:
            # Do not include response body in error - may contain sensitive data
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}",
                status_code=response.status_code,
            )

        return cast(dict[str, Any], response.json())

    def _handle_list_response(self, response: httpx.Response) -> list[dict[str, Any]]:
        """Handle HTTP response that returns a list.

        Args:
            response: The httpx response object.

        Returns:
            Parsed JSON response as a list.

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        # Reuse error handling logic (will raise on errors)
        self._handle_response(response)

        # The above will raise on errors, so we can safely parse
        return cast(list[dict[str, Any]], response.json())

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata.

        Retrieves basic PR information including title, state, head SHA,
        base branch, and timestamps.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Dictionary containing PR metadata with keys like:
            - 'number': PR number
            - 'title': PR title
            - 'state': PR state ('open', 'closed', 'merged')
            - 'head': Dictionary with 'sha' key for latest commit
            - 'base': Dictionary with 'ref' key for base branch
            - 'created_at': ISO timestamp
            - 'updated_at': ISO timestamp

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails or PR is not found.
        """
        response = self._client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        return self._handle_response(response)

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all PR comments (inline + review + issue).

        Retrieves all types of comments associated with a PR:
        - Review comments (inline on specific code lines)
        - Issue comments (on the PR itself)

        Note: Review body comments are retrieved via get_pr_reviews().

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Unique comment identifier
            - 'user': Dictionary with 'login' key for author
            - 'body': Comment text content
            - 'created_at': ISO timestamp
            - 'path': File path (for inline comments, None otherwise)
            - 'line': Line number (for inline comments, None otherwise)
            - 'in_reply_to_id': Parent comment ID if reply (None otherwise)

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        # Fetch review comments (inline code comments)
        review_comments = self._fetch_paginated(f"/repos/{owner}/{repo}/pulls/{pr_number}/comments")

        # Fetch issue comments (PR-level comments)
        issue_comments = self._fetch_paginated(f"/repos/{owner}/{repo}/issues/{pr_number}/comments")

        # Combine and return all comments
        return review_comments + issue_comments

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all PR reviews.

        Retrieves all reviews submitted on a PR, including approvals,
        change requests, and comment-only reviews.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Unique review identifier
            - 'user': Dictionary with 'login' key for reviewer
            - 'body': Review body text (may be empty)
            - 'state': Review state ('APPROVED', 'CHANGES_REQUESTED',
                      'COMMENTED', 'DISMISSED', 'PENDING')
            - 'submitted_at': ISO timestamp

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        return self._fetch_paginated(f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews")

    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all review threads with resolution status.

        Uses GitHub's GraphQL API to retrieve review threads with their
        resolution status, which is not available in the REST API.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of dictionaries, each containing:
            - 'id': Thread node ID
            - 'is_resolved': Boolean indicating if thread is resolved
            - 'is_outdated': Boolean indicating if thread is outdated
            - 'path': File path the thread is attached to
            - 'line': Line number in the diff
            - 'comments': List of comments in the thread

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        query = """
        query($owner: String!, $repo: String!, $pr_number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $pr_number) {
              reviewThreads(first: 100) {
                nodes {
                  id
                  isResolved
                  isOutdated
                  path
                  line
                  comments(first: 100) {
                    nodes {
                      id
                      body
                      author {
                        login
                      }
                      createdAt
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {"owner": owner, "repo": repo, "pr_number": pr_number}

        response = self._client.post(
            self.GRAPHQL_URL,
            json={"query": query, "variables": variables},
        )

        data = self._handle_response(response)

        # Check for GraphQL errors
        if "errors" in data:
            error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
            raise GitHubAPIError(
                f"GraphQL query failed: {'; '.join(error_messages)}",
                status_code=200,
            )

        # Extract threads from response
        threads_data = (
            data.get("data", {})
            .get("repository", {})
            .get("pullRequest", {})
            .get("reviewThreads", {})
            .get("nodes", [])
        )

        # Transform to consistent format
        threads: list[dict[str, Any]] = []
        for thread in threads_data:
            comments_nodes = thread.get("comments", {}).get("nodes", [])
            threads.append(
                {
                    "id": thread.get("id"),
                    "is_resolved": thread.get("isResolved", False),
                    "is_outdated": thread.get("isOutdated", False),
                    "path": thread.get("path"),
                    "line": thread.get("line"),
                    "comments": [
                        {
                            "id": c.get("id"),
                            "body": c.get("body", ""),
                            "author": c.get("author", {}).get("login", "unknown"),
                            "created_at": c.get("createdAt"),
                        }
                        for c in comments_nodes
                    ],
                }
            )

        return threads

    def get_commit(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Fetch commit details including timestamp.

        Retrieves detailed information about a specific commit, including
        the commit timestamp which is needed to compare against review
        submission times.

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            ref: Git reference (commit SHA, branch name, or tag).

        Returns:
            Dictionary containing:
            - 'sha': Commit SHA
            - 'commit': Dictionary with 'author' and 'committer' info
              including 'date' timestamp
            - 'author': GitHub user who authored the commit
            - 'committer': GitHub user who committed

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        response = self._client.get(f"/repos/{owner}/{repo}/commits/{ref}")
        return self._handle_response(response)

    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Fetch CI/CD check status for a commit.

        Retrieves the combined status of all CI checks for a specific
        commit reference. This includes both commit statuses (legacy)
        and check runs (GitHub Actions, third-party CI).

        Args:
            owner: Repository owner (organization or user name).
            repo: Repository name.
            ref: Git reference (commit SHA, branch name, or tag).

        Returns:
            Dictionary containing:
            - 'state': Overall state ('success', 'failure', 'pending')
            - 'total_count': Total number of checks
            - 'statuses': List of individual status checks
            - 'check_runs': List of check runs (GitHub Actions, etc.)

            Each status/check_run contains:
            - 'name': Check name
            - 'state' or 'status': Individual check state
            - 'conclusion': Final conclusion (for completed checks)
            - 'target_url' or 'html_url': Link to check details

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If the request fails.
        """
        # Fetch combined commit status (legacy status API)
        status_response = self._client.get(f"/repos/{owner}/{repo}/commits/{ref}/status")
        status_data = self._handle_response(status_response)

        # Fetch check runs (GitHub Actions, etc.)
        check_runs_response = self._client.get(f"/repos/{owner}/{repo}/commits/{ref}/check-runs")
        check_runs_data = self._handle_response(check_runs_response)

        # Combine results
        statuses = status_data.get("statuses", [])
        check_runs = check_runs_data.get("check_runs", [])

        # Calculate overall state
        all_states: list[str] = []

        # Add legacy status states
        for status in statuses:
            all_states.append(status.get("state", "pending"))

        # Add check run conclusions
        for check_run in check_runs:
            status_val = check_run.get("status", "queued")
            if status_val == "completed":
                conclusion = check_run.get("conclusion", "neutral")
                if conclusion == "success":
                    all_states.append("success")
                elif conclusion in ("failure", "cancelled", "timed_out"):
                    all_states.append("failure")
                else:
                    all_states.append("pending")
            else:
                all_states.append("pending")

        # Determine overall state
        if not all_states:
            overall_state = "success"  # No checks means success
        elif "failure" in all_states:
            overall_state = "failure"
        elif "pending" in all_states:
            overall_state = "pending"
        else:
            overall_state = "success"

        return {
            "state": overall_state,
            "total_count": len(statuses) + len(check_runs),
            "statuses": statuses,
            "check_runs": check_runs,
        }

    def _fetch_paginated(self, endpoint: str) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated endpoint.

        GitHub API paginates results. This method handles pagination
        by following 'next' links in the Link header.

        Args:
            endpoint: API endpoint path (e.g., '/repos/owner/repo/pulls').

        Returns:
            Combined list of all items from all pages.

        Raises:
            GitHubRateLimitError: If rate limit is exceeded.
            GitHubAPIError: If any request fails.
        """
        results: list[dict[str, Any]] = []
        url: Optional[str] = endpoint
        params: dict[str, str] = {"per_page": "100"}

        while url is not None:
            response = self._client.get(url, params=params if "?" not in url else None)

            # Handle response (will raise on errors)
            if response.status_code >= 400:
                self._handle_response(response)

            page_results = cast(list[dict[str, Any]], response.json())
            results.extend(page_results)

            # Check for next page in Link header
            url = self._get_next_page_url(response)
            params = {}  # Clear params for subsequent requests (URL has them)

        return results

    def _get_next_page_url(self, response: httpx.Response) -> Optional[str]:
        """Extract next page URL from Link header.

        Args:
            response: HTTP response with potential Link header.

        Returns:
            URL for next page, or None if no more pages.
        """
        link_header = response.headers.get("Link", "")
        if not link_header:
            return None

        # Parse Link header: <url>; rel="next", <url>; rel="prev"
        for part in link_header.split(","):
            if 'rel="next"' in part:
                # Extract URL from <url>
                url_part: str = part.split(";")[0].strip()
                if url_part.startswith("<") and url_part.endswith(">"):
                    next_url: str = url_part[1:-1]
                    return next_url

        return None
