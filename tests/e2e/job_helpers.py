from playwright.sync_api import expect
from datetime import datetime, timedelta

from config import DATETIME_FORMATS
from database import Job
from services.assignment_service import AssignmentService
from tests.db_helpers import get_db_session
from tests.helpers import (
    open_job_update_modal, validate_csrf_token_in_modal,
)
from utils.timezone import today_in_app_tz


class JobViewsTestHelper:
        
    def __init__(self, page) -> None:
        self.page = page
        self.db = get_db_session()
        self.assignment_service = AssignmentService(self.db)


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
        expect(popup.locator("#start_time")).to_have_value(expected_job.display_time)
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
            if attr in ['start_time', 'end_time', 'arrival_datetime', 'date', 'arrival_date', 'arrival_time']:
                return kwargs.get(attr, getattr(expected_job, f"display_{attr}"))
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

        expect(popup.locator("#date")).to_have_text(get_expected("date"))
        expect(popup.locator("#start_time")).to_have_text(get_expected("start_time"))
        expect(popup.locator("#end_time")).to_have_text(get_expected("end_time"))
        arrival_datetime = get_expected("arrival_datetime")
        if arrival_datetime:
            expect(popup.locator("#arrival_date")).to_have_text(arrival_datetime.strftime(DATETIME_FORMATS["DATE_FORMAT"]))
            expect(popup.locator("#arrival_time")).to_have_text(arrival_datetime.strftime(DATETIME_FORMATS["TIME_FORMAT"]))
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

    def open_team_timetable(self):
        """Navigates to the team timetable view for the current selected date."""
        with self.page.expect_response("**/jobs/teams**"):
            self.page.wait_for_load_state('networkidle')
            self.page.get_by_text("Team View").click()
        expect(self.page.locator("#team-timetable-view")).to_be_visible()

    def open_create_job_form(self):
        """Opens the create job form modal and returns the modal locator."""
        with self.page.expect_response("**/jobs/job/create**"):
            self.page.wait_for_load_state('networkidle')
            self.page.get_by_text("Create Job").click()
        job_modal = self.page.locator("#job-modal")
        expect(job_modal).to_be_visible()
        return job_modal
    
    def update_job(self, job_id, expect_card_after_update=True, **kwargs):
        """Helper to update job from the timetable views by opening the job details and then the update modal.
        Fills the form with provided kwargs and saves.
        Finally validates that the job details modal reflects the updated values.
        """
        job_card = self.get_job_card_by_id(job_id)
        job_card.wait_for(state="visible")
        # Open the job details modal first to ensure we have the latest data and then open the update modal from there
        job_modal = self.open_job_details(job_id)
        self.validate_job_details(job_id)

        # Open the update form and assert the same values are present there
        open_job_update_modal(self.page, job_modal, f"**/jobs/job/{job_id}/update**")
        validate_csrf_token_in_modal(job_modal)
        self.validate_form_auto_fill(job_id)
        
        self.fill_job_form(**kwargs)
        with self.page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/update**"):
            self.page.locator("#job-modal").get_by_role("button", name="Save Changes").click()
        if expect_card_after_update:
            # Get the updated job from the database
            expect(self.page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
            job_card = self.page.locator(f'div.job-card[data-job-id="{job_id}"]')
            self.open_job_details(job_id)
            self.validate_job_details(job_id, **kwargs)
        
    def create_job(self, **kwargs):
        """Helper to create a job from the timetable views by opening the create job modal.
        Fills the form with provided kwargs and saves.
        Finally validates that the job details modal reflects the created job values.
        """
        self.open_create_job_form()
        job_modal = self.page.locator("#job-modal")
        expect(job_modal).to_be_visible()
        validate_csrf_token_in_modal(job_modal)

        # Since this is a new job, we won't have an id until after creation, so we can't use validate_form_auto_fill here
        self.fill_job_form(**kwargs)
        with self.page.expect_response("**/jobs/job/create**"):
            self.page.locator("#job-modal").get_by_role("button", name="Create Job").click()
        
        expect(self.page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
        # Get the created job from the database using a combination of unique attributes (since we don't have the id)
        created_job = self.db.query(Job).order_by(Job.id.desc()).first()
        assert created_job is not None, "Created job not found in database"
        self.open_job_details(created_job.id)
        self.validate_job_details(created_job.id, **kwargs)
    
    def selected_date(self, page):
        return page.locator("#timetable-datepicker").input_value()

    def selected_datetime(self):
        selected_date = self.selected_date(self.page)
        return datetime.strptime(selected_date, DATETIME_FORMATS["DATE_FORMAT"])    
    
    def fill_job_form(self, **kwargs):
        """
        Fills the job form modal directly using page.locator calls.
        Only fills fields that are explicitly provided in kwargs.
        """
        page = self.page  # convenience

        # Fill each field only if the value is provided
        if "start_time" in kwargs:
            page.locator("#start_time").fill(kwargs["start_time"])

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
            if len(kwargs["assigned_teams"]) == 0:
                # If we want to clear all assigned teams, we can use the "deselect all" option if available
                page.locator("#assigned_teams").select_option([])
            else:
                page.locator("#assigned_teams").select_option([str(team.id) for team in kwargs["assigned_teams"]])

        if "assigned_cleaners" in kwargs:
            if len(kwargs["assigned_cleaners"]) == 0:
                page.locator("#assigned_cleaners").select_option([])
            else:
                page.locator("#assigned_cleaners").select_option([str(user.id) for user in kwargs["assigned_cleaners"]])

    def get_job_card_by_id(self, job_id):
        return self.page.locator(f'div.job-card[data-job-id="{job_id}"]')
    
    