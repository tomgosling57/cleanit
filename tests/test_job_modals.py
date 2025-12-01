from playwright.sync_api import expect
from datetime import datetime, time, timedelta
from config import DATETIME_FORMATS
from tests.helpers import assert_job_card_variables, login_owner

def test_job_details(page, goto) -> None:
    """Tests that the job details are correctly displayed in the job modal.
    
    Args:
        page: The Playwright page object.
        goto: A helper function to navigate to a specific URL.
    """
    login_owner(page, goto)
    # Locate the first job card
    job_card = page.locator('div.job-card').first
    # View job details modal
    job_card.get_by_role("button", name="View Details").click()

    # Assertions for the job details modal
    job_details_modal = page.locator("#job-modal")
    expect(job_details_modal).to_be_visible()
    expect(job_details_modal.locator("h2")).to_have_text("Job Details")

    # Assert Start and End Time
    expect(job_details_modal.get_by_text("Start: 09:00")).to_be_visible()
    expect(job_details_modal.get_by_text("End: 11:00 (2h)")).to_be_visible()
    # Assert Arrival Date & Time
    expected_date = (datetime.today().date() + timedelta(days=2)).strftime(DATETIME_FORMATS["DATE_FORMAT"])
    expect(job_details_modal.get_by_text(f"Arrives: {expected_date}")).to_be_visible()
    expect(job_details_modal.get_by_text("Time: 09:00")).to_be_visible()

    # Assert Description
    expect(job_details_modal.get_by_text("Full house clean, focus on kitchen and bathrooms.")).to_be_visible()

    # Assert Property Address
    expect(job_details_modal.get_by_text("123 Main St, Anytown")).to_be_visible()

    # Assert Assigned Teams and Cleaners
    expect(job_details_modal.get_by_text("Initial Team")).to_be_visible()
    expect(job_details_modal.get_by_text("Lily Hargrave")).to_be_visible()

    # Close the modal
    job_details_modal.get_by_text("×").click()
    expect(job_details_modal).to_be_hidden()

