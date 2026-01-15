"""Tests for token redaction and protection.

This module tests that GitHub tokens and sensitive credentials are properly
redacted from error messages, string representations, and other outputs.

Coverage target: 100% branch coverage on all token handling.
"""

from __future__ import annotations

import pytest

from goodtomerge.adapters.github import GitHubAdapter
from goodtomerge.core.errors import redact_error, RedactedError


class TestGitHubAdapterTokenProtection:
    """Verify tokens never leak through repr/str."""

    def test_repr_redacts_token(self) -> None:
        """GitHubAdapter __repr__ must not expose the token."""
        adapter = GitHubAdapter(token="ghp_secret123456789")
        repr_output = repr(adapter)
        assert "ghp_secret123456789" not in repr_output
        assert "<redacted>" in repr_output.lower()

    def test_str_redacts_token(self) -> None:
        """GitHubAdapter __str__ must not expose the token."""
        adapter = GitHubAdapter(token="ghp_secret123456789")
        str_output = str(adapter)
        assert "ghp_secret123456789" not in str_output
        assert "<redacted>" in str_output.lower()

    def test_token_not_in_public_attributes(self) -> None:
        """Token should only be in private attribute _token."""
        adapter = GitHubAdapter(token="ghp_secret123456789")
        # The token should be stored in _token (private)
        # Verify it's not accidentally exposed elsewhere
        public_attrs = [attr for attr in dir(adapter) if not attr.startswith("_")]
        for attr in public_attrs:
            attr_val = getattr(adapter, attr)
            if isinstance(attr_val, str):
                assert "ghp_secret123456789" not in attr_val

    def test_different_token_formats_redacted_in_repr(self) -> None:
        """All GitHub token formats should be hidden in repr."""
        for token in ["ghp_abc123", "gho_xyz789", "github_pat_ABC123_def"]:
            adapter = GitHubAdapter(token=token)
            assert token not in repr(adapter)
            assert token not in str(adapter)


