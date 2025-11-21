from flask import Blueprint, request
from flask_login import login_required
from controllers import property_controller
from database import teardown_db

properties_bp = Blueprint('properties', __name__, url_prefix='/address-book')

@properties_bp.teardown_request
def teardown_property_db(exception=None):
    teardown_db(exception)

@properties_bp.route('/', methods=['GET'])
@login_required
def properties_collection():
    return property_controller.get_properties_view()

@properties_bp.route('/property/create', methods=['GET', 'POST'])
@login_required
def create_property_route():
    if request.method == 'POST':
        return property_controller.create_property()
    return property_controller.get_property_creation_form()

@properties_bp.route('/property/<int:property_id>/details', methods=['GET'])
@login_required
def get_property_details(property_id):
    return property_controller.get_property_by_id(property_id)

@properties_bp.route('/property/<int:property_id>/jobs', methods=['GET'])
@login_required
def get_property_jobs_route(property_id):
    return property_controller.get_property_jobs_modal_content(property_id)

@properties_bp.route('/property/<int:property_id>/update', methods=['GET', 'PUT'])
@login_required
def update_property_route(property_id):
    if request.method == 'PUT':
        return property_controller.update_property(property_id)
    return property_controller.get_property_update_form(property_id)

@properties_bp.route('/property/<int:property_id>/delete', methods=['DELETE'])
@login_required
def delete_property_route(property_id):
    return property_controller.delete_property(property_id)