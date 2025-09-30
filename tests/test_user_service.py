import pytest
from unittest.mock import MagicMock, patch
from services.user_service import UserService
from database import User
from werkzeug.security import generate_password_hash, check_password_hash

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def user_service(mock_db_session):
    return UserService(mock_db_session)

@pytest.fixture
def sample_user_data():
    return {
        'id': 1,
        'username': 'testuser',
        'password': 'password123',
        'role': 'cleaner'
    }

class TestUserService:
    def test_list_users(self, user_service, mock_db_session):
        user1 = User(id=1, username='user1', role='cleaner')
        user2 = User(id=2, username='user2', role='manager')
        
        mock_db_session.query.return_value.all.return_value = [user1, user2]
        
        users = user_service.list_users()
        
        assert len(users) == 2
        assert users[0].username == 'user1'
        assert users[1].role == 'manager'
        mock_db_session.query.assert_called_once_with(User)

    def test_get_user_by_id_found(self, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        user = user_service.get_user_by_id(1)
        
        assert user.id == sample_user_data['id']
        assert user.username == sample_user_data['username']
        assert user.role == sample_user_data['role']
        mock_db_session.query.assert_called_once_with(User)
        mock_db_session.query.return_value.filter_by.assert_called_once_with(id=1)

    def test_get_user_by_id_not_found(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        user = user_service.get_user_by_id(99)
        
        assert user is None
        mock_db_session.query.assert_called_once_with(User)
        mock_db_session.query.return_value.filter_by.assert_called_once_with(id=99)

    def test_get_user_by_username_found(self, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_user.password_hash = generate_password_hash(sample_user_data['password'])
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        user = user_service.get_user_by_username('testuser')
        
        assert user.username == sample_user_data['username']
        assert user.password_hash == mock_user.password_hash
        mock_db_session.query.assert_called_once_with(User)
        mock_db_session.query.return_value.filter_by.assert_called_once_with(username='testuser')

    def test_get_user_by_username_not_found(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        user = user_service.get_user_by_username('nonexistent')
        
        assert user is None
        mock_db_session.query.assert_called_once_with(User)
        mock_db_session.query.return_value.filter_by.assert_called_once_with(username='nonexistent')

    def test_register_user_success(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        user_data, error = user_service.register_user('newuser', 'newpassword')
        
        assert error is None
        assert user_data['username'] == 'newuser'
        assert user_data['role'] == 'cleaner'
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_register_user_username_exists(self, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        user_data, error = user_service.register_user('testuser', 'password123')
        
        assert user_data is None
        assert error == 'Username already exists'
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @patch('services.user_service.check_password_hash')
    def test_authenticate_user_success(self, mock_check_password_hash, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_user.password_hash = generate_password_hash(sample_user_data['password'])
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_check_password_hash.return_value = True
        
        user = user_service.authenticate_user(sample_user_data['username'], sample_user_data['password'])
        
        assert user.username == sample_user_data['username']
        assert user.role == sample_user_data['role']
        mock_check_password_hash.assert_called_once_with(mock_user.password_hash, sample_user_data['password'])

    @patch('services.user_service.check_password_hash')
    def test_authenticate_user_invalid_password(self, mock_check_password_hash, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_user.password_hash = generate_password_hash(sample_user_data['password'])
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_check_password_hash.return_value = False
        
        user = user_service.authenticate_user(sample_user_data['username'], 'wrongpassword')
        
        assert user is None
        mock_check_password_hash.assert_called_once_with(mock_user.password_hash, 'wrongpassword')

    def test_authenticate_user_not_found(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        user = user_service.authenticate_user('nonexistent', 'password')
        
        assert user is None

    def test_update_user_success(self, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        updated_data = {'username': 'updateduser', 'role': 'manager', 'password': 'newpassword'}
        user = user_service.update_user(1, updated_data)
        
        assert user.username == 'updateduser'
        assert user.role == 'manager'
        mock_user.set_password.assert_called_once_with('newpassword')
        mock_db_session.commit.assert_called_once()

    def test_update_user_not_found(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        user = user_service.update_user(99, {'username': 'updated'})
        
        assert user is None
        mock_db_session.commit.assert_not_called()

    def test_delete_user_success(self, user_service, mock_db_session, sample_user_data):
        mock_user = MagicMock(spec=User, **sample_user_data)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        result = user_service.delete_user(1)
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()

    def test_delete_user_not_found(self, user_service, mock_db_session):
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = user_service.delete_user(99)
        
        assert result is False
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()