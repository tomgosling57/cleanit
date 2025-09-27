"""
Unit tests for the UsersController login function.
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
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_login_post_success_sets_session_and_redirects_to_index(mock_url_for, mock_flash, mock_request, mock_user_service, mock_teardown_db, mock_get_db, app_context, request_context):
    # Arrange
    from controllers.users_controller import login
    mock_request.method = 'POST'
    mock_request.form = MagicMock()
    mock_request.form.get.side_effect = lambda key, default=None: {
        'username': 'testuser',
        'password': 'password123'
    }.get(key, default)

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    authenticated_user = {'id': 1, 'username': 'testuser', 'role': 'cleaner'}
    mock_user_service_instance.authenticate_user.return_value = authenticated_user

    mock_url_for.return_value = '/index' # Mock redirect URL

    # Act
    response = login()

    # Assert
    mock_request.form.get.assert_any_call('username')
    mock_request.form.get.assert_any_call('password')
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('testuser', 'password123')
    mock_teardown_db.assert_called_once()
    mock_flash.assert_called_once_with(f'Welcome back, {authenticated_user["username"]}!', 'success')
    assert session['user_id'] == authenticated_user['id']
    assert session['username'] == authenticated_user['username']
    assert session['role'] == authenticated_user['role']
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/index'

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.teardown_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.request', new_callable=MagicMock)
@patch('controllers.users_controller.flash')
def test_login_post_invalid_credentials_flashes_error(mock_flash, mock_request, mock_user_service, mock_teardown_db, mock_get_db, app_context, request_context):
    # Arrange
    from controllers.users_controller import login
    mock_request.method = 'POST'
    mock_request.form = MagicMock()
    mock_request.form.get.side_effect = lambda key, default=None: {
        'username': 'wronguser',
        'password': 'wrongpassword'
    }.get(key, default)

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    mock_user_service_instance.authenticate_user.return_value = None

    # Act
    response = login()

    # Assert
    mock_request.form.get.assert_any_call('username')
    mock_request.form.get.assert_any_call('password')
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('wronguser', 'wrongpassword')
    mock_teardown_db.assert_called_once()
    mock_flash.assert_called_once_with('Invalid username or password', 'error')
    assert response.status_code == 200 # Renders template
    assert b"Login" in response.data # Assuming 'Login' is in the login.html template

@patch('controllers.users_controller.request', new_callable=MagicMock)
def test_login_get_renders_template(mock_request, app_context, request_context):
    # Arrange
    from controllers.users_controller import login
    mock_request.method = 'GET'

    # Act
    response = login()

    # Assert
    assert response.status_code == 200
    assert b"Login" in response.data # Assuming 'Login' is in the login.html template
# Test stubs for login function
def test_login_get_renders_template(app_context, request_context):
    """
    Test that a GET request to /login renders the login template.
    """
    pass

def test_login_post_missing_username_renders_template(app_context, request_context):
    """
    Test that a POST request with a missing username renders the login template.
    """
    pass

def test_login_post_missing_password_renders_template(app_context, request_context):
    """
    Test that a POST request with a missing password renders the login template.
    """
    pass

def test_login_post_invalid_credentials_flashes_error(app_context, request_context):
    """
    Test that a POST request with invalid credentials flashes an error and renders the login template.
    """
    pass

def test_login_post_success_sets_session_and_redirects_to_index(app_context, request_context):
    """
    Test that a successful POST request to /login sets session variables and redirects to the index page.
    """
    pass