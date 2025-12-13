# tests/test_login.py
from playwright.sync_api import expect

from tests.helpers import login_invalid_credentials, login_admin, login_supervisor

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