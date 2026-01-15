"""Input validation utilities for GoodToMerge.

This module provides validation functions for all external inputs to ensure
security and correctness. All GitHub identifiers, PR numbers, and cache keys
are validated before use.

Security: These functions implement defense-in-depth validation. Even if
callers have pre-validated inputs, these functions perform additional checks
to prevent injection attacks and ensure data integrity.
"""

from __future__ import annotations

import re

# GitHub identifier pattern: alphanumeric, dots, hyphens, underscores
# Must start and end with alphanumeric
# Maximum length is 39 characters (GitHub's limit)
GITHUB_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]{0,37}[a-zA-Z0-9])?$")


def validate_github_identifier(value: str, field_name: str) -> str:
    """Validate GitHub owner/repo name format.

    GitHub identifiers (usernames, organization names, repository names) must:
    - Be non-empty
    - Be at most 39 characters long
    - Contain only alphanumeric characters, dots, hyphens, and underscores
    - Start and end with an alphanumeric character

    Args:
        value: The identifier value to validate.
        field_name: The name of the field being validated (for error messages).

    Returns:
        The validated identifier (unchanged if valid).

    Raises:
        ValueError: If validation fails with a descriptive error message.

    Examples:
        >>> validate_github_identifier("my-org", "owner")
        'my-org'
        >>> validate_github_identifier("my_repo.name", "repo")
        'my_repo.name'
        >>> validate_github_identifier("", "owner")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        ValueError: owner cannot be empty
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) > 39:  # GitHub max length
        raise ValueError(f"{field_name} exceeds maximum length (39 chars)")

    if not GITHUB_ID_PATTERN.match(value):
        raise ValueError(
            f"{field_name} contains invalid characters. "
            "Must be alphanumeric with ._- allowed, "
            "starting and ending with alphanumeric."
        )

    return value


def validate_pr_number(value: int) -> int:
    """Validate PR number is a positive integer within bounds.

    PR numbers must be:
    - Greater than zero (positive)
    - At most 2147483647 (max int32 value)

    Args:
        value: The PR number to validate.

    Returns:
        The validated PR number (unchanged if valid).

    Raises:
        ValueError: If the PR number is not positive or exceeds maximum value.

    Examples:
        >>> validate_pr_number(123)
        123
        >>> validate_pr_number(0)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        ValueError: PR number must be positive
    """
    if value <= 0:
        raise ValueError("PR number must be positive")
    if value > 2147483647:  # Max int32
        raise ValueError("PR number exceeds maximum value")
    return value


def build_cache_key(*parts: str) -> str:
    """Build a cache key from validated parts.

    Constructs a colon-delimited cache key from the provided parts.
    This function performs defense-in-depth validation to ensure that
    special characters that could cause cache key collisions or glob
    pattern issues are rejected.

    Rejected characters:
    - Colon (:) - Used as the key delimiter
    - Asterisk (*) - Glob wildcard that could cause unintended pattern matches
    - Question mark (?) - Glob single-character wildcard

    All parts must be pre-validated via validate_github_identifier()
    or validate_pr_number() before calling this function, but this
    function still performs validation as a defense-in-depth measure.

    Args:
        *parts: Variable number of string parts to join into a cache key.
                Each part will be converted to string if not already.

    Returns:
        A colon-delimited cache key string.

    Raises:
        ValueError: If any part contains invalid characters (colon, asterisk,
                   question mark) or is empty.

    Examples:
        >>> build_cache_key("pr", "myorg", "myrepo", "123", "meta")
        'pr:myorg:myrepo:123:meta'
        >>> build_cache_key("pr", "org", "repo", 456, "ci")
        'pr:org:repo:456:ci'
        >>> build_cache_key("pr", "my:org", "repo", "123")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        ValueError: Invalid character in cache key part: my:org
    """
    # Double-check no special characters that could cause issues
    for part in parts:
        str_part = str(part)
        if not str_part:
            raise ValueError("Cache key parts cannot be empty")
        if ":" in str_part or "*" in str_part or "?" in str_part:
            raise ValueError(f"Invalid character in cache key part: {part}")

    return ":".join(str(p) for p in parts)
