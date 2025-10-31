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
    pass

@properties_bp.route('/', methods=['POST'])
def add_property():
    """
    Route to create a new property.
    """
    pass

@properties_bp.route('/<int:property_id>', methods=['PUT'])
def update_property_route(property_id):
    """
    Route to update an existing property.
    """
    pass

@properties_bp.route('/<int:property_id>', methods=['DELETE'])
def delete_property_route(property_id):
    """
    Route to delete a property.
    """
    pass