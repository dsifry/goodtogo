"""Tests for GoodToMerge core data models.

This module tests all Pydantic models and enums defined in goodtogo.core.models,
ensuring proper instantiation, validation, and serialization behavior.
"""

import json

import pytest
from pydantic import ValidationError

from goodtogo.core.models import (
    CacheStats,
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


class TestPRStatusEnum:
    """Tests for PRStatus enum values and behavior."""

    def test_ready_value(self):
        """READY status exists with correct value."""
        assert PRStatus.READY == "READY"
        assert PRStatus.READY.value == "READY"

    def test_action_required_value(self):
        """ACTION_REQUIRED status exists with correct value."""
        assert PRStatus.ACTION_REQUIRED == "ACTION_REQUIRED"
        assert PRStatus.ACTION_REQUIRED.value == "ACTION_REQUIRED"

    def test_unresolved_threads_value(self):
        """UNRESOLVED_THREADS status exists with correct value."""
        assert PRStatus.UNRESOLVED_THREADS == "UNRESOLVED"
        assert PRStatus.UNRESOLVED_THREADS.value == "UNRESOLVED"

    def test_ci_failing_value(self):
        """CI_FAILING status exists with correct value."""
        assert PRStatus.CI_FAILING == "CI_FAILING"
        assert PRStatus.CI_FAILING.value == "CI_FAILING"

    def test_error_value(self):
        """ERROR status exists with correct value."""
        assert PRStatus.ERROR == "ERROR"
        assert PRStatus.ERROR.value == "ERROR"

    def test_all_enum_values_exist(self):
        """All expected PRStatus values are defined."""
        expected_values = {"READY", "ACTION_REQUIRED", "UNRESOLVED", "CI_FAILING", "ERROR"}
        actual_values = {status.value for status in PRStatus}
        assert actual_values == expected_values

    def test_is_string_enum(self):
        """PRStatus is a string enum for JSON serialization."""
        assert isinstance(PRStatus.READY, str)
        assert PRStatus.READY == "READY"


class TestCommentClassificationEnum:
    """Tests for CommentClassification enum values and behavior."""

    def test_actionable_value(self):
        """ACTIONABLE classification exists with correct value."""
        assert CommentClassification.ACTIONABLE == "ACTIONABLE"
        assert CommentClassification.ACTIONABLE.value == "ACTIONABLE"

    def test_non_actionable_value(self):
        """NON_ACTIONABLE classification exists with correct value."""
        assert CommentClassification.NON_ACTIONABLE == "NON_ACTIONABLE"
        assert CommentClassification.NON_ACTIONABLE.value == "NON_ACTIONABLE"

    def test_ambiguous_value(self):
        """AMBIGUOUS classification exists with correct value."""
        assert CommentClassification.AMBIGUOUS == "AMBIGUOUS"
        assert CommentClassification.AMBIGUOUS.value == "AMBIGUOUS"

    def test_all_enum_values_exist(self):
        """All expected CommentClassification values are defined."""
        expected_values = {"ACTIONABLE", "NON_ACTIONABLE", "AMBIGUOUS"}
        actual_values = {classification.value for classification in CommentClassification}
        assert actual_values == expected_values

    def test_is_string_enum(self):
        """CommentClassification is a string enum for JSON serialization."""
        assert isinstance(CommentClassification.ACTIONABLE, str)


class TestPriorityEnum:
    """Tests for Priority enum values and behavior."""

    def test_critical_value(self):
        """CRITICAL priority exists with correct value."""
        assert Priority.CRITICAL == "CRITICAL"
        assert Priority.CRITICAL.value == "CRITICAL"

    def test_major_value(self):
        """MAJOR priority exists with correct value."""
        assert Priority.MAJOR == "MAJOR"
        assert Priority.MAJOR.value == "MAJOR"

    def test_minor_value(self):
        """MINOR priority exists with correct value."""
        assert Priority.MINOR == "MINOR"
        assert Priority.MINOR.value == "MINOR"

    def test_trivial_value(self):
        """TRIVIAL priority exists with correct value."""
        assert Priority.TRIVIAL == "TRIVIAL"
        assert Priority.TRIVIAL.value == "TRIVIAL"

    def test_unknown_value(self):
        """UNKNOWN priority exists with correct value."""
        assert Priority.UNKNOWN == "UNKNOWN"
        assert Priority.UNKNOWN.value == "UNKNOWN"

    def test_all_enum_values_exist(self):
        """All expected Priority values are defined."""
        expected_values = {"CRITICAL", "MAJOR", "MINOR", "TRIVIAL", "UNKNOWN"}
        actual_values = {priority.value for priority in Priority}
        assert actual_values == expected_values

    def test_is_string_enum(self):
        """Priority is a string enum for JSON serialization."""
        assert isinstance(Priority.CRITICAL, str)


class TestReviewerTypeEnum:
    """Tests for ReviewerType enum values and behavior."""

    def test_coderabbit_value(self):
        """CODERABBIT reviewer type exists with correct value."""
        assert ReviewerType.CODERABBIT == "coderabbit"
        assert ReviewerType.CODERABBIT.value == "coderabbit"

    def test_greptile_value(self):
        """GREPTILE reviewer type exists with correct value."""
        assert ReviewerType.GREPTILE == "greptile"
        assert ReviewerType.GREPTILE.value == "greptile"

    def test_claude_value(self):
        """CLAUDE reviewer type exists with correct value."""
        assert ReviewerType.CLAUDE == "claude"
        assert ReviewerType.CLAUDE.value == "claude"

    def test_cursor_value(self):
        """CURSOR reviewer type exists with correct value."""
        assert ReviewerType.CURSOR == "cursor"
        assert ReviewerType.CURSOR.value == "cursor"

    def test_human_value(self):
        """HUMAN reviewer type exists with correct value."""
        assert ReviewerType.HUMAN == "human"
        assert ReviewerType.HUMAN.value == "human"

    def test_unknown_value(self):
        """UNKNOWN reviewer type exists with correct value."""
        assert ReviewerType.UNKNOWN == "unknown"
        assert ReviewerType.UNKNOWN.value == "unknown"

    def test_all_enum_values_exist(self):
        """All expected ReviewerType values are defined."""
        expected_values = {"coderabbit", "greptile", "claude", "cursor", "human", "unknown"}
        actual_values = {reviewer_type.value for reviewer_type in ReviewerType}
        assert actual_values == expected_values

    def test_is_string_enum(self):
        """ReviewerType is a string enum for JSON serialization."""
        assert isinstance(ReviewerType.CODERABBIT, str)


class TestCommentModel:
    """Tests for Comment Pydantic model."""

    @pytest.fixture
    def valid_comment_data(self):
        """Provide valid comment data for testing."""
        return {
            "id": "comment_123",
            "author": "coderabbitai[bot]",
            "reviewer_type": ReviewerType.CODERABBIT,
            "body": "This is a test comment.",
            "classification": CommentClassification.ACTIONABLE,
            "priority": Priority.MINOR,
            "requires_investigation": False,
            "thread_id": "thread_456",
            "is_resolved": False,
            "is_outdated": False,
            "file_path": "src/main.py",
            "line_number": 42,
            "created_at": "2026-01-15T10:30:00Z",
            "addressed_in_commit": None,
        }

    def test_instantiation_with_valid_data(self, valid_comment_data):
        """Comment model instantiates correctly with valid data."""
        comment = Comment(**valid_comment_data)
        assert comment.id == "comment_123"
        assert comment.author == "coderabbitai[bot]"
        assert comment.reviewer_type == ReviewerType.CODERABBIT
        assert comment.body == "This is a test comment."
        assert comment.classification == CommentClassification.ACTIONABLE
        assert comment.priority == Priority.MINOR
        assert comment.requires_investigation is False
        assert comment.thread_id == "thread_456"
        assert comment.is_resolved is False
        assert comment.is_outdated is False
        assert comment.file_path == "src/main.py"
        assert comment.line_number == 42
        assert comment.created_at == "2026-01-15T10:30:00Z"
        assert comment.addressed_in_commit is None

    def test_optional_fields_accept_none(self, valid_comment_data):
        """Optional fields accept None values."""
        valid_comment_data["thread_id"] = None
        valid_comment_data["file_path"] = None
        valid_comment_data["line_number"] = None
        valid_comment_data["addressed_in_commit"] = None

        comment = Comment(**valid_comment_data)
        assert comment.thread_id is None
        assert comment.file_path is None
        assert comment.line_number is None
        assert comment.addressed_in_commit is None

    def test_missing_required_field_raises(self, valid_comment_data):
        """Missing required field raises ValidationError."""
        del valid_comment_data["id"]
        with pytest.raises(ValidationError):
            Comment(**valid_comment_data)

    def test_invalid_enum_value_raises(self, valid_comment_data):
        """Invalid enum value raises ValidationError."""
        valid_comment_data["classification"] = "INVALID_CLASSIFICATION"
        with pytest.raises(ValidationError):
            Comment(**valid_comment_data)

    def test_serialization_to_json(self, valid_comment_data):
        """Comment model serializes to JSON correctly."""
        comment = Comment(**valid_comment_data)
        json_str = comment.model_dump_json()
        data = json.loads(json_str)

        assert data["id"] == "comment_123"
        assert data["reviewer_type"] == "coderabbit"
        assert data["classification"] == "ACTIONABLE"
        assert data["priority"] == "MINOR"

    def test_serialization_roundtrip(self, valid_comment_data):
        """Comment serializes and deserializes correctly."""
        original = Comment(**valid_comment_data)
        json_str = original.model_dump_json()
        restored = Comment.model_validate_json(json_str)

        assert original.id == restored.id
        assert original.classification == restored.classification
        assert original.reviewer_type == restored.reviewer_type


class TestCICheckModel:
    """Tests for CICheck Pydantic model."""

    @pytest.fixture
    def valid_ci_check_data(self):
        """Provide valid CI check data for testing."""
        return {
            "name": "build",
            "status": "success",
            "conclusion": "success",
            "url": "https://github.com/org/repo/actions/runs/123",
        }

    def test_instantiation_with_valid_data(self, valid_ci_check_data):
        """CICheck model instantiates correctly with valid data."""
        check = CICheck(**valid_ci_check_data)
        assert check.name == "build"
        assert check.status == "success"
        assert check.conclusion == "success"
        assert check.url == "https://github.com/org/repo/actions/runs/123"

    def test_optional_fields_accept_none(self, valid_ci_check_data):
        """Optional fields accept None values."""
        valid_ci_check_data["conclusion"] = None
        valid_ci_check_data["url"] = None

        check = CICheck(**valid_ci_check_data)
        assert check.conclusion is None
        assert check.url is None

    def test_missing_required_field_raises(self, valid_ci_check_data):
        """Missing required field raises ValidationError."""
        del valid_ci_check_data["name"]
        with pytest.raises(ValidationError):
            CICheck(**valid_ci_check_data)

    def test_serialization_to_json(self, valid_ci_check_data):
        """CICheck model serializes to JSON correctly."""
        check = CICheck(**valid_ci_check_data)
        json_str = check.model_dump_json()
        data = json.loads(json_str)

        assert data["name"] == "build"
        assert data["status"] == "success"


class TestCIStatusModel:
    """Tests for CIStatus Pydantic model."""

    @pytest.fixture
    def valid_ci_status_data(self):
        """Provide valid CI status data for testing."""
        return {
            "state": "success",
            "total_checks": 5,
            "passed": 5,
            "failed": 0,
            "pending": 0,
            "checks": [
                {"name": "build", "status": "success", "conclusion": "success", "url": None},
                {"name": "test", "status": "success", "conclusion": "success", "url": None},
            ],
        }

    def test_instantiation_with_valid_data(self, valid_ci_status_data):
        """CIStatus model instantiates correctly with valid data."""
        status = CIStatus(**valid_ci_status_data)
        assert status.state == "success"
        assert status.total_checks == 5
        assert status.passed == 5
        assert status.failed == 0
        assert status.pending == 0
        assert len(status.checks) == 2

    def test_empty_checks_list_valid(self, valid_ci_status_data):
        """Empty checks list is valid."""
        valid_ci_status_data["checks"] = []
        status = CIStatus(**valid_ci_status_data)
        assert status.checks == []

    def test_nested_check_model_validation(self, valid_ci_status_data):
        """Nested CICheck models are validated."""
        valid_ci_status_data["checks"] = [{"invalid": "data"}]
        with pytest.raises(ValidationError):
            CIStatus(**valid_ci_status_data)

    def test_serialization_to_json(self, valid_ci_status_data):
        """CIStatus model serializes to JSON correctly."""
        status = CIStatus(**valid_ci_status_data)
        json_str = status.model_dump_json()
        data = json.loads(json_str)

        assert data["state"] == "success"
        assert len(data["checks"]) == 2
        assert data["checks"][0]["name"] == "build"


class TestThreadSummaryModel:
    """Tests for ThreadSummary Pydantic model."""

    @pytest.fixture
    def valid_thread_summary_data(self):
        """Provide valid thread summary data for testing."""
        return {
            "total": 10,
            "resolved": 8,
            "unresolved": 2,
            "outdated": 1,
        }

    def test_instantiation_with_valid_data(self, valid_thread_summary_data):
        """ThreadSummary model instantiates correctly with valid data."""
        summary = ThreadSummary(**valid_thread_summary_data)
        assert summary.total == 10
        assert summary.resolved == 8
        assert summary.unresolved == 2
        assert summary.outdated == 1

    def test_zero_values_valid(self):
        """Zero values are valid for all counts."""
        data = {"total": 0, "resolved": 0, "unresolved": 0, "outdated": 0}
        summary = ThreadSummary(**data)
        assert summary.total == 0

    def test_missing_required_field_raises(self, valid_thread_summary_data):
        """Missing required field raises ValidationError."""
        del valid_thread_summary_data["total"]
        with pytest.raises(ValidationError):
            ThreadSummary(**valid_thread_summary_data)

    def test_invalid_type_raises(self, valid_thread_summary_data):
        """Invalid type raises ValidationError."""
        valid_thread_summary_data["total"] = "not_a_number"
        with pytest.raises(ValidationError):
            ThreadSummary(**valid_thread_summary_data)

    def test_serialization_to_json(self, valid_thread_summary_data):
        """ThreadSummary model serializes to JSON correctly."""
        summary = ThreadSummary(**valid_thread_summary_data)
        json_str = summary.model_dump_json()
        data = json.loads(json_str)

        assert data["total"] == 10
        assert data["resolved"] == 8


class TestCacheStatsModel:
    """Tests for CacheStats Pydantic model."""

    @pytest.fixture
    def valid_cache_stats_data(self):
        """Provide valid cache stats data for testing."""
        return {
            "hits": 100,
            "misses": 20,
            "hit_rate": 0.83,
        }

    def test_instantiation_with_valid_data(self, valid_cache_stats_data):
        """CacheStats model instantiates correctly with valid data."""
        stats = CacheStats(**valid_cache_stats_data)
        assert stats.hits == 100
        assert stats.misses == 20
        assert stats.hit_rate == pytest.approx(0.83)

    def test_zero_values_valid(self):
        """Zero values are valid."""
        data = {"hits": 0, "misses": 0, "hit_rate": 0.0}
        stats = CacheStats(**data)
        assert stats.hits == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_boundary_values(self):
        """Hit rate accepts boundary values 0.0 and 1.0."""
        stats_zero = CacheStats(hits=0, misses=10, hit_rate=0.0)
        assert stats_zero.hit_rate == 0.0

        stats_one = CacheStats(hits=10, misses=0, hit_rate=1.0)
        assert stats_one.hit_rate == 1.0

    def test_serialization_to_json(self, valid_cache_stats_data):
        """CacheStats model serializes to JSON correctly."""
        stats = CacheStats(**valid_cache_stats_data)
        json_str = stats.model_dump_json()
        data = json.loads(json_str)

        assert data["hits"] == 100
        assert data["hit_rate"] == pytest.approx(0.83)


class TestPRAnalysisResultModel:
    """Tests for PRAnalysisResult Pydantic model."""

    @pytest.fixture
    def valid_analysis_result_data(self):
        """Provide valid PR analysis result data for testing."""
        return {
            "status": PRStatus.READY,
            "pr_number": 123,
            "repo_owner": "myorg",
            "repo_name": "myrepo",
            "latest_commit_sha": "abc123def456",
            "latest_commit_timestamp": "2026-01-15T10:30:00Z",
            "ci_status": {
                "state": "success",
                "total_checks": 3,
                "passed": 3,
                "failed": 0,
                "pending": 0,
                "checks": [],
            },
            "threads": {
                "total": 5,
                "resolved": 5,
                "unresolved": 0,
                "outdated": 0,
            },
            "comments": [],
            "actionable_comments": [],
            "ambiguous_comments": [],
            "action_items": [],
            "needs_action": False,
            "cache_stats": None,
        }

    def test_instantiation_with_valid_data(self, valid_analysis_result_data):
        """PRAnalysisResult model instantiates correctly with valid data."""
        result = PRAnalysisResult(**valid_analysis_result_data)
        assert result.status == PRStatus.READY
        assert result.pr_number == 123
        assert result.repo_owner == "myorg"
        assert result.repo_name == "myrepo"
        assert result.needs_action is False

    def test_status_enum_from_string(self, valid_analysis_result_data):
        """Status accepts string value matching enum."""
        valid_analysis_result_data["status"] = "READY"
        result = PRAnalysisResult(**valid_analysis_result_data)
        assert result.status == PRStatus.READY

    def test_invalid_status_raises(self, valid_analysis_result_data):
        """Invalid status raises ValidationError."""
        valid_analysis_result_data["status"] = "INVALID_STATUS"
        with pytest.raises(ValidationError):
            PRAnalysisResult(**valid_analysis_result_data)

    def test_nested_model_validation(self, valid_analysis_result_data):
        """Nested models (ci_status, threads) are validated."""
        valid_analysis_result_data["ci_status"] = {"invalid": "data"}
        with pytest.raises(ValidationError):
            PRAnalysisResult(**valid_analysis_result_data)

    def test_cache_stats_optional(self, valid_analysis_result_data):
        """cache_stats field is optional (can be None)."""
        valid_analysis_result_data["cache_stats"] = None
        result = PRAnalysisResult(**valid_analysis_result_data)
        assert result.cache_stats is None

    def test_cache_stats_with_value(self, valid_analysis_result_data):
        """cache_stats accepts valid CacheStats data."""
        valid_analysis_result_data["cache_stats"] = {
            "hits": 10,
            "misses": 2,
            "hit_rate": 0.83,
        }
        result = PRAnalysisResult(**valid_analysis_result_data)
        assert result.cache_stats is not None
        assert result.cache_stats.hits == 10

    def test_serialization_to_json(self, valid_analysis_result_data):
        """PRAnalysisResult model serializes to JSON correctly."""
        result = PRAnalysisResult(**valid_analysis_result_data)
        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert data["status"] == "READY"
        assert data["pr_number"] == 123
        assert data["ci_status"]["state"] == "success"
        assert data["threads"]["resolved"] == 5
        assert data["needs_action"] is False

    def test_serialization_roundtrip(self, valid_analysis_result_data):
        """PRAnalysisResult serializes and deserializes correctly."""
        original = PRAnalysisResult(**valid_analysis_result_data)
        json_str = original.model_dump_json()
        restored = PRAnalysisResult.model_validate_json(json_str)

        assert original.status == restored.status
        assert original.pr_number == restored.pr_number
        assert original.ci_status.state == restored.ci_status.state
        assert original.threads.total == restored.threads.total

    def test_with_comments(self, valid_analysis_result_data):
        """PRAnalysisResult accepts lists of Comment objects."""
        comment_data = {
            "id": "comment_1",
            "author": "coderabbitai[bot]",
            "reviewer_type": "coderabbit",
            "body": "Test comment",
            "classification": "ACTIONABLE",
            "priority": "MINOR",
            "requires_investigation": False,
            "thread_id": None,
            "is_resolved": False,
            "is_outdated": False,
            "file_path": "test.py",
            "line_number": 10,
            "created_at": "2026-01-15T10:00:00Z",
            "addressed_in_commit": None,
        }
        valid_analysis_result_data["comments"] = [comment_data]
        valid_analysis_result_data["actionable_comments"] = [comment_data]

        result = PRAnalysisResult(**valid_analysis_result_data)
        assert len(result.comments) == 1
        assert len(result.actionable_comments) == 1
        assert result.comments[0].id == "comment_1"

    def test_with_action_items(self, valid_analysis_result_data):
        """PRAnalysisResult accepts action_items list."""
        valid_analysis_result_data["action_items"] = [
            "Address 2 actionable comments",
            "Resolve 1 unresolved thread",
        ]
        valid_analysis_result_data["needs_action"] = True
        valid_analysis_result_data["status"] = PRStatus.ACTION_REQUIRED

        result = PRAnalysisResult(**valid_analysis_result_data)
        assert len(result.action_items) == 2
        assert "actionable comments" in result.action_items[0]
