from flask import jsonify, render_template, session, url_for, request, flash, render_template_string, Response, abort
from werkzeug.exceptions import NotFound
from flask_login import current_user
from services.property_service import PropertyService
from services.job_service import JobService
from services.media_service import MediaService
from config import DATETIME_FORMATS


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
        session['property_id'] = property_id
        property = self.property_service.get_property_by_id(property_id)
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        jobs = self.job_service.get_jobs_by_property_id(property_id)
        # Pass jobs and DATETIME_FORMATS to the timetable fragment
        return render_template('property_jobs_modal.html', property=property, jobs=jobs, DATETIME_FORMATS=DATETIME_FORMATS)

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
        POST /properties/<property_id>/media - Add media to property (single or batch)
        
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
            
            if not media_ids:
                return jsonify({'error': 'media_ids list cannot be empty'}), 400
            
            # Validate all media IDs exist
            for media_id in media_ids:
                try:
                    self.media_service.get_media_by_id(media_id)
                except Exception as e:
                    return jsonify({
                        'error': f'Media ID {media_id} not found or invalid: {str(e)}'
                    }), 404
            
            # Batch associate media with property
            associations = self.media_service.associate_media_batch_with_property(
                property_id, media_ids
            )
            
            return jsonify({
                'success': True,
                'message': f'Successfully associated {len(associations)} media items with property',
                'property_id': property_id,
                'media_ids': media_ids,
                'association_count': len(associations)
            }), 200
        except Exception as e:
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
