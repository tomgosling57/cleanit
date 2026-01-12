from flask import Blueprint, request
from flask_login import login_required
from controllers.property_controller import PropertyController
from database import get_db, teardown_db
from services.property_service import PropertyService
from services.job_service import JobService
from services.media_service import MediaService

properties_bp = Blueprint('properties', __name__, url_prefix='/address-book')

@properties_bp.teardown_request
def teardown_property_db(exception=None):
    teardown_db(exception)

def get_property_controller():
    """Create and return a PropertyController instance with request-level database session."""
    db_session = get_db()
    property_service = PropertyService(db_session)
    job_service = JobService(db_session)
    media_service = MediaService(db_session)
    controller = PropertyController(
        property_service=property_service,
        job_service=job_service,
        media_service=media_service
    )
    return controller

@properties_bp.route('/', methods=['GET'])
@login_required
def properties_collection():
    controller = get_property_controller()
    return controller.get_properties_view()

@properties_bp.route('/property/create', methods=['GET', 'POST'])
@login_required
def create_property_route():
    controller = get_property_controller()
    if request.method == 'POST':
        return controller.create_property()
    return controller.get_property_creation_form()

@properties_bp.route('/property/<int:property_id>/details', methods=['GET'])
@login_required
def get_property_details(property_id):
    controller = get_property_controller()
    return controller.get_property_by_id(property_id)

@properties_bp.route('/property/<int:property_id>/jobs', methods=['GET'])
@login_required
def get_property_jobs_route(property_id):
    controller = get_property_controller()
    return controller.get_property_jobs_modal_content(property_id)

@properties_bp.route('/property/<int:property_id>/update', methods=['GET', 'PUT'])
@login_required
def update_property_route(property_id):
    controller = get_property_controller()
    if request.method == 'PUT':
        return controller.update_property(property_id)
    return controller.get_property_update_form(property_id)

@properties_bp.route('/property/<int:property_id>/delete', methods=['DELETE'])
@login_required
def delete_property_route(property_id):
    controller = get_property_controller()
    return controller.delete_property(property_id)

# ========== PROPERTY MEDIA GALLERY ENDPOINTS ==========

@properties_bp.route('/property/<int:property_id>/media', methods=['GET'])
@login_required
def get_property_gallery(property_id):
    """GET /properties/<property_id>/media - Get all media for property"""
    controller = get_property_controller()
    return controller.get_property_gallery(property_id)

@properties_bp.route('/property/<int:property_id>/media', methods=['POST'])
@login_required
def add_property_media(property_id):
    """POST /properties/<property_id>/media - Add media to property (single or batch)"""
    controller = get_property_controller()
    return controller.add_property_media(property_id)

@properties_bp.route('/property/<int:property_id>/media', methods=['DELETE'])
@login_required
def remove_property_media(property_id):
    """DELETE /properties/<property_id>/media - Remove media from property (batch)"""
    controller = get_property_controller()
    return controller.remove_property_media(property_id)

@properties_bp.route('/property/<int:property_id>/media/<int:media_id>', methods=['DELETE'])
@login_required
def remove_single_property_media(property_id, media_id):
    """DELETE /properties/<property_id>/media/<media_id> - Remove single media from property"""
    controller = get_property_controller()
    return controller.remove_single_property_media(property_id, media_id)
