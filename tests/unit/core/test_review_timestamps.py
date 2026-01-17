"""Tests for review timestamp functionality (Issue #9).

This module tests the new review timestamp features:
- Review model creation
- has_reviews_after_latest_commit detection
- Timestamp comparison logic
- Edge cases for review detection
"""

import json

import pytest

from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import Review


class TestReviewModel:
    """Tests for the Review Pydantic model."""

    @pytest.fixture
    def valid_review_data(self):
        """Provide valid review data for testing."""
        return {
            "id": "review_123",
            "author": "reviewer-user",
            "submitted_at": "2026-01-15T12:00:00Z",
            "state": "APPROVED",
            "body": "LGTM!",
            "has_actionable_comments": False,
            "url": "https://github.com/org/repo/pull/123#pullrequestreview-123",
        }

    def test_instantiation_with_valid_data(self, valid_review_data):
        """Review model instantiates correctly with valid data."""
        review = Review(**valid_review_data)
        assert review.id == "review_123"
        assert review.author == "reviewer-user"
        assert review.submitted_at == "2026-01-15T12:00:00Z"
        assert review.state == "APPROVED"
        assert review.body == "LGTM!"
        assert review.has_actionable_comments is False
        assert review.url == "https://github.com/org/repo/pull/123#pullrequestreview-123"

    def test_optional_fields_accept_none(self, valid_review_data):
        """Optional fields accept None values."""
        valid_review_data["body"] = None
        valid_review_data["url"] = None

        review = Review(**valid_review_data)
        assert review.body is None
        assert review.url is None

    def test_has_actionable_comments_defaults_to_false(self):
        """has_actionable_comments defaults to False when not provided."""
        review = Review(
            id="123",
            author="user",
            submitted_at="2026-01-15T12:00:00Z",
            state="APPROVED",
        )
        assert review.has_actionable_comments is False

    def test_all_review_states(self):
        """Review accepts all valid GitHub review states."""
        states = ["APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED", "PENDING"]
        for state in states:
            review = Review(
                id="123",
                author="user",
                submitted_at="2026-01-15T12:00:00Z",
                state=state,
            )
            assert review.state == state

    def test_serialization_to_json(self, valid_review_data):
        """Review model serializes to JSON correctly."""
        review = Review(**valid_review_data)
        json_str = review.model_dump_json()
        data = json.loads(json_str)

        assert data["id"] == "review_123"
        assert data["author"] == "reviewer-user"
        assert data["state"] == "APPROVED"

    def test_serialization_roundtrip(self, valid_review_data):
        """Review serializes and deserializes correctly."""
        original = Review(**valid_review_data)
        json_str = original.model_dump_json()
        restored = Review.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.author == restored.author
        assert original.submitted_at == restored.submitted_at
        assert original.state == restored.state


