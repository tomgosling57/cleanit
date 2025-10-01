import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
from datetime import date, time

def test_owner_can_see_create_job_button(client, login_owner):
    """
    Test that the owner can see the 'Create Job' button or plus icon on the timetable view.
    """
    # Mock the job service to return jobs for the manage endpoint
    with patch('services.job_service.JobService.get_all_jobs') as mock_get_jobs:
        with patch('services.user_service.UserService.get_users_by_role') as mock_get_cleaners:
            mock_job = MagicMock()
            mock_job.id = 1
            mock_job.job_title = 'Test Job'
            mock_get_jobs.return_value = [mock_job]
            
            mock_cleaner = MagicMock()
            mock_cleaner.id = 1
            mock_cleaner.username = 'test_cleaner'
            mock_get_cleaners.return_value = [mock_cleaner]
            
            # Access the manage jobs page as an owner (this is where owners see the create button)
            response = client.get('/jobs/manage')
            
            # Check that the response is successful
            assert response.status_code == 200
            
            # Check that the Create Job button is present in the HTML
            assert b'Create Job' in response.data
            assert b'hx-get="/jobs/job/create"' in response.data

def test_owner_can_open_blank_job_creation_modal(client, login_owner):
    """
    Test that clicking the 'Create Job' button displays a blank, editable job modal pop-up.
    """
    # Mock the job service to return a list of cleaners
    with patch('services.user_service.UserService.get_users_by_role') as mock_get_cleaners:
        mock_cleaner = MagicMock()
        mock_cleaner.id = 1
        mock_cleaner.username = 'test_cleaner'
        mock_get_cleaners.return_value = [mock_cleaner]
        
        # Make a GET request to the job creation form endpoint
        response = client.get('/jobs/job/create')
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Check that the job creation form is returned
        assert b'Create New Job' in response.data
        assert b'job-creation-form' in response.data
        assert b'test_cleaner' in response.data  # Cleaner should be in the dropdown

def test_owner_can_submit_new_job_form(client, login_owner):
    """
    Test that the owner can submit a new job form and it is saved to the database.
    """
    # Mock the job service methods
    with patch('services.job_service.JobService.get_property_by_address') as mock_get_property:
        with patch('services.job_service.JobService.create_property') as mock_create_property:
            with patch('services.job_service.JobService.create_job') as mock_create_job:
                
                # Mock property and job creation
                mock_property = MagicMock()
                mock_property.id = 1
                mock_get_property.return_value = None  # Property doesn't exist yet
                mock_create_property.return_value = mock_property
                
                mock_job = MagicMock()
                mock_job.id = 1
                mock_job.job_title = 'Test Cleaning Job'
                mock_create_job.return_value = mock_job
                
                # Submit job creation form data
                job_data = {
                    'job_title': 'Test Cleaning Job',
                    'property_address': '123 Test Street',
                    'date': '2024-01-01',
                    'time': '09:00',
                    'duration': '2.5',
                    'assigned_cleaner_id': '1',
                    'job_type': 'standard',
                    'notes': 'Test notes'
                }
                
                response = client.post('/jobs/job/create', data=job_data)
                
                # Check that the response is successful
                assert response.status_code == 200
                
                # Verify that the job creation was called with correct data
                mock_create_job.assert_called_once()
                call_args = mock_create_job.call_args[0][0]
                assert call_args['job_title'] == 'Test Cleaning Job'
                assert call_args['property_id'] == 1
                assert call_args['is_complete'] == False

def test_newly_created_job_is_immediately_visible_on_timetable(client, login_owner):
    """
    Test that the newly created job is immediately visible on the timetable view without a full page reload.
    """
    # Mock the job service methods
    with patch('services.job_service.JobService.get_property_by_address') as mock_get_property:
        with patch('services.job_service.JobService.create_property') as mock_create_property:
            with patch('services.job_service.JobService.create_job') as mock_create_job:
                
                # Mock property and job creation
                mock_property = MagicMock()
                mock_property.id = 1
                mock_get_property.return_value = None
                mock_create_property.return_value = mock_property
                
                mock_job = MagicMock()
                mock_job.id = 1
                mock_job.job_title = 'Test Cleaning Job'
                mock_job.date = date(2024, 1, 1)
                mock_job.time = time(9, 0)
                mock_job.duration = 2.5
                mock_job.description = 'Test notes'
                mock_job.assigned_cleaners = '1'
                mock_job.job_type = 'standard'
                mock_job.property = mock_property
                mock_create_job.return_value = mock_job
                
                # Submit job creation form data
                job_data = {
                    'job_title': 'Test Cleaning Job',
                    'property_address': '123 Test Street',
                    'date': '2024-01-01',
                    'time': '09:00',
                    'duration': '2.5',
                    'assigned_cleaner_id': '1',
                    'job_type': 'standard',
                    'notes': 'Test notes'
                }
                
                response = client.post('/jobs/job/create', data=job_data)
                
                # Check that the response is successful and contains the job card HTML
                assert response.status_code == 200
                # The response should contain job card HTML that would be inserted into the timetable
                assert b'job-card' in response.data or b'Test Cleaning Job' in response.data

def test_non_owner_cannot_access_create_job_feature(client, login_cleaner):
    """
    Test that users without the 'owner' role cannot access the create job feature.
    """
    # Try to access the job creation form as a cleaner
    response = client.get('/jobs/job/create')
    
    # Check that access is denied
    assert response.status_code == 403
    assert b'Unauthorized' in response.data
    
    # Try to submit a job creation form as a cleaner
    job_data = {
        'job_title': 'Test Cleaning Job',
        'property_address': '123 Test Street',
        'date': '2024-01-01',
        'time': '09:00',
        'duration': '2.5',
        'assigned_cleaner_id': '1',
        'job_type': 'standard',
        'notes': 'Test notes'
    }
    
    response = client.post('/jobs/job/create', data=job_data)
    
    # Check that access is denied
    assert response.status_code in [403, 302]  # Either direct 403 or redirect to index

def test_unauthenticated_user_cannot_access_create_job_feature(client):
    """
    Test that an unauthenticated user cannot access the create job feature.
    """
    # Try to access the job creation form without authentication
    response = client.get('/jobs/job/create', follow_redirects=False)
    
    # Check that user is redirected to login or gets unauthorized
    assert response.status_code in [302, 401, 403]  # Redirect to login or unauthorized
    
    # Try to submit a job creation form without authentication
    job_data = {
        'job_title': 'Test Cleaning Job',
        'property_address': '123 Test Street',
        'date': '2024-01-01',
        'time': '09:00',
        'duration': '2.5',
        'assigned_cleaner_id': '1',
        'job_type': 'standard',
        'notes': 'Test notes'
    }
    
    response = client.post('/jobs/job/create', data=job_data, follow_redirects=False)
    
    # Check that access is denied
    assert response.status_code in [302, 401, 403]  # Redirect to login or unauthorized