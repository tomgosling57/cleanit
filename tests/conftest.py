# conftest.py
from typing import Generator
import pytest
from flask_login import LoginManager, login_user
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
from services.media_service import MediaService
from utils.populate_database import populate_database
from database import Team, get_db, teardown_db, User, Property, Job, Assignment, Media, PropertyMedia, JobMedia

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
    Configures and creates a Flask app for testing temporary storage.
    Uses a temporary upload directory and sets STORAGE_PROVIDER to 'temp'.
    """
    import tempfile
    import os
    
    login_manager = LoginManager()
    
    # Create a temporary directory for uploads in the current directory
    # instead of /tmp to avoid permission issues with libcloud trying to delete parent directories
    cwd = os.getcwd()
    temp_upload_dir = tempfile.mkdtemp(prefix='test_uploads_', dir=cwd)
    
    test_config = {
        'TESTING': True,
        'STORAGE_PROVIDER': 'temp',
        'UPLOAD_FOLDER': temp_upload_dir,
        'SECRET_KEY': 'testsecret',
        'DATABASE_URL': 'sqlite:///:memory:',
    }

    app = create_app(login_manager=login_manager, config_override=test_config)
    
    with app.app_context():
        yield app

    # Clean up the temporary directory after the test
    try:
        import shutil
        shutil.rmtree(temp_upload_dir, ignore_errors=True)
    except Exception as e:
        print(f"Error cleaning up temporary upload directory {temp_upload_dir}: {e}")

@pytest.fixture(scope='session')
def app(test_db_path):
    """
    Configures and creates a Flask app for testing.
    The database is configured to be seeded with deterministic data for consistent testing.
    Uses temporary storage for file uploads.
    pytest-flask will use this fixture automatically.
    """
    login_manager = LoginManager()
    
    test_config = {
        'TESTING': True,
        'STORAGE_PROVIDER': 'temp',  # Use temporary storage for all tests
    }
    
    app = create_app(login_manager=login_manager, config_override=test_config)
    populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app

@pytest.fixture(scope='session')
def app_no_csrf(test_db_path):
    """
    Configures and creates a Flask app for testing with CSRF protection disabled.
    Useful for API testing where CSRF tokens are not needed.
    """
    login_manager = LoginManager()
    
    test_config = {
        'TESTING': True,
        'STORAGE_PROVIDER': 'temp',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection
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
        # Delete any media and their associations to ensure clean state
        db_session = get_db()
        try:
            db_session.query(PropertyMedia).delete()
            db_session.query(JobMedia).delete()
            db_session.query(Media).delete()
            db_session.commit()
        finally:
            teardown_db()
        
        # Reseed data to initial state
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])

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

# User fixtures for authentication testing
@pytest.fixture
def admin_user():
    """
    A mock admin user object for testing.
    """
    user = User(
        id=999,
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True,
        is_authenticated=True,
        is_anonymous=False
    )
    return user

@pytest.fixture
def regular_user():
    """
    A mock regular user object for testing.
    """
    user = User(
        id=998,
        email="user@example.com",
        first_name="Regular",
        last_name="User",
        role="user",
        is_active=True,
        is_authenticated=True,
        is_anonymous=False
    )
    return user

@pytest.fixture
def authenticated_client(app, admin_user):
    """
    Provides a Flask test client with a mocked admin user logged in.
    Uses unittest.mock.patch to replace flask_login.current_user.
    """
    with app.test_client() as client:
        with patch('flask_login.current_user', new=admin_user):
            yield client

@pytest.fixture
def regular_authenticated_client(app, regular_user):
    """
    Provides a Flask test client with a mocked regular user logged in.
    Uses unittest.mock.patch to replace flask_login.current_user.
    """
    with app.test_client() as client:
        with patch('flask_login.current_user', new=regular_user):
            yield client

# Integration testing helpers
def login_user_for_test(client, email, password):
    """
    Helper function to log in a user via the application's login endpoint.
    Returns the client with an authenticated session.
    """
    response = client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    return client

def login_admin_for_test(client):
    """Helper to log in as admin with correct password."""
    return login_user_for_test(client, "admin@example.com", "admin_password")

def login_regular_for_test(client):
    """Helper to log in as regular user with correct password."""
    return login_user_for_test(client, "user@example.com", "user_password")

@pytest.fixture
def admin_client(app):
    """
    Provides a Flask test client with a real admin user logged in.
    Uses the seeded database to find an admin user and logs in via the login endpoint.
    """
    with app.test_client() as client:
        login_admin_for_test(client)
        yield client

@pytest.fixture
def regular_client(app):
    """
    Provides a Flask test client with a real regular user logged in.
    Uses the seeded database to find a regular user and logs in via the login endpoint.
    """
    with app.test_client() as client:
        login_regular_for_test(client)
        yield client

# Client fixtures with CSRF disabled for API testing
@pytest.fixture
def admin_client_no_csrf(app_no_csrf):
    """
    Provides a Flask test client with a real admin user logged in and CSRF disabled.
    """
    with app_no_csrf.test_client() as client:
        login_admin_for_test(client)
        yield client

@pytest.fixture
def regular_client_no_csrf(app_no_csrf):
    """
    Provides a Flask test client with a real regular user logged in and CSRF disabled.
    """
    with app_no_csrf.test_client() as client:
        login_regular_for_test(client)
        yield client

@pytest.fixture
def authenticated_client_no_csrf(app_no_csrf, admin_user):
    """
    Provides a Flask test client with a mocked admin user logged in and CSRF disabled.
    """
    with app_no_csrf.test_client() as client:
        with patch('flask_login.current_user', new=admin_user):
            yield client

@pytest.fixture
def regular_authenticated_client_no_csrf(app_no_csrf, regular_user):
    """
    Provides a Flask test client with a mocked regular user logged in and CSRF disabled.
    """
    with app_no_csrf.test_client() as client:
        with patch('flask_login.current_user', new=regular_user):
            yield client

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

@pytest.fixture
def media_service(app):
    with app.app_context():
        yield MediaService(app.config['SQLALCHEMY_SESSION']())



