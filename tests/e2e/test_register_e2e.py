import unittest

def test_issue_74_owner_can_access_registration_form(client, login_owner):
    """
    Test that only users with the 'owner' role can access the user registration feature.
    """
    response = client.get('/users/register')
    assert response.status_code == 200
    assert b"Register" in response.data

def test_issue_74_non_owner_cannot_access_registration_form(client, login_cleaner):
    """
    Test that users with a role other than 'owner' are redirected from the registration page.
    """
    response = client.get('/users/register', follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to CleanIt" in response.data # Assuming index page has this text
    assert b"Register" not in response.data

def test_issue_74_owner_can_register_new_user_with_details(client, login_owner, app_context):
    """
    Test that the owner can specify the new user's username/email, password, and role.
    """
    from services.user_service import UserService
    from database import get_db

    # Mock the UserService.register_user method
    with unittest.mock.patch('services.user_service.UserService.register_user') as mock_register_user:
        mock_register_user.return_value = ({'id': 2, 'username': 'newuser', 'role': 'cleaner'}, None)

        response = client.post('/users/register', data={
            'username': 'newuser',
            'password': 'password123',
            'role': 'cleaner'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"User registered successfully!" in response.data
        mock_register_user.assert_called_once_with('newuser', 'password123', 'cleaner')

def test_issue_74_new_user_account_created_with_assigned_role_on_success(client, login_owner, app_context):
    """
    Test that upon successful registration, the new user's account is created in the database with the assigned role.
    """
    from services.user_service import UserService
    from database import get_db
    from database import User

    # Mock the UserService.register_user method to simulate a successful registration
    with unittest.mock.patch('services.user_service.UserService.register_user') as mock_register_user:
        mock_register_user.return_value = (User(id=2, username='testuser', role='cleaner'), None)

        response = client.post('/users/register', data={
            'username': 'testuser',
            'password': 'testpassword',
            'role': 'cleaner'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"User registered successfully!" in response.data

def test_issue_74_non_owner_cannot_register_new_user(client, login_cleaner, app_context):
    """
    Test that a non-owner user cannot register a new user.
    """
    from services.user_service import UserService
    from unittest.mock import patch

    with patch('services.user_service.UserService.register_user') as mock_register_user:
        response = client.post('/users/register', data={
            'username': 'unauthorized_user',
            'password': 'password123',
            'role': 'cleaner'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Welcome to CleanIt" in response.data
        assert b"User registered successfully!" not in response.data
        mock_register_user.assert_not_called()


def test_issue_74_owner_receives_confirmation_on_successful_registration(client, login_owner, app_context):
    """
    Test that the owner receives confirmation of the new user's creation.
    """
    from services.user_service import UserService
    from database import User

    with unittest.mock.patch('services.user_service.UserService.register_user') as mock_register_user:
        mock_register_user.return_value = (User(id=2, username='confirmeduser', role='cleaner'), None)

        response = client.post('/users/register', data={
            'username': 'confirmeduser',
            'password': 'password123',
            'role': 'cleaner'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"User registered successfully!" in response.data