class TestReviewsAfterLatestCommit:
    """Tests for has_reviews_after_latest_commit detection."""

    @pytest.fixture
    def test_container(self, mock_github, make_pr_data, make_ci_status):
        """Create a test container with mock GitHub adapter."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        return Container.create_for_testing(github=mock_github)

    @pytest.fixture
    def make_commit_data(self):
        """Factory for creating commit data dictionaries."""

        def _make(
            sha: str = "abc123def456",
            committer_date: str = "2026-01-15T10:00:00Z",
            author_date: str = "2026-01-15T09:00:00Z",
        ):
            return {
                "sha": sha,
                "commit": {
                    "committer": {"date": committer_date},
                    "author": {"date": author_date},
                },
            }

        return _make

    def test_no_reviews_returns_empty_list(
        self, mock_github, make_pr_data, make_ci_status, make_commit_data
    ):
        """When there are no reviews, reviews list is empty."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data())

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.reviews == []
        assert result.has_reviews_after_latest_commit is False

    def test_review_before_commit_not_flagged(
        self, mock_github, make_pr_data, make_ci_status, make_review, make_commit_data
    ):
        """Review submitted before latest commit does not flag has_reviews_after_latest_commit."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        # Review submitted at 09:00, commit at 10:00
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer",
                    state="APPROVED",
                    submitted_at="2026-01-15T09:00:00Z",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data(committer_date="2026-01-15T10:00:00Z"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 1
        assert result.has_reviews_after_latest_commit is False

    def test_review_after_commit_is_flagged(
        self, mock_github, make_pr_data, make_ci_status, make_review, make_commit_data
    ):
        """Review submitted after latest commit flags has_reviews_after_latest_commit."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        # Review submitted at 11:00, commit at 10:00
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer",
                    state="CHANGES_REQUESTED",
                    submitted_at="2026-01-15T11:00:00Z",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data(committer_date="2026-01-15T10:00:00Z"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 1
        assert result.has_reviews_after_latest_commit is True

    def test_multiple_reviews_some_after_commit(
        self, mock_github, make_pr_data, make_ci_status, make_review, make_commit_data
    ):
        """When some reviews are after commit, has_reviews_after_latest_commit is True."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        # One review before commit (09:00), one after (11:00), commit at 10:00
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer1",
                    state="COMMENTED",
                    submitted_at="2026-01-15T09:00:00Z",
                ),
                make_review(
                    review_id=2,
                    author="reviewer2",
                    state="CHANGES_REQUESTED",
                    submitted_at="2026-01-15T11:00:00Z",
                ),
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data(committer_date="2026-01-15T10:00:00Z"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 2
        assert result.has_reviews_after_latest_commit is True

    def test_review_at_exact_same_time_as_commit(
        self, mock_github, make_pr_data, make_ci_status, make_review, make_commit_data
    ):
        """Review at exact same timestamp as commit is not flagged as after."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer",
                    state="APPROVED",
                    submitted_at="2026-01-15T10:00:00Z",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data(committer_date="2026-01-15T10:00:00Z"))

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 1
        # Same timestamp is NOT after, so should be False
        assert result.has_reviews_after_latest_commit is False


