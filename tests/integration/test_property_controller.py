
from datetime import datetime, date, timedelta

from bs4 import BeautifulSoup
import pytest

from utils.timezone import today_in_app_tz

@pytest.mark.usefixtures("admin_client_no_csrf", "job_service")
class TestJobListFiltering:

    @pytest.fixture(autouse=True)
    def _inject_fixtures(self, admin_client_no_csrf, job_service):
        self.client = admin_client_no_csrf
        self.job_service = job_service
    
    def apply_filters_and_test(self, property_id: int, start_date: date, end_date: date, show_completed: bool):
        url = (
            f'/address-book/property/{property_id}/jobs/filtered?'
            f'start_date={start_date.isoformat()}&end_date={end_date.isoformat()}'
        )

        if show_completed:
            url += f'&show_completed={str(show_completed).lower()}'
        response = self.client.get(url)

        soup = BeautifulSoup(response.text, "html.parser")        
        expected_jobs = self.job_service.get_filtered_jobs_by_property_id(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            show_completed=show_completed
        )
        expected_jobs = {job.id: job for job in expected_jobs}
        job_cards = soup.select(".job-card")
        assert len(job_cards) == len(expected_jobs), f"Expected {len(expected_jobs)} incomplete jobs: {expected_jobs.keys()}, got {len(job_cards)} {[job['data-job-id'] for job in job_cards]}"        
        # Check against the expected jobs
        for job_id, job in expected_jobs.items():
            job_card = soup.select_one(f"#job-{job_id}")
            assert job_card is not None, f"Expected job card with id job-{job_id} not found in the response"
            job_card_date = job_card.select_one(f"#job-date-{job_id}").text
            job_card_time = job_card.select_one(f"#job-time-{job_id}").text
            job_card_end_time = job_card.select_one(f"#job-end-time-{job_id}").text
            job_card_duration = job_card.select_one(f"#job-duration-{job_id}").text
            job_card_property = job_card.select_one(f"#job-property-address-{job_id}").text
            job_card_completed = 'completed' in job_card['class']
            assert job.display_date == job_card_date, f"Expected job date {job.display_date} but got {job_card_date} for job {job_id}"
            assert job.display_time == job_card_time, f"Expected job time {job.display_time} but got {job_card_time} for job {job_id}"
            assert job.display_end_time == job_card_end_time, f"Expected job end time {job.display_end_time} but got {job_card_end_time} for job {job_id}"
            assert job.duration == job_card_duration, f"Expected job duration {job.duration} but got {job_card_duration} for job {job_id}"
            assert job.property.address == job_card_property, f"Expected job property address {job.property.address} but got {job_card_property} for job {job_id}"
            assert job.is_complete == job_card_completed, f"Expected job completed status {job.is_complete} but got {job_card_completed} for job {job_id}"
            if not show_completed:
                assert job.is_complete is False, f"Job {job_id} should not be completed when show_completed=false"

    def test_job_filtering_for_property_hide_completed(self):
        """Test that the job filters for a property work correctly."""
        property_id = 1  # Assuming a property with ID 1 exists
        start_date = today_in_app_tz() - timedelta(days=30)
        end_date = today_in_app_tz()
        self.apply_filters_and_test(property_id, start_date, end_date, False)

    def test_job_filtering_for_property_show_completed(self):
        """Test that the job filters for a property work correctly when show_completed=true."""
        property_id = 1  # Assuming a property with ID 1 exists
        start_date = today_in_app_tz() - timedelta(days=30)
        end_date = today_in_app_tz()
        self.apply_filters_and_test(property_id, start_date, end_date, True)