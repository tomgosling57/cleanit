"""
Error handlers for the Flask application.
Centralized error handling for media-related and other exceptions.
"""

import os
from datetime import datetime
from flask import current_app, request, Response, jsonify, render_template, send_from_directory, flash, redirect, url_for
from flask_wtf.csrf import CSRFError
from services.media_service import MediaNotFound
from config import DATETIME_FORMATS
from .timezone import format_in_app_tz, utc_now


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


def register_general_error_handlers(app, login_manager):
    """
    Register global error handlers for general HTTP errors (404, 500, etc.).
    Should be called during application factory setup.
    
    Args:
        app: Flask application instance
        login_manager: Flask-Login LoginManager instance
    """
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """
        Global handler for CSRF token errors.
        
        Behavior:
        - Log the error as a warning.
        - Check if token expired vs missing and flash appropriate message.
        - Redirect to login page for unauthenticated users, or to referrer/index.
        """
        # Log the error
        current_app.logger.warning(f"CSRFError: {e.description}")
        
        # Determine error type and flash appropriate message
        if "expired" in e.description.lower():
            flash("Your session expired. Please refresh the page and try again.", "warning")
        else:
            flash("CSRF token missing. Please refresh the page and try again.", "danger")
        
        # Redirect to login page for unauthenticated users, or to referrer/index
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for('user.login'))
        
        # For authenticated users, redirect to referrer or index
        return redirect(request.referrer or url_for('job.timetable'))
    
    @app.errorhandler(404)
    def handle_404(error):
        """
        Global handler for 404 Not Found errors.
        
        Behavior:
        - Log the error as a warning.
        - Check if user is authenticated. If not, invoke login manager's unauthorized handler.
        - If the request accepts JSON, return a JSON error response with 404.
        - Otherwise (UI request), render the dedicated 404 page template.
        """
        # Log the error
        current_app.logger.warning(f"404 Not Found: {request.path} - {error}")
        
        # Check if user is not authenticated
        from flask_login import current_user
        if not current_user.is_authenticated:
            # Invoke the login manager's unauthorized handler directly
            # This will trigger the redirect to login page
            return login_manager.unauthorized()
        
        # UI response - render dedicated 404 page for authenticated users
        return render_template('not_found.html',
                               debug=app.debug,
                               now=format_in_app_tz(utc_now(), "%Y-%m-%d %H:%M:%S"),
                               suggestion="Check the URL for typos or navigate using the links above.",
                               DATETIME_FORMATS=DATETIME_FORMATS), 404
    
    @app.errorhandler(500)
    def handle_500(error):
        """
        Global handler for 500 Internal Server Error.
        
        Behavior:
        - Log the error as an error.
        - If the request accepts JSON, return a JSON error response with 500.
        - Otherwise (UI request), render a generic error template.
        """
        # Log the error
        current_app.logger.error(f"500 Internal Server Error: {error}")
        
        # JSON response for API requests
        if request.accept_mimetypes.accept_json:
            return jsonify({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred on the server."
            }), 500
        
        # UI response - render generic error template
        return render_template('error.html',
                               error_title="Internal Server Error",
                               error_message="An unexpected error occurred. Please try again later.",
                               status_code=500,
                               suggestion="If the problem persists, contact the administrator."), 500