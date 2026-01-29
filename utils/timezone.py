"""
Timezone handling utilities for CleanIt application.

This module provides centralized timezone handling with the following principles:
1. All internal operations use UTC
2. Conversion to/from application timezone happens only at presentation layer
3. Uses IANA timezone identifiers (e.g., 'Australia/Melbourne', 'UTC')
4. Provides helper functions to avoid direct datetime.now() calls
"""

import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from flask import current_app


def get_app_timezone() -> zoneinfo.ZoneInfo:
    """
    Get the configured application timezone as a ZoneInfo object.
    
    Returns:
        zoneinfo.ZoneInfo: The application timezone
        
    Raises:
        zoneinfo.ZoneInfoNotFoundError: If the configured timezone is invalid
    """
    tz_name = current_app.config.get('APP_TIMEZONE', 'UTC')
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except zoneinfo.ZoneInfoNotFoundError:
        # Fall back to UTC if configured timezone is invalid
        current_app.logger.warning(f"Invalid timezone '{tz_name}' configured, falling back to UTC")
        return zoneinfo.ZoneInfo('UTC')


def utc_now() -> datetime:
    """
    Get current UTC datetime with timezone awareness.
    
    Returns:
        datetime: Current UTC datetime with timezone set to UTC
        
    Example:
        >>> now = utc_now()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def to_app_tz(dt: datetime) -> datetime:
    """
    Convert a datetime to the application timezone.
    
    Args:
        dt: Datetime to convert. If naive, assumes UTC.
        
    Returns:
        datetime: Datetime in application timezone
        
    Example:
        >>> utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> app_dt = to_app_tz(utc_dt)
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    app_tz = get_app_timezone()
    return dt.astimezone(app_tz)


def from_app_tz(dt: datetime) -> datetime:
    """
    Convert a datetime from application timezone to UTC.
    
    Args:
        dt: Datetime in application timezone. If naive, assumes app timezone.
        
    Returns:
        datetime: Datetime in UTC
        
    Example:
        >>> app_dt = datetime(2024, 1, 1, 22, 0)  # Naive, assumed in app timezone
        >>> utc_dt = from_app_tz(app_dt)
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in application timezone
        app_tz = get_app_timezone()
        dt = dt.replace(tzinfo=app_tz)
    
    return dt.astimezone(timezone.utc)


def format_in_app_tz(dt: datetime, format_str: str) -> str:
    """
    Format a datetime in the application timezone.
    
    Args:
        dt: Datetime to format. If naive, assumes UTC.
        format_str: strftime format string
        
    Returns:
        str: Formatted datetime string in application timezone
        
    Example:
        >>> utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> format_in_app_tz(utc_dt, "%Y-%m-%d %H:%M")
        '2024-01-01 22:00'  # If app timezone is Australia/Melbourne (UTC+10)
    """
    app_dt = to_app_tz(dt)
    return app_dt.strftime(format_str)


def parse_to_utc(date_str: str, format_str: str, source_tz: Optional[Union[str, zoneinfo.ZoneInfo]] = None) -> datetime:
    """
    Parse a datetime string and convert to UTC.
    
    Args:
        date_str: Date string to parse
        format_str: strptime format string
        source_tz: Timezone of the source string. If None, assumes application timezone.
                   Can be string (IANA identifier) or ZoneInfo object.
        
    Returns:
        datetime: Parsed datetime in UTC
        
    Example:
        >>> parse_to_utc("2024-01-01 22:00", "%Y-%m-%d %H:%M", "Australia/Melbourne")
        datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    """
    # Parse naive datetime
    naive_dt = datetime.strptime(date_str, format_str)
    
    # Apply source timezone
    if source_tz is None:
        source_tz = get_app_timezone()
    elif isinstance(source_tz, str):
        source_tz = zoneinfo.ZoneInfo(source_tz)
    
    # Localize and convert to UTC
    localized_dt = naive_dt.replace(tzinfo=source_tz)
    return localized_dt.astimezone(timezone.utc)


def is_valid_timezone(tz_name: str) -> bool:
    """
    Check if a timezone name is valid.
    
    Args:
        tz_name: IANA timezone identifier
        
    Returns:
        bool: True if timezone is valid
        
    Example:
        >>> is_valid_timezone("Australia/Melbourne")
        True
        >>> is_valid_timezone("Invalid/Timezone")
        False
    """
    try:
        zoneinfo.ZoneInfo(tz_name)
        return True
    except zoneinfo.ZoneInfoNotFoundError:
        return False


def get_timezone_offset(tz_name: Optional[str] = None) -> timedelta:
    """
    Get current UTC offset for a timezone.
    
    Args:
        tz_name: IANA timezone identifier. If None, uses application timezone.
        
    Returns:
        timedelta: Current UTC offset
        
    Example:
        >>> get_timezone_offset("Australia/Melbourne")
        timedelta(hours=10)  # Or 11 during DST
    """
    if tz_name is None:
        tz = get_app_timezone()
    else:
        tz = zoneinfo.ZoneInfo(tz_name)
    
    now = datetime.now(timezone.utc)
    localized_now = now.astimezone(tz)
    return localized_now.utcoffset() or timedelta(0)


# Convenience functions for common operations
def today_in_app_tz() -> datetime:
    """Get today's date in application timezone."""
    utc_today = utc_now().date()
    # Convert to app timezone at midnight UTC, then get date
    midnight_utc = datetime.combine(utc_today, datetime.min.time(), tzinfo=timezone.utc)
    return to_app_tz(midnight_utc).date()


def now_in_app_tz() -> datetime:
    """Get current datetime in application timezone."""
    return to_app_tz(utc_now())