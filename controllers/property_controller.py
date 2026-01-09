from flask import jsonify, render_template, session, url_for, request, flash, render_template_string
from services.property_service import PropertyService
from services.job_service import JobService
from config import DATETIME_FORMATS


class PropertyController:
    """Controller class for property-related operations with dependency injection."""
    
    def __init__(self, property_service: PropertyService, job_service: JobService):
        """
        Initialize the controller with injected service dependencies.
        
        Args:
            property_service: Service for property operations
            job_service: Service for job operations
        """
        self.property_service = property_service
        self.job_service = job_service

    def get_properties_view(self):
        """
        Retrieve all properties and render them in a view.
        """
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

        if not address:
            return render_template_string('{% include "_form_response.html" with messages=["Address is required."] %}')

        property_data = {
            'address': address,
            'access_notes': access_notes
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