from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response, session, current_app
from flask_login import current_user
from config import DATETIME_FORMATS
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from services.media_service import MediaService
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from utils.job_helper import JobHelper
from utils.timezone import today_in_app_tz, utc_now

ERRORS = {'Job Not Found': 'Something went wrong! That job no longer exists.',
          'Missing Reassignment Details': "Missing job_id or new_team_id"}

# Time limit for media deletion by supervisors (in hours)
# Media older than this cannot be deleted by supervisors (admins can always delete)
MEDIA_DELETION_TIME_LIMIT_HOURS = 48


class JobController:
    """Controller class for job-related operations with dependency injection."""
    
    def _is_media_too_old_for_supervisor(self, media):
        """
        Check if media is too old for supervisor to delete.
        
        Args:
            media: Media object with upload_date field
            
        Returns:
            bool: True if media is too old for supervisor deletion, False otherwise
        """
        if not media or not media.upload_date:
            # If no upload date, assume it's old (shouldn't happen)
            return True
            
        cutoff_time = utc_now() - timedelta(hours=MEDIA_DELETION_TIME_LIMIT_HOURS)
        # Ensure upload_date is timezone-aware (UTC) for comparison
        upload_date = media.upload_date
        if upload_date.tzinfo is None:
            upload_date = upload_date.replace(tzinfo=timezone.utc)
        return upload_date < cutoff_time
    
    def __init__(self, job_service: JobService, team_service: TeamService,
                 user_service: UserService, property_service: PropertyService,
                 assignment_service: AssignmentService, job_helper: JobHelper,
                 media_service: MediaService = None):
        """
        Initialize the controller with injected service dependencies.
        
        Args:
            job_service: Service for job operations
            team_service: Service for team operations
            user_service: Service for user operations
            property_service: Service for property operations
            assignment_service: Service for assignment operations
            job_helper: Helper class for job-related operations
            media_service: Service for media operations (optional for backward compatibility)
        """
        self.job_service = job_service
        self.team_service = team_service
        self.user_service = user_service
        self.property_service = property_service
        self.assignment_service = assignment_service
        self.job_helper = job_helper
        self.media_service = media_service

    def _handle_errors(self, errors=None, view_type=None):
        date = request.args.get('date')
        date_to_render = self.job_helper.process_selected_date(date)

        if not view_type:
            # Retrieve view_type from request.form or request.args, defaulting to 'normal'
            view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')

        if view_type == 'team':
            main_fragment_html = self.job_helper.render_teams_timetable_fragment(current_user, date_to_render)
        else:
            main_fragment_html = self.job_helper.render_job_list_fragment(current_user, date_to_render)
        
        response_html = render_template_string(
            """
            {{ main_fragment_html | safe }}
            {% include '_form_response.html' %}
            """,
            errors=errors,
            DATETIME_FORMATS=DATETIME_FORMATS,
            is_oob_swap=True,
            main_fragment_html=main_fragment_html
        )
        return response_html, 200

    def update_job_status(self, job_id):
        """DEPRECATED: Use mark_job_complete or mark_job_pending instead."""
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized'}), 401

        is_complete = request.form.get('is_complete') == 'True'
        view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')

        job = self.job_service.update_job_completion_status(job_id, is_complete)
        
        if job:
            # Accessing job.property to eagerly load it before the session is torn down
            # This prevents DetachedInstanceError when rendering the template
            _ = job.property.address
            response = render_template_string('{% include "job_status_fragment.html" %} {% include "job_card.html" %}', job=job, is_oob_swap=True, view_type=view_type, DATETIME_FORMATS=DATETIME_FORMATS)
            return response

        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type)

    def mark_job_complete_with_report(self, job_id):
        """
        POST /jobs/job/<job_id>/mark_complete - Triggers report entry modal
        Opens modal for report text entry (first step)
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized'}), 401

        job = self._get_job_details(job_id)
        if not job:
            return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

        view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
        
        # Render report entry modal
        return render_template('job_report_modal.html', job=job, view_type=view_type, DATETIME_FORMATS=DATETIME_FORMATS)

    def submit_job_report(self, job_id):
        """
        POST /jobs/job/<job_id>/submit_report - Submits report text and opens gallery
        Validates non-empty report text, updates job.report, and opens gallery modal
        Supports skip_gallery parameter to bypass report entry when job already has report
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized'}), 401

        # Check if skip_gallery parameter is present (from hx-vals or form)
        skip_gallery = request.form.get('skip_gallery', '').lower() == 'true'
        
        # Get report text from form
        report_text = request.form.get('report_text', '').strip()
        
        # If skip_gallery is true but no report_text provided, try to get existing report
        if skip_gallery and not report_text:
            job = self._get_job_details(job_id)
            if job and job.report:
                report_text = job.report
            else:
                # No existing report, cannot skip gallery
                skip_gallery = False
        
        # Validate report text (unless skipping gallery with existing report)
        if not report_text and not skip_gallery:
            # Return error response
            job = self._get_job_details(job_id)
            if not job:
                return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})
            
            view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
            return render_template('job_report_modal.html', job=job, view_type=view_type,
                                  DATETIME_FORMATS=DATETIME_FORMATS, error='Report text is required')

        # Update job with report and mark as complete
        job = self.job_service.update_job_report_and_completion(job_id, report_text, is_complete=True)
        if not job:
            return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

        view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
        
        # Render gallery modal with submit button
        return render_template('components/job_gallery_with_submit.html', job=job, view_type=view_type, DATETIME_FORMATS=DATETIME_FORMATS)

    def mark_job_pending(self, job_id):
        """
        POST /jobs/job/<job_id>/mark_pending - Marks job as pending
        Sets job.is_complete = False (report and media remain associated)
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized'}), 401

        job = self.job_service.update_job_completion_status(job_id, is_complete=False)
        
        if job:
            # Accessing job.property to eagerly load it before the session is torn down
            # This prevents DetachedInstanceError when rendering the template
            _ = job.property.address
            view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
            response = render_template_string('{% include "job_status_fragment.html" %} {% include "job_card.html" %}', job=job, is_oob_swap=True, view_type=view_type, DATETIME_FORMATS=DATETIME_FORMATS)
            return response

        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

    def finalize_job_completion(self, job_id):
        """
        POST /jobs/job/<job_id>/complete_final - Finalizes job completion after gallery
        Job is already marked complete with report, this just closes modal and updates UI
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized'}), 401

        # Get the job to ensure it exists and is complete
        job = self._get_job_details(job_id)
        if not job:
            return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})
        
        # Job should already be complete from the report step, but ensure it is
        if not job.is_complete:
            job = self.job_service.update_job_completion_status(job_id, is_complete=True)
            if not job:
                return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

        # Accessing job.property to eagerly load it before the session is torn down
        # This prevents DetachedInstanceError when rendering the template
        _ = job.property.address
        view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
        
        # Return updated job card and status fragment to refresh UI
        response = render_template_string('{% include "job_status_fragment.html" %} {% include "job_card.html" %}', job=job, is_oob_swap=True, view_type=view_type, DATETIME_FORMATS=DATETIME_FORMATS)
        return response

    def _get_job_details(self, job_id):
        """Gets the job details from the service according to the users privileges"""
        access_notes_privilege = False
        if current_user.role in ['admin', 'supervisor']:
            access_notes_privilege = True
        elif self.team_service.is_team_leader(current_user.id, current_user.team_id):    
            access_notes_privilege = True
        job = self.job_service.get_job_details(job_id, include_access_notes=access_notes_privilege)
        return job
    
    def get_job_details(self, job_id):
        job_is_assigned_to_current_user = self.assignment_service.user_assigned_to_job(current_user.id, job_id)
        job_is_assigned_to_current_user_team = self.assignment_service.team_assigned_to_job(current_user.team_id, job_id)
        if current_user.role not in ['admin', 'supervisor'] and (current_user.role == 'user' and not (job_is_assigned_to_current_user or job_is_assigned_to_current_user_team)):
            return jsonify({'error': 'Unauthorized'}), 403

        job = self._get_job_details(job_id)
        if job:
            cleaners = self.assignment_service.get_users_for_job(job_id)
            teams = self.assignment_service.get_teams_for_job(job_id)

            selected_date = session.get('selected_date', today_in_app_tz())
            view_type = request.args.get('view_type', 'normal')
            return render_template('job_details_modal.html', job=job, job_cleaners=cleaners, job_teams=teams, DATETIME_FORMATS=DATETIME_FORMATS, selected_date=selected_date, view_type=view_type)

        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

    def get_job_creation_form(self):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        users = self.user_service.get_all_users()
        teams = self.team_service.get_all_teams()
        properties = self.property_service.get_all_properties()
        
        selected_date_obj = session.get('selected_date', today_in_app_tz())
        
        return render_template('job_creation_modal.html', users=users, teams=teams, properties=properties, DATETIME_FORMATS=DATETIME_FORMATS, today=today_in_app_tz(), selected_date=selected_date_obj)
            
    def timetable(self, date: str = None):
        date = self.job_helper.process_selected_date(date)
        # Convert the session date string to a date object for service calls
        date_obj = datetime.strptime(date, DATETIME_FORMATS["DATE_FORMAT"]).date()

        self.job_service.push_uncompleted_jobs_to_next_day()
        jobs = self.job_service.get_jobs_for_user_on_date(current_user.id, current_user.team_id, date_obj)

        all_teams = self.team_service.get_all_teams()

        team = self.team_service.get_team(current_user.team_id)
        team_leader_id = team.team_leader_id if team else None
        selected_date = session['selected_date'] # Use the string directly from session
        current_user.selected_date = selected_date
        response = render_template('timetable.html', jobs=jobs, team_leader_id=team_leader_id,
                               user_id=current_user.id, selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                               all_teams=all_teams)
        return response

    def team_timetable(self, date: str = None):
        date = self.job_helper.process_selected_date(date)
        # Convert the session date string to a date object for service calls
        date_obj = datetime.strptime(date, DATETIME_FORMATS["DATE_FORMAT"]).date()

        self.job_service.push_uncompleted_jobs_to_next_day()
        all_teams = self.team_service.get_all_teams()
        jobs_by_team = self.job_service.get_jobs_grouped_by_team_for_date(date_obj)

        selected_date = session['selected_date'] # Use the string directly from session
        current_user.selected_date = selected_date
        response = render_template('team_timetable.html', selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                                   all_teams=all_teams, jobs_by_team=jobs_by_team)
        return response

    def update_job(self, job_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        job = self._get_job_details(job_id)
        if not job:
            return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

        updated_job_data, assigned_teams, assigned_cleaners, error_response = self.job_helper.process_job_form()
        if error_response:
            return error_response

        updated_job = self.job_service.update_job(job_id, updated_job_data)
        self.assignment_service.update_assignments(updated_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

        if updated_job:
            # Determine selected_date and view_type for rendering
            date_to_render = self.job_helper.process_selected_date()
            view_type_to_render = request.form.get('view_type')

            if view_type_to_render == 'team':
                response_html = self.job_helper.render_teams_timetable_fragment(current_user, date_to_render)
            elif view_type_to_render == 'property':
                # Render property jobs modal directly (replacing get_property_jobs_modal_content)
                property_id = session.get('property_id')
                if property_id:
                    property = self.property_service.get_property_by_id(property_id)
                    if property:
                        jobs = self.job_service.get_jobs_by_property_id(property_id)
                        response_html = render_template('property_jobs_modal.html', property=property, jobs=jobs, DATETIME_FORMATS=DATETIME_FORMATS)
                    else:
                        response_html = jsonify({'error': 'Property not found'}), 404
                else:
                    response_html = jsonify({'error': 'Property ID not found in session'}), 400
            else:
                response_html = self.job_helper.render_job_list_fragment(current_user, date_to_render)
            
            return response_html
        
        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type_to_render)

    def get_job_assignments_categorized(self, job_date_str=None):
        """Get categorized teams and users for job assignment based on current workload"""
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        if not job_date_str:
            job_date_str = request.form.get('date') or date.today().isoformat()

        try:
            job_date = date.fromisoformat(job_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        # Get all teams and users
        all_teams = self.team_service.get_all_teams()
        
        # Get assignments for the date to count current workload
        all_assignments = self.assignment_service.get_all_jobs_for_date(job_date)
        
        # Count current assignments per team
        team_job_counts = defaultdict(int)
        user_job_counts = defaultdict(int)
        
        for assignment in all_assignments:
            # Count team assignments
            for team in assignment.teams:
                team_job_counts[team.id] += 1
            
            # Count user assignments
            for user in assignment.users:
                user_job_counts[user.id] += 1
        
        # Categorize teams based on current workload
        available_teams = []
        partially_booked_teams = []
        fully_booked_teams = []
        
        for team in all_teams:
            team_dict = team.to_dict()
            team_dict['current_job_count'] = team_job_counts[team.id]
            
            if team_dict['current_job_count'] == 0:
                available_teams.append(team_dict)
            elif team_dict['current_job_count'] <= 2:  # Threshold for "partially booked"
                partially_booked_teams.append(team_dict)
            else:
                fully_booked_teams.append(team_dict)
        
        # Categorize users (cleaners) based on current workload
        available_cleaners = []
        partially_booked_cleaners = []
        fully_booked_cleaners = []
        
        for team in all_teams:
            for member in team.members:
                if member.role == 'user':
                    user_dict = member.to_dict()
                    user_dict['current_job_count'] = user_job_counts[member.id]
                    user_dict['team_name'] = team.name
                    
                    if user_dict['current_job_count'] == 0:
                        available_cleaners.append(user_dict)
                    elif user_dict['current_job_count'] <= 2:  # Threshold for "partially booked"
                        partially_booked_cleaners.append(user_dict)
                    else:
                        fully_booked_cleaners.append(user_dict)
        
        categorized_assignments = {
            'teams': {
                'available': available_teams,
                'partially_booked': partially_booked_teams,
                'fully_booked': fully_booked_teams
            },
            'users': {
                'available': available_cleaners,
                'partially_booked': partially_booked_cleaners,
                'fully_booked': fully_booked_cleaners
            }
        }
        
        return jsonify(categorized_assignments)

    def get_job_update_form(self, job_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        job = self._get_job_details(job_id)
        teams = self.team_service.get_all_teams()
        users = self.user_service.get_all_users()
        job_users = self.assignment_service.get_users_for_job(job_id)
        job_teams = self.assignment_service.get_teams_for_job(job_id)
        properties = self.property_service.get_all_properties()
        if job:
            selected_date = session.get('selected_date', today_in_app_tz())
            return render_template('job_update_modal.html', job=job, users=users, job_cleaners=job_users, properties=properties, teams=teams, job_teams=job_teams, DATETIME_FORMATS=DATETIME_FORMATS, selected_date=selected_date)
        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

    def create_job(self):
        if current_user.role != 'admin':
            flash('Unauthorized access', 'error')
            return redirect(url_for('index'))

        new_job_data, assigned_teams, assigned_cleaners, error_response = self.job_helper.process_job_form()

        if error_response:
            return error_response
        
        new_job_data['is_complete'] = False # New jobs are not complete by default
        new_job = self.job_service.create_job(new_job_data)
        self.assignment_service.update_assignments(new_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

        if new_job:
            # Determine selected_date and view_type for rendering
            date_to_render = self.job_helper.process_selected_date()
            view_type_to_render = request.form.get('view_type')

            if view_type_to_render == 'team':
                response_html = self.job_helper.render_teams_timetable_fragment(current_user, date_to_render)
            else:
                response_html = self.job_helper.render_job_list_fragment(current_user, date_to_render)
            
            return response_html
        view_type_to_render = request.form.get('view_type') or request.args.get('view_type', 'normal')
        return self._handle_errors({'Failed to create job': 'Failed to create job'}, view_type=view_type_to_render)


    def delete_job(self, job_id, view_type):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        success = self.job_service.delete_job(job_id)
        if success:
            # Determine selected_date and view_type for rendering
            date_to_render = self.job_helper.process_selected_date()

            if view_type == 'team':
                response_html = self.job_helper.render_teams_timetable_fragment(current_user, date_to_render)
            else:
                # Default to normal job list if view_type is not 'team' or not provided
                response_html = self.job_helper.render_job_list_fragment(
                    current_user, date_to_render
                )
            return response_html
            
        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type)

    def reassign_job_team(self):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        job = self._get_job_details(request.form.get('job_id'))
        view_type = request.form.get('view_type') or request.args.get('view_type', 'normal')
        if not job:
            return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type)
        
        new_team = self.team_service.get_team(request.form.get('new_team_id'))
        old_team = self.team_service.get_team(request.form.get('old_team_id'))
        if not all([job, new_team]):
            return self._handle_errors({'Missing Reassignment Details': ERRORS['Missing Reassignment Details']}, view_type=view_type)

        self.assignment_service.update_job_team_assignment(job, new_team, old_team)
        
        # Re-render the entire team timetable view
        selected_date_for_fetch = self.job_helper.process_selected_date()
        response_html = self.job_helper.render_teams_timetable_fragment(current_user, selected_date_for_fetch)
        return response_html

    # ========== MEDIA GALLERY METHODS ==========

    def get_job_gallery(self, job_id):
        """
        GET /jobs/<job_id>/media - Get all media for job
        
        Args:
            job_id (int): The job ID
            
        Returns:
            JSON response with media list or error
        """
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Check if user has access to this job
        job_is_assigned_to_current_user = self.assignment_service.user_assigned_to_job(current_user.id, job_id)
        job_is_assigned_to_current_user_team = self.assignment_service.team_assigned_to_job(current_user.team_id, job_id)
        if current_user.role not in ['admin', 'supervisor'] and (current_user.role == 'user' and not (job_is_assigned_to_current_user or job_is_assigned_to_current_user_team)):
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not self.media_service:
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            media_items = self.media_service.get_media_for_job(job_id)
            formatted_media = [self._format_media_response(media) for media in media_items]
            return jsonify({
                'success': True,
                'job_id': job_id,
                'media': formatted_media,
                'count': len(formatted_media)
            }), 200
        except Exception as e:
            return jsonify({'error': f'Failed to retrieve job gallery: {str(e)}'}), 500

    def add_job_media(self, job_id):
        """
        POST /jobs/<job_id>/media - Upload and associate media with job
        
        This endpoint handles file uploads directly to job gallery.
        Files are uploaded, stored, and automatically associated with the job.
        
        Args:
            job_id (int): The job ID
            
        Returns:
            JSON response with success/error and uploaded media details
        """
        from flask import current_app
        
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            current_app.logger.warning(f"Unauthorized attempt to add media to job {job_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            return jsonify({'error': 'Unauthorized: Admin or Supervisor access required'}), 403
        
        if not self.media_service:
            current_app.logger.error("Media service not available in job controller")
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if job exists
            job = self._get_job_details(job_id)
            if not job:
                current_app.logger.warning(f"Job {job_id} not found")
                return jsonify({'error': 'Job not found'}), 404
            
            # Check content type - must be multipart/form-data for file uploads
            content_type = request.content_type or ''
            current_app.logger.debug(f"Content-Type: {content_type}")
            current_app.logger.debug(f"Request method: {request.method}")
            current_app.logger.debug(f"Request headers: {dict(request.headers)}")
            
            if 'multipart/form-data' not in content_type:
                current_app.logger.warning(f"Invalid content type for job {job_id} upload: {content_type}")
                return jsonify({'error': 'Content type must be multipart/form-data for file uploads'}), 400
            
            # Check if files are present
            current_app.logger.debug(f"Request files keys: {list(request.files.keys())}")
            current_app.logger.debug(f"Request form keys: {list(request.form.keys())}")
            
            if 'files[]' not in request.files and 'file' not in request.files:
                current_app.logger.warning(f"No files provided in request for job {job_id}")
                return jsonify({'error': 'No files provided in request'}), 400
            
            # Get files - support both 'files[]' array and single 'file'
            files = []
            if 'files[]' in request.files:
                files = request.files.getlist('files[]')
                current_app.logger.debug(f"Found {len(files)} files in 'files[]' array")
            elif 'file' in request.files:
                files = [request.files['file']]
                current_app.logger.debug(f"Found single file 'file'")
            
            if not files or all(file.filename == '' for file in files):
                current_app.logger.warning(f"No selected files for job {job_id}")
                return jsonify({'error': 'No selected files'}), 400
            
            current_app.logger.debug(f"Processing {len(files)} files for job {job_id}")
            
            # Get descriptions - support both 'descriptions[]' array and single 'description'
            descriptions = []
            if 'descriptions[]' in request.form:
                descriptions = request.form.getlist('descriptions[]')
                current_app.logger.debug(f"Found {len(descriptions)} descriptions in 'descriptions[]' array")
            elif 'description' in request.form:
                descriptions = [request.form['description']]
                current_app.logger.debug(f"Found single description 'description'")
            else:
                # Use filenames as descriptions
                descriptions = [file.filename for file in files]
                current_app.logger.debug(f"Using filenames as descriptions")
            
            # Ensure we have enough descriptions
            while len(descriptions) < len(files):
                descriptions.append(files[len(descriptions)].filename)
            
            # Import media utilities
            from utils.media_utils import (
                identify_file_type,
                validate_media,
                upload_media_to_storage,
                get_media_url,
                extract_metadata
            )
            
            uploaded_media = []
            media_ids = []
            
            for i, file in enumerate(files):
                try:
                    if not file or file.filename == '':
                        current_app.logger.debug(f"Skipping empty file at index {i}")
                        continue
                    
                    current_app.logger.debug(f"Processing file {i}: {file.filename}, size: {file.content_length}")
                    
                    # Identify file type
                    file.seek(0)
                    media_type, mime_type = identify_file_type(file)
                    current_app.logger.debug(f"File {file.filename} identified as {media_type} ({mime_type})")
                    
                    # Validate media
                    file.seek(0)
                    validate_media(file, media_type)
                    current_app.logger.debug(f"File {file.filename} validation passed")
                    
                    # Upload to storage
                    file.seek(0)
                    filename = upload_media_to_storage(file, file.filename, media_type)
                    current_app.logger.debug(f"File {file.filename} uploaded to storage as {filename}")
                    
                    # Get file size
                    file.seek(0, 2)  # Seek to end
                    size_bytes = file.tell()
                    file.seek(0)  # Reset
                    current_app.logger.debug(f"File {file.filename} size: {size_bytes} bytes")
                    
                    # Extract metadata if available
                    metadata = {}
                    try:
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                            file.save(tmp.name)
                            tmp_path = tmp.name
                            metadata = extract_metadata(tmp_path, media_type)
                            os.unlink(tmp_path)
                        current_app.logger.debug(f"Extracted metadata for {file.filename}: {metadata}")
                    except Exception as e:
                        # Metadata extraction is optional
                        current_app.logger.debug(f"Metadata extraction failed for {file.filename}: {str(e)}")
                    
                    # Create media record
                    description = descriptions[i] if i < len(descriptions) else file.filename
                    media = self.media_service.add_media(
                        file_name=file.filename,
                        file_path=filename,
                        media_type=media_type,
                        mimetype=mime_type,
                        size_bytes=size_bytes,
                        description=description,
                        metadata=metadata
                    )
                    
                    uploaded_media.append(media)
                    media_ids.append(media.id)
                    current_app.logger.debug(f"Created media record ID {media.id} for {file.filename}")
                    
                except ValueError as e:
                    # Skip invalid files but continue with others
                    current_app.logger.warning(f"File {file.filename if file else 'unknown'} validation failed: {str(e)}")
                    continue
                except Exception as e:
                    # Skip files that fail to upload but continue with others
                    current_app.logger.error(f"File {file.filename if file else 'unknown'} upload failed: {str(e)}")
                    continue
            
            if not media_ids:
                current_app.logger.error(f"No files could be uploaded for job {job_id}")
                return jsonify({'error': 'No files could be uploaded'}), 400
            
            # Associate uploaded media with job
            associations = self.media_service.associate_media_batch_with_job(
                job_id, media_ids
            )
            current_app.logger.debug(f"Associated {len(associations)} media items with job {job_id}")
            
            # Prepare response with uploaded media details
            media_details = []
            for media in uploaded_media:
                media_url = get_media_url(media.file_path) if media.file_path else None
                media_details.append({
                    'id': media.id,
                    'filename': media.filename,
                    'url': media_url,
                    'media_type': media.media_type,
                    'mimetype': media.mimetype,
                    'size_bytes': media.size_bytes,
                    'description': media.description
                })
            
            current_app.logger.info(f"Successfully uploaded and associated {len(uploaded_media)} files with job {job_id}")
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded and associated {len(uploaded_media)} files with job',
                'job_id': job_id,
                'media_ids': media_ids,
                'media': media_details,
                'association_count': len(associations)
            }), 200
                
        except Exception as e:
            current_app.logger.error(f"Failed to add media to job {job_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to add media to job: {str(e)}'}), 500

    def remove_job_media(self, job_id):
        """
        DELETE /jobs/<job_id>/media - Remove media from job (batch)
        
        Args:
            job_id (int): The job ID
            
        Returns:
            JSON response with success/error
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized: Admin or Supervisor access required'}), 403
        
        if not self.media_service:
            flash('Media service not available', 'error')
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if job exists
            job = self._get_job_details(job_id)
            if not job:
                flash('Job not found', 'error')
                return jsonify({'error': 'Job not found'}), 404
            
            # Get media IDs from request JSON
            data = request.get_json()
            if not data or 'media_ids' not in data:
                return jsonify({'error': 'Missing media_ids in request body'}), 400
            
            media_ids = data['media_ids']
            if not isinstance(media_ids, list):
                return jsonify({'error': 'media_ids must be a list'}), 400
            
            # For supervisors (not admins), check if any media is too old to delete
            if current_user.role == 'supervisor':
                from database import Media
                # Query all media objects to check their upload dates
                media_items = self.media_service.db_session.query(Media).filter(
                    Media.id.in_(media_ids)
                ).all()
                
                # Check each media item
                too_old_media = []
                for media in media_items:
                    if self._is_media_too_old_for_supervisor(media):
                        too_old_media.append({
                            'id': media.id,
                            'filename': media.filename,
                            'upload_date': media.display_upload_date if media.upload_date else None
                        })
                
                if too_old_media:
                    return jsonify({
                        'error': 'Cannot delete media: some items are too old',
                        'details': f'Media older than {MEDIA_DELETION_TIME_LIMIT_HOURS} hours cannot be deleted by supervisors',
                        'too_old_items': too_old_media,
                        'total_requested': len(media_ids),
                        'too_old_count': len(too_old_media)
                    }), 403
            
            # Batch disassociate media from job
            result = self.media_service.disassociate_media_batch_from_job(job_id, media_ids)
            
            return jsonify(result), 200
        except Exception as e:
            current_app.logger.error(f"Failed to remove media from job {job_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to remove media from job: {str(e)}'}), 500

    def remove_single_job_media(self, job_id, media_id):
        """
        DELETE /jobs/<job_id>/media/<media_id> - Remove single media from job
        
        Args:
            job_id (int): The job ID
            media_id (int): The media ID
            
        Returns:
            JSON response with success/error
        """
        if not current_user.is_authenticated or current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized: Admin or Supervisor access required'}), 403
        
        if not self.media_service:
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if job exists
            job = self._get_job_details(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # For supervisors (not admins), check if media is too old to delete
            if current_user.role == 'supervisor':
                from database import Media
                # Query the media object to check its upload date
                media = self.media_service.db_session.query(Media).filter(
                    Media.id == media_id
                ).first()
                
                if not media:
                    return jsonify({'error': 'Media not found'}), 404
                
                if self._is_media_too_old_for_supervisor(media):
                    return jsonify({
                        'error': 'Cannot delete media: item is too old',
                        'details': f'Media older than {MEDIA_DELETION_TIME_LIMIT_HOURS} hours cannot be deleted by supervisors',
                        'media_id': media_id,
                        'filename': media.filename,
                        'upload_date': media.display_upload_date if media.upload_date else None
                    }), 403
            
            # Remove single association
            success = self.media_service.remove_association_from_job(media_id, job_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Media removed from job successfully',
                    'job_id': job_id,
                    'media_id': media_id
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Association not found'
                }), 404
        except Exception as e:
            current_app.logger.error(f"Failed to remove single media {media_id} from job {job_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to remove media from job: {str(e)}'}), 500

    def _format_media_response(self, media):
        """
        Format a media object for JSON response.
        
        Args:
            media: Media object
            
        Returns:
            dict: Formatted media data
        """
        from utils.media_utils import get_media_url
        
        media_url = get_media_url(media.file_path) if media.file_path else None
        
        return {
            'id': media.id,
            'filename': media.filename,
            'url': media_url,
            'media_type': media.media_type,
            'mimetype': media.mimetype,
            'size_bytes': media.size_bytes,
            'description': media.description,
            'width': media.width,
            'height': media.height,
            'duration_seconds': media.duration_seconds,
            'thumbnail_url': media.thumbnail_url,
            'resolution': media.resolution,
            'codec': media.codec,
            'aspect_ratio': media.aspect_ratio,
            'upload_date': media.display_upload_date if media.upload_date else None
        }
