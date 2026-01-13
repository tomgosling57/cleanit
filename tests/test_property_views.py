from flask import url_for
from playwright.sync_api import expect
from datetime import datetime, time, timedelta
from config import DATETIME_FORMATS
from tests.helpers import get_first_property_card, login_admin, open_address_book, open_property_card_gallery
from tests.test_utils import get_future_date, get_future_time

def test_address_book(page, goto) -> None:
    login_admin(page, goto)
    open_address_book(page)        
    expect(page.locator("#property-list")).to_be_visible()
    expect(page.get_by_text("All Properties")).to_be_visible()

def test_property_card_gallery_button(page, goto) -> None:
    login_admin(page, goto)
    open_address_book(page)        
    expect(page.locator("#property-list")).to_be_visible()
    expect(page.get_by_text("All Properties")).to_be_visible()

    property_card = get_first_property_card(page)
    expect(property_card).to_be_visible()

    open_property_card_gallery(page, property_card)

    # Wait for the gallery modal to appear
    gallery_modal = page.locator("#media-gallery-modal")
    expect(gallery_modal).to_be_visible()

    # Close the gallery modal
    close_button = gallery_modal.locator(".close-button")
    expect(close_button).to_be_visible()
    close_button.click()

    # Ensure the gallery modal is closed
    expect(gallery_modal).not_to_be_visible()