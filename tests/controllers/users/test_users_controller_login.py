"""
Unit tests for the UsersController login function.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import session, flash, url_for, request, redirect, render_template



@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_login_post_success_sets_session_and_redirects_to_index(mock_url_for, mock_flash, mock_user_service, mock_get_db, client):
    # Arrange
    from controllers.users_controller import login

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    authenticated_user = {'id': 1, 'username': 'testuser', 'role': 'cleaner'}
    mock_user_service_instance.authenticate_user.return_value = authenticated_user

    mock_url_for.return_value = '/index' # Mock redirect URL

    # Act
    response = client.post('/users/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('testuser', 'password123')
    mock_flash.assert_called_once_with(f'Welcome back, {authenticated_user["username"]}!', 'success')
    with client.session_transaction() as sess:
        assert sess['user_id'] == authenticated_user['id']
        assert sess['username'] == authenticated_user['username']
        assert sess['role'] == authenticated_user['role']
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/index'

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
def test_login_post_invalid_credentials_flashes_error(mock_flash, mock_user_service, mock_get_db, client):
    # Arrange
    from controllers.users_controller import login

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    mock_user_service_instance.authenticate_user.return_value = None

    # Act
    response = client.post('/users/login', data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('wronguser', 'wrongpassword')
    mock_flash.assert_called_once_with('Invalid username or password', 'error')
    assert response.status_code == 200 # Renders template
    assert b"Login" in response.data # Assuming 'Login' is in the login.html template

def test_login_get_renders_template(client):
    # Arrange
    from controllers.users_controller import login

    # Act
    response = client.get('/users/login')

    # Assert
    assert response.status_code == 200
    assert b"Login" in response.data # Assuming 'Login' is in the login.html template

# Test stubs for login function  
def test_login_post_missing_username_renders_template(client, app_context):
    """
    Test that a POST request with a missing username flashes an error and renders the login template.
    """
    with patch('controllers.users_controller.flash') as mock_flash:
        response = client.post('/users/login', data={
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b"Login" in response.data
        mock_flash.assert_called_once_with('Invalid username or password', 'error')

def test_login_post_missing_password_renders_template(client, app_context):
    """
    Test that a POST request with a missing password flashes an error and renders the login template.
    """
    with patch('controllers.users_controller.flash') as mock_flash:
        response = client.post('/users/login', data={
            'username': 'testuser'
        })
        assert response.status_code == 200
        assert b"Login" in response.data
        mock_flash.assert_called_once_with('Invalid username or password', 'error')

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
def test_login_post_invalid_credentials_flashes_error_stub_replacement(mock_flash, mock_user_service, mock_get_db, client):
    # Arrange
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    mock_user_service_instance.authenticate_user.return_value = None

    # Act
    response = client.post('/users/login', data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('wronguser', 'wrongpassword')
    mock_flash.assert_called_once_with('Invalid username or password', 'error')
    assert response.status_code == 200
    assert b"Login" in response.data

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_login_post_success_sets_session_and_redirects_to_index_stub_replacement(mock_url_for, mock_flash, mock_user_service, mock_get_db, client):
    # Arrange
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    authenticated_user = {'id': 1, 'username': 'testuser', 'role': 'cleaner'}
    mock_user_service_instance.authenticate_user.return_value = authenticated_user

    mock_url_for.return_value = '/index'

    # Act
    response = client.post('/users/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.authenticate_user.assert_called_once_with('testuser', 'password123')
    mock_flash.assert_called_once_with(f'Welcome back, {authenticated_user["username"]}!', 'success')
    with client.session_transaction() as sess:
        assert sess['user_id'] == authenticated_user['id']
        assert sess['username'] == authenticated_user['username']
        assert sess['role'] == authenticated_user['role']
    assert response.status_code == 302
    assert response.headers['Location'] == '/index'