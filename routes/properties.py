from flask import Blueprint, jsonify, request
from controllers import property_controller
properties_bp = Blueprint('properties', __name__, url_prefix='/address-book')

@properties_bp.route('/', methods=['GET'])
def get_properties():
    """
    Route to get all properties.
    """
    return property_controller.get_properties()

@properties_bp.route('/<int:property_id>', methods=['GET'])
def get_property(property_id):
    """
    Route to get a single property by ID.
    """
    return property_controller.get_property_by_id(property_id)

@properties_bp.route('/', methods=['POST'])
def add_property():
    """
    Route to create a new property.
    """
    property_data = request.get_json()
    return property_controller.create_property(property_data)

@properties_bp.route('/<int:property_id>', methods=['PUT'])
def update_property_route(property_id):
    """
    Route to update an existing property.
    """
    property_data = request.get_json()
    return property_controller.update_property(property_id, property_data)

@properties_bp.route('/<int:property_id>', methods=['DELETE'])
def delete_property_route(property_id):
    """
    Route to delete a property.
    """
    pass