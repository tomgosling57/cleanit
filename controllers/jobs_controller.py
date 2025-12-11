from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response, session
from flask_login import current_user
from config import DATETIME_FORMATS, BACK_TO_BACK_THRESHOLD
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from database import get_db, teardown_db
from datetime import date, datetime
from collections import defaultdict
from utils.job_helper import JobHelper
from controllers.property_controller import get_property_jobs_modal_content

ERRORS = {'Job Not Found': 'Something went wrong! That job no longer exists.',
          'Missing Reassignment Details': "Missing job_id or new_team_id"}

def _handle_errors(errors=None, view_type=None):
    db = get_db()
    date = request.args.get('date')
    date_to_render = JobHelper.process_selected_date(date)

    if view_type == 'team':
        main_fragment_html = JobHelper.render_teams_timetable_fragment(db, current_user, date_to_render)
    else:
        main_fragment_html = JobHelper.render_job_list_fragment(db, current_user, date_to_render)
    
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
    teardown_db()
    return response_html, 200

def update_job_status(job_id):
    if not current_user.is_authenticated or current_user.role not in ['owner', 'team_leader']:
        return jsonify({'error': 'Unauthorized'}), 401

    is_complete = request.form.get('is_complete') == 'True'

    db = get_db()
    job_service = JobService(db)
    job = job_service.update_job_completion_status(job_id, is_complete)
    
    if job:
        # Accessing job.property to eagerly load it before the session is torn down
        # This prevents DetachedInstanceError when rendering the template
        _ = job.property.address
        response = render_template_string('{% include "job_status_fragment.html" %} {% include "job_actions_fragment.html" %}', job=job, is_oob_swap=True)
        teardown_db()
        return response

    return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=None)  


def get_job_details(job_id, view_type=None):
    if current_user.role not in ['cleaner', 'team_leader', 'owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    
    if job:
        back_to_back_job_ids = job_service.get_back_to_back_jobs_for_date(job.date, threshold_minutes=15)
        
        assignment_service = AssignmentService(db)
        cleaners = assignment_service.get_users_for_job(job_id)
        teams = assignment_service.get_teams_for_job(job_id)
        teardown_db()

        selected_date = session.get('selected_date', datetime.today().date())
        return render_template('job_details_modal.html', job=job, job_cleaners=cleaners, job_teams=teams, back_to_back_job_ids=back_to_back_job_ids, DATETIME_FORMATS=DATETIME_FORMATS, selected_date=selected_date, view_type=view_type)

    return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type)

def get_job_creation_form():
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)
    team_service = TeamService(db)
    property_service = PropertyService(db)
    users = user_service.get_all_users()
    teams = team_service.get_all_teams()
    properties = property_service.get_all_properties()
    
    selected_date_obj = session.get('selected_date', datetime.today().date())
    
    teardown_db()
    return render_template('job_creation_modal.html', users=users, teams=teams, properties=properties, DATETIME_FORMATS=DATETIME_FORMATS, today=datetime.today(), selected_date=selected_date_obj)
            
def timetable(date: str = None):
    db = get_db()
    job_service = JobService(db)
    team_service = TeamService(db)
    assignment_service = AssignmentService(db)

    date = JobHelper.process_selected_date(date)
    # Convert the session date string to a date object for service calls
    date_obj = datetime.strptime(date, DATETIME_FORMATS["DATE_FORMAT"]).date()

    jobs = job_service.get_jobs_for_user_on_date(current_user.id, current_user.team_id, date_obj)

    all_teams = team_service.get_all_teams()

    team_back_to_back_job_ids = {}
    for team_obj in all_teams:
        team_back_to_back_job_ids[team_obj.id] = job_service.get_back_to_back_jobs_for_team_on_date(
            team_obj.id, date_obj, threshold_minutes=BACK_TO_BACK_THRESHOLD
        )

    team = team_service.get_team(current_user.team_id)
    team_leader_id = team.team_leader_id if team else None
    selected_date = session['selected_date'] # Use the string directly from session
    current_user.selected_date = selected_date
    response = render_template('timetable.html', jobs=jobs, team_leader_id=team_leader_id,
                           user_id=current_user.id, selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                           back_to_back_job_ids=job_service.get_back_to_back_jobs_for_date(date_obj, threshold_minutes=BACK_TO_BACK_THRESHOLD),
                           all_teams=all_teams)
    teardown_db()
    return response

def team_timetable(date: str = None):
    db = get_db()
    job_service = JobService(db)
    team_service = TeamService(db)
    assignment_service = AssignmentService(db)

    date = JobHelper.process_selected_date(date)
    # Convert the session date string to a date object for service calls
    date_obj = datetime.strptime(date, DATETIME_FORMATS["DATE_FORMAT"]).date()

    all_teams = team_service.get_all_teams()
    jobs_by_team = assignment_service.get_jobs_grouped_by_team_for_date(date_obj)

    team_back_to_back_job_ids = {}
    for team_obj in all_teams:
        team_back_to_back_job_ids[team_obj.id] = job_service.get_back_to_back_jobs_for_team_on_date(
            team_obj.id, date_obj, threshold_minutes=BACK_TO_BACK_THRESHOLD
        )

    selected_date = session['selected_date'] # Use the string directly from session
    current_user.selected_date = selected_date
    response = render_template('team_timetable.html', selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                               all_teams=all_teams, jobs_by_team=jobs_by_team,
                               back_to_back_job_ids=team_back_to_back_job_ids)
    teardown_db()
    return response

