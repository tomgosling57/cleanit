from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import current_user
from config import DATE_FORMAT, DATE_FORMAT_FLATPICKR, DATETIME_FORMAT, DATETIME_FORMAT_FLATPICKR, TIME_FORMAT, TIME_FORMAT_FLATPICKR
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from database import get_db, teardown_db
from datetime import date, datetime, time
from collections import defaultdict

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

    return render_template('job_details_modal_content.html', job=job, job_cleaners=cleaners, job_teams=teams, back_to_back_job_ids=back_to_back_job_ids, date_format_flatpickr=DATE_FORMAT_FLATPICKR, time_format_flatpickr=TIME_FORMAT_FLATPICKR)

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
    teardown_db()
    return render_template('job_creation_modal_content.html', users=users, teams=teams, properties=properties, date_format_flatpickr=DATE_FORMAT_FLATPICKR, time_format_flatpickr=TIME_FORMAT_FLATPICKR)

def timetable(date: str = None):    
    db = get_db()
    job_service = JobService(db) # Instantiate JobService
    assignment_service = AssignmentService(db)

    date_obj = datetime.today().date()

    # Use given date if provided
    if date:
        try:
            date_obj = datetime.strptime(date, DATE_FORMAT).date()
        except ValueError:
            date_obj = None

    jobs = assignment_service.get_assignments_for_user_on_date(current_user.id, current_user.team_id, date_obj)
    back_to_back_job_ids = job_service.get_back_to_back_jobs_for_date(date_obj, threshold_minutes=15) # Get back-to-back jobs
    team_service = TeamService(db)
    team = team_service.get_team(current_user.team_id)
    team_leader_id = team.team_leader_id if team else None
    teardown_db()

    selected_date = date_obj.strftime(DATE_FORMAT)
    current_user.selected_date = selected_date
    return render_template('timetable.html', jobs=jobs, team_leader_id=team_leader_id, user_role=current_user.role,
                           user_id=current_user.id, selected_date=selected_date, date_format=DATE_FORMAT_FLATPICKR,
                           back_to_back_job_ids=back_to_back_job_ids) # Pass back-to-back job IDs to template

def update_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    if not job:
        teardown_db()
        return jsonify({'error': 'Job not found'}), 404

    property_address = request.form.get('property_address')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    arrival_date_str = request.form.get('arrival_date')
    arrival_time_str = request.form.get('arrival_time')
    end_time_str = request.form.get('end_time')
    assigned_cleaners = request.form.getlist('assigned_cleaners')
    assigned_teams = request.form.getlist('assigned_teams')
    job_type = request.form.get('job_type')
    notes = request.form.get('notes')

    if not all([property_address, date_str, time_str, end_time_str]):
        teardown_db()
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        job_date = date.fromisoformat(date_str)
        job_time = time.fromisoformat(time_str)
        job_end_time = time.fromisoformat(end_time_str)
        
        job_arrival_time = None
        if arrival_date_str and arrival_time_str:
            job_arrival_date = datetime.strptime(arrival_date_str, DATE_FORMAT).date()
            job_arrival_time_only = datetime.strptime(arrival_time_str, TIME_FORMAT).time()
            job_arrival_time = datetime.combine(job_arrival_date, job_arrival_time_only)
    except ValueError:
        teardown_db()
        return jsonify({'error': 'Invalid date or time format'}), 400

    property_obj = job_service.get_property_by_address(property_address)
    if not property_obj:
        property_obj = job_service.create_property(property_address)

    updated_job_data = {
        'date': job_date,
        'time': job_time,
        'arrival_time': job_arrival_time,
        'end_time': job_end_time,
        'description': notes,
        'job_type': job_type,
        'property_id': property_obj.id
    }
    updated_job = job_service.update_job(job_id, updated_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(updated_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)
    teardown_db()

    if updated_job:
        # Fetch the updated job details for the modal
        job = job_service.get_job_details(job_id)
        
        # Render job details for the modal
        job_details_html = render_template('job_details_modal_content.html', job=job, date_format_flatpickr=DATE_FORMAT_FLATPICKR, time_format_flatpickr=TIME_FORMAT_FLATPICKR)
        
        # Re-fetch all jobs to ensure the list is up-to-date
        all_jobs = job_service.get_all_jobs() 
        job_list_html = render_template('job_list_fragment.html', jobs=all_jobs)
        
        # Combine them with OOB swap attributes
        response_html = f'<div hx-swap-oob="innerHTML:#job-details-modal-content">{job_details_html}</div>' \
                        f'<div id="job-list" hx-swap-oob="outerHTML:#job-list">{job_list_html}</div>'
        
        return response_html

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
        return render_template('job_update_form.html', job=job, users=users, job_users=job_users, properties=properties, teams=teams, job_teams=job_teams, date_format_flatpickr=DATE_FORMAT_FLATPICKR, time_format_flatpickr=TIME_FORMAT_FLATPICKR)
    return jsonify({'error': 'Job not found'}), 404

def create_job():
    if current_user.role != 'owner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    assignment_service = AssignmentService(db)    

    property_address = request.form.get('property_address')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    arrival_date_str = request.form.get('arrival_date')
    arrival_time_str = request.form.get('arrival_time')
    end_time_str = request.form.get('end_time')
    assigned_teams = request.form.getlist('assigned_teams')
    assigned_cleaners = request.form.getlist('assigned_cleaners')
    job_type = request.form.get('job_type')
    notes = request.form.get('notes')
    selected_date = request.form.get('selected_date')

    if not all([property_address, date_str, time_str, end_time_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        job_date = date.fromisoformat(date_str)
        job_time = time.fromisoformat(time_str)
        job_end_time = time.fromisoformat(end_time_str)
        
        job_arrival_time = None
        if arrival_date_str and arrival_time_str:
            job_arrival_date = datetime.strptime(arrival_date_str, DATE_FORMAT).date()
            job_arrival_time_only = datetime.strptime(arrival_time_str, TIME_FORMAT).time()
            job_arrival_time = datetime.combine(job_arrival_date, job_arrival_time_only)
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400

    property_obj = job_service.get_property_by_address(property_address)
    if not property_obj:
        property_obj = job_service.create_property(property_address)

    new_job_data = {
        'is_complete': False,
        'date': job_date,
        'time': job_time,
        'arrival_time': job_arrival_time,
        'end_time': job_end_time,
        'description': notes,
        'job_type': job_type,
        'property_id': property_obj.id
    }
    new_job = job_service.create_job(new_job_data)
    assignment_service = AssignmentService(db)
    assignment_service.update_assignments(new_job.id, team_ids=assigned_teams, user_ids=assigned_cleaners)

    # Get all jobs to re-render the entire job list
    jobs = job_service.get_all_jobs()
    teardown_db()

    if new_job:
        if job_date.strftime(DATE_FORMAT) != selected_date:
            # If the new job's date doesn't match the currently selected date, don't update the list
            return Response(status=204)  # No Content
        return render_template('job_list_fragment.html', jobs=jobs)
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