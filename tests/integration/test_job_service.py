
from datetime import datetime


class TestJobServiceTimezoneHandling:
    
    def test_create_job_with_timezone(self, job_service):
        # Create a job with a specific date and time in the app's timezone
        job_data = {
            'date': '2024-07-01',
            'time': '14:00',
            'end_time': '16:00',
            'arrival_datetime': '2024-07-01 13:30',
            'property_id': 1, 
            'description': 'Test job with timezone'
        }
        new_job = job_service.create_job(job_data)
        
        # Verify that the job was created with the correct date and time in UTC
        assert new_job is not None
        assert new_job.date == datetime.fromisoformat(job_data['date']).date()  # Date should be stored as is
        assert new_job.time == datetime.strptime(job_data['time'], '%H:%M').time()  # Time should be stored as is                                
        assert new_job.end_time == datetime.strptime(job_data['end_time'], '%H:%M').time()  # End time should be stored as is
        assert new_job.arrival_datetime == datetime.fromisoformat(job_data['arrival_datetime'])  # Arrival datetime should be stored as is

    def test_update_job_with_timezone(self, job_service):
        # Update a job with a specific date and time in the app's timezone
        job_id = 1  # Assuming a job with ID 1 exists
        job_data = {
            'date': '2024-07-02',
            'time': '15:00',
            'end_time': '17:00',
            'arrival_datetime': '2024-07-02 14:30',
            'description': 'Updated job with timezone'
        }
        updated_job = job_service.update_job(job_id, job_data)
        # Verify that the job was updated with the correct date and time in UTC
        assert updated_job is not None
        assert updated_job.date == datetime.fromisoformat(job_data['date']).date()  # Date should be updated as is
        assert updated_job.time == datetime.strptime(job_data['time'], '%H:%M').time()  # Time should be updated as is
        assert updated_job.end_time == datetime.strptime(job_data['end_time'], '%H:%M').time()  # End time should be updated as is
        assert updated_job.arrival_datetime == datetime.fromisoformat(job_data['arrival_datetime'])  # Arrival datetime should be updated as is
        