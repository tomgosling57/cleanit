"""
Unit tests for the UsersController update_user and delete_user functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import jsonify


@patch('controllers.users_controller.UserService')
def test_update_user_success(mock_user_service, client):
    # Arrange
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    user_id = 1
    update_data = {'username': 'updateduser', 'role': 'owner'}
    expected_user = {'id': user_id, 'username': 'updateduser', 'role': 'owner'}
    mock_user_service_instance.update_user.return_value = expected_user

    # Act
    response = client.put(f'/users/{user_id}/update', json=update_data)

    # Assert
    mock_user_service.assert_called_once()
    mock_user_service_instance.update_user.assert_called_once_with(user_id, update_data)
    assert response.status_code == 200
    assert response.json == expected_user

@patch('controllers.users_controller.UserService')
def test_delete_user_success(mock_user_service, client):
    # Arrange
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    user_id = 1
    mock_user_service_instance.delete_user.return_value = True

    # Act
    response = client.delete(f'/users/{user_id}/delete')

    # Assert
    mock_user_service.assert_called_once()
    mock_user_service_instance.delete_user.assert_called_once_with(user_id)
    assert response.status_code == 200
    assert response.json == {'message': 'User deleted successfully'}

@patch('controllers.users_controller.UserService')
def test_delete_user_not_found(mock_user_service, client):
    # Arrange
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    user_id = 999
    mock_user_service_instance.delete_user.return_value = False

    # Act
    response = client.delete(f'/users/{user_id}/delete')

    # Assert
    mock_user_service.assert_called_once()
    mock_user_service_instance.delete_user.assert_called_once_with(user_id)
    assert response.status_code == 404
    assert response.json == {'error': 'User not found'}

@patch('controllers.users_controller.UserService')
def test_update_user_invalid_data(mock_user_service, client):
    # Arrange
    mock_user_service_instance = MagicMock()
    mock_user_service.return_value = mock_user_service_instance

    user_id = 1
    invalid_data = {'invalid_field': 'value'} # Example of invalid data

    # Act
    response = client.put(f'/users/{user_id}/update', json=invalid_data)

    # Assert
    mock_user_service.assert_not_called() # UserService should not be called if data is invalid
    mock_user_service_instance.update_user.assert_not_called()
    assert response.status_code == 400
    assert response.json == {'error': 'No valid fields provided for update'}