def update_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    if not job:
        return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=request.form.get('view_type'))

    updated_job_data, assigned_teams, assigned_cleaners, error_response = JobHelper.process_job_form()
    if error_response:
        teardown_db()
        return error_response

    updated_job = job_service.update_job(job_id, updated_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(updated_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

    if updated_job:
        # Determine selected_date and view_type for rendering
        date_to_render = JobHelper.process_selected_date()
        view_type_to_render = request.form.get('view_type')

        if view_type_to_render == 'team':
            response_html = JobHelper.render_teams_timetable_fragment(db, current_user, date_to_render)
        if view_type_to_render == 'property':
            response_html = get_property_jobs_modal_content(session['property_id'])
        else:
            response_html = JobHelper.render_job_list_fragment(db, current_user, date_to_render)
        
        teardown_db()
        return response_html
    
    return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=request.form.get('view_type'))

def get_job_assignments_categorized(job_date_str=None):
    """Get categorized teams and users for job assignment based on current workload"""
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    if not job_date_str:
        job_date_str = request.form.get('date') or date.today().isoformat()

    try:
        job_date = date.fromisoformat(job_date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    db = get_db()
    team_service = TeamService(db)
    assignment_service = AssignmentService(db)
    
    # Get all teams and users
    all_teams = team_service.get_all_teams()
    
    # Get assignments for the date to count current workload
    all_assignments = assignment_service.get_all_jobs_for_date(job_date)
    
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
            if member.role == 'cleaner':
                user_dict = member.to_dict()
                user_dict['current_job_count'] = user_job_counts[member.id]
                user_dict['team_name'] = team.name
                
                if user_dict['current_job_count'] == 0:
                    available_cleaners.append(user_dict)
                elif user_dict['current_job_count'] <= 2:  # Threshold for "partially booked"
                    partially_booked_cleaners.append(user_dict)
                else:
                    fully_booked_cleaners.append(user_dict)
    
    teardown_db()
    
    categorized_assignments = {
        'teams': {
            'available': available_teams,
            'partially_booked': partially_booked_teams,
            'fully_booked': fully_booked_teams
        },
        'cleaners': {
            'available': available_cleaners,
            'partially_booked': partially_booked_cleaners,
            'fully_booked': fully_booked_cleaners
        }
    }
    
    return jsonify(categorized_assignments)

def get_job_update_form(job_id, view_type=None):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    user_service = UserService(db)
    team_service = TeamService(db)
    property_service = PropertyService(db)
    assignment_service = AssignmentService(db)
    job = job_service.get_job_details(job_id)
    teams = team_service.get_all_teams()
    users = user_service.get_all_users()
    job_users = assignment_service.get_users_for_job(job_id)
    job_teams = assignment_service.get_teams_for_job(job_id)
    properties = property_service.get_all_properties()
    teardown_db()
    if job:
        selected_date = session.get('selected_date', datetime.today().date())
        return render_template('job_update_modal.html', job=job, users=users, job_cleaners=job_users, properties=properties, teams=teams, job_teams=job_teams, DATETIME_FORMATS=DATETIME_FORMATS, selected_date=selected_date, view_type=view_type)
    return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=view_type)

def create_job():
    if current_user.role != 'owner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    assignment_service = AssignmentService(db)

    new_job_data, assigned_teams, assigned_cleaners, error_response = JobHelper.process_job_form()

    if error_response:
        teardown_db()
        return error_response
    
    new_job_data['is_complete'] = False # New jobs are not complete by default
    new_job = job_service.create_job(new_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(new_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

    if new_job:
        # Determine selected_date and view_type for rendering
        date_to_render = JobHelper.process_selected_date()
        view_type_to_render = request.form.get('view_type')

        if view_type_to_render == 'team':
            response_html = JobHelper.render_teams_timetable_fragment(db, current_user, date_to_render)
        else:
            response_html = JobHelper.render_job_list_fragment(db, current_user, date_to_render)
        
        teardown_db()
        return response_html
    teardown_db()
    return jsonify({'error': 'Failed to create job'}), 500


def delete_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    success = job_service.delete_job(job_id)
    if success:
        # Determine selected_date and view_type for rendering
        date_to_render = JobHelper.process_selected_date()
        view_type_to_render = request.form.get('view_type')

        if view_type_to_render == 'team':
            response_html = JobHelper.render_teams_timetable_fragment(db, current_user, date_to_render)
        else:
            # Default to normal job list if view_type is not 'team' or not provided
            response_html = JobHelper.render_job_list_fragment(
                db, current_user, date_to_render
            )
        teardown_db()
        return response_html
        
    return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type=request.form.get('view_type'))

def reassign_job_team():
    if not current_user.is_authenticated or current_user.role != 'owner':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db = get_db()
    assignment_service = AssignmentService(db)
    job_service = JobService(db)
    team_service = TeamService(db)    
    job = job_service.get_job_details(request.form.get('job_id'))
    if not job:
        return _handle_errors({'Job Not Found': ERRORS['Job Not Found']}, view_type='team')
    
    new_team = team_service.get_team(request.form.get('new_team_id'))
    old_team = team_service.get_team(request.form.get('old_team_id'))
    if not all([job, new_team]):
        return _handle_errors({'Missing Reassignment Details': ERRORS['Missing Reassignment Details']}, view_type='team')

    assignment_service.update_job_team_assignment(job, new_team, old_team)
    
    # Re-render the entire team timetable view
    selected_date_for_fetch = JobHelper.process_selected_date()
    response_html = JobHelper.render_teams_timetable_fragment(db, current_user, selected_date_for_fetch)
    teardown_db()
    return response_html