from datetime import datetime, time
from playwright.sync_api import expect
import pytest

from config import DATETIME_FORMATS
from services.job_service import JobService
from tests.db_helpers import get_db_session
from utils.timezone import get_app_timezone

@pytest.mark.usefixtures("anytown_property")
class JobListHelper:

    @pytest.fixture(autouse=True)
    def _inject_fixtures(self, anytown_property):
        self.property_id = anytown_property.id

    def __init__(self, page):
        self.page = page

    @property
    def start_datetime(self):
        if hasattr(self, "_start_datetime"):
            return self._start_datetime
        else:
            self._extract_filter_datetimes()
            return self._start_datetime

    @property
    def end_datetime(self):
        if hasattr(self, "_end_datetime"):
            return self._end_datetime
        else:
            self._extract_filter_datetimes()
            return self._end_datetime
    
    def _extract_filter_datetimes(self):
        """Helper to extract the start and end datetimes from the job list filter inputs and store them as instance variables"""
        hidden_start_date_locator, hidden_end_date_locator = self.get_filter_hidden_date_locators()
        start_date = self.convert_date_locator_to_datetime(hidden_start_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
        end_date = self.convert_date_locator_to_datetime(hidden_end_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
        start_date = start_date.replace(tzinfo=get_app_timezone())
        end_date = end_date.replace(tzinfo=get_app_timezone())
        start_date = datetime.combine(start_date, time.min)
        end_date = datetime.combine(end_date, time.max.replace(microsecond=0))
        self._start_datetime = start_date
        self._end_datetime = end_date

    def tick_show_completed_checkbox(self, disable=False) -> None:
        """Helper to tick the 'Show Completed' checkbox in the job list modal. If disable is true it will disable the filter option."""
        job_list = self.page.locator("#date-filter-container")
        show_completed_checkbox = job_list.locator("#show-completed")
        if not show_completed_checkbox.is_checked() and not disable:
            show_completed_checkbox.check()
        if show_completed_checkbox.is_checked() and disable:
            show_completed_checkbox.uncheck()

    def set_filter_start_date(self, start_datetime: datetime) -> None:
        """Helper to set the start date in the job list filter. Expects date_str in ISO format YYYY-MM-DD"""
        self._start_datetime = start_datetime
        start_date_display, _ = self.get_filter_display_date_locators()
        start_date_hidden, _ = self.get_filter_hidden_date_locators()    
        date_str = start_datetime.date().isoformat()
        formatted_date = start_datetime.strftime(DATETIME_FORMATS['DATE_FORMAT'])
        start_date_display.fill(formatted_date)
        start_date_hidden.fill(date_str)
        # Trigger change event to update hidden input
        start_date_display.dispatch_event("change")
        # Wait for hidden input to update
        expect(start_date_hidden).to_have_value(date_str)

    def set_filter_end_date(self, end_datetime: datetime) -> None:
        """Helper to set the end date in the job list filter. Expects date_str in ISO format YYYY-MM-DD"""
        self._end_datetime = end_datetime
        _, end_date_display = self.get_filter_display_date_locators()
        _, end_date_hidden = self.get_filter_hidden_date_locators()
        date_str = end_datetime.date().isoformat()
        formatted_date = end_datetime.strftime(DATETIME_FORMATS['DATE_FORMAT'])                                 
        end_date_display.fill(formatted_date)
        end_date_hidden.fill(date_str)
        # Trigger change event to update hidden input
        end_date_display.dispatch_event("change")
        # Wait for hidden input to update
        expect(end_date_hidden).to_have_value(date_str)

    def get_filter_display_date_locators(self):
        """Helper to get the display date locators from the job list modal"""
        job_list = self.page.locator("#date-filter-container")
        display_start_date_locator = job_list.locator("#start-date-display")
        display_end_date_locator = job_list.locator("#end-date-display")
        return display_start_date_locator, display_end_date_locator

    def get_filter_hidden_date_locators(self):
        """Helper to get the hidden date locators from the job list modal"""
        job_list = self.page.locator("#date-filter-container")
        hidden_start_date_locator = job_list.locator("#start-date")
        hidden_end_date_locator = job_list.locator("#end-date")
        hidden_start_date_locator.wait_for(state="visible")
        hidden_end_date_locator.wait_for(state="visible")
        return hidden_start_date_locator, hidden_end_date_locator

    def assert_filtered_job_list_date_formats(self) -> None:
        """Validate that the date pickers in the filtered job list modal have correct formats"""
        display_start_date_locator, display_end_date_locator = self.get_filter_display_date_locators()
        hidden_start_date_locator, hidden_end_date_locator = self.get_filter_hidden_date_locators()
        self.assert_date_picker_formats(DATETIME_FORMATS['DATE_FORMAT'], display_start_date_locator, hidden_start_date_locator)  
        self.assert_date_picker_formats(DATETIME_FORMATS['DATE_FORMAT'], display_end_date_locator, hidden_end_date_locator)

    def  convert_date_locator_to_datetime(self, date_locator, date_format: str) -> datetime.date:
        """Convert a date locator's hidden input value to a date object"""
        date_str = date_locator.input_value()
        return datetime.strptime(date_str, date_format)

    def validate_filtered_jobs(self) -> None:
        """Helper to validate that jobs in the job list fall within the specified date range"""
        job_list = self.page.locator("#job-list")
        filters_container = self.page.locator("#date-filter-container")
        # Convert dates to datetime objects
        start_date = self.start_datetime
        end_date = self.end_datetime
        start_date = start_date.replace(tzinfo=get_app_timezone())
        end_date = end_date.replace(tzinfo=get_app_timezone())
        # Extract checkbox filter values
        show_completed = filters_container.locator("#show-completed").is_checked()
        db = get_db_session()
        job_service = JobService(db)
        expected_jobs = job_service.get_filtered_jobs_by_property_id(
            property_id=self.property_id,
            start_date=start_date,
            end_date=end_date,
            show_completed=show_completed
        )
        filtered_jobs_locators = job_list.locator(".job-card").all()
        rendered_job_ids = [int(job.get_attribute("data-job-id")) for job in filtered_jobs_locators]
        expected_job_ids = [job.id for job in expected_jobs]
        # Compare the number of jobs displayed to the number returned from the service
        assert len(filtered_jobs_locators) == len(expected_jobs), f"Expected {len(expected_jobs)} jobs but found {len(filtered_jobs_locators)} displayed \
            with filters: start_date={start_date}, end_date={end_date}, show_completed={show_completed}, property_id={self.property_id} \
            Expected job ids: {expected_job_ids}, Rendered job ids: {rendered_job_ids}" 
        # Iterate through displayed jobs and compare with expected jobs from service
        for i in range(len(filtered_jobs_locators)):
            job_locator = filtered_jobs_locators[i]
            job_id = int(job_locator.get_attribute("data-job-id"))
            # Compare with expected jobs from service
            assert job_id == expected_jobs[i].id, f"Expected job with id {expected_jobs[i].id} but found job with id {job_id} at position {i}"
            # Check that the job date is within the given range
            job_date = expected_jobs[i].display_datetime
            assert start_date <= job_date <= end_date, f"Job date {job_date} is outside of filter range {start_date} to {end_date}, job_id={job_id}, property_id={self.property_id}"
            if not show_completed:
                assert not expected_jobs[i].is_complete, f"Job with id {expected_jobs[i].id} is completed but show_completed is False. \
            Filters: start_date={start_date}, end_date={end_date}, show_completed={show_completed}"
        return expected_jobs, filtered_jobs_locators

    def validate_job_list_date_dividers(self) -> None:
        """Validate that the date dividers in the job list fall within the specified date range"""
        job_list = self.page.locator("#job-list")
        hidden_start_date_locator, hidden_end_date_locator = self.get_filter_hidden_date_locators()
        start_date = self.convert_date_locator_to_datetime(hidden_start_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
        end_date = self.convert_date_locator_to_datetime(hidden_end_date_locator, DATETIME_FORMATS['ISO_DATE_FORMAT'])
        # Get all date dividers in the job list
        date_dividers = job_list.locator(".date-divider")
        assert date_dividers.count() > 0, "Expected at least one date divider in the job list but found none"
        # Check that the job divider dates are within the given date range    
        for i in range(date_dividers.count()):
            divider_text = date_dividers.nth(i).text_content().strip().replace("\n", "")
            divider_date = datetime.strptime(divider_text, DATETIME_FORMATS['FULL_MONTH_DATE_FORMAT'])
            if not (start_date <= divider_date <= end_date):
                raise AssertionError(f"Date divider '{divider_text}' is outside of filter range {start_date} to {end_date}")
        return True

    def assert_date_picker_formats(self, expected_format: str, display_input, hidden_input) -> None:
        """Helper to assert that date formats in date picker inputs match expected format"""
        # Get values from inputs    
        internal_date = hidden_input.input_value()
        displayed_date = display_input.input_value()
        # Check that the internal value is in ISO format
        assert self.validate_iso_date_format(internal_date), f"Internal date value '{internal_date}' is not in ISO format"
        # Check that the displayed text matches expected format
        assert self.validate_date_format(displayed_date, expected_format), f"Displayed date '{displayed_date}' does not match format '{expected_format}'"  

    def validate_iso_date_format(self, date_string: str) -> bool:
        """Check if a date string is in ISO format YYYY-MM-DD"""
        try:
            datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False
        
    def validate_date_format(self, date_string, date_format):
        try:
            datetime.strptime(date_string, date_format)
            return True
        except ValueError:
            return False

    def get_property_card_by_id(self, property_id):
        """Helper to get a property card locator by property id"""
        return self.page.locator(f'#property-card-{property_id}')
    
    def open_property_jobs(self, property_id):
        """Helper to open the job list modal for a given property id"""
        self.property_id = property_id
        # Get first property card
        property_card = self.get_property_card_by_id(property_id)
        expect(property_card).to_be_visible()
        
        # Open jobs list modal
        property_card.locator(".view-jobs-button").wait_for(state="attached")
        property_id = property_card.get_attribute("data-id")
        with self.page.expect_response(f"**/property/{property_id}/jobs**"):
            self.page.wait_for_load_state('networkidle')
            property_card.locator(".view-jobs-button").click()

        self.page.wait_for_load_state('networkidle')    
        expect(self.page.locator("#property-modal")).to_be_visible()

        # Verify the contents of the date pickers are formatted correctly 
        self.assert_filtered_job_list_date_formats()
        self._extract_filter_datetimes()  # Store the filter datetimes as instance variables for later validation
        # Validate that the jobs displayed match the filter criteria
        self.validate_job_list_date_dividers()
        self.validate_filtered_jobs()
        
        return self.page.locator("#property-modal")
    
    def apply_filters(self, start_date: datetime.date = None, end_date: datetime.date = None, show_completed: bool = True) -> None:
        """Helper to apply filters in the job list modal and validate results"""
        
        if start_date:
            self.set_filter_start_date(start_date)
        if end_date:
            self.set_filter_end_date(end_date)
        
        self.tick_show_completed_checkbox(disable=not show_completed)

        self.page.locator("#date-filter-container").locator(".filter-actions button.btn-primary").click()
        expected_jobs, _ = self.validate_filtered_jobs()
        if len(expected_jobs) > 0:
            self.validate_job_list_date_dividers()