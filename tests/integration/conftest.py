# conftest.py
from typing import Generator
import pytest
from flask_login import LoginManager, login_user
from app_factory import create_app
import tempfile
import os
import shutil
import glob
from playwright.sync_api import Page, BrowserContext, sync_playwright
from unittest.mock import MagicMock, patch
import json

from services.assignment_service import AssignmentService
from services.job_service import JobService
from services.property_service import PropertyService
from services.user_service import UserService
from services.media_service import MediaService
from utils.populate_database import insert_dummy_data, populate_database
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
def app(request, test_db_path):
    """
    Configures and creates a Flask app for testing.
    The database is configured to be seeded with deterministic data for consistent testing.
    Uses temporary storage for file uploads.
    pytest-flask will use this fixture automatically.
    
    Can be configured to disable CSRF protection using the @pytest.mark.no_csrf marker.
    """
    login_manager = LoginManager()
    
    # Check if test is marked with no_csrf
    no_csrf = request.node.get_closest_marker("no_csrf") is not None

    os.environ['FLASK_ENV'] = 'testing'  # Ensure testing config is used
    
    # Ensure APP_TIMEZONE is set for tests
    if 'APP_TIMEZONE' not in os.environ:
        os.environ['APP_TIMEZONE'] = 'Australia/Melbourne'
    
    test_config = {
        'WTF_CSRF_ENABLED': not no_csrf,  # Disable CSRF only for marked tests
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
    
    os.environ['FLASK_ENV'] = 'testing'  # Ensure testing config is used
    test_config = {
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
        insert_dummy_data(existing_session=db_session)


# User fixtures for authentication testing
@pytest.fixture
def admin_user(app):
    """
    An existing admin user object from the test database.
    """
    with app.app_context():
        db_session = get_db()
        user = db_session.query(User).filter_by(role="admin").first()
        db_session.close()
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
def login_user_for_test(client, email, password, debug=False):
    """
    Enhanced login helper with debugging and CSRF support.
    Returns the client with an authenticated session.
    """
    import re
    
    # Get the correct login URL using the app's url_for
    # The login endpoint is 'user.login' which maps to '/users/user/login'
    login_url = '/users/user/login'
    
    # First, get the login page to extract CSRF token
    login_page_response = client.get(login_url)
    if debug:
        print(f"Login page status: {login_page_response.status_code}")
        print(f"Login page content length: {len(login_page_response.data)}")
        if login_page_response.status_code != 200:
            print(f"Login page response: {login_page_response.data.decode('utf-8')[:200]}")
    
    # Extract CSRF token from the HTML
    csrf_token = None
    if login_page_response.status_code == 200:
        html = login_page_response.data.decode('utf-8')
        # Look for <input type="hidden" name="csrf_token" value="..."/>
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        if match:
            csrf_token = match.group(1)
            if debug:
                print(f"Extracted CSRF token: {csrf_token[:20]}...")
        else:
            if debug:
                print("WARNING: No CSRF token found in login page")
                # Try alternative pattern
                match = re.search(r'csrf_token.*?value="([^"]+)"', html)
                if match:
                    csrf_token = match.group(1)
                    print(f"Alternative CSRF token: {csrf_token[:20]}...")
    else:
        if debug:
            print("ERROR: Could not load login page")
    
    # Prepare login data with CSRF token if found
    login_data = {
        'email': email,
        'password': password
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    # Perform login
    response = client.post(login_url, data=login_data, follow_redirects=True)
    
    if debug:
        print(f"Login POST status: {response.status_code}")
        print(f"Login POST redirected to: {response.request.path if hasattr(response, 'request') else 'unknown'}")
        
        # Debug session
        with client.session_transaction() as session:
            session_dict = dict(session)
            print(f"Session after login: {session_dict}")
            if '_user_id' in session_dict:
                print(f"User ID in session: {session_dict['_user_id']}")
            else:
                print("WARNING: No _user_id in session - login may have failed")
    
    return client

def login_admin_for_test(client, debug=False):
    """Helper to log in as admin with correct password."""
    return login_user_for_test(client, "admin@example.com", "admin_password", debug=debug)

def login_regular_for_test(client, debug=False):
    """Helper to log in as regular user with correct password."""
    return login_user_for_test(client, "user@example.com", "user_password", debug=debug)

def debug_session(client):
    """
    Print session contents for debugging.
    """
    with client.session_transaction() as session:
        print(f"Session: {dict(session)}")

@pytest.fixture
def admin_client(app):
    """
    Provides a Flask test client with a real admin user logged in.
    Uses the seeded database to find an admin user and logs in via the login endpoint.
    """
    # Create client without context manager to avoid context nesting issues
    client = app.test_client()
    login_admin_for_test(client)
    yield client

@pytest.fixture
def regular_client(app):
    """
    Provides a Flask test client with a real regular user logged in.
    Uses the seeded database to find a regular user and logs in via the login endpoint.
    """
    # Create client without context manager to avoid context nesting issues
    client = app.test_client()
    login_regular_for_test(client)
    yield client

@pytest.fixture
def regular_client_secure(app):
    """
    Provides a Flask test client with a real regular user logged in using proper CSRF handling.
    Includes debug output to verify authentication.
    """
    # Create client without context manager to avoid context nesting issues
    client = app.test_client()
    login_regular_for_test(client, debug=True)
    # Verify login succeeded
    with client.session_transaction() as session:
        if '_user_id' not in session:
            print("WARNING: regular_client_secure login may have failed")
    yield client

@pytest.fixture
def admin_client_secure(app):
    """
    Provides a Flask test client with a real admin user logged in using proper CSRF handling.
    Includes debug output to verify authentication.
    """
    # Create client without context manager to avoid context nesting issues
    client = app.test_client()
    login_admin_for_test(client, debug=True)
    # Verify login succeeded
    with client.session_transaction() as session:
        if '_user_id' not in session:
            print("WARNING: admin_client_secure login may have failed")
    yield client

@pytest.fixture
def debug_regular_client(app):
    """
    Provides a Flask test client with a real regular user logged in and verbose debugging.
    Useful for troubleshooting authentication issues.
    """
    # Create client without context manager to avoid context nesting issues
    client = app.test_client()
    print("=== DEBUG REGULAR CLIENT LOGIN ===")
    login_regular_for_test(client, debug=True)
    print("=== DEBUG SESSION CONTENTS ===")
    debug_session(client)
    print("=== END DEBUG ===")
    yield client

# Client fixtures with CSRF disabled for API testing
@pytest.fixture
def admin_client_no_csrf(app_no_csrf):
    """
    Provides a Flask test client with a real admin user logged in and CSRF disabled.
    """
    # Create client without context manager to avoid context nesting issues
    client = app_no_csrf.test_client()
    login_admin_for_test(client)
    yield client

@pytest.fixture
def supervisor_client_no_csrf(app_no_csrf):
    """
    Provides a Flask test client with a real supervisor user logged in and CSRF disabled.
    """
    # Create client without context manager to avoid context nesting issues
    client = app_no_csrf.test_client()
    login_user_for_test(client, "supervisor@example.com", "supervisor_password")
    yield client

@pytest.fixture
def regular_client_no_csrf(app_no_csrf):
    """
    Provides a Flask test client with a real regular user logged in and CSRF disabled.
    """
    # Create client without context manager to avoid context nesting issues
    client = app_no_csrf.test_client()
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
                job_key = f"{assignment.job.property.address} {assignment.job.date.strftime('%Y-%m-%d')} {assignment.job.start_time.strftime('%H:%M')}"
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
        session = app.config['SQLALCHEMY_SESSION']()
        try:
            yield JobService(session)
        finally:
            session.close()

@pytest.fixture
def assignment_service(app):
    with app.app_context():
        session = app.config['SQLALCHEMY_SESSION']()
        try:
            yield AssignmentService(session)
        finally:
            session.close()

@pytest.fixture
def user_service(app):
    with app.app_context():
        session = app.config['SQLALCHEMY_SESSION']()
        try:
            yield UserService(session)
        finally:
            session.close()

@pytest.fixture
def property_service(app):
    with app.app_context():
        session = app.config['SQLALCHEMY_SESSION']()
        try:
            yield PropertyService(session)
        finally:
            session.close()

@pytest.fixture
def media_service(app):
    with app.app_context():
        session = app.config['SQLALCHEMY_SESSION']()
        try:
            yield MediaService(session)
        finally:
            session.close()

@pytest.fixture
def anytown_property(app):
    with app.app_context():
        db_session = get_db()
        try:
            property = db_session.query(Property).filter_by(address="123 Main St, Anytown").first()
            return property
        finally:
            db_session.close()

@pytest.fixture
def teamville_property(app):
    with app.app_context():
        db_session = get_db()
        try:
            property = db_session.query(Property).filter_by(address="456 Oak Ave, Teamville").first()
            return property
        finally:
            db_session.close()