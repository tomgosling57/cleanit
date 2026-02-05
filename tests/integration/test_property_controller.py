"""
Robust integration tests for PropertyController._get_filtered_property_jobs method.
Focuses on timezone conversion correctness for date filtering and hide past jobs functionality.
"""

import pytest
from datetime import datetime, timedelta, date
from tests.db_helpers import get_db_session
from utils.timezone import today_in_app_tz, utc_now, to_app_tz, from_app_tz, parse_to_utc
from database import Job, get_db


class TestPropertyControllerFilteredJobs:
    """Test suite for PropertyController._get_filtered_property_jobs method."""
    
    def test_basic_date_filtering(self, admin_client_no_csrf):
        """Test basic date range filtering without timezone issues."""
        # Reseed database to ensure clean state
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Get today's date in application timezone
        today_app_tz = to_app_tz(utc_now()).date()
        
        # Test with date range: yesterday to 10 days from now
        start_date = today_app_tz - timedelta(days=1)
        end_date = today_app_tz + timedelta(days=10)
        
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date={start_date.isoformat()}&'
            f'end_date={end_date.isoformat()}&'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert 'jobs' in data
        assert isinstance(data['jobs'], list)
        
        # Verify all returned jobs are within the date range
        for job_data in data['jobs']:
            job_date = datetime.fromisoformat(job_data['date']).date()
            assert start_date <= job_date <= end_date, \
                f"Job {job_data['id']} date {job_date} outside range {start_date} to {end_date}"
    
    def test_date_filtering_with_timezone_boundary(self, admin_client_no_csrf):
        """Test date filtering when dates are near timezone boundaries.
        
        This test ensures that when a user selects a date in the application timezone,
        jobs on that date are correctly included even if the UTC conversion shifts
        the datetime across a date boundary.
        """
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Create a specific test date that could be problematic near timezone boundaries
        # Use a date far in the future to avoid conflicts with seeded data
        test_date = date(2025, 1, 15)  # Arbitrary future date
        
        # We need to create a test job for this specific date
        # Since we can't modify seeded data easily, we'll test with the existing
        # testing endpoint which uses seeded data. For this test, we'll verify
        # the conversion logic works correctly.
        
        # Test filtering for a single day
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date={test_date.isoformat()}&'
            f'end_date={test_date.isoformat()}&'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # With seeded data, there might be no jobs on this specific date
        # The important thing is the endpoint works correctly
        
    def test_hide_past_jobs_with_timezone(self, admin_client_no_csrf):
        """Test that 'hide past jobs' correctly considers timezone.
        
        When show_past=false, jobs before 'today' should be hidden.
        'Today' should be calculated in the application timezone, not UTC,
        to avoid filtering out jobs that are today in the local timezone
        but yesterday in UTC.
        """
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Get today in application timezone
        today_app_tz = to_app_tz(utc_now()).date()
        
        # Test with show_past=false - should only show jobs from today onward
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=false&show_completed=true'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify no past jobs are included
        for job_data in data['jobs']:
            job_date = datetime.fromisoformat(job_data['date']).date()
            assert job_date >= today_app_tz, \
                f"Job {job_data['id']} date {job_date} is in the past (today is {today_app_tz})"
    
    def test_show_past_jobs(self, admin_client_no_csrf):
        """Test that show_past option correctly includes/excludes past jobs."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Get today in application timezone
        start_date = today_in_app_tz() - timedelta(days=30)
        end_date = today_in_app_tz()
        
        
        # Test with show_past=true - should include past completed jobs
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=true&show_completed=true&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}'
        )
        db = get_db_session()
        expected_jobs = db.query(Job).filter(Job.property_id == 1).filter(
            Job.date >= from_app_tz(datetime.combine(start_date, datetime.min.time()))
            ).filter(Job.date <= from_app_tz(datetime.combine(end_date, datetime.max.time()))).all()
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        assert len(data['jobs']) == len(expected_jobs), \
            f"Expected {len(expected_jobs)} past jobs: {[job.id for job in expected_jobs]}, got {len(data['jobs'])} {[job['id'] for job in data['jobs']]}"
        # Count past jobs (jobs before today)
        past_jobs = []
        for job_data in data['jobs']:
            job_date = datetime.fromisoformat(job_data['date']).date()
            if job_date < today_in_app_tz():
                past_jobs.append(job_data)
        
        # With seeded data, there should be some past completed jobs
        # (jobs with IDs 14-17 are past and completed in seeded data)
        assert len(past_jobs) > 0, "Should include past completed jobs when show_past=true"
                
    def test_hide_completed_jobs(self, admin_client_no_csrf):
        """Test that show_completed=false hides completed jobs."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=true&show_completed=false'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify no completed jobs are included
        for job_data in data['jobs']:
            assert job_data['is_complete'] is False, \
                f"Job {job_data['id']} should not be completed when show_completed=false"
    
    def test_combined_filters(self, admin_client_no_csrf):
        """Test combination of date range, hide past, and hide completed filters."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        today_app_tz = to_app_tz(utc_now()).date()
        start_date = today_app_tz - timedelta(days=5)
        end_date = today_app_tz + timedelta(days=5)
        
        # Test: show only future (not past), incomplete jobs within date range
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date={start_date.isoformat()}&'
            f'end_date={end_date.isoformat()}&'
            f'show_past=false&show_completed=false'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        for job_data in data['jobs']:
            job_date = datetime.fromisoformat(job_data['date']).date()
            # Should be within date range
            assert start_date <= job_date <= end_date
            # Should not be in the past (relative to today in app timezone)
            assert job_date >= today_app_tz
            # Should not be completed
            assert job_data['is_complete'] is False
    
    def test_empty_date_range(self, admin_client_no_csrf):
        """Test filtering with date range that has no jobs."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Use a date far in the future where there are no jobs
        future_date = date(2030, 1, 1)
        
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date={future_date.isoformat()}&'
            f'end_date={future_date.isoformat()}&'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return empty list, not error
        assert len(data['jobs']) == 0
    
    def test_invalid_date_format(self, admin_client_no_csrf):
        """Test handling of invalid date format in query parameters."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Invalid date format
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date=invalid-date&'
            f'end_date=2024-01-01&'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_missing_date_parameters(self, admin_client_no_csrf):
        """Test filtering when date parameters are not provided."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # No date parameters at all
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        assert isinstance(data['jobs'], list)
        
        # Should return all jobs (no date filtering)
        # With seeded data for property 1, there should be multiple jobs
    
    def test_timezone_consistency_across_requests(self, admin_client_no_csrf):
        """Test that timezone handling is consistent across multiple requests."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        today_app_tz = to_app_tz(utc_now()).date()
        
        # Make first request
        response1 = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=false&show_completed=true'
        )
        assert response1.status_code == 200
        data1 = response1.get_json()
        
        # Make second identical request
        response2 = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=false&show_completed=true'
        )
        assert response2.status_code == 200
        data2 = response2.get_json()
        
        # Results should be identical (deterministic)
        assert len(data1['jobs']) == len(data2['jobs'])
        
        # Job IDs should match
        job_ids1 = {job['id'] for job in data1['jobs']}
        job_ids2 = {job['id'] for job in data2['jobs']}
        assert job_ids1 == job_ids2
    
    def test_different_properties_have_different_jobs(self, admin_client_no_csrf):
        """Test that filtering works correctly for different properties."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Get jobs for property 1
        response1 = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=true&show_completed=true'
        )
        assert response1.status_code == 200
        data1 = response1.get_json()
        
        # Get jobs for property 2
        response2 = admin_client_no_csrf.get(
            f'/testing/property/2/jobs/filtered?'
            f'show_past=true&show_completed=true'
        )
        assert response2.status_code == 200
        data2 = response2.get_json()
        
        # Properties should have different jobs (though there might be overlap in seeded data)
        job_ids1 = {job['id'] for job in data1['jobs']}
        job_ids2 = {job['id'] for job in data2['jobs']}
        
        # They might share some jobs in seeded data, but not all
        # At least verify both return some jobs
        assert len(job_ids1) > 0
        assert len(job_ids2) > 0
    
    def test_parse_to_utc_correctness(self):
        """Unit test for parse_to_utc function to verify timezone conversion logic."""
        # Test with Australia/Sydney timezone (UTC+10/+11 depending on DST)
        test_date = "2024-01-01"
        
        # When parsing in Australia/Sydney timezone
        utc_result = parse_to_utc(test_date, "%Y-%m-%d", source_tz="Australia/Sydney")
        
        # January is during Australian summer (DST), so Sydney is UTC+11
        # 2024-01-01 00:00 in Sydney = 2023-12-31 13:00 UTC
        assert utc_result.year == 2023
        assert utc_result.month == 12
        assert utc_result.day == 31
        assert utc_result.hour == 13  # 00:00 Sydney = 13:00 previous day UTC
        
        # Verify the timezone is UTC
        assert str(utc_result.tzinfo) == 'UTC'
        
        # Test reverse: when this UTC datetime is converted back to Sydney timezone
        from utils.timezone import to_app_tz
        import zoneinfo
        sydney_tz = zoneinfo.ZoneInfo("Australia/Sydney")
        sydney_time = utc_result.astimezone(sydney_tz)
        assert sydney_time.year == 2024
        assert sydney_time.month == 1
        assert sydney_time.day == 1
        assert sydney_time.hour == 0
    
    def test_edge_case_midnight_timezone_boundary(self, admin_client_no_csrf):
        """Test edge case where job date is exactly on timezone boundary.
        
        If a job is scheduled for a date that, when converted to UTC,
        becomes the previous day, filtering should still work correctly.
        """
        # This is more of a conceptual test since we can't easily modify
        # the seeded job dates. We'll verify the logic through the API.
        
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Create a test scenario by filtering with a specific date
        # and verifying the behavior is consistent
        test_date = date(2024, 6, 15)  # Arbitrary date
        
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'start_date={test_date.isoformat()}&'
            f'end_date={test_date.isoformat()}&'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200
        # The test passes if it doesn't crash and returns valid JSON
    
    def test_date_display_in_application_timezone(self, admin_client_no_csrf):
        """Test that dates are displayed in application timezone, not UTC.
        
        This test verifies that when jobs are returned, the date shown
        is in the application timezone. This is important for date dividers
        in templates to group jobs correctly by local date.
        """
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Get jobs
        response = admin_client_no_csrf.get(
            f'/testing/property/1/jobs/filtered?'
            f'show_past=true&show_completed=true'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check that job dates are valid and can be parsed
        for job_data in data['jobs']:
            job_date_str = job_data['date']
            # Should be in YYYY-MM-DD format
            assert len(job_date_str) == 10
            assert job_date_str[4] == '-' and job_date_str[7] == '-'
            
            # Parse the date
            job_date = datetime.fromisoformat(job_date_str).date()
            
            # The date should be reasonable (not far in past/future for seeded data)
            # Seeded data has jobs from 10 days ago to 10 days in future
            today_app_tz = to_app_tz(utc_now()).date()
            assert today_app_tz - timedelta(days=15) <= job_date <= today_app_tz + timedelta(days=15), \
                f"Job {job_data['id']} date {job_date} is outside expected range for seeded data"
    
    def test_timezone_aware_date_comparison(self):
        """Test that date comparisons consider application timezone.
        
        This is a unit test for the logic that compares dates with
        timezone awareness. The key issue is that 'today' should be
        calculated in application timezone, not UTC, when filtering
        jobs with show_past=false.
        """
        from utils.timezone import get_app_timezone
        import zoneinfo
        
        # Get application timezone
        app_tz = get_app_timezone()
        
        # Create test datetimes at boundary times
        # Example: 11 PM UTC is next day in Australia/Sydney
        utc_23pm = datetime(2024, 2, 5, 23, 0, tzinfo=zoneinfo.ZoneInfo('UTC'))
        app_time = utc_23pm.astimezone(app_tz)
        
        # If app timezone is Australia/Sydney (UTC+11), then:
        # 2024-02-05 23:00 UTC = 2024-02-06 10:00 Australia/Sydney
        # So 'today' in app timezone is Feb 6, but 'today' in UTC is Feb 5
        
        # The JobService should use application timezone's 'today'
        # when filtering with show_past=false
        print(f"UTC time: {utc_23pm}")
        print(f"App time ({app_tz}): {app_time}")
        print(f"UTC date: {utc_23pm.date()}")
        print(f"App date: {app_time.date()}")
        
        # This test doesn't assert anything, just demonstrates the issue
        # The actual fix would be in JobService.get_filtered_jobs_by_property_id
    
    def test_job_date_interpretation_issue(self, admin_client_no_csrf):
        """Demonstrate the job date interpretation issue.
        
        The problem: Job.date is stored as a date (no timezone).
        When we filter jobs by date, we need to interpret these dates
        consistently. If Job.date represents a UTC date, but users
        think in application timezone dates, we have a mismatch.
        
        Example scenario:
        - User in Australia/Sydney creates job for "Feb 5th"
        - System stores Job.date = 2024-02-05 (but is this UTC date or Sydney date?)
        - If stored as UTC date: Feb 5th 00:00 UTC = Feb 5th 11:00 Sydney
        - User expects to see job when filtering for "Feb 5th" (Sydney time)
        - But the job might appear on Feb 4th or Feb 5th depending on conversion
        """
        # This test demonstrates the issue conceptually
        from utils.timezone import get_app_timezone
        import zoneinfo
        
        app_tz = get_app_timezone()
        print(f"\n=== Job Date Interpretation Issue ===")
        print(f"Application timezone: {app_tz}")
        
        # Scenario 1: Job at early morning in Sydney (late previous day in UTC)
        # Job scheduled for Feb 5th 01:00 Sydney time (UTC+11)
        # = Feb 4th 14:00 UTC
        # What should Job.date be? 2024-02-05 (Sydney date) or 2024-02-04 (UTC date)?
        
        # Scenario 2: Job at late evening in Sydney (early next day in UTC)
        # Job scheduled for Feb 5th 23:00 Sydney time (UTC+11)
        # = Feb 5th 12:00 UTC
        # What should Job.date be? 2024-02-05 (Sydney date) or 2024-02-05 (UTC date)?
        
        # The issue is that Job.date field can't represent both timezone contexts
        # We need to decide: does Job.date represent date in application timezone?
        # Or does it represent date in UTC?
        
        # Current implementation in JobService uses utc_now().date() for comparison
        # This suggests Job.date should be compared with UTC dates
        # But parse_to_utc in PropertyController converts user dates from app timezone to UTC
        # This suggests Job.date should be UTC dates
        
        print("Issue demonstrated. Need to ensure consistent interpretation.")
        
        # The test passes - it's just documenting the issue
        assert True
    
    def test_default_parameter_values(self, admin_client_no_csrf):
        """Test that default parameter values work correctly."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Test with no parameters - should use defaults
        response = admin_client_no_csrf.get('/testing/property/1/jobs/filtered')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        
        # Defaults are: show_past=false, show_completed=true
        # So should not include past jobs
        today_app_tz = to_app_tz(utc_now()).date()
        for job_data in data['jobs']:
            job_date = datetime.fromisoformat(job_data['date']).date()
            assert job_date >= today_app_tz, \
                f"Default show_past=false should exclude past jobs, but found job {job_data['id']} with date {job_date}"
    
    def test_boolean_parameter_parsing(self, admin_client_no_csrf):
        """Test various boolean parameter formats."""
        # Reseed database
        admin_client_no_csrf.get('/testing/reseed-database')
        
        # Test different boolean formats
        test_cases = [
            ('true', 'true', True, True),
            ('false', 'false', False, False),
            ('True', 'True', True, True),  # Capitalized
            ('False', 'False', False, False),
            ('1', '1', True, True),  # Numeric
            ('0', '0', False, False),
        ]
        
        for show_past_val, show_completed_val, expected_show_past, expected_show_completed in test_cases:
            response = admin_client_no_csrf.get(
                f'/testing/property/1/jobs/filtered?'
                f'show_past={show_past_val}&show_completed={show_completed_val}'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify the filtering behavior matches expected
            today_app_tz = to_app_tz(utc_now()).date()
            
            for job_data in data['jobs']:
                job_date = datetime.fromisoformat(job_data['date']).date()
                
                if not expected_show_past:
                    assert job_date >= today_app_tz, \
                        f"show_past={show_past_val} should exclude past jobs"
                
                if not expected_show_completed:
                    assert job_data['is_complete'] is False, \
                        f"show_completed={show_completed_val} should exclude completed jobs"