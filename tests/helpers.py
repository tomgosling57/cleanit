# tests/helpers.py
import re
from playwright.sync_api import expect, Page, Locator
from typing import Optional

def login_with_credentials(page, goto, email, password) -> None:
    """
    Executes the login flow with the given credentials.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    
    goto("/", page)
    page.wait_for_load_state('networkidle')
    csrf = page.locator("input[name=csrf_token]")
    csrf.wait_for(state="attached")
    page.wait_for_function("() => document.querySelector('input[name=csrf_token]')?.value?.length > 0")
    page.locator("#login-form").wait_for(state="attached")
    page.locator("#email").wait_for(state="attached")
    page.locator("#password").wait_for(state="attached")
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill(email)
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill(password)
    expect(page.get_by_role("textbox", name="email")).to_have_value(email)
    expect(page.get_by_role("textbox", name="password")).to_have_value(password)
    
    page.route("**/user/login**", validate_login_request_csrf)
    # Wait for login response and redirect to complete
    with page.expect_response(f"**/user/login**"):
        page.get_by_role("button", name="Login").click()
    page.wait_for_load_state('networkidle')

def validate_login_request_csrf(route, request):
    if "/user/login" in request.url:
        post_data = request.post_data or ""
        cookies = request.headers.get("cookie")

        # Assert session cookie exists
        assert cookies and "session" in cookies, "Session cookie missing in login POST"

        # Assert CSRF token exists in the POST body
        assert "csrf_token=" in post_data, "CSRF token missing in login POST"

    # Continue the request normally
    route.continue_()

def login_admin(page, goto) -> None:
    """
    Executes the login flow for the admin user.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    """
    with page.expect_response("**/jobs**"):
        login_with_credentials(page, goto, "admin@example.com", "admin_password")
    page.wait_for_load_state('networkidle')

def login_supervisor(page, goto) -> None:
    """
    Executes the login flow for the supervisor.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    """
    
    with page.expect_response("**/jobs**"):
        login_with_credentials(page, goto, "supervisor@example.com", "supervisor_password")
    page.wait_for_load_state('networkidle')

def login_user(page, goto) -> None:
    """
    Executes the login flow for the user.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    """
    with page.expect_response("**/jobs**"):
        login_with_credentials(page, goto, "user@example.com", "user_password")
    page.wait_for_load_state('networkidle')

def login_invalid_credentials(page, goto) -> None:
    """
    Executes the login flow with invalid credentials.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    login_with_credentials(page, goto, "invalid@example.com", "wrong_password")

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
    csrf_token: str,
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

    with page.expect_response(endpoint):
        page.wait_for_load_state('networkidle')
        page.evaluate(
            f"""
            async ([method, endpoint, htmx_values, expected_fragment_locator]) => {{
                const headers = {{
                    'HX-Request': 'true',
                    'HX-Trigger': 'test-trigger',
                    'X-CSRFToken': '{csrf_token}'
                }};
                for (const key in htmx_values) {{
                    headers[`HX-Current-URL`] = htmx_values[key];
                }}

                const options = {{
                    method: method,
                    headers: headers
                }};

                const response = await fetch(endpoint, options);
                const html = await response.text();
                document.getElementById(expected_fragment_locator).innerHTML = html;
            }}
            """,
            [method, endpoint, htmx_values, expected_fragment_locator]
        )
        expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()

def get_csrf_token(page: Page) -> str:
    """Gets the CSRF token from the page's body data attribute."""
    return page.locator('body').get_attribute('data-csrf-token')

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
    page.locator("#time").wait_for(state="attached")
    page.locator("#end_time").wait_for(state="attached")
    page.locator("#date").wait_for(state="attached")
    page.locator("#description").wait_for(state="attached")
    page.locator("#property_id").wait_for(state="attached")
    page.locator('input[type="text"].flatpickr').wait_for(state="attached")
    page.locator("#access_notes").wait_for(state="attached")
    page.locator("#assigned_teams").wait_for(state="attached")
    page.locator("#assigned_cleaners").wait_for(state="attached")
    
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
    page.locator(".teams-grid").wait_for(state="attached")

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

