"""Integration tests for the GoodToMerge CLI.

This module tests the CLI interface using Click's CliRunner,
verifying command-line argument handling, output formats,
exit codes, and error handling.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from goodtogo.cli import AI_FRIENDLY_EXIT_CODES, SEMANTIC_EXIT_CODES, main
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


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CliRunner for testing."""
    return CliRunner()


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for CLI tests."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_123456")


# ============================================================================
# Test: Missing GITHUB_TOKEN Error
# ============================================================================


class TestMissingGitHubToken:
    """Tests for handling missing GITHUB_TOKEN environment variable."""

    def test_missing_github_token_exits_with_error(self, cli_runner: CliRunner):
        """CLI should exit with code 4 when GITHUB_TOKEN is missing."""
        # Ensure GITHUB_TOKEN is not set
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "owner/repo"],
            env={"GITHUB_TOKEN": None},
            catch_exceptions=False,
        )

        assert result.exit_code == 4
        assert "GITHUB_TOKEN" in result.output
        assert "Error" in result.output

    def test_missing_github_token_error_message(self, cli_runner: CliRunner):
        """Error message should clearly indicate GITHUB_TOKEN is required."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "owner/repo"],
            env={},
        )

        assert "GITHUB_TOKEN environment variable required" in result.output


# ============================================================================
# Test: Invalid --repo Format Error
# ============================================================================


class TestInvalidRepoFormat:
    """Tests for handling invalid --repo format."""

    def test_repo_without_slash_exits_with_error(self, cli_runner: CliRunner, mock_env):
        """CLI should exit with code 4 when --repo is not owner/repo format."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "invalidrepo"],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert result.exit_code == 4
        assert "owner/repo" in result.output

    def test_repo_format_error_message(self, cli_runner: CliRunner, mock_env):
        """Error message should explain correct format."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "no-slash-here"],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert "--repo must be in owner/repo format" in result.output

    def test_empty_repo_exits_with_error(self, cli_runner: CliRunner, mock_env):
        """CLI should exit with error when --repo is empty, not fall through to auto-detect."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", ""],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert result.exit_code == 4
        # Must show format error, not auto-detect error
        assert "--repo must be in owner/repo format" in result.output

    def test_whitespace_repo_exits_with_error(self, cli_runner: CliRunner, mock_env):
        """CLI should exit with error when --repo is whitespace only."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "   "],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert result.exit_code == 4
        assert "--repo must be in owner/repo format" in result.output

    def test_empty_owner_in_repo_exits_with_error(self, cli_runner: CliRunner, mock_env):
        """CLI should exit with error when owner is empty in --repo."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "/myrepo"],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert result.exit_code == 4
        assert "--repo must be in owner/repo format" in result.output

    def test_empty_reponame_in_repo_exits_with_error(self, cli_runner: CliRunner, mock_env):
        """CLI should exit with error when repo name is empty in --repo."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "owner/"],
            env={"GITHUB_TOKEN": "ghp_test_token"},
        )

        assert result.exit_code == 4
        assert "--repo must be in owner/repo format" in result.output


# ============================================================================
# Test: --help and --version
# ============================================================================


class TestHelpAndVersion:
    """Tests for --help and --version options."""

    def test_help_option(self, cli_runner: CliRunner):
        """--help should display usage information."""
        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Check if a PR is ready to merge" in result.output
        assert "--repo" in result.output
        assert "--format" in result.output
        assert "--cache" in result.output
        assert "PR_NUMBER" in result.output

    def test_help_shows_exit_codes(self, cli_runner: CliRunner):
        """--help should document exit codes."""
        result = cli_runner.invoke(main, ["--help"])

        # Both AI-friendly and semantic exit codes should be documented
        assert "Exit codes" in result.output
        assert "AI-friendly" in result.output
        assert "semantic" in result.output.lower()
        assert "Ready to merge" in result.output
        assert "Actionable comments" in result.output

    def test_version_option(self, cli_runner: CliRunner):
        """--version should display the version number."""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # Version should match the pattern X.Y.Z
        assert "0.1.0" in result.output or "version" in result.output.lower()


# ============================================================================
# Test: JSON Output Format
# ============================================================================


class TestJsonOutput:
    """Tests for JSON output format."""

    @pytest.fixture
    def mock_analysis_result(self) -> PRAnalysisResult:
        """Create a mock analysis result."""
        return PRAnalysisResult(
            status=PRStatus.READY,
            pr_number=123,
            repo_owner="owner",
            repo_name="repo",
            latest_commit_sha="abc123",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=3,
                passed=3,
                failed=0,
                pending=0,
                checks=[
                    CICheck(name="build", status="success", conclusion="success", url=None),
                    CICheck(name="test", status="success", conclusion="success", url=None),
                ],
            ),
            threads=ThreadSummary(
                total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
            ),
            comments=[],
            actionable_comments=[],
            ambiguous_comments=[],
            action_items=[],
            needs_action=False,
            cache_stats=CacheStats(hits=5, misses=2, hit_rate=0.71),
        )

    def test_json_output_is_valid_json(
        self, cli_runner: CliRunner, mock_analysis_result: PRAnalysisResult
    ):
        """JSON output should be parseable JSON."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_analysis_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "json"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.exit_code == 0
        # Should be valid JSON
        parsed = json.loads(result.output)
        assert parsed["status"] == "READY"
        assert parsed["pr_number"] == 123

    def test_json_output_contains_all_fields(
        self, cli_runner: CliRunner, mock_analysis_result: PRAnalysisResult
    ):
        """JSON output should include all result fields."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_analysis_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "json"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        parsed = json.loads(result.output)
        expected_fields = [
            "status",
            "pr_number",
            "repo_owner",
            "repo_name",
            "ci_status",
            "threads",
            "comments",
            "actionable_comments",
            "action_items",
            "needs_action",
        ]
        for field in expected_fields:
            assert field in parsed, f"Missing field: {field}"

    def test_json_output_default_format(
        self, cli_runner: CliRunner, mock_analysis_result: PRAnalysisResult
    ):
        """JSON should be the default output format."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_analysis_result
                mock_analyzer_cls.return_value = mock_analyzer

                # No --format option specified
                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        # Should be valid JSON (default format)
        parsed = json.loads(result.output)
        assert "status" in parsed


