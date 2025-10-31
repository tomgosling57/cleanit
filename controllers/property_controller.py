from flask import jsonify
from services.property_service import PropertyService
from database import get_db, teardown_db

def get_properties():
    """
    Retrieve all properties.
    """
    db = get_db()
    property_service = PropertyService(db)
    properties = property_service.get_all_properties()
    teardown_db()
    return jsonify({'properties': [prop.__repr__() for prop in properties]}), 200

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
    return jsonify({'property': new_property.__repr__()}), 201

def update_property(property_id, property_data):
    """
    Update an existing property.
    """
    pass

def delete_property(property_id):
    """
    Delete a property.
    """
    pass