def test_update_job(page, goto) -> None:
    """Tests that the update job flow works correctly for the owner.
    
    Args:
        page: The Playwright page object.
        goto: A helper function to navigate to a specific URL.
    """
    login_owner(page, goto)
    # Locate the first job card
    job_card = page.locator('div.job-card').first
    # View job details modal
    job_card.get_by_role("button", name="View Details").click()
    # Open the job update modal
    page.get_by_text("✏️ Edit").click()

    # Assertions for the job update modal
    job_update_modal = page.locator("#job-modal")
    expect(job_update_modal).to_be_visible()

    # Get the selected date from the timetable date picker
    selected_date_from_timetable = page.locator("#timetable-datepicker").input_value()

    # Assert Time and End Time
    expect(job_update_modal.locator("#time")).to_have_value("09:00")
    expect(job_update_modal.locator("#end_time")).to_have_value("11:00")

    # Assert Date
    expect(job_update_modal.locator("#date")).to_have_value(selected_date_from_timetable)

    # Assert Description (assuming a default description for the test job)
    expect(job_update_modal.locator("#description")).to_have_value("Full house clean, focus on kitchen and bathrooms.")

    # Assert Property (assuming "123 Main St, Anytown" is the first property and its ID is selected)
    expect(job_update_modal.locator("#property_id")).to_have_value("1") # Assuming property ID 1 for "123 Main St, Anytown"

    # Assert Tenant Arrival Date & Time (assuming no arrival_datetime for the test job)
    arrival_datetime = datetime.combine(datetime.today().date(), time(9, 0)) + timedelta(days=2)  # Assuming arrival is two days after the job date at 09:00
    expect(job_update_modal.locator("#arrival_datetime")).to_have_value(arrival_datetime.strftime(DATETIME_FORMATS["DATETIME_FORMAT"]))

    # Assert Teams and Cleaners (assuming default assignments for the test job)
    expect(job_update_modal.locator("#assigned_teams option[selected]").first).to_have_count(1)
    expect(job_update_modal.locator("#assigned_cleaners option[selected]").first).to_have_count(1)

    # Update the job with new data
    new_start_time = datetime.today().replace(hour=8, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_end_time = datetime.today().replace(hour=9, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_date = (datetime.today().date() + timedelta(days=1)).strftime(DATETIME_FORMATS["DATE_FORMAT"])
    new_job_description = "test"
    new_arrival_datetime = datetime.combine(datetime.today().date() + timedelta(days=1), time(10, 0)).strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])
    new_access_notes = "test"
    new_property_id = "2"
    new_assigned_teams =  ["1", "2"]    
    new_assigned_cleaners = ["1", "3"]

    job_update_modal.get_by_role("textbox", name="Start Time").fill(new_start_time)
    job_update_modal.locator("#access_notes").fill(new_access_notes)
    job_update_modal.locator("#property_id").select_option(new_property_id)
    job_update_modal.locator('input[type="text"].flatpickr').fill(new_arrival_datetime)
    job_update_modal.locator("#assigned_teams").select_option(new_assigned_teams)
    job_update_modal.locator("#assigned_cleaners").select_option(new_assigned_cleaners)
    job_update_modal.get_by_role("button", name="💾 Save Changes").click()
    expect(job_update_modal).to_be_hidden()
    assert_job_card_variables(job_card, {
        "time": f"Time: {new_start_time}",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Next Day Arrival"])  

def test_create_job(page, goto) -> None:
    """Tests that the create job flow works correctly for the owner.
    
    Args:
        page: The Playwright page object.
        goto: A helper function to navigate to a specific URL.
    """
    login_owner(page, goto)
    page.get_by_text("Create Job").click()

    # Assertions for the job update modal
    job_update_modal = page.locator("#job-modal")
    expect(job_update_modal).to_be_visible()

    # Get the selected date from the timetable date picker
    selected_date_from_timetable = page.locator("#timetable-datepicker").input_value()

    # Assert Time and End Time
    expect(job_update_modal.locator("#time")).to_be_visible()
    expect(job_update_modal.locator("#end_time")).to_be_visible()

    # Assert Date
    expect(job_update_modal.locator("#date")).to_be_visible()

    # Assert Description (assuming a default description for the test job)
    expect(job_update_modal.locator("#description")).to_be_visible()

    # Assert Property (assuming "123 Main St, Anytown" is the first property and its ID is selected)
    expect(job_update_modal.locator("#property_id")).to_be_visible()

    # Assert Tenant Arrival Date & Time (assuming no arrival_datetime for the test job)
    expect(job_update_modal.get_by_text("Arrival Date & Time")).to_be_visible()
    # Assert Teams and Cleaners (assuming default assignments for the test job)
    expect(job_update_modal.get_by_text("Lily Hargrave")).to_be_visible()
    expect(job_update_modal.get_by_text("Initial Team")).to_be_visible()

    # Update the job with new data
    new_start_time = datetime.today().replace(hour=8, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_end_time = datetime.today().replace(hour=9, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_date = (datetime.today().date() + timedelta(days=1)).strftime(DATETIME_FORMATS["DATE_FORMAT"])
    new_job_description = "test"
    new_arrival_datetime = datetime.combine(datetime.today().date() + timedelta(days=2), time(10, 0)).strftime(DATETIME_FORMATS["DATETIME_FORMAT"])
    new_access_notes = "test"
    new_property_id = "2"
    new_assigned_teams =  ["1", "2"]    
    new_assigned_cleaners = ["1", "3"]

    job_update_modal.get_by_role("textbox", name="Start Time").fill(new_start_time)
    job_update_modal.get_by_role("textbox", name="End Time").fill(new_end_time)
    job_update_modal.locator("#access_notes").fill(new_access_notes)
    job_update_modal.locator("#property_id").select_option(new_property_id)
    job_update_modal.locator("#assigned_teams").select_option(new_assigned_teams)
    job_update_modal.locator("#assigned_cleaners").select_option(new_assigned_cleaners)
    job_update_modal.get_by_role("button", name="💾 Create Job").click()
    expect(job_update_modal).to_be_hidden()
    assert_job_card_variables(page.locator('.job-card').first, {
        "time": f"Time: {new_start_time}",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }) 

def test_delete_job(page, goto) -> None:
    """Tests that the delete job flow works correctly for the owner.
    
    Args:
        page: The Playwright page object.
        goto: A helper function to navigate to a specific URL.
    """
    login_owner(page, goto)
    # Locate the first job card
    job_card = page.locator('#job-1').first
    
    # Confirm deletion in the confirmation dialog
    page.on('dialog', lambda dialog: dialog.accept())
    # Delete the job
    page.locator("#job-1").get_by_text("×").click()

    expect(page.locator('#job-1').first).to_be_hidden()