from datetime import datetime
from time import sleep
from xml.sax.xmlreader import Locator
from playwright.sync_api import expect
import pytest
from config import DATETIME_FORMATS
from services.job_service import JobService
from tests.db_helpers import get_db_session
from tests.helpers import (
    get_first_property_card, 
    open_address_book, 
    open_property_creation_modal,
    fill_property_form,
    submit_property_creation_form,
    submit_property_update_form,
    open_property_update_modal,
    open_property_jobs_modal,
    delete_property,
    assert_property_card_content
)
from utils.timezone import from_app_tz, utc_now

def test_address_book(admin_page) -> None:
    open_address_book(admin_page)
    expect(admin_page.locator("#property-list")).to_be_visible()
    expect(admin_page.get_by_text("All Properties")).to_be_visible()

@pytest.mark.db_reset
def test_create_property(admin_page) -> None:
    """Test creating a new property"""
    page = admin_page
    open_address_book(page)
    
    # Open creation modal
    property_modal = open_property_creation_modal(page)
    
    # Fill form with test data
    test_address = "789 Test Street, Testville"
    test_access_notes = "Key in lockbox, code 5678"
    test_notes = "Test property for automated testing"
    
    fill_property_form(property_modal, test_address, test_access_notes, test_notes)
    sleep(.5)
    
    # Submit form
    submit_property_creation_form(property_modal)
    
    # Wait for property list to update
    expect(page.locator("#property-list")).to_be_visible()
    
    # Find the new property card (should be in the list)
    # We'll look for a property card with the test address
    new_property_card = page.locator(f'.property-card:has(h3:has-text("{test_address}"))')
    new_property_card.wait_for(state='visible', timeout=5000)
    
    # Assert card content
    assert_property_card_content(new_property_card, test_address, test_access_notes, test_notes)

@pytest.mark.db_reset
def test_update_property(admin_page) -> None:
    """Test updating an existing property"""
    page = admin_page
    open_address_book(page)
    
    # Get first property card (Property ID 1: "123 Main St, Anytown" from seeded data)
    property_card = get_first_property_card(page)
    expect(property_card).to_be_visible()
    
    # Open update modal
    property_modal = open_property_update_modal(page, property_card)
    
    # Update form fields
    updated_address = "123 Main St UPDATED, Anytown"
    updated_access_notes = "Updated: Key under doormat"
    updated_notes = "Updated notes for testing"

    fill_property_form(property_modal, updated_address, updated_access_notes, updated_notes)
    
    # Submit form using update-specific helper
    submit_property_update_form(property_modal, property_id=1)
    
    # Wait for property list to update
    expect(page.locator("#property-list")).to_be_visible()
    
    # Find the updated property card
    updated_card = page.locator(f'.property-card:has(h3:has-text("{updated_address}"))')
    expect(updated_card).to_be_visible()
    
    # Assert updated content
    assert_property_card_content(updated_card, updated_address, updated_access_notes, updated_notes)

@pytest.mark.db_reset
def test_delete_property(admin_page) -> None:
    """Test deleting a property"""
    page = admin_page
    open_address_book(page)
    
    # Get first property card
    property_card = get_first_property_card(page)
    expect(property_card).to_be_visible()
    
    # Get the property ID and address before deletion for verification
    property_id = property_card.get_attribute("data-id")
    property_address = property_card.locator("h3").text_content()
    
    # Delete the property
    delete_property(page, property_card)
    
    # Wait for property list to update
    expect(page.locator("#property-list")).to_be_visible()
    
    # Verify property is no longer in the list
    # Check that the specific property card (by ID) is not visible
    deleted_card = page.locator(f'[data-id="{property_id}"]')
    expect(deleted_card).not_to_be_visible()

def test_view_property_jobs(admin_page) -> None:
    """Test viewing jobs for a property"""
    page = admin_page
    open_address_book(page)
    
    # Get first property card
    property_card = get_first_property_card(page)
    expect(property_card).to_be_visible()
    
    # Open jobs modal
    property_modal = open_property_jobs_modal(page, property_card)
    
    # Verify modal is open and has content
    expect(property_modal).to_be_visible()
    
    # Check for jobs content in modal (specific structure depends on template)
    # At minimum, check modal is visible and has some content
    expect(property_modal.locator("h2")).to_be_visible()
    
    # Close modal - use first close button (modal close button)
    property_modal.locator(".close-button").first.click()
    expect(property_modal).not_to_be_visible()

def test_admin_can_access_address_book(admin_page) -> None:
    """Test that admin can access the address book page"""
    page = admin_page
    open_address_book(page)
    
    # Verify address book page loads
    expect(page.locator("#property-list")).to_be_visible()
    expect(page.get_by_text("All Properties")).to_be_visible()

