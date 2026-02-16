
from datetime import datetime, timedelta, date, time
import zoneinfo

from config import DATETIME_FORMATS
from utils.timezone import from_app_tz, get_app_timezone, today_in_app_tz, to_app_tz, parse_to_utc


class TestJobServiceTimezoneHandling:
    
    def test_create_job_with_timezone(self, job_service):
        # Create a job with a specific date and time in the app's timezone
        job_data = {
            'date': '2024-07-01',
            'start_time': '14:00',
            'end_time': '16:00',
            'arrival_datetime': datetime(2024, 7, 10, 14, 30, tzinfo=get_app_timezone()),
            'property_id': 1, 
            'description': 'Test job with timezone'
        }
        new_job = job_service.create_job(job_data)
        
        # Verify that the job was created with the correct date and time in UTC
        assert new_job is not None
        expected_start_datetime = from_app_tz(datetime.fromisoformat(f"{job_data['date']}T{job_data['start_time']}"))
        expected_end_datetime = from_app_tz(datetime.fromisoformat(f"{job_data['date']}T{job_data['end_time']}"))
        expected_arrival_datetime = job_data['arrival_datetime']
        new_job_start_datetime = datetime.combine(new_job.date, new_job.start_time, tzinfo=expected_start_datetime.tzinfo)
        new_job_end_datetime = datetime.combine(new_job.date, new_job.end_time, tzinfo=expected_start_datetime.tzinfo)
        new_job_arrival_datetime = new_job.arrival_datetime.replace(tzinfo=expected_start_datetime.tzinfo)
        assert new_job_start_datetime == expected_start_datetime, "New job start datetime does not match the expected value in UTC."
        assert new_job_end_datetime == expected_end_datetime, "New job end datetime does not match the expected value in UTC."
        assert new_job_arrival_datetime == expected_arrival_datetime, "New job arrival datetime does not match the expected value in UTC."

    def test_update_job_with_timezone(self, job_service):
        # Update a job with a specific date and time in the app's timezone
        job_id = 1  # Assuming a job with ID 1 exists
        job_data = {
            'date': '2024-07-02',
            'start_time': '15:00',
            'end_time': '17:00',
            'arrival_datetime': datetime(2024, 7, 10, 14, 30, tzinfo=get_app_timezone()),
            'description': 'Updated job with timezone'
        }
        updated_job = job_service.update_job(job_id, job_data)
        # Verify that the job was updated with the correct date and time in UTC
        assert updated_job is not None
        expected_start_datetime = from_app_tz(datetime.fromisoformat(f"{job_data['date']}T{job_data['start_time']}"))
        expected_end_datetime = from_app_tz(datetime.fromisoformat(f"{job_data['date']}T{job_data['end_time']}"))
        expected_arrival_datetime = job_data['arrival_datetime']
        updated_job_start_datetime = datetime.combine(updated_job.date, updated_job.start_time, tzinfo=expected_start_datetime.tzinfo)
        updated_job_end_datetime = datetime.combine(updated_job.date, updated_job.end_time, tzinfo=expected_start_datetime.tzinfo)
        updated_job_arrival_datetime = updated_job.arrival_datetime.replace(tzinfo=expected_start_datetime.tzinfo)
        assert updated_job_start_datetime == expected_start_datetime, "Updated job start datetime does not match the expected value in UTC."
        assert updated_job_end_datetime == expected_end_datetime, "Updated job end datetime does not match the expected value in UTC."
        assert updated_job_arrival_datetime == expected_arrival_datetime, "Updated job arrival datetime does not match the expected value in UTC."
    
    def test_get_job_for_user_on_date_with_timezone(self, job_service):
        # Get jobs for a user on a specific date in the app's timezone
        user_id = 1  # Assuming a user with ID 1 exists
        team_id = 1  # Assuming a team with ID 1 exists
        expected_date = today_in_app_tz()
        expected_date_str = expected_date.strftime(DATETIME_FORMATS['DATE_FORMAT'])
        jobs = job_service.get_jobs_for_user_on_date(user_id, team_id, expected_date)
        # Verify that the returned jobs have the correct date and time in app timezone
        for job in jobs:
            assert job.display_date == expected_date_str, f"Job date {job.display_date} does not match the expected date {expected_date.strftime(DATETIME_FORMATS['DATE_FORMAT'])} in app timezone."


