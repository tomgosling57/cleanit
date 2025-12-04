# tests/helpers.py
from playwright.sync_api import expect

def login_owner(page, goto) -> None:
    """
    Executes the login flow for the owner.

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
    page.get_by_role("textbox", name="password").fill("owner_password")
    page.get_by_role("button", name="Login").click()

def login_team_leader(page, goto) -> None:
    """
    Executes the login flow for the team leader.

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

def login_cleaner(page, goto) -> None:
    """
    Executes the login flow for the cleaner.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    
    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("cleaner@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("cleaner_password")
    page.get_by_role("button", name="Login").click()

def login_invalid_credentials(page, goto) -> None:
    """
    Executes the login flow with invalid credentials.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("invalid@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("wrong_password")
    page.get_by_role("button", name="Login").click()

def assert_job_card_variables(job_card, expected_variables: dict, expected_indicators: list = None) -> None:
    """
    Asserts that a job card contains the expected variables and their values, and optionally, expected indicators.

    Args:
        job_card: Playwright Locator for the job card.
        expected_variables: A dictionary where keys are variable names and values are their expected text content.
        expected_indicators: An optional list of strings representing indicators that should be visible.
    Returns:
        None
    """
    for key, value in expected_variables.items():
        expect(job_card.get_by_text(value)).to_be_visible()
    
    if expected_indicators:
        for indicator in expected_indicators:
            expect(job_card.get_by_text(indicator)).to_be_visible()
            if indicator == 'Back to Back':
                expect(job_card).to_have_css('border', '2px solid rgb(255, 0, 0)')
                expect(job_card).to_have_css('box-shadow', 'rgba(255, 0, 0, 0.5) 0px 0px 10px 0px')
                

def mark_job_as_complete(job_card) -> None:
    """
    Marks a job as complete from its job card.

    Args:
        job_card: Playwright Locator for the job card.
    Returns:
        None
    """
    job_card.get_by_text("Pending").click()
    job_card.get_by_role("button", name="Mark Complete").click()
    expect(job_card.get_by_text("Completed")).to_be_visible()

def wait_for_modal(page, id: str):
    """
    Waits for the job modal to be visible on the page.
    Args:
        page: The page pytest-playwright fixture representing the current browser page.
    Returns:
        The modal locator once it is visible.
    """
    modal = page.locator("#job-modal")
    modal.wait_for(state="attached")
    modal.wait_for(state="visible")
    return modal
