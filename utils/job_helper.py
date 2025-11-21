from flask import request, render_template_string, session
from datetime import datetime, date
from config import DATETIME_FORMATS, BACK_TO_BACK_THRESHOLD
from services.job_service import JobService
from services.assignment_service import AssignmentService
from flask_login import current_user

from services.team_service import TeamService

class JobHelper:
    @staticmethod
    def extract_job_form_data():
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

    @staticmethod
    def validate_job_form_data(form_data):
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

    @staticmethod
    def parse_job_datetime(date_str, time_str, end_time_str, arrival_datetime_str):
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

    @staticmethod
    def prepare_job_data(parsed_data, notes, job_type, property_id):
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

    @staticmethod
    def render_form_errors(errors):
        """Renders form errors using the _form_errors.html template."""
        return render_template_string('{% include "_form_errors.html" %}', errors=errors), 400

    @staticmethod
    def process_job_form():
        """
        Orchestrates the extraction, validation, and parsing of job form data.
        Returns a tuple: (job_data, assigned_teams, assigned_cleaners, error_response)
        If an error occurs, job_data, assigned_teams, assigned_cleaners will be None,
        and error_response will contain the Flask response.
        """
        form_data = JobHelper.extract_job_form_data()
        
        errors = JobHelper.validate_job_form_data(form_data)
        if errors:
            return None, None, None, JobHelper.render_form_errors(errors)

        job_date, job_time, job_end_time, job_arrival_datetime, datetime_errors = JobHelper.parse_job_datetime(
            form_data['date_str'], form_data['time_str'], form_data['end_time_str'], form_data['arrival_datetime_str']
        )

        if datetime_errors:
            return None, None, None, JobHelper.render_form_errors(datetime_errors)

        parsed_data = {
            'job_date': job_date,
            'job_time': job_time,
            'job_end_time': job_end_time,
            'job_arrival_datetime': job_arrival_datetime
        }

        job_data = JobHelper.prepare_job_data(
            parsed_data,
            form_data['notes'],
            form_data['job_type'],
            form_data['property_id']
        )
        
        return job_data, form_data['assigned_teams'], form_data['assigned_cleaners'], None

    @staticmethod
    def get_selected_date_from_session():
        """
        Retrieves the selected date from the session and ensures it's a datetime.date object.
        Falls back to today's date if not found or invalid.
        """
        selected_date_from_session = session.get('selected_date')
        if isinstance(selected_date_from_session, str):
            try:
                return datetime.strptime(selected_date_from_session, DATETIME_FORMATS["DATE_FORMAT"]).date()
            except ValueError:
                return datetime.today().date() # Fallback to today if format is invalid
        elif isinstance(selected_date_from_session, date):
            return selected_date_from_session
        return datetime.today().date() # Fallback to today if not a date object

    @staticmethod
    def render_job_details_fragment(db, job_id):
        """
        Fetches job details and renders the job details modal fragment.
        Returns the HTML for the job details modal.
        """
        job_service = JobService(db)
        job = job_service.get_job_details(job_id)
        return render_template_string('{% include "job_details_modal.html" %}', job=job, DATETIME_FORMATS=DATETIME_FORMATS)

    @staticmethod
    def render_job_list_fragment(db, current_user, selected_date_for_fetch):
        """
        Fetches the list of jobs for the current user/team on a specific date and renders the job list fragment.
        Returns the HTML for the job list.
        """
        job_service = JobService(db)
        assigned_jobs = job_service.get_jobs_for_user_on_date(current_user.id, current_user.team_id, selected_date_for_fetch)
        back_to_back_job_ids = job_service.get_back_to_back_jobs_for_date(selected_date_for_fetch, threshold_minutes=BACK_TO_BACK_THRESHOLD)
        return render_template_string('{% include "job_list_fragment.html" %}', jobs=assigned_jobs, DATETIME_FORMATS=DATETIME_FORMATS, back_to_back_job_ids=back_to_back_job_ids, view_type='normal', current_user=current_user)

    @staticmethod
    def render_teams_timetable_fragment(db, current_user, selected_date_for_fetch):
        """
        Fetches the table of jobs categorized by their team assignments for a specific date.
        Returns the HTML of the Teams Timetable.
        """
        assignment_service = AssignmentService(db)
        job_service = JobService(db)
        team_service = TeamService(db)
        all_teams = team_service.get_all_teams()
        jobs_by_team = assignment_service.get_jobs_grouped_by_team_for_date(selected_date_for_fetch)
        team_back_to_back_job_ids = {}
        for team_obj in all_teams:
            team_back_to_back_job_ids[team_obj.id] = job_service.get_back_to_back_jobs_for_team_on_date(
                team_obj.id, selected_date_for_fetch, threshold_minutes=BACK_TO_BACK_THRESHOLD
            )
        
        # Render the entire team timetable view to ensure all columns are updated correctly
        # This will trigger the jobAssignmentsUpdated event in the frontend
        response_html = render_template_string(
            '{% include "team_timetable_fragment.html" %}',
            all_teams=all_teams,
            jobs_by_team=jobs_by_team,
            team_back_to_back_job_ids=team_back_to_back_job_ids,
            DATETIME_FORMATS=DATETIME_FORMATS,
            current_user=current_user,
            view_type='team',
            user_role=current_user.role,
            user_id=current_user.id,
            team_leader_id=current_user.team_id # Assuming current_user.team_id is the team leader's ID for simplicity, or needs to be fetched
        )
        return response_html

    @staticmethod
    def render_job_updates(db, job_id, current_user, selected_date_for_fetch):
        """
        Fetches updated job details and renders the job details and job list fragments.
        Returns a tuple: (job_details_html, job_list_html)
        """
        job_details_html = JobHelper.render_job_details_fragment(db, job_id)
        job_list_html = JobHelper.render_job_list_fragment(db, current_user, selected_date_for_fetch)
        return job_details_html, job_list_html