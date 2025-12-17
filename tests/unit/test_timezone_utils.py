from datetime import datetime, timezone, timedelta
import pytest
from utils.timezone_utils import ensure_utc_timezone, utc_now


class TestEnsureUtcTimezone:
    def test_preserves_utc_datetime(self):
        """Test that UTC datetime is returned unchanged."""
        dt = datetime(2023, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = ensure_utc_timezone(dt)

        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_adds_utc_to_naive_datetime(self):
        """Test that naive datetime gets UTC timezone added."""
        dt = datetime(2023, 6, 15, 14, 30, 0)  # naive
        result = ensure_utc_timezone(dt)

        assert result.year == 2023
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_preserves_datetime_with_timezone(self):
        """Test that datetime with existing timezone is returned as-is (no conversion)."""
        # The function does NOT convert timezones, it only adds UTC timezone if missing
        eastern_tz = timezone(timedelta(hours=-5))
        dt = datetime(2023, 6, 15, 12, 0, 0, tzinfo=eastern_tz)
        result = ensure_utc_timezone(dt)

        # The original datetime should be returned unchanged
        assert result == dt  # Same time, same timezone
        assert result.hour == 12  # Time is NOT converted to UTC
        assert result.tzinfo == eastern_tz  # Original timezone preserved

    @pytest.mark.parametrize(
        "dt",
        [
            datetime.min.replace(tzinfo=None),
            datetime.max.replace(tzinfo=None),
            datetime(1970, 1, 1),  # Unix epoch
            datetime(2038, 1, 19, 3, 14, 7),
        ],
    )
    def test_handles_edge_case_dates(self, dt):
        """Test handling of edge case datetime values."""
        result = ensure_utc_timezone(dt)
        assert result.tzinfo == timezone.utc
        # Time should be preserved for naive datetimes
        assert result.replace(tzinfo=None) == dt


class TestUtcNow:
    def test_returns_utc_datetime(self):
        """Test that utc_now returns a timezone-aware UTC datetime."""
        result = utc_now()

        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self):
        """Test that utc_now returns approximately current time."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        # Allow 1 second tolerance for slow systems
        assert before <= result <= after + timedelta(seconds=1)

    def test_consecutive_calls_increase(self):
        """Test that consecutive calls return increasing times."""
        time1 = utc_now()
        time2 = utc_now()

        # Second call should be equal or later (microseconds might differ)
        assert time2 >= time1

    def test_has_microsecond_precision(self):
        """Test that datetime includes microsecond precision."""
        result = utc_now()

        # The microsecond value should be realistic (0-999999)
        assert 0 <= result.microsecond < 1_000_000
        # Most calls should have non-zero microseconds (probabilistic test)
        results = [utc_now().microsecond for _ in range(10)]
        assert any(us != 0 for us in results)