def open_address_book(page: Page) -> None:
    """Navigate to the address book page"""
    page.wait_for_selector("a[href='/address-book/']") 
    with page.expect_response("**/address-book**"):
        page.wait_for_load_state('networkidle')
        page.get_by_text("Address Book").click()

    page.wait_for_load_state('networkidle')

def get_first_property_card(page: Page) -> Locator:
    return page.locator(".property-card").first

def open_property_details(page: Page, property_card) -> None:
    """Open the details of a property from the address book"""
    property_card.locator(".edit-button").wait_for(state="attached")
    property_id = property_card.get_attribute("data-id")
    with page.expect_response(f"**/property/{property_id}/update**"):
        page.wait_for_load_state('networkidle')
        property_card.locator(f".edit-button").click()
    
    page.wait_for_load_state('networkidle')
    expect(page.locator("#property-details-modal")).to_be_visible()

def open_property_card_gallery(page: Page, property_card: Locator) -> None:
    """Open the gallery modal from a property card"""
    property_card.locator(".gallery-button").wait_for(state="attached")
    property_id = property_card.get_attribute("data-id")
    with page.expect_response(f"**/address-book/property/{property_id}/media**"):
        page.wait_for_load_state('networkidle')
        property_card.locator(".gallery-button").click()

    expect(page.locator("#media-gallery-modal")).to_be_visible()


def assert_gallery_modal_content(page: Page) -> None:
    """
    Asserts the gallery modal structure and content.
    Since no actual images exist in test, checks for placeholder.
    When media fails to load or no media exists, thumbnail container may be hidden.
    """
    gallery_modal = page.locator("#media-gallery-modal")
    expect(gallery_modal).to_be_visible()
    
    # Check modal title using CSS selector
    expect(gallery_modal.locator("#gallery-modal-title")).to_have_text("Media Gallery")
    
    # Check media counter (shows "1 / 0" when no media)
    expect(gallery_modal.locator("#current-index")).to_be_visible()
    expect(gallery_modal.locator("#total-count")).to_be_visible()
    
    # Check navigation buttons using CSS classes
    expect(gallery_modal.locator(".prev-button")).to_be_visible()
    expect(gallery_modal.locator(".next-button")).to_be_visible()
    
    # Check media description area
    expect(gallery_modal.locator("#media-description-text")).to_be_visible()
    
    # Check gallery footer with actions
    expect(gallery_modal.locator("#download-button")).to_be_visible()
    expect(gallery_modal.locator("#fullscreen-button")).to_be_visible()
    
    # Check placeholder image is shown (image-not-found.png)
    # The placeholder div should be visible when no media exists
    placeholder = gallery_modal.locator("#media-placeholder")
    expect(placeholder).to_be_visible()
    expect(placeholder.locator('img[src*="image-not-found.png"]')).to_be_visible()
    
    # Note: thumbnail container (#thumbnail-container) may be hidden when no media exists
    # This is acceptable behavior for the "media not successfully loaded" case


def open_property_creation_modal(page: Page) -> None:
    """Open the create property modal"""
    page.wait_for_selector("button:has-text('Create Property')") 
    with page.expect_response("**/address-book/property/create**"):
        page.wait_for_load_state('networkidle')
        page.locator('button:has-text("Create Property")').click()
    
    expect(page.locator("#property-modal")).to_be_visible()


def fill_property_form(
    page: Page, 
    address: str, 
    access_notes: str = "", 
    notes: str = ""
) -> None:
    """Fill the property form fields"""
    page.locator("#address").wait_for(state="attached")
    page.locator("#access_notes").wait_for(state="attached")
    page.locator("#notes").wait_for(state="attached")
    page.locator("#address").fill(address)
    if access_notes:
        page.locator("#access_notes").fill(access_notes)
    if notes:
        page.locator("#notes").fill(notes)


