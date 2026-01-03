import os
from flask import Blueprint, send_from_directory, current_app, jsonify
from werkzeug.exceptions import NotFound

storage_bp = Blueprint('storage', __name__)

@storage_bp.route('/uploads/<path:filename>')
def serve_file(filename):
    if os.environ.get('STORAGE_PROVIDER') == 's3':
        return jsonify({"error": "File serving not available when STORAGE_PROVIDER is 's3'"}), 404

    upload_folder = current_app.config.get('UPLOAD_FOLDER', './uploads')
    try:
        return send_from_directory(upload_folder, filename)
    except (FileNotFoundError, NotFound):
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500