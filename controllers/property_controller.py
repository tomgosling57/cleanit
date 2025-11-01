from flask import jsonify, render_template, redirect, url_for
from services.property_service import PropertyService
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

def create_property(property_data):
    """
    Create a new property.
    """
    db = get_db()
    property_service = PropertyService(db)
    new_property = property_service.create_property(property_data)
    teardown_db()
    return redirect(url_for('properties.get_properties_view'))

def update_property(property_id, property_data):
    """
    Update an existing property.
    """
    db = get_db()
    property_service = PropertyService(db)
    updated_property = property_service.update_property(property_id, property_data)
    teardown_db()
    return redirect(url_for('properties.get_properties_view'))

def delete_property(property_id):
    """
    Delete a property.
    """
    db = get_db()
    property_service = PropertyService(db)
    success = property_service.delete_property(property_id)
    teardown_db()
    return redirect(url_for('properties.get_properties_view'))