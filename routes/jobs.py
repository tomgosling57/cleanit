from flask import Blueprint
from flask_login import login_required
from controllers import jobs_controller
from database import teardown_db

job_bp = Blueprint('job', __name__, url_prefix='/jobs')

@job_bp.teardown_request
def teardown_job_db(exception=None):
    teardown_db(exception)

@job_bp.route('/assigned')
@login_required
def cleaner_jobs():
    return jobs_controller.cleaner_jobs()

@job_bp.route('/job/<int:job_id>/update_status', methods=['POST'])
@login_required
def update_job_status(job_id):
    return jobs_controller.update_job_status(job_id)

@job_bp.route('/job/<int:job_id>/details', methods=['GET'])
@login_required
def get_job_details(job_id):
    return jobs_controller.get_job_details(job_id)