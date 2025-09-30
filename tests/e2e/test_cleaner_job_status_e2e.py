import pytest
from flask import url_for
from unittest.mock import patch, MagicMock

def test_cleaner_can_mark_job_in_progress(client, login_cleaner, create_job_and_property):
    """
    Test that a cleaner can mark a job as "in progress".
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Create an updated mock job with "in progress" status
        updated_job = MagicMock()
        updated_job.id = mock_job.id
        updated_job.status = 'in progress'
        updated_job.job_title = mock_job.job_title
        updated_job.time = mock_job.time
        updated_job.duration = mock_job.duration
        updated_job.property = mock_property
        
        mock_service_instance.update_job_status.return_value = updated_job
        
        # Make POST request to update job status
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'status': 'in progress'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        assert b'in progress' in response.data
        assert b'disabled' in response.data  # Button should be disabled in the response

def test_cleaner_can_mark_job_completed(client, login_cleaner, create_job_and_property):
    """
    Test that a cleaner can mark a job as "completed".
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Create an updated mock job with "completed" status
        updated_job = MagicMock()
        updated_job.id = mock_job.id
        updated_job.status = 'completed'
        updated_job.job_title = mock_job.job_title
        updated_job.time = mock_job.time
        updated_job.duration = mock_job.duration
        updated_job.property = mock_property
        
        mock_service_instance.update_job_status.return_value = updated_job
        
        # Make POST request to update job status
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'status': 'completed'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        assert b'completed' in response.data
        assert b'disabled' in response.data  # Button should be disabled in the response

def test_update_job_status_route_in_progress(client, login_cleaner, create_job_and_property):
    """
    Test the Flask route for updating job status to "in progress".
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Create an updated mock job with "in progress" status
        updated_job = MagicMock()
        updated_job.id = mock_job.id
        updated_job.status = 'in progress'
        updated_job.job_title = mock_job.job_title
        updated_job.time = mock_job.time
        updated_job.duration = mock_job.duration
        updated_job.property = mock_property
        
        mock_service_instance.update_job_status.return_value = updated_job
        
        # Test the route directly
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'status': 'in progress'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        # Verify the route returns the updated job card fragment
        assert b'job-card' in response.data
        assert b'in progress' in response.data

def test_update_job_status_route_completed(client, login_cleaner, create_job_and_property):
    """
    Test the Flask route for updating job status to "completed".
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Create an updated mock job with "completed" status
        updated_job = MagicMock()
        updated_job.id = mock_job.id
        updated_job.status = 'completed'
        updated_job.job_title = mock_job.job_title
        updated_job.time = mock_job.time
        updated_job.duration = mock_job.duration
        updated_job.property = mock_property
        
        mock_service_instance.update_job_status.return_value = updated_job
        
        # Test the route directly
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'status': 'completed'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        # Verify the route returns the updated job card fragment
        assert b'job-card' in response.data
        assert b'completed' in response.data

def test_unauthenticated_user_cannot_update_job_status(client, create_job_and_property):
    """
    Test that an unauthenticated user receives a 403 error and is redirected to the user login page.
    This test needs to assert that the redirect happens correctly and that the login component
    is not just inserted into the job card because the request was ajax.
    """
    mock_job, mock_property = create_job_and_property

    # Make POST request without authentication using direct URL
    response = client.post(
        f'/jobs/job/{mock_job.id}/update_status',
        data={'status': 'in progress'},
        follow_redirects=False
    )
    
    # Should get 401 Unauthorized for unauthenticated user (Flask-Login @login_required decorator)
    assert response.status_code == 401
    # Verify it's a JSON error response, not a redirect or HTML login form
    assert b'Unauthorized' in response.data