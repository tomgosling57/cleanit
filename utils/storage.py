import os
import uuid
from datetime import datetime
from flask import url_for, current_app
from werkzeug.utils import secure_filename
from libcloud.storage.types import ObjectDoesNotExistError
from libcloud.storage.base import StorageDriver

CHUNK_SIZE = 8192 # 8KB Practical Limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_flask_file(flask_file, filename=None):
    """
    Upload a Flask FileStorage object via Libcloud with a unique filename.

    Args:
        flask_file: werkzeug.FileStorage object from request.files
        filename: Optional custom filename (defaults to original filename)

    Returns:
        str: The unique filename that was uploaded
    """
    original_filename = filename or flask_file.filename
    name, ext = os.path.splitext(secure_filename(original_filename))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    unique_filename = f"{name}_{timestamp}_{unique_id}{ext}"

    driver = current_app.config['STORAGE_DRIVER']
    container = current_app.config['STORAGE_CONTAINER']

    container.upload_object_via_stream(
        iterator=flask_file.stream,
        object_name=unique_filename
    )
    
    # Log the full path where the file is expected to be saved
    if current_app.config.get('STORAGE_PROVIDER') == 'local':
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        current_app.logger.debug(f"File '{unique_filename}' uploaded to local path: {full_path}")

    current_app.logger.debug(f"UPLOAD_FOLDER in storage.py: {current_app.config['UPLOAD_FOLDER']}")
    return unique_filename


def get_file_url(filename):
    """
    Get URL to access a file. Handles local vs S3 automatically.

    Args:
        filename: The filename to get URL for

    Returns:
        str: URL to access the file
    """
    driver = current_app.config['STORAGE_DRIVER']
    container = current_app.config['STORAGE_CONTAINER']
    storage_provider = current_app.config.get('STORAGE_PROVIDER', 'local')

    if storage_provider == 's3':
        obj = container.get_object(filename)
        return driver.get_object_cdn_url(obj)
    else:
        return url_for('storage.serve_file', filename=filename, _external=True)


def delete_file(filename):
    """
    Delete a file from storage.

    Args:
        filename: The filename to delete

    Returns:
        bool: True if deleted, False if not found
    """
    driver = current_app.config['STORAGE_DRIVER']
    container = current_app.config['STORAGE_CONTAINER']
    try:
        obj = container.get_object(filename)
        driver.delete_object(obj)
        return True
    except ObjectDoesNotExistError:
        return False

def validate_and_upload(flask_file, filename=None):
    """Validate file before uploading"""
    current_app.logger.debug(f"validate_and_upload called for filename: {flask_file.filename if flask_file else 'None'}")

    if not flask_file:
        current_app.logger.debug("validate_and_upload: No file provided")
        raise ValueError('No file provided')

    if not allowed_file(flask_file.filename):
        current_app.logger.debug(f"validate_and_upload: File type not allowed for {flask_file.filename}")
        raise ValueError('File type not allowed')

    # Check file size (requires reading/seeking)
    flask_file.seek(0, 2)  # Seek to end
    size = flask_file.tell()
    flask_file.seek(0)  # Reset to beginning
    current_app.logger.debug(f"validate_and_upload: File size for {flask_file.filename}: {size} bytes")

    if size > MAX_FILE_SIZE:
        current_app.logger.debug(f"validate_and_upload: File too large for {flask_file.filename}")
        raise ValueError('File too large')

    # Upload if validation passes
    return upload_flask_file(flask_file, filename)


def file_exists(filename):
    """
    Check if a file exists in storage.

    Args:
        filename: The filename to check

    Returns:
        bool: True if exists, False otherwise
    """
    container = current_app.config['STORAGE_CONTAINER']
    try:
        container.get_object(filename)
        return True
    except ObjectDoesNotExistError:
        return False