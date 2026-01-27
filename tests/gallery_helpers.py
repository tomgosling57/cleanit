
from pathlib import Path
from playwright.sync_api import Locator, expect

def assert_gallery_modal_content(gallery_modal, expect_media=False) -> None:
    """
    Asserts the gallery modal structure and content.
    Since no actual images exist in test, checks for placeholder.
    When media fails to load or no media exists, thumbnail container may be hidden.
    """
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
    
    # Check edit mode toggle and batch upload/delete buttons
    gallery_edit_toggle = gallery_modal.locator("#gallery-edit-toggle")
    gallery_edit_toggle.click()
    gallery_modal.locator("#batch-upload-button").wait_for(state="attached")
    expect(gallery_modal.locator("#batch-upload-button")).to_be_visible()
    expect(gallery_modal.locator("#batch-delete-button")).to_be_visible()
    gallery_edit_toggle.click()  # Toggle back to view mode
    expect(gallery_modal.locator("#batch-upload-button")).not_to_be_visible()
    expect(gallery_modal.locator("#batch-delete-button")).not_to_be_visible()    
    # Note: thumbnail container (#thumbnail-container) may be hidden when no media exists
    # This is acceptable behavior for the "media not successfully loaded" case

def ensure_gallery_edit_mode(gallery_modal: Locator) -> None:
    """Ensures the gallery is in edit mode by toggling if necessary."""
    gallery_edit_toggle = gallery_modal.locator("#gallery-edit-toggle")
    gallery_edit_toggle.wait_for(state="visible")

    if gallery_edit_toggle.text_content().strip() == "Edit Mode":
        gallery_edit_toggle.click()
        expect(gallery_edit_toggle).to_have_text("View Mode")


def upload_files_to_gallery(gallery_modal: Locator, media_paths: list[str]) -> None:
    """Triggers batch upload and selects files, handling file chooser dialog."""
    page = gallery_modal.page
    upload_button = gallery_modal.locator("#batch-upload-button")
    upload_button.wait_for(state="visible")

    absolute_files = [str(Path(p).resolve()) for p in media_paths]

    with page.expect_file_chooser() as fc:
        upload_button.click()

    chooser = fc.value
    chooser.set_files(absolute_files)


def handle_upload_confirmation(gallery_modal: Locator) -> None:
    """Accepts browser confirmation dialog and waits for network idle."""
    page = gallery_modal.page
    page.once('dialog', lambda dialog: dialog.accept())
    page.wait_for_load_state("networkidle")


def wait_for_gallery_uploads(gallery_modal: Locator, timeout: int = 60_000) -> None:
    """Waits for upload indicators to disappear (currently commented out in original)."""
    # This function is kept for future use when upload indicators are implemented
    # uploading = gallery_modal.locator(".uploading, .upload-spinner, .progress")
    # if uploading.count() > 0:
    #     uploading.first.wait_for(state="hidden", timeout=timeout)
    pass


def verify_gallery_thumbnails(gallery_modal: Locator, expected_count: int) -> None:
    """Verifies thumbnail container is visible and has the expected number of thumbnails."""
    # Check placeholder image is not shown (image-not-found.png)
    placeholder = gallery_modal.locator("#media-placeholder")
    expect(placeholder).not_to_be_visible()
    expect(placeholder.locator('img[src*="image-not-found.png"]')).not_to_be_visible()

    # Checks that the thumbnails are visible
    thumbnail_container = gallery_modal.locator("#thumbnail-container")
    thumbnail_container.wait_for(state="visible", timeout=30_000)
    expect(thumbnail_container).to_be_visible()
    expect(thumbnail_container.locator(".thumbnail")).to_have_count(expected_count)
    checkboxes = thumbnail_container.locator(".thumbnail input.media-checkbox")
    expect(checkboxes).to_have_count(expected_count)


def verify_media_visibility(gallery_modal: Locator, media_paths: list[str]) -> None:
    """Verifies each media item is visible and matches the filename."""
    for i, media_path in enumerate(media_paths):
        filename = Path(media_path).name.lower()

        image = gallery_modal.locator("#gallery-image")
        video = gallery_modal.locator("#gallery-video")

        if image.is_visible():
            src = image.get_attribute("src")
            assert src and filename.replace(".png", "").replace(".jpg", "") in src.lower(), f"{filename} not found in image src"
        elif video.is_visible():
            src = video.get_attribute("src")
            assert src and filename in src.lower(), f"{filename} not found in video src"
        else:
            raise AssertionError(f"No media visible for {filename}")


def navigate_through_media(gallery_modal: Locator, media_paths: list[str]) -> None:
    """Navigates through media items using the next button."""
    next_button = gallery_modal.locator(".next-button")
    
    for i in range(len(media_paths) - 1):
        expect(next_button).to_be_enabled()
        next_button.click()


def upload_gallery_media(gallery_modal: Locator, media_paths: list[str]) -> None:
    """Uploads media files to the gallery modal using the batch upload button,
    accepts browser confirmation, and verifies each media item.
    
    This function now uses the reusable helper functions for better test composability.
    """
    # 1. Ensure Edit Mode
    ensure_gallery_edit_mode(gallery_modal)
    
    # 2. Trigger batch upload + choose files
    upload_files_to_gallery(gallery_modal, media_paths)
    
    # 3. Accept browser confirm() and wait for network
    handle_upload_confirmation(gallery_modal)
    
    # 4. Wait for uploads to finish (optional - currently no-op)
    wait_for_gallery_uploads(gallery_modal)
    
    # 5. Verify gallery contents
    verify_gallery_thumbnails(gallery_modal, len(media_paths))
    
    # 6. Verify each media item is visible and matches filename
    verify_media_visibility(gallery_modal, media_paths)
    
    # 7. Navigate through media items
    navigate_through_media(gallery_modal, media_paths)

def delete_all_gallery_media(gallery_modal: Locator) -> None:
    """Deletes all media items in the gallery using batch delete."""
    # Ensure Edit Mode
    ensure_gallery_edit_mode(gallery_modal)
    
    # Select all media items
    thumbnail_container = gallery_modal.locator("#thumbnail-container")
    checkboxes = thumbnail_container.locator(".thumbnail input.media-checkbox")
    count = checkboxes.count()
    
    for i in range(count):
        checkboxes.nth(i).check()

    # Handle confirmation dialog
    page = gallery_modal.page
    page.once('dialog', lambda dialog: dialog.accept())
    
    # Click batch delete button
    delete_button = gallery_modal.locator("#batch-delete-button")
    delete_button.click()
    
    # Wait for network idle after deletion
    page.wait_for_load_state("networkidle")

    # Ensure that the images are no longer visible
    gallery_modal.locator('img[src*="image-not-found.png"]').wait_for(state="visible")
    expect(gallery_modal.locator("#gallery-image")).not_to_be_visible()
    expect(gallery_modal.locator("#gallery-video")).not_to_be_visible()
    
    # Verify no thumbnails remain
    expect(thumbnail_container.locator(".thumbnail")).to_have_count(0)