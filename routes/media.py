"""
Media routes for handling media-related API endpoints.
"""
from flask import Blueprint, request, g
from flask_login import login_required
from database import get_db, teardown_db
from services.media_service import MediaService
from controllers.media_controller import MediaController

media_bp = Blueprint('media', __name__, url_prefix='/media')

@media_bp.teardown_request
def teardown_media_db(exception=None):
    """Ensure database session is torn down after each request."""
    teardown_db(exception)

def get_media_controller():
    """
    Create and return a MediaController instance with request-level database session.
    
    Returns:
        MediaController: Controller instance with MediaService dependency
    """
    db_session = get_db()
    media_service = MediaService(db_session)
    controller = MediaController(media_service=media_service)
    return controller

@media_bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """Handle POST /media/upload - upload media file."""
    controller = get_media_controller()
    return controller.upload_media()

@media_bp.route('/<int:media_id>', methods=['GET'])
def get_media(media_id):
    """Handle GET /media/<media_id> - retrieve media metadata."""
    controller = get_media_controller()
    return controller.get_media(media_id)

@media_bp.route('/serve/<path:filename>', methods=['GET'])
def serve_media(filename):
    """Handle GET /media/serve/<path:filename> - serve media file."""
    controller = get_media_controller()
    return controller.serve_media(filename)

@media_bp.route('/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """Handle DELETE /media/<media_id> - delete media."""
    controller = get_media_controller()
    return controller.delete_media(media_id)
