from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import current_user
from config import DATE_FORMAT
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.assignment_service import AssignmentService
from database import get_db, teardown_db
from datetime import date, datetime, time

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
    teardown_db()

    if job:
        job.assigned_cleaners_list = job.assigned_cleaners.split(',') if job.assigned_cleaners else []
        return render_template('job_details_modal_content.html', job=job)
    return jsonify({'error': 'Job not found'}), 404

def get_job_creation_form():
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)
    cleaners = user_service.get_users_by_role('cleaner')
    teardown_db()
    return render_template('job_creation_modal_content.html', cleaners=cleaners)

def timetable(date: str = None):    
    db = get_db()
    assignment_service = AssignmentService(db)
    
    if date:
        try:
            date_obj = datetime.strptime(date, DATE_FORMAT).date()
        except ValueError:
            date_obj = None
    else:
        date_obj = datetime.today().date()

    jobs = assignment_service.get_assignments_for_user_on_date(current_user.id, current_user.team_id, date_obj)
    team_service = TeamService(db)    
    team = team_service.get_team(current_user.team_id)
    team_leader_id = team.team_leader_id if team else None
    teardown_db()
    return render_template('timetable.html', jobs=jobs, team_leader_id=team_leader_id, user_role=current_user.role, user_id=current_user.id, selected_date=date_obj)

def update_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    job = job_service.get_job_details(job_id)
    if not job:
        teardown_db()
        return jsonify({'error': 'Job not found'}), 404

    job_title = request.form.get('job_title')
    property_address = request.form.get('property_address')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    duration = request.form.get('duration')
    assigned_cleaner_id = request.form.get('assigned_cleaner_id')
    job_type = request.form.get('job_type')
    notes = request.form.get('notes')

    if not all([job_title, property_address, date_str, time_str, duration]):
        print(f"Missing fields: Job Title: {job_title}, Property Address: {property_address}, Date: {date_str}, Time: {time_str}, Duration:: {duration}")
        teardown_db()
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        job_date = date.fromisoformat(date_str)
        job_time = time.fromisoformat(time_str)
    except ValueError:
        teardown_db()
        return jsonify({'error': 'Invalid date or time format'}), 400

    property_obj = job_service.get_property_by_address(property_address)
    if not property_obj:
        property_obj = job_service.create_property(property_address)

    updated_job_data = {
        'job_title': job_title,
        'date': job_date,
        'time': job_time,
        'duration': duration,
        'description': notes,
        'assigned_cleaners': "assigned_cleaner_id",
        'job_type': job_type,
        'property_id': property_obj.id
    }
    updated_job = job_service.update_job(job_id, updated_job_data)
    teardown_db()

    if updated_job:
        # Fetch the updated job details for the modal
        job = job_service.get_job_details(job_id)
        job.assigned_cleaners_list = job.assigned_cleaners.split(',') if job.assigned_cleaners else []
        
        # Render job details for the modal
        job_details_html = render_template('job_details_modal_content.html', job=job)
        
        # Re-fetch all jobs to ensure the list is up-to-date
        all_jobs = job_service.get_all_jobs() 
        job_list_html = render_template('job_list_fragment.html', jobs=all_jobs)
        
        # Combine them with OOB swap attributes
        response_html = f'<div hx-swap-oob="innerHTML:#job-details-modal-content">{job_details_html}</div>' \
                        f'<div id="job-list" hx-swap-oob="outerHTML:#job-list">{job_list_html}</div>'
        
        return response_html

    return jsonify({'error': 'Failed to update job'}), 500

def get_job_update_form(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    user_service = UserService(db)
    job = job_service.get_job_details(job_id)
    cleaners = user_service.get_users_by_role('cleaner')
    teardown_db()
    if job:
        return render_template('job_update_form.html', job=job, cleaners=cleaners)
    return jsonify({'error': 'Job not found'}), 404

def create_job():
    if current_user.role != 'owner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    
    job_title = request.form.get('job_title')
    property_address = request.form.get('property_address')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    duration = request.form.get('duration')
    assigned_cleaner_id = request.form.get('assigned_cleaner_id')
    job_type = request.form.get('job_type')
    notes = request.form.get('notes')

    if not all([job_title, property_address, date_str, time_str, duration]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        job_date = date.fromisoformat(date_str)
        job_time = time.fromisoformat(time_str)
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400

    property_obj = job_service.get_property_by_address(property_address)
    if not property_obj:
        property_obj = job_service.create_property(property_address)

    new_job_data = {
        'job_title': job_title,
        'is_complete': False,
        'date': job_date,
        'time': job_time,
        'duration': duration,
        'description': notes,
        'assigned_cleaners': assigned_cleaner_id,
        'job_type': job_type,
        'property_id': property_obj.id
    }
    new_job = job_service.create_job(new_job_data)
    
    # Get all jobs to re-render the entire job list
    jobs = job_service.get_all_jobs()
    teardown_db()

    if new_job:
        return render_template('job_list_fragment.html', jobs=jobs)
    return jsonify({'error': 'Failed to create job'}), 500


def delete_job(job_id):
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    job_service = JobService(db)
    success = job_service.delete_job(job_id)
    if success:
        jobs = job_service.get_all_jobs()
        teardown_db()
        return render_template('job_list_fragment.html', jobs=jobs)
    
    teardown_db()
    return jsonify({'error': 'Job not found'}), 404