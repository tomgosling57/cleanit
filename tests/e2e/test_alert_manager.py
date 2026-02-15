from controllers.jobs_controller import ERRORS
import pytest
from playwright.sync_api import expect
from tests.helpers import get_csrf_token, make_htmx_request
from utils.timezone import app_now


class TestAlertManager:
    """Tests the javascript alert manager for the frontend client successfully displays messages related from the api via JSON responses."""
    
    @pytest.mark.parametrize("page_fixture", ["admin_page", "supervisor_page", "user_page"])
    @pytest.mark.parametrize("endpoint, method, data, expected_message", [
        ("/jobs/job/reassign", "POST", {"job_id": 999, "new_team_id": 1, "old_team_id": 2, "date": app_now().date(), "view_type": "team"}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update_status", "POST", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/delete", "DELETE", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update", "PUT", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/update", "GET", {}, ERRORS['Job Not Found']),
        ("/jobs/job/999/details", "GET", {}, ERRORS['Job Not Found'])
    ])
    def test_json_error_handling(self, request, page_fixture, server_url, endpoint, method, data, expected_message) -> None:
        """Test that JSON error messages are displayed in an alert when received in API responses.
        
        Args:
            request: Pytest request object for fixture access
            page_fixture: Name of the page fixture to use (admin_page, supervisor_page, user_page)
            server_url: Base URL of the test server
        """
        # Get the actual fixture by name
        page = request.getfixturevalue(page_fixture)
        
        make_htmx_request(
            page,
            method,
            server_url + endpoint,
            body=data,
            csrf_token=get_csrf_token(page)
        )
        if page.locator(".alert").get_by_text(expected_message).is_visible():
            alert = page.locator(".alert").get_by_text(expected_message)
            expect(alert).to_be_visible()
        else:
            expect(page.locator(".alert")).to_have_text(ERRORS['Unauthorized'])                