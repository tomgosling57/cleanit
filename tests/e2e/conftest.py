#!/usr/bin/env python3
"""
End-to-end (E2E) test fixtures for testing against a running Docker application.
This module provides fixtures for E2E tests that interact with a live Docker
application (web container) without creating a separate Flask app instance.
These tests assume Docker containers (postgres, minio, web) are already running.
"""
import pytest
import os
import subprocess
import datetime
from typing import Generator
from playwright.sync_api import Page, BrowserContext, Browser
from database import Property, User
from tests.db_helpers import get_db_session
from utils.populate_database import USER_DATA
from utils.timezone import compare_times
from requests import get


def docker_containers_running():
    """Check if required Docker containers are running."""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--services', '--filter', 'status=running'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        running_services = result.stdout.strip().split('\n')
        required_services = {'postgres', 'minio', 'web'}
        return all(service in running_services for service in required_services)
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Skip all E2E tests if containers are not running
pytestmark = pytest.mark.skipif(
    not docker_containers_running(),
    reason="Docker containers (postgres, minio, web) must be running. Run 'docker compose up -d' first."
)


# Playwright fixtures for Docker environment

@pytest.fixture(scope="session")
def server_url() -> str:
    """
    Get the base URL for the flask application running in the cleanit-web container.
    """
    return "http://localhost:5000/"


@pytest.fixture
def goto(page, server_url):
    """Helper fixture that navigates to a path"""
    def _goto(path="/", _page=None):
        if _page is None:
            _page = page
        return _page.goto(f"{server_url}{path}")
    return _goto


@pytest.fixture
def context(browser) -> Generator[BrowserContext, None, None]:
    ctx = browser.new_context()  # NEW context per test
    yield ctx
    ctx.close()


@pytest.fixture
def page(context) -> Generator[Page, None, None]:
    page = context.new_page()
    page.set_default_navigation_timeout(5000)  # the timeout is in milliseconds
    yield page


# --- Helper to create auth state ---
def _create_auth_state(browser: Browser, server_url: str, email: str, password: str):
    """
    Creates authentication state for a user.
    """
    context = browser.new_context()
    page = context.new_page()
    page.goto(f"{server_url}/")
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


# --- Generic auth page fixture creator ---
def create_auth_page_fixture(user_key: str):
    """Factory function to create authenticated page fixtures for different user roles."""
    def _auth_page(browser: Browser, server_url: str) -> Generator[Page, None, None]:
        # Create a new context for this user
        context: BrowserContext = browser.new_context(
            storage_state=_create_auth_state(
                browser, 
                server_url,
                USER_DATA[user_key]['email'],
                USER_DATA[user_key]['password']
            )
        )
        page: Page = context.new_page()
        page.set_default_navigation_timeout(5000)
        page.goto(f"{server_url}/jobs/")
        page.wait_for_load_state("networkidle")
        yield page
        context.close()
    
    # Set a unique name for the function to avoid pytest conflicts
    _auth_page.__name__ = f"{user_key}_page"
    return _auth_page


# --- Create and register fixtures for each user role ---
admin_page = pytest.fixture()(create_auth_page_fixture("admin"))
supervisor_page = pytest.fixture()(create_auth_page_fixture("supervisor"))
user_page = pytest.fixture()(create_auth_page_fixture("user"))
team_leader_page = pytest.fixture()(create_auth_page_fixture("team_leader"))


@pytest.fixture(scope="session")
def db_with_test_data():
    """Populate database once for the entire test session."""
    from tests.db_helpers import get_session_maker
    from utils.populate_database import populate_database
    
    Session = get_session_maker()
    populate_database(Session=Session)
    
    yield


@pytest.fixture(autouse=True)
def handle_db_reset(request, db_with_test_data):
    """
    Automatically reset database after tests marked with @pytest.mark.db_reset.
    
    Usage:
        @pytest.mark.db_reset
        def test_that_modifies_database():
            # Test code that commits changes
            pass
    """
    yield
    
    # Check if the test has the db_reset marker
    if request.node.get_closest_marker('db_reset'):
        from tests.db_helpers import get_session_maker
        from utils.populate_database import populate_database
        
        Session = get_session_maker()
        populate_database(Session=Session)


def pytest_collection_modifyitems(config, items):
    """Skip all tests if Docker containers are not running."""
    def skip_items(items, reason):
        skip_marker = pytest.mark.skip(reason=reason)
        for item in items:
            item.add_marker(skip_marker)
    
    if os.getenv('FLASK_ENV') != 'testing':
        skip_items(items, "E2E tests require FLASK_ENV to be set to 'testing'")
        return
    
    if not docker_containers_running():
        skip_items(items, "Docker containers not running")
        return
    
    # Make sure the reseed database endpoint is available
    reason = "Reseed database endpoint not available. Ensure the web container is running and FLASK_ENV is set to 'testing'."
    try:
        response = get('http://localhost:5000/testing/reseed-database')
        if response.status_code != 200:
            skip_items(items, reason)
            return
        
        # Check timezone endpoint
        response = get('http://localhost:5000/testing/timezone')
        if response.status_code != 200:
            skip_items(items, "Timezone endpoint not available.")
            return
        
        data = response.json()
        
        app_tz = data.get('system_timezone')
        app_tz_config = data.get('APP_TIMEZONE')
        testing_tz = os.getenv('APP_TIMEZONE')
        if app_tz != testing_tz or app_tz_config != testing_tz:
            reason = f"APP_TIMEZONE mismatch: expected '{testing_tz}', got '{app_tz}'"
            skip_items(items, reason)
        
        app_dt = datetime.datetime.fromisoformat(data.get('current_time_utc'))
        now_dt = datetime.datetime.utcnow()
        if compare_times(app_dt, now_dt)['difference_seconds'] > 5:
            reason = f"System time mismatch: app time '{app_dt}' vs system time '{now_dt}'"
            skip_items(items, reason)
        
    except Exception as e:
        skip_marker = pytest.mark.skip(reason=reason + f" (Error: {str(e)})")
        for item in items:
            item.add_marker(skip_marker)


@pytest.fixture
def admin_user():
    """
    An existing admin user object from the test database.
    """
    db_session = get_db_session()
    user = db_session.query(User).filter_by(role="admin").first()
    return user


@pytest.fixture
def supervisor_user():
    """
    An existing supervisor user object from the test database.
    """
    db_session = get_db_session()
    user = db_session.query(User).filter_by(role="supervisor").first()
    return user


@pytest.fixture
def user_user():
    """
    An existing regular user object from the test database.
    """
    db_session = get_db_session()
    user = db_session.query(User).filter_by(role="user").first()
    return user

@pytest.fixture
def team_leader_user():
    """
    An existing team leader user object from the test database.
    """
    db_session = get_db_session()
    user = db_session.query(User).filter(User.is_team_leader == True).filter(User.role == "user").first()
    return user

@pytest.fixture
def anytown_property():
    """
    An existing property object from the test database with address "123 Main St, Anytown".
    """
    db_session = get_db_session()
    property = db_session.query(Property).filter_by(address="123 Main St, Anytown").first()
    return property

@pytest.fixture
def teamville_property():
    """
    An existing property object from the test database with address "456 Oak Ave, Teamville".
    """
    db_session = get_db_session()
    property = db_session.query(Property).filter_by(address="456 Oak Ave, Teamville").first()
    return property