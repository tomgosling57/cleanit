import re
from playwright.sync_api import expect
from datetime import datetime, time, timedelta

import pytest
from config import DATETIME_FORMATS
from database import Job, Team, User
from tests.e2e.conftest import page
from tests.helpers import (
    assert_job_card_variables,
    get_first_job_card, open_job_details_modal, open_job_update_modal,
    fill_job_modal_form, validate_csrf_token_in_modal, wait_for_modal,
    get_future_date, get_future_time
)
from tests.e2e.job_helpers import JobViewsTestHelper
from utils.populate_database import USER_DATA
from utils.timezone import to_app_tz, today_in_app_tz, utc_now

class TestJobViews:
    
    
    def test_job_details(self, admin_page) -> None:
        page = admin_page
        job_card = get_first_job_card(page)
        job_card.wait_for(state="visible")
        job_id = job_card.get_attribute('data-job-id')
        test_helper = JobViewsTestHelper(page)
        # Open the job details modal first to ensure we have the latest data and then open the update modal from there
        job_modal = test_helper.open_job_details(job_id)
        test_helper.validate_job_details(job_id)        
    
    @pytest.mark.db_reset
    def test_update_job_time_attributes(self, admin_page) -> None:
        page = admin_page
        # Extract the idea of the first job card
        job_card = get_first_job_card(page)
        job_card.wait_for(state="visible")
        job_id = job_card.get_attribute('data-job-id')
        
        # Open the job details modal first to ensure we have the latest data and then open the update modal from there
        new_start_time = "08:00"
        new_end_time = "09:00"
        new_arrival_datetime = datetime.combine(
            today_in_app_tz() + timedelta(days=1), time(10, 0)
        )
        test_helper = JobViewsTestHelper(page)
        
        test_helper.update_job(
            job_id,
            start_time=new_start_time,
            end_time=new_end_time,
            arrival_datetime=new_arrival_datetime
        )    

    @pytest.mark.db_reset
    def test_update_job_to_next_day_arrival(self, admin_page) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        test_helper = JobViewsTestHelper(page)
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        new_arrival_datetime = test_helper.selected_datetime() + timedelta(days=1, hours=2)
        test_helper.update_job(job_id, arrival_datetime=new_arrival_datetime)

    @pytest.mark.db_reset    
    def test_update_job_to_same_day_arrival(self, admin_page) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        test_helper = JobViewsTestHelper(page)
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        new_arrival_datetime = to_app_tz(utc_now() + timedelta(hours=2))
        test_helper.update_job(job_id, arrival_datetime=new_arrival_datetime)
    
    @pytest.mark.db_reset
    def test_update_job_to_user_assignment_only(self, admin_page, admin_user) -> None:
        """Test that updating a job to be assigned to only a user and no teams is not successful and an 
        error alert appears saying that at least one team must be assigned to the job."""
        page = admin_page
        page.set_default_timeout(3_000)
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        test_helper = JobViewsTestHelper(page)
        test_helper.update_job(
            job_id,
            expect_card_after_update=False,
            assigned_cleaners=[admin_user],
            assigned_teams=[]
        )
        expect(admin_page.locator(".alert").get_by_text("At least one team must be assigned to the job.")).to_be_visible()
        expect(admin_page.locator('#job-modal')).to_be_visible()
        page.keyboard.press("Escape")
        test_helper.open_job_details(job_id)
        test_helper.validate_job_details(job_id)

    @pytest.mark.db_reset
    def test_update_job_to_team_assignment_only(self, admin_page, admin_user) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        test_helper = JobViewsTestHelper(page)
        test_helper.update_job(
            job_id,
            assigned_teams=test_helper.db.query(Team).filter(Team.id.in_([admin_user.team_id])).all()
        )

    @pytest.mark.db_reset
    def test_update_job_to_no_assignment(self, admin_page) -> None:
        """Test that updating a job to have no assignments blocks the job update and chose an error."""
        page = admin_page
        page.set_default_timeout(3_000)
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        test_helper = JobViewsTestHelper(page)
        test_helper.update_job(
            job_id,
            expect_card_after_update=False,
            assigned_cleaners=[],
            assigned_teams=[]
        )
        expect(admin_page.locator(".alert").get_by_text("At least one team must be assigned to the job.")).to_be_visible()
        expect(admin_page.locator('#job-modal')).to_be_visible()

    @pytest.mark.db_reset
    def test_update_job_assignment_to_non_admin_entities(self, admin_page, supervisor_page, team_leader_page, admin_user, supervisor_user, team_leader_user) -> None:
        """Test that when an admin assigns job to another user or a team that they are not on, the update is successful and the job card is
        no longer rendered on their personal timetable page but is visible within the appropriate team's column on the team
        timetable as well as the personal timetables of the team's members and any other assigned users."""
        assert supervisor_user.team_id != admin_user.team_id, "The supervisor user should be assigned to a different team than the" \
        " admin user for this test to be valid."
        assert team_leader_user.team_id != supervisor_user.team_id and team_leader_user.team_id != admin_user.team_id, "The team " \
        "leader user should be assigned to a different team than the admin and supervisor users for this test to be valid."
        page = admin_page
        page.set_default_timeout(3_000)
        admin_page.bring_to_front()
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        admin_helper = JobViewsTestHelper(page)
        supervisor_team = admin_helper.db.query(Team).filter(Team.id == supervisor_user.team_id).first()
        admin_helper.update_job(
            job_id,
            expect_card_after_update=False,
            assigned_teams=[supervisor_team],
            assigned_cleaners=[team_leader_user]
        )
        expect(admin_helper.get_job_card_by_id(job_id)).to_be_hidden()
        admin_helper.open_team_timetable()
        team_timetable = page.locator("#team-timetable-view")
        team_column = team_timetable.locator(f'[data-team-id="{supervisor_team.id}"]')
        expect(team_column.locator(f'div.job-card[data-job-id="{job_id}"]')).to_be_visible()
        # Assert job card is visible on supervisor's personal timetable
        supervisor_page.bring_to_front()
        supervisor_page.reload()
        supervisor_helper = JobViewsTestHelper(supervisor_page)
        expect(supervisor_helper.get_job_card_by_id(job_id)).to_be_visible()
        supervisor_helper.open_job_details(job_id)
        supervisor_helper.validate_job_details(job_id)
        # Assert job card is visible on team leader's personal timetable
        team_leader_page.bring_to_front()
        team_leader_page.reload()
        team_leader_helper = JobViewsTestHelper(team_leader_page)
        expect(team_leader_helper.get_job_card_by_id(job_id)).to_be_visible()
        team_leader_helper.open_job_details(job_id)
        team_leader_helper.validate_job_details(job_id)

    @pytest.mark.db_reset
    def test_update_job_description_adds_see_notes_indicator_and_outline(self, admin_page, admin_user) -> None:
        """Test that when a job description is added to a job that previously had no description, the job card updates to have a see notes indicator and an outline."""
        page = admin_page
        page.set_default_timeout(3_000)
        test_helper = JobViewsTestHelper(page)
        assigned_jobs = test_helper.job_service.get_jobs_for_user_on_date(admin_user.id, admin_user.team_id, today_in_app_tz())
        job_without_description = None
        for job in assigned_jobs:
            if not job.description:
                job_without_description = job
                break
        assert job_without_description is not None, "No assigned job without a description found for admin user, please insure the " \
        "local SQLite test database is seeded with appropriate data for this test to be valid"
        job_id = job_without_description.id
        test_helper.update_job(
            job_id,
            description="This is a test description."
        )
        updated_job_card = test_helper.get_job_card_by_id(job_id)
        expect(updated_job_card.locator(".job-statuses").get_by_text("See Notes")).to_be_visible()
        expect(updated_job_card).to_have_class(re.compile(r"red-outline"))

    @pytest.mark.db_reset
    def test_create_job(self, admin_page, admin_user) -> None:
        page = admin_page
        page.set_default_timeout(3_000)
        page.get_by_text("Create Job").wait_for(state="attached")

        test_helper = JobViewsTestHelper(page)
        test_helper.create_job(
            start_time="07:00",
            end_time="08:00",
            date=today_in_app_tz().strftime(DATETIME_FORMATS["DATE_FORMAT"]),
            description="Full house clean, focus on kitchen and bathrooms.",
            property_id="2",
            access_notes="test",
            assigned_teams=test_helper.db.query(Team).filter(Team.id.in_([admin_user.team_id])).all(),
        )    

    @pytest.mark.db_reset
    def test_create_job_next_day_arrival(self, admin_page, admin_user) -> None:
        page = admin_page
        page.get_by_text("Create Job").wait_for(state="attached")

        test_helper = JobViewsTestHelper(page)
        test_helper.create_job(
            start_time="07:00",
            end_time="08:00",
            date=today_in_app_tz().strftime(DATETIME_FORMATS["DATE_FORMAT"]),
            arrival_datetime=datetime.combine(today_in_app_tz(), time(10, 0)),
            description="Full house clean, focus on kitchen and bathrooms.",
            property_id="2",
            access_notes="test",
            assigned_teams=test_helper.db.query(Team).filter(Team.id.in_([admin_user.team_id])).all(),
        )    

    def test_access_notes_visibility_supervisor(self, supervisor_page) -> None:
        """Test that the access notes are visible to supervisors within the job details."""
        page = supervisor_page
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        JobViewsTestHelper(page).assert_access_notes_visible(job_id)

    def test_access_notes_visibility_team_leader(self, team_leader_page) -> None:
        """Tests that the access notes are visible to team leaders within the job details."""
        page = team_leader_page
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        JobViewsTestHelper(page).assert_access_notes_visible(job_id)

    def test_access_notes_visibility_admin(self, admin_page) -> None:
        """Tests that the access notes are visible to admins within the job details."""
        page = admin_page
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        JobViewsTestHelper(page).assert_access_notes_visible(job_id)

    def test_access_notes_visibility_user(self, user_page) -> None:
        """Tests that the access notes are not visible to regular users within the job details."""
        page = user_page
        job_card = get_first_job_card(page)
        job_id = job_card.get_attribute('data-job-id')
        JobViewsTestHelper(page).assert_access_notes_not_visible(job_id)
