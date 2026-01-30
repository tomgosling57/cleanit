from playwright.sync_api import expect
from datetime import datetime, time, timedelta
from config import DATETIME_FORMATS
from tests.helpers import (
    assert_job_card_variables,
    get_first_job_card, open_job_details_modal, open_job_update_modal,
    fill_job_modal_form, assert_job_details_modal_content, close_modal_and_assert_hidden, validate_csrf_token_in_modal, wait_for_modal,
    get_future_date, get_future_time
)
from utils.timezone import today_in_app_tz

def test_job_details(admin_page) -> None:

    job_card = get_first_job_card(admin_page)
    expect(job_card).to_be_visible()

    job_id = job_card.get_attribute('data-job-id')
    with admin_page.expect_response(f"**/jobs/job/{job_id}/details**"):
        admin_page.wait_for_load_state('networkidle')
        open_job_details_modal(admin_page, job_card, f"**/jobs/job/{job_id}/details**")
    modal = admin_page.locator("#job-modal")

    expected_date = get_future_date(days=2)
    assert_job_details_modal_content(
        admin_page,
        modal_id="#job-modal",
        title="Job Details",
        start_time="09:00",
        end_time="11:00 (2h)",
        arrival_date=expected_date,
        arrival_time="09:00",
        description="Full house clean, focus on kitchen and bathrooms.",
        property_address="123 Main St, Anytown",
        assigned_team="Initial Team",
        assigned_cleaner="Lily Hargrave",
    )

    close_modal_and_assert_hidden(admin_page, "#job-modal")


def test_update_job(admin_page) -> None:
    page = admin_page
    get_first_job_card(page).wait_for(state="attached")
    page.get_by_text("Create Job").wait_for(state="attached")
    job_card = get_first_job_card(page)
    expect(job_card).to_be_visible()

    job_id = job_card.get_attribute('data-job-id')
    with page.expect_response(f"**/jobs/job/{job_id}/details**"):
        open_job_details_modal(page, job_card, f"**/jobs/job/{job_id}/details**")
    modal = page.locator("#job-modal")
    modal.wait_for(state="attached")
    expect(modal.get_by_text("Edit")).to_be_visible()

    job_id = job_card.get_attribute('data-job-id')
    with page.expect_response(f"**/jobs/job/{job_id}/update**"):
        open_job_update_modal(page, modal, f"**/jobs/job/{job_id}/update**")
    modal = page.locator("#job-modal")
    validate_csrf_token_in_modal(modal)
    expect(modal.locator("#time")).to_be_visible()

    selected_date_from_timetable = page.locator("#timetable-datepicker").input_value()

    expect(modal.locator("#time")).to_have_value("09:00")
    expect(modal.locator("#end_time")).to_have_value("11:00")
    expect(modal.locator("#date")).to_have_value(selected_date_from_timetable)
    expect(modal.locator("#description")).to_have_value("Full house clean, focus on kitchen and bathrooms.")
    expect(modal.locator("#property_id")).to_have_value("1")

    arrival_datetime = datetime.combine(
        datetime.strptime(get_future_date(days=2), DATETIME_FORMATS["DATE_FORMAT"]).date(), time(9, 0)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT"])
    expect(modal.locator("#arrival_datetime")).to_have_value(arrival_datetime)

    new_start_time = get_future_time(hours=-1) # 8:00 AM
    new_end_time = get_future_time(hours=0) # 9:00 AM
    new_arrival_datetime = datetime.combine(
        today_in_app_tz() + timedelta(days=1), time(10, 0)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])
    
    fill_job_modal_form(
        page,
        start_time=new_start_time,
        end_time=new_end_time,
        date=selected_date_from_timetable,
        description="Full house clean, focus on kitchen and bathrooms.",
        property_id="2",
        arrival_datetime=new_arrival_datetime,
        access_notes="test",
        assigned_teams=["1", "2"],
        assigned_cleaners=["1", "3"],
    )

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update**"):
        modal.get_by_role("button", name="Save Changes").click()

    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    job_card = page.locator(f'div.job-card[data-job-id="{job_id}"]')
    assert_job_card_variables(
        job_card,
        {
            "time": f"Time: {new_start_time}",
            "address": "Property Address: 456 Oak Ave, Teamville"
        },
        expected_indicators=["Next Day Arrival"]
    )

def test_create_job(admin_page) -> None:
    page = admin_page

    get_first_job_card(page).wait_for(state="attached")
    page.get_by_text("Create Job").wait_for(state="attached")

    with page.expect_response("**/jobs/job/create**"):
        page.wait_for_load_state('networkidle')
        page.get_by_text("Create Job").click()

    modal = wait_for_modal(page, "#job-modal")
    validate_csrf_token_in_modal(modal)
    # optional: log its length or hash to see if it changes per login

    expect(modal.locator("#time")).to_be_visible()

    new_start_time = "07:00"
    new_end_time = "08:00"
    new_date = get_future_date(days=0)
    new_arrival_datetime = datetime.combine(
        datetime.strptime(get_future_date(days=0), DATETIME_FORMATS["DATE_FORMAT"]).date(), time(10, 0)
    ).strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])

    fill_job_modal_form(
        page,
        start_time=new_start_time,
        end_time=new_end_time,
        date=new_date,
        description="Full house clean, focus on kitchen and bathrooms.",
        property_id="2",
        arrival_datetime=new_arrival_datetime,
        access_notes="test",
        assigned_teams=["1", "2"],
        assigned_cleaners=["1", "3"],
    )
    
    with page.expect_response("**/jobs/job/create**"):
        page.wait_for_load_state('networkidle')
        modal.get_by_role("button", name="Create Job").click()

    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    assert_job_card_variables(
        get_first_job_card(page),
        {
            "time": f"Time: {new_start_time}",
            "address": "Property Address: 456 Oak Ave, Teamville"
        },
        expected_indicators=["Same Day Arrival"]
    )


