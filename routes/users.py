from flask import Blueprint
from flask_login import login_required, current_user
from controllers import users_controller
from flask import flash, redirect, url_for

# Create the user blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

# This function will be called after each request, even if an exception occurs
@user_bp.teardown_request
def teardown_db(exception=None):
    users_controller.teardown_db(exception)

@user_bp.route('/view')
@login_required
def list_all_users_view():
    """List all users with their teams and roles for the owner view."""
    return users_controller.list_all_users_view()

@user_bp.route('/')
@login_required
def list_users_api():
    """List all users (API endpoint)"""
    return users_controller.list_users()

@user_bp.route('/<int:user_id>')
@login_required
def get_user(user_id):
    """Get a specific user by ID"""
    return users_controller.get_user(user_id)

@user_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new user"""
    return users_controller.register()
    
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    return users_controller.login()

@user_bp.route('/<int:user_id>/update', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user information"""
    return users_controller.update_user(user_id)

@user_bp.route('/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    return users_controller.delete_user(user_id)
