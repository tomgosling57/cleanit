
from pathlib import Path
from playwright.sync_api import Locator, expect, Page

def open_job_report(page: Page, parent: Locator, job_id) -> None:
    """Open the job report modal by pressing the mark as complete button on a job card"""
    parent.locator(".mark-as-complete-button").wait_for(state="attached")
    with page.expect_response(f"**/jobs/job/{job_id}/mark_complete**"):
        page.wait_for_load_state('networkidle')
        parent.locator(".mark-as-complete-button").click()
    
    return page.locator("#job-modal")

def fill_job_report_and_submit(page: Page, parent: Locator, job_id) -> None:
    """Fill in the job report text area and submit the report to open the gallery"""
    report_textarea = parent.locator("#report_text")
    report_textarea.fill("This is a test job report.")
    
    with page.expect_response(f"**/jobs/job/{job_id}/submit_report**"):
        parent.locator(".save-button").click()
    
    return page.locator("#media-gallery-modal")