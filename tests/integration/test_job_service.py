
from datetime import datetime

from config import DATETIME_FORMATS
from utils.timezone import from_app_tz, get_app_timezone, today_in_app_tz


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