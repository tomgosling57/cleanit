# tests/test_login.py
from playwright.sync_api import expect

def test_login_owner(page, goto) -> None:
    """
    Tests the login functionality for the owner.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("owner@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("ownerpassword")
    page.get_by_role("button", name="Login").click()
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
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("team_leader@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("team_leader_password")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_title("Timetable") # Assert login was successful
    expect(page.get_by_text("Create Job")).to_be_hidden() # Assert owner-specific element is hidden