def test_supervisor_cannot_access_address_book(supervisor_page, goto) -> None:
    """Test that supervisor cannot access the address book page"""
    page = supervisor_page
    
    # Supervisor should not see the "Address Book" link in navigation
    # Check that the link is not visible (it's only shown to admins)
    expect(page.get_by_text("Address Book")).not_to_be_visible()
        
    # Try to navigate directly to address book URL
    goto("/address-book/", page)
    
    # Supervisor should not see address book content
    # They might be redirected or see an error/empty state
    # Check that property list is not visible
    expect(page.locator("#property-list")).not_to_be_visible()
    # Supervisor should be redirected to the login page
    expect(page.get_by_text("404")).to_be_visible()

def test_user_cannot_access_address_book(user_page, goto) -> None:
    """Test that regular user cannot access the address book page"""
    page = user_page
    
    # User should not see the "Address Book" link in navigation
    # Check that the link is not visible (it's only shown to admins)
    expect(page.get_by_text("Address Book")).not_to_be_visible()
    
    # Try to navigate directly to address book URL
    goto("/address-book/", page)
    
    # User should not see address book content
    # They might be redirected or see an error/empty state
    # Check that property list is not visible
    expect(page.locator("#property-list")).not_to_be_visible()
    # User should be redirected to the login page
    expect(page.get_by_text("404")).to_be_visible()

def test_job_list_filtering(admin_page) -> None:
    """Test filtering jobs in the property jobs modal"""
    page = admin_page
    open_address_book(page)
    
    # Get first property card
    property_card = page.locator('#property-card-1')
    address = property_card.locator("h3#address").text_content()
    expect(property_card).to_be_visible()
    
    # Open jobs modal
    job_list =open_property_jobs_modal(page, property_card)
    # Verify the contents of the date pickers are formatted correctly 
    assert_filtered_job_list_date_formats(job_list)
    
    # Validate that the jobs displayed match the filter criteria
    assert validate_job_list_date_dividers(job_list) == True, "Job list date dividers do not match filter criteria"
    assert validate_filtered_jobs(job_list) == True, "Filtered jobs do not match filter criteria"

    # Apply various filters and validate results
    # 1. Set start date filter
    set_filter_start_date(job_list, "2024-01-15")
    assert validate_job_list_date_dividers(job_list) == True, "Job list date dividers do not match after setting start date filter"
    assert validate_filtered_jobs(job_list) == True, "Filtered jobs do not match after setting start date filter"

def tick_show_completed_checkbox(job_list: Locator, disable=False) -> None:
    """Helper to tick the 'Show Completed' checkbox in the job list modal. If disable is true it will disable the filter option."""
    show_completed_checkbox = job_list.locator("#show-completed")
    if not show_completed_checkbox.is_checked() and not disable:
        show_completed_checkbox.check()
    if show_completed_checkbox.is_checked() and disable:
        show_completed_checkbox.uncheck()

def tick_show_past_checkbox(job_list: Locator, disable=False) -> None:
    """Helper to update the 'Show Past Jobs' checkbox in the job list modal. If disable is true it will disable the filter option."""
    show_past_checkbox = job_list.locator("#show-past")
    if not show_past_checkbox.is_checked() and not disable:
        show_past_checkbox.check()
    if show_past_checkbox.is_checked() and disable:
        show_past_checkbox.uncheck()

def set_filter_start_date(job_list: Locator, date_str: str) -> None:
    """Helper to set the start date in the job list filter"""
    start_date_display = job_list.locator("#start-date-1")
    start_date_hidden = job_list.locator("#start-date-hidden-1")
    start_date_display.fill(date_str)
    # Trigger change event to update hidden input
    start_date_display.dispatch_event("change")
    # Wait for hidden input to update
    expect(start_date_hidden).to_have_value(date_str)

def set_filter_end_date(job_list: Locator, date_str: str) -> None:
    """Helper to set the end date in the job list filter"""
    end_date_display = job_list.locator("#end-date-1")
    end_date_hidden = job_list.locator("#end-date-hidden-1")
    end_date_display.fill(date_str)
    # Trigger change event to update hidden input
    end_date_display.dispatch_event("change")
    # Wait for hidden input to update
    expect(end_date_hidden).to_have_value(date_str)

def get_filter_display_date_locators(job_list: Locator):
    """Helper to get the display date locators from the job list modal"""
    display_start_date_locator = job_list.locator("#start-date-display-1")
    display_end_date_locator = job_list.locator("#end-date-display-1")
    return display_start_date_locator, display_end_date_locator

