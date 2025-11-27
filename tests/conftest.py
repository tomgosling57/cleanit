# conftest.py
import pytest
from flask_login import LoginManager
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
    login_manager = LoginManager()
    
    test_config = {
        'TESTING': True,
        'DATABASE': test_db_path,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
        'DEBUG': True,
        'SECRET_KEY': 'test-secret-key',
    }
    
    app = create_app(login_manager=login_manager, test_config=test_config)
    
    yield app

@pytest.fixture
def goto(page, live_server):
    """Helper fixture that navigates to a path"""
    def _goto(path="/"):
        return page.goto(f"{live_server.url()}{path}")
    return _goto