import pytest
from flask import url_for
from unittest.mock import patch, MagicMock

def test_cleaner_can_toggle_job_completion_status(client, login_cleaner, create_job_and_property):
    """
    Test that a cleaner can toggle a job's completion status.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_completion_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Test marking as completed
        updated_job_completed = MagicMock()
        updated_job_completed.id = mock_job.id
        updated_job_completed.is_complete = True
        updated_job_completed.job_title = mock_job.job_title
        updated_job_completed.time = mock_job.time
        updated_job_completed.duration = mock_job.duration
        updated_job_completed.property = mock_property
        
        mock_service_instance.update_job_completion_status.return_value = updated_job_completed
        
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'is_complete': 'True'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        assert b'Completed' in response.data
        assert b'job-status-' + str(mock_job.id).encode() in response.data
        mock_service_instance.update_job_completion_status.assert_called_with(mock_job.id, True)

        # Test marking as pending
        updated_job_pending = MagicMock()
        updated_job_pending.id = mock_job.id
        updated_job_pending.is_complete = False
        updated_job_pending.job_title = mock_job.job_title
        updated_job_pending.time = mock_job.time
        updated_job_pending.duration = mock_job.duration
        updated_job_pending.property = mock_property

        mock_service_instance.update_job_completion_status.return_value = updated_job_pending

        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'is_complete': 'False'},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b'Pending' in response.data
        assert b'job-status-' + str(mock_job.id).encode() in response.data
        mock_service_instance.update_job_completion_status.assert_called_with(mock_job.id, False)

def test_unauthenticated_user_cannot_update_job_status(client, create_job_and_property):
    """
    Test that an unauthenticated user receives a 401 error for unauthorized access.
    """
    mock_job, mock_property = create_job_and_property

    # Make POST request without authentication using direct URL
    response = client.post(
        f'/jobs/job/{mock_job.id}/update_status',
        data={'is_complete': 'True'},
        follow_redirects=False
    )
    
    # Should get 401 Unauthorized for unauthenticated user (Flask-Login @login_required decorator)
    assert response.status_code == 401
    # Verify it's a JSON error response
    assert b'Unauthorized' in response.data

def test_job_status_update_returns_status_and_actions_fragments(client, login_cleaner, create_job_and_property):
    """
    Test that updating job status returns both status and actions fragments
    to update both the status display and action buttons in the UI.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Mock the job service update_job_completion_status method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        
        # Create an updated mock job with "completed" status
        updated_job = MagicMock()
        updated_job.id = mock_job.id
        updated_job.is_complete = True
        updated_job.job_title = mock_job.job_title
        updated_job.time = mock_job.time
        updated_job.duration = mock_job.duration
        updated_job.property = mock_property
        
        mock_service_instance.update_job_completion_status.return_value = updated_job
        
        # Make POST request to update job status
        response = client.post(
            url_for('job.update_job_status', job_id=mock_job.id),
            data={'is_complete': 'True'},
            follow_redirects=False
        )
        
        assert response.status_code == 200
        
        # Verify that the response contains both status and actions fragments
        # The status fragment should contain the job status span with the correct ID
        assert b'job-status-' + str(mock_job.id).encode() in response.data
        assert b'Completed' in response.data
        
        # Verify that the response contains the actions fragment
        assert b'job-actions-' + str(mock_job.id).encode() in response.data
        assert b'Mark Pending' in response.data
        assert b'View Details' in response.data
        
        # Verify that the response does NOT contain the entire job card structure
        # This ensures we're not returning the full job_card.html
        assert b'job-card' not in response.data
        assert b'job_title' not in response.data
        assert b'Property Address' not in response.data
        
        # Verify the response contains both fragments with OOB swap attributes
        response_text = response.get_data(as_text=True)
        assert f'id="job-status-{mock_job.id}"' in response_text
        assert f'id="job-actions-{mock_job.id}"' in response_text
        assert 'hx-swap-oob="true"' in response_text

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
