from datetime import timedelta
from controllers.jobs_controller import ERRORS
from database import Job
import pytest

from tests.db_helpers import get_db_session
from utils.job_helper import ARRIVAL_DATETIME_IN_PAST, INVALID_ARRIVAL_DATE_TIME_FORMAT, INVALID_DATE_OR_TIME_FORMAT, NON_SEQUENTIAL_START_AND_END, START_DATETIME_IN_PAST
from utils.timezone import today_in_app_tz, app_now

class TestJobController:

    def job_data_for_request(self, job_id, job_service, assignment_service, **kwargs):
        job = job_service.get_job_details(job_id)
        if not job:
            raise ValueError(f"Job with id {job_id} not found.")
        job_teams = assignment_service.get_teams_for_job(job_id)
        job_users = assignment_service.get_users_for_job(job_id)
        
        job_data = {
            "property_id": job.property.id,
            "date": job.display_date,
            "start_time": job.display_start_time,
            "end_time": job.display_end_time,
            "arrival_datetime": job.display_arrival_datetime,
            "description": job.description,
            "property_id": job.property.id,
            "assigned_teams": [team.id for team in job_teams],
            "assigned_cleaners": [user.id for user in job_users],
        }
        job_data.update(kwargs)
        return job_data
        
    def test_create_job_no_assignments(self, admin_client_no_csrf):
        """Test that creating a job without any assigned teams or cleaners returns an error."""
        response = admin_client_no_csrf.post(                                     
            "/jobs/job/create",
            data={
                "date": today_in_app_tz().isoformat(),
                "start_time": "10:00",
                "end_time": "12:00",
                "description": "Test job with no assignments",
                "job_type": "standard",
                "property_id": 1,
                # No assigned teams or cleaners
            }
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        json_data = response.get_json()
        assert 'At least one team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

    def test_create_job_empty_assignments(self, admin_client_no_csrf):
        """Test that creating a job with empty assigned teams and cleaners returns an error."""
        response = admin_client_no_csrf.post(                                     
            "/jobs/job/create",
            data={
                "date": today_in_app_tz().isoformat(),
                "start_time": "10:00",
                "end_time": "12:00",
                "description": "Test job with empty assignments",
                "job_type": "standard",
                "property_id": 1,
                "assigned_teams": [],
                "assigned_cleaners": []
            }
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        json_data = response.get_json()
        assert 'At least one team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

    def test_update_job_no_assignments(self, admin_client_no_csrf, admin_user, job_service):
        """Tests that updating a job without any assigned teams or cleaners returns an error."""
        jobs_assigned_to_admin = job_service.get_jobs_for_user_on_date(admin_user.id, admin_user.team_id, today_in_app_tz())
        assert len(jobs_assigned_to_admin) > 0, "No jobs found for admin user to update, please insure the local SQLite test database is seeded with data"
        job_to_update = jobs_assigned_to_admin[0]
        response = admin_client_no_csrf.put(
            f"/jobs/job/{job_to_update.id}/update",
            data={
                "property_id": job_to_update.property.id,
                "date": job_to_update.date.isoformat(),
                "start_time": job_to_update.display_start_time,
                "end_time": job_to_update.display_end_time,
            }
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        
        json_data = response.get_json()
        assert 'At least one team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

    def test_update_job_empty_assignments(self, admin_client_no_csrf, admin_user, job_service, assignment_service):
        """Tests that updating a job with empty assigned teams and cleaners returns an error."""
        jobs_assigned_to_admin = job_service.get_jobs_for_user_on_date(admin_user.id, admin_user.team_id, today_in_app_tz())
        assert len(jobs_assigned_to_admin) > 0, "No jobs found for admin user to update, please insure the local SQLite test database is seeded with data"
        job_to_update = jobs_assigned_to_admin[0]
        response = admin_client_no_csrf.put(
            f"/jobs/job/{job_to_update.id}/update",
            data=self.job_data_for_request(job_to_update.id, job_service, assignment_service, assigned_teams=[], assigned_cleaners=[])
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        json_data = response.get_json()
        assert 'At least one team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"
    
    def test_update_job_to_user_assignment_only(self, admin_client_no_csrf, admin_user, job_service, assignment_service):
        """Tests that updating a job with empty assigned teams and cleaners returns an error."""
        jobs_assigned_to_admin = job_service.get_jobs_for_user_on_date(admin_user.id, admin_user.team_id, today_in_app_tz())
        assert len(jobs_assigned_to_admin) > 0, "No jobs found for admin user to update, please insure the local SQLite test database is seeded with data"
        job_to_update = jobs_assigned_to_admin[0]
        response = admin_client_no_csrf.put(
            f"/jobs/job/{job_to_update.id}/update",
            data=self.job_data_for_request(job_to_update.id, job_service, assignment_service, assigned_teams=[], assigned_cleaners=[admin_user])
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        json_data = response.get_json()
        assert 'At least one team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"
    

    @pytest.mark.parametrize(
        "invalid_attrs,expected_error",
        [
            
            ({"start_time": "invalid-time"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"end_time": "invalid-time"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"date": "invalid-date"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"arrival_datetime": "invalid-datetime"}, INVALID_ARRIVAL_DATE_TIME_FORMAT),
            # Test values with correct format but invalid date/time values
            ({"start_time": "25:00"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"end_time": "25:00"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"date": "2024-02-30"}, INVALID_DATE_OR_TIME_FORMAT),
            ({"arrival_datetime": "2024-02-30T10:00:00"}, INVALID_ARRIVAL_DATE_TIME_FORMAT),
            ({"start_time": "00:00"}, START_DATETIME_IN_PAST),
            # Note: end_time "00:00" is now valid because when it's before start_time,
            # it gets adjusted to 00:00 on the next day (see job_helper.parse_job_datetime)
            # This case has been removed from invalid attributes test
            ({"arrival_datetime": (app_now() - timedelta(days=1)).isoformat()}, ARRIVAL_DATETIME_IN_PAST),
            ({"start_time": "10:00", "end_time": "09:00"}, NON_SEQUENTIAL_START_AND_END),
        ],
        ids=[
            "invalid_start_time_format",
            "invalid_end_time_format",
            "invalid_date_format",
            "invalid_arrival_datetime_format",
            "invalid_start_time_value",
            "invalid_end_time_value",
            "invalid_date_value",
            "invalid_arrival_datetime_value",
            "start_time_in_past",
            # "end_time_in_past" removed - end_time "00:00" is now valid (adjusted to next day)
            "arrival_datetime_in_past",
            "non_sequential_start_end",
        ]
    )
    def test_update_job_invalid_datetime_attributes(
        self, 
        admin_client_no_csrf, 
        admin_user, 
        job_service, 
        assignment_service,
        invalid_attrs,
        expected_error
    ):
        """Tests that updating a job with invalid datetime attributes returns an error."""
        expected_error = expected_error.format(invalid_attrs.get("start_time") or invalid_attrs.get("end_time") or invalid_attrs.get("date") or invalid_attrs.get("arrival_datetime"))
        jobs_assigned_to_admin = job_service.get_jobs_for_user_on_date(
            admin_user.id, admin_user.team_id, today_in_app_tz()
        )
        assert len(jobs_assigned_to_admin) > 0, (
            "No jobs found for admin user to update, please ensure the local SQLite "
            "test database is seeded with data"
        )
        job_to_update = jobs_assigned_to_admin[0]
        
        response = admin_client_no_csrf.put(
            f"/jobs/job/{job_to_update.id}/update",
            data=self.job_data_for_request(
                job_to_update.id, job_service, assignment_service, **invalid_attrs
            )
        )
        
        assert response.status_code == 400, (
            f"Expected status code 400 but got {response.status_code}"
        )
        json_data = response.get_json()
        assert expected_error in json_data.get('message', ''), (
            f"Expected error message '{expected_error}' not found in response"
        )
    @pytest.mark.parametrize("endpoint,method", [
        ("/jobs/job/{}/update", "put"),
        ("/jobs/job/{}/mark_complete", "post"),
        ("/jobs/job/{}/submit_report", "post"),
    ])
    def test_job_not_found(self, admin_client_no_csrf, endpoint, method):
        """Tests that accessing a job that does not exist returns an error."""
        response = admin_client_no_csrf.open(endpoint.format(9999), method=method)
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        json_data = response.get_json()
        assert ERRORS['Job Not Found'] in json_data.get('message', ''), "Expected 'Job Not Found' error message not found in response"


class TestJobControllerDSTEdgeCases:
    """Test class specifically for daylight savings time edge cases in job controller endpoints."""
    
    def test_create_job_with_dst_transition_time(self, admin_client_no_csrf, job_service):
        """Test creating a job with a time during DST transition."""
        # DST starts: First Sunday in October 2026 (October 4, 2026) at 2:00 AM (clocks jump to 3:00 AM)
        # Test creating a job at 3:00 AM on DST start day
        
        response = admin_client_no_csrf.post(
            "/jobs/job/create",
            data={
                "date": "04-10-2026",
                "start_time": "03:00",
                "end_time": "05:00",
                "description": "Job created during DST transition",
                "job_type": "standard",
                "property_id": 1,
                "assigned_teams": [1],
                "assigned_cleaners": [1]
            }
        )
        
        # Job should be created successfully - controller returns HTML for HTMX
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}. Response: {response.data[:500]}"
        
        # Find the created job by its description in the database
        # Since we can't easily get job ID from HTML, we'll query by description
        db = get_db_session()

        created_job = db.query(Job).order_by(Job.id.desc()).first()
        db.close()
        
        assert created_job is not None, "Job was not created in database"
        
        # Verify the job has correct display times
        assert created_job.display_start_time == '03:00', f"Expected display start time 03:00 but got {created_job.display_start_time}"
        assert created_job.display_end_time == '05:00', f"Expected display end time 05:00 but got {created_job.display_end_time}"
    
    def test_create_job_during_ambiguous_dst_hour(self, admin_client_no_csrf, job_service):
        """Test creating a job during the ambiguous hour when DST ends."""
        # DST ends: First Sunday in April 2026 (April 5, 2026) at 3:00 AM (2:00 AM becomes 3:00 AM)
        # 2:30 AM occurs twice - once in DST, once in standard time
        
        response = admin_client_no_csrf.post(
            "/jobs/job/create",
            data={
                "date": "05-04-2026",
                "start_time": "02:30",
                "end_time": "03:30",
                "description": "Job during ambiguous DST hour",
                "job_type": "standard",
                "property_id": 1,
                "assigned_teams": [1],
                "assigned_cleaners": [1]
            }
        )
        
        # Job should be created successfully - controller returns HTML for HTMX
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}. Response: {response.data[:500]}"
        
        db = get_db_session()
        created_job = db.query(Job).order_by(Job.id.desc()).first()
        db.close()
        
        assert created_job is not None, "Job was not created in database"
        
        # Verify the job has correct display times
        assert created_job.display_start_time == '02:30', f"Expected display start time 02:30 but got {created_job.display_start_time}"
        assert created_job.display_end_time == '03:30', f"Expected display end time 03:30 but got {created_job.display_end_time}"
    
    def test_timetable_display_across_dst_boundary(self, admin_client_no_csrf):
        """Test timetable display logic across DST boundaries."""
        # Test accessing timetable on a date that crosses DST boundary
        # DST starts: October 4, 2026
        
        # Access timetable for DST start day
        response = admin_client_no_csrf.get("/jobs/?date=2026-10-04")
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
        
        # The page should load successfully
        # We can't easily verify the rendered HTML without parsing,
        # but a 200 status indicates the date was accepted
        
        # Also test accessing timetable for day after DST start
        response = admin_client_no_csrf.get("/jobs/?date=2024-10-07")
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    
    def test_date_navigation_across_dst_transition(self, admin_client_no_csrf):
        """Test date navigation in controllers across DST transitions."""
        # Test navigating from day before DST to DST day
        # Using the timetable date navigation endpoints
        
        # Note: This test assumes there are date navigation endpoints
        # Since we don't have direct navigation endpoints, we'll test
        # that the timetable works correctly for dates around DST
        
        dates_around_dst = [
            "2026-10-03",  # Day before DST start (October 3, 2026)
            "2026-10-04",  # DST start day (October 4, 2026)
            "2026-10-05",  # Day after DST start (October 5, 2026)
        ]
        
        for test_date in dates_around_dst:
            response = admin_client_no_csrf.get(f"/jobs/?date={test_date}")
            assert response.status_code == 200, f"Failed to load timetable for date {test_date}: {response.status_code}"
            
            # Also test team timetable
            response = admin_client_no_csrf.get(f"/jobs/teams/?date={test_date}")
            assert response.status_code == 200, f"Failed to load team timetable for date {test_date}: {response.status_code}"
    
    def test_job_duration_display_across_dst(self, admin_client_no_csrf, job_service):
        """Test that job duration is displayed correctly across DST transitions."""
        # Create a job that spans DST transition
        # Job from 1:30 AM to 3:30 AM on DST start day (October 4, 2026)
        db = get_db_session()        
        last_job_id = db.query(Job.id).order_by(Job.id.desc()).first()[0] if db.query(Job.id).count() > 0 else 0
        response = admin_client_no_csrf.post(
            "/jobs/job/create",
            data={
                "date": "04-10-2026",
                "start_time": "01:30",
                "end_time": "03:30",
                "notes": "Job spanning DST start",
                "job_type": "standard",
                "property_id": 1,
                "assigned_teams": [1],
                "assigned_cleaners": [1]
            }
        )
        
        # Job should be created successfully - controller returns HTML for HTMX
        assert response.status_code == 200, f"Job creation failed: {response.status_code}. Response: {response.data[:500]}"
        # Find the created job by its description in the database
        created_job = db.query(Job).order_by(Job.id.desc()).first()
        db.close()
        assert created_job.id > last_job_id, "No new job was created in the database"
        assert created_job is not None, "Job was not created in database"
        assert created_job.description is not None
        # Get job details to check duration
        job = job_service.get_job_details(created_job.id)
        if job:
            # Duration should be "2 hours" even though UTC duration is 1 hour
            assert job.duration == "2h", f"Expected duration '2 hours' but got '{job.duration}'"