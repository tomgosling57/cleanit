from flask import Blueprint, request
from flask_login import login_required
from controllers import jobs_controller
from database import teardown_db

job_bp = Blueprint('job', __name__, url_prefix='/jobs')

@job_bp.teardown_request
def teardown_job_db(exception=None):
    teardown_db(exception)

@job_bp.route('/', methods=['GET'])
@login_required
def timetable():
    date = request.args.get('date')
    return jobs_controller.timetable(date)

@job_bp.route('/job/<int:job_id>/update_status', methods=['POST'])
def update_job_status(job_id):
    return jobs_controller.update_job_status(job_id)

@job_bp.route('/job/<int:job_id>/update', methods=['GET', 'PUT'])
@login_required
def update_job(job_id):
    if request.method == 'PUT':
        return jobs_controller.update_job(job_id)
    else:
        return jobs_controller.get_job_update_form(job_id)

@job_bp.route('/job/<int:job_id>/details', methods=['GET'])
@login_required
def get_job_details(job_id):
    return jobs_controller.get_job_details(job_id)

@job_bp.route('/job/create', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        _return = jobs_controller.create_job()
    else:
        _return = jobs_controller.get_job_creation_form()
    return _return

@job_bp.route('/job/<int:job_id>/delete', methods=['DELETE'])
@login_required
def delete_job(job_id):
    return jobs_controller.delete_job(job_id)

@job_bp.route('/job/<int:job_id>/reassign', methods=['POST'])
@login_required
def reassign_job_team(job_id):
    return jobs_controller.reassign_job_team(job_id)