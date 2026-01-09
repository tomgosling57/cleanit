# routes/users.py
from flask import Blueprint, request, g
from flask_login import login_required
from database import get_db, teardown_db
from services.user_service import UserService
from utils.user_helper import UserHelper
from controllers.users_controller import UserController

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.teardown_request
def teardown_user_db(exception=None):
    teardown_db(exception)

def get_user_controller():
    """Create and return a UserController instance with request-level database session."""
    db_session = get_db()
    user_service = UserService(db_session)
    user_helper = UserHelper(db_session)
    controller = UserController(
        user_service=user_service,
        user_helper=user_helper
    )
    return controller

@user_bp.route('/')
@login_required
def users():
    controller = get_user_controller()
    return controller.list_users()

@user_bp.route('/all_categorized', methods=['GET'])
@login_required
def get_all_categorized_users():
    controller = get_user_controller()
    return controller.get_all_categorized_users()

@user_bp.route('/view')
@login_required
def users_view():
    controller = get_user_controller()
    return controller.list_all_users_view()

@user_bp.route('/user/<int:user_id>/details', methods=['GET'])
@login_required
def get_user_details(user_id):
    controller = get_user_controller()
    return controller.get_user(user_id)

@user_bp.route('/user/<int:user_id>/change_password', methods=['GET'])
@login_required
def get_user_update_password_form(user_id):
    controller = get_user_controller()
    return controller.get_user_update_password_form(user_id)

@user_bp.route('/user/<int:user_id>/change_password', methods=['PUT'])
@login_required
def update_user_password(user_id):
    controller = get_user_controller()
    return controller.update_user_password(user_id)
    
@user_bp.route('/profile', methods=['GET'])
@login_required
def get_user_profile():
    controller = get_user_controller()
    return controller.get_user_profile()

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_user_profile():
    controller = get_user_controller()
    return controller.update_user_profile()

@user_bp.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    controller = get_user_controller()
    if request.method == 'POST':
        return controller.create_user()
    else:
        return controller.get_user_creation_form()

@user_bp.route('/user/login', methods=['GET', 'POST'])
def login():
    controller = get_user_controller()
    return controller.login()

@user_bp.route('/user/<int:user_id>/update', methods=['PUT', 'GET'])
@login_required
def update_user(user_id):
    controller = get_user_controller()
    if request.method == 'PUT':
        return controller.update_user(user_id)
    else:
        return controller.get_user_update_form(user_id)

@user_bp.route('/user/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user(user_id):
    controller = get_user_controller()
    return controller.delete_user(user_id)
