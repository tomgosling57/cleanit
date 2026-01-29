from flask import request, render_template_string, session
from datetime import datetime, date
from config import DATETIME_FORMATS
from services.job_service import JobService
from services.assignment_service import AssignmentService
from flask_login import current_user
from services.team_service import TeamService
from .timezone import today_in_app_tz


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
            'time_str': request.form.get('time'),
            'arrival_datetime_str': request.form.get('arrival_datetime'),
            'end_time_str': request.form.get('end_time'),
            'assigned_cleaners': request.form.getlist('assigned_cleaners'),
            'assigned_teams': request.form.getlist('assigned_teams'),
            'job_type': request.form.get('job_type'),
            'notes': request.form.get('notes')
        }

    def validate_job_form_data(self, form_data):
        """Validates job form data and returns an errors dictionary."""
        errors = {}
        if not form_data['property_id']:
            errors['property_address'] = 'Property address is required.'
        if not form_data['date_str']:
            errors['date'] = 'Date is required.'
        if not form_data['time_str']:
            errors['time'] = 'Start time is required.'
        if not form_data['end_time_str']:
            errors['end_time'] = 'End time is required.'
        return errors

    def parse_job_datetime(self, date_str, time_str, end_time_str, arrival_datetime_str):
        """Parses date and time strings into datetime objects."""
        errors = {}
        job_date = None
        job_time = None
        job_end_time = None
        job_arrival_datetime = None

        try:
            job_date = datetime.strptime(date_str, DATETIME_FORMATS["DATE_FORMAT"]).date()
            job_time = datetime.strptime(time_str, DATETIME_FORMATS["TIME_FORMAT"]).time()
            job_end_time = datetime.strptime(end_time_str, DATETIME_FORMATS["TIME_FORMAT"]).time()

            if job_time and job_end_time and job_time >= job_end_time:
                errors['time'] = 'Start time must be before end time.'

            if arrival_datetime_str:
                # Assuming arrival_datetime_str might come in ISO format or a specific DATETIME_FORMAT
                # Try ISO format first, then fall back to DATETIME_FORMAT if it exists
                try:
                    job_arrival_datetime = datetime.fromisoformat(arrival_datetime_str)
                except ValueError:
                    if "DATETIME_FORMAT" in DATETIME_FORMATS:
                        job_arrival_datetime = datetime.strptime(arrival_datetime_str, DATETIME_FORMATS["DATETIME_FORMAT"])
                    else:
                        errors['arrival_datetime'] = 'Invalid arrival date/time format.'

        except ValueError:
            errors['date_time_format'] = 'Invalid date or time format.'
        
        return job_date, job_time, job_end_time, job_arrival_datetime, errors

    def prepare_job_data(self, parsed_data, notes, job_type, property_id):
        """Prepares a dictionary of job data for service calls."""
        return {
            'date': parsed_data['job_date'],
            'time': parsed_data['job_time'],
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
        Returns a tuple: (job_data, assigned_teams, assigned_cleaners, error_response)
        If an error occurs, job_data, assigned_teams, assigned_cleaners will be None,
        and error_response will contain the Flask response.
        """
        form_data = self.extract_job_form_data()
        
        errors = self.validate_job_form_data(form_data)
        if errors:
            return None, None, None, self.render_response(errors)

        job_date, job_time, job_end_time, job_arrival_datetime, datetime_response = self.parse_job_datetime(
            form_data['date_str'], form_data['time_str'], form_data['end_time_str'], form_data['arrival_datetime_str']
        )

        if datetime_response:
            return None, None, None, self.render_response(datetime_response)

        parsed_data = {
            'job_date': job_date,
            'job_time': job_time,
            'job_end_time': job_end_time,
            'job_arrival_datetime': job_arrival_datetime
        }

        job_data = self.prepare_job_data(
            parsed_data,
            form_data['notes'],
            form_data['job_type'],
            form_data['property_id']
        )
        
        return job_data, form_data['assigned_teams'], form_data['assigned_cleaners'], None

    def process_selected_date(self, date: str = None):
        """Chooses the right date value for the timetable views. If the given date is not none it will 
        return the given date otherwise it will use the date value stored in this session or else today's date.
        
        Returns date string"""
        if date: # Use given date if not none
            session['selected_date'] = date
        elif session.get('selected_date'): # Use session date if not none
            date = session['selected_date']
        else: # Else use today's date
            session['selected_date'] = today_in_app_tz().strftime(DATETIME_FORMATS["DATE_FORMAT"])
            date = session['selected_date']
        
        return date

    def render_job_details_fragment(self, job_id):
        """
        Fetches job details and renders the job details modal fragment.
        Returns the HTML for the job details modal.
        """
        job = self.job_service.get_job_details(job_id)
        return render_template_string('{% include "job_details_modal.html" %}', job=job, DATETIME_FORMATS=DATETIME_FORMATS)

    def render_job_list_fragment(self, current_user, date_str):
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

        return render_template_string('{% include "job_list_fragment.html" %}', jobs=assigned_jobs, DATETIME_FORMATS=DATETIME_FORMATS, view_type='normal', current_user=current_user, team_leader_id=team_leader_id)

    def render_teams_timetable_fragment(self, current_user, date_str):
        """
        Fetches the table of jobs categorized by their team assignments for a specific date.
        Returns the HTML of the Teams Timetable.
        """
        date_obj = datetime.strptime(date_str, DATETIME_FORMATS["DATE_FORMAT"]).date()
        all_teams = self.team_service.get_all_teams()
        jobs_by_team = self.assignment_service.get_jobs_grouped_by_team_for_date(date_obj)
        
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
            team_leader_id=team_leader_id
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