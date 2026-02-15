from flask import request, render_template_string, session
from datetime import datetime, date
from config import DATETIME_FORMATS
from services.job_service import JobService
from services.assignment_service import AssignmentService
from flask_login import current_user
from services.team_service import TeamService
from .timezone import app_now, today_in_app_tz

INVALID_DATE_OR_TIME_FORMAT = 'Invalid date or time format: {}. Please use the datepicker for date and ' + DATETIME_FORMATS["TIME_FORMAT"].replace('%H', 'HH').replace('%M', 'MM') + ' format for time.'
INVALID_ARRIVAL_DATE_TIME_FORMAT = 'Invalid datetime format: {}. Please use the datetime picker.'
ARRIVAL_DATETIME_IN_PAST = 'Arrival date and time cannot be in the past.'
START_DATETIME_IN_PAST = 'Start date and time cannot be in the past.'
END_DATETIME_IN_PAST = 'End date and time cannot be in the past.'
NON_SEQUENTIAL_START_AND_END = 'Start date and time must be before end date and time.'
class JobHelper:
    def __init__(self, job_service: JobService, team_service: TeamService, assignment_service: AssignmentService):
        """
        Initialize JobHelper with injected service dependencies.
        
        Args:
            job_service: Service for job operations
            team_service: Service for team operations  
            assignment_service: Service for assignment operations
        """
        self.job_service = job_service
        self.team_service = team_service
        self.assignment_service = assignment_service

    def extract_job_form_data(self):
        """Extracts job-related data from the request form."""
        return {
            'property_id': request.form.get('property_id'),
            'date_str': request.form.get('date'),
            'start_time_str': request.form.get('start_time'),
            'arrival_datetime_str': request.form.get('arrival_datetime'),
            'end_time_str': request.form.get('end_time'),
            'assigned_cleaners': request.form.getlist('assigned_cleaners'),
            'assigned_teams': request.form.getlist('assigned_teams'),
            'job_type': request.form.get('job_type'),
            'notes': request.form.get('notes')
        }

    def validate_job_form_data(self, form_data):
        """Validates job form data and raises ValueError if invalid."""
        if not form_data['property_id']:
            raise ValueError('Property id is required.')
        if not form_data['date_str']:
            raise ValueError('Date is required.')
        if not form_data['start_time_str']:
            raise ValueError('Start time is required.')
        if not form_data['end_time_str']:
            raise ValueError('End time is required.')
        if len(form_data['assigned_teams']) == 0:
            raise ValueError('At least one team must be assigned to the job.')

    def parse_job_datetime(self, date_str, start_time_str, end_time_str, arrival_datetime_str):
        """Parses date and time strings into datetime objects."""
        job_arrival_datetime = None
        i = ''
        try:
            i = date_str
            job_date = datetime.strptime(date_str, DATETIME_FORMATS["DATE_FORMAT"]).date()
            i = start_time_str
            job_start_time = datetime.strptime(start_time_str, DATETIME_FORMATS["TIME_FORMAT"]).time()
            i = end_time_str
            job_end_time = datetime.strptime(end_time_str, DATETIME_FORMATS["TIME_FORMAT"]).time()
            job_start_datetime = datetime.combine(job_date, job_start_time, tzinfo=app_now().tzinfo)
            job_end_datetime = datetime.combine(job_date, job_end_time, tzinfo=app_now().tzinfo)
        except ValueError as e:
            raise ValueError(INVALID_DATE_OR_TIME_FORMAT.format(i)) from e

        if arrival_datetime_str:
            # Assuming arrival_datetime_str might come in ISO format or a specific DATETIME_FORMAT
            # Try ISO format first, then fall back to DATETIME_FORMAT if it exists
            try:
                job_arrival_datetime = datetime.fromisoformat(arrival_datetime_str)
                job_arrival_datetime = job_arrival_datetime.replace(tzinfo=app_now().tzinfo)
            except ValueError:
                try:
                    job_arrival_datetime = datetime.strptime(arrival_datetime_str, DATETIME_FORMATS["DATETIME_FORMAT"])
                    job_arrival_datetime = job_arrival_datetime.replace(tzinfo=app_now().tzinfo)
                except ValueError as e:
                    raise ValueError(INVALID_ARRIVAL_DATE_TIME_FORMAT.format(arrival_datetime_str)) from e
                
        if job_start_datetime and job_end_datetime and job_start_datetime >= job_end_datetime:
            raise ValueError(NON_SEQUENTIAL_START_AND_END)
        if job_start_datetime <= app_now().replace(hour=0, minute=0, second=0):
            raise ValueError(START_DATETIME_IN_PAST)
        if job_end_datetime <= app_now().replace(hour=0, minute=0, second=0):
            raise ValueError(END_DATETIME_IN_PAST)
    
        if job_arrival_datetime and job_arrival_datetime <= app_now().replace(hour=0, minute=0, second=0):
            raise ValueError(ARRIVAL_DATETIME_IN_PAST)
    
        return job_date, job_start_time, job_end_time, job_arrival_datetime

    def prepare_job_data(self, parsed_data, notes, job_type, property_id):
        """Prepares a dictionary of job data for service calls."""
        return {
            'date': parsed_data['job_date'],
            'start_time': parsed_data['job_start_time'],
            'arrival_datetime': parsed_data['job_arrival_datetime'],
            'end_time': parsed_data['job_end_time'],
            'description': notes,
            'job_type': job_type,
            'property_id': property_id
        }

    def render_response(self, errors):
        """Renders form errors using the _form_response.html template."""
        return render_template_string('{% include "_form_response.html" %}', errors=errors), 400

    def process_job_form(self):
        """
        Orchestrates the extraction, validation, and parsing of job form data.
        Returns a tuple: (job_data, assigned_teams, assigned_cleaners)
        If an error occurs, a ValueError will be raised.
        """
        form_data = self.extract_job_form_data()
        
        self.validate_job_form_data(form_data)

        job_date, job_start_time, job_end_time, job_arrival_datetime = self.parse_job_datetime(
            form_data['date_str'], form_data['start_time_str'], form_data['end_time_str'], form_data['arrival_datetime_str']
        )

        parsed_data = {
            'job_date': job_date,
            'job_start_time': job_start_time,
            'job_end_time': job_end_time,
            'job_arrival_datetime': job_arrival_datetime
        }

        job_data = self.prepare_job_data(
            parsed_data,
            form_data['notes'],
            form_data['job_type'],
            form_data['property_id']
        )
        
        return job_data, form_data['assigned_teams'], form_data['assigned_cleaners']

    def process_selected_date(self, date: str = None):
        """Chooses the right date value for the timetable views. If the given date is not none it will 
        return the given date otherwise it will use the date value stored in this session or else today's date.
        
        Returns date string"""
        if date: # Use given date if not none
            session['selected_date'] = date
        elif session.get('selected_date'): # Use session date if not none
            date = session['selected_date']
        else: # Else use today's date
            session['selected_date'] = today_in_app_tz().isoformat()
            date = session['selected_date']
        
        return date

    def render_job_details_fragment(self, job_id):
        """
        Fetches job details and renders the job details modal fragment.
        Returns the HTML for the job details modal.
        """
        job = self.job_service.get_job_details(job_id)
        return render_template_string('{% include "job_details_modal.html" %}', job=job, DATETIME_FORMATS=DATETIME_FORMATS)

    def render_job_list_fragment(self, current_user, date_str, **kwargs):
        """
        Fetches the list of jobs for the current user/team on a specific date and renders the job list fragment.
        Returns the HTML for the job list.
        """
        date_obj = datetime.strptime(date_str, DATETIME_FORMATS["DATE_FORMAT"]).date()
        assigned_jobs = self.job_service.get_jobs_for_user_on_date(current_user.id, current_user.team_id, date_obj)

        team_leader_id = None
        if current_user.team_id:
            current_user_team = self.team_service.get_team(current_user.team_id)
            if current_user_team:
                team_leader_id = current_user_team.team_leader_id

        return render_template_string('{% include "job_list_fragment.html" %}', jobs=assigned_jobs,
                                      DATETIME_FORMATS=DATETIME_FORMATS, view_type='normal', 
                                      current_user=current_user, team_leader_id=team_leader_id, **kwargs)

    def render_teams_timetable_fragment(self, current_user, date_str, **kwargs):
        """
        Fetches the table of jobs categorized by their team assignments for a specific date.
        Returns the HTML of the Teams Timetable.
        """
        date_obj = datetime.strptime(date_str, DATETIME_FORMATS["DATE_FORMAT"]).date()
        all_teams = self.team_service.get_all_teams()
        jobs_by_team = self.job_service.get_jobs_grouped_by_team_for_date(date_obj)
        
        team_leader_id = None
        if current_user.team_id:
            current_user_team = self.team_service.get_team(current_user.team_id)
            if current_user_team:
                team_leader_id = current_user_team.team_leader_id

        # Render the entire team timetable view to ensure all columns are updated correctly
        # This will trigger the jobAssignmentsUpdated event in the frontend
        response_html = render_template_string(
            '{% include "team_timetable_fragment.html" %}',
            all_teams=all_teams,
            jobs_by_team=jobs_by_team,
            DATETIME_FORMATS=DATETIME_FORMATS,
            current_user=current_user,
            view_type='team',
            user_id=current_user.id,
            team_leader_id=team_leader_id,
            **kwargs
        )
        return response_html

    def render_job_updates(self, job_id, current_user, selected_date_for_fetch):
        """
        Fetches updated job details and renders the job details and job list fragments.
        Returns a tuple: (job_details_html, job_list_html)
        """
        job_details_html = self.render_job_details_fragment(job_id)
        job_list_html = self.render_job_list_fragment(current_user, selected_date_for_fetch)
        return job_details_html, job_list_html