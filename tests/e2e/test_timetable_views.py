# tests/test_timetable.py
import os
import re
from controllers.jobs_controller import ERRORS
from playwright.sync_api import expect
import pytest
from config import DATETIME_FORMATS
from tests.helpers import (
    get_csrf_token, assert_job_card_variables, make_htmx_request, mark_job_as_complete, assert_job_card_default_state,
    assert_job_not_found_htmx_error, assert_team_column_content, delete_job_and_confirm,
    get_future_date,
)
from utils.timezone import to_app_tz, today_in_app_tz, utc_now

def test_timetable_selected_date(admin_page) -> None:
    """Test at the timetable renders today's date in the app time zone."""
    page = admin_page
    selected_date = page.locator("#timetable-datepicker").input_value()
    assert selected_date == to_app_tz(utc_now()).strftime(DATETIME_FORMATS['DATE_FORMAT'])
    assert selected_date == today_in_app_tz().strftime(DATETIME_FORMATS['DATE_FORMAT'])
    assert os.getenv('APP_TIMEZONE') == 'Australia/Melbourne'

@pytest.mark.db_reset
def test_supervisors_timetable(supervisor_page) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a supervisor.

    Args:
        supervisor_page: Playwright page object with supervisor authentication
    Returns:
        None
    """
    page = supervisor_page
    

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 10:30 (1h 30m)"
    }, expected_indicators=["See Notes"])
    expect(job_card_1).to_have_class(re.compile(r"red-outline"))
    job_card_1.get_by_text("Property Address: 123 Main St, Anytown").click()
    
    # Check that supervisor can mark job as complete
    mark_job_as_complete(page, job_card_1)

    # View job details modal
    job_card_1.get_by_role("button", name="View Details").click()
    page.locator("#job-modal").get_by_text("×").click()

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 10:00",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Same Day Arrival"])
    assert_job_card_default_state(job_card_2)

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 12:30",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(job_card_3)

    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(job_card_4)

@pytest.mark.db_reset
def test_admin_timetable(admin_page) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an admin.

    Args:
        admin_page: Playwright page object with admin authentication
    Returns:
        None
    """
    page = admin_page

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 11:00 (2h)"
    }, expected_indicators=["See Notes"])
    expect(job_card_1).to_have_class(re.compile(r"red-outline"))
    job_card_1.get_by_text("Property Address: 123 Main St, Anytown").click()
    expect(job_card_1).to_have_attribute("data-view-type", "normal")
    
    # Check that supervisor can mark job as complete
    mark_job_as_complete(page, job_card_1)

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(job_card_2)

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])
    assert_job_card_default_state(job_card_3)

def test_user_timetable(user_page) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a user.

    Args:
        user_page: Playwright page object with user authentication
    Returns:
        None
    """
    page = user_page

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 11:00 (2h)"
    }, expected_indicators=["See Notes"])
    expect(job_card_1).to_have_class(re.compile(r"red-outline"))

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(job_card_2)
    
    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])
    assert_job_card_default_state(job_card_3)

    # Assert user job assignment
    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(job_card_4)


def test_admin_team_timetable(admin_page) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an admin with team assignments.

    Args:
        admin_page: Playwright page object with admin authentication
    Returns:
        None
    """
    page = admin_page
    
    page.get_by_text('Team View').click()

    # Initial Team
    # Assert the jobs loaded and the job holds have all of the necessary details rendered
    team_column_1 = page.locator('div.column-container').first
    assert_team_column_content(team_column_1, "Initial Team", 3)
    
    team_1_job_card_1 = team_column_1.locator('div.job-card').first
    assert_job_card_variables(team_1_job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 11:00 (2h)"
    }, expected_indicators=["See Notes"])
    expect(team_1_job_card_1).to_have_class(re.compile(r"red-outline"))
    expect(team_1_job_card_1).to_have_attribute("data-view-type", "team")
    
    team_1_job_card_2 = team_column_1.locator('div.job-card').nth(1)
    assert_job_card_variables(team_1_job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    assert_job_card_default_state(team_1_job_card_2)
    
    team_1_job_card_3 = team_column_1.locator('div.job-card').nth(2)
    assert_job_card_variables(team_1_job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])    
    assert_job_card_default_state(team_1_job_card_3)

    # Assert the jobs loaded for the other team columns
    team_column_2 = page.locator('div.column-container').nth(1)
    assert_team_column_content(team_column_2, "Alpha Team", 4)
    team_column_3 = page.locator('div.column-container').nth(2)
    assert_team_column_content(team_column_3, "Beta Team", 2)
    team_column_4 = page.locator('div.column-container').nth(3)
    assert_team_column_content(team_column_4, "Charlie Team", 1)
    team_column_5 = page.locator('div.column-container').nth(4)
    assert_team_column_content(team_column_5, "Delta Team", 1)

@pytest.mark.db_reset
def test_team_timetable_job_reassignment(admin_page) -> None:
    """
    Test that a job can be reassigned to a different team via drag-and-drop in the team timetable.

    Args:
        admin_page: Playwright page object with admin authentication
    Returns:
        None
    """
    page = admin_page
    
    page.get_by_text('Team View').click()

    # Drag and drop a job from one team to another
    team_column_1 = page.locator('div.team-column').first
    job_card_to_move = team_column_1.locator('div.job-card').first
    team_column_2 = page.locator('div.team-column').nth(1)
    move_target = team_column_2.locator('div.job-card').first
    page.wait_for_timeout(500)
    job_id = int(job_card_to_move.get_attribute('data-job-id'))
    job_card_to_move = page.locator(f'div.job-card[data-job-id="{job_id}"]')
    job_card_to_move.drag_to(move_target)

    # Verify that the job has been moved to the new team column
    expect(team_column_2.locator(f'div.job-card[data-job-id="{job_id}"]')).to_be_visible()
    expect(team_column_1.locator(f'div.job-card[data-job-id="{job_id}"]')).to_have_count(0)

@pytest.mark.db_reset
def test_delete_job(admin_page) -> None:
    page = admin_page

    expect(page.locator('div.job-card').first).to_be_visible()
    job_card = page.locator('div.job-card').first
    job_id = int(job_card.get_attribute('data-job-id'))
    expect(job_card.locator(".job-close-button")).to_be_visible()
    job_card = page.locator(f'div.job-card[data-job-id="{job_id}"]')
    delete_job_and_confirm(page, job_card)

def test_auto_push_for_uncompleted_jobs(admin_page) -> None:
    """
    Test that uncompleted jobs from previous days are pushed to the next day upon accessing the timetable.

    Checks for the presence of the second beta team job which has yesterday's date.

    Args:
        admin_page: Playwright page object with admin authentication
    """
    page = admin_page

    page.get_by_text('Team View').click()

    team_column_3 = page.locator('div.column-container').nth(2)
    # Check that the job from previous day is now present in today's timetable
    yesterday_job = team_column_3.locator('div.job-card').nth(1)
    expect(yesterday_job).to_be_visible()