# ============================================================================
# Test: Text Output Format
# ============================================================================


class TestTextOutput:
    """Tests for text output format."""

    @pytest.fixture
    def ready_result(self) -> PRAnalysisResult:
        """Create a READY status result."""
        return PRAnalysisResult(
            status=PRStatus.READY,
            pr_number=456,
            repo_owner="myorg",
            repo_name="myrepo",
            latest_commit_sha="def456",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=2,
                passed=2,
                failed=0,
                pending=0,
                checks=[],
            ),
            threads=ThreadSummary(
                total=5, resolved=5, unresolved=0, outdated=1, unresolved_threads=[]
            ),
            comments=[],
            actionable_comments=[],
            ambiguous_comments=[],
            action_items=[],
            needs_action=False,
            cache_stats=None,
        )

    @pytest.fixture
    def action_required_result(self) -> PRAnalysisResult:
        """Create an ACTION_REQUIRED status result."""
        return PRAnalysisResult(
            status=PRStatus.ACTION_REQUIRED,
            pr_number=789,
            repo_owner="myorg",
            repo_name="myrepo",
            latest_commit_sha="ghi789",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=2,
                passed=2,
                failed=0,
                pending=0,
                checks=[],
            ),
            threads=ThreadSummary(
                total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
            ),
            comments=[],
            actionable_comments=[
                Comment(
                    id="1",
                    author="reviewer",
                    reviewer_type=ReviewerType.HUMAN,
                    body="Please fix this bug",
                    classification=CommentClassification.ACTIONABLE,
                    priority=Priority.MAJOR,
                    requires_investigation=False,
                    thread_id=None,
                    is_resolved=False,
                    is_outdated=False,
                    file_path="src/main.py",
                    line_number=42,
                    created_at="2024-01-15T10:00:00Z",
                    addressed_in_commit=None,
                    url=None,
                )
            ],
            ambiguous_comments=[],
            action_items=["1 major issue must be fixed before merge"],
            needs_action=True,
            cache_stats=None,
        )

    def test_text_output_shows_status(self, cli_runner: CliRunner, ready_result: PRAnalysisResult):
        """Text output should display the PR status."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = ready_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["456", "--repo", "myorg/myrepo", "--format", "text"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert "READY" in result.output
        assert "PR #456" in result.output

    def test_text_output_shows_ci_summary(
        self, cli_runner: CliRunner, ready_result: PRAnalysisResult
    ):
        """Text output should show CI check summary."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = ready_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["456", "--repo", "myorg/myrepo", "--format", "text"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert "CI:" in result.output
        assert "2/2" in result.output  # passed/total

    def test_text_output_shows_thread_summary(
        self, cli_runner: CliRunner, ready_result: PRAnalysisResult
    ):
        """Text output should show thread resolution summary."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = ready_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["456", "--repo", "myorg/myrepo", "--format", "text"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert "Threads:" in result.output
        assert "5/5" in result.output  # resolved/total

    def test_text_output_shows_action_items(
        self, cli_runner: CliRunner, action_required_result: PRAnalysisResult
    ):
        """Text output should display action items when present."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = action_required_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["789", "--repo", "myorg/myrepo", "--format", "text"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert "Action required:" in result.output
        assert "major issue" in result.output

    def test_text_output_uses_status_icons(
        self, cli_runner: CliRunner, ready_result: PRAnalysisResult
    ):
        """Text output should use status icons (OK, !!, ??, XX, ##)."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = ready_result
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["456", "--repo", "myorg/myrepo", "--format", "text"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert "OK" in result.output


# ============================================================================
# Test: Exit Codes
# ============================================================================


class TestExitCodes:
    """Tests for correct exit codes based on PR status."""

    @pytest.fixture
    def make_result(self):
        """Factory for creating PRAnalysisResult with different statuses."""

        def _make(status: PRStatus) -> PRAnalysisResult:
            return PRAnalysisResult(
                status=status,
                pr_number=123,
                repo_owner="owner",
                repo_name="repo",
                latest_commit_sha="abc123",
                latest_commit_timestamp="2024-01-15T10:00:00Z",
                ci_status=CIStatus(
                    state="success" if status == PRStatus.READY else "failure",
                    total_checks=1,
                    passed=1 if status == PRStatus.READY else 0,
                    failed=0 if status == PRStatus.READY else 1,
                    pending=0,
                    checks=[],
                ),
                threads=ThreadSummary(
                    total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
                ),
                comments=[],
                actionable_comments=[],
                ambiguous_comments=[],
                action_items=[],
                needs_action=status != PRStatus.READY,
                cache_stats=None,
            )

        return _make

    @pytest.mark.parametrize(
        "status,expected_code",
        [
            (PRStatus.READY, 0),
            (PRStatus.ACTION_REQUIRED, 1),
            (PRStatus.UNRESOLVED_THREADS, 2),
            (PRStatus.CI_FAILING, 3),
            (PRStatus.ERROR, 4),
        ],
    )
    def test_semantic_exit_code_matches_status(
        self, cli_runner: CliRunner, make_result, status: PRStatus, expected_code: int
    ):
        """Exit code should match the PR status when using --semantic-codes."""
        result_model = make_result(status)

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_model
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--semantic-codes"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.exit_code == expected_code
        # Unlike -q, --semantic-codes should still produce output
        assert result.output != ""

    @pytest.mark.parametrize(
        "status,expected_code",
        [
            (PRStatus.READY, 0),
            (PRStatus.ACTION_REQUIRED, 0),
            (PRStatus.UNRESOLVED_THREADS, 0),
            (PRStatus.CI_FAILING, 0),
            (PRStatus.ERROR, 4),
        ],
    )
    def test_default_exit_code_is_ai_friendly(
        self, cli_runner: CliRunner, make_result, status: PRStatus, expected_code: int
    ):
        """Default exit code should be AI-friendly (0 for non-error states)."""
        result_model = make_result(status)

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_model
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.exit_code == expected_code

    def test_semantic_exit_codes_constant_matches_documentation(self):
        """SEMANTIC_EXIT_CODES constant should match documented values."""
        assert SEMANTIC_EXIT_CODES[PRStatus.READY] == 0
        assert SEMANTIC_EXIT_CODES[PRStatus.ACTION_REQUIRED] == 1
        assert SEMANTIC_EXIT_CODES[PRStatus.UNRESOLVED_THREADS] == 2
        assert SEMANTIC_EXIT_CODES[PRStatus.CI_FAILING] == 3
        assert SEMANTIC_EXIT_CODES[PRStatus.ERROR] == 4

    def test_ai_friendly_exit_codes_only_error_is_nonzero(self):
        """AI_FRIENDLY_EXIT_CODES should only have non-zero for ERROR."""
        assert AI_FRIENDLY_EXIT_CODES[PRStatus.READY] == 0
        assert AI_FRIENDLY_EXIT_CODES[PRStatus.ACTION_REQUIRED] == 0
        assert AI_FRIENDLY_EXIT_CODES[PRStatus.UNRESOLVED_THREADS] == 0
        assert AI_FRIENDLY_EXIT_CODES[PRStatus.CI_FAILING] == 0
        assert AI_FRIENDLY_EXIT_CODES[PRStatus.ERROR] == 4


# ============================================================================
# Test: Error Redaction in CLI Output
# ============================================================================


class TestErrorRedaction:
    """Tests for error redaction in CLI error output."""

    def test_github_token_is_redacted_in_errors(self, cli_runner: CliRunner):
        """GitHub tokens should be redacted from error messages."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            # Simulate an exception that contains a token
            mock_container_cls.create_default.side_effect = Exception(
                "Auth failed with token ghp_secret123456789"
            )

            result = cli_runner.invoke(
                main,
                ["123", "--repo", "owner/repo", "--verbose"],
                env={"GITHUB_TOKEN": "ghp_real_token"},
            )

        assert result.exit_code == 4
        # Token should be redacted
        assert "ghp_secret123456789" not in result.output
        assert "<REDACTED_TOKEN>" in result.output or "Failed to analyze" in result.output

    def test_error_without_verbose_hides_details(self, cli_runner: CliRunner):
        """Without --verbose, error details should be hidden."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container_cls.create_default.side_effect = Exception(
                "Network timeout connecting to api.github.com"
            )

            result = cli_runner.invoke(
                main,
                ["123", "--repo", "owner/repo"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4
        assert "Network timeout" not in result.output
        assert "Failed to analyze PR" in result.output
        assert "--verbose for details" in result.output

    def test_error_with_verbose_shows_details(self, cli_runner: CliRunner):
        """With --verbose, redacted error details should be shown."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container_cls.create_default.side_effect = Exception(
                "Network timeout connecting to api.github.com"
            )

            result = cli_runner.invoke(
                main,
                ["123", "--repo", "owner/repo", "--verbose"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4
        assert "Network timeout" in result.output

    def test_url_credentials_are_redacted(self, cli_runner: CliRunner):
        """URL credentials should be redacted from error messages."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container_cls.create_default.side_effect = Exception(
                "Failed to connect to redis://user:secretpass@redis.example.com"
            )

            result = cli_runner.invoke(
                main,
                ["123", "--repo", "owner/repo", "--verbose"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4
        assert "secretpass" not in result.output
        assert "<REDACTED>" in result.output


# ============================================================================
# Test: Cache Options
# ============================================================================


class TestCacheOptions:
    """Tests for cache configuration options."""

    def test_default_cache_is_sqlite(self, cli_runner: CliRunner):
        """Default cache should be sqlite."""
        result = cli_runner.invoke(main, ["--help"])
        assert "default: sqlite" in result.output

    def test_cache_none_option(self, cli_runner: CliRunner):
        """--cache=none should be accepted."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = PRAnalysisResult(
                    status=PRStatus.READY,
                    pr_number=123,
                    repo_owner="owner",
                    repo_name="repo",
                    latest_commit_sha="abc",
                    latest_commit_timestamp="2024-01-15T10:00:00Z",
                    ci_status=CIStatus(
                        state="success",
                        total_checks=0,
                        passed=0,
                        failed=0,
                        pending=0,
                        checks=[],
                    ),
                    threads=ThreadSummary(
                        total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
                    ),
                    comments=[],
                    actionable_comments=[],
                    ambiguous_comments=[],
                    action_items=[],
                    needs_action=False,
                    cache_stats=None,
                )
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--cache", "none"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.exit_code == 0
        # Verify cache type was passed correctly
        mock_container_cls.create_default.assert_called_once()
        call_kwargs = mock_container_cls.create_default.call_args[1]
        assert call_kwargs["cache_type"] == "none"

    def test_invalid_cache_option_rejected(self, cli_runner: CliRunner):
        """Invalid cache type should be rejected."""
        result = cli_runner.invoke(
            main,
            ["123", "--repo", "owner/repo", "--cache", "invalid"],
            env={"GITHUB_TOKEN": "ghp_test"},
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()


# ============================================================================
# Test: Verbose Output with Ambiguous Comments
# ============================================================================


class TestVerboseAmbiguousComments:
    """Tests for verbose output showing ambiguous comments."""

    @pytest.fixture
    def result_with_ambiguous_comments(self) -> PRAnalysisResult:
        """Create a result with ambiguous comments."""
        return PRAnalysisResult(
            status=PRStatus.ACTION_REQUIRED,
            pr_number=123,
            repo_owner="owner",
            repo_name="repo",
            latest_commit_sha="abc123",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=2,
                passed=2,
                failed=0,
                pending=0,
                checks=[],
            ),
            threads=ThreadSummary(
                total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
            ),
            comments=[
                Comment(
                    id="1",
                    author="human-reviewer",
                    reviewer_type=ReviewerType.HUMAN,
                    body="This is an interesting approach. What about edge cases?",
                    classification=CommentClassification.AMBIGUOUS,
                    priority=Priority.UNKNOWN,
                    requires_investigation=True,
                    thread_id=None,
                    is_resolved=False,
                    is_outdated=False,
                    file_path="src/main.py",
                    line_number=42,
                    created_at="2024-01-15T10:00:00Z",
                    addressed_in_commit=None,
                    url=None,
                ),
                Comment(
                    id="2",
                    author="another-reviewer",
                    reviewer_type=ReviewerType.HUMAN,
                    body=(
                        "Have you considered the performance implications "
                        "of this change? It might be slow for large inputs."
                    ),
                    classification=CommentClassification.AMBIGUOUS,
                    priority=Priority.UNKNOWN,
                    requires_investigation=True,
                    thread_id=None,
                    is_resolved=False,
                    is_outdated=False,
                    file_path="src/processor.py",
                    line_number=100,
                    created_at="2024-01-15T11:00:00Z",
                    addressed_in_commit=None,
                    url=None,
                ),
            ],
            actionable_comments=[],
            ambiguous_comments=[
                Comment(
                    id="1",
                    author="human-reviewer",
                    reviewer_type=ReviewerType.HUMAN,
                    body="This is an interesting approach. What about edge cases?",
                    classification=CommentClassification.AMBIGUOUS,
                    priority=Priority.UNKNOWN,
                    requires_investigation=True,
                    thread_id=None,
                    is_resolved=False,
                    is_outdated=False,
                    file_path="src/main.py",
                    line_number=42,
                    created_at="2024-01-15T10:00:00Z",
                    addressed_in_commit=None,
                    url=None,
                ),
                Comment(
                    id="2",
                    author="another-reviewer",
                    reviewer_type=ReviewerType.HUMAN,
                    body=(
                        "Have you considered the performance implications "
                        "of this change? It might be slow for large inputs."
                    ),
                    classification=CommentClassification.AMBIGUOUS,
                    priority=Priority.UNKNOWN,
                    requires_investigation=True,
                    thread_id=None,
                    is_resolved=False,
                    is_outdated=False,
                    file_path="src/processor.py",
                    line_number=100,
                    created_at="2024-01-15T11:00:00Z",
                    addressed_in_commit=None,
                    url=None,
                ),
            ],
            action_items=["2 comments require investigation (ambiguous)"],
            needs_action=True,
            cache_stats=None,
        )

    def test_verbose_shows_ambiguous_comments(
        self, cli_runner: CliRunner, result_with_ambiguous_comments: PRAnalysisResult
    ):
        """Verbose text output should show ambiguous comments.

        This tests lines 176-183 in cli.py where ambiguous comments are displayed.
        """
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_with_ambiguous_comments
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "text", "--verbose"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        # Verify verbose output contains ambiguous comments section
        assert "Ambiguous" in result.output or "needs investigation" in result.output
        assert "human-reviewer" in result.output
        assert "interesting approach" in result.output

    def test_verbose_truncates_long_comment_bodies(
        self, cli_runner: CliRunner, result_with_ambiguous_comments: PRAnalysisResult
    ):
        """Long comment bodies should be truncated to 80 chars.

        This tests lines 179-182 in cli.py where bodies are truncated.
        """
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_with_ambiguous_comments
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "text", "--verbose"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        # The second comment body is longer than 80 chars, should be truncated
        # "Have you considered the performance implications of this change?..."
        # After truncation it should have "..." appended
        assert "..." in result.output

    def test_non_verbose_hides_ambiguous_comments(
        self, cli_runner: CliRunner, result_with_ambiguous_comments: PRAnalysisResult
    ):
        """Without --verbose, ambiguous comments should not be shown."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_with_ambiguous_comments
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "text"],  # No --verbose
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        # Without verbose, individual ambiguous comments should not be shown
        # (The action items may still mention them)
        assert "human-reviewer" not in result.output

    def test_verbose_with_no_ambiguous_comments(self, cli_runner: CliRunner):
        """Verbose output should not show ambiguous section if no ambiguous comments."""
        result_no_ambiguous = PRAnalysisResult(
            status=PRStatus.READY,
            pr_number=123,
            repo_owner="owner",
            repo_name="repo",
            latest_commit_sha="abc123",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=1,
                passed=1,
                failed=0,
                pending=0,
                checks=[],
            ),
            threads=ThreadSummary(
                total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
            ),
            comments=[],
            actionable_comments=[],
            ambiguous_comments=[],  # Empty!
            action_items=[],
            needs_action=False,
            cache_stats=None,
        )

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_no_ambiguous
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--format", "text", "--verbose"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        # Should not show "Ambiguous" section header
        assert "Ambiguous (needs investigation)" not in result.output


# ============================================================================
# Test: CLI Main Entry Point
# ============================================================================


class TestCLIMainEntryPoint:
    """Tests for the CLI main entry point (if __name__ == '__main__')."""

    def test_main_function_is_callable(self):
        """The main function should be callable.

        This verifies that the main function exists and is the Click command.
        Line 187 calls main() when the module is run directly.
        """
        from goodtogo.cli import main

        # main should be a Click command
        assert callable(main)
        assert hasattr(main, "callback")  # Click commands have a callback attribute

    def test_cli_module_main_block(self, cli_runner: CliRunner):
        """Test that the cli module can be run as __main__.

        This tests line 186-187 in cli.py.
        """
        import subprocess
        import sys

        # Run the CLI module with --help flag to avoid actually needing GITHUB_TOKEN
        result = subprocess.run(
            [sys.executable, "-m", "goodtogo.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should show help text and exit successfully
        assert result.returncode == 0
        assert "Check if a PR is ready to merge" in result.stdout


# ============================================================================
# Test: Quiet Mode (-q/--quiet)
# ============================================================================


class TestQuietMode:
    """Tests for quiet mode (-q/--quiet) which suppresses output and uses semantic codes."""

    @pytest.fixture
    def make_result(self):
        """Factory for creating PRAnalysisResult with different statuses."""

        def _make(status: PRStatus) -> PRAnalysisResult:
            return PRAnalysisResult(
                status=status,
                pr_number=123,
                repo_owner="owner",
                repo_name="repo",
                latest_commit_sha="abc123",
                latest_commit_timestamp="2024-01-15T10:00:00Z",
                ci_status=CIStatus(
                    state="success" if status == PRStatus.READY else "failure",
                    total_checks=1,
                    passed=1 if status == PRStatus.READY else 0,
                    failed=0 if status == PRStatus.READY else 1,
                    pending=0,
                    checks=[],
                ),
                threads=ThreadSummary(
                    total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
                ),
                comments=[],
                actionable_comments=[],
                ambiguous_comments=[],
                action_items=[],
                needs_action=status != PRStatus.READY,
                cache_stats=None,
            )

        return _make

    def test_quiet_mode_suppresses_output(self, cli_runner: CliRunner, make_result):
        """Quiet mode should produce no output."""
        result_model = make_result(PRStatus.READY)

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_model
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "-q"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.output == ""
        assert result.exit_code == 0

    def test_quiet_long_form_suppresses_output(self, cli_runner: CliRunner, make_result):
        """--quiet should work the same as -q."""
        result_model = make_result(PRStatus.ACTION_REQUIRED)

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_model
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "--quiet"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.output == ""
        assert result.exit_code == 1  # Semantic exit code

    @pytest.mark.parametrize(
        "status,expected_code",
        [
            (PRStatus.READY, 0),
            (PRStatus.ACTION_REQUIRED, 1),
            (PRStatus.UNRESOLVED_THREADS, 2),
            (PRStatus.CI_FAILING, 3),
            (PRStatus.ERROR, 4),
        ],
    )
    def test_quiet_mode_uses_semantic_exit_codes(
        self, cli_runner: CliRunner, make_result, status: PRStatus, expected_code: int
    ):
        """Quiet mode should use semantic exit codes."""
        result_model = make_result(status)

        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = result_model
                mock_analyzer_cls.return_value = mock_analyzer

                result = cli_runner.invoke(
                    main,
                    ["123", "--repo", "owner/repo", "-q"],
                    env={"GITHUB_TOKEN": "ghp_test"},
                )

        assert result.exit_code == expected_code
        assert result.output == ""  # No output in quiet mode

    def test_help_shows_quiet_option(self, cli_runner: CliRunner):
        """--help should document the -q/--quiet option."""
        result = cli_runner.invoke(main, ["--help"])

        assert "-q" in result.output or "--quiet" in result.output
        assert "Quiet mode" in result.output or "quiet" in result.output.lower()

    def test_help_shows_semantic_codes_option(self, cli_runner: CliRunner):
        """--help should document the --semantic-codes option."""
        result = cli_runner.invoke(main, ["--help"])

        assert "--semantic-codes" in result.output


# ============================================================================
# Test: Auto-Detect Repository from Git Origin
# ============================================================================


class TestAutoDetectRepo:
    """Tests for auto-detecting repository from git remote origin."""

    @pytest.fixture
    def mock_result(self) -> PRAnalysisResult:
        """Create a mock READY result for testing."""
        return PRAnalysisResult(
            status=PRStatus.READY,
            pr_number=123,
            repo_owner="detected-owner",
            repo_name="detected-repo",
            latest_commit_sha="abc123",
            latest_commit_timestamp="2024-01-15T10:00:00Z",
            ci_status=CIStatus(
                state="success",
                total_checks=1,
                passed=1,
                failed=0,
                pending=0,
                checks=[],
            ),
            threads=ThreadSummary(
                total=0, resolved=0, unresolved=0, outdated=0, unresolved_threads=[]
            ),
            comments=[],
            actionable_comments=[],
            ambiguous_comments=[],
            action_items=[],
            needs_action=False,
            cache_stats=None,
        )

    def test_explicit_repo_takes_precedence(
        self, cli_runner: CliRunner, mock_result: PRAnalysisResult
    ):
        """When --repo is provided, it should be used even if git origin exists."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_result
                mock_analyzer_cls.return_value = mock_analyzer

                # Even with a git origin, explicit --repo should be used
                with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
                    mock_git.return_value = ("git-owner", "git-repo")

                    result = cli_runner.invoke(
                        main,
                        ["123", "--repo", "explicit-owner/explicit-repo"],
                        env={"GITHUB_TOKEN": "ghp_test"},
                    )

        assert result.exit_code == 0
        # Verify analyze was called with explicit repo, not git origin
        mock_analyzer.analyze.assert_called_once()
        call_args = mock_analyzer.analyze.call_args
        assert call_args[0][0] == "explicit-owner"
        assert call_args[0][1] == "explicit-repo"

    def test_auto_detect_from_https_origin(
        self, cli_runner: CliRunner, mock_result: PRAnalysisResult
    ):
        """Should auto-detect repo from HTTPS git origin URL."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_result
                mock_analyzer_cls.return_value = mock_analyzer

                with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
                    mock_git.return_value = ("https-owner", "https-repo")

                    # No --repo provided, should use git origin
                    result = cli_runner.invoke(
                        main,
                        ["123"],
                        env={"GITHUB_TOKEN": "ghp_test"},
                    )

        assert result.exit_code == 0
        mock_analyzer.analyze.assert_called_once()
        call_args = mock_analyzer.analyze.call_args
        assert call_args[0][0] == "https-owner"
        assert call_args[0][1] == "https-repo"

    def test_auto_detect_from_ssh_origin(
        self, cli_runner: CliRunner, mock_result: PRAnalysisResult
    ):
        """Should auto-detect repo from SSH git origin URL."""
        with patch("goodtogo.cli.Container") as mock_container_cls:
            mock_container = MagicMock()
            mock_container_cls.create_default.return_value = mock_container

            with patch("goodtogo.cli.PRAnalyzer") as mock_analyzer_cls:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze.return_value = mock_result
                mock_analyzer_cls.return_value = mock_analyzer

                with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
                    mock_git.return_value = ("ssh-owner", "ssh-repo")

                    result = cli_runner.invoke(
                        main,
                        ["123"],
                        env={"GITHUB_TOKEN": "ghp_test"},
                    )

        assert result.exit_code == 0
        mock_analyzer.analyze.assert_called_once()
        call_args = mock_analyzer.analyze.call_args
        assert call_args[0][0] == "ssh-owner"
        assert call_args[0][1] == "ssh-repo"

    def test_error_when_no_repo_and_no_git_origin(self, cli_runner: CliRunner):
        """Should exit with error when no --repo and no git origin."""
        with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
            mock_git.return_value = None  # No git origin found

            result = cli_runner.invoke(
                main,
                ["123"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4
        assert "origin" in result.output.lower() or "repo" in result.output.lower()

    def test_error_when_not_in_git_repo(self, cli_runner: CliRunner):
        """Should exit with error when not in a git repository.

        Note: get_repo_from_git_origin catches subprocess errors and returns None,
        so when not in a git repo, it returns None rather than raising.
        """
        with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
            # Not in a git repo returns None (subprocess error is caught internally)
            mock_git.return_value = None

            result = cli_runner.invoke(
                main,
                ["123"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4
        assert "origin" in result.output.lower() or "repo" in result.output.lower()

    def test_error_when_origin_not_github(self, cli_runner: CliRunner):
        """Should exit with error when origin is not a GitHub URL."""
        with patch("goodtogo.cli.get_repo_from_git_origin") as mock_git:
            # Return None to indicate non-GitHub origin
            mock_git.return_value = None

            result = cli_runner.invoke(
                main,
                ["123"],
                env={"GITHUB_TOKEN": "ghp_test"},
            )

        assert result.exit_code == 4

    def test_help_shows_repo_is_optional(self, cli_runner: CliRunner):
        """--help should indicate that --repo is optional."""
        result = cli_runner.invoke(main, ["--help"])

        # The help text should not show --repo as required
        # or should mention auto-detection
        assert "--repo" in result.output
        # Should mention it's optional or auto-detected
        assert "auto" in result.output.lower() or "optional" in result.output.lower()


# ============================================================================
# Test: parse_github_remote_url function
# ============================================================================


class TestParseGitHubRemoteUrl:
    """Tests for parsing GitHub remote URLs."""

    def test_parse_https_url(self):
        """Should parse HTTPS GitHub URL."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("https://github.com/owner/repo.git")
        assert result == ("owner", "repo")

    def test_parse_https_url_without_git_suffix(self):
        """Should parse HTTPS GitHub URL without .git suffix."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("https://github.com/owner/repo")
        assert result == ("owner", "repo")

    def test_parse_ssh_url(self):
        """Should parse SSH GitHub URL."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("git@github.com:owner/repo.git")
        assert result == ("owner", "repo")

    def test_parse_ssh_url_without_git_suffix(self):
        """Should parse SSH GitHub URL without .git suffix."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("git@github.com:owner/repo")
        assert result == ("owner", "repo")

    def test_parse_https_with_trailing_slash(self):
        """Should handle HTTPS URL with trailing slash."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("https://github.com/owner/repo/")
        assert result == ("owner", "repo")

    def test_parse_ssh_with_trailing_slash(self):
        """Should handle SSH URL with trailing slash."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("git@github.com:owner/repo/")
        assert result == ("owner", "repo")

    def test_returns_none_for_non_github_https(self):
        """Should return None for non-GitHub HTTPS URL."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("https://gitlab.com/owner/repo.git")
        assert result is None

    def test_returns_none_for_non_github_ssh(self):
        """Should return None for non-GitHub SSH URL."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("git@gitlab.com:owner/repo.git")
        assert result is None

    def test_returns_none_for_invalid_url(self):
        """Should return None for invalid URL."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("not-a-valid-url")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """Should return None for empty string."""
        from goodtogo.cli import parse_github_remote_url

        result = parse_github_remote_url("")
        assert result is None


# ============================================================================
# Test: get_repo_from_git_origin function
# ============================================================================


class TestGetRepoFromGitOrigin:
    """Tests for get_repo_from_git_origin function."""

    def test_returns_none_when_git_command_fails(self):
        """Should return None when git command fails (not a git repo)."""
        import subprocess

        from goodtogo.cli import get_repo_from_git_origin

        with patch("goodtogo.cli.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=128,
                cmd=["git", "remote", "get-url", "origin"],
                output=b"",
                stderr=b"fatal: not a git repository",
            )

            result = get_repo_from_git_origin()

        assert result is None

    def test_parses_https_origin(self):
        """Should parse HTTPS origin URL."""
        from goodtogo.cli import get_repo_from_git_origin

        with patch("goodtogo.cli.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "https://github.com/test-owner/test-repo.git\n"
            mock_run.return_value = mock_result

            result = get_repo_from_git_origin()

        assert result == ("test-owner", "test-repo")

    def test_parses_ssh_origin(self):
        """Should parse SSH origin URL."""
        from goodtogo.cli import get_repo_from_git_origin

        with patch("goodtogo.cli.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "git@github.com:test-owner/test-repo.git\n"
            mock_run.return_value = mock_result

            result = get_repo_from_git_origin()

        assert result == ("test-owner", "test-repo")

    def test_returns_none_for_non_github_origin(self):
        """Should return None for non-GitHub origin."""
        from goodtogo.cli import get_repo_from_git_origin

        with patch("goodtogo.cli.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "https://gitlab.com/test-owner/test-repo.git\n"
            mock_run.return_value = mock_result

            result = get_repo_from_git_origin()

        assert result is None
