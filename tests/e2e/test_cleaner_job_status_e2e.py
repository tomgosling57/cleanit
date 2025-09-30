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
        # Now returns only status fragment, not the full job card with buttons
        assert b'job-status-' + str(mock_job.id).encode() in response.data

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
        # Now returns only status fragment, not the full job card with buttons
        assert b'job-status-' + str(mock_job.id).encode() in response.data

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
        # Verify the route returns the updated status fragment (not the full job card)
        assert b'job-status-' + str(mock_job.id).encode() in response.data
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
        # Verify the route returns the updated status fragment (not the full job card)
        assert b'job-status-' + str(mock_job.id).encode() in response.data
        assert b'completed' in response.data

def test_unauthenticated_user_cannot_update_job_status(client, create_job_and_property):
    """
    Test that an unauthenticated user receives a 401 error for unauthorized access.
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
    # Verify it's a JSON error response
    assert b'Unauthorized' in response.data

def test_job_status_update_returns_only_status_fragment(client, login_cleaner, create_job_and_property):
    """
    Test that updating job status returns only the status fragment (not the entire job card)
    to prevent duplication bugs when updating newly created jobs.
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
        
        # Verify that the response contains only the status fragment, not the entire job card
        # The status fragment should contain the job status span with the correct ID
        assert b'job-status-' + str(mock_job.id).encode() in response.data
        assert b'in progress' in response.data
        
        # Verify that the response does NOT contain the entire job card structure
        # This ensures we're not returning the full job_card_fragment.html
        assert b'job-card' not in response.data
        assert b'job-actions' not in response.data
        assert b'Mark In Progress' not in response.data
        assert b'Mark Completed' not in response.data
        assert b'View Details' not in response.data
        
        # Verify the response is specifically the job_status_fragment.html content
        # which should be just a span element with the status
        response_text = response.get_data(as_text=True)
        assert response_text.strip().startswith('<span')
        assert response_text.strip().endswith('</span>')
        assert f'id="job-status-{mock_job.id}"' in response_text