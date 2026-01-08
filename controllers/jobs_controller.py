from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response, session
from flask_login import current_user
from config import DATETIME_FORMATS
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from datetime import date, datetime
from collections import defaultdict
from utils.job_helper import JobHelper
from controllers.property_controller import get_property_jobs_modal_content

ERRORS = {'Job Not Found': 'Something went wrong! That job no longer exists.',
          'Missing Reassignment Details': "Missing job_id or new_team_id"}


class JobController:
    """Controller class for job-related operations with dependency injection."""
    
    def __init__(self, job_service: JobService, team_service: TeamService,
                 user_service: UserService, property_service: PropertyService,
                 assignment_service: AssignmentService, job_helper: JobHelper):
        """
        Initialize the controller with injected service dependencies.
        
        Args:
            job_service: Service for job operations
            team_service: Service for team operations
            user_service: Service for user operations
            property_service: Service for property operations
            assignment_service: Service for assignment operations
            job_helper: Helper class for job-related operations
        """
        self.job_service = job_service
        self.team_service = team_service
        self.user_service = user_service
        self.property_service = property_service
        self.assignment_service = assignment_service
        self.job_helper = job_helper

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


    def get_job_details(self, job_id):
        job_is_assigned_to_current_user = self.assignment_service.user_assigned_to_job(current_user.id, job_id)
        job_is_assigned_to_current_user_team = self.assignment_service.team_assigned_to_job(current_user.team_id, job_id)
        if current_user.role not in ['admin', 'supervisor'] and (current_user.role == 'user' and not (job_is_assigned_to_current_user or job_is_assigned_to_current_user_team)):
            return jsonify({'error': 'Unauthorized'}), 403

        job = self.job_service.get_job_details(job_id)
        
        if job:
            cleaners = self.assignment_service.get_users_for_job(job_id)
            teams = self.assignment_service.get_teams_for_job(job_id)

            selected_date = session.get('selected_date', datetime.today().date())
            view_type = request.args.get('view_type', 'normal')
            return render_template('job_details_modal.html', job=job, job_cleaners=cleaners, job_teams=teams, DATETIME_FORMATS=DATETIME_FORMATS, selected_date=selected_date, view_type=view_type)

        return self._handle_errors({'Job Not Found': ERRORS['Job Not Found']})

    def get_job_creation_form(self):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        users = self.user_service.get_all_users()
        teams = self.team_service.get_all_teams()
        properties = self.property_service.get_all_properties()
        
        selected_date_obj = session.get('selected_date', datetime.today().date())
        
        return render_template('job_creation_modal.html', users=users, teams=teams, properties=properties, DATETIME_FORMATS=DATETIME_FORMATS, today=datetime.today(), selected_date=selected_date_obj)
            
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
        jobs_by_team = self.assignment_service.get_jobs_grouped_by_team_for_date(date_obj)

        selected_date = session['selected_date'] # Use the string directly from session
        current_user.selected_date = selected_date
        response = render_template('team_timetable.html', selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                                   all_teams=all_teams, jobs_by_team=jobs_by_team)
        return response

    def update_job(self, job_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        job = self.job_service.get_job_details(job_id)
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
                response_html = get_property_jobs_modal_content(session['property_id'])
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

        job = self.job_service.get_job_details(job_id)
        teams = self.team_service.get_all_teams()
        users = self.user_service.get_all_users()
        job_users = self.assignment_service.get_users_for_job(job_id)
        job_teams = self.assignment_service.get_teams_for_job(job_id)
        properties = self.property_service.get_all_properties()
        if job:
            selected_date = session.get('selected_date', datetime.today().date())
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

        job = self.job_service.get_job_details(request.form.get('job_id'))
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