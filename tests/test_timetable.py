# tests/test_timetable.py
from playwright.sync_api import expect
from tests.helpers import login_team_leader


def test_team_leaders_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a team leader.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_team_leader(page, goto)
    page.get_by_text("Property Address: 456 Oak Ave").click()
    page.get_by_text("Time: 10:").click()
    page.get_by_text("Ends: 12:00 (2h)").click()
    page.locator(".status-text").get_by_text("Pending").click()
    page.get_by_role("button", name="Mark Complete").click()
    expect(page.locator(".status-text").get_by_text("Completed")).to_be_visible()
    page.get_by_text("Same Day Arrival").click()
    page.get_by_role("button", name="View Details").click()
    page.locator("#job-modal").get_by_text("×").click()