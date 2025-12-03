# conftest.py
from typing import Generator
import pytest
from flask_login import LoginManager
from app_factory import create_app
import tempfile
import os
from playwright.sync_api import Page, BrowserContext

from utils.populate_database import populate_database

@pytest.fixture(scope='session')
def test_db_path():
    """Create temp database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

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
