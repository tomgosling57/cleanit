# tests/test_timetable.py
from datetime import datetime, time, timedelta
import re
from playwright.sync_api import expect
from config import DATETIME_FORMATS
from tests.conftest import page
from tests.helpers import login_user, login_admin, login_supervisor, assert_job_card_variables, mark_job_as_complete


def test_supervisors_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a supervisor.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_supervisor(page, goto)
    

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
    mark_job_as_complete(job_card_1)

    # View job details modal
    job_card_1.get_by_role("button", name="View Details").click()
    page.locator("#job-modal").get_by_text("×").click()

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 10:00",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Same Day Arrival"])
    expect( job_card_2.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_2).not_to_have_class(re.compile(r"red-outline"))

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 12:30",
        "address": "Property Address: 456 Oak Ave, Teamville"
    }, expected_indicators=["Next Day Arrival"])
    expect( job_card_3.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_3).not_to_have_class(re.compile(r"red-outline"))

    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    expect( job_card_4.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_4).not_to_have_class(re.compile(r"red-outline"))

def test_admin_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an admin.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_admin(page, goto)

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
    mark_job_as_complete(job_card_1)

    job_card_2 = page.locator('div.job-card').nth(1)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_2, {
        "time": "Time: 12:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    expect( job_card_2.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_2).not_to_have_class(re.compile(r"red-outline"))

    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])
    expect( job_card_3.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_3).not_to_have_class(re.compile(r"red-outline"))

def test_user_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as a user.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_user(page, goto)

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
    expect(job_card_2.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_2).not_to_have_class(re.compile(r"red-outline"))
    
    job_card_3 = page.locator('div.job-card').nth(2)
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])
    expect(job_card_3.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_3).not_to_have_class(re.compile(r"red-outline"))

    # Assert user job assignment
    job_card_4 = page.locator('div.job-card').last
    # Assert that jobs are listed in chronological order
    assert_job_card_variables(job_card_4, {
        "time": "Time: 18:30",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Next Day Arrival"])
    expect(job_card_4.get_by_text("See Notes")).to_be_hidden()
    expect(job_card_4  ).not_to_have_class(re.compile(r"red-outline"))

def test_admin_team_timetable(page, goto) -> None:
    """
    Test that the timetable is displayed correctly after logging in as an admin with team assignments.

    Args:
        page: Playwright page object
        goto: Function to navigate to a URL
    Returns:
        None
    """
    login_admin(page, goto)
    
    page.get_by_text('Team View').click()

    # Initial Team
    # Assert the jobs loaded and the job holds have all of the necessary details rendered
    team_column_1 = page.locator('div.column-container').first
    expect(team_column_1.get_by_text("Initial Team")).to_be_visible()
    expect(team_column_1.locator('div.job-card')).to_have_count(3)
    
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
    expect(team_1_job_card_2.get_by_text("See Notes")).to_be_hidden()
    expect(team_1_job_card_2).not_to_have_class(re.compile(r"red-outline"))
    
    team_1_job_card_3 = team_column_1.locator('div.job-card').nth(2)
    assert_job_card_variables(team_1_job_card_3, {
        "time": "Time: 14:00",
        "address": "Property Address: 123 Main St, Anytown"
    }, expected_indicators=["Same Day Arrival"])    
    expect(team_1_job_card_3.get_by_text("See Notes")).to_be_hidden()
    expect(team_1_job_card_3).not_to_have_class(re.compile(r"red-outline"))

    # Assert the jobs loaded for the other team columns
    team_column_2 = page.locator('div.column-container').nth(1)
    expect(team_column_2.get_by_role("heading", name="Alpha Team")).to_be_visible()
    expect(team_column_2.locator('div.job-card')).to_have_count(4)
    team_column_3 = page.locator('div.column-container').nth(2)
    expect(team_column_3.get_by_role("heading", name="Beta Team")).to_be_visible()
    expect(team_column_3.locator('div.job-card')).to_have_count(1)
    team_column_4 = page.locator('div.column-container').nth(3)
    expect(team_column_4.get_by_role("heading", name="Charlie Team")).to_be_visible()
    expect(team_column_4.locator('div.job-card')).to_have_count(1)
    team_column_5 = page.locator('div.column-container').nth(4)
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
    login_admin(page, goto)
    
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
        page.wait_for_load_state('networkidle')
        job_card_to_move.drag_to(team_column_2)
        # Verify that the job has been moved to the new team column
        expect(team_column_2.locator(f'div.job-card[data-job-id="{job_id}"]')).to_be_visible()
        expect(team_column_1.locator(f'div.job-card[data-job-id="{job_id}"]')).to_have_count(0)

def test_delete_job(page, goto) -> None:
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()
    job_card = page.locator('div.job-card').first

    expect(job_card.locator(".job-close-button")).to_be_visible()

    page.on('dialog', lambda d: d.accept())

    with page.expect_response(f"**/jobs/job/{job_card.get_attribute('data-job-id')}/delete**"):
        page.wait_for_load_state('networkidle')
        job_card.locator(".job-close-button").click()
    expect(page.locator('#job-1')).to_be_hidden()

def test_job_not_found_handling_for_update_status(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to interact with non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/999/update_status**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('POST', '{server_url}/jobs/job/999/update_status', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    

def test_job_not_found_handling_for_get_job_details(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to get details of a non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/999/details**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('GET', '{server_url}/jobs/job/999/details', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    

def test_job_not_found_handling_for_update_job(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to update a non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/999/update**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('PUT', '{server_url}/jobs/job/999/update', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered

def test_job_not_found_handling_for_delete_job(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to delete a non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/999/delete**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('DELETE', '{server_url}/jobs/job/999/delete', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    

def test_job_not_found_handling_for_get_update_job_form(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to get update form of a non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/999/update**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('GET', '{server_url}/jobs/job/999/update', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#job-list')).to_be_visible() # Assert job list fragment is rendered
    

def test_job_not_found_handling_for_reassign_job_team(page, goto, server_url) -> None:
    """Test that the job not found message is displayed when trying to reassign team for a non-existent job.
    
    Args:
        page: Playwright page object
        goto: Function to navigate to a URL"""
    login_admin(page, goto)

    page.get_by_text('Team View').click()
    
    expect(page.locator('div.job-card').first).to_be_visible()

    with page.expect_response(f"**/jobs/job/reassign**") as response_info:
        page.wait_for_function("() => window.htmx !== undefined")
        page.evaluate(f"""
            htmx.ajax('POST', '{server_url}/jobs/job/reassign', {{
                target: '#errors-container',
                swap: 'innerHTML',
                values: {{
                    job_id: 999,
                    new_team_id: 1,
                    date: '{datetime.today().strftime(DATETIME_FORMATS["DATE_FORMAT"])}',
                    view_type: 'team'
                }}
            }})
        """)

    expect(page.get_by_text("Something went wrong! That job no longer exists.")).to_be_visible()
    expect(page.get_by_text("View type not provided, defaulting to normal.")).to_be_hidden()
    expect(page.locator('#team-timetable-view')).to_be_visible() # Assert team timetable fragment is rendered
    