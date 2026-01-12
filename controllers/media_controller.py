"""
Media controller for handling media-related API endpoints.
Handles upload, retrieval, serving, and deletion of media.
Note: Media associations with properties and jobs are now handled by their respective controllers.
"""
from flask import request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from services.media_service import MediaService, MediaNotFound
from utils.media_utils import (
    identify_file_type,
    validate_media,
    upload_media_to_storage,
    delete_media_from_storage,
    get_media_url,
    extract_metadata,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_VIDEO,
    MEDIA_TYPE_DOCUMENT,
    MEDIA_TYPE_AUDIO
)
import logging

logger = logging.getLogger(__name__)


class MediaController:
    """
    Controller class for media operations with dependency injection.
    
    Args:
        media_service (MediaService): Service for media database operations
    """
    
    def __init__(self, media_service: MediaService):
        self.media_service = media_service
    
    def upload_media(self):
        """
        Handle POST /media/upload endpoint.
        Uploads a media file (image, video, document, audio) and creates a Media record.
        
        Returns:
            JSON response with media details or error.
        """
        logger.debug(f"Received upload request. Method: {request.method}")
        
        # Authorization check - only admin can upload
        if current_user.role != 'admin':
            logger.warning(f"Unauthorized upload attempt by user role: {current_user.role}")
            return jsonify({"error": "Unauthorized: Admin access required"}), 403
        
        if request.method != 'POST':
            logger.debug(f"Method not allowed: {request.method}")
            return jsonify({"error": "Method not allowed"}), 405
        
        if 'file' not in request.files:
            logger.debug("No file part in the request.")
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files.get('file')
        if not file or file.filename == '':
            logger.debug("No selected file or empty filename.")
            return jsonify({"error": "No selected file"}), 400
        
        try:
            # Identify file type
            file.seek(0)
            media_type, mime_type = identify_file_type(file)
            logger.debug(f"Identified media type: {media_type}, MIME type: {mime_type}")
            
            # Validate media
            file.seek(0)
            validate_media(file, media_type)
            
            # Upload to storage
            file.seek(0)
            filename = upload_media_to_storage(file, file.filename, media_type)
            
            # Get file size
            file.seek(0, 2)  # Seek to end
            size_bytes = file.tell()
            file.seek(0)  # Reset
            
            # Extract metadata if available
            metadata = {}
            try:
                # For now, we need to save to temp file to extract metadata
                # In production, this could be done differently
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name
                    metadata = extract_metadata(tmp_path, media_type)
                    os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}")
            
            # Get file path (storage utility returns filename, path is derived)
            file_path = filename  # In current storage implementation, filename is used as path
            
            # Create media record
            description = request.form.get('description', None)
            media = self.media_service.add_media(
                file_name=file.filename,
                file_path=file_path,
                media_type=media_type,
                mimetype=mime_type,
                size_bytes=size_bytes,
                description=description,
                metadata=metadata
            )
            
            # Get URL for accessing the media
            media_url = get_media_url(file_path)
            
            logger.info(f"Media uploaded successfully: {filename}, ID: {media.id}")
            return jsonify({
                "message": "Media uploaded successfully",
                "media_id": media.id,
                "filename": media.filename,
                "file_path": media.file_path,
                "media_type": media.media_type,
                "mimetype": media.mimetype,
                "size_bytes": media.size_bytes,
                "url": media_url,
                "description": media.description
            }), 200
            
        except ValueError as e:
            logger.warning(f"Media validation error: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Media upload failed: {e}", exc_info=True)
            return jsonify({"error": "Media upload failed"}), 500
    
    def get_media(self, media_id):
        """
        Handle GET /media/<media_id> endpoint.
        Retrieves metadata for a specific media item.
        
        Args:
            media_id (int): The media ID
            
        Returns:
            JSON response with media metadata or error.
        """
        # MediaNotFound exceptions will propagate to global error handler
        media = self.media_service.get_media_by_id(media_id)
        
        # Get URL for accessing the media
        media_url = get_media_url(media.file_path)
        
        return jsonify({
            "media_id": media.id,
            "filename": media.filename,
            "file_path": media.file_path,
            "media_type": media.media_type,
            "mimetype": media.mimetype,
            "size_bytes": media.size_bytes,
            "upload_date": media.upload_date.isoformat() if media.upload_date else None,
            "description": media.description,
            "width": media.width,
            "height": media.height,
            "duration_seconds": media.duration_seconds,
            "thumbnail_url": media.thumbnail_url,
            "resolution": media.resolution,
            "codec": media.codec,
            "aspect_ratio": media.aspect_ratio,
            "url": media_url
        }), 200
    
    def serve_media(self, filename):
        """
        Handle GET /media/serve/<path:filename> endpoint.
        Serves actual media files, adapting to the configured storage provider.
        
        Args:
            filename (str): The filename to serve
            
        Returns:
            File response or error.
        """
        # This endpoint should be handled by the routes/media.py directly
        # but we keep it here for consistency
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
        except Exception as e:
            # Let the global error handler handle MediaNotFound
            # For other errors, return appropriate response
            current_app.logger.error(f"Error serving file {filename}: {e}")
            return jsonify({"error": "File not found or inaccessible"}), 404
    
    @login_required
    def delete_media(self, media_id):
        """
        Handle DELETE /media/<media_id> endpoint.
        Deletes a media item and its associations from database and storage.
        
        Args:
            media_id (int): The media ID
            
        Returns:
            JSON response with success message or error.
        """
        # Authorization check - only admin can delete
        if current_user.role != 'admin':
            logger.warning(f"Unauthorized delete attempt by user role: {current_user.role}")
            return jsonify({"error": "Unauthorized: Admin access required"}), 403
        
        # MediaNotFound exceptions will propagate to global error handler
        media = self.media_service.get_media_by_id(media_id)
        
        # Delete from storage
        try:
            delete_media_from_storage(media.file_path)
        except Exception as e:
            logger.error(f"Failed to delete media file from storage: {e}")
            # Continue with database deletion anyway
        
        # Delete from database (this will also delete associations via cascade)
        self.media_service.delete_media(media_id)
        
        logger.info(f"Media deleted successfully: ID {media_id}")
        return jsonify({
            "message": "Media deleted successfully",
            "media_id": media_id
        }), 200
