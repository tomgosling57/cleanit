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
from typing import Generator
from playwright.sync_api import Page, BrowserContext, sync_playwright
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
from typing import Generator
from playwright.sync_api import Page, BrowserContext, sync_playwright

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
    page.set_default_navigation_timeout(5000) # the timeout is in milliseconds
    yield page

# Authorization state fixtures for Playwright tests
def _create_auth_state(browser, server_url, email, password):
    """
    Generic helper for creating authentication state.
    Uses pytest-playwright's browser fixture to avoid nested async contexts.
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

@pytest.fixture(scope="session")
def admin_auth_state(browser, server_url):
    """
    Creates and returns authentication state (cookies, storage) for admin user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        server_url,
        "admin@example.com",
        "admin_password",
    )

@pytest.fixture(scope="session")
def supervisor_auth_state(browser, server_url):
    """
    Creates and returns authentication state (cookies, storage) for supervisor user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        server_url,
        "supervisor@example.com",
        "supervisor_password",
    )

@pytest.fixture(scope="session")
def user_auth_state(browser, server_url):
    """
    Creates and returns authentication state (cookies, storage) for regular user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        server_url,
        "user@example.com",
        "user_password",
    )

@pytest.fixture
def admin_context(browser, admin_auth_state):
    """
    Creates a browser context with admin user already authenticated.
    """
    context = browser.new_context(storage_state=admin_auth_state)
    yield context
    context.close()

@pytest.fixture
def admin_page(admin_context, server_url):
    """
    Creates a page with admin user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = admin_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture
def supervisor_context(browser, supervisor_auth_state):
    """
    Creates a browser context with supervisor user already authenticated.
    """
    context = browser.new_context(storage_state=supervisor_auth_state)
    yield context
    context.close()

@pytest.fixture
def supervisor_page(supervisor_context, server_url):
    """
    Creates a page with supervisor user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = supervisor_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture
def user_context(browser, user_auth_state):
    """
    Creates a browser context with regular user already authenticated.
    """
    context = browser.new_context(storage_state=user_auth_state)
    yield context
    context.close()

@pytest.fixture
def user_page(user_context, server_url):
    """
    Creates a page with regular user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = user_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{server_url}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture(autouse=True)
def rollback_db_after_test():
    """Rollback database changes after each test to maintain isolation."""

    # Use the reseed endpoint to reset the database state    
    get('http://localhost:5000/testing/reseed-database')

# Skip if Docker containers not running
# This will be handled by the conftest.py in tests/e2e/
# but we add a safety check here too
def pytest_collection_modifyitems(config, items):
    """Skip all tests if Docker containers are not running."""
    if os.getenv('FLASK_ENV') != 'testing':
        skip_marker = pytest.mark.skip(reason="E2E tests require FLASK_ENV to be set to 'testing'")
        for item in items:
            item.add_marker(skip_marker)
    if not docker_containers_running():
        skip_marker = pytest.mark.skip(reason="Docker containers not running")
        for item in items:
            item.add_marker(skip_marker)
    
    # Check timezone configuration
    expected_tz = os.environ.get('APP_TIMEZONE', 'UTC')
    if expected_tz != 'UTC':
        # For E2E tests, we should verify the container's timezone matches
        try:
            response = get('http://localhost:5000/testing/timezone/check')
            if response.status_code == 200:
                data = response.json()
                container_tz = data.get('container_timezone')
                
                if container_tz != expected_tz:
                    skip_marker = pytest.mark.skip(
                        reason=f"Timezone mismatch: container is {container_tz}, expected {expected_tz}"
                    )
                    for item in items:
                        item.add_marker(skip_marker)
        except Exception as e:
            # If we can't check, log but don't skip
            print(f"Warning: Could not verify timezone configuration: {e}")
    
    # Make sure the reseed database endpoint is available
    reason = "Reseed database endpoint not available. Ensure the web container is running and FLASK_ENV is set to 'testing'."
    try:
        response = get('http://localhost:5000/testing/reseed-database')
        if response.status_code != 200:
            skip_marker = pytest.mark.skip(reason=reason)
            for item in items:
                item.add_marker(skip_marker)
    except Exception as e:
        skip_marker = pytest.mark.skip(reason=reason + f" (Error: {str(e)})")
        for item in items:
            item.add_marker(skip_marker)    