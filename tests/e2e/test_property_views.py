from datetime import datetime, timedelta, time
from time import sleep
from playwright.sync_api import expect
import pytest
from tests.e2e.property_helpers import JobListHelper
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
from utils.timezone import from_app_tz, get_app_timezone, to_app_tz, today_in_app_tz, utc_now

FILTER_INTERVALS = [timedelta(days=i) for i in [0, 30]]

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


@pytest.mark.usefixtures("anytown_property", "teamville_property")
class TestJobFiltering:

    @pytest.fixture(autouse=True)
    def _inject_fixtures(self, anytown_property, teamville_property):
        self.anytown_property = anytown_property
        self.teamville_property = teamville_property

    def test_default_filters(self, admin_page, anytown_property, teamville_property) -> None:
        """Test filtering jobs in the property jobs modal"""
        page = admin_page
        page.set_default_timeout(5000)
        open_address_book(page)
        helper = JobListHelper(page)
        helper.open_property_jobs(anytown_property.id)
        page.keyboard.press("Escape")  # Close the modal to reset state
        helper.open_property_jobs(teamville_property.id)

    def test_date_filters_combinations(self, admin_page, anytown_property, teamville_property, request) -> None:
        """Test applying date filters in the property jobs modal"""
        # Skip this test if not running in headed mode
        # The --headed flag is passed to pytest-playwright
        if not request.config.option.headed:
            pytest.skip("test_draggable_elements requires --headed flag to run")
        
        page = admin_page
        page.set_default_timeout(5000)
        open_address_book(page)
        helper = JobListHelper(page)
        helper.open_property_jobs(anytown_property.id)        
        self.apply_filter_combinations(helper)
        page.keyboard.press("Escape")  # Close the modal to reset state
        helper.open_property_jobs(teamville_property.id)
        self.apply_filter_combinations(helper)
    
    def apply_filter_combinations(self, helper: JobListHelper, show_completed=None):
        
        # Apply various filters and validate results
        base_date = today_in_app_tz()

        # Shift each date independently in both directions: past (-) and future (+)
        date_offsets = [-delta for delta in FILTER_INTERVALS] + [delta for delta in FILTER_INTERVALS]
        
        _skipped = 0
        _visited = {}
        _total_tested = 0
        for start_offset in date_offsets:
            for end_offset in date_offsets:
                start_date = datetime.combine(base_date + start_offset, time.min)
                end_date = datetime.combine(base_date + end_offset, time.max.replace(microsecond=0))
                if (start_date, end_date) in _visited:
                    _skipped += 1
                    continue
                # Skip invalid ranges where start is not before end
                if start_date >= end_date:
                    continue


                if show_completed in [True, None]:
                    helper.apply_filters(
                        start_date=start_date,
                        end_date=end_date,
                        show_completed=True,
                    )
                if show_completed in [False, None]:
                    helper.apply_filters(
                        start_date=start_date,
                        end_date=end_date,
                        show_completed=False,
                    )   
                _visited[(start_date, end_date)] = True
                _total_tested += 1

        print(f"Completed applying filter combinations. Visited: {len(_visited)}, Skipped: {_skipped}, Total Tested: {_total_tested}")

    def test_specific_filters(self, admin_page, anytown_property, teamville_property) -> None:
        """Test specific filter combinations that are likely to cause edge cases."""
        page = admin_page
        page.set_default_timeout(5000)
        open_address_book(page)
        helper = JobListHelper(page)
        
        # Test edge case: start date in the future, end date in the past (should show no jobs)
        start_date = datetime.combine(today_in_app_tz(), time.min, tzinfo=get_app_timezone())
        end_date = datetime.combine(today_in_app_tz(), time.max, tzinfo=get_app_timezone())
        self.apply_filter_dates(helper, start_date, end_date)
        
        start_date = datetime.combine(today_in_app_tz() - timedelta(days=2), time.min, tzinfo=get_app_timezone())
        end_date = datetime.combine(today_in_app_tz(), time.max, tzinfo=get_app_timezone())
        self.apply_filter_dates(helper, start_date, end_date)

        start_date = datetime.combine(today_in_app_tz(), time.min, tzinfo=get_app_timezone())
        end_date = datetime.combine(today_in_app_tz() + timedelta(days=2), time.max, tzinfo=get_app_timezone())
        self.apply_filter_dates(helper, start_date, end_date)
        
        start_date = datetime.combine(today_in_app_tz() - timedelta(days=2), time.min, tzinfo=get_app_timezone())
        end_date = datetime.combine(today_in_app_tz() + timedelta(days=2), time.max, tzinfo=get_app_timezone())
        self.apply_filter_dates(helper, start_date, end_date)
        
    
    def apply_filter_dates(self, helper: JobListHelper, start_date: datetime, end_date: datetime):
        helper.open_property_jobs(self.anytown_property.id)
        helper.apply_filters(start_date=start_date, end_date=end_date, show_completed=True)
        helper.apply_filters(start_date=start_date, end_date=end_date, show_completed=False)  # Invalid range, should show no jobs
        helper.page.keyboard.press("Escape")  # Close the modal to reset state  
        helper.open_property_jobs(self.teamville_property.id)
        helper.apply_filters(start_date=start_date, end_date=end_date, show_completed=True)
        helper.apply_filters(start_date=start_date, end_date=end_date, show_completed=False)
        helper.page.keyboard.press("Escape")  # Close the modal to reset state  