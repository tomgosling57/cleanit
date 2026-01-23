from playwright.sync_api import expect
from pathlib import Path

from tests.helpers import (
    get_first_property_card, 
    open_address_book, 
    open_property_card_gallery,
    assert_gallery_modal_content,
    upload_gallery_media,
)


def jpg_media():
    return ["tests/media/test_image_1.jpg"]

def test_property_card_gallery(admin_page) -> None:
    """
    Test that the property card gallery modal opens and shows expected content.
    Uses test media from tests/media directory with temporary storage configuration.
    """
    # Now run the UI test
    open_address_book(admin_page)
    expect(admin_page.locator("#property-list")).to_be_visible()
    expect(admin_page.get_by_text("All Properties")).to_be_visible()

    property_card = get_first_property_card(admin_page)
    expect(property_card).to_be_visible()

    open_property_card_gallery(admin_page, property_card)
    
    # Assert gallery modal content - should show actual media now
    gallery_modal = admin_page.locator("#media-gallery-modal")
    assert_gallery_modal_content(gallery_modal, expect_media=False)
    
    # Upload test media
    upload_gallery_media(gallery_modal, jpg_media())