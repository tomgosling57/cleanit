
import os
from datetime import datetime, timezone, timedelta
import zoneinfo


def test_today_in_app_tz() -> None:
    """Test that today_in_app_tz returns the correct date in the app timezone."""
    from utils.timezone import today_in_app_tz, to_app_tz, utc_now
    app_today = today_in_app_tz()
    expected_today = to_app_tz(utc_now()).date()
    assert app_today == expected_today
    
    assert os.getenv('APP_TIMEZONE') == 'Australia/Melbourne'


def test_get_app_timezone() -> None:
    """Test that get_app_timezone returns the correct timezone."""
    from utils.timezone import get_app_timezone
    
    # The environment should be set to Australia/Melbourne in tests
    app_tz = get_app_timezone()
    assert isinstance(app_tz, zoneinfo.ZoneInfo)
    assert str(app_tz) == 'Australia/Melbourne'
    
    # Test that invalid timezone falls back to UTC
    original_tz = os.environ.get('APP_TIMEZONE')
    os.environ['APP_TIMEZONE'] = 'Invalid/Timezone'
    
    # Import again to get fresh function with new environment
    import importlib
    import utils.timezone
    importlib.reload(utils.timezone)
    from utils.timezone import get_app_timezone as get_app_timezone_reloaded
    
    # Should fall back to UTC with warning
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tz = get_app_timezone_reloaded()
        assert len(w) == 1
        assert "Invalid timezone" in str(w[0].message)
        assert str(tz) == 'UTC'
    
    # Restore original timezone
    if original_tz:
        os.environ['APP_TIMEZONE'] = original_tz
    else:
        del os.environ['APP_TIMEZONE']
    
    # Reload again to restore original behavior
    importlib.reload(utils.timezone)


def test_utc_now() -> None:
    """Test that utc_now returns a timezone-aware UTC datetime."""
    from utils.timezone import utc_now
    
    now = utc_now()
    assert now.tzinfo == timezone.utc
    assert now.tzinfo is not None
    
    # Should be close to actual current time (within 1 second)
    actual_now = datetime.now(timezone.utc)
    time_diff = abs((now - actual_now).total_seconds())
    assert time_diff < 1.0


def test_app_now() -> None:
    """Test that app_now returns current datetime in application timezone."""
    from utils.timezone import app_now, get_app_timezone, utc_now
    
    app_now_dt = app_now()
    app_tz = get_app_timezone()
    
    assert app_now_dt.tzinfo == app_tz
    
    # Should be close to current time converted to app timezone
    utc_now_dt = utc_now()
    expected_app_now = utc_now_dt.astimezone(app_tz)
    
    # Allow small time difference due to execution time
    time_diff = abs((app_now_dt - expected_app_now).total_seconds())
    assert time_diff < 1.0


def test_to_app_tz() -> None:
    """Test conversion of datetime to application timezone."""
    from utils.timezone import to_app_tz, get_app_timezone
    
    app_tz = get_app_timezone()
    
    # Test with UTC datetime
    utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    app_dt = to_app_tz(utc_dt)
    
    assert app_dt.tzinfo == app_tz
    
    # Australia/Melbourne is UTC+10 or UTC+11 depending on DST
    # On Jan 1 (summer), it should be UTC+11
    expected_hour = (12 + 11) % 24  # 23:00
    assert app_dt.hour == expected_hour
    assert app_dt.date() == utc_dt.date()
    
    # Test with naive datetime (should assume UTC)
    naive_dt = datetime(2024, 1, 1, 12, 0, 0)
    app_dt_naive = to_app_tz(naive_dt)
    assert app_dt_naive.tzinfo == app_tz
    
    # Test with date object
    from datetime import date
    date_obj = date(2024, 1, 1)
    app_dt_from_date = to_app_tz(date_obj)
    assert app_dt_from_date.tzinfo == app_tz
    # Date at midnight UTC becomes 11:00 in Australia/Melbourne (UTC+11)
    # because naive datetime is assumed to be UTC, then converted to app timezone
    assert app_dt_from_date.hour == 11  # 00:00 UTC = 11:00 Australia/Melbourne
    assert app_dt_from_date.date() == date_obj


