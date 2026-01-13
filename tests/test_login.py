# tests/test_login.py
from playwright.sync_api import expect

from tests.helpers import login_invalid_credentials, login_admin, login_supervisor

def test_unauthorized_redirect_to_login(page, goto) -> None:
    """
    Tests that unauthenticated users are redirected to the login page
    when trying to access protected pages, not given JSON responses.
    
    This verifies the fix for the unauthorized handler in app_factory.py.
    
    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    # Should be redirected to login page
    with page.expect_response("**/users/user/login**"):
        # Try to access a protected page without logging in
        # The timetable page requires authentication
        goto("/jobs/")
    

    expect(page.locator("h1")).to_have_text("Login to CleanIt")
    
    # Should show login form, not JSON error
    expect(page.locator('form[action*="/user/login"]')).to_be_visible()
    expect(page.locator('input[name="email"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()

def test_login_admin(page, goto) -> None:
    """
    Tests the login functionality for the admin.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_admin(page, goto)
    expect(page).to_have_title("Timetable") # Assert login was successful
    expect(page.get_by_text("Create Job")).to_be_visible() # Assert admin-specific element is visible

def test_login_supervisor(page, goto) -> None:
    """
    Tests the login functionality for the supervisor.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_supervisor(page, goto)
    expect(page).to_have_title("Timetable") # Assert login was successful
    expect(page.get_by_text("Create Job")).to_be_hidden() # Assert admin-specific element is hidden
    
def test_unauthorized_json_api_returns_json(page, goto) -> None:
    """
    Tests that JSON API requests get JSON responses when unauthorized,
    not HTML redirects.
    
    This verifies the unauthorized handler correctly handles API requests.
    
    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    # Make a JSON request to a protected endpoint
    # We'll use the fetch API to make a request with Accept: application/json header
    response = page.evaluate("""
        async () => {
            const response = await fetch('/users/', {
                headers: {
                    'Accept': 'application/json'
                }
            });
            return {
                status: response.status,
                contentType: response.headers.get('content-type'),
                body: await response.text()
            };
        }
    """)
    
    # Should return 401 Unauthorized with JSON content
    assert response['status'] == 401
    assert 'application/json' in response['contentType']
    # The response should be JSON, not HTML
    import json
    json_response = json.loads(response['body'])
    assert 'error' in json_response
    assert json_response['error'] == 'Unauthorized'

def test_login_invalid_credentials(page, goto) -> None:
    """
    Tests the login functionality with invalid credentials.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_invalid_credentials(page, goto)
    expect(page.get_by_text("Invalid email or password")).to_be_visible() # Assert error
