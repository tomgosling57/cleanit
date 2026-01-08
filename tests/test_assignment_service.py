
import pytest
from services.assignment_service import AssignmentService
from database import Assignment, User, Job, Team, Property, get_db, teardown_db
from datetime import date, time, datetime, timedelta

today = date.today()
tomorrow = date.today() + timedelta(days=1)
yesterday = date.today() - timedelta(days=1)

def test_user_assigned_to_job_assigned(assignment_service, seeded_test_data):
    """
    Tests if a user is assigned to a job then assignment_service.user_assigned_to_job returns True.
    The admin user (id=1) is assigned to job1 (id=1) in the seeded data.
    """
    # Retrieve the admin user and job1 from the seeded test data
    user = seeded_test_data['users']['admin@example.com']
    job = seeded_test_data['jobs'][1]
    # Assert that the assignment service confirms the user is assigned to the job
    assert job.id == 1
    assert user.id == 1
    assert assignment_service.user_assigned_to_job(user.id, job.id) is True

def test_user_assigned_to_job_not_assigned(assignment_service, seeded_test_data):
    """
    Tests if a user is not assigned to a job then assignment_service.user_assigned_to_job returns False.
    The 'user' user (id=3) is not assigned to job1 (id=1) in the seeded data.
    """
    # Retrieve job1 from the seeded test data
    job = seeded_test_data['jobs'][1]
    # Assert that the assignment service confirms the user is NOT assigned to the job
    assert assignment_service.user_assigned_to_job(seeded_test_data['users']['user@example.com'].id, job.id) is False

def test_team_assigned_to_job_assigned(assignment_service, seeded_test_data):
    """
    Tests if a team is assigned to a job then assignment_service.team_assigned_to_job returns True.
    The 'initial_team' (id=1) is assigned to job4 (id=4) in the seeded data.
    """
    # Retrieve the initial team and job4 from the seeded test data
    team = seeded_test_data['teams']['Alpha Team']
    job = seeded_test_data['jobs'][4]
    # Assert that the assignment service confirms the team is assigned to the job
    assert assignment_service.team_assigned_to_job(team.id, job.id) is True

def test_team_assigned_to_job_not_assigned(assignment_service, seeded_test_data):
    """
    Tests if a team is not assigned to a job then assignment_service.team_assigned_to_job returns False.
    The 'beta_team' (id=3) is not assigned to job1 (id=1) in the seeded data.
    """
    # Retrieve job1 from the seeded test data
    job = seeded_test_data['jobs'][1]
    # Assert that the assignment service confirms the team is NOT assigned to the job
    assert assignment_service.team_assigned_to_job(seeded_test_data['teams']['Beta Team'].id, job.id) is False
