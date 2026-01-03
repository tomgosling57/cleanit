# conftest.py
from typing import Generator
import pytest
from flask_login import LoginManager
from app_factory import create_app
import tempfile
import os
import shutil
from playwright.sync_api import Page, BrowserContext
from unittest.mock import MagicMock, patch

from utils.populate_database import populate_database

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
    tmpdir = tempfile.mkdtemp()
    upload_folder = os.path.join(tmpdir, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Ensure UPLOAD_FOLDER is an absolute path for send_from_directory
    absolute_upload_folder = os.path.abspath(upload_folder)

    test_config = {
        'TESTING': True,
        'STORAGE_PROVIDER': 'local',
        'UPLOAD_FOLDER': absolute_upload_folder,
        'SECRET_KEY': 'testsecret',
        'DATABASE_URL': 'sqlite:///:memory:',
    }

    app = create_app(login_manager=login_manager, config_override=test_config)
    
    with app.app_context():
        yield app

    # Clean up the temporary directory after the test
    shutil.rmtree(tmpdir, ignore_errors=True)

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