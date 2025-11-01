from flask import Blueprint, jsonify, request
from flask_login import login_required
from controllers import property_controller

properties_bp = Blueprint('properties', __name__, url_prefix='/address-book')

@properties_bp.route('/', methods=['GET'])
@login_required
def get_properties_view():
    """
    Route to display all properties in a view.
    """
    return property_controller.get_properties_view()

@properties_bp.route('/<int:property_id>', methods=['GET'])
@login_required
def get_property(property_id):
    """
    Route to get a single property by ID.
    """
    return property_controller.get_property_by_id(property_id)

@properties_bp.route('/', methods=['POST'])
@login_required
def add_property():
    """
    Route to create a new property.
    """
    property_data = request.get_json()
    return property_controller.create_property(property_data)

@properties_bp.route('/<int:property_id>', methods=['PUT'])
@login_required
def update_property(property_id):
    """
    Route to update an existing property.
    """
    property_data = request.get_json()
    return property_controller.update_property(property_id, property_data)

@properties_bp.route('/<int:property_id>', methods=['DELETE'])
@login_required
def delete_property(property_id):
    """
    Route to delete a property.
    """
    return property_controller.delete_property(property_id)