#!/usr/bin/env python3
"""
Docker-specific fixtures for integration tests.

This module provides fixtures for testing with Docker containers running
(MinIO, PostgreSQL, Flask app). These fixtures are completely isolated
from local test fixtures to prevent cross-contamination.
"""

import pytest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, rely on environment variables

from app_factory import create_app
from flask_login import LoginManager
from utils.populate_database import populate_database


def docker_containers_running():
    """Check if required Docker containers are running."""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--services', '--filter', 'status=running'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        running_services = result.stdout.strip().split('\n')
        required_services = {'postgres', 'minio', 'web'}
        return all(service in running_services for service in required_services)
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Skip all Docker tests if containers are not running
pytestmark = pytest.mark.skipif(
    not docker_containers_running(),
    reason="Docker containers (postgres, minio, web) must be running. Run 'docker compose up -d' first."
)


# Add docker marker to all tests in this directory
def pytest_collection_modifyitems(config, items):
    """Add docker marker to all tests in this directory."""
    for item in items:
        # Only add marker if not already present
        if not any(marker.name == 'docker' for marker in item.iter_markers()):
            item.add_marker(pytest.mark.docker)


@pytest.fixture(scope="session")
def docker_app_config():
    """
    Configuration for Docker-based app with S3/MinIO storage.
    
    This configuration matches the Docker Compose setup with:
    - S3 storage provider (MinIO)
    - PostgreSQL database
    - Docker network endpoints
    
    Note: We don't set TESTING=True because that would trigger TestConfig
    which uses temp storage. We want to test actual S3 storage.
    """
    os.environ['FLASK_ENV'] = 'testing'  # Ensure testing config is used
    return {
        'STORAGE_PROVIDER': 's3',
        'S3_BUCKET': os.getenv('S3_BUCKET', 'cleanit-media'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
        'AWS_ACCESS_KEY_ID': os.getenv('MINIO_ROOT_USER', 'minioadmin'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
        'S3_ENDPOINT_URL': os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000'),
        'S3_USE_HTTPS': 'false',
        'S3_VERIFY_SSL': 'false',
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://cleanit_user@localhost:5432/cleanit'),
        'SECRET_KEY': 'test-secret-key-for-docker-tests',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for API testing
    }


@pytest.fixture(scope="session")
def docker_app_debug_config(docker_app_config):
    """Configuration for debug mode {with} is a} Docker S3 storage."""
    config = docker_app_config.copy()
    os.environ['FLASK_ENV'] = 'debug'
    config['FLASK_ENV'] = 'debug'
    config['DEBUG'] = True
    return config


@pytest.fixture(scope="session")
def docker_app_production_config(docker_app_config):
    """Configuration for production mode with Docker S3 storage."""
    config = docker_app_config.copy()
    os.environ['FLASK_ENV'] = 'production'
    config['FLASK_ENV'] = 'production'
    config['DEBUG'] = False
    return config


@pytest.fixture(scope="session")
def docker_app(docker_app_config):
    """
    Create a Flask app configured for Docker S3/MinIO storage.
    
    This app uses the same configuration as the running Docker containers,
    allowing tests to interact with the actual S3/MinIO storage and
    PostgreSQL database.
    """
    login_manager = LoginManager()
    
    app = create_app(login_manager=login_manager, config_override=docker_app_config)
    
    # Populate database with test data
    with app.app_context():
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app
    
    # Cleanup if needed
    # Note: Database cleanup happens via rollback fixture in main conftest.py


@pytest.fixture(scope="session")
def docker_app_no_csrf(docker_app_config):
    """
    Create a Flask app configured for Docker with CSRF disabled.
    
    Useful for API testing where CSRF tokens are not needed.
    """
    login_manager = LoginManager()
    
    # Ensure CSRF is disabled
    config = docker_app_config.copy()
    config['WTF_CSRF_ENABLED'] = False
    
    app = create_app(login_manager=login_manager, config_override=config)
    
    # Populate database with test data
    with app.app_context():
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app


# Helper functions for authentication (copied from main conftest to avoid imports)
def _login_user_for_test(client, email, password, debug=False):
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


def _login_admin_for_test(client, debug=False):
    """Helper to log in as admin with correct password."""
    return _login_user_for_test(client, "admin@example.com", "admin_password", debug=debug)


def _login_regular_for_test(client, debug=False):
    """Helper to log in as regular user with correct password."""
    return _login_user_for_test(client, "user@example.com", "user_password", debug=debug)


@pytest.fixture
def docker_admin_client(docker_app_no_csrf):
    """
    Provides a Flask test client with admin user logged in for Docker tests.
    
    Uses the seeded database to find an admin user and logs in via the
    login endpoint. CSRF is disabled for easier API testing.
    """
    client = docker_app_no_csrf.test_client()
    _login_admin_for_test(client)
    yield client


@pytest.fixture
def docker_regular_client(docker_app_no_csrf):
    """
    Provides a Flask test client with regular user logged in for Docker tests.
    
    Uses the seeded database to find a regular user and logs in via the
    login endpoint. CSRF is disabled for easier API testing.
    """
    client = docker_app_no_csrf.test_client()
    _login_regular_for_test(client)
    yield client


@pytest.fixture
def docker_client(docker_app_no_csrf):
    """
    Provides a Flask test client without authentication for Docker tests.
    
    Useful for testing authentication flows and public endpoints.
    """
    client = docker_app_no_csrf.test_client()
    yield client


@pytest.fixture
def minio_endpoint():
    """Get the MinIO S3 endpoint URL."""
    return os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')


@pytest.fixture
def minio_bucket():
    """Get the MinIO S3 bucket name."""
    return os.getenv('S3_BUCKET', 'cleanit-media')


@pytest.fixture
def minio_credentials():
    """Get MinIO credentials."""
    return {
        'access_key': os.getenv('MINIO_ROOT_USER', 'minioadmin'),
        'secret_key': os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
    }


@pytest.fixture
def test_image_file():
    """Create a test image file for upload tests."""
    import io
    
    # Create a simple PNG file in memory
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR'  # IHDR chunk start
        b'\x00\x00\x00\x01'    # width: 1
        b'\x00\x00\x00\x01'    # height: 1
        b'\x08\x02\x00\x00\x00'  # bit depth, color type, etc.
        b'\x91x\xda\x63'       # CRC
        b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
    )
    file_obj = io.BytesIO(png_data)
    file_obj.name = 'test_image.png'
    return file_obj


@pytest.fixture
def test_jpeg_file():
    """Create a test JPEG file for upload tests."""
    import io
    
    # Minimal JPEG data (just enough to pass validation)
    jpeg_data = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
        b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01'
        b'\x00\x00?\x00\xff\xd9'
    )
    file_obj = io.BytesIO(jpeg_data)
    file_obj.name = 'test_image.jpg'
    return file_obj


