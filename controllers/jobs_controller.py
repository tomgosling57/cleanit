from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from services.job_service import JobService
from database import get_db, teardown_db

def cleaner_jobs():
    if current_user.role != 'cleaner':
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    db = get_db()
    job_service = JobService(db)
    jobs = job_service.get_cleaner_jobs_for_today(current_user.id)
    teardown_db()

    return render_template('job_cards.html', jobs=jobs, current_user=current_user)

def update_job_status(job_id):
    if current_user.role != 'cleaner':
        return jsonify({'error': 'Unauthorized'}), 403

    status = request.form.get('status')
    if not status:
        return jsonify({'error': 'Status is required'}), 400

    db = get_db()
    job_service = JobService(db)
    job = job_service.update_job_status(job_id, status)
    teardown_db()

    if job:
        return jsonify({'message': 'Job status updated successfully', 'status': job.status})
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