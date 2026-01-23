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
def goto(page, live_server):
    """Helper fixture that navigates to a path"""
    def _goto(path="/", _page=None):
        if _page is None:
            _page = page
        return _page.goto(f"{live_server.url()}{path}")
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
def _create_auth_state(browser, live_server, email, password):
    """
    Generic helper for creating authentication state.
    Uses pytest-playwright's browser fixture to avoid nested async contexts.
    """
    context = browser.new_context()
    page = context.new_page()

    page.goto(f"{live_server.url()}/")
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
def admin_auth_state(browser, live_server):
    """
    Creates and returns authentication state (cookies, storage) for admin user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        live_server,
        "admin@example.com",
        "admin_password",
    )

@pytest.fixture(scope="session")
def supervisor_auth_state(browser, live_server):
    """
    Creates and returns authentication state (cookies, storage) for supervisor user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        live_server,
        "supervisor@example.com",
        "supervisor_password",
    )

@pytest.fixture(scope="session")
def user_auth_state(browser, live_server):
    """
    Creates and returns authentication state (cookies, storage) for regular user.
    Uses CSRF-disabled server so authentication state can be saved and reused.
    """
    return _create_auth_state(
        browser,
        live_server,
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
def admin_page(admin_context, live_server):
    """
    Creates a page with admin user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = admin_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{live_server.url()}/jobs/")
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
def supervisor_page(supervisor_context, live_server):
    """
    Creates a page with supervisor user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = supervisor_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{live_server.url()}/jobs/")
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
def user_page(user_context, live_server):
    """
    Creates a page with regular user already authenticated and navigates to timetable.
    Uses CSRF-disabled server.
    """
    page = user_context.new_page()
    page.set_default_navigation_timeout(5000)
    # Navigate to timetable page (where login redirects to)
    page.goto(f"{live_server.url()}/jobs/")
    page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture(autouse=True)
def rollback_db_after_test(app):
    """Rollback database changes after each test to maintain isolation."""
    yield  # Test runs here

    # Use the reseed endpoint to reset the database state    
    get('http://localhost:5000/testing/reseed-database')