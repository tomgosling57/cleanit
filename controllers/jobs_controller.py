from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from services.job_service import JobService
from services.user_service import UserService
from database import get_db, teardown_db
from datetime import date, time

def cleaner_jobs():
    if current_user.role != 'cleaner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    jobs = job_service.get_cleaner_jobs_for_today(current_user.id)
    teardown_db()

    return Response(render_template('timetable.html', jobs=jobs, current_user=current_user), content_type="text/html")

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

def manage_jobs():
    if current_user.role != 'owner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    user_service = UserService(db)

    jobs = job_service.get_all_jobs() # Assuming a method to get all jobs
    cleaners = user_service.get_users_by_role('cleaner')
    teardown_db()
    return render_template('timetable.html', jobs=jobs, current_user=current_user, cleaners=cleaners)

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
    teardown_db()

    if new_job:
        return render_template('job_card.html', job=new_job, is_oob_swap=False)
    return jsonify({'error': 'Failed to create job'}), 500
