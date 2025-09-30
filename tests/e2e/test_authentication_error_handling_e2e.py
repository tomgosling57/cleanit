import pytest


def test_htmx_request_unauthorized_returns_hx_redirect(client):
    """
    Test that HTMX requests receive 401 with HX-Redirect header when unauthorized.
    """
    # Make HTMX request to a protected endpoint without authentication
    response = client.get(
        '/jobs/assigned',
        headers={'HX-Request': 'true'}
    )
    
    # Should get 401 Unauthorized with HX-Redirect header
    assert response.status_code == 401
    assert response.headers.get('HX-Redirect') == '/users/login'
    assert b'Unauthorized' in response.data


def test_ajax_request_unauthorized_returns_401(client):
    """
    Test that AJAX requests receive 401 with "Unauthorized" text when unauthorized.
    """
    # Make AJAX request to a protected endpoint without authentication
    response = client.get(
        '/jobs/assigned',
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )
    
    # Should get 401 Unauthorized with plain text response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data
    # Should not redirect (no Location header)
    assert 'Location' not in response.headers


def test_regular_browser_request_unauthorized_redirects_to_login(client):
    """
    Test that regular browser requests (page refreshes) redirect to login page when unauthorized.
    """
    # Make regular browser request to a protected endpoint without authentication
    response = client.get(
        '/jobs/assigned',
        follow_redirects=False
    )
    
    # Should get 302 redirect to login page
    assert response.status_code == 302
    assert 'Location' in response.headers
    assert '/users/login' in response.headers['Location']


def test_job_status_update_unauthorized_returns_401(client, create_job_and_property):
    """
    Test that job status update endpoints return 401 when unauthorized (for AJAX compatibility).
    """
    mock_job, mock_property = create_job_and_property
    
    # Make POST request to job status update without authentication
    response = client.post(
        f'/jobs/job/{mock_job.id}/update_status',
        data={'status': 'in progress'},
        follow_redirects=False
    )
    
    # Should get 401 Unauthorized with plain text response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data


def test_manage_jobs_unauthorized_redirects_to_login(client):
    """
    Test that owner-only endpoints redirect to login when accessed without authentication.
    """
    # Make request to manage jobs endpoint without authentication
    response = client.get(
        '/jobs/manage',
        follow_redirects=False
    )
    
    # Should get 302 redirect to login page
    assert response.status_code == 302
    assert 'Location' in response.headers
    assert '/users/login' in response.headers['Location']


def test_job_creation_form_unauthorized_returns_401_for_ajax(client):
    """
    Test that job creation form endpoint returns 401 for AJAX requests when unauthorized.
    """
    # Make AJAX request to job creation form without authentication
    response = client.get(
        '/jobs/job/create',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False
    )
    
    # Should get 401 Unauthorized with plain text response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data


def test_job_details_unauthorized_returns_401_for_ajax(client, create_job_and_property):
    """
    Test that job details endpoint returns 401 for AJAX requests when unauthorized.
    """
    mock_job, mock_property = create_job_and_property
    
    # Make AJAX request to job details without authentication
    response = client.get(
        f'/jobs/job/{mock_job.id}/details',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False
    )
    
    # Should get 401 Unauthorized with plain text response
    assert response.status_code == 401
    assert b'Unauthorized' in response.data


def test_authenticated_user_can_access_protected_endpoints(client, login_cleaner):
    """
    Test that authenticated users can successfully access protected endpoints.
    """
    cleaner_user = login_cleaner
    
    # Make request to cleaner jobs endpoint with authentication
    response = client.get(
        '/jobs/assigned',
        follow_redirects=False
    )
    
    # Should get 200 OK (successful access)
    assert response.status_code == 200
    # Should not redirect
    assert 'Location' not in response.headers


def test_mixed_request_types_handled_correctly(client):
    """
    Test that different request types are handled correctly in the same session.
    """
    # Test 1: Regular browser request should redirect
    response1 = client.get(
        '/jobs/assigned',
        follow_redirects=False
    )
    assert response1.status_code == 302
    
    # Test 2: HTMX request should return 401 with HX-Redirect
    response2 = client.get(
        '/jobs/assigned',
        headers={'HX-Request': 'true'},
        follow_redirects=False
    )
    assert response2.status_code == 401
    assert response2.headers.get('HX-Redirect') == '/users/login'
    
    # Test 3: AJAX request should return 401 with plain text
    response3 = client.get(
        '/jobs/assigned',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False
    )
    assert response3.status_code == 401
    assert b'Unauthorized' in response3.data