class TestErrorRedaction:
    """Verify error messages redact sensitive patterns."""

    # --- GitHub Personal Access Token patterns ---
    @pytest.mark.parametrize(
        "token_prefix",
        [
            "ghp_",  # GitHub Personal Access Token
            "gho_",  # GitHub OAuth Token
            "github_pat_",  # GitHub PAT (newer format)
        ],
    )
    def test_github_token_patterns_redacted(self, token_prefix: str) -> None:
        """All GitHub token prefixes must be redacted."""
        token = f"{token_prefix}abcdefghijklmnop1234567890"
        error = Exception(f"Authentication failed: {token}")
        redacted = redact_error(error)
        assert token not in str(redacted)
        assert "<REDACTED_TOKEN>" in str(redacted)

    def test_ghp_token_in_url_redacted(self) -> None:
        """Token in URL query params must be redacted."""
        error = Exception("Failed: https://api.github.com?token=ghp_secret123")
        redacted = redact_error(error)
        assert "ghp_secret123" not in str(redacted)

    def test_gho_token_redacted(self) -> None:
        """gho_ tokens must be redacted."""
        error = Exception("OAuth token gho_abc123xyz789 is invalid")
        redacted = redact_error(error)
        assert "gho_abc123xyz789" not in str(redacted)
        assert "<REDACTED_TOKEN>" in str(redacted)

    def test_github_pat_token_redacted(self) -> None:
        """github_pat_ tokens must be redacted."""
        error = Exception("PAT github_pat_22A_verylongtoken123 expired")
        redacted = redact_error(error)
        assert "github_pat_22A_verylongtoken123" not in str(redacted)
        assert "<REDACTED_TOKEN>" in str(redacted)

    def test_multiple_tokens_in_message_all_redacted(self) -> None:
        """Multiple tokens in a single message should all be redacted."""
        error = Exception(
            "Tokens ghp_first123 and gho_second456 and github_pat_third789 all invalid"
        )
        redacted = redact_error(error)
        assert "ghp_first123" not in str(redacted)
        assert "gho_second456" not in str(redacted)
        assert "github_pat_third789" not in str(redacted)
        assert str(redacted).count("<REDACTED_TOKEN>") == 3

    # --- URL credential patterns ---
    def test_url_basic_auth_redacted(self) -> None:
        """user:pass@host pattern in URL must be redacted."""
        error = Exception("Failed to connect: https://user:ghp_secret@github.com/repo")
        redacted = redact_error(error)
        assert "ghp_secret" not in str(redacted)
        assert "<REDACTED>" in str(redacted)

    def test_url_oauth_token_in_password_redacted(self) -> None:
        """OAuth token used as password in URL must be redacted."""
        error = Exception("Connection: https://x-access-token:gho_token123@api.github.com")
        redacted = redact_error(error)
        assert "gho_token123" not in str(redacted)

    def test_url_credentials_with_special_chars(self) -> None:
        """URL credentials with special characters should be redacted."""
        error = Exception("Failed: https://user:p@ssw0rd!@example.com/path")
        redacted = redact_error(error)
        assert "p@ssw0rd!" not in str(redacted)
        assert "://<REDACTED>@" in str(redacted)

    # --- Authorization header patterns ---
    def test_authorization_bearer_redacted(self) -> None:
        """Authorization: Bearer <token> must be redacted."""
        error = Exception('Header: {"Authorization": "Bearer ghp_secret123"}')
        redacted = redact_error(error)
        assert "ghp_secret123" not in str(redacted)

    def test_authorization_token_redacted(self) -> None:
        """Authorization: token <token> must be redacted."""
        error = Exception("Authorization: token ghp_verysecret")
        redacted = redact_error(error)
        assert "ghp_verysecret" not in str(redacted)

    def test_authorization_header_case_insensitive(self) -> None:
        """Authorization header redaction should be case insensitive."""
        error = Exception("AUTHORIZATION: Bearer secrettoken123")
        redacted = redact_error(error)
        assert "secrettoken123" not in str(redacted)

    def test_authorization_with_various_formats(self) -> None:
        """Various Authorization header formats should be redacted."""
        test_cases = [
            "Authorization: Bearer abc123",
            'Authorization: "abc123"',
            "authorization: bearer xyz789",
            "Authorization:abc456",
        ]
        for case in test_cases:
            error = Exception(case)
            redacted = redact_error(error)
            # The token portion should be redacted
            assert "<REDACTED>" in str(redacted)

    # --- Verify original exception preserved ---
    def test_original_exception_preserved(self) -> None:
        """The original exception should be accessible via .original attribute."""
        original = ValueError("ghp_secret123 is invalid")
        redacted = redact_error(original)
        assert redacted.original is original
        assert isinstance(redacted.original, ValueError)

    def test_original_exception_type_preserved(self) -> None:
        """Original exception type should be preserved in .original."""
        original = ConnectionError("Failed with token gho_secret456")
        redacted = redact_error(original)
        assert isinstance(redacted.original, ConnectionError)
        assert "gho_secret456" in str(redacted.original)  # Original has it
        assert "gho_secret456" not in str(redacted)  # Redacted doesn't

    def test_redacted_error_is_exception(self) -> None:
        """RedactedError should be an Exception subclass."""
        redacted = redact_error(Exception("test"))
        assert isinstance(redacted, Exception)
        assert isinstance(redacted, RedactedError)

    # --- Edge cases ---
    def test_empty_error_message(self) -> None:
        """Empty error message should be handled gracefully."""
        error = Exception("")
        redacted = redact_error(error)
        assert str(redacted) == ""
        assert redacted.original is error

    def test_no_sensitive_data_unchanged(self) -> None:
        """Messages without sensitive data should remain unchanged."""
        original_msg = "Generic error: connection timeout"
        error = Exception(original_msg)
        redacted = redact_error(error)
        assert str(redacted) == original_msg

    def test_token_like_but_not_token_preserved(self) -> None:
        """Strings that look like tokens but aren't shouldn't be over-redacted."""
        # "ghp" alone without underscore should not be redacted
        error = Exception("The ghp function failed")
        redacted = redact_error(error)
        assert "ghp function" in str(redacted)

    def test_partial_token_prefix_not_redacted(self) -> None:
        """Partial token prefixes without full pattern should be preserved."""
        error = Exception("ghp_ by itself is not a token")
        redacted = redact_error(error)
        # The pattern requires characters after the prefix
        assert "ghp_" in str(redacted)
