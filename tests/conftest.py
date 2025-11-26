# conftest.py
import pytest
from playwright.sync_api import sync_playwright
from app_factory import create_app
import tempfile
import os

@pytest.fixture(scope='session')
def test_db_path():
    """Create temp database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='session')
def app(test_db_path):
    """pytest-flask will use this fixture automatically"""
    app = create_app({
        'TESTING': True,
        'DATABASE': test_db_path,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        # Initialize database
        # db.create_all()
        pass
    
    yield app


# Playwright fixtures
@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, live_server):
    """Use pytest-flask's live_server fixture"""
    context = browser.new_context(base_url=live_server.url())
    page = context.new_page()
    yield page
    page.close()
    context.close()