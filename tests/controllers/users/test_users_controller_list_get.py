"""
Unit tests for the UsersController list_users and get_user functions.
"""
import pytest
from unittest.mock import MagicMock, patch
from services.user_service import UserService
from database import User


def test_list_users(client, app_context):
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Create dummy users
        dummy_users = [
            {'id': 1, 'username': 'testuser1', 'role': 'cleaner'},
            {'id': 2, 'username': 'testuser2', 'role': 'owner'}
        ]
        
        # Mock the UserService.list_users method
        with patch('services.user_service.UserService.list_users', return_value=dummy_users) as mock_list_users:
            response = client.get('/users/')

            assert response.status_code == 200
            assert response.json == dummy_users
            mock_list_users.assert_called_once()
            mock_get_db.assert_called_once()

def test_get_user_success(client, app_context):
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        dummy_user = {'id': 1, 'username': 'testuser', 'role': 'cleaner'}
        
        with patch('services.user_service.UserService.get_user_by_id', return_value=dummy_user) as mock_get_user_by_id:
            response = client.get('/users/1')
            
            assert response.status_code == 200
            assert response.json == dummy_user
            mock_get_user_by_id.assert_called_once_with(1)
            mock_get_db.assert_called_once()


def test_list_users_empty_list(client, app_context):
    """
    Test that list_users returns an empty list when no users are present.
    """
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        with patch('services.user_service.UserService.list_users', return_value=[]) as mock_list_users:
            response = client.get('/users/')
            
            assert response.status_code == 200
            assert response.json == []
            mock_list_users.assert_called_once()
            mock_get_db.assert_called_once()

def test_list_users_database_error(client, app_context):
    """
    Test that list_users handles database errors gracefully.
    """
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        with patch('services.user_service.UserService.list_users', side_effect=Exception("Database error")) as mock_list_users:
            response = client.get('/users/')
            
            assert response.status_code == 500
            assert response.json == {'error': 'Internal Server Error'}
            mock_list_users.assert_called_once()
            mock_get_db.assert_called_once()

def test_get_user_not_found(client, app_context):
    """
    Test that get_user returns a 404 error when the user is not found.
    """
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        with patch('services.user_service.UserService.get_user_by_id', return_value=None) as mock_get_user_by_id:
            response = client.get('/users/999')
            
            assert response.status_code == 404
            assert response.json == {'error': 'User not found'}
            mock_get_user_by_id.assert_called_once_with(999)
            mock_get_db.assert_called_once()

def test_get_user_invalid_id(client, app_context):
    """
    Test that get_user handles invalid user IDs (e.g., non-integer) gracefully.
    """
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # We don't need to mock UserService.get_user_by_id here, as the routing should handle invalid IDs
        response = client.get('/users/abc')
        
        assert response.status_code == 404 # Flask's default for invalid URL parameters
        mock_get_db.assert_not_called() # get_db should not be called for invalid routes

def test_get_user_database_error(client, app_context):
    """
    Test that get_user handles database errors gracefully.
    """
    with patch('controllers.users_controller.get_db') as mock_get_db, \
         patch('controllers.users_controller.teardown_db') as mock_teardown_db:
        
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        with patch('services.user_service.UserService.get_user_by_id', side_effect=Exception("Database error")) as mock_get_user_by_id:
            response = client.get('/users/1')
            
            assert response.status_code == 500
            assert response.json == {'error': 'Internal Server Error'}
            mock_get_user_by_id.assert_called_once_with(1)
            mock_get_db.assert_called_once()