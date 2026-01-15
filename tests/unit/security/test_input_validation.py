"""Tests for input validation boundaries.

Coverage target: 100% branch coverage on all validation functions.

This module contains comprehensive security tests for input validation functions,
including boundary testing for GitHub identifiers, PR numbers, and cache key
construction. All test cases are derived from the Security Test Specifications
section of the GoodToMerge CLI Design document.
"""

import pytest

from goodtomerge.core.validation import (
    build_cache_key,
    validate_github_identifier,
    validate_pr_number,
)


class TestGitHubIdentifierValidation:
    """Boundary tests for validate_github_identifier()."""

    # --- Empty/Null boundaries ---
    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_github_identifier("", "owner")

    def test_whitespace_only_raises_value_error(self):
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("   ", "owner")

    # --- Length boundaries (GitHub max: 39 characters) ---
    def test_single_character_valid(self):
        assert validate_github_identifier("a", "owner") == "a"

    def test_39_characters_valid(self):
        valid_39 = "a" * 39
        assert validate_github_identifier(valid_39, "owner") == valid_39

    def test_40_characters_raises_value_error(self):
        invalid_40 = "a" * 40
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_github_identifier(invalid_40, "owner")

    # --- Character boundaries ---
    def test_alphanumeric_only_valid(self):
        assert validate_github_identifier("abc123", "owner") == "abc123"

    def test_with_hyphen_valid(self):
        assert validate_github_identifier("my-org", "owner") == "my-org"

    def test_with_underscore_valid(self):
        assert validate_github_identifier("my_org", "owner") == "my_org"

    def test_with_dot_valid(self):
        assert validate_github_identifier("my.org", "owner") == "my.org"

    def test_starts_with_hyphen_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("-invalid", "owner")

    def test_ends_with_hyphen_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("invalid-", "owner")

    def test_starts_with_dot_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier(".invalid", "owner")

    # --- Injection attempt boundaries ---
    def test_slash_raises_value_error(self):
        """Path traversal attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("../etc/passwd", "owner")

    def test_semicolon_raises_value_error(self):
        """Command injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid;rm -rf", "owner")

    def test_backtick_raises_value_error(self):
        """Command substitution attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid`id`", "owner")

    def test_null_byte_raises_value_error(self):
        """Null byte injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid\x00evil", "owner")

    # --- Additional edge cases ---
    def test_two_character_identifier_valid(self):
        """Two character identifier (boundary for middle content)."""
        assert validate_github_identifier("ab", "owner") == "ab"

    def test_mixed_case_valid(self):
        """Mixed case alphanumeric identifier."""
        assert validate_github_identifier("MyOrg123", "owner") == "MyOrg123"

    def test_multiple_dots_hyphens_underscores_valid(self):
        """Multiple special characters in middle."""
        assert validate_github_identifier("my.org-name_test", "owner") == "my.org-name_test"

    def test_ends_with_dot_raises(self):
        """Ends with dot should fail (not alphanumeric)."""
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("invalid.", "owner")

    def test_ends_with_underscore_raises(self):
        """Ends with underscore should fail (not alphanumeric)."""
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("invalid_", "owner")

    def test_starts_with_underscore_raises(self):
        """Starts with underscore should fail (not alphanumeric)."""
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("_invalid", "owner")

    def test_numeric_only_valid(self):
        """Numeric-only identifier is valid."""
        assert validate_github_identifier("123456", "owner") == "123456"

    def test_field_name_in_error_message(self):
        """Field name appears in error message for context."""
        with pytest.raises(ValueError, match="repo"):
            validate_github_identifier("", "repo")

    def test_path_traversal_double_dots(self):
        """Double dots for path traversal."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("foo/../bar", "owner")

    def test_newline_injection_raises(self):
        """Newline injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid\nevil", "owner")

    def test_carriage_return_injection_raises(self):
        """Carriage return injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid\revil", "owner")

    def test_tab_injection_raises(self):
        """Tab injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid\tevil", "owner")


