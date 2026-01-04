from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from utils import storage
import logging

logger = logging.getLogger(__name__)

@login_required
def upload_file_view():
    logger.debug(f"Received upload request. Method: {request.method}")
    if current_user.role != 'admin':
        logger.warning(f"Unauthorized upload attempt by user role: {current_user.role}")
        return jsonify({"error": "Unauthorized: Admin access required"}), 403

    if request.method == 'POST':
        if 'file' not in request.files:
            logger.debug("No file part in the request.")
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files.get('file')
        if not file or file.filename == '':
            logger.debug("No selected file or empty filename.")
            return jsonify({"error": "No selected file"}), 400

        try:
            filename = storage.validate_and_upload(file)
            file_url = storage.get_file_url(filename)
            logger.info(f"File uploaded successfully: {filename}")
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "url": file_url
            }), 200
        except ValueError as e:
            logger.warning(f"File upload validation error: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"File upload failed: {e}", exc_info=True)
            return jsonify({"error": "File upload failed"}), 500
    
    logger.debug(f"Method not allowed: {request.method}")
    return jsonify({"error": "Method not allowed"}), 405