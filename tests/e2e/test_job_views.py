from playwright.sync_api import expect
from datetime import datetime, time, timedelta

import pytest
from config import DATETIME_FORMATS
from database import Assignment, Job
from services.assignment_service import AssignmentService
from tests.db_helpers import get_db_session
from tests.helpers import (
    assert_job_card_variables,
    get_first_job_card, open_job_details_modal, open_job_update_modal,
    fill_job_modal_form, assert_job_details_modal_content, close_modal_and_assert_hidden, validate_csrf_token_in_modal, wait_for_modal,
    get_future_date, get_future_time
)
from utils.populate_database import USER_DATA
from utils.timezone import to_app_tz, today_in_app_tz, utc_now

@pytest.mark.db_reset
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

class TestJobModalViews:
    
    
    def test_job_details(self, admin_page) -> None:
        page = admin_page
        job_card = get_first_job_card(page)
        job_card.wait_for(state="visible")
        job_id = job_card.get_attribute('data-job-id')
        # Open the job details modal first to ensure we have the latest data and then open the update modal from there
        open_job_details_modal(page, job_card, f"**/jobs/job/{job_id}/details**")
        self.expect_job_attributes_in_modal(page, job_id)
    
    @pytest.mark.db_reset
    def test_update_job_to_next_day_arrival(self, admin_page) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        test_helper = JobViewsTestHelper(page)
        get_first_job_card(page).wait_for(state="attached")
        page.get_by_text("Create Job").wait_for(state="attached")
        job_card = get_first_job_card(page)
        expect(job_card).to_be_visible()
        new_arrival_datetime = test_helper.selected_datetime() + timedelta(days=1, hours=2)
        test_helper.update_job_card(job_card, arrival_datetime=new_arrival_datetime)
        job_card = self.get_job_card_by_id(job_card.get_attribute("data-job-id"))
        assert_job_card_variables(
            job_card,
            {},
            expected_indicators=["Next Day Arrival"]
        )        
    
    def test_update_job_to_same_day_arrival(self, admin_page) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        test_helper = JobViewsTestHelper(page)
        get_first_job_card(page).wait_for(state="attached")
        page.get_by_text("Create Job").wait_for(state="attached")
        job_card = get_first_job_card(page)
        expect(job_card).to_be_visible()
        new_arrival_datetime = to_app_tz(utc_now() + timedelta(hours=2))
        test_helper.update_job_card(job_card, new_arrival_datetime=new_arrival_datetime)

@pytest.mark.db_reset
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

def assert_access_notes_visible(page, job_card) -> None:
    """Open the job detail modal of the given job card and assert that the access notes attribute is visible."""
    job_id = job_card.get_attribute('data-job-id')
    job_modal = open_job_details_modal(page, job_card, f"**/jobs/job/{job_id}/details**")
    expect(job_modal.locator("#access-notes")).to_be_visible()

def assert_access_notes_not_visible(page, job_card) -> None:
    """Open the job details modal of the given job card and assert that the access notes attribute is not visible."""
    job_id = job_card.get_attribute('data-job-id')
    job_modal = open_job_details_modal(page, job_card, f"**/jobs/job/{job_id}/details**")
    expect(job_modal.locator("#access-notes")).not_to_be_visible()

def test_access_notes_visibility_supervisor(supervisor_page) -> None:
    """Test that the access notes are visible to supervisors within the job details."""
    page = supervisor_page
    job_card = get_first_job_card(page)
    assert_access_notes_visible(page, job_card)
    
def test_access_notes_visibility_team_leader(team_leader_page) -> None:
    """Tests that the access notes are visible to team leaders within the job details."""
    page = team_leader_page
    job_card = get_first_job_card(page)
    assert_access_notes_visible(page, job_card)

def test_access_notes_visibility_admin(admin_page) -> None:
    """Tests that the access notes are visible to admins within the job details."""
    page = admin_page
    job_card = get_first_job_card(page)
    assert_access_notes_visible(page, job_card)

