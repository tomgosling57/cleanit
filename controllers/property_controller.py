from flask import jsonify, render_template, redirect, url_for, request, flash, render_template_string
from services.property_service import PropertyService
from services.job_service import JobService # Import JobService
from database import get_db, teardown_db

def get_properties_view():
    """
    Retrieve all properties and render them in a view.
    """
    db = get_db()
    property_service = PropertyService(db)
    properties = property_service.get_all_properties()
    teardown_db()
    return render_template('properties.html', properties=properties)

def get_property_by_id(property_id):
    """
    Retrieve a single property by its ID.
    """
    db = get_db()
    property_service = PropertyService(db)
    property = property_service.get_property_by_id(property_id)
    teardown_db()
    if property:
        return jsonify({'property': property.__repr__()}), 200
    return jsonify({'error': 'Property not found'}), 404

def get_property_jobs_modal_content(property_id):
    """
    Renders the modal content for displaying jobs associated with a property.
    """
    db = get_db()
    property_service = PropertyService(db)
    job_service = JobService(db)

    property = property_service.get_property_by_id(property_id)
    if not property:
        teardown_db()
        return jsonify({'error': 'Property not found'}), 404
    
    jobs = job_service.get_jobs_by_property_id(property_id)
    teardown_db()
    return render_template('property_jobs_modal_content.html', property=property, jobs=jobs)

def get_property_creation_form():
    """
    Renders the property creation form.
    """
    return render_template('property_creation_modal_content.html')

def create_property():
    """
    Create a new property.
    """
    db = get_db()
    property_service = PropertyService(db)

    address = request.form.get('address')
    access_notes = request.form.get('access_notes')

    if not address:
        teardown_db()
        return render_template_string('{% include "_form_errors.html" with messages=["Address is required."] %}')

    property_data = {
        'address': address,
        'access_notes': access_notes
    }

    new_property = property_service.create_property(property_data)
    
    if new_property:
        properties = property_service.get_all_properties()
        teardown_db()
        return render_template_string('{% include "property_list_fragment.html" %}', properties=properties)
    
    teardown_db()
    return render_template_string('{% include "_form_errors.html" with messages=["Failed to create property."] %}')

def get_property_update_form(property_id):
    """
    Renders the property update form for a given property ID.
    """
    db = get_db()
    property_service = PropertyService(db)
    property = property_service.get_property_by_id(property_id)
    teardown_db()
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    return render_template('property_update_form.html', property=property)

def update_property(property_id):
    """
    Update an existing property.
    """
    db = get_db()
    property_service = PropertyService(db)

    address = request.form.get('address')
    access_notes = request.form.get('access_notes')

    if not address:
        teardown_db()
        return render_template_string('{% include "_form_errors.html" with messages=["Address is required."] %}')

    property_data = {
        'address': address,
        'access_notes': access_notes
    }

    updated_property = property_service.update_property(property_id, property_data)
    
    if updated_property:
        teardown_db()
        return render_template_string('{% include "property_card.html" %}', property=updated_property)
    
    teardown_db()
    return render_template_string('{% include "_form_errors.html" with messages=["Failed to update property."] %}')

def delete_property(property_id):
    """
    Delete a property.
    """
    db = get_db()
    property_service = PropertyService(db)
    success = property_service.delete_property(property_id)
    
    if success:
        properties = property_service.get_all_properties()
        teardown_db()
        return render_template_string('{% include "property_list_fragment.html" %}', properties=properties)
    
    teardown_db()
    return jsonify({'error': 'Failed to delete property'}), 500