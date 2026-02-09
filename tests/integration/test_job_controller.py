import pytest

from services.job_service import JobService
from tests.db_helpers import get_db_session
from utils.timezone import today_in_app_tz

class TestJobController:

    def setup_method(self):
        self.db = get_db_session()
        self.job_service = JobService(self.db)
        
    def test_create_job_no_assignments(self, admin_client_no_csrf):
        """Test that creating a job without any assigned teams or cleaners returns an error."""
        response = admin_client_no_csrf.post(
            "/jobs/job/create",
            data={
                "date_str": today_in_app_tz().isoformat(),
                "start_time_str": "10:00",
                "end_time_str": "12:00",
                "description": "Test job with no assignments",
                "job_type": "standard",
                "property_id": 1,
                # No assigned teams or cleaners
            }
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        assert b'At least one cleaner or team must be assigned to the job.' in response.data, "Expected error message about missing assignments not found in response"

    def test_update_job_no_assignments(self, admin_client_no_csrf, admin_user):
        """Tests that updating a job without any assigned teams or cleaners returns an error."""
        jobs_assigned_to_admin = self.job_service.get_jobs_for_user_on_date(admin_user.id, admin_user.team_id, today_in_app_tz())
        assert len(jobs_assigned_to_admin) > 0, "No jobs found for admin user to update, please insure the local SQLite test database is seeded with data"
        job_to_update = jobs_assigned_to_admin[0]
        response = admin_client_no_csrf.put(
            f"/jobs/job/{job_to_update.id}/update",
            data={
                "assigned_cleaners": [],
                "assigned_teams": []
            }
        )
        assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"
        assert b'At least one cleaner or team must be assigned to the job.' in response.data, "Expected error message about missing assignments not found in response"