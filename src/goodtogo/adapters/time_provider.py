"""Time provider implementations.

This module provides implementations of the TimeProvider interface:
- SystemTimeProvider: Uses real system time (for production)
- MockTimeProvider: Controllable time for deterministic tests

Using dependency injection for time eliminates flaky tests caused by
time.sleep() calls and non-deterministic time.time() values.
"""

from __future__ import annotations

import time

from goodtogo.core.interfaces import TimeProvider


class SystemTimeProvider(TimeProvider):
    """Real system time provider for production use.

    This implementation delegates to the standard library time module.
    Use this in production code where real time behavior is needed.
    """

    def now(self) -> float:
        """Get current time as Unix timestamp.

        Returns:
            Current time as seconds since epoch (float).
        """
        return time.time()

    def now_int(self) -> int:
        """Get current time as Unix timestamp (integer).

        Returns:
            Current time as seconds since epoch (int).
        """
        return int(time.time())

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified duration.

        Args:
            seconds: Duration to sleep in seconds.
        """
        time.sleep(seconds)


class MockTimeProvider(TimeProvider):
    """Controllable time provider for deterministic testing.

    This implementation allows tests to control time precisely:
    - Set an initial time
    - Advance time by specific amounts
    - Sleep advances simulated time instantly (no real waiting)

    Example:
        >>> time_provider = MockTimeProvider(start=1000.0)
        >>> time_provider.now()
        1000.0
        >>> time_provider.advance(60)
        >>> time_provider.now()
        1060.0
        >>> time_provider.sleep(30)  # Instant, no real waiting
        >>> time_provider.now()
        1090.0
    """

    def __init__(self, start: float = 0.0) -> None:
        """Initialize with a starting time.

        Args:
            start: Initial time value (seconds since epoch).
                   Defaults to 0.0 for simplicity in tests.
        """
        self._current_time = start

    def now(self) -> float:
        """Get current simulated time.

        Returns:
            Current simulated time as float.
        """
        return self._current_time

    def now_int(self) -> int:
        """Get current simulated time as integer.

        Returns:
            Current simulated time as int.
        """
        return int(self._current_time)

    def sleep(self, seconds: float) -> None:
        """Advance simulated time instantly.

        Unlike real sleep, this returns immediately after
        advancing the internal time counter.

        Args:
            seconds: Duration to advance time by.
        """
        self._current_time += seconds

    def advance(self, seconds: float) -> None:
        """Advance simulated time by the specified amount.

        This is an alias for sleep() but with clearer intent
        when used in test setup.

        Args:
            seconds: Duration to advance time by.
        """
        self._current_time += seconds

    def set_time(self, timestamp: float) -> None:
        """Set simulated time to a specific value.

        Args:
            timestamp: New time value (seconds since epoch).
        """
        self._current_time = timestamp