def check_minio_accessible():
    """Check if MinIO is accessible."""
    import requests
    try:
        response = requests.get(
            os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000'),
            timeout=5
        )
        return response.status_code in [200, 403, 404]
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session", autouse=True)
def verify_docker_environment():
    """
    Verify Docker environment before running tests.
    
    This fixture runs automatically before any Docker test and verifies
    that the required services are accessible.
    """
    if not docker_containers_running():
        pytest.skip("Docker containers not running")
    
    if not check_minio_accessible():
        pytest.skip("MinIO not accessible")
    
    print("✓ Docker environment verified:")
    print(f"  - STORAGE_PROVIDER: {os.getenv('STORAGE_PROVIDER', 's3')}")
    print(f"  - S3_ENDPOINT_URL: {os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')}")
    print(f"  - S3_BUCKET: {os.getenv('S3_BUCKET', 'cleanit-media')}")


# Playwright fixtures for Docker environment
from typing import Generator
from playwright.sync_api import Page, BrowserContext, sync_playwright

@pytest.fixture(scope="session")
def docker_playwright_browser(pytestconfig):
    """
    Session-scoped Playwright browser for Docker tests.
    Launches a browser instance that can be used across multiple tests.
    Respects the --headed flag for visible browser windows.
    """
    playwright = sync_playwright().start()
    
    # Check if --headed flag is set
    headed = pytestconfig.getoption("--headed", False)
    
    browser = playwright.chromium.launch(
        headless=not headed,  # Show browser window if --headed flag is used
        args=["--no-sandbox"]
    )
    yield browser
    browser.close()
    playwright.stop()

@pytest.fixture
def docker_browser_context(docker_playwright_browser) -> Generator[BrowserContext, None, None]:
    """
    Function-scoped browser context for Docker tests.
    Creates a new context per test for isolation.
    """
    ctx = docker_playwright_browser.new_context()
    yield ctx
    ctx.close()

@pytest.fixture
def docker_page(docker_browser_context) -> Generator[Page, None, None]:
    """
    Function-scoped page for Docker tests.
    Creates a new page within the browser context with appropriate timeouts.
    """
    page = docker_browser_context.new_page()
    page.set_default_navigation_timeout(5000)  # 5 seconds in milliseconds
    yield page

@pytest.fixture(scope="session")
def docker_server_url(live_server):
    """
    Get the base URL from the live server for Docker tests.
    Uses pytest-flask's live_server which picks up docker_app from this module.
    """
    return live_server.url()

