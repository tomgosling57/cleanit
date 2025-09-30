import pytest
from database import User
from werkzeug.security import check_password_hash

def test_set_password_hashes_and_salts_password():
    """
    Test that the set_password method correctly hashes and salts the password.
    """
    user = User(username='testuser', role='cleaner')
    password = 'securepassword'
    user.set_password(password)

    assert user.password_hash is not None
    assert user.password_hash != password
    assert check_password_hash(user.password_hash, password)

def test_check_password_hash_valid_password():
    """
    Test that check_password_hash returns True for a valid password.
    """
    user = User(username='testuser', role='cleaner')
    password = 'securepassword'
    user.set_password(password)

    assert check_password_hash(user.password_hash, password)

def test_check_password_hash_invalid_password():
    """
    Test that check_password_hash returns False for an invalid password.
    """
    user = User(username='testuser', role='cleaner')
    password = 'securepassword'
    user.set_password(password)

    assert not check_password_hash(user.password_hash, 'wrongpassword')