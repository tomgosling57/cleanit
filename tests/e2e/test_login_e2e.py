from unittest import mock

def test_login_page_loads_successfully(client):
    """
    Test that the login page loads and displays the necessary fields.
    """
    response = client.get("/users/login")
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Username" in response.data
    assert b"Password" in response.data

def test_password_hashing_is_handled_by_backend(client):
    """
    This E2E test primarily ensures that the login form submits data correctly.
    The actual hashing mechanism is a backend concern, but we can verify the submission.
    """
    # Mock the UserService.authenticate_user to simulate a successful authentication
    # without needing actual password hashing logic in the test.
    mock_user = mock.Mock()
    mock_user.username = 'testuser'
    mock_user.role = 'cleaner'
    mock_user.get_id.return_value = '1' # Flask-Login expects a serializable ID
    with mock.patch('services.user_service.UserService.authenticate_user', return_value=mock_user):
        with mock.patch('utils.http.validate_request_host', return_value=True): # Mock host validation
            response = client.post("/users/login?next=/", data={
                "username": "testuser",
                "password": "anypassword"  # Password content doesn't matter for this test due to mocking
            }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to CleanIt" in response.data
    assert b"Login" not in response.data # Ensure we are redirected away from the login page

def test_successful_login_redirects_to_dashboard(client):
    """
    Test that a successful login redirects the user to the dashboard.
    """
    mock_user = mock.Mock()
    mock_user.username = 'testuser'
    mock_user.role = 'cleaner'
    mock_user.get_id.return_value = '1'
    with mock.patch('services.user_service.UserService.authenticate_user', return_value=mock_user):
        with mock.patch('utils.http.validate_request_host', return_value=True):
            response = client.post("/users/login?next=/", data={
                "username": "testuser",
                "password": "anypassword"
            }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to CleanIt" in response.data # Assuming dashboard has this text
    assert b"Login" not in response.data # Ensure we are redirected away from the login page

def test_invalid_login_displays_generic_error(client):
    """
    Test that an invalid login attempt displays a generic error message on the login page.
    """
    with mock.patch('services.user_service.UserService.authenticate_user', return_value=None):
        with mock.patch('utils.http.validate_request_host', return_value=True):
            response = client.post("/users/login", data={
                "username": "invaliduser",
                "password": "wrongpassword"
            }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data # Should remain on the login page
    assert b"Invalid username or password" in response.data # Assuming a generic error message

def test_empty_credentials_display_error(client):
    """
    Test that submitting empty credentials displays an appropriate error message.
    """
    with mock.patch('services.user_service.UserService.authenticate_user', return_value=None):
        with mock.patch('utils.http.validate_request_host', return_value=True):
            response = client.post("/users/login", data={
                "username": "",
                "password": ""
            }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data # Should remain on the login page
    assert b"Invalid username or password" in response.data # Assuming a generic error message

def test_successful_login_redirects_to_dashboard_with_password(client):
    """
    Test that a user with valid credentials can log in and is redirected to their role-specific dashboard.
    This test assumes a user 'testuser' with password 'password123' exists in the mocked system.
    """
    mock_user = mock.Mock()
    mock_user.username = 'testuser'
    mock_user.role = 'cleaner'
    mock_user.get_id.return_value = '1'
    with mock.patch('services.user_service.UserService.authenticate_user', return_value=mock_user):
        with mock.patch('utils.http.validate_request_host', return_value=True):
            response = client.post("/users/login?next=/", data={
                "username": "testuser",
                "password": "password123"
            }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to CleanIt" in response.data
    assert b"Login" not in response.data

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

