from flask import Blueprint
from controllers import users_controller

# Create the user blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

# This function will be called after each request, even if an exception occurs
@user_bp.teardown_request
def teardown_db(exception=None):
    users_controller.teardown_db(exception)

@user_bp.route('/')
def list_users():
    """List all users"""
    return users_controller.list_users()

@user_bp.route('/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID"""
    return users_controller.get_user(user_id)

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    return users_controller.register()
    
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    return users_controller.login()

@user_bp.route('/<int:user_id>/update', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    return users_controller.update_user(user_id)

@user_bp.route('/<int:user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    return users_controller.delete_user(user_id)
