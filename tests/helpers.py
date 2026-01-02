# tests/helpers.py
import re
from playwright.sync_api import expect, Page, Locator
from typing import Optional

def login_admin(page, goto) -> None:
    """
    Executes the login flow for the admin.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("admin@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("admin_password")
    page.get_by_role("button", name="Login").click()

def login_supervisor(page, goto) -> None:
    """
    Executes the login flow for the supervisor.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("supervisor@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("supervisor_password")
    page.get_by_role("button", name="Login").click()

def login_user(page, goto) -> None:
    """
    Executes the login flow for the user.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    
    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("user@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("user_password")
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
                

def mark_job_as_complete(page, job_card) -> None:
    """
    Marks a job as complete from its job card.

    Args:
        job_card: Playwright Locator for the job card.
    Returns:
        None
    """
    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update_status**"):    
        page.wait_for_load_state('networkidle')
        job_card.get_by_role("button", name="Mark Complete").click()
        
    expect(job_card.get_by_text("Mark Pending")).to_be_visible()
    expect(job_card).to_have_class(re.compile(r"completed"))

def delete_job_and_confirm(page: Page, job_card: Locator) -> None:
    """
    Deletes a job and confirms the deletion through a dialog.

    Args:
        page: Playwright Page object.
        job_card: Playwright Locator for the job card to be deleted.
    Returns:
        None
    """
    page.on('dialog', lambda d: d.accept())
    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/delete**"):
        page.wait_for_load_state('networkidle')
        job_card.locator(".job-close-button").click()
    expect(job_card).to_be_hidden()

def wait_for_modal(page, id: str):
    """
    Waits for the job modal to be visible on the page.
    Args:
        page: The page pytest-playwright fixture representing the current browser page.
    Returns:
        The modal locator once it is visible.
    """
    modal = page.locator(id)
    modal.wait_for(state="attached")
    return modal


from playwright.sync_api import expect, Page, Locator
from typing import Optional

def assert_job_card_default_state(job_card_locator: Locator) -> None:
    expect(job_card_locator.get_by_text("See Notes")).not_to_be_visible()
    expect(job_card_locator).not_to_have_class(re.compile(r"red-outline"))

def assert_job_not_found_htmx_error(
    page: Page,
    server_url: str,
    method: str,
    endpoint: str,
    expected_fragment_locator: str,
    htmx_values: Optional[dict] = None,
    team_view: bool = False
) -> None:
    if htmx_values is None:
        htmx_values = {}

    if team_view:
        page.get_by_text('Team View').click()
        expect(page.locator("#team-columns-container")).to_be_visible()
    else:
        expect(page.locator("#job-list")).to_be_visible()

    page.evaluate(
        """
        async ([method, endpoint, htmx_values, expected_fragment_locator]) => {
            const headers = {
                'HX-Request': 'true',
                'HX-Trigger': 'test-trigger'
            };
            for (const key in htmx_values) {
                headers[`HX-Current-URL`] = htmx_values[key];
            }

            const options = {
                method: method,
                headers: headers
            };

            const response = await fetch(endpoint, options);
            const html = await response.text();
            document.getElementById(expected_fragment_locator).innerHTML = html;
        }
        """,
        [method, endpoint, htmx_values, expected_fragment_locator]
    )
    page.wait_for_load_state('networkidle')
    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()

def get_first_job_card(page: Page) -> Locator:
    return page.locator(".job-card").first

def open_job_details_modal(page: Page, job_card: Locator, url_pattern: str) -> None:
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        job_card.get_by_role("button", name="View Details").click()
    expect(page.locator("#job-modal")).to_be_visible()

def open_job_update_modal(page: Page, job_card: Locator, url_pattern: str) -> None:
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        job_card.get_by_role("button", name="Edit").click()
    expect(page.locator("#job-modal")).to_be_visible()

def fill_job_modal_form(
    page: Page,
    start_time: str,
    end_time: str,
    date: str,
    description: str,
    property_id: str,
    arrival_datetime: str,
    access_notes: str,
    assigned_teams: list[str],
    assigned_cleaners: list[str],
) -> None:
    page.locator("#time").fill(start_time)
    page.locator("#end_time").fill(end_time)
    page.locator("#date").fill(date)
    page.locator("#description").fill(description)
    page.locator("#property_id").select_option(property_id)
    page.locator('input[type="text"].flatpickr').fill(arrival_datetime)
    page.locator("#access_notes").fill(access_notes)
    page.locator("#assigned_teams").select_option(assigned_teams)
    page.locator("#assigned_cleaners").select_option(assigned_cleaners)

def assert_job_details_modal_content(
    page: Page,
    modal_id: str,
    title: str,
    start_time: str,
    end_time: str,
    arrival_date: str,
    arrival_time: str,
    description: str,
    property_address: str,
    assigned_team: str,
    assigned_cleaner: str,
) -> None:
    modal = page.locator(modal_id)
    expect(modal.locator("h2")).to_have_text(title)
    expect(modal.get_by_text(f"Start: {start_time}")).to_be_visible()
    expect(modal.get_by_text(f"End: {end_time}")).to_be_visible()
    expect(modal.get_by_text(f"Arrives: {arrival_date}")).to_be_visible()
    expect(modal.get_by_text(f"Time: {arrival_time}")).to_be_visible()
    expect(modal.get_by_text(description)).to_be_visible()
    expect(modal.get_by_text(property_address)).to_be_visible()
    expect(modal.get_by_text(assigned_team)).to_be_visible()
    expect(modal.get_by_text(assigned_cleaner)).to_be_visible()

def close_modal_and_assert_hidden(page: Page, modal_id: str) -> None:
    modal = page.locator(modal_id)
    modal.get_by_text("×").click()
    expect(modal).to_be_hidden()

def assert_team_column_content(team_column_locator: Locator, team_name: str, expected_job_count: int) -> None:
    expect(team_column_locator.get_by_text(team_name)).to_be_visible()
    expect(team_column_locator.locator('div.job-card')).to_have_count(expected_job_count)

def setup_team_page(page: Page) -> None:
    page.get_by_text("Teams").click()
    page.locator(".teams-grid").wait_for()

def get_all_team_cards(page: Page) -> Locator:
    return page.locator(".team-card")

def assert_modal_title(page: Page, modal_id: str, title: str) -> None:
    modal = page.locator(modal_id)
    expect(modal.locator("h2")).to_have_text(title)

def close_modal(page: Page, modal_id: str) -> None:
    modal = page.locator(modal_id)
    modal.get_by_text("×").click()
    expect(modal).to_be_hidden()

def click_and_wait_for_response(page: Page, locator: Locator, url_pattern: str) -> None:
    """
    Clicks a locator and waits for a specific network response and network idle state.
    """
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        locator.click()

def drag_to_and_wait_for_response(page: Page, source_locator: Locator, target_locator: Locator, url_pattern: str) -> None:
    """
    Drags a source locator to a target locator and waits for a specific network response and network idle state.
    """
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        source_locator.drag_to(target_locator)
    

def simulate_htmx_delete_and_expect_response(page: Page, server_url: str, endpoint: str, target_id: str) -> Page.expect_response:
    """
    Simulates an HTMX DELETE request and waits for the corresponding network response.
    """
    with page.expect_response(f"**{endpoint}**") as response_info:
        page.evaluate(f"""
            htmx.ajax('DELETE', '{server_url}{endpoint}', {{
                target: '{target_id}',
                swap: 'innerHTML'
            }})
        """)
    return response_info
