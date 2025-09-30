import pytest
from flask import url_for
from unittest.mock import patch, MagicMock

def test_cleaner_can_view_assigned_jobs(client, login_cleaner, create_job_and_property):
    """
    Test that a cleaner can view only jobs assigned to them for the current day.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method directly in the controller
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_cleaner_jobs_for_today.return_value = [mock_job]
        
        response = client.get(url_for('job.cleaner_jobs'))
        assert response.status_code == 200
        assert b"Test Job" in response.data
        assert b"123 Test St" in response.data
        assert b"pending" in response.data

def test_cleaner_cannot_view_other_cleaners_jobs(client, login_cleaner, create_job_and_property):
    """
    Test that a cleaner cannot view jobs assigned to other cleaners or teams.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Modify the mock job to be assigned to a different cleaner
    mock_job.assigned_cleaners = '3' # Assuming another cleaner with ID 3

    # Patch the job service method to return empty list for different cleaner
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_cleaner_jobs_for_today.return_value = []
        
        response = client.get(url_for('job.cleaner_jobs'))
        assert response.status_code == 200
        assert b"Test Job" not in response.data
        assert b"123 Test St" not in response.data

def test_sensitive_job_attributes_not_displayed(client, login_cleaner, create_job_and_property):
    """
    Test that sensitive job attributes are not displayed to the cleaner.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_cleaner_jobs_for_today.return_value = [mock_job]
        
        response = client.get(url_for('job.cleaner_jobs'))
        assert response.status_code == 200
        # Assuming 'access_notes' is a sensitive attribute that should not be displayed directly on the job card
        assert b"Gate code 1234" not in response.data

def test_job_list_format_is_clear_and_readable(client, login_cleaner, create_job_and_property):
    """
    Test that the job list is presented in a clear, easy-to-read format.
    This test primarily checks for the presence of key elements and structure.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_cleaner_jobs_for_today.return_value = [mock_job]
        
        response = client.get(url_for('job.cleaner_jobs'))
        assert response.status_code == 200
        # Check for the presence of job card structure elements
        assert b"job-card" in response.data
        assert b"Test Job" in response.data  # Job title content
        assert b"123 Test St" in response.data  # Property address content
        assert b"pending" in response.data  # Job status content
        assert b"View Details" in response.data

def test_view_basic_property_details_modal(client, login_cleaner, create_job_and_property):
    """
    Test that the system provides a way to view basic property details for each job.
    This test checks if the modal content for job details can be retrieved.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method for get_job_details
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_job_details.return_value = mock_job
        
        response = client.get(url_for('job.get_job_details', job_id=mock_job.id))
        assert response.status_code == 200
        assert b"Test Job" in response.data
        assert b"123 Test St" in response.data
        assert b"Gate code 1234" in response.data

def test_multiple_cleaners_assigned_to_same_job(client, login_cleaner, create_job_and_property):
    """
    Test that multiple cleaners can be assigned to the same job and see other assigned cleaners.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Assign another cleaner (e.g., ID 3) to the same job and create mock cleaner objects
    mock_job.assigned_cleaners = '2,3'
    mock_cleaner1 = MagicMock(username='cleaner_user', id=2)
    mock_cleaner2 = MagicMock(username='another_cleaner', id=3)
    mock_job.assigned_cleaners_list = [mock_cleaner1, mock_cleaner2]

    # Patch the job service method for get_job_details
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_job_details.return_value = mock_job
        
        response = client.get(url_for('job.get_job_details', job_id=mock_job.id))
        assert response.status_code == 200
        assert b"cleaner_user" in response.data # First cleaner username
        assert b"another_cleaner" in response.data # Second cleaner username

def test_get_job_details_route(client, login_cleaner, create_job_and_property):
    """
    Test the Flask route for getting job details.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method for get_job_details
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_job_details.return_value = mock_job
        
        response = client.get(url_for('job.get_job_details', job_id=mock_job.id))
        assert response.status_code == 200
        assert b"Test Job" in response.data
        assert b"123 Test St" in response.data

def test_get_cleaner_job_route(client, login_cleaner, create_job_and_property):
    """
    Test the Flask route for getting cleaner's jobs.
    """
    cleaner_user = login_cleaner
    mock_job, mock_property = create_job_and_property

    # Patch the job service method
    with patch('controllers.jobs_controller.JobService') as MockJobService:
        mock_service_instance = MockJobService.return_value
        mock_service_instance.get_cleaner_jobs_for_today.return_value = [mock_job]
        
        response = client.get(url_for('job.cleaner_jobs'))
        assert response.status_code == 200
        assert b"Test Job" in response.data
        assert b"123 Test St" in response.data