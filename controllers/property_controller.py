from flask import current_app, jsonify, render_template, session, url_for, request, flash, render_template_string, Response, abort
from werkzeug.exceptions import NotFound
from flask_login import current_user
from services.property_service import PropertyService
from services.job_service import JobService
from services.media_service import MediaService
from config import DATETIME_FORMATS
from utils.timezone import parse_to_utc


class PropertyController:
    """Controller class for property-related operations with dependency injection."""
    
    def __init__(self, property_service: PropertyService, job_service: JobService,
                 media_service: MediaService = None):
        """
        Initialize the controller with injected service dependencies.
        
        Args:
            property_service: Service for property operations
            job_service: Service for job operations
            media_service: Service for media operations (optional for backward compatibility)
        """
        self.property_service = property_service
        self.job_service = job_service
        self.media_service = media_service

    def get_properties_view(self):
        """
        Retrieve all properties and render them in a view.
        Access restricted to admin users only.
        """
        if not current_user.is_authenticated or current_user.role != 'admin':
            # Return 404 Not Found for non-admin users
            raise NotFound()
        
        properties = self.property_service.get_all_properties()
        return render_template('properties.html', properties=properties, view_type='property', DATETIME_FORMATS=DATETIME_FORMATS)

    def get_property_by_id(self, property_id):
        """
        Retrieve a single property by its ID.
        """
        property = self.property_service.get_property_by_id(property_id)
        if property:
            return jsonify({'property': property.__repr__()}), 200
        return jsonify({'error': 'Property not found'}), 404

    def get_property_jobs_modal_content(self, property_id):
        """
        Renders the modal content for displaying jobs associated with a property.
        """
        from utils.timezone import today_in_app_tz
        from datetime import timedelta
        
        session['property_id'] = property_id
        property = self.property_service.get_property_by_id(property_id)
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        # Calculate default dates (today to today+30 in application timezone)
        today_app_tz = today_in_app_tz()
        default_start_date = today_app_tz
        default_end_date = today_app_tz + timedelta(days=30)
        
        # Format dates for HTML date inputs (using configured DATE_FORMAT)
        default_start_date_str = default_start_date.isoformat()
        default_end_date_str = default_end_date.isoformat()
        
        # Get jobs with default filters (hide past jobs, show completed)
        jobs = self.job_service.get_filtered_jobs_by_property_id(
            property_id=property_id,
            start_date=default_start_date,
            end_date=default_end_date,
            show_past_jobs=False,
            show_completed=True
        )
        
        # Pass jobs and DATETIME_FORMATS to the timetable fragment
        return render_template('property_jobs_modal.html',
                               property=property,
                               property_id=property.id,
                               jobs=jobs,
                               DATETIME_FORMATS=DATETIME_FORMATS,
                               default_start_date=default_start_date_str,
                               default_end_date=default_end_date_str,
                               show_date_dividers=True,
                               show_past=False,
                               show_completed=True,
                               filter_applied=False,
                               display_start_date=default_start_date.strftime(DATETIME_FORMATS["DATE_FORMAT"]),
                               display_end_date=default_end_date.strftime(DATETIME_FORMATS["DATE_FORMAT"]))

    def get_filtered_property_jobs(self, property_id):
        """
        Renders filtered job list for a property based on query parameters.
        
        Supports:
        - start_date: Start date in YYYY-MM-DD format (application timezone)
        - end_date: End date in YYYY-MM-DD format (application timezone)
        - show_past: Boolean flag to show past jobs (default: false)
        - show_completed: Boolean flag to show completed jobs (default: true)
        """
        jobs = self._get_filtered_property_jobs(property_id)        
        # Render job list fragment with date divider context
        return render_template(
            'job_list_fragment.html',
            jobs=jobs,
            show_date_dividers=True,
            property_id=property_id,
            DATETIME_FORMATS=DATETIME_FORMATS,
            view_type=None  # Ensure view_type is passed (optional)
        )

    def _get_filtered_property_jobs(self, property_id):
        """
        Internal method to get filtered jobs for a property based on query parameters.
        This method is used by both the modal content and the AJAX endpoint.
        """
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        show_past_jobs = request.args.get('show_past', 'false').lower() == 'true'
        show_completed = request.args.get('show_completed', 'true').lower() == 'true'
        
        # Parse dates in application timezone
        start_date = parse_to_utc(start_date_str, DATETIME_FORMATS['ISO_DATE_FORMAT']) if start_date_str else None
        end_date = parse_to_utc(end_date_str, DATETIME_FORMATS['ISO_DATE_FORMAT']) if end_date_str else None
        
        # Get filtered jobs from service
        jobs = self.job_service.get_filtered_jobs_by_property_id(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            show_past_jobs=show_past_jobs,
            show_completed=show_completed
        )
                
        return jobs
    
    def _get_app_timezone(self):
        """Helper to get application timezone from config."""
        from flask import current_app
        return current_app.config.get('APP_TIMEZONE', 'UTC')

    def get_property_creation_form(self):
        """
        Renders the property creation form.
        """
        return render_template('property_creation_modal.html', DATETIME_FORMATS=DATETIME_FORMATS)

    def create_property(self):
        """
        Create a new property.
        """
        address = request.form.get('address')
        access_notes = request.form.get('access_notes')
        notes = request.form.get('notes')

        if not address:
            return render_template_string('{% include "_form_response.html" with messages=["Address is required."] %}')

        property_data = {
            'address': address,
            'access_notes': access_notes,
            'notes': notes
        }

        new_property = self.property_service.create_property(property_data)
        
        if new_property:
            properties = self.property_service.get_all_properties()
            return render_template_string('{% include "property_list_fragment.html" %}', properties=properties)
        
        return render_template_string('{% include "_form_response.html" with messages=["Failed to create property."] %}')

    def get_property_update_form(self, property_id):
        """
        Renders the property update form for a given property ID.
        """
        property = self.property_service.get_property_by_id(property_id)
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        return render_template('property_update_modal.html', property=property, DATETIME_FORMATS=DATETIME_FORMATS)

    def update_property(self, property_id):
        """
        Update an existing property.
        """
        address = request.form.get('address')

        if not address:
            return render_template_string('{% include "_form_response.html" with messages=["Address is required."] %}')

        property_data = {
            'address': address,
            'access_notes': request.form.get('access_notes'),
            'notes': request.form.get('notes')
        }

        updated_property = self.property_service.update_property(property_id, property_data)
        
        if updated_property:
            return render_template_string('{% include "property_card.html" %}', property=updated_property)
        
        return render_template_string('{% include "_form_response.html" with messages=["Failed to update property."] %}')

    def delete_property(self, property_id):
        """
        Delete a property.
        """
        success = self.property_service.delete_property(property_id)
        
        if success:
            properties = self.property_service.get_all_properties()
            return render_template_string('{% include "property_list_fragment.html" %}', properties=properties)
        
        return jsonify({'error': 'Failed to delete property'}), 500

    # ========== MEDIA GALLERY METHODS ==========

    def get_property_gallery(self, property_id):
        """
        GET /properties/<property_id>/media - Get all media for property
        
        Args:
            property_id (int): The property ID
            
        Returns:
            JSON response with media list or error
        """
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Check if user has access to this property
        # For now, only admin and supervisor can view property media
        if current_user.role not in ['admin', 'supervisor']:
            return jsonify({'error': 'Unauthorized: Admin or supervisor access required'}), 403
        
        if not self.media_service:
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            media_items = self.media_service.get_media_for_property(property_id)
            formatted_media = [self._format_media_response(media) for media in media_items]
            return jsonify({
                'success': True,
                'property_id': property_id,
                'media': formatted_media,
                'count': len(formatted_media)
            }), 200
        except Exception as e:
            return jsonify({'error': f'Failed to retrieve property gallery: {str(e)}'}), 500

    def add_property_media(self, property_id):
        """
        POST /properties/<property_id>/media - Upload and associate media with property
        
        This endpoint handles file uploads directly to property gallery.
        Files are uploaded, stored, and automatically associated with the property.
        
        Args:
            property_id (int): The property ID
            
        Returns:
            JSON response with success/error and uploaded media details
        """
        from flask import current_app
        
        if not current_user.is_authenticated or current_user.role != 'admin':
            current_app.logger.warning(f"Unauthorized attempt to add media to property {property_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            return jsonify({'error': 'Unauthorized: Admin access required'}), 403
        
        if not self.media_service:
            current_app.logger.error("Media service not available in property controller")
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if property exists
            property = self.property_service.get_property_by_id(property_id)
            if not property:
                current_app.logger.warning(f"Property {property_id} not found")
                return jsonify({'error': 'Property not found'}), 404
            
            # Check content type - must be multipart/form-data for file uploads
            content_type = request.content_type or ''
            current_app.logger.debug(f"Content-Type: {content_type}")
            current_app.logger.debug(f"Request method: {request.method}")
            current_app.logger.debug(f"Request headers: {dict(request.headers)}")
            
            if 'multipart/form-data' not in content_type:
                current_app.logger.warning(f"Invalid content type for property {property_id} upload: {content_type}")
                return jsonify({'error': 'Content type must be multipart/form-data for file uploads'}), 400
            
            # Check if files are present
            current_app.logger.debug(f"Request files keys: {list(request.files.keys())}")
            current_app.logger.debug(f"Request form keys: {list(request.form.keys())}")
            
            if 'files[]' not in request.files and 'file' not in request.files:
                current_app.logger.warning(f"No files provided in request for property {property_id}")
                return jsonify({'error': 'No files provided in request'}), 400
            
            # Get files - support both 'files[]' array and single 'file'
            files = []
            if 'files[]' in request.files:
                files = request.files.getlist('files[]')
                current_app.logger.debug(f"Found {len(files)} files in 'files[]' array")
            elif 'file' in request.files:
                files = [request.files['file']]
                current_app.logger.debug(f"Found single file 'file'")
            
            if not files or all(file.filename == '' for file in files):
                current_app.logger.warning(f"No selected files for property {property_id}")
                return jsonify({'error': 'No selected files'}), 400
            
            current_app.logger.debug(f"Processing {len(files)} files for property {property_id}")
            
            # Get descriptions - support both 'descriptions[]' array and single 'description'
            descriptions = []
            if 'descriptions[]' in request.form:
                descriptions = request.form.getlist('descriptions[]')
                current_app.logger.debug(f"Found {len(descriptions)} descriptions in 'descriptions[]' array")
            elif 'description' in request.form:
                descriptions = [request.form['description']]
                current_app.logger.debug(f"Found single description 'description'")
            else:
                # Use filenames as descriptions
                descriptions = [file.filename for file in files]
                current_app.logger.debug(f"Using filenames as descriptions")
            
            # Ensure we have enough descriptions
            while len(descriptions) < len(files):
                descriptions.append(files[len(descriptions)].filename)
            
            # Import media utilities
            from utils.media_utils import (
                identify_file_type,
                validate_media,
                upload_media_to_storage,
                get_media_url,
                extract_metadata
            )
            
            uploaded_media = []
            media_ids = []
            
            for i, file in enumerate(files):
                try:
                    if not file or file.filename == '':
                        current_app.logger.debug(f"Skipping empty file at index {i}")
                        continue
                    
                    current_app.logger.debug(f"Processing file {i}: {file.filename}, size: {file.content_length}")
                    
                    # Identify file type
                    file.seek(0)
                    media_type, mime_type = identify_file_type(file)
                    current_app.logger.debug(f"File {file.filename} identified as {media_type} ({mime_type})")
                    
                    # Validate media
                    file.seek(0)
                    validate_media(file, media_type)
                    current_app.logger.debug(f"File {file.filename} validation passed")
                    
                    # Upload to storage
                    file.seek(0)
                    filename = upload_media_to_storage(file, file.filename, media_type)
                    current_app.logger.debug(f"File {file.filename} uploaded to storage as {filename}")
                    
                    # Get file size
                    file.seek(0, 2)  # Seek to end
                    size_bytes = file.tell()
                    file.seek(0)  # Reset
                    current_app.logger.debug(f"File {file.filename} size: {size_bytes} bytes")
                    
                    # Extract metadata if available
                    metadata = {}
                    try:
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                            file.save(tmp.name)
                            tmp_path = tmp.name
                            metadata = extract_metadata(tmp_path, media_type)
                            os.unlink(tmp_path)
                        current_app.logger.debug(f"Extracted metadata for {file.filename}: {metadata}")
                    except Exception as e:
                        # Metadata extraction is optional
                        current_app.logger.debug(f"Metadata extraction failed for {file.filename}: {str(e)}")
                    
                    # Create media record
                    description = descriptions[i] if i < len(descriptions) else file.filename
                    media = self.media_service.add_media(
                        file_name=file.filename,
                        file_path=filename,
                        media_type=media_type,
                        mimetype=mime_type,
                        size_bytes=size_bytes,
                        description=description,
                        metadata=metadata
                    )
                    
                    uploaded_media.append(media)
                    media_ids.append(media.id)
                    current_app.logger.debug(f"Created media record ID {media.id} for {file.filename}")
                    
                except ValueError as e:
                    # Skip invalid files but continue with others
                    current_app.logger.warning(f"File {file.filename if file else 'unknown'} validation failed: {str(e)}")
                    continue
                except Exception as e:
                    # Skip files that fail to upload but continue with others
                    current_app.logger.error(f"File {file.filename if file else 'unknown'} upload failed: {str(e)}")
                    continue
            
            if not media_ids:
                current_app.logger.error(f"No files could be uploaded for property {property_id}")
                return jsonify({'error': 'No files could be uploaded'}), 400
            
            # Associate uploaded media with property
            associations = self.media_service.associate_media_batch_with_property(
                property_id, media_ids
            )
            current_app.logger.debug(f"Associated {len(associations)} media items with property {property_id}")
            
            # Prepare response with uploaded media details
            media_details = []
            for media in uploaded_media:
                media_url = get_media_url(media.file_path) if media.file_path else None
                media_details.append({
                    'id': media.id,
                    'filename': media.filename,
                    'url': media_url,
                    'media_type': media.media_type,
                    'mimetype': media.mimetype,
                    'size_bytes': media.size_bytes,
                    'description': media.description
                })
            
            current_app.logger.info(f"Successfully uploaded and associated {len(uploaded_media)} files with property {property_id}")
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded and associated {len(uploaded_media)} files with property',
                'property_id': property_id,
                'media_ids': media_ids,
                'media': media_details,
                'association_count': len(associations)
            }), 200
                
        except Exception as e:
            current_app.logger.error(f"Failed to add media to property {property_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to add media to property: {str(e)}'}), 500

    def remove_property_media(self, property_id):
        """
        DELETE /properties/<property_id>/media - Remove media from property (batch)
        
        Args:
            property_id (int): The property ID
            
        Returns:
            JSON response with success/error
        """
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized: Admin access required'}), 403
        
        if not self.media_service:
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if property exists
            property = self.property_service.get_property_by_id(property_id)
            if not property:
                return jsonify({'error': 'Property not found'}), 404
            
            # Get media IDs from request JSON
            data = request.get_json()
            if not data or 'media_ids' not in data:
                return jsonify({'error': 'Missing media_ids in request body'}), 400
            
            media_ids = data['media_ids']
            if not isinstance(media_ids, list):
                return jsonify({'error': 'media_ids must be a list'}), 400
            
            # Batch disassociate media from property
            result = self.media_service.disassociate_media_batch_from_property(property_id, media_ids)
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': f'Failed to remove media from property: {str(e)}'}), 500

    def remove_single_property_media(self, property_id, media_id):
        """
        DELETE /properties/<property_id>/media/<media_id> - Remove single media from property
        
        Args:
            property_id (int): The property ID
            media_id (int): The media ID
            
        Returns:
            JSON response with success/error
        """
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized: Admin access required'}), 403
        
        if not self.media_service:
            return jsonify({'error': 'Media service not available'}), 500
        
        try:
            # Check if property exists
            property = self.property_service.get_property_by_id(property_id)
            if not property:
                return jsonify({'error': 'Property not found'}), 404
            
            # Remove single association
            success = self.media_service.remove_association_from_property(media_id, property_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Media removed from property successfully',
                    'property_id': property_id,
                    'media_id': media_id
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Association not found'
                }), 404
        except Exception as e:
            return jsonify({'error': f'Failed to remove media from property: {str(e)}'}), 500

    def _format_media_response(self, media):
        """
        Format a media object for JSON response.
        
        Args:
            media: Media object
            
        Returns:
            dict: Formatted media data
        """
        from utils.media_utils import get_media_url
        
        media_url = get_media_url(media.file_path) if media.file_path else None
        
        return {
            'id': media.id,
            'filename': media.filename,
            'url': media_url,
            'media_type': media.media_type,
            'mimetype': media.mimetype,
            'size_bytes': media.size_bytes,
            'description': media.description,
            'width': media.width,
            'height': media.height,
            'duration_seconds': media.duration_seconds,
            'thumbnail_url': media.thumbnail_url,
            'resolution': media.resolution,
            'codec': media.codec,
            'aspect_ratio': media.aspect_ratio,
            'upload_date': media.upload_date.isoformat() if media.upload_date else None
        }
