from flask import Blueprint, request, g
from flask_login import login_required
from database import get_db, teardown_db
from services.job_service import JobService
from services.team_service import TeamService
from services.user_service import UserService
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from services.media_service import MediaService
from utils.job_helper import JobHelper
from controllers.jobs_controller import JobController

job_bp = Blueprint('job', __name__, url_prefix='/jobs')

@job_bp.teardown_request
def teardown_job_db(exception=None):
    teardown_db(exception)

def get_job_controller():
    """Create and return a JobController instance with request-level database session."""
    db_session = get_db()
    job_service = JobService(db_session)
    team_service = TeamService(db_session)
    user_service = UserService(db_session)
    property_service = PropertyService(db_session)
    assignment_service = AssignmentService(db_session)
    media_service = MediaService(db_session)
    job_helper = JobHelper(job_service, team_service, assignment_service)
    controller = JobController(
        job_service=job_service,
        team_service=team_service,
        user_service=user_service,
        property_service=property_service,
        assignment_service=assignment_service,
        job_helper=job_helper,
        media_service=media_service
    )
    return controller

@job_bp.route('/', methods=['GET'])
@login_required
def timetable():
    date = request.args.get('date')
    controller = get_job_controller()
    return controller.timetable(date)

@job_bp.route('/teams/', methods=['GET'])
@login_required
def team_timetable():
    date = request.args.get('date')
    controller = get_job_controller()
    return controller.team_timetable(date)

@job_bp.route('/job/<int:job_id>/update_status', methods=['POST'])
def update_job_status(job_id):
    controller = get_job_controller()
    return controller.update_job_status(job_id)

@job_bp.route('/job/<int:job_id>/update', methods=['GET', 'PUT'])
@login_required
def update_job(job_id):
    controller = get_job_controller()
    if request.method == 'PUT':
        return controller.update_job(job_id)
    else:
        return controller.get_job_update_form(job_id)

@job_bp.route('/job/<int:job_id>/details', methods=['GET'])
@login_required
def get_job_details(job_id):
    controller = get_job_controller()
    return controller.get_job_details(job_id)

@job_bp.route('/job/create', methods=['GET', 'POST'])
@login_required
def create_job():
    controller = get_job_controller()
    if request.method == 'POST':
        _return = controller.create_job()
    else:
        _return = controller.get_job_creation_form()
    return _return

@job_bp.route('/job/<int:job_id>/delete', methods=['DELETE'])
@login_required
def delete_job(job_id):
    view_type = request.args.get('view_type', None)
    controller = get_job_controller()
    return controller.delete_job(job_id, view_type)

@job_bp.route('/job/reassign', methods=['POST'])
@login_required
def reassign_job_team():
    controller = get_job_controller()
    return controller.reassign_job_team()

# ========== JOB MEDIA GALLERY ENDPOINTS ==========

@job_bp.route('/<int:job_id>/media', methods=['GET'])
@login_required
def get_job_gallery(job_id):
    """GET /jobs/<job_id>/media - Get all media for job"""
    controller = get_job_controller()
    return controller.get_job_gallery(job_id)

@job_bp.route('/<int:job_id>/media', methods=['POST'])
@login_required
def add_job_media(job_id):
    """POST /jobs/<job_id>/media - Add media to job (single or batch)"""
    controller = get_job_controller()
    return controller.add_job_media(job_id)

@job_bp.route('/<int:job_id>/media', methods=['DELETE'])
@login_required
def remove_job_media(job_id):
    """DELETE /jobs/<job_id>/media - Remove media from job (batch)"""
    controller = get_job_controller()
    return controller.remove_job_media(job_id)

@job_bp.route('/<int:job_id>/media/<int:media_id>', methods=['DELETE'])
@login_required
def remove_single_job_media(job_id, media_id):
    """DELETE /jobs/<job_id>/media/<media_id> - Remove single media from job"""
    controller = get_job_controller()
    return controller.remove_single_job_media(job_id, media_id)
