
import os


def test_today_in_app_tz() -> None:
    """Test that today_in_app_tz returns the correct date in the app timezone."""
    from utils.timezone import today_in_app_tz, to_app_tz, utc_now
    app_today = today_in_app_tz()
    expected_today = to_app_tz(utc_now()).date()
    assert app_today == expected_today
    
    assert os.getenv('APP_TIMEZONE') == 'Australia/Melbourne'