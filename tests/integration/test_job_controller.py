import pytest

from services.assignment_service import AssignmentService
from services.job_service import JobService
from tests.db_helpers import get_db_session
from utils.timezone import today_in_app_tz

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
        assert 'At least one cleaner or team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

    def tests_create_job_empty_assignments(self, admin_client_no_csrf):
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
        assert 'At least one cleaner or team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

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
        assert 'At least one cleaner or team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"

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
        assert 'At least one cleaner or team must be assigned to the job.' in json_data.get('message', ''), "Expected error message about missing assignments not found in response"