class TestReviewTimestampFieldsInOutput:
    """Tests for review timestamp fields in PRAnalysisResult."""

    def test_latest_commit_timestamp_included(self, mock_github, make_pr_data, make_ci_status):
        """latest_commit_timestamp is included in the result."""

        def make_commit_data():
            return {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data())

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.latest_commit_timestamp == "2026-01-15T10:00:00Z"

    def test_reviews_list_contains_all_reviews(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """reviews list contains all submitted reviews."""

        def make_commit_data():
            return {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer1",
                    state="APPROVED",
                    submitted_at="2026-01-15T08:00:00Z",
                ),
                make_review(
                    review_id=2,
                    author="reviewer2",
                    state="CHANGES_REQUESTED",
                    submitted_at="2026-01-15T09:00:00Z",
                ),
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data())

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 2
        assert result.reviews[0].id == "1"
        assert result.reviews[0].author == "reviewer1"
        assert result.reviews[0].state == "APPROVED"
        assert result.reviews[1].id == "2"
        assert result.reviews[1].author == "reviewer2"
        assert result.reviews[1].state == "CHANGES_REQUESTED"

    def test_result_serializes_with_reviews(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """PRAnalysisResult with reviews serializes to JSON correctly."""

        def make_commit_data():
            return {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }

        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer",
                    state="APPROVED",
                    submitted_at="2026-01-15T11:00:00Z",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(make_commit_data())

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        # Serialize to JSON and verify
        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert "reviews" in data
        assert len(data["reviews"]) == 1
        assert data["reviews"][0]["id"] == "1"
        assert data["reviews"][0]["submitted_at"] == "2026-01-15T11:00:00Z"
        assert data["has_reviews_after_latest_commit"] is True
        assert data["latest_commit_timestamp"] == "2026-01-15T10:00:00Z"


class TestCommitTimestampFallback:
    """Tests for commit timestamp fallback logic."""

    def test_uses_committer_date_primarily(self, mock_github, make_pr_data, make_ci_status):
        """Uses committer date when available."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(
            {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }
        )

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.latest_commit_timestamp == "2026-01-15T10:00:00Z"

    def test_falls_back_to_author_date(self, mock_github, make_pr_data, make_ci_status):
        """Falls back to author date when committer date is missing."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(
            {
                "sha": "abc123",
                "commit": {
                    "committer": {},  # No date
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }
        )

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.latest_commit_timestamp == "2026-01-15T09:00:00Z"

    def test_falls_back_to_pr_updated_at(self, mock_github, make_pr_data, make_ci_status):
        """Falls back to PR updated_at when commit dates are missing."""
        mock_github.set_pr_data(make_pr_data(number=123, updated_at="2026-01-15T08:00:00Z"))
        mock_github.set_comments([])
        mock_github.set_reviews([])
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(
            {
                "sha": "abc123",
                "commit": {
                    "committer": {},
                    "author": {},
                },
            }
        )

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert result.latest_commit_timestamp == "2026-01-15T08:00:00Z"


class TestReviewHasActionableComments:
    """Tests for has_actionable_comments field on reviews."""

    def test_review_with_actionable_body_has_actionable_comments_true(
        self, mock_github, make_pr_data, make_ci_status
    ):
        """Review with actionable body (e.g., CodeRabbit issue) sets has_actionable_comments."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        # Review with CodeRabbit-style actionable body
        mock_github.set_reviews(
            [
                {
                    "id": 12345,
                    "user": {"login": "coderabbitai[bot]"},
                    "state": "COMMENTED",
                    "submitted_at": "2026-01-15T11:00:00Z",
                    "body": """_⚠️ Potential issue_ | _🔴 Critical_

Missing null check in handler function.

This could cause a runtime exception.""",
                    "html_url": "https://github.com/org/repo/pull/123#pullrequestreview-12345",
                }
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(
            {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }
        )

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 1
        assert result.reviews[0].id == "12345"
        assert result.reviews[0].has_actionable_comments is True

    def test_review_with_non_actionable_body_has_actionable_comments_false(
        self, mock_github, make_pr_data, make_ci_status, make_review
    ):
        """Review with non-actionable body sets has_actionable_comments to False."""
        mock_github.set_pr_data(make_pr_data(number=123))
        mock_github.set_comments([])
        # Review with simple LGTM body - not actionable
        mock_github.set_reviews(
            [
                make_review(
                    review_id=1,
                    author="reviewer",
                    state="APPROVED",
                    submitted_at="2026-01-15T11:00:00Z",
                    body="LGTM! Great work.",
                )
            ]
        )
        mock_github.set_threads([])
        mock_github.set_ci_status(make_ci_status(state="success"))
        mock_github.set_commit_data(
            {
                "sha": "abc123",
                "commit": {
                    "committer": {"date": "2026-01-15T10:00:00Z"},
                    "author": {"date": "2026-01-15T09:00:00Z"},
                },
            }
        )

        container = Container.create_for_testing(github=mock_github)
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze("owner", "repo", 123)

        assert len(result.reviews) == 1
        assert result.reviews[0].has_actionable_comments is False


class TestGetCommitMethod:
    """Tests for the get_commit adapter method."""

    def test_get_commit_returns_commit_data(self, mock_github):
        """get_commit returns the configured commit data."""
        commit_data = {
            "sha": "abc123",
            "commit": {
                "committer": {"date": "2026-01-15T10:00:00Z"},
                "author": {"date": "2026-01-15T09:00:00Z"},
            },
        }
        mock_github.set_commit_data(commit_data)

        result = mock_github.get_commit("owner", "repo", "abc123")

        assert result == commit_data

    def test_get_commit_empty_returns_empty_dict(self, mock_github):
        """get_commit returns empty dict when not configured."""
        result = mock_github.get_commit("owner", "repo", "abc123")

        assert result == {}