class TestPRNumberValidation:
    """Boundary tests for validate_pr_number()."""

    # --- Zero boundary ---
    def test_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_pr_number(0)

    def test_negative_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_pr_number(-1)

    # --- Positive boundary ---
    def test_one_valid(self):
        assert validate_pr_number(1) == 1

    # --- Upper boundary (int32 max) ---
    def test_int32_max_valid(self):
        assert validate_pr_number(2147483647) == 2147483647

    def test_int32_max_plus_one_raises(self):
        with pytest.raises(ValueError, match="exceeds maximum value"):
            validate_pr_number(2147483648)

    # --- Additional edge cases ---
    def test_large_negative_raises_value_error(self):
        """Large negative number should fail."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_pr_number(-2147483648)

    def test_typical_pr_number_valid(self):
        """Typical PR number in normal range."""
        assert validate_pr_number(123) == 123
        assert validate_pr_number(9999) == 9999

    def test_large_pr_number_valid(self):
        """Large but valid PR number."""
        assert validate_pr_number(1000000000) == 1000000000


class TestCacheKeySanitization:
    """Verify cache keys are safely constructed."""

    # --- Valid key construction ---
    def test_valid_parts_create_key(self):
        key = build_cache_key("pr", "myorg", "myrepo", "123", "meta")
        assert key == "pr:myorg:myrepo:123:meta"

    def test_numeric_parts_converted_to_string(self):
        key = build_cache_key("pr", "org", "repo", 123, "ci")
        assert key == "pr:org:repo:123:ci"

    # --- Colon rejection (delimiter collision) ---
    def test_colon_in_owner_raises(self):
        """Colons would corrupt key structure."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my:org", "repo", "123")

    def test_colon_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "my:repo", "123")

    def test_colon_in_suffix_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "123", "meta:data")

    # --- Asterisk rejection (glob pattern safety) ---
    def test_asterisk_in_owner_raises(self):
        """Asterisks could cause unintended pattern matches."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my*org", "repo", "123")

    def test_asterisk_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "*repo", "123")

    def test_asterisk_alone_raises(self):
        """Wildcard injection attempt."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "*")

    # --- Question mark rejection (glob pattern safety) ---
    def test_question_mark_in_owner_raises(self):
        """Question marks are glob single-char wildcards."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my?org", "repo", "123")

    def test_question_mark_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo?name", "123")

    # --- Combined injection attempts ---
    def test_combined_special_chars_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org:*?", "repo", "123")

    # --- Empty parts ---
    def test_empty_part_in_middle_raises(self):
        """Empty parts would create malformed keys."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("pr", "org", "", "123")

    # --- Pre-validated inputs (defense in depth) ---
    def test_validates_even_if_inputs_already_validated(self):
        """
        Even if caller validated inputs, build_cache_key should
        still reject special characters (defense in depth).
        """
        # Simulating a bug where validation was bypassed
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo:injection", "123")

    # --- Additional edge cases ---
    def test_single_part_valid(self):
        """Single part cache key."""
        key = build_cache_key("prefix")
        assert key == "prefix"

    def test_two_parts_valid(self):
        """Two part cache key."""
        key = build_cache_key("pr", "meta")
        assert key == "pr:meta"

    def test_many_parts_valid(self):
        """Many parts cache key."""
        key = build_cache_key("a", "b", "c", "d", "e", "f")
        assert key == "a:b:c:d:e:f"

    def test_empty_first_part_raises(self):
        """Empty first part should fail."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("", "org", "repo", "123")

    def test_empty_last_part_raises(self):
        """Empty last part should fail."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("pr", "org", "repo", "")

    def test_colon_at_start_of_part_raises(self):
        """Colon at start of part."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", ":org", "repo", "123")

    def test_colon_at_end_of_part_raises(self):
        """Colon at end of part."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org:", "repo", "123")

    def test_asterisk_at_end_raises(self):
        """Asterisk at end of part."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo*", "123")

    def test_question_mark_at_start_raises(self):
        """Question mark at start of part."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "?repo", "123")

    def test_integer_zero_converted_to_string(self):
        """Integer zero is valid and converted to string."""
        # Note: This is different from empty string
        key = build_cache_key("pr", "org", "repo", 0)
        assert key == "pr:org:repo:0"

    def test_hyphen_in_parts_valid(self):
        """Hyphens are allowed in parts."""
        key = build_cache_key("pr", "my-org", "my-repo", "123")
        assert key == "pr:my-org:my-repo:123"

    def test_underscore_in_parts_valid(self):
        """Underscores are allowed in parts."""
        key = build_cache_key("pr", "my_org", "my_repo", "123")
        assert key == "pr:my_org:my_repo:123"

    def test_dot_in_parts_valid(self):
        """Dots are allowed in parts."""
        key = build_cache_key("pr", "my.org", "my.repo", "123")
        assert key == "pr:my.org:my.repo:123"
