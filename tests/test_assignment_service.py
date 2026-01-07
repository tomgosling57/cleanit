
import pytest
from services.assignment_service import AssignmentService
from database import Assignment, User, Job, Team, Property, get_db, teardown_db
from datetime import date, time, datetime

@pytest.fixture
def assignment_service(app):
    with app.app_context():
        yield AssignmentService(app.config['SQLALCHEMY_SESSION']())

@pytest.fixture
def setup_assignments(app):
    with app.app_context():
        # Create a user, team, property, and job for testing
        user = User(first_name='Test', last_name='User', email='test@example.com', password_hash='password')
        team = Team(name='Test Team')
        property_obj = Property(address='123 Test St', access_notes='Test notes')
        db = get_db()
        db.add_all([property_obj])
        db.commit()
        job = Job(date=date.today(), time=time(10, 0), end_time=time(12, 0), description='A job for testing', 
                  property_id=property_obj.id, job_type='Cleaning', is_complete=False, report='No issues', 
                  arrival_datetime=datetime.combine(date.today(), time(10, 0)))
        
        db.add_all([user, team, job])
        db.commit()

        # Create assignments
        user_assignment = Assignment(user_id=user.id, job_id=job.id)
        team_assignment = Assignment(team_id=team.id, job_id=job.id)
        
        db.add_all([user_assignment, team_assignment])
        db.commit()
        
        yield user, team, job, user_assignment, team_assignment
        
        # Clean up
        db = get_db()
        db.delete(user_assignment)
        db.delete(team_assignment)
        db.delete(user)
        db.delete(team)
        db.delete(job)
        db.commit()
        teardown_db()


def test_user_assigned_to_job_assigned(assignment_service, setup_assignments):
    user, _, job, _, _ = setup_assignments
    assert assignment_service.user_assigned_to_job(user.id, job.id) is True

def test_user_assigned_to_job_not_assigned(assignment_service, setup_assignments):
    user, _, job, _, _ = setup_assignments
    # Use a non-existent user ID
    assert assignment_service.user_assigned_to_job(user.id + 999, job.id) is False

def test_team_assigned_two_job_assigned(assignment_service, setup_assignments):
    _, team, job, _, _ = setup_assignments
    assert assignment_service.team_assigned_two_job(team.id, job.id) is True

def test_team_assigned_two_job_not_assigned(assignment_service, setup_assignments):
    _, team, job, _, _ = setup_assignments
    # Use a non-existent team ID
    assert assignment_service.team_assigned_two_job(team.id + 999, job.id) is False
