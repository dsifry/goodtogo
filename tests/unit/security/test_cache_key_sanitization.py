"""Tests for cache key sanitization.

This module tests that cache keys are safely constructed and that special
characters that could cause cache key collisions or glob pattern issues
are properly rejected.

Coverage target: 100% branch coverage on cache key construction.
"""

from __future__ import annotations

import pytest

from goodtomerge.core.validation import build_cache_key


class TestValidCacheKeyConstruction:
    """Verify valid cache keys are properly constructed."""

    def test_valid_parts_create_key(self) -> None:
        """Standard parts should create a colon-delimited key."""
        key = build_cache_key("pr", "myorg", "myrepo", "123", "meta")
        assert key == "pr:myorg:myrepo:123:meta"

    def test_numeric_parts_converted_to_string(self) -> None:
        """Numeric parts should be converted to strings."""
        key = build_cache_key("pr", "org", "repo", 123, "ci")
        assert key == "pr:org:repo:123:ci"

    def test_single_part_creates_key(self) -> None:
        """Single part should create a key without delimiter."""
        key = build_cache_key("simple")
        assert key == "simple"

    def test_two_parts_creates_key(self) -> None:
        """Two parts should create key with one delimiter."""
        key = build_cache_key("prefix", "suffix")
        assert key == "prefix:suffix"

    def test_mixed_string_and_int_parts(self) -> None:
        """Mixed string and integer parts should work."""
        key = build_cache_key("pr", "org", "repo", 456, "thread", 789)
        assert key == "pr:org:repo:456:thread:789"

    def test_alphanumeric_parts(self) -> None:
        """Alphanumeric parts should be accepted."""
        key = build_cache_key("prefix123", "abc456def", "789")
        assert key == "prefix123:abc456def:789"

    def test_parts_with_hyphen(self) -> None:
        """Parts with hyphens should be accepted."""
        key = build_cache_key("pr", "my-org", "my-repo", "123")
        assert key == "pr:my-org:my-repo:123"

    def test_parts_with_underscore(self) -> None:
        """Parts with underscores should be accepted."""
        key = build_cache_key("pr", "my_org", "my_repo", "123")
        assert key == "pr:my_org:my_repo:123"

    def test_parts_with_dot(self) -> None:
        """Parts with dots should be accepted."""
        key = build_cache_key("pr", "my.org", "my.repo", "123")
        assert key == "pr:my.org:my.repo:123"


class TestColonRejection:
    """Verify colons in parts are rejected (delimiter collision)."""

    def test_colon_in_owner_raises(self) -> None:
        """Colons would corrupt key structure."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my:org", "repo", "123")

    def test_colon_in_repo_raises(self) -> None:
        """Colons in repo name should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "my:repo", "123")

    def test_colon_in_suffix_raises(self) -> None:
        """Colons in suffix should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "123", "meta:data")

    def test_colon_in_prefix_raises(self) -> None:
        """Colons in prefix should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr:invalid", "org", "repo", "123")

    def test_multiple_colons_raises(self) -> None:
        """Multiple colons should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "a:b:c", "repo", "123")


class TestAsteriskRejection:
    """Verify asterisks in parts are rejected (glob pattern safety)."""

    def test_asterisk_in_owner_raises(self) -> None:
        """Asterisks could cause unintended pattern matches."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my*org", "repo", "123")

    def test_asterisk_in_repo_raises(self) -> None:
        """Asterisks in repo name should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "*repo", "123")

    def test_asterisk_alone_raises(self) -> None:
        """Wildcard injection attempt should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "*")

    def test_asterisk_at_end_raises(self) -> None:
        """Trailing asterisk should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo*", "123")

    def test_multiple_asterisks_raises(self) -> None:
        """Multiple asterisks should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "*org*", "repo", "123")


class TestQuestionMarkRejection:
    """Verify question marks in parts are rejected (glob pattern safety)."""

    def test_question_mark_in_owner_raises(self) -> None:
        """Question marks are glob single-char wildcards."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my?org", "repo", "123")

    def test_question_mark_in_repo_raises(self) -> None:
        """Question marks in repo name should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo?name", "123")

    def test_question_mark_alone_raises(self) -> None:
        """Single question mark should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "?", "123")

    def test_multiple_question_marks_raises(self) -> None:
        """Multiple question marks should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo???", "123")


class TestEmptyPartRejection:
    """Verify empty parts are rejected."""

    def test_empty_part_in_middle_raises(self) -> None:
        """Empty parts would create malformed keys."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("pr", "org", "", "123")

    def test_empty_part_at_start_raises(self) -> None:
        """Empty part at start should be rejected."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("", "org", "repo", "123")

    def test_empty_part_at_end_raises(self) -> None:
        """Empty part at end should be rejected."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("pr", "org", "repo", "")

    def test_all_empty_parts_raises(self) -> None:
        """All empty parts should be rejected."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("", "", "")

    def test_whitespace_only_part_treated_as_non_empty(self) -> None:
        """Whitespace-only strings are technically non-empty but may be undesirable."""
        # Note: The current implementation allows whitespace-only strings
        # as they don't contain the forbidden characters
        # This test documents current behavior
        key = build_cache_key("pr", "org", "   ", "123")
        assert key == "pr:org:   :123"


class TestCombinedSpecialCharacterRejection:
    """Verify combined injection attempts are rejected."""

    def test_combined_special_chars_raises(self) -> None:
        """Multiple special characters should all be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org:*?", "repo", "123")

    def test_colon_and_asterisk_raises(self) -> None:
        """Colon and asterisk combination should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org:*", "repo", "123")

    def test_asterisk_and_question_raises(self) -> None:
        """Asterisk and question mark combination should be rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org*?", "repo", "123")


class TestDefenseInDepth:
    """Verify defense-in-depth validation works."""

    def test_validates_even_if_inputs_already_validated(self) -> None:
        """
        Even if caller validated inputs, build_cache_key should
        still reject special characters (defense in depth).
        """
        # Simulating a bug where validation was bypassed
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo:injection", "123")

    def test_all_parts_are_validated(self) -> None:
        """Every part should be validated, not just some."""
        # Test that validation happens on every position
        test_cases = [
            ("*invalid", "org", "repo", "123"),
            ("pr", "*invalid", "repo", "123"),
            ("pr", "org", "*invalid", "123"),
            ("pr", "org", "repo", "*"),
        ]
        for parts in test_cases:
            with pytest.raises(ValueError, match="Invalid character"):
                build_cache_key(*parts)

    def test_validation_order_does_not_matter(self) -> None:
        """Invalid characters should be caught regardless of position."""
        # First invalid char is in last position
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("a", "b", "c", "d*")

        # First invalid char is in first position
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("*a", "b", "c", "d")