def test_from_app_tz() -> None:
    """Test conversion of datetime from application timezone to UTC."""
    from utils.timezone import from_app_tz, get_app_timezone
    
    app_tz = get_app_timezone()
    
    # Test with app timezone datetime
    app_dt = datetime(2024, 1, 1, 23, 0, 0, tzinfo=app_tz)
    utc_dt = from_app_tz(app_dt)
    
    assert utc_dt.tzinfo == timezone.utc
    
    # Australia/Melbourne is UTC+11 on Jan 1 (summer)
    # So 23:00 Melbourne time should be 12:00 UTC
    assert utc_dt.hour == 12
    assert utc_dt.date() == app_dt.date()
    
    # Test with naive datetime (should assume app timezone)
    naive_dt = datetime(2024, 1, 1, 23, 0, 0)
    utc_dt_naive = from_app_tz(naive_dt)
    assert utc_dt_naive.tzinfo == timezone.utc
    assert utc_dt_naive.hour == 12
    
    # Test with date object
    from datetime import date
    date_obj = date(2024, 1, 1)
    utc_dt_from_date = from_app_tz(date_obj)
    assert utc_dt_from_date.tzinfo == timezone.utc
    assert utc_dt_from_date.hour == 13  # 00:00 Melbourne time = 13:00 UTC previous day? Wait, check
    # Actually 00:00 Melbourne (UTC+11) = 13:00 UTC previous day (Dec 31)
    # So date would be Dec 31, 2023
    assert utc_dt_from_date.date() == date(2023, 12, 31)


def test_parse_to_utc() -> None:
    """Test parsing datetime string to UTC."""
    from utils.timezone import parse_to_utc, get_app_timezone
    
    app_tz = get_app_timezone()
    
    # Test parsing with explicit timezone
    date_str = "2024-01-01 23:00"
    format_str = "%Y-%m-%d %H:%M"
    utc_dt = parse_to_utc(date_str, format_str, "Australia/Melbourne")
    
    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.hour == 12  # 23:00 Melbourne = 12:00 UTC
    assert utc_dt.date() == datetime(2024, 1, 1).date()
    
    # Test parsing with default (app) timezone
    utc_dt_default = parse_to_utc(date_str, format_str)
    assert utc_dt_default.tzinfo == timezone.utc
    # Should be same as above since app timezone is Australia/Melbourne
    assert utc_dt_default.hour == 12
    
    # Test parsing with different timezone
    utc_dt_ny = parse_to_utc("2024-01-01 18:00", "%Y-%m-%d %H:%M", "America/New_York")
    assert utc_dt_ny.tzinfo == timezone.utc
    # 18:00 New York (UTC-5) = 23:00 UTC
    assert utc_dt_ny.hour == 23
    
    # Test with timezone object instead of string
    ny_tz = zoneinfo.ZoneInfo("America/New_York")
    utc_dt_tz_obj = parse_to_utc("2024-01-01 18:00", "%Y-%m-%d %H:%M", ny_tz)
    assert utc_dt_tz_obj == utc_dt_ny


def test_timezone_conversion_roundtrip() -> None:
    """Test that converting to app timezone and back preserves the datetime."""
    from utils.timezone import to_app_tz, from_app_tz, utc_now
    
    # Test with current UTC time
    utc_dt = utc_now()
    app_dt = to_app_tz(utc_dt)
    utc_dt_roundtrip = from_app_tz(app_dt)
    
    # Should be very close (within microseconds)
    time_diff = abs((utc_dt - utc_dt_roundtrip).total_seconds())
    assert time_diff < 0.001
    
    # Test with naive datetime
    naive_dt = datetime(2024, 6, 15, 14, 30, 0)
    app_dt = to_app_tz(naive_dt)
    utc_dt = from_app_tz(app_dt)
    app_dt_roundtrip = to_app_tz(utc_dt)
    
    # Should be equal
    assert app_dt == app_dt_roundtrip


def test_app_now_uses_utc_now() -> None:
    """Test that app_now is equivalent to utc_now converted to app timezone."""
    from utils.timezone import app_now, utc_now, to_app_tz
    
    app_now_dt = app_now()
    utc_now_dt = utc_now()
    expected_app_now = to_app_tz(utc_now_dt)
    
    # Allow small difference due to execution time
    time_diff = abs((app_now_dt - expected_app_now).total_seconds())
    assert time_diff < 0.1


