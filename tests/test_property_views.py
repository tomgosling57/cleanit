from playwright.sync_api import expect
import pytest
from tests.helpers import (
    get_first_property_card, 
    login_admin, 
    login_supervisor, 
    login_user,
    open_address_book, 
    open_property_card_gallery,
    assert_gallery_modal_content,
    open_property_creation_modal,
    fill_property_form,
    submit_property_creation_form,
    submit_property_update_form,
    open_property_update_modal,
    open_property_jobs_modal,
    delete_property,
    assert_property_card_content
)
from tests.test_utils import get_future_date, get_future_time

def test_address_book(admin_page) -> None:
    open_address_book(admin_page)
    expect(admin_page.locator("#property-list")).to_be_visible()
    expect(admin_page.get_by_text("All Properties")).to_be_visible()

def test_create_property(admin_page) -> None:
    """Test creating a new property"""
    page = admin_page
    open_address_book(page)
    
    # Open creation modal
    open_property_creation_modal(page)
    
    # Fill form with test data
    test_address = "789 Test Street, Testville"
    test_access_notes = "Key in lockbox, code 5678"
    test_notes = "Test property for automated testing"
    
    fill_property_form(page, test_address, test_access_notes, test_notes)
    
    # Submit form
    submit_property_creation_form(page)
    
    # Wait for property list to update
    expect(page.locator("#property-list")).to_be_visible()
    
    # Find the new property card (should be in the list)
    # We'll look for a property card with the test address
    new_property_card = page.locator(f'.property-card:has(h3:has-text("{test_address}"))')
    expect(new_property_card).to_be_visible()
    
    # Assert card content
    assert_property_card_content(new_property_card, test_address, test_access_notes, test_notes)

def test_update_property(admin_page) -> None:
    """Test updating an existing property"""
    page = admin_page
    open_address_book(page)
    
    # Get first property card (Property ID 1: "123 Main St, Anytown" from seeded data)
    property_card = get_first_property_card(page)
    expect(property_card).to_be_visible()
    
    # Open update modal
    open_property_update_modal(page, property_card)
    
    # Update form fields
    updated_address = "123 Main St UPDATED, Anytown"
    updated_access_notes = "Updated: Key under doormat"
    updated_notes = "Updated notes for testing"
    
    fill_property_form(page, updated_address, updated_access_notes, updated_notes)
    
    # Submit form using update-specific helper
    submit_property_update_form(page, property_id=1)
    
    # Wait for property list to update
    expect(page.locator("#property-list")).to_be_visible()
    
    # Find the updated property card
    updated_card = page.locator(f'.property-card:has(h3:has-text("{updated_address}"))')
    expect(updated_card).to_be_visible()
    
    # Assert updated content
    assert_property_card_content(updated_card, updated_address, updated_access_notes, updated_notes)

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
    open_property_jobs_modal(page, property_card)
    
    # Verify modal is open and has content
    modal = page.locator("#property-modal")
    expect(modal).to_be_visible()
    
    # Check for jobs content in modal (specific structure depends on template)
    # At minimum, check modal is visible and has some content
    expect(modal.locator("h2")).to_be_visible()
    
    # Close modal - use first close button (modal close button)
    modal.locator(".close-button").first.click()
    expect(modal).not_to_be_visible()

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