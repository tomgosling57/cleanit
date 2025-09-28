"""
Unit tests for the UsersController register function.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import session


@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.teardown_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_register_owner_post_success(mock_url_for, mock_flash, mock_user_service, mock_teardown_db, mock_get_db, client):
    """
    Test that a valid registration post request succeeds
    """
    # Arrange
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    
    new_user = {'id': 1, 'username': 'newuser', 'role': 'cleaner'}
    mock_user_service_instance.register_user.return_value = (new_user, None)
    
    mock_url_for.return_value = '/login'

    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.post('/users/register', data={
        'username': 'newuser',
        'password': 'password123',
        'role': 'cleaner'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.register_user.assert_called_once_with('newuser', 'password123', 'cleaner')
    mock_teardown_db.assert_any_call()  # Accept any call to teardown_db
    mock_flash.assert_called_once_with('User registered successfully!', 'success')
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/login'

def test_register_get_owner_role_renders_template(client):
    """
    Test that an owner role making a GET request to /register renders the register template.
    """
    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.get('/users/register')

    # Assert
    assert response.status_code == 200
    assert b"Register" in response.data # Assuming 'Register' is in the register.html template

def test_register_get_cleaner_role_redirects_to_index(client):
    """
    Test that a cleaner role making a GET request to /register redirects to the index page.
    """
    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'cleaner'
    
    response = client.get('/users/register')

    # Assert
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/' # Redirects to index

def test_register_post_missing_username_flashes_error(client):
    """
    Test that a POST request with a missing username flashes an error and renders the register template.
    """
    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.post('/users/register', data={
        'password': 'password123'
        # Missing username
    })

    # Assert
    assert response.status_code == 200
    assert b"Register" in response.data # Renders register template

def test_register_post_missing_password_flashes_error(client):
    """
    Test that a POST request with a missing password flashes an error and renders the register template.
    """
    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.post('/users/register', data={
        'username': 'newuser'
        # Missing password
    })

    # Assert
    assert response.status_code == 200
    assert b"Register" in response.data # Renders register template

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.teardown_db')
@patch('controllers.users_controller.UserService')
def test_register_post_user_service_error_flashes_error(mock_user_service, mock_teardown_db, mock_get_db, client):
    """
    Test that if UserService.register_user returns an error, it flashes an error and renders the register template.
    """
    # Arrange
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    
    # Simulate UserService returning an error
    mock_user_service_instance.register_user.return_value = (None, 'Username already exists')

    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.post('/users/register', data={
        'username': 'newuser',
        'password': 'password123',
        'role': 'cleaner'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.register_user.assert_called_once_with('newuser', 'password123', 'cleaner')
    mock_teardown_db.assert_any_call()  # Accept any call to teardown_db
    assert response.status_code == 200
    assert b"Register" in response.data # Renders register template

@patch('controllers.users_controller.get_db')
@patch('controllers.users_controller.teardown_db')
@patch('controllers.users_controller.UserService')
@patch('controllers.users_controller.flash')
@patch('controllers.users_controller.url_for')
def test_register_post_success_redirects_to_login(mock_url_for, mock_flash, mock_user_service, mock_teardown_db, mock_get_db, client):
    """
    Test that a successful POST request to /register flashes a success message and redirects to the login page.
    """
    # Arrange
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance
    
    new_user = {'id': 1, 'username': 'newuser', 'role': 'cleaner'}
    mock_user_service_instance.register_user.return_value = (new_user, None)
    
    mock_url_for.return_value = '/login'

    # Act
    with client.session_transaction() as sess:
        sess['role'] = 'owner'
    
    response = client.post('/users/register', data={
        'username': 'newuser',
        'password': 'password123',
        'role': 'cleaner'
    })

    # Assert
    mock_get_db.assert_called_once()
    mock_user_service.assert_called_once_with(mock_db)
    mock_user_service_instance.register_user.assert_called_once_with('newuser', 'password123', 'cleaner')
    mock_teardown_db.assert_any_call()  # Accept any call to teardown_db
    mock_flash.assert_called_once_with('User registered successfully!', 'success')
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/login'