def submit_property_creation_form(page: Page) -> None:
    """Submit the property form (for creation)"""
    page.locator("#property-modal button[type='submit']").wait_for(state="attached")
    with page.expect_response("**/address-book/property/create**"):
        page.wait_for_load_state('networkidle')
        page.locator('#property-modal button[type="submit"]').click()
    
    page.wait_for_load_state('networkidle')

def submit_property_update_form(page: Page, property_id: int) -> None:
    """Submit the property update form"""
    page.locator("#property-modal button[type='submit']").wait_for(state="attached")
    with page.expect_response(f"**/address-book/property/{property_id}/update**"):
        page.wait_for_load_state('networkidle')
        page.locator('#property-modal button[type="submit"]').click()

    page.wait_for_load_state('networkidle')

def open_property_update_modal(page: Page, property_card: Locator) -> None:
    """Open the update modal for a property"""
    property_card.locator(".edit-button").wait_for(state="attached")
    property_id = property_card.get_attribute("data-id")
    with page.expect_response(f"**/property/{property_id}/update**"):
        page.wait_for_load_state('networkidle')
        property_card.locator(".edit-button").click()
    
    page.wait_for_load_state('networkidle')
    expect(page.locator("#property-modal")).to_be_visible()


def open_property_jobs_modal(page: Page, property_card: Locator) -> None:
    """Open the view jobs modal for a property"""
    property_card.locator(".view-jobs-button").wait_for(state="attached")
    property_id = property_card.get_attribute("data-id")
    with page.expect_response(f"**/property/{property_id}/jobs**"):
        page.wait_for_load_state('networkidle')
        property_card.locator(".view-jobs-button").click()

    page.wait_for_load_state('networkidle')    
    expect(page.locator("#property-modal")).to_be_visible()


def delete_property(page: Page, property_card: Locator) -> None:
    """Delete a property with confirmation"""
    property_id = property_card.get_attribute("data-id")
    
    # Set up dialog handler to accept confirmation
    page.once('dialog', lambda dialog: dialog.accept())
    
    with page.expect_response(f"**/property/{property_id}/delete**"):
        page.wait_for_load_state('networkidle')
        # Find delete button by CSS class
        property_card.locator(".property-delete-button").click()

    page.wait_for_load_state('networkidle')

def assert_property_card_content(
    property_card: Locator,
    address: str,
    access_notes: str = None,
    notes: str = None
) -> None:
    """Assert the content of a property card using CSS selectors"""
    # Check address in h3 tag
    expect(property_card.locator("h3")).to_have_text(address)
    
    # Check address line - find the paragraph containing "Address:" text
    # Using CSS selector to find p tag that contains strong with text "Address:"
    address_paragraph = property_card.locator('p:has(strong:has-text("Address:"))')
    expect(address_paragraph).to_be_visible()
    expect(address_paragraph).to_contain_text(address)
    
    if access_notes:
        # Check access notes - find paragraph containing "Access Notes:"
        access_notes_paragraph = property_card.locator('p:has(strong:has-text("Access Notes:"))')
        expect(access_notes_paragraph).to_be_visible()
        expect(access_notes_paragraph).to_contain_text(access_notes)
    
    if notes:
        # Check additional notes - find paragraph containing "Additional Notes:"
        notes_paragraph = property_card.locator('p:has(strong:has-text("Additional Notes:"))')
        expect(notes_paragraph).to_be_visible()
        expect(notes_paragraph).to_contain_text(notes)

def validate_csrf_token_in_modal(modal: Locator) -> None:
    """Validate that the CSRF token input in the modal is present and has a value"""
    csrf_input = modal.locator("input[name=csrf_token]")
    csrf_input.wait_for(state="attached")
    assert csrf_input.input_value(), "CSRF token input is empty in modal"