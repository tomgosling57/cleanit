import pytest
from flask import Flask
from unittest.mock import MagicMock
from app import app as main_app # Import the main app instance
from flask_login import FlaskLoginClient, current_user, login_user, UserMixin

# Mock User class for testing purposes
class MockUser(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

# Override Flask's default test client with FlaskLoginClient
main_app.test_client_class = FlaskLoginClient

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

@pytest.fixture
def login_owner(client, app_context):
    from services.user_service import UserService
    from unittest.mock import patch

    owner_user = MockUser(1, 'owner_user', 'owner')

    with patch('services.user_service.UserService.authenticate_user') as mock_authenticate_user:
        mock_authenticate_user.return_value = owner_user
        client.post('/users/login', data={'username': 'owner_user', 'password': 'password'}, follow_redirects=True)
    return owner_user

@pytest.fixture
def login_cleaner(client, app_context):
    from services.user_service import UserService
    from unittest.mock import patch

    cleaner_user = MockUser(2, 'cleaner_user', 'cleaner')

    with patch('services.user_service.UserService.authenticate_user') as mock_authenticate_user:
        mock_authenticate_user.return_value = cleaner_user
        client.post('/users/login', data={'username': 'cleaner_user', 'password': 'password'}, follow_redirects=True)
    return cleaner_user