@pytest.fixture
def docker_goto(docker_page, docker_server_url):
    """
    Helper fixture that navigates to a path within the Docker-based application.
    """
    def _goto(path="/", _page=None):
        if _page is None:
            _page = docker_page
        return _page.goto(f"{docker_server_url}{path}")
    return _goto

def _create_docker_auth_state(docker_playwright_browser, docker_server_url, email, password):
    """
    Generic helper for creating authentication state for Docker tests.
    Uses the Docker-specific browser and server URL.
    """
    context = docker_playwright_browser.new_context()
    page = context.new_page()

    page.goto(f"{docker_server_url}/")
    page.wait_for_load_state("networkidle")

    page.locator('input[name="email"]').fill(email)
    page.locator('input[name="password"]').fill(password)

    with page.expect_response("**/user/login**"):
        page.locator('button[type="submit"]').click()

    page.wait_for_load_state("networkidle")

    assert any(k in page.url.lower() for k in ("jobs", "timetable")), "Login failed"

    state = context.storage_state()
    context.close()
    return state

@pytest.fixture(scope="session")
def docker_admin_auth_state(docker_playwright_browser, docker_server_url):
    """
    Creates and returns authentication state (cookies, storage) for admin user in Docker tests.
    """
    return _create_docker_auth_state(
        docker_playwright_browser,
        docker_server_url,
        "admin@example.com",
        "admin_password",
    )

@pytest.fixture(scope="session")
def docker_supervisor_auth_state(docker_playwright_browser, docker_server_url):
    """
    Creates and returns authentication state (cookies, storage) for supervisor user in Docker tests.
    """
    return _create_docker_auth_state(
        docker_playwright_browser,
        docker_server_url,
        "supervisor@example.com",
        "supervisor_password",
    )

@pytest.fixture(scope="session")
def docker_user_auth_state(docker_playwright_browser, docker_server_url):
    """
    Creates and returns authentication state (cookies, storage) for regular user in Docker tests.
    """
    return _create_docker_auth_state(
        docker_playwright_browser,
        docker_server_url,
        "user@example.com",
        "user_password",
    )

@pytest.fixture
def docker_admin_context(docker_playwright_browser, docker_admin_auth_state):
    """
    Creates a browser context with admin user already authenticated for Docker tests.
    """
    context = docker_playwright_browser.new_context(storage_state=docker_admin_auth_state)
    yield context
    context.close()

@pytest.fixture
def docker_admin_page(docker_admin_context, docker_server_url):
    """
    Creates a page with admin user already authenticated and navigates to jobs page for Docker tests.
    """
    page = docker_admin_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to jobs page (where login redirects to)
    page.goto(f"{docker_server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture
def docker_supervisor_context(docker_playwright_browser, docker_supervisor_auth_state):
    """
    Creates a browser context with supervisor user already authenticated for Docker tests.
    """
    context = docker_playwright_browser.new_context(storage_state=docker_supervisor_auth_state)
    yield context
    context.close()

@pytest.fixture
def docker_supervisor_page(docker_supervisor_context, docker_server_url):
    """
    Creates a page with supervisor user already authenticated and navigates to jobs page for Docker tests.
    """
    page = docker_supervisor_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to jobs page (where login redirects to)
    page.goto(f"{docker_server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture
def docker_user_context(docker_playwright_browser, docker_user_auth_state):
    """
    Creates a browser context with regular user already authenticated for Docker tests.
    """
    context = docker_playwright_browser.new_context(storage_state=docker_user_auth_state)
    yield context
    context.close()

@pytest.fixture
def docker_user_page(docker_user_context, docker_server_url):
    """
    Creates a page with regular user already authenticated and navigates to jobs page for Docker tests.
    """
    page = docker_user_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to jobs page (where login redirects to)
    page.goto(f"{docker_server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture(autouse=True)
def docker_rollback_db_after_test(docker_app):
    """
    Rollback database changes after each Docker test to maintain isolation.
    Uses docker_app for database cleanup and re-population.
    """
    yield  # Test runs here
    
    # After test completes, rollback any uncommitted changes
    with docker_app.app_context():
        from database import get_db, teardown_db, PropertyMedia, JobMedia, Media
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
        from utils.populate_database import populate_database
        populate_database(docker_app.config['SQLALCHEMY_DATABASE_URI'])

@pytest.fixture(scope='function')
def seeded_test_data(docker_app):
    """
    Fixture that provides easy access to seeded test data for Docker tests.
    Uses the Docker app context to ensure database access works with Docker configuration.
    """
    from database import get_db, teardown_db, User, Property, Job, Team, Assignment
    
    with docker_app.app_context():
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