from playwright.sync_api import expect
from pathlib import Path

from tests.helpers import (
    get_first_property_card, 
    open_address_book,
    open_job_details_modal, 
    open_property_gallery,
    open_timetable,
    get_first_job_card,
)
from tests.gallery_helpers import (
    delete_all_gallery_media, upload_gallery_media, assert_gallery_modal_content,
)
from tests.job_helpers import (
    open_job_report,
    fill_job_report_and_submit,
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

    open_property_gallery(admin_page, property_card, property_card.get_attribute("data-id"))
    
    # Assert gallery modal content - should show actual media now
    gallery_modal = admin_page.locator("#media-gallery-modal")
    assert_gallery_modal_content(gallery_modal, expect_media=False)
    
    # Upload test media
    upload_gallery_media(gallery_modal, jpg_media())

    # Delete test media
    delete_all_gallery_media(gallery_modal)
    

def test_job_property_gallery_continuity(admin_page) -> None:
    """
    Test that the property gallery modal open from the job details view shows the media for the property associated with the job. 
    To ensure continuity, the test will upload the media via the property card gallery first, then open the job property gallery
    via the job modal to verify the media is present.
    Uses test media from tests/media directory with temporary storage configuration.
    """
    # Now run the UI test
    open_address_book(admin_page)
    expect(admin_page.locator("#property-list")).to_be_visible()
    expect(admin_page.get_by_text("All Properties")).to_be_visible()

    property_card = get_first_property_card(admin_page)
    expect(property_card).to_be_visible()

    # Open the property gallery and upload media
    property_id = property_card.get_attribute("data-id")
    open_property_gallery(admin_page, property_card, property_id)
    gallery_modal = admin_page.locator("#media-gallery-modal")

    # Upload test media
    upload_gallery_media(gallery_modal, jpg_media())

    # Close the gallery modal with the escape key
    gallery_modal.press("Escape")
    expect(gallery_modal).not_to_be_visible()
    
    # Navigate to the job details view
    open_timetable(admin_page)
    job_card = get_first_job_card(admin_page)
    job_id = job_card.get_attribute('data-job-id')
    job_modal = open_job_details_modal(admin_page, job_card, f"**/jobs/job/{job_id}/details**")

    # Open the property gallery from the job modal
    open_property_gallery(admin_page, job_modal, property_id)
    gallery_modal = admin_page.locator("#media-gallery-modal")
    
    # Delete test media
    delete_all_gallery_media(gallery_modal)

def test_job_report_gallery_submission(admin_page) -> None:
    """
    Test that the job report gallery with submit modal opens and shows expected content.
    Uses test media from tests/media directory with temporary storage configuration.
    """
    # Now run the UI test
    open_timetable(admin_page)
    job_card = get_first_job_card(admin_page)
    job_id = job_card.get_attribute('data-job-id')

    job_modal = open_job_report(admin_page, job_card, job_id)
    
    # Fill the job report in and open the media gallery
    gallery_modal = fill_job_report_and_submit(admin_page, job_modal, job_id)
    assert_gallery_modal_content(gallery_modal, expect_media=False)
    
    # Upload test media
    upload_gallery_media(gallery_modal, jpg_media())

    # Close the gallery modal with the escape key
    gallery_modal.press("Escape")
    expect(gallery_modal).not_to_be_visible()

    # Submit the Job Report and Media
    gallery_modal.click("#gallery-submit-button")

    job_modal = open_job_details_modal(admin_page, job_card, f"**/jobs/job/{job_id}/details**")

    # Open the property gallery from the job modal
    open_property_gallery(admin_page, job_modal, property_id)
    gallery_modal = admin_page.locator("#media-gallery-modal")
    
    # Delete test media
    delete_all_gallery_media(gallery_modal)