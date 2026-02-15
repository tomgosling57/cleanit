from controllers.jobs_controller import ERRORS
import pytest
from playwright.sync_api import expect
from tests.helpers import get_csrf_token, make_htmx_request
from utils.timezone import app_now
class TestAlertManager:
    """Tests the javascript alert manager for the frontend client successfully displays messages related from the api via JSON responses."""    

    @pytest.mark.parametrize("endpoint, method, data, expected_message", [
        ("/jobs/job/reassign", "POST", {"job_id": 999,"new_team_id": 1,"old_team_id": 2,"date": app_now().date(),"view_type": "team"}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update_status", "POST", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/delete", "DELETE", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update", "PUT", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update", "GET", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/details", "GET", {}, ERRORS['Job Not Found'])
    ])
    def test_job_not_found_handling(self, admin_page, server_url, endpoint, method, data, expected_message) -> None:
        """Test that the job not found message is displayed in an alert when trying to interact with non-existent job.
        
        Args:
            admin_page: Playwright page object with admin authentication
            server_url: Base URL of the test server"""
        page = admin_page
        make_htmx_request(
            page,
            method,
            server_url + endpoint,
            body=data,
            csrf_token=get_csrf_token(page)
        )
        expect(page.locator(".alert").get_by_text(expected_message)).to_be_visible()