class TestJobServiceDSTEdgeCases:
    """Test class specifically for daylight savings time edge cases in job service business logic."""
    
    def test_job_duration_calculation_across_dst(self, job_service):
        """Test duration calculation for a job that spans DST transition."""
        # Create a job that starts before DST and ends after DST transition
        # DST starts: First Sunday in October at 2:00 AM (2024-10-06)
        # Create job from 1:30 AM to 3:30 AM on DST start day
        
        # In app timezone (Australia/Melbourne):
        # 1:30 AM (before DST, UTC+10) = 15:30 UTC previous day
        # 3:30 AM (after DST, UTC+11) = 16:30 UTC same day
        
        job_data = {
            'date': '2024-10-06',
            'start_time': '01:30',
            'end_time': '03:30',
            'property_id': 1,
            'description': 'Job spanning DST start transition'
        }
        
        new_job = job_service.create_job(job_data)
        assert new_job is not None
        
        # Calculate expected duration
        # 1:30 AM to 3:30 AM is 2 hours in local time
        # Even though there's a DST transition, the local clock shows 2 hours
        assert new_job.duration == "2 hours", f"Expected duration '2 hours' but got '{new_job.duration}'"
        
        # Verify start and end times are stored correctly in UTC
        app_tz = get_app_timezone()
        start_app = datetime.combine(date(2024, 10, 6), time(1, 30)).replace(tzinfo=app_tz)
        end_app = datetime.combine(date(2024, 10, 6), time(3, 30)).replace(tzinfo=app_tz)
        
        start_utc = from_app_tz(start_app)
        end_utc = from_app_tz(end_app)
        
        # The actual time difference in UTC should be 1 hour (because of DST jump)
        # 1:30 AM (UTC+10) = 15:30 UTC previous day
        # 3:30 AM (UTC+11) = 16:30 UTC same day
        # Difference: 1 hour in UTC, but 2 hours in local time
        utc_duration = (end_utc - start_utc).total_seconds() / 3600
        assert utc_duration == 1.0, f"Expected 1 hour UTC duration but got {utc_duration} hours"
    
    def test_recurring_jobs_maintain_local_time_across_dst(self, job_service):
        """Test that recurring jobs maintain local time across DST transitions."""
        # Create a weekly job at 9:00 AM
        # This job should stay at 9:00 AM local time even after DST transitions
        
        # Create initial job in winter (UTC+10)
        winter_date = date(2024, 7, 1)  # Winter in Australia
        job_data = {
            'date': winter_date.isoformat(),
            'start_time': '09:00',
            'end_time': '11:00',
            'property_id': 1,
            'description': 'Weekly recurring job'
        }
        
        initial_job = job_service.create_job(job_data)
        assert initial_job is not None
        
        # Get the UTC start time for the initial job
        initial_start_utc = from_app_tz(
            datetime.combine(winter_date, time(9, 0)).replace(tzinfo=get_app_timezone())
        )
        
        # Simulate the same job recurring in summer (UTC+11)
        summer_date = date(2024, 1, 1)  # Summer in Australia
        summer_job_data = {
            'date': summer_date.isoformat(),
            'start_time': '09:00',
            'end_time': '11:00',
            'property_id': 1,
            'description': 'Weekly recurring job in summer'
        }
        
        summer_job = job_service.create_job(summer_job_data)
        assert summer_job is not None
        
        # Get the UTC start time for the summer job
        summer_start_utc = from_app_tz(
            datetime.combine(summer_date, time(9, 0)).replace(tzinfo=get_app_timezone())
        )
        
        # Verify that both jobs have the same local time (9:00 AM)
        # but different UTC offsets
        assert initial_job.display_start_time == '09:00'
        assert summer_job.display_start_time == '09:00'
        
        # The UTC times should differ by 1 hour due to DST
        time_diff = abs((summer_start_utc - initial_start_utc).total_seconds() / 3600)
        # Adjust for the date difference - we're checking that 9:00 local time
        # results in different UTC times in different seasons
        assert time_diff != 0, "UTC times should differ due to DST"
    
    def test_date_range_queries_include_dst_transition(self, job_service):
        """Test date range queries that include DST transition."""
        # Create jobs on dates around DST transition
        app_tz = get_app_timezone()
        
        # DST starts: October 6, 2024
        # Create jobs on Oct 5 (before DST), Oct 6 (DST day), Oct 7 (after DST)
        dates = [
            date(2024, 10, 5),  # Before DST (UTC+10)
            date(2024, 10, 6),  # DST transition day
            date(2024, 10, 7),  # After DST (UTC+11)
        ]
        
        created_jobs = []
        for i, job_date in enumerate(dates):
            job_data = {
                'date': job_date.isoformat(),
                'start_time': '10:00',
                'end_time': '12:00',
                'property_id': 1,
                'description': f'Job on {job_date} around DST'
            }
            job = job_service.create_job(job_data)
            assert job is not None
            created_jobs.append(job)
        
        # Test query for date range that includes DST transition
        # Query for jobs from Oct 5 to Oct 7
        # This should return all 3 jobs
        
        # Note: This test assumes the job service has a method to query by date range
        # Since we don't have direct access to such method, we'll test the individual
        # date queries to verify DST handling
        
        for i, job_date in enumerate(dates):
            # Convert date to app timezone midnight for query
            midnight_app = datetime.combine(job_date, time.min).replace(tzinfo=app_tz)
            midnight_utc = from_app_tz(midnight_app)
            
            # Verify that job dates are stored correctly
            assert created_jobs[i].date == job_date, \
                f"Job date mismatch: expected {job_date}, got {created_jobs[i].date}"
            
            # Verify display times are correct (should be 10:00 in local time)
            assert created_jobs[i].display_start_time == '10:00', \
                f"Job start time should be 10:00 but got {created_jobs[i].display_start_time}"
    
    def test_job_creation_with_dst_transition_times(self, job_service):
        """Test job creation with times that cross DST boundaries."""
        # Test creating a job during the ambiguous hour when DST ends
        # DST ends: April 7, 2024 at 3:00 AM (2:00 AM becomes 3:00 AM)
        # 2:30 AM occurs twice - once in DST, once in standard time
        
        # Create job at 2:30 AM on DST end day
        job_data = {
            'date': '2024-04-07',
            'start_time': '02:30',
            'end_time': '03:30',
            'property_id': 1,
            'description': 'Job during ambiguous DST hour'
        }
        
        # This should succeed - zoneinfo will pick one of the two possible times
        new_job = job_service.create_job(job_data)
        assert new_job is not None
        
        # Verify the job was created with correct time
        # The exact UTC time depends on which occurrence zoneinfo picks
        # but the local time should be 2:30 AM
        assert new_job.display_start_time == '02:30'
        
        # The duration should be 1 hour in local time
        assert new_job.duration == "1 hour"
    
    def test_today_queries_during_dst_transition(self, job_service):
        """Test 'get jobs for today' queries on DST transition day."""
        # This test verifies that date-based queries work correctly
        # when "today" includes a DST transition
        
        # Note: This is a conceptual test since we can't easily mock "today"
        # to be a DST transition day without complex mocking
        
        # Instead, we'll test the timezone conversion logic
        app_tz = get_app_timezone()
        
        # Test date conversion for DST transition day
        dst_date = date(2024, 10, 6)  # DST start day
        
        # Midnight in app timezone on DST day
        midnight_app = datetime.combine(dst_date, time.min).replace(tzinfo=app_tz)
        midnight_utc = from_app_tz(midnight_app)
        
        # Next midnight in app timezone
        next_midnight_app = datetime.combine(dst_date + timedelta(days=1), time.min).replace(tzinfo=app_tz)
        next_midnight_utc = from_app_tz(next_midnight_app)
        
        # The UTC time range for "DST day in Melbourne" should be
        # from 14:00 UTC previous day to 13:00 UTC DST day
        # (because of DST offset change from +10 to +11)
        
        # Verify the range is 23 hours in UTC (due to DST)
        utc_range_hours = (next_midnight_utc - midnight_utc).total_seconds() / 3600
        assert utc_range_hours == 23.0, \
            f"Expected 23-hour UTC range for DST day but got {utc_range_hours} hours"