def test_access_notes_visibility_user(user_page) -> None:
    """Tests that the access notes are not visible to regular users within the job details."""
    page = user_page
    job_card = get_first_job_card(page)
    assert_access_notes_not_visible(page, job_card)

class JobViewsTestHelper:
        
    db = get_db_session()
    assignment_service = AssignmentService(db)

    def __init__(self, page) -> None:
        self.page = page

    def validate_form_auto_fill(self, job_id) -> None:
        """Validates the input values of a job update/creation form against the database values. 
        - Expects the form to already be open within the #job-modal element.
        - Uses playwright expect calls for assertions.
        - Intended for forms contained within the job_update_modal and job_creation_modal templates.
        """
        popup = self.page.locator("#job-modal")        
        # Get the job from the database popu use for expected values
        expected_job = self.db.query(Job).filter_by(id=job_id).first()
        assert expected_job is not None, f"Job with id {job_id} not found in database"
        # Assert that the autofill values match the database object
        expected_team_assignments = self.assignment_service.get_teams_for_job(job_id)
        expected_user_assignments = self.assignment_service.get_users_for_job(job_id)
        expect(popup.locator("#assigned_teams")).to_have_values([str(team.id) for team in expected_team_assignments])
        expect(popup.locator("#assigned_cleaners")).to_have_values([str(user.id) for user in expected_user_assignments])
        expect(popup.locator("#date")).to_have_value(expected_job.display_date)
        expect(popup.locator("#time")).to_have_value(expected_job.display_time)
        expect(popup.locator("#end_time")).to_have_value(expected_job.display_end_time)
        expect(popup.locator("#arrival_datetime")).to_have_value(expected_job.display_arrival_datetime_strf)
        expect(popup.locator("#description")).to_have_value(expected_job.description)
        expect(popup.locator("#property_id")).to_have_value(str(expected_job.property.id))
        expect(popup.locator("#access_notes")).to_have_value(expected_job.property.access_notes)

    def validate_job_details(self, job_id, **kwargs) -> None:
        """
        Validates the content of a job details modal against the database values. 
        - Expects the modal to already be open within the #job-modal element.
        - Uses playwright expect calls for assertions.
        - Intended for modals contained within the job_details_modal template.
        - Additional kwargs with keys using snake case id selectors of elements to validate passed values, eg time='12:00'.
        """
        popup = self.page.locator("#job-modal")

        # Get the job from the database to use for expected values
        expected_job = self.db.query(Job).filter_by(id=job_id).first()
        assert expected_job is not None, f"Job with id {job_id} not found in database"

        # Helper to get attribute from kwargs or expected_job
        def get_expected(attr, default=None):
            return kwargs.get(attr, getattr(expected_job, attr, default))


        expected_team_assignments = kwargs.get(
            "assigned_teams",
            self.assignment_service.get_teams_for_job(job_id)
        )
        expected_user_assignments = kwargs.get(
            "assigned_cleaners",
            self.assignment_service.get_users_for_job(job_id)
        )

        for team in expected_team_assignments:
            expect(popup.locator("#assigned_teams")).to_contain_text(team.name)

        for user in expected_user_assignments:
            expect(popup.locator("#assigned_cleaners")).to_contain_text(user.full_name)

        expect(popup.locator("#date")).to_have_text(get_expected("display_date"))
        expect(popup.locator("#time")).to_have_text(get_expected("display_time"))
        expect(popup.locator("#end_time")).to_have_text(get_expected("display_end_time"))

        arrival_datetime = get_expected("arrival_datetime")
        if arrival_datetime:
            expect(popup.locator("#arrival_date")).to_have_text(get_expected("display_arrival_date"))
            expect(popup.locator("#arrival_time")).to_have_text(get_expected("display_arrival_time"))
        else:
            expect(popup.locator("#arrival_date")).to_have_text("Not specified")
            expect(popup.locator("#arrival_time")).to_have_text("Not specified")

        expect(popup.locator("#description")).to_have_text(get_expected("description"))

        property_obj = get_expected("property")
        expect(popup.locator("#property_address")).to_have_text(property_obj.address)
        expect(popup.locator("#property_address")).to_have_attribute("data-property-id", str(property_obj.id))
        expect(popup.locator("#access_notes")).to_have_text(property_obj.access_notes)

        # Validate arrival indicators
        if expected_job.arrival_date_in_app_tz == today_in_app_tz():
            expect(popup.locator("#arrival-indicator")).to_have_text("Same Day Arrival")
        elif expected_job.arrival_date_in_app_tz == today_in_app_tz() + timedelta(days=1):
            expect(popup.locator("#arrival-indicator")).to_have_text("Next Day Arrival")
        


    def open_job_details(self, job_id):
        """Opens the job details model for the given job id and returns the modal locator."""
        with self.page.expect_response(f"**/jobs/job/{job_id}/details**"):
            self.page.wait_for_load_state('networkidle')
            # Hover over the job card to ensure buttons are clickable (especially for completed jobs)
            job_card = self.get_job_card_by_id(job_id)
            job_card.hover()
            job_card.get_by_role("button", name="View Details").click()
        job_modal = self.page.locator("#job-modal")
        expect(job_modal).to_be_visible()
        return job_modal


    def update_job_card(self, job_card, **kwargs):
        job_id = job_card.get_attribute('data-job-id')
        # Open the job details modal first to ensure we have the latest data and then open the update modal from there
        job_modal = self.open_job_details(job_id)
        self.validate_job_details(job_id)

        # Open the update form and assert the same values are present there
        open_job_update_modal(self.page, job_modal, f"**/jobs/job/{job_id}/update**")
        validate_csrf_token_in_modal(job_modal)
        self.validate_form_auto_fill(job_id)
        
        self.fill_job_form(job_id, **kwargs)
        with self.page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update**"):
            self.page.locator("#job-modal").get_by_role("button", name="Save Changes").click()
        
        # Get the updated job from the database
        expect(self.page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
        job_card = self.page.locator(f'div.job-card[data-job-id="{job_id}"]')
        self.open_job_details(job_id)
        self.validate_job_details(job_id)
    
    def selected_date(self, page):
        return page.locator("#timetable-datepicker").input_value()

    def selected_datetime(self):
        selected_date = self.selected_date(self.page)
        return datetime.strptime(selected_date, DATETIME_FORMATS["DATE_FORMAT"])    
    
    def fill_job_form(self, job_id, **kwargs):
        """
        Fills the job form modal directly using page.locator calls.
        Only fills fields that are explicitly provided in kwargs.
        """
        expected_job = self.db.query(Job).filter_by(id=job_id).first()
        assert expected_job is not None, f"Job with id {job_id} not found in database"

        page = self.page  # convenience

        # Fill each field only if the value is provided
        if "start_time" in kwargs:
            page.locator("#time").fill(kwargs["start_time"])

        if "end_time" in kwargs:
            page.locator("#end_time").fill(kwargs["end_time"])

        if "date" in kwargs:
            page.locator("#date").fill(kwargs["date"])

        if "description" in kwargs:
            page.locator("#description").fill(kwargs["description"])

        if "property_id" in kwargs:
            page.locator("#property_id").select_option(kwargs["property_id"])

        if "arrival_datetime" in kwargs:
            arrival = kwargs["arrival_datetime"]
            if isinstance(arrival, datetime):
                arrival = arrival.strftime(DATETIME_FORMATS["DATETIME_FORMAT_JOBS_PY"])
            # Assuming this is the correct flatpickr input selector
            page.locator('input[type="text"].flatpickr').fill(arrival)

        if "access_notes" in kwargs:
            page.locator("#access_notes").fill(kwargs["access_notes"])

        if "assigned_teams" in kwargs:
            page.locator("#assigned_teams").select_option(kwargs["assigned_teams"])

        if "assigned_cleaners" in kwargs:
            page.locator("#assigned_cleaners").select_option(kwargs["assigned_cleaners"])

    def get_job_card_by_id(self, job_id):
        return self.page.locator(f'div.job-card[data-job-id="{job_id}"]')
    
    