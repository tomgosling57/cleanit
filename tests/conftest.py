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

@pytest.fixture
def create_job_and_property(app_context):
    from database import Job, Property
    from datetime import date, time
    from app import app as main_app
    from unittest.mock import patch

    # The app_context fixture already provides the application context, no need to re-enter it.
    db_session = main_app.config['SQLALCHEMY_SESSION']

    # Create a mock property
    mock_property = MagicMock(spec=Property)
    mock_property.id = 1
    mock_property.address = '123 Test St'
    mock_property.access_notes = 'Gate code 1234'
    mock_property.client_name = 'Test Client'
    mock_property.client_phone = '0400000000'

    # Create a mock job
    mock_job = MagicMock(spec=Job)
    mock_job.id = 1
    mock_job.job_title = 'Test Job'
    mock_job.date = date.today()
    
    # Create a mock time object
    mock_time = MagicMock(spec=time)
    mock_time.strftime.return_value = '09:00'
    mock_job.time = mock_time
    
    mock_job.duration = 120
    mock_job.description = 'Clean the house'
    mock_job.assigned_cleaners = '2' # cleaner_user id
    mock_job.status = 'pending'
    mock_job.job_type = 'standard'
    mock_job.property_id = 1
    mock_job.property = mock_property # Assign the mock property
    mock_job.assigned_cleaners_list = [MagicMock(username='cleaner_user', id=2)] # For multiple cleaners test
    
    # Configure property attributes for direct access
    mock_job.property.address = '123 Test St'
    mock_job.property.client_name = 'Test Client'
    mock_job.property.client_phone = '0400000000'
    mock_job.property.access_notes = 'Gate code 1234'

    # Mock the database session queries for job service
    db_session.query.return_value.filter.return_value.first.return_value = mock_job
    db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_job]
    db_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_job
    db_session.query.return_value.options.return_value.all.return_value = [mock_job]

    # Mock the job service methods directly
    with patch('services.job_service.JobService.get_cleaner_jobs_for_today') as mock_get_jobs:
        mock_get_jobs.return_value = [mock_job]
    
    with patch('services.job_service.JobService.get_job_details') as mock_get_details:
        mock_get_details.return_value = mock_job

    yield mock_job, mock_property