def get_filter_hidden_date_locators(job_list: Locator):
    """Helper to get the hidden date locators from the job list modal"""
    hidden_start_date_locator = job_list.locator("#start-date-1")
    hidden_end_date_locator = job_list.locator("#end-date-1")
    return hidden_start_date_locator, hidden_end_date_locator

def assert_filtered_job_list_date_formats(job_list: Locator):
    """Validate that the date pickers in the filtered job list modal have correct formats"""
    display_start_date_locator, display_end_date_locator = get_filter_display_date_locators(job_list)
    hidden_start_date_locator, hidden_end_date_locator = get_filter_hidden_date_locators(job_list)
    assert_date_picker_formats(DATETIME_FORMATS['DATE_FORMAT'], display_start_date_locator, hidden_start_date_locator)  
    assert_date_picker_formats(DATETIME_FORMATS['DATE_FORMAT'], display_end_date_locator, hidden_end_date_locator)

def  convert_date_locator_to_datetime(date_locator: Locator, date_format: str) -> datetime.date:
    """Convert a date locator's hidden input value to a date object"""
    date_str = date_locator.input_value()
    return datetime.strptime(date_str, date_format)

def validate_filtered_jobs(job_list: Locator) -> bool:
    """Helper to validate that jobs in the job list fall within the specified date range"""
    # Convert dates to datetime objects
    hidden_start_date_locator, hidden_end_date_locator = get_filter_hidden_date_locators(job_list)
    start_date = convert_date_locator_to_datetime(hidden_start_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
    end_date = convert_date_locator_to_datetime(hidden_end_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
    # Extract checkbox filter values
    show_completed = job_list.locator("#show-completed").is_checked()
    show_past = job_list.locator("#show-past").is_checked()
    db = get_db_session()
    job_service = JobService(db)
    start_date_utc = from_app_tz(start_date).date()
    end_date_utc = from_app_tz(end_date).date()
    expected_jobs = job_service.get_filtered_jobs_by_property_id(
        property_id=1,
        start_date=start_date_utc,
        end_date=end_date_utc,
        show_past_jobs=show_past,
        show_completed=show_completed
    )
    filtered_jobs_locators = job_list.locator(".job-card")
    # Compare the number of jobs displayed to the number returned from the service
    if filtered_jobs_locators.count() != len(expected_jobs):
        return False
    for i in range(filtered_jobs_locators.count()):
        job_locator = filtered_jobs_locators.nth(i)
        job_id = int(job_locator.get_attribute("data-job-id"))
        # Compare with expected jobs from service
        if job_id != expected_jobs[i].id:
            return False
        # Check that the job date is within the given range
        job_date = expected_jobs[i].date
        if not (start_date_utc <= job_date <= end_date_utc):
            return False
        if not show_completed and expected_jobs[i].is_completed:
            return False
        if not show_past and job_date < utc_now().date():
            return False
    return True

def validate_job_list_date_dividers(job_list: Locator) -> bool:
    """Validate that the date dividers in the job list fall within the specified date range"""
    hidden_start_date_locator, hidden_end_date_locator = get_filter_hidden_date_locators(job_list)
    start_date = convert_date_locator_to_datetime(hidden_start_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
    end_date = convert_date_locator_to_datetime(hidden_end_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
    start_date_utc = from_app_tz(start_date).date()
    end_date_utc = from_app_tz(end_date).date()
    # Get all date dividers in the job list
    date_dividers = job_list.locator(".date-divider")
    # Check that the job divider dates are within the given date range    
    for i in range(date_dividers.count()):
        divider_text = date_dividers.nth(i).text_content().strip().replace("\n", "")
        divider_date = datetime.strptime(divider_text, DATETIME_FORMATS['FULL_MONTH_DATE_FORMAT'])
        divider_date_utc = from_app_tz(divider_date).date()
        if not (start_date_utc <= divider_date_utc <= end_date_utc):
            return False
    return True

def assert_date_picker_formats(expected_format: str, display_input: Locator, hidden_input: Locator) -> None:
    """Helper to assert that date formats in date picker inputs match expected format"""
    # Get values from inputs    
    internal_date = hidden_input.input_value()
    displayed_date = display_input.input_value()
    # Check that the internal value is in ISO format
    assert validate_iso_date_format(internal_date), f"Internal date value '{internal_date}' is not in ISO format"
    # Check that the displayed text matches expected format
    assert validate_date_format(displayed_date, expected_format), f"Displayed date '{displayed_date}' does not match format '{expected_format}'"  

def validate_iso_date_format(date_string: str) -> bool:
    """Check if a date string is in ISO format YYYY-MM-DD"""
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False
    
def validate_date_format(date_string, date_format):
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False
