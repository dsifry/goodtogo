"""Tests for TimeProvider implementations.

This module tests both SystemTimeProvider (real time) and MockTimeProvider
(controllable time for deterministic tests).
"""

from __future__ import annotations

import time

from goodtogo.adapters.time_provider import MockTimeProvider, SystemTimeProvider
from goodtogo.core.interfaces import TimeProvider


class TestSystemTimeProvider:
    """Tests for SystemTimeProvider."""

    def test_implements_time_provider_interface(self) -> None:
        """SystemTimeProvider should implement TimeProvider interface."""
        provider = SystemTimeProvider()
        assert isinstance(provider, TimeProvider)

    def test_now_returns_current_time(self) -> None:
        """now() should return current time as float."""
        provider = SystemTimeProvider()
        before = time.time()
        result = provider.now()
        after = time.time()
        assert before <= result <= after

    def test_now_int_returns_current_time_as_integer(self) -> None:
        """now_int() should return current time as integer."""
        provider = SystemTimeProvider()
        before = int(time.time())
        result = provider.now_int()
        after = int(time.time())
        assert before <= result <= after
        assert isinstance(result, int)

    def test_sleep_waits_for_duration(self) -> None:
        """sleep() should wait for the specified duration."""
        provider = SystemTimeProvider()
        before = time.monotonic()
        provider.sleep(0.01)  # Sleep for 10ms
        after = time.monotonic()
        assert after - before >= 0.01


class TestMockTimeProvider:
    """Tests for MockTimeProvider."""

    def test_implements_time_provider_interface(self) -> None:
        """MockTimeProvider should implement TimeProvider interface."""
        provider = MockTimeProvider()
        assert isinstance(provider, TimeProvider)

    def test_default_start_time_is_zero(self) -> None:
        """Default start time should be 0.0."""
        provider = MockTimeProvider()
        assert provider.now() == 0.0

    def test_custom_start_time(self) -> None:
        """Should respect custom start time."""
        provider = MockTimeProvider(start=1000.0)
        assert provider.now() == 1000.0

    def test_now_returns_float(self) -> None:
        """now() should return float."""
        provider = MockTimeProvider(start=1234.5)
        assert provider.now() == 1234.5
        assert isinstance(provider.now(), float)

    def test_now_int_returns_integer(self) -> None:
        """now_int() should return integer."""
        provider = MockTimeProvider(start=1234.5)
        assert provider.now_int() == 1234
        assert isinstance(provider.now_int(), int)

    def test_sleep_advances_time_instantly(self) -> None:
        """sleep() should advance time without real waiting."""
        provider = MockTimeProvider(start=1000.0)
        before = time.monotonic()
        provider.sleep(3600)  # "Sleep" for 1 hour
        after = time.monotonic()

        # Real time should barely have passed (tolerance for busy CI systems)
        assert after - before < 0.5

        # But mock time should have advanced
        assert provider.now() == 4600.0

    def test_advance_increases_time(self) -> None:
        """advance() should increase time by specified amount."""
        provider = MockTimeProvider(start=1000.0)
        provider.advance(60)
        assert provider.now() == 1060.0
        provider.advance(30)
        assert provider.now() == 1090.0

    def test_set_time_sets_specific_value(self) -> None:
        """set_time() should set time to a specific value."""
        provider = MockTimeProvider(start=1000.0)
        provider.set_time(5000.0)
        assert provider.now() == 5000.0

    def test_set_time_can_go_backwards(self) -> None:
        """set_time() should allow going backwards in time."""
        provider = MockTimeProvider(start=1000.0)
        provider.advance(500)
        assert provider.now() == 1500.0
        provider.set_time(100.0)
        assert provider.now() == 100.0

    def test_multiple_operations(self) -> None:
        """Multiple operations should work correctly together."""
        provider = MockTimeProvider(start=0.0)
        provider.advance(100)
        provider.sleep(50)
        provider.set_time(1000)
        provider.advance(1)
        assert provider.now() == 1001.0
        assert provider.now_int() == 1001
