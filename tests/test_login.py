# tests/test_login.py
from playwright.sync_api import expect

from tests.helpers import login_invalid_credentials, login_owner, login_team_leader

def test_login_owner(page, goto) -> None:
    """
    Tests the login functionality for the owner.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_owner(page, goto)
    expect(page).to_have_title("Timetable") # Assert login was successful
    expect(page.get_by_text("Create Job")).to_be_visible() # Assert owner-specific element is visible

def test_login_team_leader(page, goto) -> None:
    """
    Tests the login functionality for the team leader.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_team_leader(page, goto)
    expect(page).to_have_title("Timetable") # Assert login was successful
    expect(page.get_by_text("Create Job")).to_be_hidden() # Assert owner-specific element is hidden
    
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