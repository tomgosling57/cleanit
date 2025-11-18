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

def update_job_status(job_id):
    if not current_user.is_authenticated or current_user.role not in ['cleaner', 'owner', 'team-leader']:
        return jsonify({'error': 'Unauthorized'}), 401

    is_complete = request.form.get('is_complete') == 'True'

    db = get_db()
    job_service = JobService(db)
    job = job_service.update_job_completion_status(job_id, is_complete)
    
    if job:
        # Accessing job.property to eagerly load it before the session is torn down
        # This prevents DetachedInstanceError when rendering the template
        # Accessing job.property to eagerly load it before the session is torn down
        # This prevents DetachedInstanceError when rendering the template
        _ = job.property.address
        response = render_template_string('{% include "job_status_fragment.html" %} {% include "job_actions_fragment.html" %}', job=job, user=current_user, is_oob_swap=True)
        teardown_db()
        return response
    
    teardown_db()
    return jsonify({'error': 'Job not found'}), 404

def get_job_details(job_id):
    if current_user.role not in ['cleaner', 'team_leader', 'owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    
    if not job:
        teardown_db()
        return jsonify({'error': 'Job not found'}), 404

    back_to_back_job_ids = job_service.get_back_to_back_jobs_for_date(job.date, threshold_minutes=15)
    
    assignment_service = AssignmentService(db)
    cleaners = assignment_service.get_users_for_job(job_id)
    teams = assignment_service.get_teams_for_job(job_id)
    teardown_db()

    return render_template('job_details_modal_content.html', job=job, job_cleaners=cleaners, job_teams=teams, back_to_back_job_ids=back_to_back_job_ids, DATETIME_FORMATS=DATETIME_FORMATS)

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
    
    # Retrieve selected_date from session, default to today if not found
    selected_date_from_session = session.get('selected_date', datetime.today().date())
    
    teardown_db()
    return render_template('job_creation_modal_content.html', users=users, teams=teams, properties=properties, DATETIME_FORMATS=DATETIME_FORMATS, today=datetime.today(), selected_date=selected_date_from_session)

def timetable(date: str = None):    
    db = get_db()
    job_service = JobService(db) # Instantiate JobService
    assignment_service = AssignmentService(db)

    date_obj = datetime.today().date()
    session['selected_date'] = date_obj

    # Use given date if provided
    if date:
        try:
            date_obj = datetime.strptime(date, DATETIME_FORMATS["DATE_FORMAT"]).date()
        except ValueError:
            date_obj = None

    jobs = assignment_service.get_assignments_for_user_on_date(current_user.id, current_user.team_id, date_obj)
    back_to_back_job_ids = job_service.get_back_to_back_jobs_for_date(date_obj, threshold_minutes=15) # Get back-to-back jobs
    team_service = TeamService(db)
    team = team_service.get_team(current_user.team_id)
    team_leader_id = team.team_leader_id if team else None
    selected_date = date_obj.strftime(DATETIME_FORMATS["DATE_FORMAT"])
    current_user.selected_date = selected_date
    response = render_template('timetable.html', jobs=jobs, team_leader_id=team_leader_id, user_role=current_user.role,
                           user_id=current_user.id, selected_date=selected_date, DATETIME_FORMATS=DATETIME_FORMATS,
                           back_to_back_job_ids=back_to_back_job_ids) # Pass back-to-back job IDs to template
    teardown_db()
    return response

def update_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    if not job:
        teardown_db()
        return jsonify({'error': 'Job not found'}), 404

    updated_job_data, assigned_teams, assigned_cleaners, error_response = JobHelper.process_job_form()

    if error_response:
        teardown_db()
        return error_response

    updated_job = job_service.update_job(job_id, updated_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(updated_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

    if updated_job:
        selected_date_for_fetch = JobHelper.get_selected_date_from_session()
        job_details_html, job_list_html = JobHelper.render_job_updates(
            db, job_id, current_user, DATETIME_FORMATS, BACK_TO_BACK_THRESHOLD, selected_date_for_fetch
        )
        
        response_html = f'<div hx-swap-oob="innerHTML:#job-details-modal-content">{job_details_html}</div>' \
                        f'<div id="job-list" hx-swap-oob="outerHTML:#job-list">{job_list_html}</div>'
        teardown_db()
        return response_html
    teardown_db()
    return jsonify({'error': 'Failed to update job'}), 500

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

def get_job_update_form(job_id):
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
        return render_template('job_update_form.html', job=job, users=users, job_users=job_users, properties=properties, teams=teams, job_teams=job_teams, DATETIME_FORMATS=DATETIME_FORMATS)
    return jsonify({'error': 'Job not found'}), 404

def create_job():
    if current_user.role != 'owner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    assignment_service = AssignmentService(db)    

    selected_date_obj = JobHelper.get_selected_date_from_session()
    selected_date = selected_date_obj.strftime(DATETIME_FORMATS["DATE_FORMAT"])

    new_job_data, assigned_teams, assigned_cleaners, error_response = JobHelper.process_job_form()

    if error_response:
        teardown_db()
        return error_response
    
    new_job_data['is_complete'] = False # New jobs are not complete by default
    new_job = job_service.create_job(new_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(new_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

    # Store job_date before tearing down the database session
    new_job_date = new_job.date

    # Re-fetch all jobs and render the list fragment
    selected_date_for_fetch = JobHelper.get_selected_date_from_session()
    _, job_list_html = JobHelper.render_job_updates(
        db, new_job.id, current_user, DATETIME_FORMATS, BACK_TO_BACK_THRESHOLD, selected_date_for_fetch
    )

    teardown_db()

    if new_job:
        print(f"selected_date: {selected_date}")
        if new_job_date.strftime(DATETIME_FORMATS["DATE_FORMAT"]) != selected_date:
            # If the new job's date doesn't match the currently selected date, don't update the list
            return Response(status=204)  # No Content
        return job_list_html
    return jsonify({'error': 'Failed to create job'}), 500


def delete_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    success = job_service.delete_job(job_id)
    if success:
        jobs = job_service.get_all_jobs().all()
        teardown_db()
        return render_template('job_list_fragment.html', jobs=jobs)
        
    teardown_db()
    return jsonify({'error': 'Job not found'}), 404