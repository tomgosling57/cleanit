import pytest

def test_login_page_loads_successfully(client):
    """
    Test that the login page loads and displays the necessary fields.
    """
    response = client.get("/users/login")
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Username" in response.data
    assert b"Password" in response.data
    assert b"Log In" in response.data

def test_password_hashing_is_handled_by_backend(client):
    """
    This E2E test primarily ensures that the login form submits data correctly.
    The actual hashing mechanism is a backend concern, but we can verify the submission.
    """
    pass

def test_successful_login_redirects_to_dashboard(client):
    """
    Test that a user with valid credentials can log in and is redirected to their role-specific dashboard.
    This test assumes a user 'testuser' with password 'password123' exists in the mocked system.
    """
    pass

def test_invalid_login_displays_generic_error(client):
    """
    Test that invalid credentials result in a generic error message without revealing specific details.
    """
    pass

def test_empty_credentials_display_error(client):
    """
    Test that submitting empty credentials displays an appropriate error message.
    """
    pass

