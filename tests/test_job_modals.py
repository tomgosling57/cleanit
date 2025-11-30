from playwright.sync_api import expect
from datetime import datetime, time, timedelta
from config import DATETIME_FORMATS
from tests.helpers import assert_job_card_variables, login_owner

def test_update_job(page, goto) -> None:
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
    new_arrival_datetime = datetime.combine(datetime.today().date() + timedelta(days=2), time(10, 0)).strftime(DATETIME_FORMATS["DATETIME_FORMAT"])
    new_access_notes = "test"
    new_property_id = "2"
    new_assigned_teams =  ["1", "2"]    
    new_assigned_cleaners = ["1", "3"]

    # job_update_modal.get_by_role("textbox", name="Start Time").click()
    job_update_modal.get_by_role("textbox", name="Start Time").fill(new_start_time)
    job_update_modal.get_by_role("textbox", name="End Time").fill(new_end_time)
    job_update_modal.get_by_role("textbox", name="Job description").fill(new_job_description)
    job_update_modal.get_by_role("textbox", name="Tenant Arrival Date & Time").fill(new_arrival_datetime)
    job_update_modal.get_by_role("textbox", name="Access Notes").fill(new_access_notes)
    job_update_modal.locator("#property_id").select_option(new_property_id)
    job_update_modal.locator("#assigned_teams").select_option(new_assigned_teams)
    job_update_modal.locator("#assigned_cleaners").select_option(new_assigned_cleaners)
    job_update_modal.get_by_role("button", name="💾 Save Changes").click()
    expect(job_update_modal).to_be_hidden()
    expect(job_card.get_by_text("456 Oak Ave, Teamville")).to_be_visible()
    assert_job_card_variables(job_card, {
        "time": f"Time: {new_start_time}",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Next Day Arrival"])