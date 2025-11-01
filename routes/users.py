from flask import Blueprint, request
from flask_login import login_required
from controllers import users_controller
from database import teardown_db

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.teardown_request
def teardown_user_db(exception=None):
    teardown_db(exception)

@user_bp.route('/')
@login_required
def users():
    return users_controller.list_users()

@user_bp.route('/view')
@login_required
def users_view():
    return users_controller.list_all_users_view()

@user_bp.route('/user/<int:user_id>/details', methods=['GET'])
@login_required
def get_user_details(user_id):
    return users_controller.get_user(user_id)

@user_bp.route('/user/register', methods=['GET', 'POST'])
@login_required
def register():
    return users_controller.register()

@user_bp.route('/user/login', methods=['GET', 'POST'])
def login():
    return users_controller.login()

@user_bp.route('/user/<int:user_id>/update', methods=['PUT'])
@login_required
def update_user(user_id):
    return users_controller.update_user(user_id)

@user_bp.route('/user/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user(user_id):
    return users_controller.delete_user(user_id)
