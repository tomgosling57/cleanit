# tests/test_timetable.py
from datetime import datetime, time, timedelta
from playwright.sync_api import expect
from config import DATETIME_FORMATS
from tests.helpers import login_cleaner, login_owner, login_team_leader, assert_job_card_variables, mark_job_as_complete


def test_team_leaders_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a team leader.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_team_leader(page, goto)
    

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 10:30 (1h 30m)"
    }, expected_indicators=["Back to Back"])
    job_card_1.get_by_text("Property Address: 123 Main St, Anytown").click()
    
    # Check that team leader can mark job as complete
    mark_job_as_complete(job_card_1)

    # View job details modal
    job_card_1.get_by_role("button", name="View Details").click()
    page.locator("#job-modal").get_by_text("×").click()

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 10:00",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Back to Back", "Same Day Arrival"])

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 12:30",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Back to Back", "Next Day Arrival"])

    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    expect(job_card_4.get_by_text("Back to Back")).to_be_hidden()

def test_owner_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an owner.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_owner(page, goto)

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 11:00 (2h)"
    }, expected_indicators=["Back to Back"])
    job_card_1.get_by_text("Property Address: 123 Main St, Anytown").click()
    
    # Check that team leader can mark job as complete
    mark_job_as_complete(job_card_1)

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Next Day Arrival"])

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Same Day Arrival"])

def test_cleaner_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a cleaner.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_cleaner(page, goto)

    # Check jobs in expected order    
    job_card_1 = page.locator('div.job-card').first
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_1, {
        "time": "Time: 09:00",
        "address": "Property Address: 123 Main St, Anytown",
        "ends": "Ends: 11:00 (2h)"
    }, expected_indicators=["Back to Back"])
    job_card_1.get_by_text("Property Address: 123 Main St, Anytown").click()

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Next Day Arrival"])

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Same Day Arrival"])

    # Assert user job assignment
    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    expect(job_card_4.get_by_text("Back to Back")).to_be_hidden()


def test_owner_team_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an owner with team assignments.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_owner(page, goto)
    
    page.get_by_text('Team View').click()

    # Initial Team
    # Assert the jobs loaded and the job holds have all of the necessary details rendered
    team_column_1 = page.locator('div.team-column').first
    expect(team_column_1.get_by_role("heading", name="Initial Team")).to_be_visible()
    expect(team_column_1.locator('div.job-card')).to_have_count(3)
    team_1_job_card_2 = team_column_1.locator('div.job-card').nth(1)
    assert_job_card_variables(team_1_job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Next Day Arrival"])
    team_1_job_card_3 = team_column_1.locator('div.job-card').nth(2)
    assert_job_card_variables(team_1_job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Back to Back", "Same Day Arrival"])    

    # Assert the jobs loaded for the other team columns
    team_column_2 = page.locator('div.team-column').nth(1)
    expect(team_column_2.get_by_role("heading", name="Alpha Team")).to_be_visible()
    expect(team_column_2.locator('div.job-card')).to_have_count(4)
    team_column_3 = page.locator('div.team-column').nth(2)
    expect(team_column_3.get_by_role("heading", name="Beta Team")).to_be_visible()
    expect(team_column_3.locator('div.job-card')).to_have_count(1)
    team_column_4 = page.locator('div.team-column').nth(3)
    expect(team_column_4.get_by_role("heading", name="Charlie Team")).to_be_visible()
    expect(team_column_4.locator('div.job-card')).to_have_count(1)
    team_column_5 = page.locator('div.team-column').nth(4)
    expect(team_column_5.get_by_role("heading", name="Delta Team")).to_be_visible()
    expect(team_column_5.locator('div.job-card')).to_have_count(1)

def test_team_timetable_job_reassignment(page, goto) -> None:
    """
    Test that a job can be reassigned to a different team via drag-and-drop in the team timetable.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_owner(page, goto)
    
    page.get_by_text('Team View').click()

    # Drag and drop a job from one team to another
    team_column_1 = page.locator('div.team-column').first
    job_card_to_move = team_column_1.locator('div.job-card').first
    team_column_2 = page.locator('div.team-column').nth(1)
    # move_target = team_column_2.locator('div.job-card').first

    job_id = int(job_card_to_move.get_attribute('data-job-id'))
    # old_team_id = int(team_column_1.get_attribute('data-team-id'))
    # new_team_id = int(team_column_2.get_attribute('data-team-id'))

    with page.expect_response(f"**/jobs/job/reassign**"):
        job_card_to_move.drag_to(team_column_2)
        # Verify that the job has been moved to the new team column
        expect(team_column_2.locator(f'div.job-card[data-job-id="{job_id}"]')).to_be_visible()
        expect(team_column_1.locator(f'div.job-card[data-job-id="{job_id}"]')).to_have_count(0)