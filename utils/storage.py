import os
import uuid
from datetime import datetime
from flask import url_for, current_app
from werkzeug.utils import secure_filename
from libcloud.storage.types import ObjectDoesNotExistError, ContainerDoesNotExistError
from libcloud.storage.base import StorageDriver

CHUNK_SIZE = 8192 # 8KB Practical Limit

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp',  # images
    'mp4', 'webm', 'ogg', 'mov', 'avi',   # videos
    'mp3', 'wav', 'ogg', 'flac',          # audio
    'pdf', 'doc', 'docx', 'txt',          # documents
}
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
    
    # Log upload information based on storage provider
    storage_provider = current_app.config.get('STORAGE_PROVIDER', 's3')
    if storage_provider == 'local' or storage_provider == 'temp':
        upload_folder = current_app.config.get('UPLOAD_FOLDER', './uploads')
        full_path = os.path.join(upload_folder, unique_filename)
        current_app.logger.debug(f"File '{unique_filename}' uploaded to {storage_provider} storage at: {full_path}")
    else:
        current_app.logger.debug(f"File '{unique_filename}' uploaded to S3 bucket: {current_app.config.get('S3_BUCKET')}")

    return unique_filename


def get_file_url(filename):
    """
    Get URL to access a file. Handles S3, local, and temp storage automatically.

    Args:
        filename: The filename to get URL for

    Returns:
        str: URL to access the file
    """
    driver = current_app.config['STORAGE_DRIVER']
    container = current_app.config['STORAGE_CONTAINER']
    storage_provider = current_app.config.get('STORAGE_PROVIDER', 's3')

    if storage_provider == 's3':
        obj = container.get_object(filename)
        return driver.get_object_cdn_url(obj)
    else:
        # For 'local' and 'temp' providers, use the Flask route to serve files
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
    except (ObjectDoesNotExistError, ContainerDoesNotExistError):
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

    # Identify media type and perform media-specific validation
    try:
        # Import here to avoid circular import with media_utils
        from utils.media_utils import validate_media, identify_file_type
        media_type, mime_type = identify_file_type(flask_file.stream)
        current_app.logger.debug(f"validate_and_upload: Identified media type '{media_type}', mime type '{mime_type}' for {flask_file.filename}")
        
        # Validate media integrity and security
        validate_media(flask_file.stream, media_type)
        current_app.logger.debug(f"validate_and_upload: Media validation passed for {flask_file.filename}")
    except ValueError as e:
        current_app.logger.debug(f"validate_and_upload: Media validation failed for {flask_file.filename}: {e}")
        raise ValueError(f'Media validation failed: {e}')
    except Exception as e:
        current_app.logger.debug(f"validate_and_upload: Unexpected error during media validation for {flask_file.filename}: {e}")
        raise ValueError(f'Media validation error: {e}')

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
    except (ObjectDoesNotExistError, ContainerDoesNotExistError):
        return False