class TestTimezoneDSTEdgeCases:
    """Test class specifically for daylight savings time edge cases."""
    
    def test_dst_summer_conversion(self) -> None:
        """Test conversion during DST (summer = UTC+11) - e.g., January 1st."""
        from utils.timezone import to_app_tz, from_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # January 1, 2024 - during Australian summer DST (UTC+11)
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        app_dt = to_app_tz(utc_dt)
        
        # Should be UTC+11: 12:00 UTC = 23:00 Melbourne
        assert app_dt.hour == 23
        assert app_dt.date() == utc_dt.date()
        assert app_dt.tzinfo == app_tz
        
        # Round-trip conversion
        utc_dt_roundtrip = from_app_tz(app_dt)
        assert utc_dt_roundtrip == utc_dt
        
        # Verify offset is +11 hours
        offset = app_dt.utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 11 * 3600  # 11 hours
    
    def test_dst_winter_conversion(self) -> None:
        """Test conversion outside DST (winter = UTC+10) - e.g., July 1st."""
        from utils.timezone import to_app_tz, from_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # July 1, 2024 - during Australian winter (UTC+10)
        utc_dt = datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        app_dt = to_app_tz(utc_dt)
        
        # Should be UTC+10: 12:00 UTC = 22:00 Melbourne
        assert app_dt.hour == 22
        assert app_dt.date() == utc_dt.date()
        assert app_dt.tzinfo == app_tz
        
        # Round-trip conversion
        utc_dt_roundtrip = from_app_tz(app_dt)
        assert utc_dt_roundtrip == utc_dt
        
        # Verify offset is +10 hours
        offset = app_dt.utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 10 * 3600  # 10 hours
    
    def test_dst_transition_start(self) -> None:
        """Test DST start transition (first Sunday in October at 2:00 AM)."""
        from utils.timezone import to_app_tz, from_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # DST starts: First Sunday in October at 2:00 AM
        # For 2024: October 6, 2024 at 2:00 AM
        
        # Test just before DST starts (1:59 AM) - still in standard time (UTC+10)
        before_dst_utc = datetime(2024, 10, 5, 15, 59, 0, tzinfo=timezone.utc)  # 1:59 AM Melbourne
        before_dst_app = to_app_tz(before_dst_utc)
        assert before_dst_app.hour == 1
        assert before_dst_app.minute == 59
        offset_before = before_dst_app.utcoffset()
        assert offset_before is not None
        assert offset_before.total_seconds() == 10 * 3600  # UTC+10
        
        # Test just after DST starts (3:00 AM) - now in DST (UTC+11)
        # Note: 2:00 AM doesn't exist - clocks jump from 1:59:59 to 3:00:00
        after_dst_utc = datetime(2024, 10, 5, 16, 0, 0, tzinfo=timezone.utc)  # 3:00 AM Melbourne
        after_dst_app = to_app_tz(after_dst_utc)
        assert after_dst_app.hour == 3
        assert after_dst_app.minute == 0
        offset_after = after_dst_app.utcoffset()
        assert offset_after is not None
        assert offset_after.total_seconds() == 11 * 3600  # UTC+11
    
    def test_dst_transition_end(self) -> None:
        """Test DST end transition (first Sunday in April at 3:00 AM)."""
        from utils.timezone import to_app_tz, from_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # DST ends: First Sunday in April at 3:00 AM (2:00 AM becomes 3:00 AM)
        # For 2024: April 7, 2024 at 3:00 AM
        
        # Test just before DST ends (1:59 AM) - still in DST (UTC+11)
        before_end_utc = datetime(2024, 4, 6, 14, 59, 0, tzinfo=timezone.utc)  # 1:59 AM Melbourne
        before_end_app = to_app_tz(before_end_utc)
        assert before_end_app.hour == 1
        assert before_end_app.minute == 59
        offset_before = before_end_app.utcoffset()
        assert offset_before is not None
        assert offset_before.total_seconds() == 11 * 3600  # UTC+11
        
        # Test during the ambiguous hour (2:30 AM) - this time occurs twice!
        # Python's zoneinfo will use the later occurrence (after fallback)
        ambiguous_utc_1 = datetime(2024, 4, 6, 15, 30, 0, tzinfo=timezone.utc)  # 2:30 AM first occurrence
        ambiguous_app_1 = to_app_tz(ambiguous_utc_1)
        # This should be in DST (first occurrence)
        assert ambiguous_app_1.hour == 2
        assert ambiguous_app_1.minute == 30
        
        # Test after DST ends (3:00 AM) - now in standard time (UTC+10)
        after_end_utc = datetime(2024, 4, 6, 17, 0, 0, tzinfo=timezone.utc)  # 3:00 AM Melbourne
        after_end_app = to_app_tz(after_end_utc)
        assert after_end_app.hour == 3
        assert after_end_app.minute == 0
        offset_after = after_end_app.utcoffset()
        assert offset_after is not None
        assert offset_after.total_seconds() == 10 * 3600  # UTC+10
    
    def test_24_hour_boundary_crossing(self) -> None:
        """Test dates that convert across UTC date boundaries."""
        from utils.timezone import to_app_tz, from_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # Test a time in Melbourne that's near midnight, causing UTC date change
        # 11:30 PM Melbourne (UTC+11) = 12:30 PM UTC same day
        # But 1:30 AM Melbourne (UTC+11) = 2:30 PM UTC previous day
        
        # Case 1: 11:30 PM Melbourne = 12:30 PM UTC same day
        app_dt_1 = datetime(2024, 1, 1, 23, 30, 0, tzinfo=app_tz)
        utc_dt_1 = from_app_tz(app_dt_1)
        assert utc_dt_1.date() == app_dt_1.date()  # Same date
        assert utc_dt_1.hour == 12
        assert utc_dt_1.minute == 30
        
        # Case 2: 1:30 AM Melbourne = 2:30 PM UTC previous day
        app_dt_2 = datetime(2024, 1, 2, 1, 30, 0, tzinfo=app_tz)
        utc_dt_2 = from_app_tz(app_dt_2)
        assert utc_dt_2.date() == datetime(2024, 1, 1).date()  # Previous day
        assert utc_dt_2.hour == 14  # 2:30 PM = 14:30
        assert utc_dt_2.minute == 30
        
        # Round-trip both cases
        assert to_app_tz(utc_dt_1) == app_dt_1
        assert to_app_tz(utc_dt_2) == app_dt_2
    
    def test_midnight_edge_cases(self) -> None:
        """Test midnight edge cases in app timezone."""
        from utils.timezone import to_app_tz, from_app_tz, today_in_app_tz, get_app_timezone
        
        app_tz = get_app_timezone()
        
        # Test midnight in app timezone
        app_midnight = datetime(2024, 1, 1, 0, 0, 0, tzinfo=app_tz)
        utc_midnight = from_app_tz(app_midnight)
        
        # Midnight Melbourne (UTC+11) = 1:00 PM UTC previous day
        assert utc_midnight.hour == 13
        assert utc_midnight.date() == datetime(2023, 12, 31).date()
        
        # Test today_in_app_tz with edge cases
        # Mock a UTC time that's just before midnight in Melbourne
        # 10:00 PM UTC = 9:00 AM next day Melbourne (UTC+11)
        test_utc = datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc)
        
        # We can't easily mock utc_now(), but we can test the logic:
        # 22:00 UTC = 09:00 next day Melbourne
        app_time = to_app_tz(test_utc)
        assert app_time.date() == datetime(2024, 1, 2).date()  # Next day
    
    def test_local_midnight_conversion_most_important(self) -> None:
        """
        Test that 'today' in app timezone converts correctly to UTC.
        
        This catches the most common DST-related bug: 'Get jobs for today'
        returning wrong date range.
        """
        from utils.timezone import from_app_tz, get_app_timezone
        from datetime import time
        
        app_tz = get_app_timezone()
        
        # Test with a date during DST (summer)
        summer_date = datetime(2024, 1, 1).date()
        summer_midnight_app = datetime.combine(summer_date, time.min).replace(tzinfo=app_tz)
        summer_midnight_utc = from_app_tz(summer_midnight_app)
        
        # Midnight Melbourne (UTC+11) on Jan 1 = 13:00 UTC on Dec 31
        assert summer_midnight_utc.hour == 13
        assert summer_midnight_utc.date() == datetime(2023, 12, 31).date()
        
        # Test with a date outside DST (winter)
        winter_date = datetime(2024, 7, 1).date()
        winter_midnight_app = datetime.combine(winter_date, time.min).replace(tzinfo=app_tz)
        winter_midnight_utc = from_app_tz(winter_midnight_app)
        
        # Midnight Melbourne (UTC+10) on Jul 1 = 14:00 UTC on Jun 30
        assert winter_midnight_utc.hour == 14
        assert winter_midnight_utc.date() == datetime(2024, 6, 30).date()
        
        # Verify the date range for "today" queries
        # If querying for jobs on Jan 1 in Melbourne timezone,
        # the UTC range should be from 13:00 Dec 31 to 13:00 Jan 1
        summer_next_midnight_app = datetime.combine(
            summer_date + timedelta(days=1), time.min
        ).replace(tzinfo=app_tz)
        summer_next_midnight_utc = from_app_tz(summer_next_midnight_app)
        
        # The UTC time range for "Jan 1 in Melbourne" is:
        # From: 13:00 UTC Dec 31 (summer_midnight_utc)
        # To:   13:00 UTC Jan 1 (summer_next_midnight_utc)
        assert summer_next_midnight_utc.hour == 13
        assert summer_next_midnight_utc.date() == summer_date
    
    def test_get_timezone_offset_with_dst(self) -> None:
        """Test get_timezone_offset() function with DST dates."""
        from utils.timezone import get_timezone_offset
        
        # Test during DST (summer)
        # Mock datetime.now to return a summer date
        import utils.timezone
        original_datetime = utils.timezone.datetime
        
        try:
            # Mock datetime.now to return a fixed summer date
            class MockDatetime:
                @staticmethod
                def now(tz):
                    if tz == timezone.utc:
                        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                    return original_datetime.now(tz)
            
            utils.timezone.datetime = MockDatetime
            
            # During summer DST, offset should be +11 hours
            summer_offset = get_timezone_offset("Australia/Melbourne")
            assert summer_offset.total_seconds() == 11 * 3600
            
            # Mock datetime.now to return a fixed winter date
            class MockDatetimeWinter:
                @staticmethod
                def now(tz):
                    if tz == timezone.utc:
                        return datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
                    return original_datetime.now(tz)
            
            utils.timezone.datetime = MockDatetimeWinter
            
            # During winter, offset should be +10 hours
            winter_offset = get_timezone_offset("Australia/Melbourne")
            assert winter_offset.total_seconds() == 10 * 3600
            
        finally:
            # Restore original datetime
            utils.timezone.datetime = original_datetime
    
    def test_parse_to_utc_with_dst_aware_timezones(self) -> None:
        """Test parse_to_utc() with DST-aware timezones."""
        from utils.timezone import parse_to_utc
        
        # Test parsing a summer date
        summer_utc = parse_to_utc("2024-01-01 23:00", "%Y-%m-%d %H:%M", "Australia/Melbourne")
        # 23:00 Melbourne (UTC+11) = 12:00 UTC
        assert summer_utc.hour == 12
        assert summer_utc.date() == datetime(2024, 1, 1).date()
        
        # Test parsing a winter date
        winter_utc = parse_to_utc("2024-07-01 22:00", "%Y-%m-%d %H:%M", "Australia/Melbourne")
        # 22:00 Melbourne (UTC+10) = 12:00 UTC
        assert winter_utc.hour == 12
        assert winter_utc.date() == datetime(2024, 7, 1).date()
        
        # Test parsing during DST transition (ambiguous time)
        # 2:30 AM on DST end day - should parse to the first occurrence (in DST)
        transition_utc = parse_to_utc("2024-04-07 02:30", "%Y-%m-%d %H:%M", "Australia/Melbourne")
        # The result depends on how zoneinfo handles ambiguous times
        # We just verify it parses successfully
        assert transition_utc.tzinfo == timezone.utc