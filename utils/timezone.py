"""
Timezone handling utilities for CleanIt application.

This module provides centralized timezone handling with the following principles:
1. All internal operations use UTC
2. Conversion to/from application timezone happens only at presentation layer
3. Uses IANA timezone identifiers (e.g., 'Australia/Melbourne', 'UTC')
4. Provides helper functions to avoid direct datetime.now() calls
5. Does not depend on Flask application context - can be used in tests and scripts
"""

import os
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Tuple, Dict, Any
import warnings


def get_app_timezone() -> zoneinfo.ZoneInfo:
    """
    Get the configured application timezone as a ZoneInfo object.
    
    Returns:
        zoneinfo.ZoneInfo: The application timezone
        
    Raises:
        zoneinfo.ZoneInfoNotFoundError: If the configured timezone is invalid
    """
    # Read directly from environment variable to avoid Flask context dependency
    tz_name = os.getenv('APP_TIMEZONE', 'UTC')
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except zoneinfo.ZoneInfoNotFoundError:
        # Fall back to UTC if configured timezone is invalid
        warnings.warn(f"Invalid timezone '{tz_name}' configured, falling back to UTC", RuntimeWarning)
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


# Time comparison utilities for environment synchronization
def compare_times(time1: datetime, time2: datetime, max_difference_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Compare two datetime objects and determine if they're within acceptable difference.
    
    Args:
        time1: First datetime (should be timezone-aware)
        time2: Second datetime (should be timezone-aware)
        max_difference_seconds: Maximum allowed difference in seconds
        
    Returns:
        Dict with comparison results including:
        - difference_seconds: Absolute time difference in seconds
        - within_threshold: Boolean indicating if difference is within max_difference_seconds
        - time1_ahead: Boolean indicating if time1 is ahead of time2
        - time2_ahead: Boolean indicating if time2 is ahead of time1
        - threshold_seconds: The maximum difference threshold used
        
    Example:
        >>> utc_now1 = utc_now()
        >>> utc_now2 = utc_now()
        >>> result = compare_times(utc_now1, utc_now2, 5.0)
        >>> result['within_threshold']
        True
    """
    # Ensure both datetimes are timezone-aware
    if time1.tzinfo is None:
        time1 = time1.replace(tzinfo=timezone.utc)
    if time2.tzinfo is None:
        time2 = time2.replace(tzinfo=timezone.utc)
    
    # Convert both to UTC for comparison
    time1_utc = time1.astimezone(timezone.utc)
    time2_utc = time2.astimezone(timezone.utc)
    
    # Calculate difference
    if time1_utc > time2_utc:
        difference = time1_utc - time2_utc
        time1_ahead = True
        time2_ahead = False
    else:
        difference = time2_utc - time1_utc
        time1_ahead = False
        time2_ahead = True
    
    difference_seconds = difference.total_seconds()
    within_threshold = difference_seconds <= max_difference_seconds
    
    return {
        'difference_seconds': difference_seconds,
        'within_threshold': within_threshold,
        'time1_ahead': time1_ahead,
        'time2_ahead': time2_ahead,
        'threshold_seconds': max_difference_seconds,
        'time1': time1_utc.isoformat(),
        'time2': time2_utc.isoformat(),
    }


def compare_timezones(tz1: str, tz2: str) -> Dict[str, Any]:
    """
    Compare two timezone identifiers and check if they're equivalent.
    
    Args:
        tz1: First IANA timezone identifier
        tz2: Second IANA timezone identifier
        
    Returns:
        Dict with comparison results including:
        - tz1_valid: Boolean indicating if tz1 is valid
        - tz2_valid: Boolean indicating if tz2 is valid
        - equivalent: Boolean indicating if timezones are equivalent (same identifier)
        - tz1_offset: Current UTC offset for tz1
        - tz2_offset: Current UTC offset for tz2
        - offsets_match: Boolean indicating if current offsets match
        
    Example:
        >>> result = compare_timezones("Australia/Sydney", "Australia/Melbourne")
        >>> result['equivalent']
        False
    """
    tz1_valid = is_valid_timezone(tz1)
    tz2_valid = is_valid_timezone(tz2)
    
    equivalent = tz1_valid and tz2_valid and tz1 == tz2
    
    # Get current offsets
    tz1_offset = get_timezone_offset(tz1) if tz1_valid else None
    tz2_offset = get_timezone_offset(tz2) if tz2_valid else None
    
    offsets_match = tz1_offset == tz2_offset if (tz1_offset and tz2_offset) else False
    
    return {
        'tz1': tz1,
        'tz2': tz2,
        'tz1_valid': tz1_valid,
        'tz2_valid': tz2_valid,
        'equivalent': equivalent,
        'tz1_offset': str(tz1_offset) if tz1_offset else None,
        'tz2_offset': str(tz2_offset) if tz2_offset else None,
        'offsets_match': offsets_match,
    }


def compare_environment_times(
    container_time: datetime,
    testing_time: datetime,
    container_tz: str,
    testing_tz: str,
    max_time_diff_seconds: float = 5.0
) -> Dict[str, Any]:
    """
    Compare times between container application environment and testing environment.
    
    This is the main utility function for the pre-run sanity check to ensure
    the container and testing environments are synchronized.
    
    Args:
        container_time: Current time in container environment (should be timezone-aware)
        testing_time: Current time in testing environment (should be timezone-aware)
        container_tz: Timezone configured in container environment
        testing_tz: Timezone configured in testing environment
        max_time_diff_seconds: Maximum allowed time difference in seconds
        
    Returns:
        Dict with comprehensive comparison results including:
        - time_comparison: Results from compare_times()
        - timezone_comparison: Results from compare_timezones()
        - environments_synchronized: Boolean indicating if both time and timezone are synchronized
        - issues: List of issues found (empty if synchronized)
        
    Example:
        >>> container_now = utc_now()
        >>> testing_now = utc_now()
        >>> result = compare_environment_times(container_now, testing_now, "UTC", "UTC", 5.0)
        >>> result['environments_synchronized']
        True
    """
    # Compare times
    time_comparison = compare_times(container_time, testing_time, max_time_diff_seconds)
    
    # Compare timezones
    timezone_comparison = compare_timezones(container_tz, testing_tz)
    
    # Determine if environments are synchronized
    time_synchronized = time_comparison['within_threshold']
    timezone_synchronized = timezone_comparison['equivalent'] or timezone_comparison['offsets_match']
    
    environments_synchronized = time_synchronized and timezone_synchronized
    
    # Collect issues
    issues = []
    
    if not time_synchronized:
        diff_seconds = time_comparison['difference_seconds']
        if time_comparison['time1_ahead']:
            issues.append(f"Container time is {diff_seconds:.1f} seconds ahead of testing environment")
        else:
            issues.append(f"Container time is {diff_seconds:.1f} seconds behind testing environment")
    
    if not timezone_comparison['equivalent']:
        if not timezone_comparison['tz1_valid']:
            issues.append(f"Container timezone '{container_tz}' is invalid")
        if not timezone_comparison['tz2_valid']:
            issues.append(f"Testing timezone '{testing_tz}' is invalid")
        if timezone_comparison['tz1_valid'] and timezone_comparison['tz2_valid'] and not timezone_comparison['equivalent']:
            issues.append(f"Timezone mismatch: container uses '{container_tz}', testing uses '{testing_tz}'")
    
    return {
        'time_comparison': time_comparison,
        'timezone_comparison': timezone_comparison,
        'environments_synchronized': environments_synchronized,
        'issues': issues,
        'container_timezone': container_tz,
        'testing_timezone': testing_tz,
        'max_allowed_time_difference_seconds': max_time_diff_seconds,
    }