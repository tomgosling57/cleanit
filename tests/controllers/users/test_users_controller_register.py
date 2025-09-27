"""
Unit tests for the UsersController register function.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, session, flash, url_for, request, redirect, render_template

@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield

@pytest.fixture
def request_context():
    app = Flask(__name__)
    with app.test_request_context():
        yield

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.teardown_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.request', new_callable=MagicMock)
@patch('controllers.users_controller.session', new_callable=MagicMock)
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_register_owner_post_success(mock_url_for, mock_flash, mock_session, mock_request, mock_user_service, mock_teardown_db, mock_get_db, app_context, request_context):
    # Arrange
    from controllers.users_controller import register
    mock_session.get.return_value = 'owner'
    mock_request.method = 'POST'
    
    mock_request.form = MagicMock()
    mock_request.form.get.side_effect = lambda key, default=None: {
        'username': 'newuser',
        'password': 'password123',
        'role': 'cleaner'
    }.get(key, default)
    
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    
    new_user_data = {'id': 3, 'username': 'newuser', 'role': 'cleaner'}
    mock_user_service_instance.register_user.return_value = (new_user_data, None)
    
    mock_url_for.return_value = '/login' # Mock redirect URL

    # Act
    response = register()

    # Assert
    mock_session.get.assert_called_once_with('role')
    mock_request.form.get.assert_any_call('username')
    mock_request.form.get.assert_any_call('password')
    mock_request.form.get.assert_any_call('role', 'cleaner')
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.register_user.assert_called_once_with('newuser', 'password123', 'cleaner')
    mock_teardown_db.assert_called_once()
    mock_flash.assert_called_once_with('User registered successfully!', 'success')
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/login'
# Test stubs for register function
def test_register_get_owner_role_renders_template(app_context, request_context):
    """
    Test that an owner role making a GET request to /register renders the register template.
    """
    pass

def test_register_get_cleaner_role_redirects_to_index(app_context, request_context):
    """
    Test that a cleaner role making a GET request to /register redirects to the index page.
    """
    pass

def test_register_post_missing_username_flashes_error(app_context, request_context):
    """
    Test that a POST request with a missing username flashes an error and renders the register template.
    """
    pass

def test_register_post_missing_password_flashes_error(app_context, request_context):
    """
    Test that a POST request with a missing password flashes an error and renders the register template.
    """
    pass

def test_register_post_user_service_error_flashes_error(app_context, request_context):
    """
    Test that if UserService.register_user returns an error, it flashes an error and renders the register template.
    """
    pass

def test_register_post_success_redirects_to_login(app_context, request_context):
    """
    Test that a successful POST request to /register flashes a success message and redirects to the login page.
    """
    pass