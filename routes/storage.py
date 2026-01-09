import os
from flask import Blueprint, send_from_directory, current_app, jsonify, request
from werkzeug.exceptions import NotFound
from controllers.storage_controller import upload_file_view

storage_bp = Blueprint('storage', __name__)

@storage_bp.route('/uploads/<path:filename>')
def serve_file(filename):
    storage_provider = current_app.config.get('STORAGE_PROVIDER', 's3')
    
    # Only serve files for local and temp storage providers
    if storage_provider == 's3':
        return jsonify({
            "error": "File serving not available when STORAGE_PROVIDER is 's3'",
            "message": "Files are stored in S3 and should be accessed via S3 URLs"
        }), 404

    upload_folder = current_app.config.get('UPLOAD_FOLDER', './uploads')
    try:
        return send_from_directory(upload_folder, filename)
    except (FileNotFoundError, NotFound):
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@storage_bp.route('/upload', methods=['POST'])
def upload():
    return upload_file_view()