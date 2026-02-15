from bs4 import BeautifulSoup
import pytest

from config import DATETIME_FORMATS
from database import Job, Assignment, Team
from tests.db_helpers import get_db_session
from utils.test_data import get_job_data_by_id
from utils.timezone import today_in_app_tz

def test_timetable_timezone_handling(admin_client_no_csrf, job_service, admin_user):
    """Tests that the default selected date is the current date in the application timezone."""
    response = admin_client_no_csrf.get("/jobs/")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.text, "html.parser")
    job_list = soup.select_one("#job-list")
    assert job_list is not None
    expected_date = today_in_app_tz().strftime(DATETIME_FORMATS['DATE_FORMAT'])
    expected_timetable_date = today_in_app_tz().isoformat()
    assert job_list['data-selected-date'] == expected_timetable_date, \
        f"Expected data-selected-date to be {expected_timetable_date} but got {job_list['data-selected-date']}"
    job_cards = soup.select(".job-card")
    expected_jobs = job_service.get_jobs_for_user_on_date(user_id=admin_user.id, team_id=admin_user.team_id, date_obj=today_in_app_tz())
    expected_jobs = {job.id: job for job in expected_jobs}
    assert len(job_cards) == len(expected_jobs), f"Expected {len(expected_jobs)} job cards but found {len(job_cards)}"    
    for job_card in job_cards:
        job_id = int(job_card['data-job-id'])
        assert job_id in expected_jobs, f"Job card with id {job_id} does not match any expected job"
        job_date = job_card.select_one(f"#job-date-{job_id}").text
        job_start_time = job_card.select_one(f"#job-start-time-{job_id}").text
        job_end_time = job_card.select_one(f"#job-end-time-{job_id}").text
        job_duration = job_card.select_one(f"#job-duration-{job_id}").text
        job_property_address = job_card.select_one(f"#job-property-address-{job_id}").text
        assert job_date == expected_date, f"Expected job date for job {job_id} to be {expected_date} but got {job_date}"
        assert job_start_time == expected_jobs[job_id].display_time, f"Expected job start time for job {job_id} to be {expected_jobs[job_id].display_time} but got {job_start_time}"
        assert job_end_time == expected_jobs[job_id].display_end_time, f"Expected job end time for job {job_id} to be {expected_jobs[job_id].display_end_time} but got {job_end_time}"
        assert job_duration == expected_jobs[job_id].duration, f"Expected job duration for job {job_id} to be {expected_jobs[job_id].duration} but got {job_duration}"
        assert job_property_address == expected_jobs[job_id].property.address, \
            f"Expected job property address for job {job_id} to be {expected_jobs[job_id].property.address} but got {job_property_address}"                              

def test_team_timetable_timezone_handling(admin_client_no_csrf, assignment_service, job_service):
    """Tests that the default selected date on the team timetable is the current date in the application timezone."""
    response = admin_client_no_csrf.get("/jobs/teams/")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.text, "html.parser")
    job_list = soup.select_one("#team-columns-container")
    assert job_list is not None
    expected_date = today_in_app_tz().strftime(DATETIME_FORMATS['DATE_FORMAT'])
    expected_timetable_date = today_in_app_tz().isoformat()
    assert job_list['data-selected-date'] == expected_timetable_date, \
        f"Expected data-selected-date to be {expected_timetable_date} but got {job_list['data-selected-date']}"
    # Check that the rendered timetable matches the expected jobs by team 
    check_jobs_by_team(job_service.get_jobs_grouped_by_team_for_date(today_in_app_tz()), soup, expected_date=expected_date)

def check_jobs_by_team(expected_jobs_by_team: dict, soup: BeautifulSoup, expected_date: str = None):
    """Test that the rendered timetable matches the expected jobs by team according to the database content. Expects a dict with team ids as keys and lists of job objects as values."""
    expected_jobs_by_team = {team.id: jobs for team, jobs in expected_jobs_by_team.items()}
    team_columns = soup.select(".team-column")
    assert len(team_columns) == len(expected_jobs_by_team), f"Expected {len(expected_jobs_by_team)} team columns but found {len(team_columns)}"
    for team_column in team_columns:
        team_id = int(team_column['data-team-id'])
        assert expected_jobs_by_team.get(team_id) is not None, f"Team column with id {team_id} does not match any expected team"
        job_cards = team_column.select(".job-card")
        expected_jobs = {job.id: job for job in expected_jobs_by_team[team_id]}
        assert len(job_cards) == len(expected_jobs), f"Expected {len(expected_jobs)} job cards for team {team_id} but found {len(job_cards)}"
        for job_card in job_cards:
            job_id = int(job_card['data-job-id'])
            assert job_id in expected_jobs, f"Job card with id {job_id} does not match any expected job for team {team_id}"
            job_date = job_card.select_one(f"#job-date-{job_id}").text
            job_start_time = job_card.select_one(f"#job-start-time-{job_id}").text
            job_end_time = job_card.select_one(f"#job-end-time-{job_id}").text
            job_duration = job_card.select_one(f"#job-duration-{job_id}").text
            job_property_address = job_card.select_one(f"#job-property-address-{job_id}").text
            assert job_date == expected_date, f"Expected job date for job {job_id} to be {expected_date} but got {job_date}"
            assert job_start_time == expected_jobs[job_id].display_time, f"Expected job start time for job {job_id} to be {expected_jobs[job_id].display_time} but got {job_start_time}"
            assert job_end_time == expected_jobs[job_id].display_end_time, f"Expected job end time for job {job_id} to be {expected_jobs[job_id].display_end_time} but got {job_end_time}"
            assert job_duration == expected_jobs[job_id].duration, f"Expected job duration for job {job_id} to be {expected_jobs[job_id].duration} but got {job_duration}"
            assert job_property_address == expected_jobs[job_id].property.address, \
                f"Expected job property address for job {job_id} to be {expected_jobs[job_id].property.address} but got {job_property_address}"                              

@pytest.mark.parametrize("client_fixture", ["admin_client_no_csrf", "supervisor_client_no_csrf", "regular_client_no_csrf"])
def test_timetable_job_data(request, client_fixture):
    """Tests that the job data rendered on the timetable views matches the test data."""
    client = request.getfixturevalue(client_fixture)
    response = client.get("/jobs/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    job_cards = soup.select(".job-card")
    for job_card in job_cards:
        validate_job_time_data_with_test_data(job_card)

def validate_job_time_data_with_test_data(job_card):
    job_id = int(job_card['data-job-id'])
    job_date = job_card.select_one(f"#job-date-{job_id}").text
    job_start_time = job_card.select_one(f"#job-start-time-{job_id}").text
    expected_job = get_job_data_by_id(job_id)
    assert job_date == expected_job['date'].strftime(DATETIME_FORMATS['DATE_FORMAT']), f"Expected job date for job {job_id} to be {expected_job['date'].strftime(DATETIME_FORMATS['DATE_FORMAT'])} but got {job_date}"
    assert job_start_time == expected_job['start_time'].strftime(DATETIME_FORMATS['TIME_FORMAT']), f"Expected job start time for job {job_id} to be {expected_job['start_time']} but got {job_start_time}"
    