"""Shared pytest fixtures for GoodToMerge tests.

This module provides common fixtures used across integration and unit tests,
including mock data factories, container setup, and GitHub response fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from goodtomerge.container import Container
from goodtomerge.core.interfaces import GitHubPort


# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def load_fixture():
    """Factory fixture for loading JSON fixture files.

    Returns:
        A callable that loads a JSON fixture file by path relative to fixtures dir.
    """

    def _load(relative_path: str) -> dict[str, Any]:
        fixture_path = FIXTURES_DIR / relative_path
        with open(fixture_path) as f:
            return json.load(f)

    return _load


# ============================================================================
# Mock GitHub Adapter Factory
# ============================================================================


class MockableGitHubAdapter(GitHubPort):
    """GitHub adapter with mockable methods for testing.

    This adapter stores return values for each method and returns them
    when called. Useful for integration tests where you want to control
    the exact responses.
    """

    def __init__(self) -> None:
        """Initialize with default empty responses."""
        self._pr_data: dict[str, Any] = {}
        self._comments: list[dict[str, Any]] = []
        self._reviews: list[dict[str, Any]] = []
        self._threads: list[dict[str, Any]] = []
        self._ci_status: dict[str, Any] = {}

    def set_pr_data(self, data: dict[str, Any]) -> None:
        """Set the PR data to return from get_pr."""
        self._pr_data = data

    def set_comments(self, comments: list[dict[str, Any]]) -> None:
        """Set the comments to return from get_pr_comments."""
        self._comments = comments

    def set_reviews(self, reviews: list[dict[str, Any]]) -> None:
        """Set the reviews to return from get_pr_reviews."""
        self._reviews = reviews

    def set_threads(self, threads: list[dict[str, Any]]) -> None:
        """Set the threads to return from get_pr_threads."""
        self._threads = threads

    def set_ci_status(self, status: dict[str, Any]) -> None:
        """Set the CI status to return from get_ci_status."""
        self._ci_status = status

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Return configured PR data."""
        return self._pr_data

    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return configured comments."""
        return self._comments

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return configured reviews."""
        return self._reviews

    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Return configured threads."""
        return self._threads

    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        """Return configured CI status."""
        return self._ci_status


@pytest.fixture
def mock_github() -> MockableGitHubAdapter:
    """Create a mockable GitHub adapter for testing.

    Returns:
        A MockableGitHubAdapter instance with empty default responses.
    """
    return MockableGitHubAdapter()


@pytest.fixture
def test_container(mock_github: MockableGitHubAdapter) -> Container:
    """Create a test container with mock GitHub adapter.

    Uses Container.create_for_testing() with the mock GitHub adapter,
    providing full isolation from real GitHub API.

    Returns:
        A Container configured for testing with mocked GitHub.
    """
    return Container.create_for_testing(github=mock_github)


# ============================================================================
# Common Mock Data Factories
# ============================================================================


@pytest.fixture
def make_pr_data():
    """Factory for creating PR data dictionaries.

    Returns:
        A callable that creates PR data with sensible defaults.
    """

    def _make(
        number: int = 123,
        title: str = "Test PR",
        head_sha: str = "abc123def456",
        updated_at: str = "2024-01-15T10:00:00Z",
        state: str = "open",
    ) -> dict[str, Any]:
        return {
            "number": number,
            "title": title,
            "state": state,
            "head": {
                "sha": head_sha,
                "ref": "feature-branch",
                "committed_at": updated_at,
            },
            "base": {
                "ref": "main",
            },
            "updated_at": updated_at,
            "user": {"login": "test-author"},
        }

    return _make


@pytest.fixture
def make_comment():
    """Factory for creating comment data dictionaries.

    Returns:
        A callable that creates comment data with sensible defaults.
    """

    def _make(
        comment_id: int = 1,
        author: str = "reviewer",
        body: str = "Looks good!",
        path: str | None = None,
        line: int | None = None,
        in_reply_to_id: int | None = None,
        created_at: str = "2024-01-15T10:00:00Z",
    ) -> dict[str, Any]:
        return {
            "id": comment_id,
            "user": {"login": author},
            "body": body,
            "path": path,
            "line": line,
            "in_reply_to_id": in_reply_to_id,
            "created_at": created_at,
        }

    return _make


@pytest.fixture
def make_review():
    """Factory for creating review data dictionaries.

    Returns:
        A callable that creates review data with sensible defaults.
    """

    def _make(
        review_id: int = 1,
        author: str = "reviewer",
        body: str = "",
        state: str = "APPROVED",
        submitted_at: str = "2024-01-15T10:00:00Z",
    ) -> dict[str, Any]:
        return {
            "id": review_id,
            "user": {"login": author},
            "body": body,
            "state": state,
            "submitted_at": submitted_at,
        }

    return _make


@pytest.fixture
def make_thread():
    """Factory for creating thread data dictionaries.

    Returns:
        A callable that creates thread data with sensible defaults.
    """

    def _make(
        thread_id: str = "thread-1",
        is_resolved: bool = False,
        is_outdated: bool = False,
        path: str = "src/main.py",
        line: int = 10,
    ) -> dict[str, Any]:
        return {
            "id": thread_id,
            "is_resolved": is_resolved,
            "is_outdated": is_outdated,
            "path": path,
            "line": line,
        }

    return _make


@pytest.fixture
def make_ci_status():
    """Factory for creating CI status data dictionaries.

    Returns:
        A callable that creates CI status data with sensible defaults.
    """

    def _make(
        state: str = "success",
        statuses: list[dict[str, Any]] | None = None,
        check_runs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "state": state,
            "statuses": statuses or [],
            "check_runs": check_runs or [],
        }

    return _make


@pytest.fixture
def make_check_run():
    """Factory for creating check run data dictionaries.

    Returns:
        A callable that creates check run data with sensible defaults.
    """

    def _make(
        name: str = "build",
        status: str = "completed",
        conclusion: str | None = "success",
        html_url: str = "https://github.com/owner/repo/actions/runs/123",
    ) -> dict[str, Any]:
        return {
            "name": name,
            "status": status,
            "conclusion": conclusion,
            "html_url": html_url,
        }

    return _make


# ============================================================================
# Pre-configured Scenario Fixtures
# ============================================================================


@pytest.fixture
def ready_to_merge_pr(
    mock_github: MockableGitHubAdapter,
    make_pr_data,
    make_ci_status,
    make_check_run,
) -> MockableGitHubAdapter:
    """Configure mock for a PR that is ready to merge.

    Sets up a PR with:
    - Successful CI
    - No comments
    - No threads
    - No reviews with bodies

    Returns:
        The configured mock GitHub adapter.
    """
    mock_github.set_pr_data(make_pr_data(number=123))
    mock_github.set_comments([])
    mock_github.set_reviews([])
    mock_github.set_threads([])
    mock_github.set_ci_status(
        make_ci_status(
            state="success",
            check_runs=[
                make_check_run(name="build", conclusion="success"),
                make_check_run(name="test", conclusion="success"),
                make_check_run(name="lint", conclusion="success"),
            ],
        )
    )
    return mock_github


@pytest.fixture
def pr_with_failing_ci(
    mock_github: MockableGitHubAdapter,
    make_pr_data,
    make_ci_status,
    make_check_run,
) -> MockableGitHubAdapter:
    """Configure mock for a PR with failing CI.

    Sets up a PR with:
    - Failing CI (build failed)
    - No comments or threads

    Returns:
        The configured mock GitHub adapter.
    """
    mock_github.set_pr_data(make_pr_data(number=123))
    mock_github.set_comments([])
    mock_github.set_reviews([])
    mock_github.set_threads([])
    mock_github.set_ci_status(
        make_ci_status(
            state="failure",
            check_runs=[
                make_check_run(name="build", conclusion="failure"),
                make_check_run(name="test", status="queued", conclusion=None),
            ],
        )
    )
    return mock_github


@pytest.fixture
def pr_with_unresolved_threads(
    mock_github: MockableGitHubAdapter,
    make_pr_data,
    make_ci_status,
    make_check_run,
    make_thread,
    make_comment,
) -> MockableGitHubAdapter:
    """Configure mock for a PR with unresolved threads.

    Sets up a PR with:
    - Successful CI
    - One unresolved thread

    Returns:
        The configured mock GitHub adapter.
    """
    mock_github.set_pr_data(make_pr_data(number=123))
    mock_github.set_comments([
        make_comment(
            comment_id=1,
            author="reviewer",
            body="Please fix this",
            in_reply_to_id=None,
        )
    ])
    mock_github.set_reviews([])
    mock_github.set_threads([
        make_thread(thread_id="thread-1", is_resolved=False),
    ])
    mock_github.set_ci_status(
        make_ci_status(
            state="success",
            check_runs=[
                make_check_run(name="build", conclusion="success"),
            ],
        )
    )
    return mock_github


@pytest.fixture
def pr_with_actionable_comments(
    mock_github: MockableGitHubAdapter,
    make_pr_data,
    make_ci_status,
    make_check_run,
    make_comment,
) -> MockableGitHubAdapter:
    """Configure mock for a PR with actionable CodeRabbit comments.

    Sets up a PR with:
    - Successful CI
    - CodeRabbit comment with actionable issue using correct emoji pattern

    CodeRabbit uses specific emoji patterns for severity:
    - _Warning Potential issue_ | _Red Circle Critical_
    - _Warning Potential issue_ | _Orange Circle Major_
    - _Warning Potential issue_ | _Yellow Circle Minor_

    Returns:
        The configured mock GitHub adapter.
    """
    mock_github.set_pr_data(make_pr_data(number=123))
    mock_github.set_comments([
        make_comment(
            comment_id=1,
            author="coderabbitai[bot]",
            body="""_⚠️ Potential issue_ | _🔴 Critical_

Missing null check in handler function.

This could cause a runtime exception if the input is undefined.

<details>
<summary>Suggestion</summary>

```python
if input is None:
    raise ValueError("Input cannot be None")
```
</details>
""",
            path="src/handler.py",
            line=42,
        )
    ])
    mock_github.set_reviews([])
    mock_github.set_threads([])
    mock_github.set_ci_status(
        make_ci_status(
            state="success",
            check_runs=[
                make_check_run(name="build", conclusion="success"),
            ],
        )
    )
    return mock_github
