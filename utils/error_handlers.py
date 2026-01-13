"""
Error handlers for the Flask application.
Centralized error handling for media-related and other exceptions.
"""

import os
from flask import current_app, request, jsonify, render_template, send_from_directory
from services.media_service import MediaNotFound


def register_media_error_handlers(app):
    """
    Register global error handlers for media-related exceptions.
    Should be called during application factory setup.
    """
    @app.errorhandler(MediaNotFound)
    def handle_media_not_found(error):
        """
        Global handler for MediaNotFound exceptions.
        
        Behavior:
        - Log the error as a warning.
        - If the request is for an image (path contains '/uploads/' and ends with image extension),
          serve the placeholder image 'image-not-found.png' with 404 status.
        - If the request accepts JSON, return a JSON error response with 404.
        - Otherwise (UI request), render a generic error template with 404.
        """
        # Log the error
        current_app.logger.warning(f"MediaNotFound: {error}")
        
        # Determine if request is for an image
        is_image_request = False
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
        
        # Check if request path matches media serve route and has image extension
        if request.path.startswith('/media/serve/'):
            # Extract filename and check extension
            filename = os.path.basename(request.path)
            _, ext = os.path.splitext(filename.lower())
            if ext in image_extensions:
                is_image_request = True
        
        # Serve placeholder image for image requests
        if is_image_request:
            placeholder_path = os.path.join(app.static_folder, 'images', 'placeholders', 'image-not-found.png')
            if os.path.exists(placeholder_path):
                return send_from_directory(
                    os.path.dirname(placeholder_path),
                    'image-not-found.png'
                ), 404
            else:
                # Fallback to simple 404
                current_app.logger.error(f"Placeholder image not found at {placeholder_path}")
        
        # JSON response for API requests
        if request.accept_mimetypes.accept_json:
            return jsonify({
                "error": "Media not found",
                "message": str(error)
            }), 404
        
        # UI response - render generic error template
        return render_template('error.html',
                               error_title="Media Not Found",
                               error_message="The requested media could not be found.",
                               status_code=404,
                               suggestion="Please check the media ID or filename and try again."), 404