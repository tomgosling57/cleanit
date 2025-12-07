from flask import url_for
from playwright.sync_api import expect
from datetime import datetime, time, timedelta
from config import DATETIME_FORMATS
from tests.helpers import assert_job_card_variables, login_owner, wait_for_modal

def test_job_details(page, goto) -> None:
    login_owner(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()
    job_card = page.locator('div.job-card').first

    with page.expect_response('**/jobs/job/1/details**'):
        page.wait_for_load_state('networkidle')
        job_card.get_by_text("View Details").click()

    modal = wait_for_modal(page, "#job-modal")

    expect(modal.locator("h2")).to_have_text("Job Details")
    expect(modal.get_by_text("Start: 09:00")).to_be_visible()
    expect(modal.get_by_text("End: 11:00 (2h)")).to_be_visible()

    expected_date = (datetime.today().date() + timedelta(days=2)).strftime(DATETIME_FORMATS["DATE_FORMAT"])
    expect(modal.get_by_text(f"Arrives: {expected_date}")).to_be_visible()
    expect(modal.get_by_text("Time: 09:00")).to_be_visible()
    expect(modal.get_by_text("Full house clean, focus on kitchen and bathrooms.")).to_be_visible()
    expect(modal.get_by_text("123 Main St, Anytown")).to_be_visible()
    expect(modal.get_by_text("Initial Team")).to_be_visible()
    expect(modal.get_by_text("Lily Hargrave")).to_be_visible()

    modal.get_by_text("×").click()
    expect(modal).to_be_hidden()


def test_update_job(page, goto) -> None:
    login_owner(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()
    job_card = page.locator('div.job-card').first

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/details**"):
        page.wait_for_load_state('networkidle')
        job_card.get_by_text("View Details").click()

    modal = wait_for_modal(page, "#job-modal")

    expect(modal.get_by_text("Edit")).to_be_visible()

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update**"):
        page.wait_for_load_state('networkidle')
        modal.get_by_role("button", name="Edit").click()

    modal = wait_for_modal(page, "#job-modal")
    modal.locator("#time").wait_for(state="visible")

    selected_date_from_timetable = page.locator("#timetable-datepicker").input_value()

    expect(modal.locator("#time")).to_have_value("09:00")
    expect(modal.locator("#end_time")).to_have_value("11:00")
    expect(modal.locator("#date")).to_have_value(selected_date_from_timetable)
    expect(modal.locator("#description")).to_have_value("Full house clean, focus on kitchen and bathrooms.")
    expect(modal.locator("#property_id")).to_have_value("1")

    arrival_datetime = (
        datetime.combine(datetime.today().date(), time(9, 0)) + timedelta(days=2)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT"])
    expect(modal.locator("#arrival_datetime")).to_have_value(arrival_datetime)

    new_start_time = datetime.today().replace(hour=8, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_end_time = datetime.today().replace(hour=9, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_arrival_datetime = datetime.combine(
        datetime.today().date() + timedelta(days=1), time(10, 0)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])

    modal.get_by_role("textbox", name="Start Time").fill(new_start_time)
    modal.locator("#access_notes").fill("test")
    modal.locator("#property_id").select_option("2")
    modal.locator('input[type="text"].flatpickr').fill(new_arrival_datetime)
    modal.locator("#assigned_teams").select_option(["1", "2"])
    modal.locator("#assigned_cleaners").select_option(["1", "3"])

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update**"):
        modal.get_by_role("button", name="Save Changes").click()

    expect(modal).to_be_hidden()

    assert_job_card_variables(
        job_card,
        {
            "time": f"Time: {new_start_time}",
            "address": "Property Address: 456 Oak Ave, Teamville"
        },
        expected_indicators=["Next Day Arrival"]
    )

def test_create_job(page, goto) -> None:
    login_owner(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()
    expect(page.get_by_text("Create Job")).to_be_enabled()

    with page.expect_response("**/jobs/job/create**"):
        page.wait_for_load_state('networkidle')
        page.get_by_text("Create Job").click()

    modal = wait_for_modal(page, "#job-modal")
    modal.locator("#time").wait_for(state="visible")

    new_start_time = datetime.today().replace(hour=8, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_end_time = datetime.today().replace(hour=9, minute=0).time().strftime(DATETIME_FORMATS["TIME_FORMAT"])
    new_arrival_datetime = datetime.combine(
        datetime.today().date(), time(10, 0)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])

    modal.get_by_role("textbox", name="Start Time").fill(new_start_time)
    modal.get_by_role("textbox", name="End Time").fill(new_end_time)
    modal.locator("#access_notes").fill("test")
    modal.locator("#property_id").select_option("2")
    modal.locator('input[type="text"].flatpickr').fill(new_arrival_datetime)
    modal.locator("#assigned_teams").select_option(["1", "2"])
    modal.locator("#assigned_cleaners").select_option(["1", "3"])

    with page.expect_response("**/jobs/job/create**"):
        page.wait_for_load_state('networkidle')
        modal.get_by_role("button", name="Create Job").click()

    expect(modal).to_be_hidden()
    assert_job_card_variables(
        page.locator('.job-card').first,
        {
            "time": f"Time: {new_start_time}",
            "address": "Property Address: 456 Oak Ave, Teamville"
        },
        expected_indicators=["Same Day Arrival"]
    )


def test_delete_job(page, goto) -> None:
    login_owner(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()
    job_card = page.locator('div.job-card').first

    expect(job_card.locator(".job-close-button")).to_be_visible()

    page.on('dialog', lambda d: d.accept())

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/delete**"):
        page.wait_for_load_state('networkidle')
        job_card.locator(".job-close-button").click()
    expect(page.locator('#job-1')).to_be_hidden()
