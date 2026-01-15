"""Error handling utilities for GoodToMerge.

This module provides secure error handling that prevents sensitive information
like GitHub tokens and credentials from leaking in error messages, logs, or
exception tracebacks.
"""

from __future__ import annotations

import re
from typing import Optional


class RedactedError(Exception):
    """Exception with sensitive data redacted from the message.

    This exception wraps an original exception while redacting any sensitive
    information (tokens, credentials, etc.) from the error message.

    Attributes:
        original: The original exception that was redacted, if any.

    Example:
        >>> original = Exception("Failed with token ghp_secret123")
        >>> redacted = RedactedError("Failed with token <REDACTED_TOKEN>", original)
        >>> str(redacted)
        'Failed with token <REDACTED_TOKEN>'
        >>> redacted.original
        Exception('Failed with token ghp_secret123')
    """

    def __init__(self, message: str, original: Optional[Exception] = None) -> None:
        """Initialize a RedactedError.

        Args:
            message: The redacted error message (should already be sanitized).
            original: The original exception before redaction.
        """
        self.original = original
        super().__init__(message)


def redact_error(error: Exception) -> RedactedError:
    """Redact sensitive information from an exception's error message.

    This function creates a new RedactedError with all sensitive patterns
    removed from the message. The original exception is preserved in the
    `original` attribute for debugging purposes.

    Redacted patterns include:
        - GitHub Personal Access Tokens (ghp_*)
        - GitHub OAuth Tokens (gho_*)
        - GitHub PAT tokens (github_pat_*)
        - URL credentials (://user:pass@host)
        - Authorization headers (Authorization: Bearer/token ...)

    Args:
        error: The exception to redact.

    Returns:
        A RedactedError with sensitive data replaced with placeholders.

    Example:
        >>> error = Exception("Auth failed: ghp_abc123xyz789")
        >>> redacted = redact_error(error)
        >>> "ghp_abc123xyz789" in str(redacted)
        False
        >>> "<REDACTED_TOKEN>" in str(redacted)
        True
        >>> redacted.original is error
        True
    """
    message = str(error)

    # Redact GitHub tokens (ghp_, gho_, github_pat_)
    # Pattern: prefix followed by alphanumeric characters and underscores
    message = re.sub(
        r"(ghp_|gho_|github_pat_)[a-zA-Z0-9_]+",
        "<REDACTED_TOKEN>",
        message,
    )

    # Redact URL credentials (://user:pass@host)
    # Pattern: :// followed by non-colon chars, colon, non-@ chars, @
    message = re.sub(
        r"://[^:]+:[^@]+@",
        "://<REDACTED>@",
        message,
    )

    # Redact Authorization headers
    # Pattern: Authorization (with optional quotes/colons) followed by Bearer/token and the value
    message = re.sub(
        r'(Authorization["\']?\s*:\s*["\']?)(Bearer\s+)?[a-zA-Z0-9_-]+',
        r"\1<REDACTED>",
        message,
        flags=re.IGNORECASE,
    )

    return RedactedError(message, original=error)
