# conftest.py
from typing import Generator
import pytest
from flask_login import LoginManager
from app_factory import create_app
import tempfile
import os
import shutil
import glob
from playwright.sync_api import Page, BrowserContext
from unittest.mock import MagicMock, patch

from services.assignment_service import AssignmentService
from services.job_service import JobService
from services.property_service import PropertyService
from services.user_service import UserService
from utils.populate_database import populate_database
from database import Team, get_db, teardown_db, User, Property, Job, Assignment

@pytest.fixture(scope='session')
def test_db_path():
    """Create temp database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def local_storage_app():
    """
    Configures and creates a Flask app for testing local storage.
    Uses a temporary upload directory and sets STORAGE_PROVIDER to 'local'.
    """
    login_manager = LoginManager()
    upload_folder = './uploads'
    # Ensure the uploads directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Track files in the upload directory before the test
    files_before_test = set(glob.glob(os.path.join(upload_folder, '*')))

    test_config = {
        'TESTING': True,
        'STORAGE_PROVIDER': 'local',
        'UPLOAD_FOLDER': os.path.abspath(upload_folder), # Ensure UPLOAD_FOLDER is an absolute path
        'SECRET_KEY': 'testsecret',
        'DATABASE_URL': 'sqlite:///:memory:',
    }

    app = create_app(login_manager=login_manager, config_override=test_config)
    
    with app.app_context():
        yield app

    # Clean up only files created by the test
    files_after_test = set(glob.glob(os.path.join(upload_folder, '*')))
    new_files = files_after_test - files_before_test
    for file_path in new_files:
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")

@pytest.fixture(scope='session')
def app(test_db_path):
    """
    Configures and creates a Flask app for testing.
    The database is configured to be seeded with deterministic data for consistent testing.
    pytest-flask will use this fixture automatically.
    """
    login_manager = LoginManager()
    
    test_config = {
        'TESTING': True,
    }
    
    app = create_app(login_manager=login_manager, config_override=test_config)
    populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app

    
@pytest.fixture(autouse=True)
def rollback_db_after_test(app):
    """Rollback database changes after each test to maintain isolation."""
    yield  # Test runs here
    
    # After test completes, rollback any uncommitted changes
    with app.app_context():
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])  # Reseed data to initial state

@pytest.fixture
def goto(page, live_server):
    """Helper fixture that navigates to a path"""
    def _goto(path="/"):
        return page.goto(f"{live_server.url()}{path}")
    return _goto


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    page.set_default_navigation_timeout(5000) # the timeout is in milliseconds
    yield page

@pytest.fixture
def server_url(live_server):
    """Get the base URL from the live server"""
    return live_server.url()

@pytest.fixture(scope='function')
def seeded_test_data(app):
    """
    Fixture that provides easy access to seeded test data (users, properties, jobs, assignments).
    Depends on 'app' to ensure the database is populated with deterministic data.
    """
    with app.app_context():
        db_session = get_db()
        try:
            users = db_session.query(User).all()
            properties = db_session.query(Property).all()
            jobs = db_session.query(Job).all()
            teams = db_session.query(Team).all()
            assignments = db_session.query(Assignment).all()
            
            
            seeded_users = {user.email: user for user in users}
            seeded_properties = {prop.address: prop for prop in properties}
            seeded_jobs = {job.id: job for job in jobs}
            seeded_teams = {team.name: team for team in teams}
            seeded_assignments = {}
            for assignment in assignments:
                job_key = f"{assignment.job.property.address} {assignment.job.date.strftime('%Y-%m-%d')} {assignment.job.time.strftime('%H:%M')}"
                if assignment.user:
                    assignment_key = f"Job: {job_key} | User: {assignment.user.email}"
                elif assignment.team:
                    assignment_key = f"Job: {job_key} | Team: {assignment.team.name}"
                else:
                    continue # Should not happen in seeded data
                seeded_assignments[assignment_key] = assignment
            
            return {
                'users': seeded_users,
                'properties': seeded_properties,
                'jobs': seeded_jobs,
                'teams': seeded_teams,
                'assignments': seeded_assignments,
            }
        finally:
            teardown_db()

# Database Service Fixtures
@pytest.fixture
def job_service(app):
    with app.app_context():
        yield JobService(app.config['SQLALCHEMY_SESSION']())

@pytest.fixture
def assignment_service(app):
    with app.app_context():
        yield AssignmentService(app.config['SQLALCHEMY_SESSION']())

@pytest.fixture
def user_service(app):
    with app.app_context():
        yield UserService(app.config['SQLALCHEMY_SESSION']())

@pytest.fixture
def property_service(app):
    with app.app_context():
        yield PropertyService(app.config['SQLALCHEMY_SESSION']())



