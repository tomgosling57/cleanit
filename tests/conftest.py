import pytest
from flask import Flask
from unittest.mock import MagicMock
from app import app as main_app # Import the main app instance

@pytest.fixture
def app_context():
    with main_app.app_context():
        yield

@pytest.fixture
def client():
    main_app.config['TESTING'] = True
    main_app.config['SQLALCHEMY_SESSION'] = MagicMock() # Mock the SQLAlchemy session
    with main_app.test_client() as client:
        yield client