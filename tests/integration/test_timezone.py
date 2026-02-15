
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